# Portfolio — divijhanda.in

A research-forward personal site for an LLM researcher, built from scratch in **Django**.
Live at [divijhanda.in](https://www.divijhanda.in).

Design: a dark/light "Latent Space" theme — an interactive neural-constellation hero,
an LLM-style token-stream tagline, an interactive agent-lifecycle stepper, and
scroll-reveal animations throughout. All content (profile, publications, research
areas, news, experience) is managed from the Django admin, so updates never require
a redeploy. The CV PDF ships in static (override it by uploading a resume in the admin).

## Pages
Home · Research · Publications (+ a page per paper) · Contact

The Home and Research pages feature an interactive **LLM-agent lifecycle** graphic
(Data Generation → Training → Test-Time → Evaluation & Safety) whose papers are driven
by each Publication's `stage` field — editable in the admin.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Local config (gitignored). For local dev a config.json with DEBUG is enough;
# SECRET_KEY falls back to a dev key if unset.
echo '{ "DEBUG": "True" }' > config.json

python manage.py migrate
python manage.py createsuperuser     # for /admin access
python manage.py seed_demo           # loads the real profile + publications from Google Scholar
python manage.py runserver
```

Open <http://127.0.0.1:8000/> and the admin at <http://127.0.0.1:8000/admin/>.

## Managing content
Everything lives under **/admin**:
- **Profile** — name, role, tagline (the hero types each `|`-separated phrase), bio,
  social links, and an optional **resume** upload (overrides the bundled static CV).
- **Publications** — each has a `stage` (lifecycle stepper), a `tldr`, a `slug` (its
  own page), and `featured` (home page) flag.
- **News / Research areas / Experience** — the rest of the page content.
- **Contact messages** — every contact-form submission is saved here (read-only);
  mark one *handled* once you've replied.

> `seed_demo` loads real content from Google Scholar (profile, 10 publications,
> news, research areas, experience). It clears and rebuilds those sections on each
> run; it never touches contact messages. After running it once, manage everything
> from the admin.

## Configuration
Settings read from environment variables first, then `config.json`, then a default:

| Key                   | Purpose                                                        |
|-----------------------|----------------------------------------------------------------|
| `SECRET_KEY`          | Django secret. **Required** when `DEBUG=False` (app won't boot without it). |
| `DEBUG`               | `True`/`False` (default `False`).                              |
| `CONTACT_EMAIL`       | Where contact-form messages are emailed (default `dhanda@asu.edu`). |
| `DEFAULT_FROM_EMAIL`  | From address for outgoing mail.                                |
| `EMAIL_HOST`          | SMTP host. If unset, mail prints to the console (messages are still saved to the DB). |
| `EMAIL_PORT`          | SMTP port (default `587`).                                     |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | SMTP credentials.                          |
| `EMAIL_USE_TLS`       | `True`/`False` (default `True`).                               |
| `STATIC_DIR`          | Name of the collectstatic output dir (default `staticfiles`); set to match your web server's `/static` alias. |
| `SECURE_SSL_REDIRECT` | `True` to force HTTPS (default `False` — enable once HTTPS is confirmed end-to-end). |
| `SECURE_HSTS_SECONDS` | HSTS max-age in seconds; `0` disables (default `0`).           |

## Contact form
Submissions are always saved to the database (**Contact messages** in the admin) and,
when SMTP is configured, also emailed to `CONTACT_EMAIL` with the sender as `Reply-To`.
Nothing is required for local dev — mail is printed to the console.

## Deployment notes
- Set a real `SECRET_KEY` and `DEBUG=False`. With `DEBUG=False`, production hardening
  turns on automatically: HTTPS redirect, HSTS, secure session/CSRF cookies, and the
  `X-Forwarded-Proto` header is trusted (for a reverse proxy / load balancer).
- `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` already include `divijhanda.in`.
- Static files are served by **WhiteNoise** (already wired). Run
  `python manage.py collectstatic`; serve with `gunicorn divijhanda.wsgi`. Uploaded
  images live under `MEDIA_ROOT` (serve it separately if you use admin uploads).
- Configure the `EMAIL_*` vars so the contact form can send mail.
- SEO: `robots.txt` and `sitemap.xml` are served at the site root.
