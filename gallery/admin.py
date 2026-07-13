# gallery/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import ImageUpload

logger = __import__('logging').getLogger(__name__)


class ImageUploadAdmin(admin.ModelAdmin):
    list_display = ('title', 'partner', 'image_preview', 'uploaded_at')
    list_display_links = ('title',)
    search_fields = ('title', 'description')
    list_filter = ('partner', 'uploaded_at')
    readonly_fields = ('uploaded_at',)
    ordering = ('-uploaded_at',)
    autocomplete_fields = ['partner']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = getattr(request, 'user', None)
        if user and user.is_authenticated and not user.is_superuser:
            allowed_partners = getattr(user, 'user_partners', set())
            if allowed_partners:
                return qs.filter(partner__in=allowed_partners)
            return qs.none()
        return qs

    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'description', 'partner')
        }),
        ('Imagen', {
            'fields': ('image',),
        }),
        ('Metadata', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        """Show image preview in list view."""
        if obj.image:
            try:
                return format_html(
                    '<div style="pointer-events:none;">'
                    '<img src="{}" style="max-height: 50px; max-width: 50px; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);pointer-events:none;cursor:default;" alt="" role="presentation" />'
                    '<br><small style="color: #666;pointer-events:none;">{}</small>'
                    '</div>',
                    obj.image.url,
                    obj.title[:20]
                )
            except Exception:
                return format_html('<span style="color: #dc3545;">Error loading image</span>')
        return format_html('<span style="color: #6c757d;">No image</span>')
    image_preview.short_description = 'Image Preview'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        logger.info(f"Image '{obj.title}' was {'updated' if change else 'uploaded'} by {request.user}")


admin.site.register(ImageUpload, ImageUploadAdmin)
