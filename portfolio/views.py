import hmac
import json

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
            })
            n += 1
        return JsonResponse({'ok': True, 'games_upserted': n})

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
    """Session-gated JSON: head-to-head record + game list for two models."""
    if not request.session.get('eb_ok'):
        return JsonResponse({'ok': False, 'error': 'locked'}, status=403)
    a = request.GET.get('a', '').strip()
    b = request.GET.get('b', '').strip()
    if not a or not b:
        return JsonResponse({'ok': False, 'error': 'pick two models'}, status=400)
    from django.db.models import Q
    games = list(models.Game.objects.filter(
        Q(model_a=a, model_b=b) | Q(model_a=b, model_b=a)).order_by('seed', 'game_idx'))

    def margin_a(g):
        if g.popular_margin is None:
            return None
        return g.popular_margin if g.model_a == a else -g.popular_margin

    def states_of(g, model):
        return g.states_a if model == g.model_a else g.states_b

    n = len(games)
    a_wins = sum(1 for g in games if g.winner_model == a)
    b_wins = sum(1 for g in games if g.winner_model == b)
    draws = sum(1 for g in games if not g.winner_model)
    margins = [m for m in (margin_a(g) for g in games) if m is not None]
    return JsonResponse({
        'ok': True, 'a': a, 'b': b, 'n': n,
        'a_wins': a_wins, 'b_wins': b_wins, 'draws': draws,
        'a_win_pct': round(100 * a_wins / n, 1) if n else 0.0,
        'avg_margin_a': round(sum(margins) / len(margins), 4) if margins else None,
        'games': [{
            'id': g.id, 'seed': g.seed, 'game_idx': g.game_idx,
            'winner': g.winner_model or 'draw',
            'margin_a': margin_a(g), 'states_a': states_of(g, a), 'states_b': states_of(g, b),
            'turnout': g.turnout,
        } for g in games],
    })


def electionbench_game(request, game_id):
    """Session-gated full-page view of one game (setup + timeline, or the flat transcript)."""
    if not settings.ELECTIONBENCH_PASSWORD:
        raise Http404()
    if not request.session.get('eb_ok'):
        return redirect('portfolio:electionbench')
    try:
        g = models.Game.objects.get(pk=game_id)
    except models.Game.DoesNotExist:
        raise Http404()
    return render(request, 'portfolio/electionbench_game.html', {'g': g, 'detail': g.detail or None})
