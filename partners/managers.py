# partners/managers.py
from django.db import models


class PartnerScopedQuerySet(models.QuerySet):
    def for_user(self, user):
        if getattr(user, 'is_superuser', False):
            return self
        partners = user.partner_memberships.values_list('partner_id', flat=True)
        return self.filter(partner_id__in=partners)


class PartnerScopedManager(models.Manager):
    def get_queryset(self):
        return PartnerScopedQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user)
