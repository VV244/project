# Deployment guide: GitHub + Render + PostgreSQL + Redis + S3

This guide deploys the actual Django application. The source archive is not a live deployment. The supplied Blueprint creates **paid** infrastructure; review Render’s current plans first. Use your own Render/GitHub accounts, domain and cloud storage credentials.

## 1. Install the tools

Install Python 3.12+ from python.org, Git from git-scm.com, and a code editor. Enable Python on PATH when using Windows. Confirm `python --version`, `python -m pip --version` and `git --version`. Python 3.12.14 was used for the packaged verification.

## 2. Create a virtual environment

Extract the archive. Enter the `little_rhymes` directory containing `manage.py`:

```bash
python -m venv .venv
```

Activate with `.\.venv\Scripts\Activate.ps1` in PowerShell or `source .venv/bin/activate` on Linux/macOS. If corporate PowerShell policy blocks activation, use `.\.venv\Scripts\python.exe` directly for subsequent Python commands.

## 3. Install the pinned dependencies

```bash
python -m pip install -r requirements.txt
```

`requirements.txt` pins the tested dependency set, including PostgreSQL’s binary adapter. Periodically update compatible security patches and rerun tests; a pinned file needs maintenance.

## 4. Set up the local database

Copy `.env.example` to `.env`. Keep `DEBUG=True`. Leave `DATABASE_URL` empty for SQLite. For a local PostgreSQL instance, create a UTF-8 database and dedicated role, set `DATABASE_URL=postgresql://USER:PASSWORD@127.0.0.1:5432/little_rhymes`, and use `DATABASE_SSL_REQUIRE=False` only for trusted local development. Percent-encode special characters in database URL credentials.

## 5. Run migrations and create sample content

```bash
python manage.py migrate
python manage.py seed_demo
```

Seed data includes 16 original poems across English, Hindi, Marathi and Urdu; six classes; 13 languages; 13 categories; editable information pages; FAQs; and one synthetic English MP3. It creates missing entries without overwriting existing edits. Do not use it as an import mechanism for unlicensed material.

## 6. Create the local administrator

```bash
python manage.py createsuperuser
```

Choose a unique username and a strong private password. No admin password exists in this repository. Staff accounts and Groups should receive only necessary model permissions.

## 7. Launch and test locally

```bash
python manage.py check
python manage.py test
python manage.py runserver
```

Visit http://127.0.0.1:8000/ and `/admin/`. Add a draft, preview it, publish it after recording rights, and confirm combined class/language/category filters. Test mobile layouts and a real device voice. The development server is for local use only.

## 8. Create a GitHub repository

Create a new empty **private** repository in GitHub. Do not add a license or README remotely before the initial push. Keep credentials in Git’s credential manager or GitHub CLI authentication, never in repository URLs, source files, or command history.

## 9. Commit and push the project

Run these inside the extracted project directory (replace the URL with your repository):

```bash
git init
git add .
git status
git commit -m "Build Little Rhymes multilingual Django library"
git branch -M main
git remote add origin https://github.com/YOUR-ACCOUNT/little-rhymes.git
git push -u origin main
```

Inspect staged files before committing. `.env`, local databases, uploaded media and virtual environments are ignored. Do not commit cloud keys, superuser credentials, raw database dumps, or adult contact messages. Original static assets and migrations must be committed.

## 10. Create the hosting service

In Render, connect your GitHub repository and choose **New → Blueprint**. Use the included `render.yaml`. It defines a Python web service, PostgreSQL and a shared Key Value cache in Singapore. The web service uses a paid plan so `preDeployCommand` can run migrations. You can change regions/plans together before creation.

The build installs requirements, collects static files and runs deployment checks, failing on errors. Django’s HSTS subdomain/preload advisories remain visible until you deliberately enable those domain-wide options; they do not block the build. The pre-deploy command runs migrations exactly once before rollout. Gunicorn binds Render’s `PORT` with one worker and four threads by default. Adjust concurrency after observing memory and database connections.

## 11. Connect PostgreSQL and Redis

The Blueprint references the database’s internal `connectionString` as `DATABASE_URL` and Key Value’s `connectionString` as `REDIS_URL`. Internal-only IP allowlists are configured. Keep all services in the same region. Enable database encryption in transit; the app sets `sslmode=require` when `DATABASE_SSL_REQUIRE=True`.

Redis is required in production for rate limits shared across all workers. Use a dedicated cache or isolated Redis database; never run application tests against the live cache. The Blueprint uses `noeviction` so counters are not silently evicted. Monitor memory and availability; an unavailable cache should be repaired rather than disabling rate limits.

## 12. Set production environment variables

Set these in Render’s environment dashboard, not a committed `.env`:

| Variable | Production value |
| --- | --- |
| `DEBUG` | `False` |
| `SECRET_KEY` | Unique random value of at least 50 characters, or the Blueprint-generated 256-bit base64 seed (expanded by the app for Django) |
| `SITE_URL` | Exact public HTTPS origin, e.g. `https://little-rhymes.onrender.com` |
| `ALLOWED_HOSTS` | Exact hostnames without scheme, comma-separated; no wildcard |
| `CSRF_TRUSTED_ORIGINS` | Exact HTTPS origins, comma-separated |
| `DATABASE_URL` | Internal PostgreSQL connection URL from the Blueprint |
| `DATABASE_SSL_REQUIRE` | `True` |
| `REDIS_URL` | Internal dedicated Redis/Key Value connection URL |
| `USE_S3` | `True` |
| `AWS_STORAGE_BUCKET_NAME` | Your private media bucket name |
| `AWS_S3_REGION_NAME` | Your bucket region |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Least-privilege media credentials, or supported workload identity |
| `AWS_S3_ENDPOINT_URL` | Empty for AWS S3; HTTPS endpoint for a compatible provider |
| `MEDIA_ORIGINS` | Exact HTTPS bucket/video delivery origins for CSP |
| `EXTERNAL_VIDEO_HOSTS` | Optional approved direct-video hostnames, comma-separated |
| `TRUST_RENDER_PROXY` | `True` only on Render’s trusted proxy infrastructure |
| `WEB_CONCURRENCY` | Start with `1`; tune after measuring |

`RENDER_EXTERNAL_HOSTNAME` is automatically included in allowed hosts and HTTPS trusted origins when Render supplies it. Still set `SITE_URL` correctly for canonical URLs, sharing and sitemap generation. If the assigned service hostname differs from your first choice, update these variables and redeploy. Do not enter your own custom domain until it resolves to this service.

## 13. Configure static files and persistent media

Static interface assets are deployed with the code and served through WhiteNoise with compression and fingerprinted cache names. `collectstatic` runs during the build. Fonts and illustrations are local assets; no external font service is contacted by visitors.

Create a private S3 bucket (or compatible object storage). Keep public access blocked. The application uses authenticated signed read URLs valid for one hour; media lives outside Render’s ephemeral disk. Use a dedicated origin for uploads. Grant only `s3:ListBucket` on the bucket and `s3:GetObject`, `s3:PutObject`, and `s3:DeleteObject` on the needed object prefixes. Do not grant account-level administration or publish cloud keys. Enable versioning and encryption at rest.

Set `MEDIA_ORIGINS` to the exact origins used by returned media URLs, e.g. `https://YOUR-BUCKET.s3.ap-south-1.amazonaws.com`. For S3-compatible storage, match its returned URL origin. This setting is a Content Security Policy allowlist; a working upload can still be blocked in the browser if its origin is missing.

If using direct MP4/WebM video, include its exact hostname in `EXTERNAL_VIDEO_HOSTS` and HTTPS origin in `MEDIA_ORIGINS`. Only YouTube URLs or approved direct-video hosts are accepted. A YouTube player loads after explicit user interaction; it uses `youtube-nocookie.com`, and recommendations cannot be completely removed.

For browser cross-origin media, configure bucket CORS for only your real website origin with GET/HEAD (and Range if needed by your provider). Do not permit browser uploads: uploads happen through authenticated Django Admin. Confirm content types and Range responses for MP3 playback. Remove unused permissions.

Uploaded file rules: images are JPEG/PNG/WebP up to 5 MB and 16 MP with Pillow verification; MP3 files are up to 20 MB with extension/header checks and randomized names. SVG/HTML uploads are rejected. All uploads are staff-only. Header checks are not antivirus or full media decoding; use malware scanning/transcoding if your editorial workflow needs it. Configure upstream request-size limits and retention for orphaned storage objects.

## 14. Deploy

Apply the Blueprint. Confirm the build succeeds, static collection finishes, the pre-deploy migration completes, Gunicorn starts, and Render’s `/health/` check returns 200. Production settings intentionally refuse SQLite, missing secrets, missing Redis or local-only media. Never switch DEBUG on to hide a production configuration error.

An existing deployment remains active if the pre-deploy step fails. Use forward-compatible database changes and take a database backup before destructive migrations. Roll back app code only when it remains compatible with the database schema.

## 15. Create the production administrator securely

Use Render’s authenticated web-service shell:

```bash
python manage.py createsuperuser
```

Enter a unique username, operator-controlled email and password interactively. Never store a superuser password in `render.yaml`, a build command, a fixture, or a GitHub secret just to automate initial seeding. Then, if you want demonstration content:

```bash
python manage.py seed_demo
```

This uploads the bundled sample recording to configured object storage. The Blueprint runs it once via initialDeployHook after the first successful deployment; it does not run on every rollout. Migrations themselves never create demo content. If an object upload fails during seeding, correct credentials/policy and rerun; inspect and remove any orphaned files from failed attempts.

Use staff Groups to separate content editors from contact-inbox reviewers. Test a least-privilege account. Django Axes limits repeated failed logins; recover a legitimate locked account through the authenticated shell and documented Axes reset command. Consider a separately vetted MFA/SSO integration before broad administrative access.

## 16. Verify the actual live website

- Open the exact HTTPS domain in a clean browser. Check `/health/`, `/sitemap.xml` and `/robots.txt`.
- Visit every directory, a class/language/category result, Unicode/RTL poem, About/FAQ/policy page and a nonexistent URL.
- Combine filters, search by author and native text, and navigate pagination. Confirm drafts and future poems return 404 publicly and through the API.
- Upload a real image/MP3 through admin, open them publicly, seek the MP3, redeploy, and verify those objects still load.
- Save/remove favorites, change text size, print, share, use an available device voice and verify unavailable voices are explained.
- Add an authorized video, confirm no player request occurs before Load video, then preview and supervise playback.
- Submit an adult-only test contact message, review it in admin, resolve/delete it, and confirm CSRF/rate controls. No email is sent automatically.
- Check phone/tablet/desktop navigation, keyboard focus, zoom and reduced-motion settings. Measure Core Web Vitals on the deployed origin; local checks are not field performance measurements.
- Confirm secure cookies, HTTPS redirects, security headers, no debug traces, and no missing/blocked static or media files in browser developer tools.

Only after these checks should you announce a verified live URL.

## 17. Connect a custom domain

Add your domain in Render’s Custom Domains settings. Follow the exact DNS records shown for that service, including apex/subdomain instructions. Wait for verification and DNS propagation. Add the domain to `ALLOWED_HOSTS`, add its HTTPS origin to `CSRF_TRUSTED_ORIGINS`, set `SITE_URL` to the chosen canonical origin, and update media CORS origins. Keep the Render hostname allowed until redirects and health checks are confirmed.

## 18. Enable and verify HTTPS

Render manages certificates for verified domains. Confirm HTTPS works on the final domain and HTTP redirects to HTTPS. The application enables secure cookies, HSTS and HTTPS redirects when DEBUG is false. Forwarded HTTPS headers are trusted only behind your managed proxy; do not expose Gunicorn directly to untrusted traffic. Enable HSTS subdomains/preload only after verifying HTTPS on every affected subdomain.

## 19. Backups, monitoring and maintenance

Configure PostgreSQL managed backups/point-in-time recovery according to the selected plan. Enable S3 versioning/lifecycle controls and periodic off-provider backups. Test a restore into an isolated staging database and media bucket; a backup that has never been restored is unverified.

Monitor the public HTTPS `/health/` endpoint, error logs, HTTP error rate, memory, PostgreSQL connections/storage, Redis memory, storage failures and certificate expiry. Avoid adding child-tracking analytics. Keep secrets out of error reports. Logs intentionally omit contact bodies and Gunicorn access logging is off.

Schedule daily maintenance in a trusted runner (Render cron/job or your operations system) with the same production environment:

```bash
python manage.py purge_contacts --days 90
python manage.py clearsessions
python manage.py axes_reset_logs --age 30
```

The first command removes only resolved contact messages older than 90 days; use `--dry-run` first. The Axes command removes access logs older than 30 days; verify behavior after dependency upgrades. Document who owns unresolved rights/privacy requests. See OPERATIONS.md for incident and release procedures.

## Container alternative

```bash
docker build -t little-rhymes .
docker run --env-file /secure/path/production.env -p 8000:8000 little-rhymes
```

The image runs as a non-root user. It includes static assets but no `.env`, database or uploaded media. Supply PostgreSQL/Redis/S3 settings at runtime and run `python manage.py migrate --noinput` as a separate release task using the same image/environment. Place the container behind a trusted TLS proxy and block direct public access to port 8000. The packaged Dockerfile requires actual Docker infrastructure to build/run; local Python tests alone do not verify a container deployment.

## Official references

- https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
- https://render.com/docs/deploy-django
- https://render.com/docs/blueprint-spec
- https://render.com/docs/deploys
- https://render.com/docs/compute-plans
- https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html
- https://whitenoise.readthedocs.io/en/stable/django.html
