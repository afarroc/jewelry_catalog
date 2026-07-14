from .models import Banner


HOME_HERO_DEFAULTS = {
    'eyebrow': 'Colección 2026',
    'title': 'Luz eternizada en metal',
    'subtitle': 'Piezas creadas para perdurar: diseño atemporal, materiales nobles y acabados a mano.',
    'primary_cta_text': 'Explorar colección',
    'primary_cta_url': '/products/',
    'secondary_cta_text': 'Nuestras tiendas',
    'secondary_cta_url': '/tiendas/',
    'background_image_url': 'https://res.cloudinary.com/dwidzc3k/image/upload/banner.jpg',
}

TIENDAS_HERO_DEFAULTS = {
    'eyebrow': 'Ecosistema Miluxious',
    'title': 'Nuestras tiendas',
    'subtitle': 'Descubrí las colecciones de nuestros socios dentro del ecosistema Miluxious.',
    'primary_cta_text': 'Ver colección',
    'primary_cta_url': '/products/',
    'secondary_cta_text': 'Contacto',
    'secondary_cta_url': '/contacto/',
    'background_image_url': 'https://res.cloudinary.com/dwidzc3k/image/upload/banner1.jpg',
}


def build_hero_from_banners(banners_qs, defaults):
    """Build a hero dict from an active Banner queryset, falling back to defaults."""
    hero = dict(defaults)
    if banners_qs.exists():
        b = banners_qs[0]
        hero.update({
            'eyebrow': b.subtitle or hero['eyebrow'],
            'title': b.title or hero['title'],
            'subtitle': b.description or hero['subtitle'],
            'primary_cta_text': b.button_text or hero['primary_cta_text'],
            'primary_cta_url': b.button_url or hero['primary_cta_url'],
            'background_image_url': b.get_image_url,
        })
    return hero
