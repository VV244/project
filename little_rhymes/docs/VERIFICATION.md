# Verification record

Verified on 14 November 2026 with Python 3.12.14 and the pinned application dependencies. This records completed checks rather than promising unperformed cloud tests.

| Check | Observed result |
| --- | --- |
| Django system check | Pass: no issues |
| Migration drift check | Pass: no changes detected |
| Automated Django tests | **73 passed**, including core routing, models, admin, API, contact and production startup validation |
| Fresh archive installation | Extracted source into a clean folder; installed only pinned requirements in a new virtual environment; migrations, repeated seeding, all 73 tests and static collection passed |
| Dependency compatibility | `pip check`: no broken requirements |
| Local migrations | All Django, Axes, core, poems and contact migrations applied successfully |
| Demo seed | 16 poems, 13 languages, 6 classes, 13 categories; repeat seed preserves edits |
| Production static collection | Pass with DEBUG false and compressed-manifest WhiteNoise storage; fingerprinted/compressed assets generated |
| Deployment security checks | No errors; two visible Django advisories for optional HSTS subdomain coverage and preload |
| Gunicorn configuration | `gunicorn config.wsgi:application --config gunicorn.conf.py --check-config` passed |
| Public listing query bound | Automated regression test enforces at most 7 queries for 12 cards with multiple classes/categories, with navigation cache warm |
| Desktop browser | Homepage rendered; original hero artwork and all 13 page images loaded without missing assets; no horizontal overflow |
| Combined filters in browser | Marathi + Junior KG + Nature returned the expected two poems |
| Local favorites in browser | Saved a Marathi poem and confirmed it appeared in the browser-local collection |
| Responsive menu | Open/close navigation verified at an effective 545 CSS-pixel browser viewport using native browser zoom |
| Narrow Urdu page | Verified at 340 CSS pixels, no horizontal overflow; RTL direction and Noto Nastaliq Urdu confirmed; joined Urdu text rendered in the reading panel |
| Uploaded sample MP3 | Playback started without media error; observed duration 11.685 seconds |
| Adjustable reading text | Slider changed computed poem text size from 26px to 30px |
| Device read-aloud fallback | Browser had no matching installed voice; the page displayed the explanatory fallback and hid the unavailable control |

The browser’s device-emulation DevTools are unavailable in this environment. Narrow-width checks above used normal browser zoom and responsive layout inspection, not a physical phone or device emulator.

## HSTS advisories

`SECURE_HSTS_SECONDS` is enabled in production. `HSTS_INCLUDE_SUBDOMAINS` and `HSTS_PRELOAD` default to false because the operator has not verified HTTPS on every affected subdomain or chosen preload enrollment. Django reports `security.W005` and `security.W021` for these choices. They are visible and documented; the build fails on actual deployment errors. Enable the corresponding options only after checking the domain configuration.

## Tests that require your real infrastructure

- Production PostgreSQL and Redis connectivity/load behavior. A GitHub Actions workflow with isolated PostgreSQL/Redis services is included but has not been run remotely in this workspace.
- Render Blueprint application, build rollout, HTTPS certificate, custom DNS/domain and a verified public production URL.
- A real private S3-compatible bucket, least-privilege credentials, upload/read/seek after redeployment, CORS and backup restoration.
- Docker image build/run (no Docker engine is available here).
- A permissioned, age-appropriate external video and its provider behavior. No unverified video is included in seed data.
- A working matching device voice for each target language and supported phone/browser/screen-reader combinations.
- Physical mobile-device, production load, field Core Web Vitals, uptime, restore drills, and jurisdiction-specific operator policy approval.

Production settings and static collection were checked with non-live validation values. No claim of actual cloud connections or public deployment is made. Do not expose the application publicly until real infrastructure and the operator’s content/contact policies have been verified.
