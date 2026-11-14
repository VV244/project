import secrets
from django.conf import settings

class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.csp_nonce = secrets.token_urlsafe(24)
        response = self.get_response(request)
        media = ' '.join(settings.MEDIA_ORIGINS)
        # Django admin needs its own inline styles/scripts; keep public pages strict.
        if not request.path.startswith('/admin/'):
            response['Content-Security-Policy'] = (
                f"default-src 'self'; script-src 'self' 'nonce-{request.csp_nonce}'; style-src 'self'; "
                f"img-src 'self' data: {media}; font-src 'self'; "
                f"media-src 'self' {media}; connect-src 'self'; "
                "frame-src https://www.youtube-nocookie.com; object-src 'none'; "
                "base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
            )
        response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=(), payment=(), browsing-topics=()'
        if request.path.startswith(('/admin/', '/contact/')):
            response['X-Robots-Tag'] = 'noindex, nofollow'
        return response
