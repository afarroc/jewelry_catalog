# home/views.py
from django.shortcuts import render
from django.views.generic import TemplateView
from products.models import Product, Category
from products.grid_packer import pack_products
from products.grid_items import GenericSlot
from .models import Banner, SocialMedia
import logging

logger = logging.getLogger(__name__)


class IndexView(TemplateView):
    """Class-based view for the home page."""
    template_name = 'index_editorial.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            # Obtener banners activos ordenados por prioridad
            active_banners = Banner.objects.filter(is_active=True).order_by('order', '-created_at')

            # Obtener redes sociales activas ordenadas por prioridad
            active_social_media = SocialMedia.objects.filter(is_active=True).order_by('order', 'platform')

            # Obtener categorías activas
            active_categories = Category.objects.filter(visible_in_index=True).order_by('index_order')[:4]

            # Obtener productos destacados por mejor rating/review_count primero
            featured_products = Product.objects.filter(available=True).order_by('-average_rating', '-review_count', '-created_at')
            heroes = list(featured_products.filter(bento_size='hero')[:2])
            featured_bucket = list(featured_products.filter(bento_size='featured')[:2])
            others_qs = featured_products.exclude(bento_size__in=['hero', 'featured'])
            others = list(others_qs[:max(0, 16 - len(heroes) - len(featured_bucket))])
            ranked = sorted(
                heroes + featured_bucket + others,
                key=lambda p: (-p.average_rating, -p.review_count)
            )[:16]
            mandatory_slots = [
                GenericSlot(slot_type='ad', label='Oferta especial', icon='fas fa-tag', url='#oferta', style='accent'),
                GenericSlot(slot_type='icon_grid', label='Servicios', icon='fas fa-gem', url='#servicios', style='neutral'),
            ]
            ranked = ranked + mandatory_slots
            ranked_ids = {p.id for p in ranked if hasattr(p, 'id')}
            filler_products = list(
                Product.objects.exclude(id__in=ranked_ids)
                .filter(image__isnull=False)
                .exclude(image='')
                .order_by('-created_at')[:100])
            generic_slots = [
                GenericSlot(slot_type='subscription', label='Newsletter', icon='fas fa-envelope', url='#', style='accent'),
                GenericSlot(slot_type='section_buttons', label='Categorías', icon='fas fa-th-large', url='#categorias', style='neutral'),
            ]
            filler_pool = filler_products + generic_slots
            placements = pack_products(ranked, columns=6, filler_pool=filler_pool)
            products_out = [product for _, _, _, _, product in placements]
            mandatory_set = set(mandatory_slots)
            for slot in mandatory_slots:
                if slot not in products_out[:18]:
                    for i in range(min(18, len(products_out)) - 1, -1, -1):
                        if products_out[i] not in mandatory_set:
                            products_out[i] = slot
                            break
            featured_products = products_out[:18]

            logger.debug(f"Mostrando {len(active_banners)} banners, {len(active_categories)} categorías y {len(featured_products)} productos")

        except Exception as e:
            active_banners = []
            active_categories = []
            featured_products = []
            logger.error(f"Error al obtener datos para la página de inicio: {str(e)}")

        context.update({
            'title': 'Miluxious accesorios',
            'welcome_message': '¡Bienvenido a nuestra colección de Miluxious accesorios!',
            'banners': active_banners,
            'categories': active_categories,
            'featured_products': featured_products,
            'social_media': active_social_media,
        })

        return context


def index(request):
    """Legacy function-based view for backward compatibility."""
    view = IndexView.as_view()
    return view(request)