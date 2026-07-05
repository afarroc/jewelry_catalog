# products/admin.py
from django.contrib import admin
from django.forms import ModelForm
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from adminsortable2.admin import SortableAdminMixin
from .models import Category, Product, ImageUpload
import logging

logger = logging.getLogger(__name__)

class CategoryAdmin(SortableAdminMixin, admin.ModelAdmin):
    ordering_field = 'index_order'
    list_display = ('name', 'slug', 'index_order', 'visible_in_index', 'created_at')
    list_display_links = ('name',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('visible_in_index', 'index_order')
    list_filter = ('visible_in_index',)
    ordering = ('index_order',)

    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Visualización en Index', {
            'fields': ('visible_in_index', 'index_order'),
            'description': 'Configuración para mostrar esta categoría en el index y header del sitio.'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

    @admin.action(description='Renumerar categorías secuencialmente (1, 2, 3...) sin huecos')
    def renumber_categories_sequentially(self, request, queryset):
        categories = list(Category.objects.all().order_by('index_order', 'name'))
        for index, category in enumerate(categories, start=1):
            Category.objects.filter(pk=category.pk).update(index_order=index)
        self.message_user(request, f'{len(categories)} categorías reordenadas secuencialmente.')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        logger.info(f"Category '{obj.name}' was {'updated' if change else 'created'} by {request.user}")

class ProductAdminForm(ModelForm):
    """Custom form for Product admin to handle file uploads."""

    class Meta:
        model = Product
        fields = '__all__'

class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ('name', 'jewelry_type', 'material', 'price', 'stock', 'available', 'bento_size', 'image_preview', 'created_at')
    list_display_links = ('name', 'image_preview')
    list_filter = ('available', 'jewelry_type', 'material', 'category', 'bento_size', 'created_at')
    search_fields = ('name', 'description', 'slug', 'bento_size')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('price', 'stock', 'available', 'bento_size')
    readonly_fields = ('created_at', 'updated_at', 'image_preview_large')
    ordering = ('-created_at',)
    list_per_page = 25

    # Actions en lote
    actions = ['make_available', 'make_unavailable', 'export_csv']

    def make_available(self, request, queryset):
        updated = queryset.update(available=True)
        self.message_user(request, f'{updated} productos marcados como disponibles.')
    make_available.short_description = 'Marcar productos como disponibles'

    def make_unavailable(self, request, queryset):
        updated = queryset.update(available=False)
        self.message_user(request, f'{updated} productos marcados como no disponibles.')
    make_unavailable.short_description = 'Marcar productos como no disponibles'

    def export_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="productos.csv"'

        writer = csv.writer(response)
        writer.writerow(['Nombre', 'Tipo', 'Material', 'Precio', 'Stock', 'Disponible'])

        for product in queryset:
            writer.writerow([
                product.name,
                product.get_jewelry_type_display(),
                product.get_material_display(),
                product.price,
                product.stock,
                'Sí' if product.available else 'No'
            ])

        self.message_user(request, f'Exportados {queryset.count()} productos a CSV.')
        return response
    export_csv.short_description = 'Exportar productos a CSV'

    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Características', {
            'fields': ('jewelry_type', 'material', 'category')
        }),
        ('Imagen', {
            'fields': ('image', 'image_preview_large'),
            'classes': ('collapse',)
        }),
        ('Inventario y Precio', {
            'fields': ('price', 'stock', 'available')
        }),
        ('Home Bento', {
            'fields': ('bento_size',),
            'description': 'Elige cómo se muestra este producto en la sección destacada de la home.'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        """Show image preview in list view."""
        if obj.image:
            try:
                return format_html(
                    '<div style="text-align: center;">'
                    '<img src="{}" style="max-height: 50px; max-width: 50px; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />'
                    '<br><small style="color: #666;">{}</small>'
                    '</div>',
                    obj.get_image_url,
                    obj.name[:20]
                )
            except Exception:
                return format_html('<span style="color: #dc3545;">Error loading image</span>')
        return format_html('<span style="color: #6c757d;">No image</span>')
    image_preview.short_description = 'Image Preview'

    def image_preview_large(self, obj):
        """Show image preview in edit form."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 400px; max-height: 200px; object-fit: contain; border: 1px solid #ddd; border-radius: 4px;" alt="{}">',
                obj.get_image_url,
                obj.name
            )
        return format_html('<p style="color: #666; font-style: italic;">No hay imagen configurada</p>')
    image_preview_large.short_description = 'Vista Previa de Imagen'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        logger.info(f"Product '{obj.name}' was {'updated' if change else 'created'} by {request.user}")

class ImageUploadAdmin(admin.ModelAdmin):
    list_display = ('title', 'image_preview', 'uploaded_at')
    list_display_links = ('title', 'image_preview')
    search_fields = ('title', 'description')
    readonly_fields = ('uploaded_at',)
    ordering = ('-uploaded_at',)

    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'description')
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
                    '<div style="text-align: center;">'
                    '<img src="{}" style="max-height: 50px; max-width: 50px; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />'
                    '<br><small style="color: #666;">{}</small>'
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


admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ImageUpload, ImageUploadAdmin)