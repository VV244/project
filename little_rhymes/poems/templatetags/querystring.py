from django import template
register = template.Library()

@register.simple_tag(takes_context=True)
def replace_query(context, **kwargs):
    query = context['request'].GET.copy()
    query.update(kwargs)
    return query.urlencode()
