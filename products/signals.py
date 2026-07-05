from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Product, Category
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Product)
def invalidate_product_cache(sender, instance, **kwargs):
    """Invalidate cache when a product is saved."""
    # Invalidate product list caches
    cache.delete('products_list_all')

    # Invalidate category-specific caches
    if instance.category:
        cache.delete(f'products_list_{instance.category.slug}')

    # Invalidate individual product cache
    cache.delete(f'product_detail_{instance.id}_{instance.slug}')

    # Invalidate featured products cache
    cache.delete('featured_products')

    logger.info(f"Invalidated cache for product: {instance.name}")


@receiver(post_delete, sender=Product)
def invalidate_product_cache_on_delete(sender, instance, **kwargs):
    """Invalidate cache when a product is deleted."""
    # Invalidate product list caches
    cache.delete('products_list_all')

    # Invalidate category-specific caches
    if instance.category:
        cache.delete(f'products_list_{instance.category.slug}')

    # Invalidate individual product cache
    cache.delete(f'product_detail_{instance.id}_{instance.slug}')

    # Invalidate featured products cache
    cache.delete('featured_products')

    logger.info(f"Invalidated cache for deleted product: {instance.name}")


def invalidate_category_cache(sender, instance, **kwargs):
    """Invalidate cache when a category is saved."""
    # Invalidate categories list cache
    cache.delete('categories_list')

    # Invalidate all product lists (since category names might have changed)
    try:
        cache.delete_pattern('products_list_*')
    except AttributeError:
        pass

    logger.info(f"Invalidated cache for category: {instance.name}")


@receiver(post_delete, sender=Category)
def invalidate_category_cache_on_delete(sender, instance, **kwargs):
    """Invalidate cache when a category is deleted."""
    # Invalidate categories list cache
    cache.delete('categories_list')

    # Invalidate category-specific product cache
    cache.delete(f'products_list_{instance.slug}')

    # Invalidate all product lists
    try:
        cache.delete_pattern('products_list_*')
    except AttributeError:
        pass

    logger.info(f"Invalidated cache for deleted category: {instance.name}")


# Helper functions for manual cache invalidation
def invalidate_all_product_caches():
    """Invalidate all product-related caches."""
    cache.delete_pattern('products_list_*')
    cache.delete_pattern('product_detail_*')
    cache.delete('featured_products')
    cache.delete('categories_list')
    logger.info("Invalidated all product caches")


def invalidate_product_cache_by_category(category_slug):
    """Invalidate cache for a specific category."""
    cache.delete(f'products_list_{category_slug}')
    logger.info(f"Invalidated cache for category: {category_slug}")


def invalidate_product_detail_cache(product_id, product_slug):
    """Invalidate cache for a specific product."""
    cache.delete(f'product_detail_{product_id}_{product_slug}')
    logger.info(f"Invalidated cache for product: {product_id}_{product_slug}")