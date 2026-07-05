"""Load Divij Handa's real site content (from his Google Scholar / public profile).

    python manage.py seed_demo

Populates the Profile, Research areas, Publications, News and Experience with
real data. Idempotent: it clears and rebuilds those sections each run, so it is
safe to run repeatedly. Experience dates/titles were inferred from public
profiles — verify them in the admin.
"""
import datetime
import pathlib

from django.core.management.base import BaseCommand

from portfolio import models

P = models.Publication.Kind
S = models.Publication.Stage


class Command(BaseCommand):
    help = "Load Divij Handa's real profile, publications, news and experience."

    def handle(self, *args, **options):
        # ---- Profile -----------------------------------------------------
        profile = models.Profile.load()
        profile.name = 'Divij Handa'
        profile.role = 'LLM Agents Researcher'
        profile.tagline = ('building reliable LLM agents | '
                           'reasoning, planning & tool use | '
                           'evaluating and securing agentic systems')
        profile.bio = ("I'm a PhD researcher in Computer Science at Arizona State University. My core "
                       "research is on LLM agents — how they're trained, how they reason and act at test "
                       "time, and how we evaluate and keep them safe. My work spans these stages, with "
                       "papers at ICLR, ACL, NAACL, EMNLP and NeurIPS workshops.")
        profile.location = 'Tempe, Arizona'
        profile.email = 'dhanda@asu.edu'
        profile.scholar_url = 'https://scholar.google.com/citations?user=6q8kRwYAAAAJ&hl=en'
        profile.github_url = 'https://github.com/DivijH'
        profile.linkedin_url = 'https://www.linkedin.com/in/divij-handa-504b9766/'
        profile.instagram_url = ''
        profile.save()
        self.stdout.write(self.style.SUCCESS('✓ Profile'))

        # ---- Tags (reused by publications) ------------------------------
        tag_names = ['Reasoning', 'Safety', 'Agents', 'Evaluation', 'LLMs', 'Training']
        tags = {n: models.Tag.objects.get_or_create(tag_name=n)[0] for n in tag_names}

        # ---- Research areas ---------------------------------------------
        models.ResearchArea.objects.all().delete()
        areas = [
            ('🤖', 'LLM Agents',
             'My core focus — building capable, reliable agents across their whole lifecycle.',
             'Multi-agent query rewriting for e-commerce (OptAgent), goal-driven hypothesis generation for '
             'materials discovery, and agents that compile real-world open-source software (BuildBench) — '
             'spanning how agents are trained, act, and are evaluated.'),
            ('🧩', 'Reasoning & Planning',
             'How agents reason about actions, change and state — and steering them at inference time.',
             'Reasoning about actions and change (ActionReasoningBench) and guiding models toward more '
             'diverse, higher-quality solutions at inference time (GuidedSampling).'),
            ('📊', 'Evaluation & Benchmarks',
             'Contamination-free benchmarks that test genuine agent capability, not memorization.',
             'Benchmarks for temporal reasoning (UnSeenTimeQA), reasoning about actions '
             '(ActionReasoningBench) and agentic software building (BuildBench).'),
            ('🛡️', 'Safety & Robustness',
             'Where strong reasoning becomes a vulnerability, and when agents break under shifted assumptions.',
             'Jailbreaking LLMs with novel complex ciphers (ACE / LACE) and studying how models fail when '
             'the common assumptions behind a context no longer hold.'),
            ('🏋️', 'Training & Self-Improvement',
             'Instilling reasoning through self-generated data and teacher-guided reflection.',
             'Teaching models to reflect without distillation (ThinkTuning) and improving RL with '
             'self-generated mid-training data.'),
        ]
        for i, (icon, title, summary, desc) in enumerate(areas):
            models.ResearchArea.objects.create(icon=icon, title=title, summary=summary,
                                               description=desc, order=i)
        self.stdout.write(self.style.SUCCESS('✓ Research areas'))

        # ---- Publications ------------------------------------------------
        models.Publication.objects.all().delete()
        pubs = [
            # 2026
            dict(title='GuidedSampling: Steering LLMs Towards Diverse Candidate Solutions at Inference-Time',
                 slug='guidedsampling',
                 tldr='Makes inference-time sampling produce genuinely diverse solutions — +21.6% pass@50.',
                 authors='Divij Handa, Mihir Parmar, Aswin RRV, Md Nayem Uddin, Hamid Palangi, Chitta Baral',
                 venue='ICLR 2026', year=2026, month=1, kind=P.CONFERENCE, stage=S.TEST_TIME, featured=True,
                 arxiv_url='https://openreview.net/forum?id=TD9jC48sts',
                 abstract='Decouples exploration from generation at inference time so repeated sampling '
                          'produces genuinely diverse candidate solutions, improving pass@50 by ~21.6% '
                          'over standard repeated sampling.',
                 tag_keys=['Reasoning', 'LLMs']),
            dict(title='Mid-Training with Self-Generated Data Improves Reinforcement Learning in Language Models',
                 slug='mid-training-self-generated',
                 tldr='Mid-training on self-generated data boosts downstream RL and reasoning.',
                 authors='Aswin RRV, Jacob Dineen, Divij Handa, Mihir Parmar, Ben Zhou, Swaroop Mishra, Chitta Baral',
                 venue='arXiv preprint', year=2026, month=5, kind=P.PREPRINT, stage=S.TRAINING,
                 arxiv_url='https://arxiv.org/abs/2605.08472',
                 abstract='Shows that mid-training language models on their own self-generated data improves '
                          'downstream reinforcement learning, yielding stronger reasoning than RL alone.',
                 tag_keys=['Training', 'LLMs']),
            # 2025
            dict(title="When “Competency” in Reasoning Opens the Door to Vulnerability: "
                       "Jailbreaking LLMs via Novel Complex Ciphers",
                 slug='jailbreaking-llms-ciphers',
                 tldr='Stronger reasoning makes LLMs easier to jailbreak — via custom ciphers (ACE/LACE).',
                 authors='Divij Handa, Zehua Zhang, Amir Saeidi, Shrinidhi Kumbhar, '
                         'Md Nayem Uddin, Aswin RRV, Chitta Baral',
                 venue='NeurIPS 2025 Workshop (Reliable ML from Unreliable Data)', year=2025, month=12,
                 kind=P.WORKSHOP, stage=S.EVAL_SAFETY, featured=True, arxiv_url='https://openreview.net/forum?id=7ddhbe1YyX',
                 abstract='Shows that as LLMs get better at reasoning they become more susceptible to novel '
                          'jailbreaks. Introduces ACE and LACE — attacks that encode malicious queries with '
                          'custom and layered ciphers — and CipherBench to measure cipher-decoding ability.',
                 tag_keys=['Safety', 'LLMs']),
            dict(title='ThinkTuning: Instilling Cognitive Reflections without Distillation',
                 slug='thinktuning',
                 tldr='Teaches models to self-reflect through teacher feedback, without distillation.',
                 authors='Aswin RRV, Jacob Dineen, Divij Handa, Md Nayem Uddin, Mihir Parmar, Chitta Baral, Ben Zhou',
                 venue='EMNLP 2025', year=2025, month=11, kind=P.CONFERENCE, stage=S.TRAINING,
                 arxiv_url='https://arxiv.org/abs/2508.07616',
                 abstract='A GRPO-based interactive training method where a teacher model gives corrective '
                          'feedback on a student model’s rollouts, instilling self-reflective reasoning '
                          'without distillation.',
                 tag_keys=['Training', 'Reasoning']),
            dict(title='OptAgent: Optimizing Query Rewriting for E-Commerce via Multi-Agent Simulation',
                 slug='optagent',
                 tldr='Uses multi-agent shopper simulation as a reward to optimize e-commerce query rewriting.',
                 authors='Divij Handa, David Blincoe, Orson Adams, Yinlin Fu',
                 venue='arXiv preprint', year=2025, month=10, kind=P.PREPRINT, stage=S.TEST_TIME, featured=True,
                 arxiv_url='https://arxiv.org/abs/2510.03771',
                 abstract='Combines multi-agent simulation with an evolutionary algorithm for query rewriting: '
                          'multiple LLM agents act as simulated shoppers, and their averaged scores form a '
                          'dynamic reward that iteratively refines the query — improving fitness by ~22%.',
                 tag_keys=['Agents', 'LLMs']),
            dict(title='BuildBench: Benchmarking LLM Agents on Compiling Real-World Open-Source Software',
                 slug='buildbench',
                 tldr='A realistic benchmark for LLM agents that compile real-world open-source software.',
                 authors='Zehua Zhang, A. P. Bajaj, Divij Handa, S. Liu, A. S. Raj, '
                         'H. Chen, H. Wang, Y. Liu, et al.',
                 venue='DL4C @ NeurIPS 2025', year=2025, month=12, kind=P.WORKSHOP, stage=S.EVAL_SAFETY,
                 arxiv_url='https://arxiv.org/abs/2509.25248',
                 abstract='A challenging, realistic benchmark of diverse real-world open-source software for '
                          'evaluating LLM agents on automatically compiling projects, plus OSS-Build-Agent, a '
                          'strong baseline with an enhanced build-instruction retrieval module.',
                 tag_keys=['Agents', 'Evaluation']),
            dict(title="UnSeenTimeQA: Time-Sensitive Question-Answering Beyond LLMs' Memorization",
                 slug='unseentimeqa',
                 tldr='A contamination-free benchmark that forces genuine temporal reasoning, not memorization.',
                 authors='Md Nayem Uddin, Amir Saeidi, Divij Handa, Agastya Seth, Tran Cao Son, '
                         'Eduardo Blanco, Steven R. Corman, Chitta Baral',
                 venue='ACL 2025', year=2025, month=7, kind=P.CONFERENCE, stage=S.DATA_GENERATION,
                 arxiv_url='https://arxiv.org/abs/2407.03525',
                 abstract='A contamination-free, time-sensitive QA benchmark built on synthetic facts, '
                          'forcing models to do genuine temporal reasoning rather than recalling '
                          'pre-training knowledge.',
                 tag_keys=['Evaluation', 'Reasoning']),
            dict(title='ActionReasoningBench: Reasoning about Actions with and without Ramification Constraints',
                 slug='actionreasoningbench',
                 tldr='A diagnostic benchmark for reasoning about actions, change and ramifications.',
                 authors='Divij Handa, Pavel Dolin, Shrinidhi Kumbhar, Tran Cao Son, Chitta Baral',
                 venue='ICLR 2025', year=2025, month=8, kind=P.CONFERENCE, stage=S.DATA_GENERATION, featured=True,
                 # month is ordering-only (ICLR was Apr); set above UnSeenTimeQA so it leads Data Generation.
                 arxiv_url='https://arxiv.org/abs/2406.04046',
                 abstract='A diagnostic benchmark spanning eight domains that evaluates LLMs on six '
                          'dimensions of reasoning about actions and change, including new ramification '
                          'constraints for indirect effects. State-of-the-art models struggle across all '
                          'dimensions, especially ramifications.',
                 tag_keys=['Reasoning', 'Evaluation']),
            dict(title='Hypothesis Generation for Materials Discovery and Design Using '
                       'Goal-Driven and Constraint-Guided LLM Agents',
                 slug='hypothesis-generation-materials',
                 tldr='Goal-driven, constraint-guided LLM agents that generate materials-science hypotheses.',
                 authors='Shrinidhi Kumbhar, Venkatesh Mishra, Kevin Coutinho, Divij Handa, '
                         'Ashif Iquebal, Chitta Baral',
                 venue='Findings of NAACL 2025', year=2025, month=4, kind=P.CONFERENCE, stage=S.TEST_TIME,
                 abstract='Goal-driven, constraint-guided LLM agents that generate scientific hypotheses for '
                          'materials discovery and design.',
                 tag_keys=['Agents']),
            # 2023
            dict(title='Can NLP Models Correctly Reason Over Contexts That Break the Common Assumptions?',
                 slug='reasoning-broken-assumptions',
                 tldr='Models reason well — until you break the common assumptions behind a context.',
                 authors='Neeraj Varshney, Mihir Parmar, Nisarg Patel, Divij Handa, '
                         'Sayantan Sarkar, Man Luo, Chitta Baral',
                 venue='arXiv preprint', year=2023, month=5, kind=P.PREPRINT, stage=S.EVAL_SAFETY,
                 arxiv_url='https://arxiv.org/abs/2305.12096',
                 abstract='Systematically constructs contexts that break common assumptions and shows that, '
                          'while models reason well over assumption-following contexts, performance drops by '
                          'up to 20% when those assumptions are broken.',
                 tag_keys=['Reasoning']),
        ]

        for p in pubs:
            tag_keys = p.pop('tag_keys')
            obj = models.Publication.objects.create(**p)
            obj.tags.set([tags[k] for k in tag_keys])

        # Long-form page bodies live next to this command (seed_content/<slug>_body.html)
        content_dir = pathlib.Path(__file__).resolve().parent / 'seed_content'
        for f in content_dir.glob('*_body.html') if content_dir.exists() else []:
            slug = f.name[:-len('_body.html')]
            models.Publication.objects.filter(slug=slug).update(body=f.read_text())
        self.stdout.write(self.style.SUCCESS(f'✓ {len(pubs)} publications'))

        # ---- News (paper acceptances) -----------------------------------
        models.News.objects.all().delete()
        news = [
            (datetime.date(2026, 1, 22), 'GuidedSampling accepted at ICLR 2026.',
             'https://openreview.net/forum?id=TD9jC48sts'),
            (datetime.date(2025, 10, 1), 'Work on jailbreaking LLMs via novel ciphers accepted at the '
             'NeurIPS 2025 Workshop on Reliable ML from Unreliable Data.', 'https://openreview.net/forum?id=7ddhbe1YyX'),
            (datetime.date(2025, 8, 20), 'ThinkTuning accepted at EMNLP 2025.', 'https://arxiv.org/abs/2508.07616'),
            (datetime.date(2025, 5, 15), 'UnSeenTimeQA accepted at ACL 2025.', 'https://arxiv.org/abs/2407.03525'),
            (datetime.date(2025, 1, 22), 'ActionReasoningBench accepted at ICLR 2025.',
             'https://arxiv.org/abs/2406.04046'),
        ]
        for d, content, url in news:
            models.News.objects.create(date=d, content=content, url=url)
        self.stdout.write(self.style.SUCCESS(f'✓ {len(news)} news items'))

        # ---- Experience (top three from CV; Nagarro roles are older, kept as-is) --
        models.Experience.objects.all().delete()
        experiences = [
            ('Adobe', 'Research Scientist Intern', 'College Park, MD', 'May 2026', 'Aug 2026',
             'Building a multi-agent system that turns any uploaded document into an interactive webpage, '
             'and an optimization pipeline that autonomously improves multi-agent systems — tuning their '
             'context, topology, harness, cost, and latency.'),
            ('Etsy', 'AI Research Intern', 'Brooklyn, NY', 'May 2025', 'Aug 2025',
             'Designed an agentic framework for e-commerce query rewriting via a genetic algorithm (OptAgent), '
             'using a multi-agent shopper simulation for offline semantic evaluation — a 3.28% gain over '
             'test-time baselines. Scaled data collection and analysis over large query logs with BigQuery.'),
            ('Arizona State University', 'Research Assistant', 'Tempe, AZ', 'Jan 2024', 'Present',
             'Built an LLM system translating decompiler output into high-level source code for reverse '
             'engineering; fine-tuned with SFT + RL (GRPO) and a graph-edit-distance reward for structural '
             'fidelity, achieving a 2.75× improvement on held-out repositories.'),
            ('Arizona State University', 'Graduate Teaching Assistant', 'Tempe, AZ', 'Aug 2022', 'May 2023',
             'Teaching assistant for graduate machine-learning coursework.'),
            ('Nagarro', 'Associate Engineer', 'Gurugram, India', 'Oct 2020', 'Apr 2021',
             'Built and maintained enterprise web applications.'),
            ('Nagarro', 'Software Engineering Intern', 'Gurugram, India', 'Jun 2019', 'Aug 2019',
             'Full-stack web development internship.'),
        ]
        for i, (company, title, loc, start, end, desc) in enumerate(experiences):
            models.Experience.objects.create(
                company_name=company, job_title=title, location=loc,
                start_date=start, end_date=end, job_description=desc, order=i)
        self.stdout.write(self.style.SUCCESS(f'✓ {len(experiences)} experiences'))

        self.stdout.write(self.style.SUCCESS('\nDone — real content loaded from Google Scholar.'))
