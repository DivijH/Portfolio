import hmac
import json
import re

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.http import Http404, HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from . import models


def robots_txt(request):
    """Serve robots.txt with an absolute link to the sitemap."""
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /admin/',
        'Disallow: /electionbench',  # private, password-gated
        f'Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml',
    ]
    return HttpResponse('\n'.join(lines) + '\n', content_type='text/plain')

# The LLM-agent lifecycle stages shown in the interactive pipeline graphic.
# (key matches Publication.Stage; icon/blurb describe the stage)
AGENT_STAGES = [
    ('data_generation', 'Data Generation', '🧪', 'Creating the benchmarks and datasets that probe and stress-test agents.'),
    ('training', 'Training', '🏋️', 'How agents learn — post-training, RL and self-improvement.'),
    ('test_time', 'Test-Time', '⚡', 'How agents reason and act at inference — sampling, planning and multi-agent methods.'),
    ('eval_safety', 'Evaluation & Safety', '🛡️', 'Measuring real capability and surfacing failure modes — jailbreaks and robustness.'),
]


def build_agent_pipeline():
    """Group publications by their LLM-agent lifecycle stage for the graphic."""
    by_stage = {key: [] for key, *_ in AGENT_STAGES}
    for pub in models.Publication.objects.exclude(stage=''):
        by_stage.get(pub.stage, []).append(pub)
    return [
        {'key': key, 'label': label, 'icon': icon, 'blurb': blurb, 'papers': by_stage[key]}
        for key, label, icon, blurb in AGENT_STAGES
    ]


class IndexView(View):
    def get(self, request):
        featured_pubs = models.Publication.objects.filter(featured=True)
        if not featured_pubs.exists():
            featured_pubs = models.Publication.objects.all()[:3]

        return render(request, 'portfolio/index.html', {
            'agent_pipeline': build_agent_pipeline(),
            'publications': featured_pubs,
            'news': models.News.objects.all()[:5],
            'experiences': models.Experience.objects.all(),
        })


class ResearchView(View):
    def get(self, request):
        return render(request, 'portfolio/research.html', {
            'agent_pipeline': build_agent_pipeline(),
            'research_areas': models.ResearchArea.objects.all(),
            'publications': models.Publication.objects.all(),
        })


class PublicationsView(View):
    def get(self, request):
        publications = models.Publication.objects.all()
        active_tag = request.GET.get('tag', '')
        if active_tag:
            publications = publications.filter(tags__tag_name=active_tag)
        tags = models.Tag.objects.filter(publication__isnull=False).distinct()
        return render(request, 'portfolio/publications.html', {
            'publications': publications,
            'tags': tags,
            'active_tag': active_tag,
            'total': models.Publication.objects.count(),
        })


class SinglePublicationView(View):
    def get(self, request, slug):
        try:
            publication = models.Publication.objects.get(slug=slug)
        except models.Publication.DoesNotExist:
            raise Http404('Publication not found')
        return render(request, 'portfolio/publication.html', {'publication': publication})


class ContactView(View):
    def get(self, request):
        return render(request, 'portfolio/contact.html')

    def post(self, request):
        data = {
            'name': request.POST.get('name', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'subject': request.POST.get('subject', '').strip(),
            'message': request.POST.get('message', '').strip(),
        }

        # Honeypot: real users leave this hidden field empty; bots fill it.
        if request.POST.get('website'):
            messages.success(request, "Thanks — your message has been sent.")
            return redirect('portfolio:contact')

        errors = {}
        if not data['name']:
            errors['name'] = 'Please enter your name.'
        if '@' not in data['email'] or '.' not in data['email']:
            errors['email'] = 'Please enter a valid email address.'
        if not data['message']:
            errors['message'] = 'Please enter a message.'

        if errors:
            return render(request, 'portfolio/contact.html', {'errors': errors, 'form': data})

        models.ContactMessage.objects.create(**data)

        # Best-effort email notification — a mail failure must never lose the
        # message (it is already saved) or break the page.
        recipient = getattr(settings, 'CONTACT_EMAIL', '')
        if recipient:
            try:
                EmailMessage(
                    subject=f'[divijhanda.in] {data["subject"] or "New message"} — from {data["name"]}',
                    body=f'From: {data["name"]} <{data["email"]}>\n\n{data["message"]}',
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', '') or recipient,
                    to=[recipient],
                    reply_to=[data['email']],
                ).send(fail_silently=True)
            except Exception:
                pass

        messages.success(request, "Thanks — your message has been sent. I'll get back to you soon.")
        return redirect('portfolio:contact')


# ---------------------------------------------------------------------------
# ElectionBench — private page (password gate) + streamed-results ingest
# ---------------------------------------------------------------------------

class ElectionBenchView(View):
    """Password-gated benchmark page. Correct password sets a session flag."""
    template = 'portfolio/electionbench.html'

    def get(self, request):
        if not settings.ELECTIONBENCH_PASSWORD:
            raise Http404()  # feature off until a password is configured
        if request.session.get('eb_ok'):
            return render(request, self.template, {'bench': models.ElectionBench.load()})
        return render(request, self.template, {'locked': True})

    def post(self, request):
        if not settings.ELECTIONBENCH_PASSWORD:
            raise Http404()
        entered = request.POST.get('password', '')
        if hmac.compare_digest(entered, settings.ELECTIONBENCH_PASSWORD):
            request.session['eb_ok'] = True
            return redirect('portfolio:electionbench')
        return render(request, self.template, {'locked': True, 'error': 'Incorrect password.'})


@csrf_exempt
def electionbench_ingest(request):
    """Token-authenticated endpoint the simulation POSTs results to.

    Auth: `Authorization: Bearer <token>` (or `X-Api-Token: <token>`).
    Body: JSON — {"columns": [...], "rows": [[...]], "note": "...", "status": "..."}.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    token = settings.ELECTIONBENCH_TOKEN
    if not token:
        raise Http404()

    auth = request.headers.get('Authorization', '')
    provided = auth[7:].strip() if auth.startswith('Bearer ') else request.headers.get('X-Api-Token', '')
    if not provided or not hmac.compare_digest(provided, token):
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid JSON'}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({'ok': False, 'error': 'expected a JSON object'}, status=400)

    # Maintenance: wipe all games (e.g. before re-streaming a fresh run).
    if payload.get('clear_games') is True:
        deleted, _ = models.Game.objects.all().delete()
        return JsonResponse({'ok': True, 'games_deleted': deleted})

    # Games batch (explorer data) — upsert by log_name.
    if isinstance(payload.get('games'), list):
        n = 0
        for g in payload['games']:
            ln = g.get('log_name')
            if not ln:
                continue
            models.Game.objects.update_or_create(log_name=ln[:200], defaults={
                'model_a': (g.get('model_a') or '')[:80],
                'model_b': (g.get('model_b') or '')[:80],
                'seed': int(g.get('seed') or 0),
                'game_idx': int(g.get('game_idx') or 0),
                'winner_model': (g.get('winner_model') or '')[:80],
                'popular_margin': g.get('popular_margin'),
                'states_a': int(g.get('states_a') or 0),
                'states_b': int(g.get('states_b') or 0),
                'turnout': g.get('turnout'),
                'transcript': g.get('transcript') or '',
                'detail': g.get('detail') or {},
                'raw_log': g.get('raw_log') or '',
            })
            n += 1
        deleted = 0
        prefix = payload.get('games_keep_prefix')
        if isinstance(prefix, str) and prefix:
            # Full-run sync: games outside the current run's log prefix are
            # stale leftovers from an earlier simulation — drop them.
            deleted, _ = models.Game.objects.exclude(log_name__startswith=prefix[:200]).delete()
        return JsonResponse({'ok': True, 'games_upserted': n, 'games_deleted': deleted})

    # Standalone prefix purge (no batch): keep only the current run's games.
    if isinstance(payload.get('games_keep_prefix'), str) and payload['games_keep_prefix']:
        deleted, _ = models.Game.objects.exclude(
            log_name__startswith=payload['games_keep_prefix'][:200]).delete()
        return JsonResponse({'ok': True, 'games_deleted': deleted})

    # Leaderboard update.
    bench = models.ElectionBench.load()
    bench.results = {
        'columns': payload.get('columns', []),
        'rows': payload.get('rows', []),
        'note': str(payload.get('note', '')),
        'models': payload.get('models', []),
    }
    if 'status' in payload:
        bench.status = str(payload.get('status', ''))[:160]
    bench.results_updated_at = timezone.now()
    bench.save()
    return JsonResponse({'ok': True, 'updated_at': bench.results_updated_at.isoformat()})


def electionbench_h2h(request):
    """Session-gated JSON: head-to-head record + game list for two models.

    Supports self-play (a == b): games are reported in slot orientation
    (slot A vs slot B), with the slot holding more states counted as the
    winner, since `winner_model` cannot distinguish the two sides.
    """
    if not request.session.get('eb_ok'):
        return JsonResponse({'ok': False, 'error': 'locked'}, status=403)
    a = request.GET.get('a', '').strip()
    b = request.GET.get('b', '').strip()
    if not a or not b:
        return JsonResponse({'ok': False, 'error': 'pick two models'}, status=400)
    from django.db.models import Q
    games = list(models.Game.objects.filter(
        Q(model_a=a, model_b=b) | Q(model_a=b, model_b=a)).order_by('seed', 'game_idx'))
    selfplay = (a == b)

    def oriented(g):
        """(margin toward a, a-side states, b-side states) in the caller's
        (a, b) orientation. Self-play games are already in slot order."""
        if selfplay or g.model_a == a:
            return g.popular_margin, g.states_a, g.states_b
        m = None if g.popular_margin is None else -g.popular_margin
        return m, g.states_b, g.states_a

    n = len(games)
    a_wins = b_wins = draws = 0
    margins = []
    rows = []
    for g in games:
        m, sa, sb = oriented(g)
        if m is not None:
            margins.append(m)
        if not g.winner_model:
            draws += 1
            winner = 'draw'
        elif selfplay:
            slot_a_won = sa > sb or (sa == sb and (m or 0) > 0)
            if slot_a_won:
                a_wins += 1
                winner = 'slot A'
            else:
                b_wins += 1
                winner = 'slot B'
        elif g.winner_model == a:
            a_wins += 1
            winner = g.winner_model
        else:
            b_wins += 1
            winner = g.winner_model
        rows.append({
            'id': g.id, 'seed': g.seed, 'game_idx': g.game_idx,
            'winner': winner, 'margin_a': m, 'states_a': sa, 'states_b': sb,
            'turnout': g.turnout,
        })
    return JsonResponse({
        'ok': True, 'a': a, 'b': b, 'n': n, 'selfplay': selfplay,
        'a_wins': a_wins, 'b_wins': b_wins, 'draws': draws,
        'a_win_pct': round(100 * a_wins / n, 1) if n else 0.0,
        'avg_margin_a': round(sum(margins) / len(margins), 4) if margins else None,
        'games': rows,
    })


# --- game-page chat parsing --------------------------------------------------

_THINK_RE = re.compile(r'<think>(.*?)</think>', re.S | re.I)
_FENCE_RE = re.compile(r'```[a-zA-Z]*\s*(.*?)```', re.S)
_ENV_RE = re.compile(
    r'favorability A ([\d.]+) / B ([\d.]+) · budget A ([\d.]+) / B ([\d.]+)')
_STATE_RE = re.compile(r'\bS(\d+): (\d+) voters')


_PROMPT_DAY_RE = re.compile(r'===\s*Day\s+(\d+)\s+of\b')
_TOOL_RE = re.compile(r'^\s*\[tool_call\]\s*([A-Za-z0-9_.\-]+)\((.*)\)\s*$', re.M)


def _fmt_tool_args(raw):
    """Render a tool call's JSON arguments as readable key: value lines."""
    raw = (raw or '').strip()
    if not raw:
        return ''
    try:
        args = json.loads(raw)
    except ValueError:
        return raw
    if not isinstance(args, dict):
        return json.dumps(args, indent=2, ensure_ascii=False)
    lines = []
    for k, v in args.items():
        if isinstance(v, (dict, list)):
            lines.append('%s: %s' % (k, json.dumps(v, indent=2, ensure_ascii=False)))
        else:
            lines.append('%s: %s' % (k, v))
    return '\n'.join(lines)


def _parse_llm_response(text):
    """Split a candidate response into (thinking, prose, action, tools).

    Current sims use tool calling — the streamer serializes each call as a
    "[tool_call] name({json args})" line. Older runs replied with a JSON
    action in ``` fences instead. Thinking comes only from explicit <think>
    content (sometimes with the opening tag stripped by the serving stack);
    non-reasoning models have none, and their prose is simply their reply.
    """
    text = text or ''
    thinking = '\n\n'.join(p.strip() for p in _THINK_RE.findall(text)).strip()
    body = _THINK_RE.sub('', text)
    low = body.lower()
    if '</think>' in low:
        cut = low.rfind('</think>')
        head = re.sub(r'(?i)<think>', '', body[:cut]).strip()
        thinking = (thinking + '\n\n' + head).strip() if thinking else head
        body = body[cut + len('</think>'):]

    tools = [{'name': m.group(1), 'args': _fmt_tool_args(m.group(2))}
             for m in _TOOL_RE.finditer(body)]
    body = _TOOL_RE.sub('', body)

    action = ''
    if not tools:  # legacy fenced-JSON actions
        fences = _FENCE_RE.findall(body)
        action = fences[-1].strip() if fences else ''
    prose = _FENCE_RE.sub('', body).strip()
    if not tools and not action:
        # legacy models occasionally skipped the fences entirely
        m = re.search(r'(?s)(\{\s*"action".*\})\s*$', prose)
        if m:
            action = m.group(1).strip()
            prose = prose[:m.start()].strip()
    return thinking, prose, action, tools


def _build_game_chat(g):
    """Shape a game's detail {setup, timeline} into per-day chat sections."""
    detail = g.detail or {}
    setup = detail.get('setup') or {}
    timeline = detail.get('timeline') or []
    if not timeline:
        return None

    slot_of = {}
    if setup.get('candidate_a'):
        slot_of[setup['candidate_a']] = 'A'
    if setup.get('candidate_b') and setup.get('candidate_b') != setup.get('candidate_a'):
        slot_of[setup['candidate_b']] = 'B'

    # The sim logs each day's first LLM call *before* it writes the day
    # marker, so a call's own "=== Day N of M ===" prompt header is the
    # authoritative day; the running marker is only the fallback (and is
    # what events/env attach to).
    # Within a day the two candidates act in parallel, so each day renders
    # as two side-by-side columns (col_a / col_b); slotless items go to
    # `mid`. Only the debate is a genuine exchange — it stays sequential.
    sections = {}
    def section(n):
        if n not in sections:
            sections[n] = {'n': n, 'col_a': [], 'col_b': [], 'mid': [],
                           'debate': [], 'env': '', 'env_stats': None}
        return sections[n]

    def place(cur, slot, entry):
        if slot == 'A':
            cur['col_a'].append(entry)
        elif slot == 'B':
            cur['col_b'].append(entry)
        else:
            cur['mid'].append(entry)

    cur_n = None
    systems = {}          # slot -> system prompt (shown once, in the header)
    state_sizes = []

    for it in timeline:
        t = it.get('t')
        if t == 'day':
            cur_n = it.get('day') or ((cur_n or 0) + 1)
            section(cur_n)
            continue

        if t == 'env':
            cur = section(cur_n or 1)
            cur['env'] = (it.get('text') or '').strip()
            m = _ENV_RE.search(cur['env'])
            if m:
                cur['env_stats'] = {'fav_a': m.group(1), 'fav_b': m.group(2),
                                    'bud_a': m.group(3), 'bud_b': m.group(4)}
        elif t == 'cand_call':
            prompt = (it.get('prompt') or '').strip()
            m = _PROMPT_DAY_RE.search(prompt)
            cur = section(int(m.group(1)) if m else (cur_n or 1))
            thinking, prose, action, tools = _parse_llm_response(it.get('response'))
            slot = slot_of.get(it.get('model'), '')
            entry = {
                'kind': 'call', 'tag': it.get('tag', ''), 'slot': slot,
                'model': it.get('model', ''),
                'thinking': thinking,
                'prose': prose, 'action': action, 'tools': tools,
                'prompt': prompt,
            }
            if slot and slot not in systems and (it.get('system') or '').strip():
                systems[slot] = it['system'].strip()
            if not state_sizes:
                state_sizes = _STATE_RE.findall(prompt)
            if it.get('tag') == 'debate':
                cur['debate'].append(entry)
            else:
                place(cur, slot, entry)
        elif t == 'action':
            cur = section(cur_n or 1)
            entry = {
                'kind': 'event', 'event_kind': it.get('kind', ''),
                'slot': it.get('slot') or '', 'text': (it.get('text') or '').strip(),
            }
            if 'debate' in (it.get('kind') or ''):
                cur['debate'].append(entry)
            else:
                place(cur, entry['slot'], entry)
        elif t == 'other_call':
            section(cur_n or 1)['mid'].append({
                'kind': 'other', 'tag': it.get('tag', ''), 'model': it.get('model', ''),
                'prompt': (it.get('prompt') or '').strip(),
                'response': (it.get('response') or '').strip(),
            })

    days = [sections[n] for n in sorted(sections)]
    return {
        'setup': setup,
        'days': days,
        'systems': systems,
        'state_sizes': [{'state': 'S' + s, 'voters': v} for s, v in state_sizes],
    }


def electionbench_game(request, game_id):
    """Session-gated full-page view of one game (chat-style days, or the flat transcript)."""
    if not settings.ELECTIONBENCH_PASSWORD:
        raise Http404()
    if not request.session.get('eb_ok'):
        return redirect('portfolio:electionbench')
    try:
        g = models.Game.objects.get(pk=game_id)
    except models.Game.DoesNotExist:
        raise Http404()
    chat = _build_game_chat(g)
    return render(request, 'portfolio/electionbench_game.html',
                  {'g': g, 'chat': chat, 'setup': (chat or {}).get('setup')})


def electionbench_game_full(request, game_id):
    """Session-gated plain-text dump of a game's complete event log (the 'full log' link)."""
    if not settings.ELECTIONBENCH_PASSWORD:
        raise Http404()
    if not request.session.get('eb_ok'):
        return redirect('portfolio:electionbench')
    try:
        g = models.Game.objects.get(pk=game_id)
    except models.Game.DoesNotExist:
        raise Http404()
    return HttpResponse(g.raw_log or g.transcript or '(no log)',
                        content_type='text/plain; charset=utf-8')
