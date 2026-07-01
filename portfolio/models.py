from django.db import models
from django.templatetags.static import static
from django.urls import reverse
from django.utils.text import slugify


# ---------------------------------------------------------------------------
# Site identity
# ---------------------------------------------------------------------------

class Profile(models.Model):
    """Singleton holding the site's editable identity, bio and links.

    Lets everything on the page (name, tagline, bio, socials, resume) be
    managed from the Django admin without touching code or redeploying.
    """
    name = models.CharField(max_length=80, default='Divij Handa')
    role = models.CharField(
        max_length=120, default='LLM Researcher',
        help_text='Short role/title shown under your name, e.g. "LLM Researcher".',
    )
    tagline = models.CharField(
        max_length=200, blank=True,
        help_text='One-line hook streamed in the hero, e.g. your research focus.',
    )
    bio = models.TextField(
        max_length=1500, blank=True,
        help_text='A few sentences about you for the About section.',
    )
    location = models.CharField(max_length=120, blank=True, default='Tempe, Arizona')
    email = models.EmailField(blank=True)
    avatar = models.ImageField(upload_to='avatar/', blank=True, null=True)
    resume = models.FileField(
        upload_to='resume/', blank=True, null=True,
        help_text='Upload your CV/resume PDF here — the download button uses it.',
    )

    # Social / academic links (left blank to hide that icon)
    github_url = models.URLField(max_length=300, blank=True)
    linkedin_url = models.URLField(max_length=300, blank=True)
    scholar_url = models.URLField(max_length=300, blank=True, verbose_name='Google Scholar URL')
    twitter_url = models.URLField(max_length=300, blank=True, verbose_name='X / Twitter URL')
    huggingface_url = models.URLField(max_length=300, blank=True, verbose_name='Hugging Face URL')
    orcid_url = models.URLField(max_length=300, blank=True, verbose_name='ORCID URL')
    instagram_url = models.URLField(max_length=300, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Enforce a single row.
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def cv_url(self):
        """URL for the downloadable CV.

        Prefers an admin-uploaded resume (Profile.resume); otherwise falls back
        to the version-controlled PDF bundled in static, so the CV button always
        works even before anything is uploaded.
        """
        if self.resume:
            return self.resume.url
        return static('portfolio/files/CV_Divij_Handa.pdf')

    @property
    def stream_phrases(self):
        """Phrases the hero 'types out'. Split the tagline on '|', else defaults."""
        if self.tagline.strip():
            parts = [p.strip() for p in self.tagline.split('|') if p.strip()]
            if parts:
                return parts
        return [
            'aligning language models with human intent',
            'reasoning and planning with LLMs',
            'evaluating what models actually know',
        ]

    @property
    def socials(self):
        """List of (label, url, icon-key) for present social links."""
        mapping = [
            ('Email', f'mailto:{self.email}' if self.email else '', 'mail'),
            ('Google Scholar', self.scholar_url, 'scholar'),
            ('GitHub', self.github_url, 'github'),
            ('LinkedIn', self.linkedin_url, 'linkedin'),
            ('X', self.twitter_url, 'twitter'),
            ('Hugging Face', self.huggingface_url, 'huggingface'),
            ('ORCID', self.orcid_url, 'orcid'),
            ('Instagram', self.instagram_url, 'instagram'),
        ]
        return [(label, url, icon) for label, url, icon in mapping if url]


# ---------------------------------------------------------------------------
# Research
# ---------------------------------------------------------------------------

class ResearchArea(models.Model):
    """A theme/area of research shown on the home and research pages."""
    title = models.CharField(max_length=120)
    summary = models.CharField(max_length=300, help_text='One-line description.')
    description = models.TextField(max_length=1200, blank=True)
    icon = models.CharField(
        max_length=8, blank=True, default='',
        help_text='Optional emoji shown with the area, e.g. 🧠.',
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.title


class Tag(models.Model):
    tag_name = models.CharField(max_length=50, default='')

    class Meta:
        ordering = ['tag_name']

    def __str__(self):
        return self.tag_name


class Publication(models.Model):
    class Kind(models.TextChoices):
        CONFERENCE = 'conference', 'Conference'
        JOURNAL = 'journal', 'Journal'
        WORKSHOP = 'workshop', 'Workshop'
        PREPRINT = 'preprint', 'Preprint'
        THESIS = 'thesis', 'Thesis'

    class Stage(models.TextChoices):
        DATA_GENERATION = 'data_generation', 'Data Generation'
        TRAINING = 'training', 'Training'
        TEST_TIME = 'test_time', 'Test-Time'
        EVAL_SAFETY = 'eval_safety', 'Evaluation & Safety'

    title = models.CharField(max_length=300)
    slug = models.SlugField(
        max_length=140, unique=True, blank=True, null=True,
        help_text='URL for this paper’s page. Auto-generated from the title if left blank.')
    authors = models.CharField(
        max_length=500,
        help_text='Comma-separated. Your own name is auto-highlighted on the page.',
    )
    venue = models.CharField(max_length=200, help_text='e.g. "ICLR 2024", "NeurIPS Workshop".')
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField(default=1, help_text='1-12, used only for ordering.')
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.CONFERENCE)
    tldr = models.CharField(
        max_length=300, blank=True,
        help_text='One-line TL;DR shown with featured publications on the home page.')
    abstract = models.TextField(max_length=3000, blank=True)
    award = models.CharField(
        max_length=120, blank=True,
        help_text='Optional badge, e.g. "Oral", "Spotlight", "Best Paper".',
    )

    pdf_url = models.URLField(max_length=400, blank=True)
    arxiv_url = models.URLField(max_length=400, blank=True)
    code_url = models.URLField(max_length=400, blank=True)
    project_url = models.URLField(max_length=400, blank=True)
    video_url = models.URLField(max_length=400, blank=True)
    slides_url = models.URLField(max_length=400, blank=True)
    bibtex = models.TextField(max_length=2000, blank=True)

    image = models.ImageField(upload_to='publications/', blank=True, null=True,
                              help_text='Optional teaser/figure thumbnail.')
    tags = models.ManyToManyField(Tag, blank=True)
    featured = models.BooleanField(default=False, help_text='Show on the home page.')
    stage = models.CharField(
        max_length=20, choices=Stage.choices, blank=True, default='',
        help_text='Where this paper sits in the LLM-agent lifecycle. Drives the '
                  'interactive agent-lifecycle graphic on the home and research pages.')

    class Meta:
        ordering = ['-year', '-month', '-id']

    def __str__(self):
        return f'{self.title} ({self.year})'

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:110] or 'paper'
            slug, n = base, 2
            while Publication.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug = f'{base}-{n}'
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('portfolio:publication', args=[self.slug])

    @property
    def is_published(self):
        """True when the paper is accepted at a venue (i.e. not just a preprint)."""
        return self.kind != self.Kind.PREPRINT

    @property
    def links(self):
        """Present external links as (label, url) pairs in a stable order."""
        candidates = [
            ('PDF', self.pdf_url),
            ('arXiv', self.arxiv_url),
            ('Code', self.code_url),
            ('Project', self.project_url),
            ('Video', self.video_url),
            ('Slides', self.slides_url),
        ]
        return [(label, url) for label, url in candidates if url]


class News(models.Model):
    date = models.DateField()
    content = models.CharField(max_length=400, help_text='Short update, e.g. "Paper accepted at ICLR 2024."')
    url = models.URLField(max_length=400, blank=True)

    class Meta:
        ordering = ['-date', '-id']
        verbose_name_plural = 'News'

    def __str__(self):
        return f'{self.date}: {self.content[:50]}'


# ---------------------------------------------------------------------------
# Experience
# ---------------------------------------------------------------------------

class Experience(models.Model):
    company_name = models.CharField(max_length=80)
    job_title = models.CharField(max_length=80)
    location = models.CharField(max_length=120, blank=True)
    start_date = models.CharField(max_length=20)
    end_date = models.CharField(max_length=20, null=True, blank=True)
    job_description = models.CharField(max_length=600)
    order = models.PositiveIntegerField(default=0, help_text='Lower numbers show first.')

    class Meta:
        ordering = ['order', '-id']

    def __str__(self):
        return f'{self.company_name} ({self.start_date})'


# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------

class ContactMessage(models.Model):
    """A message sent through the contact form.

    Every submission is stored here (so nothing is ever lost) and, when email is
    configured, also emailed to the site owner. Visible/manageable in the admin.
    """
    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField(max_length=4000)
    created_at = models.DateTimeField(auto_now_add=True)
    handled = models.BooleanField(default=False, help_text='Tick once you have replied.')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} <{self.email}> — {self.subject or "(no subject)"}'
