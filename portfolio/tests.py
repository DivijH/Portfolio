import json

from django.core import mail
from django.test import TestCase, override_settings
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


@override_settings(ELECTIONBENCH_PASSWORD='pw-test', ELECTIONBENCH_TOKEN='tok-test')
class ElectionBenchTests(TestCase):
    url = reverse('portfolio:electionbench')
    ingest = reverse('portfolio:electionbench_ingest')
    h2h = reverse('portfolio:electionbench_h2h')

    def test_locked_and_noindex(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Private benchmark')
        self.assertContains(r, 'noindex')

    def test_wrong_password_stays_locked(self):
        r = self.client.post(self.url, {'password': 'nope'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Incorrect password')
        self.assertNotIn('eb_ok', self.client.session)

    def test_correct_password_unlocks(self):
        r = self.client.post(self.url, {'password': 'pw-test'})
        self.assertRedirects(r, self.url)
        self.assertTrue(self.client.session.get('eb_ok'))
        self.assertContains(self.client.get(self.url), 'ElectionBench')

    def test_ingest_requires_token(self):
        r = self.client.post(self.ingest, data='{}', content_type='application/json')
        self.assertEqual(r.status_code, 403)

    def test_ingest_stores_and_renders(self):
        body = {'columns': ['Model', 'Score'], 'rows': [['GPT-4', 0.82]], 'status': 'Running 1/10'}
        r = self.client.post(self.ingest, data=json.dumps(body), content_type='application/json',
                             HTTP_AUTHORIZATION='Bearer tok-test')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()['ok'])
        bench = models.ElectionBench.load()
        self.assertEqual(bench.results['rows'], [['GPT-4', 0.82]])
        self.assertEqual(bench.status, 'Running 1/10')
        s = self.client.session; s['eb_ok'] = True; s.save()
        self.assertContains(self.client.get(self.url), 'GPT-4')

    def test_ingest_get_405(self):
        self.assertEqual(self.client.get(self.ingest).status_code, 405)

    @override_settings(ELECTIONBENCH_PASSWORD='')
    def test_404_when_unconfigured(self):
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def _ingest_two_games(self):
        body = {"games": [
            {"log_name": "cand_x_v_cand_y_100_0.jsonl", "model_a": "cand_x", "model_b": "cand_y",
             "seed": 100, "game_idx": 0, "winner_model": "cand_x", "popular_margin": 0.1,
             "states_a": 3, "states_b": 2, "turnout": 0.5, "transcript": "X campaigned hard. X wins."},
            {"log_name": "cand_x_v_cand_y_100_1.jsonl", "model_a": "cand_x", "model_b": "cand_y",
             "seed": 100, "game_idx": 1, "winner_model": "cand_y", "popular_margin": -0.05,
             "states_a": 2, "states_b": 3, "transcript": "Y edged it."},
        ]}
        return self.client.post(self.ingest, data=json.dumps(body), content_type='application/json',
                                HTTP_X_API_TOKEN='tok-test')  # X-Api-Token (Apache-safe) path

    def test_games_ingest_upserts(self):
        r = self._ingest_two_games()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['games_upserted'], 2)
        self.assertEqual(models.Game.objects.count(), 2)
        self._ingest_two_games()  # idempotent (upsert by log_name)
        self.assertEqual(models.Game.objects.count(), 2)

    def test_h2h_requires_session_then_returns_record(self):
        self._ingest_two_games()
        self.assertEqual(self.client.get(self.h2h, {'a': 'cand_x', 'b': 'cand_y'}).status_code, 403)
        s = self.client.session; s['eb_ok'] = True; s.save()
        d = self.client.get(self.h2h, {'a': 'cand_x', 'b': 'cand_y'}).json()
        self.assertEqual((d['n'], d['a_wins'], d['b_wins']), (2, 1, 1))
        self.assertEqual(len(d['games']), 2)

    def test_game_page_renders_and_is_gated(self):
        self._ingest_two_games()
        gid = models.Game.objects.get(log_name='cand_x_v_cand_y_100_0.jsonl').id
        url = reverse('portfolio:electionbench_game', args=[gid])
        self.assertEqual(self.client.get(url).status_code, 302)  # redirects to gate when locked
        s = self.client.session; s['eb_ok'] = True; s.save()
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'X campaigned')  # transcript fallback (no detail here)

    def test_game_detail_ingest(self):
        body = {"games": [{"log_name": "g_v_h_1_0.jsonl", "model_a": "cand_g", "model_b": "cand_h",
                           "winner_model": "cand_g",
                           "detail": {"setup": {"candidate_a": "g", "candidate_b": "h"},
                                      "timeline": [{"t": "cand_call", "tag": "action", "model": "g",
                                                    "prompt": "OBSERVATION XYZ", "response": "REASONING then action"}]}}]}
        self.client.post(self.ingest, data=json.dumps(body), content_type='application/json',
                         HTTP_X_API_TOKEN='tok-test')
        s = self.client.session; s['eb_ok'] = True; s.save()
        gid = models.Game.objects.get(log_name='g_v_h_1_0.jsonl').id
        r = self.client.get(reverse('portfolio:electionbench_game', args=[gid]))
        self.assertContains(r, 'OBSERVATION XYZ')
        self.assertContains(r, 'REASONING then action')
