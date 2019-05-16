
from django import template

register = template.Library()

@register.inclusion_tag('Paging.html')
def custom(page_obj):
    page_info = page_obj
    return {'page_list': page_info}


