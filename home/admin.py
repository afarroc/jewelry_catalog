from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Banner, SocialMedia
import logging

logger = logging.getLogger(__name__)


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    """
    Admin configuration for Banner model
    """
    # Campos que se muestran en la lista
    list_display = (
        'title',
        'image_filename',
        'is_active',
        'order',
        'has_button',
        'button_info',
        'created_at',
        'preview_image'
    )

    # Campos por los que se puede filtrar
    list_filter = (
        'is_active',
        'created_at',
        'updated_at',
        ('button_text', admin.EmptyFieldListFilter),
    )

    # Campos de búsqueda
    search_fields = (
        'title',
        'subtitle',
        'description',
        'image_filename'
    )

    # Campos de solo lectura
    readonly_fields = (
        'created_at',
        'updated_at',
        'preview_image_large'
    )

    # Ordenamiento por defecto
    ordering = ('order', '-created_at')

    # Configuración de los campos en el formulario
    fieldsets = (
        (None, {
            'fields': ('title', 'subtitle', 'description')
        }),
        ('Imagen', {
            'fields': ('image_filename', 'preview_image_large'),
            'description': 'El archivo de imagen debe estar ubicado en static/images/banners/'
        }),
        ('Configuración', {
            'fields': ('is_active', 'order'),
            'classes': ('collapse',)
        }),
        ('Botón de Acción', {
            'fields': ('button_text', 'button_url'),
            'classes': ('collapse',),
            'description': 'Opcional: agregar un botón de acción al banner'
        }),
        ('Información del Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Acciones personalizadas
    actions = [
        'activate_banners',
        'deactivate_banners',
        'reset_order'
    ]

    def preview_image(self, obj):
        """Mostrar miniatura de la imagen en la lista"""
        if obj.image_filename:
            return format_html(
                '<img src="{}" style="width: 60px; height: 40px; object-fit: cover; border-radius: 4px;" alt="{}">',
                obj.get_image_url,
                obj.title
            )
        return "Sin imagen"
    preview_image.short_description = "Vista Previa"

    def preview_image_large(self, obj):
        """Mostrar imagen grande en el formulario de edición"""
        if obj.image_filename:
            return format_html(
                '<img src="{}" style="max-width: 400px; max-height: 200px; object-fit: contain; border: 1px solid #ddd; border-radius: 4px;" alt="{}">',
                obj.get_image_url,
                obj.title
            )
        return format_html('<p style="color: #666; font-style: italic;">No hay imagen configurada</p>')
    preview_image_large.short_description = "Vista Previa de Imagen"

    def has_button(self, obj):
        """Mostrar si el banner tiene botón configurado"""
        return obj.has_button
    has_button.short_description = "Botón"
    has_button.boolean = True

    def button_info(self, obj):
        """Mostrar información detallada del botón"""
        if obj.has_button:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓</span> {} → {}',
                obj.button_text,
                obj.button_url
            )
        return format_html('<span style="color: #6c757d;">Sin botón</span>')
    button_info.short_description = "Información del Botón"

    def activate_banners(self, request, queryset):
        """Activar banners seleccionados"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            ngettext(
                '%d banner was successfully activated.',
                '%d banners were successfully activated.',
                updated,
            ) % updated,
        )
        logger.info(f"Activated {updated} banners by {request.user.username}")
    activate_banners.short_description = "Activar banners seleccionados"

    def deactivate_banners(self, request, queryset):
        """Desactivar banners seleccionados"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            ngettext(
                '%d banner was successfully deactivated.',
                '%d banners were successfully deactivated.',
                updated,
            ) % updated,
        )
        logger.info(f"Deactivated {updated} banners by {request.user.username}")
    deactivate_banners.short_description = "Desactivar banners seleccionados"

    def reset_order(self, request, queryset):
        """Resetear el orden de los banners"""
        updated = queryset.update(order=0)
        self.message_user(
            request,
            ngettext(
                'Order reset for %d banner.',
                'Order reset for %d banners.',
                updated,
            ) % updated,
        )
        logger.info(f"Reset order for {updated} banners by {request.user.username}")
    reset_order.short_description = "Resetear orden de banners"

    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request).select_related()

    def save_model(self, request, obj, form, change):
        """Log cuando se guarda un banner"""
        action = "updated" if change else "created"
        super().save_model(request, obj, form, change)
        logger.info(f"Banner '{obj.title}' was {action} by {request.user.username}")

    def delete_model(self, request, obj):
        """Log cuando se elimina un banner"""
        logger.info(f"Banner '{obj.title}' was deleted by {request.user.username}")
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """Log cuando se eliminan múltiples banners"""
        count = queryset.count()
        titles = list(queryset.values_list('title', flat=True))
        logger.info(f"Banners {titles} were deleted by {request.user.username}")
        super().delete_queryset(request, queryset)

    class Media:
        """Archivos CSS y JS personalizados para el admin"""
        css = {
            'all': ('css/admin/banner.css',)
        }
        js = ('js/admin/banner.js',)


@admin.register(SocialMedia)
class SocialMediaAdmin(admin.ModelAdmin):
    """
    Admin configuration for SocialMedia model
    """
    # Campos que se muestran en la lista
    list_display = (
        'name',
        'platform',
        'url',
        'is_active',
        'order',
        'display_followers',
        'platform_icon_display',
        'created_at'
    )

    # Campos por los que se puede filtrar
    list_filter = (
        'is_active',
        'platform',
        'created_at',
        'updated_at',
    )

    # Campos de búsqueda
    search_fields = (
        'name',
        'platform',
        'url'
    )

    # Campos de solo lectura
    readonly_fields = (
        'created_at',
        'updated_at',
        'platform_icon_display'
    )

    # Ordenamiento por defecto
    ordering = ('order', 'platform')

    # Configuración de los campos en el formulario
    fieldsets = (
        (None, {
            'fields': ('name', 'platform', 'url')
        }),
        ('Configuración', {
            'fields': ('is_active', 'order', 'followers_count'),
            'classes': ('collapse',)
        }),
        ('Icono', {
            'fields': ('icon_class', 'platform_icon_display'),
            'classes': ('collapse',),
            'description': 'El icono se establece automáticamente basado en la plataforma seleccionada'
        }),
        ('Información del Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Acciones personalizadas
    actions = [
        'activate_social_media',
        'deactivate_social_media',
        'reset_order'
    ]

    def platform_icon_display(self, obj):
        """Mostrar el icono de la plataforma"""
        if obj.platform_icon:
            return format_html(
                '<i class="{}" style="font-size: 24px; color: #666;"></i> <code>{}</code>',
                obj.platform_icon,
                obj.platform_icon
            )
        return "Sin icono"
    platform_icon_display.short_description = "Icono de la Plataforma"

    def display_followers(self, obj):
        """Mostrar el número de seguidores de forma legible"""
        if obj.display_followers:
            return format_html(
                '<span style="font-weight: bold; color: #28a745;">{}</span>',
                obj.display_followers
            )
        return format_html('<span style="color: #6c757d;">—</span>')
    display_followers.short_description = "Seguidores"

    def activate_social_media(self, request, queryset):
        """Activar redes sociales seleccionadas"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            ngettext(
                '%d red social was successfully activated.',
                '%d social media accounts were successfully activated.',
                updated,
            ) % updated,
        )
        logger.info(f"Activated {updated} social media accounts by {request.user.username}")
    activate_social_media.short_description = "Activar redes sociales seleccionadas"

    def deactivate_social_media(self, request, queryset):
        """Desactivar redes sociales seleccionadas"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            ngettext(
                '%d red social was successfully deactivated.',
                '%d social media accounts were successfully deactivated.',
                updated,
            ) % updated,
        )
        logger.info(f"Deactivated {updated} social media accounts by {request.user.username}")
    deactivate_social_media.short_description = "Desactivar redes sociales seleccionadas"

    def reset_order(self, request, queryset):
        """Resetear el orden de las redes sociales"""
        updated = queryset.update(order=0)
        self.message_user(
            request,
            ngettext(
                'Order reset for %d social media account.',
                'Order reset for %d social media accounts.',
                updated,
            ) % updated,
        )
        logger.info(f"Reset order for {updated} social media accounts by {request.user.username}")
    reset_order.short_description = "Resetear orden de redes sociales"

    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request).select_related()

    def save_model(self, request, obj, form, change):
        """Log cuando se guarda una red social"""
        action = "updated" if change else "created"
        super().save_model(request, obj, form, change)
        logger.info(f"Social media '{obj.name}' ({obj.platform}) was {action} by {request.user.username}")

    def delete_model(self, request, obj):
        """Log cuando se elimina una red social"""
        logger.info(f"Social media '{obj.name}' ({obj.platform}) was deleted by {request.user.username}")
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """Log cuando se eliminan múltiples redes sociales"""
        count = queryset.count()
        names = list(queryset.values_list('name', flat=True))
        logger.info(f"Social media accounts {names} were deleted by {request.user.username}")
        super().delete_queryset(request, queryset)

    class Media:
        """Archivos CSS y JS personalizados para el admin"""
        css = {
            'all': ('css/admin/social_media.css',)
        }
        js = ('js/admin/social_media.js',)
