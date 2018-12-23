from django.template.library import Library


register = Library()


level_map = {
    'info': 'text-info',
    'success': 'text-success',
    'error': 'text-danger',
    'warning': 'text-warning',
    'debug': 'text-secondary',
}


@register.filter
def level2class(value):
    return level_map.get(value, 'text-primary')
