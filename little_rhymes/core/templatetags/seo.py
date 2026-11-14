import json
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag(takes_context=True)
def structured_data(context):
    poem = context.get('poem')
    if poem:
        data = {'@context': 'https://schema.org', '@type': 'CreativeWork',
                'name': poem.title, 'text': poem.poem_text, 'inLanguage': poem.language.code,
                'url': settings.SITE_URL + poem.get_absolute_url(),
                'description': poem.seo_description, 'isAccessibleForFree': True,
                'dateModified': poem.updated_at.isoformat(),
                'audience': {'@type': 'EducationalAudience', 'educationalRole': 'student'}}
        if poem.author:
            data['creditText'] = poem.author
    else:
        data = {'@context': 'https://schema.org', '@type': 'WebSite', 'name': 'Little Rhymes',
                'url': settings.SITE_URL, 'description': 'Multilingual poems for little learners.'}
    # Escape HTML delimiters so arbitrary poem text cannot close the script tag.
    return mark_safe(json.dumps(data, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026'))
