from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
import os


def validate_image_extension(value):
    """Validar que la imagen tenga una extensión permitida"""
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    if ext not in valid_extensions:
        raise ValidationError('Solo se permiten archivos de imagen: JPG, PNG, WebP')


class Banner(models.Model):
    """
    Modelo para banners de la página principal
    """
    title = models.CharField(
        max_length=200,
        verbose_name="Título del Banner",
        help_text="Título principal que se mostrará en el banner"
    )

    subtitle = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Subtítulo",
        help_text="Subtítulo opcional para el banner"
    )

    description = models.TextField(
        blank=True,
        verbose_name="Descripción",
        help_text="Descripción detallada del banner"
    )

    # Campo para la imagen del banner
    image_filename = models.CharField(
        max_length=255,
        verbose_name="Ruta/URL de la Imagen",
        help_text="Ruta relativa o URL absoluta del banner. Puede ser ruta estática (ej: banner1.jpg), ruta Cloudinary relativa (ej: v1783035210/banner.jpg) o URL completa de Cloudinary.",
        unique=True
    )

    # Campos de control
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Si está marcado, el banner se mostrará en la página principal"
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Orden",
        help_text="Orden de aparición (menor número = mayor prioridad)"
    )

    # Campos de enlace opcional
    button_text = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Texto del Botón",
        help_text="Texto que aparecerá en el botón de acción"
    )

    button_url = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="URL del Botón",
        help_text="URL a la que redirigirá el botón (puede ser absoluta o relativa, ej: /contacto o https://...)"
    )

    # Campos de fecha
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Modificación")

    class Meta:
        verbose_name = "Banner"
        verbose_name_plural = "Banners"
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title

    @property
    def get_image_url(self):
        """Obtener la URL completa de la imagen desde Cloudinary, S3/media o ruta local."""
        if not self.image_filename:
            return '/static/images/placeholder-banner.jpg'

        filename = self.image_filename.strip()

        if not filename:
            return '/static/images/placeholder-banner.jpg'

        # Ya es URL absoluta
        if filename.startswith('http://') or filename.startswith('https://'):
            return filename

        # Si parece ruta Cloudinary, devolverla directamente
        if filename.startswith('v') and '/' in filename:
            cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
            if cloud_name:
                return f"https://res.cloudinary.com/{cloud_name}/image/upload/{filename}"
            return f"/static/images/banners/{filename}"

        # Construir URL de Cloudinary para nombres de archivo simples
        cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
        if cloud_name:
            return f"https://res.cloudinary.com/{cloud_name}/image/upload/{filename}"

        # Ruta local para desarrollo
        return f"/static/images/banners/{filename}"

    def clean(self):
        """Validaciones personalizadas"""
        if self.button_text and not self.button_url:
            raise ValidationError("Si especifica texto del botón, debe proporcionar una URL")
        if not self.button_text and self.button_url:
            raise ValidationError("Si especifica una URL del botón, debe proporcionar texto del botón")

    @property
    def has_button(self):
        """Verificar si el banner tiene botón configurado"""
        return bool(self.button_text and self.button_url)


class SocialMedia(models.Model):
    """
    Modelo para gestionar las redes sociales de la tienda
    """
    PLATFORM_CHOICES = [
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('twitter', 'Twitter'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
        ('pinterest', 'Pinterest'),
        ('linkedin', 'LinkedIn'),
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram'),
        ('other', 'Otro'),
    ]

    name = models.CharField(
        max_length=50,
        verbose_name="Nombre de la Red Social",
        help_text="Ej: Facebook, Instagram, Twitter, etc."
    )

    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        default='other',
        verbose_name="Plataforma",
        help_text="Selecciona la plataforma de redes sociales"
    )

    url = models.URLField(
        verbose_name="URL del Perfil",
        help_text="URL completa del perfil o página (ej: https://www.facebook.com/tu-pagina)",
        validators=[URLValidator()]
    )

    icon_class = models.CharField(
        max_length=50,
        verbose_name="Clase del Icono",
        help_text="Clase CSS del icono (ej: fab fa-facebook-f)",
        default="fas fa-link"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Activa",
        help_text="Si está marcado, se mostrará en el sitio web"
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Orden",
        help_text="Orden de aparición (menor número = mayor prioridad)"
    )

    followers_count = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Número de Seguidores",
        help_text="Número aproximado de seguidores (opcional)"
    )

    # Campos de fecha
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Modificación")

    class Meta:
        verbose_name = "Red Social"
        verbose_name_plural = "Redes Sociales"
        ordering = ['order', 'platform']
        unique_together = ['platform', 'url']  # Evitar duplicados

    def __str__(self):
        return f"{self.get_platform_display()} - {self.name}"

    def clean(self):
        """Validaciones personalizadas"""
        if self.platform != 'other' and not self.icon_class.startswith('fab fa-'):
            # Establecer icono por defecto basado en la plataforma
            platform_icons = {
                'facebook': 'fab fa-facebook-f',
                'instagram': 'fab fa-instagram',
                'twitter': 'fab fa-twitter',
                'tiktok': 'fab fa-tiktok',
                'youtube': 'fab fa-youtube',
                'pinterest': 'fab fa-pinterest-p',
                'linkedin': 'fab fa-linkedin-in',
                'whatsapp': 'fab fa-whatsapp',
                'telegram': 'fab fa-telegram-plane',
            }
            self.icon_class = platform_icons.get(self.platform, 'fas fa-link')

    @property
    def display_followers(self):
        """Mostrar el número de seguidores de forma legible"""
        if self.followers_count:
            if self.followers_count >= 1000000:
                return f"{self.followers_count // 1000000}M"
            elif self.followers_count >= 1000:
                return f"{self.followers_count // 1000}K"
            else:
                return str(self.followers_count)
        return None

    @property
    def platform_icon(self):
        """Obtener el icono basado en la plataforma"""
        platform_icons = {
            'facebook': 'fab fa-facebook-f',
            'instagram': 'fab fa-instagram',
            'twitter': 'fab fa-twitter',
            'tiktok': 'fab fa-tiktok',
            'youtube': 'fab fa-youtube',
            'pinterest': 'fab fa-pinterest-p',
            'linkedin': 'fab fa-linkedin-in',
            'whatsapp': 'fab fa-whatsapp',
            'telegram': 'fab fa-telegram-plane',
        }
        return platform_icons.get(self.platform, self.icon_class)
