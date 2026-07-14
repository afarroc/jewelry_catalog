# partners/models.py
import uuid
import logging
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from cloudinary.models import CloudinaryField


logger = logging.getLogger(__name__)


class Partner(models.Model):
    """
    Socio/proveedor que vende dentro del ecosistema Miluxious.
    Cada partner tiene su propia tienda pública en /tiendas/<slug>/
    y sus usuarios administradores gestionan solo sus productos e imágenes.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text='Nombre público de la tienda del socio')
    slug = models.SlugField(max_length=200, unique=True, help_text='URL: /tiendas/<slug>/')
    description = models.TextField(blank=True, help_text='Descripción de la tienda del socio')
    hero_image = CloudinaryField(
        'image',
        folder='partners/hero',
        blank=True,
        null=True,
        help_text='Banner/imagen hero de la tienda del socio'
    )
    is_active = models.BooleanField(default=True, help_text='Si está activo, se muestra en el directorio')
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text='Comisión sobre ventas (0-100). Postergado para payouts.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Partner'
        verbose_name_plural = 'Partners'

    def __str__(self):
        return self.name

    def clean(self):
        if self.commission_rate < 0 or self.commission_rate > 100:
            raise ValidationError('La comisión debe estar entre 0 y 100.')

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def get_hero_image_url(self):
        """Return image URL for display - aligned with Product.get_image_url."""
        img = self.hero_image
        if not img or not getattr(img, 'public_id', None):
            return ''
        try:
            return img.url or ''
        except Exception:
            return ''


class PartnerUser(models.Model):
    """
    Tabla intermedia: usuario asignado a un partner con rol y permisos granulares.
    Un usuario puede pertenecer a múltiples partners con roles diferentes.
    """
    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('editor', 'Editor'),
        ('viewer', 'Viewer'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='partner_memberships'
    )
    partner = models.ForeignKey(
        Partner,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    can_manage_products = models.BooleanField(default=False, help_text='Puede crear/editar/eliminar productos')
    can_manage_images = models.BooleanField(default=False, help_text='Puede subir/editar/eliminar imágenes')
    can_manage_orders = models.BooleanField(default=False, help_text='Puede ver/ gestionar órdenes del partner')
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['user', 'partner']]
        ordering = ['partner', 'role']
        verbose_name = 'Partner User'
        verbose_name_plural = 'Partner Users'

    def __str__(self):
        return f"{self.user.username} → {self.partner.name} ({self.role})"

    def clean(self):
        # Manager implícitamente tiene todos los permisos
        if self.role == 'manager':
            self.can_manage_products = True
            self.can_manage_images = True
            self.can_manage_orders = True
