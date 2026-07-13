# products/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Category, Product
from gallery.models import ImageUpload
from .forms import ProductSearchForm, ProductForm
from gallery.utils import process_product_image
from .serializers import (
    CategorySerializer, ProductSerializer,
    ProductListSerializer
)
import logging

logger = logging.getLogger('products')
api_logger = logging.getLogger('api')
cache_logger = logging.getLogger('cache')


def product_list(request, category_slug=None):
    """Simple function-based view for displaying products."""
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    if not category_slug and request.GET.get('category'):
        category_slug = request.GET['category'].strip().lower()

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    context = {
        'category': category,
        'categories': categories,
        'products': products,
        'search_form': ProductSearchForm(),
        'has_filters': False,
    }
    return render(request, 'products/product_list.html', context)


class ProductDetailView(DetailView):
    """Class-based view for displaying product details with caching."""
    model = Product
    template_name = 'products/product_detail_editorial.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    @method_decorator(cache_page(600))  # Cache for 10 minutes
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        """Allow detail view for any existing product slug."""
        return Product.objects.select_related('category')


# API Views
class StandardResultsSetPagination(PageNumberPagination):
    """Custom pagination class."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CategoryListAPIView(generics.ListCreateAPIView):
    """API view for listing and creating categories."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class CategoryDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """API view for retrieving, updating and deleting categories."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class ProductListAPIView(generics.ListCreateAPIView):
    """API view for listing and creating products."""
    queryset = Product.objects.filter(available=True)
    permission_classes = [AllowAny]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_fields = ['category', 'jewelry_type', 'material', 'available']
    search_fields = ['name', 'description', 'jewelry_type', 'material']
    ordering_fields = ['name', 'price', 'created_at', 'updated_at']
    ordering = ['-created_at']
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        """Use different serializer for list vs create."""
        if self.request.method == 'GET':
            return ProductListSerializer
        return ProductSerializer


class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """API view for retrieving, updating and deleting products."""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'


@api_view(['GET'])
@permission_classes([AllowAny])
def featured_products_api(request):
    """API endpoint for featured products."""
    products = Product.objects.filter(available=True).order_by('-created_at')[:8]
    serializer = ProductListSerializer(products, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def products_by_category_api(request, category_slug):
    """API endpoint for products by category."""
    try:
        category = Category.objects.get(slug=category_slug)
        products = Product.objects.filter(category=category, available=True)
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    except Category.DoesNotExist:
        return Response(
            {'error': 'Category not found'},
            status=status.HTTP_404_NOT_FOUND
        )


# Product Management Views (for admin/staff)
@login_required
def product_create(request):
    """View for creating new products with inline image crop."""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)

            # Si hay imagen + crop_data, procesar y asignar URL de Cloudinary
            image_file = request.FILES.get('image')
            crop_data_raw = request.POST.get('crop_data')
            gallery_image_id = request.POST.get('gallery_image_id')
            if gallery_image_id:
                try:
                    gallery = ImageUpload.objects.get(pk=gallery_image_id)
                    product.image = gallery.image
                except ImageUpload.DoesNotExist:
                    messages.warning(request, 'La imagen de galería seleccionada no existe.')
            elif image_file and crop_data_raw:
                try:
                    import json
                    crop_data = json.loads(crop_data_raw)
                    # Validar mínimo
                    if isinstance(crop_data, dict) and 'ratio' in crop_data:
                        url = process_product_image(image_file, crop_data, product)
                        product.image = url
                except Exception as e:
                    logger.error(f"Error procesando imagen en create: {e}")
                    messages.warning(request, f'Producto creado, pero error al procesar imagen: {e}')

            product.save()
            form.save_m2m()
            messages.success(request, f'Producto "{product.name}" creado exitosamente.')
            logger.info(f"Product created: {product.name} by user {request.user.username}")
            return redirect('products:product_detail', slug=product.slug)
    else:
        form = ProductForm()

    # Si viene gallery_image_id en GET, preparar preview
    gallery_image_url = None
    gallery_image_id = request.GET.get('gallery_image_id')
    if gallery_image_id:
        try:
            gallery = ImageUpload.objects.get(pk=gallery_image_id)
            gallery_image_url = gallery.image
            form = ProductForm(initial={'gallery_image_id': gallery.id})
        except ImageUpload.DoesNotExist:
            messages.warning(request, 'La imagen de galería seleccionada no existe.')

    context = {
        'form': form,
        'title': 'Crear Nuevo Producto',
        'button_text': 'Crear Producto',
        'gallery_image_url': gallery_image_url,
        'admin_header_title': 'Crear Nuevo Producto',
        'admin_header_subtitle': 'Crear nuevo producto',
    }
    return render(request, 'products/product_form_editorial.html', context)


@login_required
def product_update(request, product_id):
    """View for updating existing products with inline image crop."""
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save(commit=False)

            # Si hay imagen nueva + crop_data, procesar y reemplazar
            image_file = request.FILES.get('image')
            crop_data_raw = request.POST.get('crop_data')
            gallery_image_id = request.POST.get('gallery_image_id')
            if gallery_image_id:
                try:
                    gallery = ImageUpload.objects.get(pk=gallery_image_id)
                    product.image = gallery.image
                except ImageUpload.DoesNotExist:
                    messages.warning(request, 'La imagen de galería seleccionada no existe.')
            elif image_file and crop_data_raw:
                try:
                    import json
                    crop_data = json.loads(crop_data_raw)
                    if isinstance(crop_data, dict) and 'ratio' in crop_data:
                        url = process_product_image(image_file, crop_data, product)
                        product.image = url
                except Exception as e:
                    logger.error(f"Error procesando imagen en update: {e}")
                    messages.warning(request, f'Producto actualizado, pero error al procesar imagen: {e}')

            product.save()
            form.save_m2m()
            messages.success(request, f'Producto "{product.name}" actualizado exitosamente.')
            logger.info(f"Product updated: {product.name} by user {request.user.username}")
            return redirect('products:product_detail', slug=product.slug)
    else:
        form = ProductForm(instance=product)

    # Si viene gallery_image_id en GET, preparar preview
    gallery_image_url = None
    gallery_image_id = request.GET.get('gallery_image_id')
    if gallery_image_id:
        try:
            gallery = ImageUpload.objects.get(pk=gallery_image_id)
            gallery_image_url = gallery.image
            form = ProductForm(instance=product, initial={'gallery_image_id': gallery.id})
        except ImageUpload.DoesNotExist:
            messages.warning(request, 'La imagen de galería seleccionada no existe.')

    context = {
        'form': form,
        'product': product,
        'title': f'Editar Producto: {product.name}',
        'button_text': 'Actualizar Producto',
        'gallery_image_url': gallery_image_url,
        'admin_header_title': f'Editar Producto: {product.name}',
        'admin_header_subtitle': f'Producto: {product.name}',
    }
    return render(request, 'products/product_form_editorial.html', context)


@login_required
def product_delete(request, product_id):
    """View for deleting products and their associated image files."""
    user = request.user.username or 'Anonymous'

    try:
        product = get_object_or_404(Product, id=product_id)
        product_name = product.name
        has_image = bool(product.image and product.image.name)
        image_file = product.image.name if has_image else 'No image'

        if request.method == 'POST':
            logger.warning(f"[DELETE] Starting deletion process for product: ID={product_id}, Name='{product_name}', Image='{image_file}', User={user}")

            try:
                # Django automatically handles file deletion for ImageField when model is deleted
                product.delete()

                logger.info(f"[SUCCESS] Product deleted successfully: ID={product_id}, Name='{product_name}', User={user}")
                if has_image:
                    logger.info(f"[FILE] Associated image file also deleted: '{image_file}', User={user}")

                messages.success(request, f'Producto "{product_name}" eliminado exitosamente.')
                return redirect('products:product_list')

            except Exception as e:
                logger.error(f"[ERROR] Error deleting product ID={product_id}: {str(e)}, User={user}")
                messages.error(request, 'Error al eliminar el producto. Intente nuevamente.')

        else:
            logger.info(f"[CONFIRM] GET request to delete confirmation for product: ID={product.id}, Name='{product.name}', User={user}")

        context = {
            'product': product,
            'title': f'Eliminar Producto: {product.name}'
        }
        return render(request, 'products/product_confirm_delete_editorial.html', context)

    except Product.DoesNotExist:
        logger.error(f"[ERROR] Attempted to delete non-existent product: ID={product_id}, User={user}")
        messages.error(request, 'El producto que intenta eliminar no existe.')
        return redirect('products:product_list')
    except Exception as e:
        logger.error(f"[ERROR] Unexpected error in product_delete for ID={product_id}: {str(e)}, User={user}")
        messages.error(request, 'Error inesperado al procesar la eliminación.')
        return redirect('products:product_list')



