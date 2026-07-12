# partners/middleware.py
from django.utils.deprecation import MiddlewareMixin
from partners.models import Partner


class PartnerContextMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated and not request.user.is_superuser:
            request.user_partners = {
                pu.partner for pu in request.user.partner_memberships.select_related('partner')
            }
        else:
            request.user_partners = Partner.objects.all()
