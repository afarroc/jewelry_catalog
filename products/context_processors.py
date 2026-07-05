# products/context_processors.py
from .models import Category

def categories(request):
    """Make categories available to all templates."""
    return {
        'categories': Category.objects.filter(visible_in_index=True).order_by('index_order')
    }