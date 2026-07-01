from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.views import View

from . import models


def robots_txt(request):
    """Serve robots.txt with an absolute link to the sitemap."""
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /admin/',
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
