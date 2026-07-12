# partners/permissions.py
from rest_framework import permissions


class IsPartnerManager(permissions.BasePermission):
    """
    Permite acceso si el usuario es superuser o manager del partner indicado.
    El partner_id puede venir de kwargs, query_params o data.
    """

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        partner_id = (
            view.kwargs.get('partner_id')
            or view.kwargs.get('slug')
            or request.data.get('partner')
        )
        if not partner_id:
            return False
        return request.user.partner_memberships.filter(
            partner_id=partner_id,
            role__in=['manager', 'owner'],
            can_manage_products=True
        ).exists()


class IsPartnerEditor(permissions.BasePermission):
    """
    Permite acceso si el usuario es superuser o tiene rol editor/manager/owner del partner.
    """

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        partner_id = (
            view.kwargs.get('partner_id')
            or view.kwargs.get('slug')
            or request.data.get('partner')
        )
        if not partner_id:
            return False
        return request.user.partner_memberships.filter(
            partner_id=partner_id,
            role__in=['editor', 'manager', 'owner'],
            can_manage_products=True
        ).exists()
