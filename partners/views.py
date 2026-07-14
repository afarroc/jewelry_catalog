# partners/views.py
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from home.models import Banner
from home.hero_utils import build_hero_from_banners, TIENDAS_HERO_DEFAULTS
from .models import Partner


class PartnerListView(ListView):
    """Directorio público de tiendas (vitrina).

    La vitrina es pública para todos los visitantes (anónimos o logueados),
    sin importar la membresía: un cliente normal logueado debe poder descubrir
    y navegar todas las tiendas activas. El aislamiento por membresía corresponde
    al dashboard privado del partner (Fase 2) y al admin de Product/ImageUpload,
    no a la vitrina pública.
    """
    model = Partner
    template_name = 'partners/list.html'
    context_object_name = 'partners'

    def get_queryset(self):
        return Partner.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_tiendas_banners = Banner.objects.filter(is_active=True, page='tiendas').order_by('order', '-created_at')
        context['hero'] = build_hero_from_banners(active_tiendas_banners, TIENDAS_HERO_DEFAULTS)
        return context


class PartnerDetailView(DetailView):
    model = Partner
    template_name = 'partners/detail.html'
    context_object_name = 'partner'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        # Vitrina pública: cualquier visitante ve cualquier tienda activa.
        return Partner.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        partner = self.object
        context['products'] = partner.products.filter(available=True)
        return context
