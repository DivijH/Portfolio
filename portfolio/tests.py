from django.core import mail
from django.test import TestCase
from django.urls import reverse

from . import models


class SmokeTests(TestCase):
    """Every page should render (200) even with an empty database."""

    @classmethod
    def setUpTestData(cls):
        cls.pub = models.Publication.objects.create(
            title='A Test Paper on LLM Agents', authors='Divij Handa, Coauthor',
            venue='ICLR 2026', year=2026, kind=models.Publication.Kind.CONFERENCE,
            stage=models.Publication.Stage.DATA_GENERATION,
        )

    def test_public_pages_render(self):
        names = ['index', 'research', 'publications', 'contact']
        for name in names:
            with self.subTest(page=name):
                resp = self.client.get(reverse(f'portfolio:{name}'))
                self.assertEqual(resp.status_code, 200)

    def test_publication_detail_renders(self):
        self.assertTrue(self.pub.slug)  # auto-generated on save
        resp = self.client.get(reverse('portfolio:publication', args=[self.pub.slug]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'A Test Paper on LLM Agents')

    def test_missing_publication_404s(self):
        resp = self.client.get(reverse('portfolio:publication', args=['nope']))
        self.assertEqual(resp.status_code, 404)

    def test_profile_singleton(self):
        a = models.Profile.load()
        b = models.Profile.load()
        self.assertEqual(a.pk, b.pk)
        self.assertEqual(models.Profile.objects.count(), 1)

    def test_filtered_publications(self):
        resp = self.client.get(reverse('portfolio:publications'), {'tag': 'LLMs'})
        self.assertEqual(resp.status_code, 200)

    def test_cv_url_falls_back_to_static(self):
        profile = models.Profile.load()
        self.assertFalse(profile.resume)
        self.assertIn('CV_Divij_Handa.pdf', profile.cv_url)

    def test_sitemap_and_robots(self):
        self.assertEqual(self.client.get('/sitemap.xml').status_code, 200)
        robots = self.client.get('/robots.txt')
        self.assertEqual(robots.status_code, 200)
        self.assertContains(robots, 'Sitemap:')


class ContactFormTests(TestCase):
    url = reverse('portfolio:contact')
    valid = {'name': 'Ada Lovelace', 'email': 'ada@example.com',
             'subject': 'Collaboration', 'message': 'Loved your work on agents.'}

    def test_get_renders(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_valid_submission_saves_and_emails(self):
        resp = self.client.post(self.url, self.valid)
        self.assertRedirects(resp, self.url)
        msg = models.ContactMessage.objects.get()
        self.assertEqual(msg.email, 'ada@example.com')
        # Emailed to the site owner, with reply-to set to the sender.
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('dhanda@asu.edu', mail.outbox[0].to)
        self.assertEqual(mail.outbox[0].reply_to, ['ada@example.com'])

    def test_invalid_submission_reports_errors(self):
        resp = self.client.post(self.url, {**self.valid, 'message': ''})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(models.ContactMessage.objects.count(), 0)
        self.assertContains(resp, 'Please enter a message.')
        # Previously entered values are preserved.
        self.assertContains(resp, 'Ada Lovelace')

    def test_honeypot_silently_drops_bots(self):
        resp = self.client.post(self.url, {**self.valid, 'website': 'http://spam'})
        self.assertRedirects(resp, self.url)
        self.assertEqual(models.ContactMessage.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)
