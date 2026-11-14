from ipaddress import ip_address
from django.conf import settings

def client_ip(request):
    """Use the last proxy-appended hop only on explicitly trusted Render deployments."""
    address = request.META.get('REMOTE_ADDR', '')
    if settings.TRUST_RENDER_PROXY:
        address = request.META.get('HTTP_X_FORWARDED_FOR', address).split(',')[-1].strip()
    try:
        return str(ip_address(address))
    except ValueError:
        return None
