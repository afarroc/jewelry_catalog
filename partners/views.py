# partners/views.py
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Partner


class PartnerListView(ListView):
    model = Partner
    template_name = 'partners/list.html'
    context_object_name = 'partners'

    def get_queryset(self):
        qs = Partner.objects.filter(is_active=True)
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated and not user.is_superuser:
            partner_ids = user.partner_memberships.values_list('partner_id', flat=True)
            qs = qs.filter(id__in=partner_ids)
        return qs


class PartnerDetailView(DetailView):
    model = Partner
    template_name = 'partners/detail.html'
    context_object_name = 'partner'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        qs = Partner.objects.filter(is_active=True)
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated and not user.is_superuser:
            partner_ids = user.partner_memberships.values_list('partner_id', flat=True)
            qs = qs.filter(id__in=partner_ids)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        partner = self.object
        context['products'] = partner.products.filter(available=True)
        return context
