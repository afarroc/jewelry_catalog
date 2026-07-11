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
from .models import Category, Product, ImageUpload

logger = logging.getLogger('products')


def upload_to_cloudinary(image_file, folder='gallery', public_id=None, title=None):
    """Sube un file object a Cloudinary y devuelve la URL."""
    buffer = io.BytesIO()
    img = Image.open(image_file)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    fmt = img.format or 'JPEG'
    save_kwargs = {'format': fmt}
    if fmt == 'JPEG':
        save_kwargs['quality'] = 90
        save_kwargs['optimize'] = True
    img.save(buffer, **save_kwargs)
    buffer.seek(0)

    now = datetime.now()
    if not public_id:
        if title:
            base = slugify(title)
        else:
            base = f"img-{int(time.time())}"
        public_id = f"{now.year}/{now.month:02d}/{base}"

    result = cloudinary.uploader.upload(
        buffer,
        folder=folder,
        public_id=public_id,
        overwrite=True,
        resource_type='image',
    )
    return result['secure_url']


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


class SimpleImageUploadForm(forms.ModelForm):
    """Simple form for uploading images only."""

    # Sobrescribir image para que sea upload y no URLField del modelo
    image = forms.ImageField(
        label='Imagen',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'required': True
        }),
        help_text='Formatos permitidos: JPG, PNG, GIF. Tamaño máximo recomendado: 5MB'
    )

    class Meta:
        model = ImageUpload
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la imagen (opcional)',
                'autocomplete': 'off'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción opcional de la imagen'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = False
        self.fields['description'].required = False
        self.fields['title'].help_text = "Si no se proporciona, se generará automáticamente del nombre del archivo"

    def clean_image(self):
        """Validate image file and return file object."""
        image = self.cleaned_data.get('image')
        if image:
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("El archivo es demasiado grande. Máximo 5MB.")
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if hasattr(image, 'content_type') and image.content_type not in allowed_types:
                raise forms.ValidationError("Tipo de archivo no permitido. Use JPG, PNG, GIF o WebP.")
        return image

    def save(self, commit=True):
        """Override save to upload file to Cloudinary and store URL."""
        instance = super().save(commit=False)
        image_file = self.cleaned_data.get('image')
        if image_file:
            try:
                url = upload_to_cloudinary(
                    image_file,
                    folder='gallery',
                    title=instance.title or ''
                )
                instance.image = url
            except Exception as e:
                logger.error(f"[FORM] Error uploading to Cloudinary: {e}")
                raise forms.ValidationError(f"Error al subir la imagen: {e}")
        if commit:
            instance.save()
        return instance


class ProductImageCropForm(forms.Form):
    """Form for uploading an image and selecting a crop ratio for products."""

    image = forms.ImageField(
        label='Imagen original',
        widget=forms.FileInput(attrs={
            'accept': 'image/*',
            'required': False,  # No requerida si se elige de galería
        }),
        help_text='Formatos permitidos: JPG, PNG, WebP. Tamaño máximo recomendado: 10MB.',
    )
    product_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    gallery_image_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    crop_data = forms.CharField(widget=forms.HiddenInput(), required=True)

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and image.size > 10 * 1024 * 1024:
            raise forms.ValidationError("El archivo supera el tamaño máximo de 10MB.")
        return image

    def clean_gallery_image_id(self):
        gallery_id = self.cleaned_data.get('gallery_image_id')
        if gallery_id:
            try:
                return ImageUpload.objects.get(pk=gallery_id)
            except ImageUpload.DoesNotExist:
                raise forms.ValidationError("La imagen de galería seleccionada no existe.")
        return None

    def clean_crop_data(self):
        raw = self.cleaned_data['crop_data']
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            raise forms.ValidationError("Datos de recorte inválidos.")

        required_keys = ['ratio', 'x', 'y', 'width', 'height', 'scale']
        missing = [k for k in required_keys if k not in data]
        if missing:
            raise forms.ValidationError(f"Faltan campos en crop_data: {', '.join(missing)}")

        for k in ['x', 'y', 'width', 'height', 'scale']:
            if not isinstance(data[k], (int, float)) or data[k] < 0:
                raise forms.ValidationError(f"El campo '{k}' debe ser un número positivo.")

        return data
