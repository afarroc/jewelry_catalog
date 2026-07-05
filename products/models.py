# products/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

class Category(models.Model):
    """Model representing a product category."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    visible_in_index = models.BooleanField(default=True, help_text='Mostrar esta categoría en el index y header')
    index_order = models.PositiveIntegerField(default=0, help_text='Orden de visualización en el index/header (menor número = primero)')

    class Meta:
        verbose_name_plural = "categories"
        ordering = ['index_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Automatically create slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        self._renumber_all_categories()
        logger.info(f"Category '{self.name}' saved")

    def _renumber_all_categories(self):
        categories = list(Category.objects.all().order_by('index_order', 'name'))
        for index, category in enumerate(categories, start=1):
            if category.index_order != index:
                Category.objects.filter(pk=category.pk).update(index_order=index)

class Product(models.Model):
    """Model representing a Miluxious accesorios product."""
    JEWELRY_TYPES = [
        ('ring', 'Ring'),
        ('necklace', 'Necklace'),
        ('bracelet', 'Bracelet'),
        ('earring', 'Earring'),
        ('brooch', 'Brooch'),
        ('tiara', 'Tiara'),
        ('other', 'Other'),
    ]

    MATERIALS = [
        ('metal', 'Metal'),
        ('resin', 'Resin'),
        ('glass', 'Glass'),
        ('crystal', 'Crystal'),
        ('pearl', 'Pearl'),
        ('fabric', 'Fabric'),
        ('other', 'Other'),
    ]

    BENTO_SIZES = [
        ('standard', 'Standard (1x1)'),
        ('wide', 'Wide (2x1)'),
        ('wide-image', 'Wide image (2x1 solo imagen)'),
        ('tall', 'Tall (1x2)'),
        ('tall-image', 'Tall image (1x2 solo imagen)'),
        ('featured', 'Featured (2x2)'),
        ('hero', 'Hero (full-width)'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    jewelry_type = models.CharField(
        max_length=20,
        choices=JEWELRY_TYPES,
        default='other'
    )
    material = models.CharField(
        max_length=20,
        choices=MATERIALS,
        default='other'
    )
    category = models.ForeignKey(
        Category,
        related_name='products',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.TextField(
        blank=True,
        null=True,
        help_text='Cloudinary URL or image path'
    )
    # Bento Grid size for e-commerce editorial layout
    bento_size = models.CharField(
        max_length=20,
        choices=BENTO_SIZES,
        default='standard',
        help_text='Grid size: standard (1x1), wide (2x1), tall (1x2), featured (2x2)'
    )
    average_rating = models.FloatField(
        default=0.0,
        help_text='Average product rating (0-5)'
    )
    review_count = models.PositiveIntegerField(
        default=0,
        help_text='Number of reviews'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Automatically create slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        logger.info(f"Product '{self.name}' saved")

    @property
    def display_price(self):
        """Format price for display with currency symbol."""
        return f"S/. {self.price:.2f}"

    @property
    def get_image_url(self):
        """Return image URL for display - supports Cloudinary URLs or local paths."""
        if not self.image:
            return ''
        return self.image

    @property
    def is_new(self):
        """Check if product was created in the last 7 days."""
        from django.utils import timezone
        return (timezone.now() - self.created_at).days <= 7


class ImageUpload(models.Model):
    """Simple model for image uploads."""
    title = models.CharField(max_length=200, blank=True, help_text='Optional title for the image')
    image = models.ImageField(
        upload_to='uploads/%Y/%m/%d/',
        help_text='Upload an image file (JPG, PNG, GIF). Max 5MB.'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, help_text='Optional description')

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