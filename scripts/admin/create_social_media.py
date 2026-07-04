#!/usr/bin/env python
"""
Script para crear datos de ejemplo de redes sociales
Ejecutar con: python manage.py shell < create_social_media.py
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jewelry_catalog.settings')
django.setup()

from home.models import SocialMedia

def create_social_media():
    """Crear redes sociales de ejemplo"""

    social_media_data = [
        {
            'name': 'Facebook',
            'platform': 'facebook',
            'url': 'https://www.facebook.com/joyeriafantasia',
            'is_active': True,
            'order': 1,
            'followers_count': 12500,
        },
        {
            'name': 'Instagram',
            'platform': 'instagram',
            'url': 'https://www.instagram.com/joyeriafantasia',
            'is_active': True,
            'order': 2,
            'followers_count': 8900,
        },
        {
            'name': 'Pinterest',
            'platform': 'pinterest',
            'url': 'https://www.pinterest.com/joyeriafantasia',
            'is_active': True,
            'order': 3,
            'followers_count': 5600,
        },
        {
            'name': 'Twitter',
            'platform': 'twitter',
            'url': 'https://www.twitter.com/joyeriafantasia',
            'is_active': True,
            'order': 4,
            'followers_count': 3200,
        },
    ]

    created_count = 0
    for data in social_media_data:
        social, created = SocialMedia.objects.get_or_create(
            platform=data['platform'],
            defaults=data
        )
        if created:
            print(f"✓ Creada red social: {social.name} ({social.platform})")
            created_count += 1
        else:
            print(f"• Ya existe: {social.name} ({social.platform})")

    print(f"\n📊 Resumen: {created_count} redes sociales creadas")
    print("🔗 Total de redes sociales activas:", SocialMedia.objects.filter(is_active=True).count())

if __name__ == '__main__':
    create_social_media()