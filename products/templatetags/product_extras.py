from django import template

register = template.Library()


BENTO_SIZE_LABELS = {
    "standard": "1x1",
    "wide": "2x1",
    "wide-image": "2x1-img",
    "tall": "1x2",
    "tall-image": "1x2-img",
    "featured": "2x2",
    "hero": "hero",
}


@register.filter
def bento_label(value):
    """Return human-readable Bento size label."""
    return BENTO_SIZE_LABELS.get(str(value).lower(), str(value))


@register.filter
def stars(value):
    """Render star rating string from a numeric average_rating."""
    try:
        rating = float(value)
    except (TypeError, ValueError):
        return ""
    filled = int(rating)
    remainder = rating - filled
    if remainder >= 0.75:
        filled += 1
    elif remainder >= 0.25:
        filled += 0.5
    filled = max(0, min(5, filled))
    return "★" * int(filled) + ("½" if filled % 1 else "") + "☆" * (5 - int(filled) - (1 if filled % 1 else 0))


@register.simple_tag
def rating_label(product):
    """Return compact rating + review count label."""
    if not getattr(product, "review_count", 0):
        return ""
    return f'{getattr(product, "average_rating", 0):.1f} ({product.review_count})'
