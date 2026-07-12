# partners/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Partner, PartnerUser


class PartnerUserInline(admin.TabularInline):
    model = PartnerUser
    extra = 1
    autocomplete_fields = ['user']
    fields = ['user', 'role', 'can_manage_products', 'can_manage_images', 'can_manage_orders', 'assigned_at']
    readonly_fields = ['assigned_at']


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'commission_rate', 'created_at', 'updated_at')
    list_display_links = ('name',)
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active', 'commission_rate')
    inlines = [PartnerUserInline]
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Branding', {
            'fields': ('hero_image',),
        }),
        ('Configuración', {
            'fields': ('is_active', 'commission_rate')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PartnerUser)
class PartnerUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'partner', 'role', 'can_manage_products', 'can_manage_images', 'can_manage_orders', 'assigned_at')
    list_display_links = ('user',)
    list_filter = ('partner', 'role', 'can_manage_products', 'can_manage_images', 'can_manage_orders')
    search_fields = ('user__username', 'partner__name')
    autocomplete_fields = ['user', 'partner']
    readonly_fields = ('assigned_at',)
