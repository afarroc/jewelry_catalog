# gallery/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


class ImageUpload(models.Model):
    """Model representing an uploaded image in the gallery."""
    title = models.CharField(max_length=200, blank=True, help_text='Optional title for the image')
    image = models.URLField(
        max_length=500,
        help_text='URL de la imagen (Cloudinary o path local).'
    )
    asset_folder = models.CharField(max_length=255, blank=True, help_text='Carpeta actual en Cloudinary (asset_folder)')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, help_text='Optional description')
    partner = models.ForeignKey(
        'partners.Partner',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='images',
        help_text='Partner/tienda al que pertenece esta imagen. Vacío = galería global Miluxious.'
    )

    class Meta:
        verbose_name = "Image Upload"
        verbose_name_plural = "Image Uploads"
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title or f"Image {self.id}"

    def save(self, *args, **kwargs):
        """Auto-generate title if not provided."""
        if not self.title and hasattr(self.image, 'name'):
            # Extract filename without extension
            filename = self.image.name.rsplit('.', 1)[0] if '.' in self.image.name else self.image.name
            self.title = filename.replace('_', ' ').title()
        super().save(*args, **kwargs)
        logger.info(f"Image uploaded: {self.title}")
