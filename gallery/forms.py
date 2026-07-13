# gallery/forms.py
import json
import io
import time
import logging
from datetime import datetime
from PIL import Image
import cloudinary.uploader
from django import forms
from django.utils.text import slugify
from .models import ImageUpload

logger = logging.getLogger(__name__)


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
