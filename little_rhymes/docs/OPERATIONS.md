# Operating Little Rhymes

## Publish responsibly

Keep text, artwork, audio and video sources in each poem’s rights statement. Check that the license covers display, playback, distribution and any translations. Original demonstration content is provided with a content license; uploaded third-party content is not automatically covered. Fluent editors should review regional-language spelling, pronunciation, reading level and local cultural context. Never translate protected content without permission.

Review the staff preview before publishing. Set a date/time in the future to schedule visibility. `status=published` plus an active language and a publication time at or before now are all required for public visibility. Scheduled records are included in the administrative “Published” count because that count represents workflow status, not current public availability.

To remove a poem quickly, return it to draft. Its public page and API detail then return 404. The original slug remains locked; do not delete/recreate or use direct ORM updates to bypass the stable-URL rule. Related entries, search, feeds and the sitemap all share the same publication filter. An S3 signed URL already issued can remain usable for up to one hour; revoke/delete the underlying object for urgent media removal and check backups/caches as appropriate.

The admin’s default model permissions apply. A staff flag alone gives no model permissions. Grant editors view/add/change poems plus related content access, and grant contact review separately. Only trusted operators should grant staff/superuser status. Use distinct accounts, unique strong passwords, and a verified MFA/SSO or access-proxy integration where needed. Do not give children accounts.

## Privacy and retention

Adults use Contact Us; children are never asked to register. Ask adults to avoid child-identifying content. Review unresolved messages regularly and mark them resolved once handled. Run `purge_contacts --days 90 --dry-run`, inspect the count, then schedule the non-dry command daily. Keep unresolved copyright/privacy requests only as long as necessary and document decisions. Restrict exports and backups containing adult messages.

Run `clearsessions` and `axes_reset_logs --age 30` as maintenance. Failed-login protections can store staff IP/username metadata. Do not publish logs. Render and your object-storage provider have their own infrastructure logging; configure access and retention there. Application form counters use keyed hashes with a 15-minute cache TTL rather than raw IP storage. Use a dedicated cache and trusted proxy settings.

## Media and storage

Uploaded names become random UUID paths. Images are verified with Pillow and uploads are restricted to trusted staff. MP3 extension/header validation does not replace a full codec scan; listen and verify rights before publishing. Add scanning/transcoding if your organization accepts files from broader contributors. Uploaded SVG/HTML is not accepted.

Serve uploaded media from a separate origin with correct Content-Type and storage access controls. Local `media/` is development-only. S3 private objects use signed URLs; these will expire, so never persist a media URL in another product as a permanent link. Expired browser tabs may need a refresh after an hour.

Django does not automatically delete old files when an upload is replaced or a record is deleted. Preserve referenced assets for recovery, then periodically inventory object storage against current database references and your retention policy. Preview deletion plans before removing objects; account for backups and any legal hold. Never delete your bucket as a shortcut.

## Availability and incidents

`/health/` performs a database query and returns a minimal 200/503 response without connection details. Monitor Redis and S3 separately: the health endpoint is not an end-to-end media/cache test. A cache outage can affect cached navigation and form submissions; repair it and examine monitoring before reopening public contact traffic.

If content is inappropriate or rights are disputed, unpublish it, review media access, and record the resolution in restricted operations records. If a credential leaks, rotate it at the provider, replace the environment value, restart/redeploy, and review access logs. Rotation of Django’s signing key invalidates sessions and signed form tokens; plan that intentionally.

If the database fails, custom 500 responses avoid querying the database again. Inspect service errors without showing exception details to visitors. Restore backups into staging before making an emergency production restoration. Keep database and media restoration aligned.

## Releases

Use pull requests, automated tests and a staging environment. CI includes PostgreSQL and Redis so portability does not depend solely on SQLite. Review generated migrations and run `makemigrations --check --dry-run`; do not generate schema migrations automatically on a production boot. Use additive schema changes before destructive follow-ups.

Run tests, deployment checks, static collection and relevant browser checks before merging. Monitor after rollout. Do not automatically run seed data on each deploy. Upgrade dependencies intentionally and review Django/Axes/Render release notes, storage configuration and security fixes.

## Search and performance

Public listings are paginated at 12 items and eager-load language/class/category data. Status/date/language/featured indexes support discovery; text search uses ORM `icontains` across a small library. For a large catalogue, measure query plans and introduce PostgreSQL trigram/full-text indexing appropriate to each writing system; do not assume English stemming works across scripts.

Navigation/settings cache lasts five minutes and is invalidated by admin changes. Public poem pages are not cached as whole responses, so draft/unpublish changes take effect immediately in application queries. WhiteNoise serves compressed, hashed static assets. Uploaded image dimensions and file size are capped; editors should still export appropriately sized WebP/JPEG thumbnails (about 960×600 or smaller) for mobile performance.

Use real mobile network tests and field Core Web Vitals measurements on the deployed domain. Do not claim a Lighthouse score or production uptime from a local test run.

## Intentional scope

No automatic poem translation, paid subscriptions, child accounts, user uploads, comments, contact-email delivery, behavioral analytics, full interface translation, or external video moderation service is included. These are not required for reading and managing the library. Optional read-aloud depends on the matching voices available on each device. Full screen-reader/device/browser and load-testing coverage remains an operator acceptance task.
