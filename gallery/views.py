# gallery/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.db.models import Q
from .models import ImageUpload
from .forms import SimpleImageUploadForm, ProductImageCropForm
from .utils import process_product_image, get_cloudinary_folders, get_cloudinary_resources, build_folder_breadcrumbs, is_cloudinary_root_image
import logging

logger = logging.getLogger('gallery')
image_logger = logging.getLogger('image_upload')


@login_required
def image_upload(request):
    """Simple view for uploading images."""
    user = request.user.username or 'Anonymous'

    if request.method == 'POST':
        image_logger.info(f"[UPLOAD] === STARTING IMAGE UPLOAD ===")
        image_logger.info(f"[UPLOAD] POST request to image_upload by user: {user}")
        image_logger.info(f"[UPLOAD] Request timestamp: {timezone.now()}")
        image_logger.info(f"[UPLOAD] Remote IP: {request.META.get('REMOTE_ADDR', 'Unknown')}")
        image_logger.info(f"[UPLOAD] User agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")

        if request.FILES:
            image_logger.info(f"[UPLOAD] Files received: {len(request.FILES)} file(s)")
            for field_name, uploaded_file in request.FILES.items():
                image_logger.info(f"[UPLOAD] File details:")
                image_logger.info(f"[UPLOAD]   Field: {field_name}")
                image_logger.info(f"[UPLOAD]   Name: {uploaded_file.name}")
                image_logger.info(f"[UPLOAD]   Size: {uploaded_file.size} bytes")
                image_logger.info(f"[UPLOAD]   Content-Type: {uploaded_file.content_type}")
                image_logger.info(f"[UPLOAD]   Temporary file: {hasattr(uploaded_file, 'temporary_file_path')}")
        else:
            image_logger.warning(f"[UPLOAD] No files received in POST request")
            image_logger.warning(f"[UPLOAD] POST data keys: {list(request.POST.keys()) if request.POST else 'None'}")

        form = SimpleImageUploadForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                image_logger.info(f"[UPLOAD] Form validation passed, preparing to save...")
                image_logger.info(f"[UPLOAD] Form cleaned data: {dict(form.cleaned_data)}")

                image_logger.info(f"[UPLOAD] Calling form.save()...")
                image_upload = form.save()
                image_logger.info(f"[UPLOAD] Model instance created with ID: {image_upload.id}")

                if image_upload.image:
                    image_url = image_upload.image

                    image_logger.info(f"[SUCCESS] === IMAGE UPLOAD COMPLETED SUCCESSFULLY ===")
                    image_logger.info(f"[SUCCESS] Image ID: {image_upload.id}")
                    image_logger.info(f"[SUCCESS] Title: '{image_upload.title}'")
                    image_logger.info(f"[SUCCESS] Image URL: '{image_url}'")
                    image_logger.info(f"[SUCCESS] Upload timestamp: {image_upload.uploaded_at}")
                    image_logger.info(f"[SUCCESS] User: {user}")

                    messages.success(request, f'Imagen "{image_upload.title}" subida exitosamente.')
                    image_logger.info(f"[REDIRECT] Redirecting to image list for user: {user}")
                    return redirect('gallery:image_list')
                else:
                    image_logger.error(f"[ERROR] Image model saved but no image URL found in model")
                    messages.error(request, 'Error: La imagen no se guardó correctamente.')

            except Exception as e:
                image_logger.error(f"[ERROR] === CRITICAL ERROR DURING IMAGE SAVE ===")
                image_logger.error(f"[ERROR] Error saving image upload: {str(e)}")
                image_logger.error(f"[ERROR] Exception type: {type(e).__name__}")
                image_logger.error(f"[ERROR] User: {user}")
                image_logger.error(f"[ERROR] Form data: {dict(form.cleaned_data) if form.is_valid() else 'Form invalid'}")

                import traceback
                image_logger.error(f"[ERROR] Full traceback:")
                for line in traceback.format_exc().split('\n'):
                    if line.strip():
                        image_logger.error(f"[ERROR] {line}")

                messages.error(request, 'Error al guardar la imagen. Intente nuevamente.')
        else:
            image_logger.warning(f"[WARNING] Invalid form submission in image_upload: {form.errors}, User={user}")
            for field, errors in form.errors.items():
                for error in errors:
                    image_logger.warning(f"   Field '{field}': {error}")
    else:
        image_logger.debug(f"[PAGE] GET request to image_upload page by user: {user}")

    form = SimpleImageUploadForm()
    context = {
        'form': form,
        'title': 'Subir Imagen',
        'button_text': 'Subir Imagen',
        'admin_header_title': 'Subir imagen',
        'admin_header_subtitle': 'Subir imagen a la galería',
    }
    return render(request, 'gallery/pages/image_upload_editorial.html', context)


@login_required
def gallery_home(request):
    """Home/dashboard de la galería: métricas, accesos rápidos y actividad reciente."""
    user = request.user.username or 'Anonymous'
    start_time = timezone.now()

    total_images = ImageUpload.objects.count()
    recent_uploads = ImageUpload.objects.filter(
        uploaded_at__gte=timezone.now() - timezone.timedelta(days=7)
    ).count()

    try:
        subfolders = get_cloudinary_folders('')
    except Exception:
        subfolders = []

    try:
        recent_images = list(ImageUpload.objects.order_by('-uploaded_at')[:8])
    except Exception:
        recent_images = []

    context = {
        'title': 'Galería',
        'admin_header_title': 'Galería',
        'admin_header_subtitle': 'Panel de administración de imágenes',
        'total_images': total_images,
        'recent_uploads': recent_uploads,
        'subfolders': subfolders,
        'recent_images': recent_images,
    }
    return render(request, 'gallery/pages/gallery_home.html', context)


@login_required
def image_list(request):
    """View for listing uploaded images with folder navigation and search."""
    user = request.user.username or 'Anonymous'
    start_time = timezone.now()

    search_query = request.GET.get('q', '').strip()
    folder_path = request.GET.get('folder', '').strip()
    view_mode = request.GET.get('view', 'folder')
    page = request.GET.get('page', '1')

    image_logger.info(f"[LIST] === STARTING IMAGE LIST REQUEST ===")
    image_logger.info(f"[LIST] GET request to image_list by user: {user}")
    image_logger.info(f"[LIST] Folder: '{folder_path}', View: '{view_mode}', Search: '{search_query}', Page: {page}")

    images = ImageUpload.objects.all()
    total_before_filter = images.count()

    if search_query:
        images = images.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
        image_logger.info(f"[SEARCH] Search applied: '{search_query}'")
        image_logger.info(f"[SEARCH] Results: {images.count()} of {total_before_filter} images found")

    if view_mode == 'folder':
        if folder_path:
            images = [img for img in images if img.asset_folder == folder_path]
            image_logger.info(f"[FOLDER] Filtering by asset_folder: '{folder_path}' ({len(images)} images)")
        else:
            images = [img for img in images if not img.asset_folder]
            image_logger.info(f"[FOLDER] Root view: showing only root images ({len(images)} images)")

    images = sorted(images, key=lambda x: x.uploaded_at, reverse=True)

    paginator = Paginator(images, 24)

    try:
        images_page = paginator.page(page)
    except PageNotAnInteger:
        images_page = paginator.page(1)
    except EmptyPage:
        images_page = paginator.page(paginator.num_pages)

    subfolders = []
    cloudinary_resources = []
    breadcrumbs = []
    if view_mode == 'folder':
        try:
            subfolders = get_cloudinary_folders(folder_path)
            cloudinary_resources = get_cloudinary_resources(folder_path, max_results=30)
        except Exception as e:
            image_logger.warning(f"[CLOUDINARY] Could not load folder data: {e}")

        breadcrumbs = build_folder_breadcrumbs(folder_path)

    filtered_images = list(images_page.object_list)
    local_urls = set(img.image for img in filtered_images)
    combined_images = list(filtered_images)
    for idx, res in enumerate(cloudinary_resources):
        url = res.get('secure_url', '')
        if url and url not in local_urls:
            combined_images.append({
                'id': f'cloud_{idx}',
                'title': res.get('public_id', '').split('/')[-1] or url.split('/')[-1],
                'description': '',
                'image': url,
                'is_cloudinary': True,
                'uploaded_at': None,
            })

    total_images = ImageUpload.objects.count()
    recent_uploads = ImageUpload.objects.filter(
        uploaded_at__gte=timezone.now() - timezone.timedelta(days=7)
    ).count()

    end_time = timezone.now()
    duration = (end_time - start_time).total_seconds() * 1000

    image_logger.info(f"[PERF] === IMAGE LIST RENDERED SUCCESSFULLY ===")
    image_logger.info(f"[PERF] Execution time: {duration:.2f}ms")
    image_logger.info(f"[PERF] Total images in DB: {total_images}")
    image_logger.info(f"[PERF] Recent uploads (7 days): {recent_uploads}")
    image_logger.info(f"[PERF] Filtered images: {len(filtered_images)}")
    image_logger.info(f"[PERF] Combined images: {len(combined_images)}")
    image_logger.info(f"[PERF] Page: {images_page.number}/{paginator.num_pages}")
    image_logger.info(f"[PERF] Folder: '{folder_path}', Subfolders: {len(subfolders)}, Cloudinary resources: {len(cloudinary_resources)}")
    image_logger.info(f"[PERF] View mode: '{view_mode}'")
    image_logger.info(f"[PERF] Search query: '{search_query}'")
    image_logger.info(f"[PERF] User: {user}")
    image_logger.info(f"[PERF] Response: 200 OK")

    context = {
        'images': images_page,
        'combined_images': combined_images,
        'title': 'Imágenes Subidas',
        'search_query': search_query,
        'total_images': total_images,
        'recent_uploads': recent_uploads,
        'is_paginated': images_page.has_other_pages(),
        'page_obj': images_page,
        'cloudinary_cloud_name': settings.CLOUDINARY_CLOUD_NAME,
        'folder_path': folder_path,
        'subfolders': subfolders,
        'cloudinary_resources': cloudinary_resources,
        'breadcrumbs': breadcrumbs,
        'view_mode': view_mode,
        'admin_header_title': 'Imágenes',
        'admin_header_subtitle': 'Panel de administración de imágenes' if not folder_path else f'Carpeta: {folder_path}',
    }
    return render(request, 'gallery/pages/image_list_editorial.html', context)


@login_required
def image_detail(request, image_id):
    """View for displaying image details."""
    user = request.user.username or 'Anonymous'

    try:
        image = get_object_or_404(ImageUpload, id=image_id)
        image_url = image.image or ''

        image_logger.info(f"[VIEW] Image detail viewed: ID={image.id}, Title='{image.title}', URL='{image_url}', User={user}")

        context = {
            'image': image,
            'image_url': image_url,
            'title': f'Imagen: {image.title}',
            'cloudinary_cloud_name': settings.CLOUDINARY_CLOUD_NAME,
            'admin_header_title': image.title,
            'admin_header_subtitle': f'Detalle de imagen · {image.asset_folder or "Sin carpeta"}',
        }
        return render(request, 'gallery/pages/image_detail_editorial.html', context)

    except ImageUpload.DoesNotExist:
        image_logger.error(f"[ERROR] Image not found: ID={image_id}, User={user}")
        raise
    except Exception as e:
        image_logger.error(f"[ERROR] Error displaying image detail ID={image_id}: {str(e)}, User={user}")
        raise


@login_required
def image_delete(request, image_id):
    """View for deleting uploaded images from the gallery."""
    user = request.user.username or 'Anonymous'

    try:
        image = get_object_or_404(ImageUpload, id=image_id)
        image_url = image.image or ''

        if request.method == 'POST':
            title = image.title
            image_id_deleted = image.id

            image_logger.warning(f"[DELETE] Starting deletion process for image: ID={image_id_deleted}, Title='{title}', URL='{image_url}', User={user}")

            image.delete()
            image_logger.info(f"[DELETE] Image record deleted from database: ID={image_id_deleted}, User={user}")

            messages.success(request, f'Imagen "{title}" eliminada exitosamente.')
            return redirect('gallery:image_list')

        context = {
            'image': image,
            'title': f'Eliminar imagen: {image.title}',
            'admin_header_title': 'Confirmar eliminación',
            'admin_header_subtitle': image.title,
        }
        return render(request, 'gallery/pages/image_confirm_delete_editorial.html', context)

    except ImageUpload.DoesNotExist:
        image_logger.error(f"[ERROR] Image not found: ID={image_id}, User={user}")
        raise
    except Exception as e:
        image_logger.error(f"[ERROR] Error deleting image ID={image_id}: {str(e)}, User={user}")
        raise


@login_required
def image_bulk_delete(request):
    """Bulk delete selected images from the gallery."""
    user = request.user.username or 'Anonymous'

    if request.method != 'POST':
        messages.error(request, 'Método no permitido.')
        return redirect('gallery:image_list')

    selected_ids = request.POST.getlist('selected_images')
    if not selected_ids:
        messages.warning(request, 'No seleccionaste ninguna imagen para eliminar.')
        return redirect('gallery:image_list')

    # Only delete images that belong to the current user's partner scope (if applicable)
    qs = ImageUpload.objects.filter(id__in=selected_ids)
    if hasattr(request, 'user_partners'):
        allowed_partners = request.user_partners
        if allowed_partners:
            qs = qs.filter(partner__in=allowed_partners)
        else:
            qs = qs.none()

    deleted_count = qs.count()
    deleted_titles = [img.title or f'Image {img.id}' for img in qs]

    for img in qs:
        image_logger.warning(f"[BULK_DELETE] Deleting image: ID={img.id}, Title='{img.title}', URL='{img.image}', User={user}")

    qs.delete()

    image_logger.info(f"[BULK_DELETE] Bulk deleted {deleted_count} images by user: {user}")
    messages.success(request, f'Se eliminaron {deleted_count} imagen(es): {", ".join(deleted_titles[:5])}{"..." if len(deleted_titles) > 5 else ""}')
    return redirect('gallery:image_list')


@login_required
def product_image_editor(request):
    """Vista de carga y recorte de imagen.
    
    Modos:
    - Con product_id: asigna la imagen procesada a un producto.
    - Sin product_id: crea un ImageUpload en la galería general.
    """
    from products.models import Product

    product = None
    product_id = request.GET.get('product_id') or request.POST.get('product_id')
    gallery_mode = not bool(product_id)

    if product_id:
        product = get_object_or_404(Product, pk=product_id)

    if request.method == 'POST':
        form = ProductImageCropForm(request.POST, request.FILES)
        if form.is_valid():
            crop_data = form.cleaned_data['crop_data']
            image_file = form.cleaned_data.get('image')
            gallery_image = form.cleaned_data.get('gallery_image_id')
            product_id = form.cleaned_data.get('product_id')

            if gallery_mode:
                if not image_file:
                    messages.error(request, 'Selecciona una imagen para subir a la galería.')
                    return redirect('gallery:image_editor')
                
                try:
                    url = process_product_image(image_file, crop_data, Product(pk=0, slug='gallery'))
                    gallery = ImageUpload.objects.create(
                        title=f"Galería {timezone.now().strftime('%Y-%m-%d %H:%M')}",
                        image=url,
                        description='Subida desde editor de imágenes'
                    )
                    messages.success(request, f'Imagen subida a galería correctamente.')
                    return redirect('gallery:image_list')
                except Exception as e:
                    logger.error(f"Error subiendo a galería: {e}")
                    messages.error(request, f'Error al subir la imagen: {e}')
                    return redirect('gallery:image_editor')

            if not product_id:
                messages.error(request, 'Primero crea el producto antes de subir su imagen.')
                return redirect('products:product_create')

            product = get_object_or_404(Product, pk=product_id)

            if gallery_image:
                product.image = gallery_image.image
                product.save(update_fields=['image'])
                messages.success(request, f'Imagen de galería asignada a {product.name}.')
                return redirect('products:product_update', product_id=product.id)

            if not image_file:
                messages.error(request, 'Selecciona una imagen o elige una de la galería.')
                return redirect('products:product_update', product_id=product.id)

            try:
                url = process_product_image(image_file, crop_data, product)
                product.image = url
                product.save(update_fields=['image'])
                messages.success(request, f'Imagen guardada correctamente para {product.name}.')
                return redirect('products:product_update', product_id=product.id)
            except Exception as e:
                logger.error(f"Error procesando imagen para producto {product.id}: {e}")
                messages.error(request, f'Error al procesar la imagen: {e}')
        else:
            messages.error(request, 'Corrige los errores en el formulario.')
    else:
        initial = {'product_id': product_id} if product_id else {}
        form = ProductImageCropForm(initial=initial)

    context = {
        'form': form,
        'product': product,
        'gallery_mode': gallery_mode,
        'title': 'Editor de imagen' + (f' — {product.name}' if product else ' (Galería)'),
        'admin_header_title': 'Editor de imagen' + (f' — {product.name}' if product else ''),
        'admin_header_subtitle': 'Galería general' if gallery_mode else (f'Producto: {product.name}' if product else 'Selecciona un producto para asignar la imagen'),
    }
    return render(request, 'gallery/pages/image_editor_editorial.html', context)


@login_required
def s3_diagnostic(request):
    """Diagnostic view for S3 configuration and connectivity"""
    try:
        user = request.user.username or 'Anonymous'
        start_time = timezone.now()

        image_logger.info(f"[S3_DIAGNOSTIC] Starting diagnostic for user: {user}")
        image_logger.info(f"[S3_DIAGNOSTIC] Request timestamp: {start_time}")
        image_logger.info(f"[S3_DIAGNOSTIC] User agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")

        diagnostic_info = {
            'timestamp': timezone.now(),
            'user': user,
            'storage_type': 'Unknown',
            'bucket_name': 'N/A',
            'region': 'N/A',
            'tests': [],
            'folders': {
                'count': 0,
                'list': [],
                'total_objects': 0,
                'note': 'Diagnostic not completed'
            },
            'recent_uploads': []
        }

        try:
            diagnostic_info['storage_type'] = default_storage.__class__.__name__
            diagnostic_info['bucket_name'] = getattr(default_storage, 'bucket_name', 'N/A')
            diagnostic_info['region'] = getattr(default_storage, 'region_name', 'N/A')

            image_logger.info(f"[S3_DIAGNOSTIC] Storage type: {diagnostic_info['storage_type']}")
            image_logger.info(f"[S3_DIAGNOSTIC] Bucket name: {diagnostic_info['bucket_name']}")
            image_logger.info(f"[S3_DIAGNOSTIC] Region: {diagnostic_info['region']}")
        except Exception as e:
            image_logger.warning(f"[S3_DIAGNOSTIC] Could not get storage info: {str(e)}")
            pass

        image_logger.info("[S3_DIAGNOSTIC] === TEST 1: Environment Variables ===")
        try:
            aws_access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
            aws_secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
            bucket_name = getattr(default_storage, 'bucket_name', 'N/A')
            region_name = getattr(default_storage, 'region_name', 'N/A')

            env_status = 'success' if aws_access_key and aws_secret_key else 'error'

            image_logger.info(f"[S3_DIAGNOSTIC] AWS_ACCESS_KEY_ID: {'✓ Set' if aws_access_key else '✗ Not set'}")
            image_logger.info(f"[S3_DIAGNOSTIC] AWS_SECRET_ACCESS_KEY: {'✓ Set' if aws_secret_key else '✗ Not set'}")
            image_logger.info(f"[S3_DIAGNOSTIC] AWS_STORAGE_BUCKET_NAME: {bucket_name}")
            image_logger.info(f"[S3_DIAGNOSTIC] AWS_S3_REGION_NAME: {region_name}")
            image_logger.info(f"[S3_DIAGNOSTIC] Environment test result: {env_status}")

            diagnostic_info['tests'].append({
                'name': 'Environment Variables',
                'status': env_status,
                'details': {
                    'AWS_ACCESS_KEY_ID': 'Set' if aws_access_key else 'Not set',
                    'AWS_SECRET_ACCESS_KEY': 'Set' if aws_secret_key else 'Not set',
                    'AWS_STORAGE_BUCKET_NAME': bucket_name,
                    'AWS_S3_REGION_NAME': region_name
                }
            })
        except Exception as e:
            image_logger.error(f"[S3_DIAGNOSTIC] Environment variables test failed: {str(e)}")
            diagnostic_info['tests'].append({
                'name': 'Environment Variables',
                'status': 'error',
                'details': {'error': str(e)}
            })

        image_logger.info("[S3_DIAGNOSTIC] === TEST 2: Storage Connectivity ===")
        try:
            if hasattr(default_storage, 'bucket') and default_storage.bucket:
                image_logger.info("[S3_DIAGNOSTIC] S3 bucket detected")
                if hasattr(default_storage.bucket, 'objects'):
                    image_logger.info("[S3_DIAGNOSTIC] Bucket.objects available, attempting to list objects...")
                    objects = list(default_storage.bucket.objects.limit(5))
                    image_logger.info(f"[S3_DIAGNOSTIC] Found {len(objects)} objects in bucket")

                    if objects:
                        image_logger.info("[S3_DIAGNOSTIC] Sample objects:")
                        for i, obj in enumerate(objects[:3]):
                            image_logger.info(f"[S3_DIAGNOSTIC]   {i+1}. {obj.key} ({obj.size} bytes)")

                    diagnostic_info['tests'].append({
                        'name': 'S3 Connectivity',
                        'status': 'success',
                        'details': {
                            'objects_found': len(objects),
                            'sample_objects': [obj.key for obj in objects[:3]] if objects else []
                        }
                    })
                else:
                    image_logger.warning("[S3_DIAGNOSTIC] S3 storage detected but bucket.objects not available")
                    diagnostic_info['tests'].append({
                        'name': 'Storage Type',
                        'status': 'info',
                        'details': {'note': 'S3 storage detected but bucket.objects not available'}
                    })
            else:
                image_logger.info(f"[S3_DIAGNOSTIC] Not S3 storage - using {diagnostic_info['storage_type']}")
                diagnostic_info['tests'].append({
                    'name': 'Storage Type',
                    'status': 'info',
                    'details': {
                        'storage_type': diagnostic_info['storage_type'],
                        'note': 'Not S3 storage - using local filesystem'
                    }
                })
        except Exception as e:
            image_logger.error(f"[S3_DIAGNOSTIC] Storage connectivity test failed: {str(e)}")
            image_logger.error(f"[S3_DIAGNOSTIC] Error type: {type(e).__name__}")
            diagnostic_info['tests'].append({
                'name': 'S3 Connectivity',
                'status': 'error',
                'details': {
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            })

        image_logger.info("[S3_DIAGNOSTIC] === TEST 3: File Upload Test ===")
        try:
            test_content = b"S3 diagnostic test file"
            test_filename = f"diagnostic_test_{int(timezone.now().timestamp())}.txt"

            image_logger.info(f"[S3_DIAGNOSTIC] Creating test file: {test_filename}")
            image_logger.info(f"[S3_DIAGNOSTIC] File content size: {len(test_content)} bytes")

            file_obj = ContentFile(test_content)
            image_logger.info("[S3_DIAGNOSTIC] ContentFile created, attempting to save...")

            saved_name = default_storage.save(test_filename, file_obj)
            image_logger.info(f"[S3_DIAGNOSTIC] File saved as: {saved_name}")

            exists = default_storage.exists(saved_name)
            image_logger.info(f"[S3_DIAGNOSTIC] File exists check: {exists}")

            file_url = 'No URL method'
            if hasattr(default_storage, 'url'):
                try:
                    file_url = default_storage.url(saved_name)
                    image_logger.info(f"[S3_DIAGNOSTIC] Generated URL: {file_url}")
                except Exception as url_error:
                    file_url = 'URL generation failed'
                    image_logger.warning(f"[S3_DIAGNOSTIC] URL generation failed: {str(url_error)}")
            else:
                image_logger.info("[S3_DIAGNOSTIC] Storage does not have URL method")

            cleanup_ok = False
            try:
                default_storage.delete(saved_name)
                cleanup_ok = True
                image_logger.info("[S3_DIAGNOSTIC] Test file cleanup successful")
            except Exception as cleanup_error:
                image_logger.warning(f"[S3_DIAGNOSTIC] Test file cleanup failed: {str(cleanup_error)}")

            upload_status = 'success' if exists else 'warning'
            image_logger.info(f"[S3_DIAGNOSTIC] File upload test result: {upload_status}")

            diagnostic_info['tests'].append({
                'name': 'File Upload Test',
                'status': upload_status,
                'details': {
                    'file_saved': saved_name,
                    'file_exists': exists,
                    'file_url': file_url,
                    'cleanup_successful': cleanup_ok
                }
            })
        except Exception as e:
            image_logger.error(f"[S3_DIAGNOSTIC] File upload test failed: {str(e)}")
            image_logger.error(f"[S3_DIAGNOSTIC] Error type: {type(e).__name__}")
            import traceback
            image_logger.error(f"[S3_DIAGNOSTIC] Traceback: {traceback.format_exc()}")

            diagnostic_info['tests'].append({
                'name': 'File Upload Test',
                'status': 'error',
                'details': {
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            })

        try:
            recent_uploads = ImageUpload.objects.filter(
                uploaded_at__gte=timezone.now() - timezone.timedelta(hours=24)
            ).order_by('-uploaded_at')[:5]

            diagnostic_info['recent_uploads'] = []
            for upload in recent_uploads:
                try:
                    diagnostic_info['recent_uploads'].append({
                        'id': upload.id,
                        'title': upload.title or f'Image {upload.id}',
                        'filename': upload.image.name if upload.image else 'No file',
                        'size': upload.image.size if upload.image else 0,
                        'uploaded_at': upload.uploaded_at,
                        'url': upload.image.url if upload.image else 'No URL'
                    })
                except:
                    diagnostic_info['recent_uploads'].append({
                        'id': upload.id,
                        'title': f'Image {upload.id}',
                        'filename': 'Error loading file info',
                        'size': 0,
                        'uploaded_at': upload.uploaded_at,
                        'url': 'No URL'
                    })
        except Exception as e:
            diagnostic_info['recent_uploads'] = []
            diagnostic_info['tests'].append({
                'name': 'Database Query',
                'status': 'error',
                'details': {'error': f'Could not query recent uploads: {str(e)}'}
            })

        end_time = timezone.now()
        execution_time = (end_time - start_time).total_seconds() * 1000

        test_counts = {'success': 0, 'error': 0, 'warning': 0, 'info': 0}
        for test in diagnostic_info['tests']:
            status = test.get('status', 'unknown')
            if status in test_counts:
                test_counts[status] += 1

        image_logger.info("[S3_DIAGNOSTIC] === DIAGNOSTIC SUMMARY ===")
        image_logger.info(f"[S3_DIAGNOSTIC] Execution time: {execution_time:.2f}ms")
        image_logger.info(f"[S3_DIAGNOSTIC] Tests run: {len(diagnostic_info['tests'])}")
        image_logger.info(f"[S3_DIAGNOSTIC] Results: {test_counts['success']} success, {test_counts['error']} errors, {test_counts['warning']} warnings, {test_counts['info']} info")
        image_logger.info(f"[S3_DIAGNOSTIC] Recent uploads found: {len(diagnostic_info['recent_uploads'])}")
        image_logger.info(f"[S3_DIAGNOSTIC] Folders detected: {diagnostic_info['folders']['count']}")
        image_logger.info("[S3_DIAGNOSTIC] === END DIAGNOSTIC ===")

        context = {
            'diagnostic_info': diagnostic_info,
            'title': 'Diagnóstico S3'
        }

        return render(request, 'gallery/pages/s3_diagnostic.html', context)

    except Exception as e:
        error_time = timezone.now()
        image_logger.critical(f"[S3_DIAGNOSTIC] CRITICAL ERROR at {error_time}: {str(e)}")
        image_logger.critical(f"[S3_DIAGNOSTIC] Error type: {type(e).__name__}")
        import traceback
        image_logger.critical(f"[S3_DIAGNOSTIC] Full traceback: {traceback.format_exc()}")

        context = {
            'diagnostic_info': {
                'timestamp': error_time,
                'user': request.user.username if request.user.is_authenticated else 'Anonymous',
                'error': f'Critical error in diagnostic: {str(e)}',
                'error_type': type(e).__name__,
                'tests': [{
                    'name': 'System Status',
                    'status': 'error',
                    'details': {'message': 'Diagnostic system failed to load'}
                }],
                'folders': {'count': 0, 'list': [], 'note': 'Diagnostic failed'},
                'recent_uploads': []
            },
            'title': 'Diagnóstico S3 - Error'
        }
        return render(request, 'gallery/pages/s3_diagnostic.html', context)
