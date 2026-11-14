from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.utils.crypto import salted_hmac
from django.views.decorators.http import require_http_methods
from .forms import ContactForm
from core.security import client_ip

def rate_limited(request):
    address = client_ip(request) or 'unknown'
    key = 'contact:' + salted_hmac('contact-rate', address).hexdigest()
    if cache.add(key, 1, timeout=settings.CONTACT_RATE_WINDOW):
        return False
    try:
        return cache.incr(key) > settings.CONTACT_RATE_LIMIT
    except ValueError:
        cache.set(key, 1, timeout=settings.CONTACT_RATE_WINDOW)
        return False

@require_http_methods(['GET', 'POST'])
def contact(request):
    form = ContactForm(request.POST if request.method == 'POST' else None)
    status = 200
    if request.method == 'POST':
        if rate_limited(request):
            form.add_error(None, 'Too many attempts. Please try again in 15 minutes.')
            status = 429
        elif form.is_valid():
            form.save()
            messages.success(request, 'Thank you! Your message is with our team. We’ll reply to the email you provided.')
            return redirect('contact')
        else:
            status = 400
    response = render(request, 'contact/form.html', {'form': form, 'title': 'Hello, grown-ups!', 'description': 'Questions, ideas, or a little feedback? We would love to hear from parents and educators.'}, status=status)
    response['Cache-Control'] = 'no-store'
    if status == 429:
        response['Retry-After'] = str(settings.CONTACT_RATE_WINDOW)
    return response
