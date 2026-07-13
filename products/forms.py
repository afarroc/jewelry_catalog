import json
import io
import time
import logging
import re
from datetime import datetime
from PIL import Image
import cloudinary.uploader
from django import forms
from django.utils.text import slugify
from .models import Category, Product

logger = logging.getLogger('products')


class ProductForm(forms.ModelForm):
    """Form for creating and editing products with image upload."""

    class Meta:
        model = Product
        fields = [
            'name', 'description', 'price', 'jewelry_type', 'material',
            'category', 'stock', 'available', 'bento_size', 'image'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción detallada del producto'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'jewelry_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'material': forms.Select(attrs={
                'class': 'form-select'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'available': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'bento_size': forms.Select(attrs={
                'class': 'form-select'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }

    crop_data = forms.CharField(widget=forms.HiddenInput(), required=False)
    gallery_image_id = forms.IntegerField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes to category field
        self.fields['category'].empty_label = "Seleccionar categoría"
        self.fields['category'].required = False

        # Add help texts
        self.fields['image'].help_text = "Formatos permitidos: JPG, PNG, GIF. Tamaño máximo recomendado: 2MB"
        self.fields['price'].help_text = "Precio en soles peruanos (S/.)"
        self.fields['stock'].help_text = "Cantidad disponible en inventario"

    def clean_price(self):
        """Validate price is positive."""
        price = self.cleaned_data.get('price')
        if price and price <= 0:
            raise forms.ValidationError("El precio debe ser mayor a cero.")
        return price

    def clean_stock(self):
        """Validate stock is not negative."""
        stock = self.cleaned_data.get('stock')
        if stock is not None and stock < 0:
            raise forms.ValidationError("El stock no puede ser negativo.")
        return stock


class ProductSearchForm(forms.Form):
    """Form for advanced product search and filtering."""

    # Search query
    q = forms.CharField(
        required=False,
        label='Buscar productos',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, descripción...',
            'autocomplete': 'off'
        })
    )

    # Category filter
    category = forms.ModelChoiceField(
        required=False,
        queryset=Category.objects.all(),
        empty_label='Todas las categorías',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # Jewelry type filter
    JEWELRY_TYPE_CHOICES = [('', 'Todos los tipos')] + list(Product.JEWELRY_TYPES)
    jewelry_type = forms.ChoiceField(
        required=False,
        choices=JEWELRY_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # Material filter
    MATERIAL_CHOICES = [('', 'Todos los materiales')] + list(Product.MATERIALS)
    material = forms.ChoiceField(
        required=False,
        choices=MATERIAL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # Price range filters
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Precio mínimo',
            'step': '0.01'
        })
    )

    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Precio máximo',
            'step': '0.01'
        })
    )

    # Availability filter
    availability = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todos'),
            ('available', 'Disponibles'),
            ('unavailable', 'No disponibles')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # Sort options
    SORT_CHOICES = [
        ('-created_at', 'Más recientes'),
        ('created_at', 'Más antiguos'),
        ('name', 'Nombre A-Z'),
        ('-name', 'Nombre Z-A'),
        ('price', 'Precio menor a mayor'),
        ('-price', 'Precio mayor a menor'),
    ]

    sort = forms.ChoiceField(
        required=False,
        choices=SORT_CHOICES,
        initial='-created_at',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes to all fields
        for field_name, field in self.fields.items():
            if not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super().clean()
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')

        if min_price and max_price and min_price > max_price:
            raise forms.ValidationError(
                "El precio mínimo no puede ser mayor al precio máximo."
            )

        return cleaned_data
