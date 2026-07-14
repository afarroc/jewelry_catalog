# partners/admin.py
import logging
from django.contrib import admin
from django.utils.html import format_html
from .models import Partner, PartnerUser

logger = logging.getLogger(__name__)


class PartnerUserInline(admin.TabularInline):
    model = PartnerUser
    extra = 1
    autocomplete_fields = ['user']
    fields = ['user', 'role', 'can_manage_products', 'can_manage_images', 'can_manage_orders', 'assigned_at']
    readonly_fields = ['assigned_at']


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'commission_rate', 'hero_image_preview', 'created_at', 'updated_at')
    list_display_links = ('name',)
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active', 'commission_rate')
    inlines = [PartnerUserInline]
    readonly_fields = ('created_at', 'updated_at', 'hero_image_preview_large')

    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Branding', {
            'fields': ('hero_image', 'hero_image_preview_large'),
        }),
        ('Configuración', {
            'fields': ('is_active', 'commission_rate')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def hero_image_preview(self, obj):
        """Mostrar miniatura de la imagen hero en la lista"""
        if obj.get_hero_image_url:
            try:
                return format_html(
                    '<img src="{}" style="width: 60px; height: 40px; object-fit: cover; border-radius: 4px;" alt="{}">',
                    obj.get_hero_image_url,
                    obj.name
                )
            except Exception:
                return format_html('<span style="color: #dc3545;">Error</span>')
        return format_html('<span style="color: #6c757d;">Sin imagen</span>')
    hero_image_preview.short_description = "Hero"

    def hero_image_preview_large(self, obj):
        """Mostrar imagen grande en el formulario de edición"""
        if obj.get_hero_image_url:
            try:
                return format_html(
                    '<img src="{}" style="max-width: 400px; max-height: 200px; object-fit: contain; border: 1px solid #ddd; border-radius: 4px;" alt="{}">',
                    obj.get_hero_image_url,
                    obj.name
                )
            except Exception:
                return format_html('<span style="color: #dc3545;">Error loading image</span>')
        return format_html('<p style="color: #666; font-style: italic;">No hay imagen configurada</p>')
    hero_image_preview_large.short_description = "Vista Previa de Imagen Hero"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        logger.info(f"Partner '{obj.name}' was {'updated' if change else 'created'} by {request.user.username}")


@admin.register(PartnerUser)
class PartnerUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'partner', 'role', 'can_manage_products', 'can_manage_images', 'can_manage_orders', 'assigned_at')
    list_display_links = ('user',)
    list_filter = ('partner', 'role', 'can_manage_products', 'can_manage_images', 'can_manage_orders')
    search_fields = ('user__username', 'partner__name')
    autocomplete_fields = ['user', 'partner']
    readonly_fields = ('assigned_at',)
