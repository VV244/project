> Repository deployment: this application lives in `little_rhymes/` on the `little-rhymes-deploy` branch. Render reads `little_rhymes/render.yaml`, uses the `little_rhymes` root directory, and seeds original demo content after the first successful deployment. The root GitHub Actions workflow tests this folder with PostgreSQL and Redis.

# Little Rhymes – Learn, Sing & Grow

A complete server-rendered Django application for a multilingual children’s poetry library. Python 3.12+, Django 5.2 LTS, Bootstrap 5, Django REST Framework, PostgreSQL/SQLite, WhiteNoise and S3-compatible media. No child accounts, public comments, advertising, or external font requests.

## Quick start

Install Python 3.12 or a compatible later version, Git, and pip. Open a terminal **in this folder** (the one containing `manage.py`).

```bash
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
source .venv/bin/activate
```

Copy `.env.example` to `.env` (`Copy-Item .env.example .env` in PowerShell, `cp .env.example .env` elsewhere). The development settings use SQLite and local media. Then:

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/ and http://127.0.0.1:8000/admin/. Create your own private admin password; none is shipped. The seed command creates missing data only and preserves subsequent edits.

## What works

- Homepage with class/language discovery, editorial popular picks, featured and latest poems, resources, and FAQs.
- Dedicated class, language, and category directories and filtered pages; six class levels, 13 initial languages and 13 categories.
- Database-backed poem titles, body text, language, multiple classes/categories, author, SEO, original illustration choices, images, MP3 recordings, approved videos and permissions.
- Combined title/body/keyword/author/language/class/category search, four sorting modes, pagination, empty states, and validation.
- Large Unicode reading text, Urdu RTL, text size, uploaded audio player, optional matching device voices, click-to-load privacy-enhanced YouTube, and approved direct MP4/WebM.
- Print view, share link, previous/next poems, related language suggestions, and up to 100 local favorites.
- Authenticated admin, permission-aware statistics, content preview, search/filter controls and publish/unpublish/feature bulk actions. Failed-login protection with Django Axes.
- Adult contact form with CSRF, signed expiring form token, honeypot, shared-cache rate limits and a staff inbox. This stores messages; it does **not** send email notifications.
- Editable About, privacy, terms, copyright/removal, resources, FAQs, hero text/artwork, logo and footer.
- Canonical/OG metadata, escaped CreativeWork JSON-LD, XML sitemap, robots.txt, noindex on filtered/private pages, custom 404/500, and a DB health endpoint.
- Explicit production requirements: PostgreSQL, Redis, persistent S3 media, secret key, hosts and HTTPS site origin; startup fails if these are missing.

## Content administration

1. Add or enable a language under Languages: native name, BCP 47 code (e.g. `kok`), unique ASCII URL slug, and `ltr`/`rtl` direction. Language entries are unlimited; no code edits are required.
2. Create a poem with its language, classes, categories and text. ASCII slugs give shareable stable URLs; a unique slug is generated for non-Latin titles when omitted.
3. Use an original built-in SVG illustration or upload a JPEG/PNG/WebP up to 5 MB and 16 MP. Add MP3 up to 20 MB, and an optional video URL.
4. Record rights/attribution for **every** asset, confirm permissions, preview, and publish. A future publication time keeps content hidden until that time.
5. Once first published, the URL slug is locked, including after returning to draft. Keep its publication date; change the text/title without changing its URL. Staff ORM bulk updates must not bypass these editorial rules.

Poems in disabled languages are hidden. Inactive classes/categories disappear from browsing and tags. Initial regional-language entries without poems intentionally show an honest empty state.

Interface language is separate from poem language: the footer selector changes translated navigation labels (English/Hindi/Marathi); other English labels fall back where no translation is included. Expand `locale/*/LC_MESSAGES/django.po` using Django’s standard gettext workflow, then `python manage.py compilemessages` with GNU gettext installed. Compiled `.mo` files are included. This does not translate any poem. New content languages work immediately; a new script may need an appropriate licensed local font.

Popular picks are editorially selected using each poem’s Home priority field; featured poems are selected separately. Neither uses behavioral analytics. Class levels are editorial suggestions, not a verified curriculum. Have fluent editors review demonstration language and age suitability before a school/public launch.

## Tests and verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py collectstatic --noinput
```

Tests cover published/draft/scheduled visibility, all core routes, combined filters, Unicode/RTL, search, pagination, query bounds, APIs, permission separation, permanent URLs, database constraints, rights checks, media validation, contact spam/rate/CSRF controls, retention and idempotent seeding. See [docs/VERIFICATION.md](docs/VERIFICATION.md) for the actual handoff results and remaining external verification.

## Structure

```text
config/         environment-based settings, URL routing, WSGI/ASGI
poems/          library models, filters, views, API, admin, seed and tests
core/           site settings, pages, FAQs, SEO, headers and navigation cache
contact/        adult messages, validation, rate limiting and retention
templates/      shared shell, home, directories, poem reading and admin
static/         CSS, JS, original SVGs, local fonts and vendor licenses
demo_assets/    original-verse synthetic English narration
docs/           deployment, operations and verification
```

## API

`GET /api/poems/` returns published poems, 12 per page. Supported filters: `q`, `language=<slug>`, `class_level=<slug>`, `category=<slug>`, `sort=newest|oldest|title|featured`, `page`, and `ids=1,2` (maximum 100 IDs). `GET /api/poems/<slug>/` retrieves one public poem. Writes are disabled. Uploaded media may use expiring signed URLs; refetch metadata rather than persisting those URLs.

## Production deployment

Follow [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the complete Render, PostgreSQL, Redis, S3, GitHub, domain, HTTPS, monitoring and backup walkthrough. `render.yaml`, `Dockerfile`, `build.sh` and Gunicorn settings are included. **Render resources incur hosting costs.** No public production deployment, GitHub push, custom domain, cloud credential validation, or production media round-trip is claimed by this source deliverable.

Use [docs/OPERATIONS.md](docs/OPERATIONS.md) to maintain staff access, content rights, contact retention and backups. Public legal pages are editable starter policies: the operator must supply its real identity, contact details and applicable terms before launch.

## Licenses and maintenance

Application code: MIT. Original demo verses and vector artwork: CC0 1.0. See [LICENSE](LICENSE), [CONTENT_LICENSE.md](CONTENT_LICENSE.md) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Third-party font and speech notices are bundled; uploaded content keeps its own license.

Dependencies are pinned to the versions used for this handoff; periodically install supported security patches and rerun the tests. Framework and deployment references: [Django supported releases](https://www.djangoproject.com/download/), [Django production checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/), [Render Django deployment](https://render.com/docs/deploy-django), [Render Blueprints](https://render.com/docs/blueprint-spec), [Render plans](https://render.com/docs/compute-plans), [django-storages S3](https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html), [WhiteNoise](https://whitenoise.readthedocs.io/en/stable/django.html).
