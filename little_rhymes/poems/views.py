from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_safe

from .forms import PoemFilterForm
from .models import Poem, ClassLevel, Language, Category
from .services import filter_poems

@require_safe
def listing(request, kind=None, slug=None):
    title, description, current = 'A poem for every little wonder', 'Find a new favorite. Explore by class, language, or the things that make you smile.', None
    data = request.GET.copy()
    fixed = None
    models = {'class': (ClassLevel, 'class_level'), 'language': (Language, 'language'), 'category': (Category, 'category')}
    if kind:
        model, fixed = models[kind]
        current = get_object_or_404(model, slug=slug, is_active=True)
        data[fixed] = current.slug
        title = current.native_name if kind == 'language' else current.name
        description = f'Beautiful poems in {current.name}, made for little learners.' if kind == 'language' else current.description
    form = PoemFilterForm(data)
    if fixed:
        form.fields[fixed].disabled = True
        form.initial[fixed] = current
    poems = Poem.objects.published().with_relations()
    poems = filter_poems(poems, form.cleaned_data) if form.is_valid() else poems.none()
    page = Paginator(poems, 12).get_page(request.GET.get('page'))
    return render(request, 'poems/list.html', {
        'page_obj': page, 'filter_form': form, 'title': title, 'description': description,
        'current': current, 'kind': kind, 'fixed': fixed, 'noindex': bool(request.GET),
    })

@require_safe
def directory(request, kind):
    model, title, description = {
        'classes': (ClassLevel, 'Little steps. Big discoveries.', 'Choose a class and find poems for your learning journey.'),
        'languages': (Language, 'Many languages. One joyful world.', 'Celebrate the sounds and stories of your favorite language.'),
        'categories': (Category, 'Follow your curiosity', 'From tiny animals to faraway stars, there is a poem for that.'),
    }[kind]
    visible = Q(poems__status='published', poems__language__is_active=True, poems__published_at__lte=timezone.now())
    entries = model.objects.filter(is_active=True).annotate(poem_count=Count('poems', filter=visible, distinct=True))
    return render(request, 'poems/directory.html', {'entries': entries, 'kind': kind, 'title': title, 'description': description})

def detail_context(poem):
    visible = Poem.objects.published()
    related = visible.filter(language=poem.language).exclude(pk=poem.pk).with_relations()[:3]
    return {
        'poem': poem, 'related_poems': related,
        'previous_poem': visible.filter(pk__lt=poem.pk).order_by('-pk').only('title', 'slug').first(),
        'next_poem': visible.filter(pk__gt=poem.pk).order_by('pk').only('title', 'slug').first(),
        'title': poem.seo_title, 'description': poem.seo_description,
    }

@require_safe
def detail(request, slug):
    poem = get_object_or_404(Poem.objects.published().with_relations(), slug=slug)
    return render(request, 'poems/detail.html', detail_context(poem))

@staff_member_required
@require_safe
def preview(request, pk):
    if not (request.user.has_perm('poems.view_poem') or request.user.has_perm('poems.change_poem')):
        raise PermissionDenied
    poem = get_object_or_404(Poem.objects.with_relations(), pk=pk)
    response = render(request, 'poems/detail.html', {**detail_context(poem), 'preview': True, 'noindex': True})
    response['Cache-Control'] = 'private, no-store'
    response['X-Robots-Tag'] = 'noindex, nofollow'
    return response

@require_safe
def favorites(request):
    return render(request, 'poems/favorites.html', {'title': 'My little collection', 'noindex': True})
