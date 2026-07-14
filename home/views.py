# home/views.py
from django.shortcuts import render
from django.views.generic import TemplateView
from products.models import Product, Category
from products.grid_packer import pack_products
from products.grid_items import GenericSlot
from partners.models import Partner
from .models import Banner, SocialMedia
from .hero_utils import build_hero_from_banners, HOME_HERO_DEFAULTS
import logging

logger = logging.getLogger(__name__)


def index(request):
    """Home global: hero Miluxious + trust bar + categorías + partners + best-sellers + reel CTA."""
    context = {
        'title': 'Miluxious accesorios',
        'welcome_message': '¡Bienvenido a nuestra colección de Miluxious accesorios!',
        'user': getattr(request, 'user', None),
    }

    try:
        active_banners = Banner.objects.filter(is_active=True).order_by('order', '-created_at')
        active_social_media = SocialMedia.objects.filter(is_active=True).order_by('order', 'platform')
        active_categories = Category.objects.filter(visible_in_index=True).order_by('index_order')[:4]

        # Productos globales (sin partner) destacados
        global_products = Product.objects.filter(available=True, partner__isnull=True).order_by('-average_rating', '-review_count', '-created_at')[:8]

        # Partners activos
        partners = Partner.objects.filter(is_active=True)

        # Hero admin-managed: prioriza SiteConfiguration/HomeConfig, fallback a primer banner
        active_home_banners = active_banners.filter(page='home')
        hero = build_hero_from_banners(active_home_banners, HOME_HERO_DEFAULTS)

        # Best-sellers globales (Miluxious)
        best_sellers = Product.objects.filter(available=True, partner__isnull=True).order_by('-review_count', '-average_rating')[:8]

        context.update({
            'banners': active_banners,
            'categories': active_categories,
            'social_media': active_social_media,
            'global_products': global_products,
            'partners': partners,
            'hero': hero,
            'best_sellers': best_sellers,
        })
    except Exception as e:
        logger.error(f"Error al obtener datos para la página de inicio global: {str(e)}")

    return render(request, 'home/index_global.html', context)



def reel(request):
    """Reel editorial: bento grid con todos los productos disponibles."""
    context = {
        'title': 'Reel — Miluxious',
    }

    try:
        active_banners = Banner.objects.filter(is_active=True).order_by('order', '-created_at')
        active_categories = Category.objects.filter(visible_in_index=True).order_by('index_order')[:4]

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

        logger.debug(f"Mostrando {len(active_banners)} banners, {len(active_categories)} categorías y {len(featured_products)} productos en reel")

        context.update({
            'banners': active_banners,
            'categories': active_categories,
            'featured_products': featured_products,
        })
    except Exception as e:
        logger.error(f"Error al obtener datos para la página de reel: {str(e)}")

    return render(request, 'home/reel.html', context)


class IndexView(TemplateView):
    """Legacy class-based view for backward compatibility."""
    template_name = 'index_editorial.html'

    def get_context_data(self, **kwargs):
        # Mantenemos compatibilidad apuntando al reel
        return reel(self.request)
