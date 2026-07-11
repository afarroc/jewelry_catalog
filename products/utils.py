import io
import json
import time
import logging
from PIL import Image
import cloudinary.uploader
import cloudinary.api

logger = logging.getLogger('products')

PRODUCT_SIZES = {
    'card': (800, 800),
    'banner': (1200, 400),
    'hero': (1920, 600),
    '1x1': (800, 800),
    '1x2': (800, 1600),
    'wide': (1200, 600),
    'tall': (600, 1200),
    'classic': (800, 600),
}


def process_product_image(image_file, crop_data, product_instance):
    """
    Procesa una imagen original aplicando crop y resize, luego sube a Cloudinary.

    crop_data = {
        'ratio': str,
        'x': float, 'y': float,
        'width': float, 'height': float,
        'scale': float
    }
    Returns: secure_url (str)
    """
    ratio = crop_data.get('ratio', 'card')
    size = PRODUCT_SIZES.get(ratio, (800, 800))

    img = Image.open(image_file)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    scale = crop_data.get('scale', 1) or 1
    left = crop_data['x'] / scale
    top = crop_data['y'] / scale
    right = left + crop_data['width'] / scale
    bottom = top + crop_data['height'] / scale

    left = max(0, left)
    top = max(0, top)
    right = min(img.width, right)
    bottom = min(img.height, bottom)

    img_cropped = img.crop((left, top, right, bottom))
    img_resized = img_cropped.resize(size, Image.LANCZOS)

    buffer = io.BytesIO()
    fmt = img.format or 'JPEG'
    save_kwargs = {'format': fmt}
    if fmt == 'JPEG':
        save_kwargs['quality'] = 90
        save_kwargs['optimize'] = True
    img_resized.save(buffer, **save_kwargs)
    buffer.seek(0)

    # Ruta consistente: products/{slug}/{ratio}
    public_id = f"{product_instance.slug}/{ratio}"
    result = cloudinary.uploader.upload(
        buffer,
        folder='products',
        public_id=public_id,
        overwrite=True,
        resource_type='image',
    )
    logger.info(
        "Imagen procesada para producto %s ratio=%s size=%s url=%s",
        product_instance.slug, ratio, size, result['secure_url']
    )
    return result['secure_url']


def is_cloudinary_root_image(url, cloudinary_cloud_name):
    """
    Determina si una URL de Cloudinary corresponde a la raíz (sin subfolders).
    Maneja URLs con o sin versión Cloudinary.
    """
    if not url:
        return True
    url = str(url)
    if 'res.cloudinary.com' not in url or f'/{cloudinary_cloud_name}/' not in url:
        return True
    try:
        parts = url.split('/image/upload/')
        if len(parts) != 2:
            return True
        path = parts[1]
        # Quitar versión si existe (ej: v1783723855/sample.jpg)
        path_parts = path.split('/')
        if len(path_parts) > 1 and path_parts[0].startswith('v') and path_parts[0][1:].isdigit():
            path_parts = path_parts[1:]
        # Si queda solo el nombre de archivo, es raíz
        return len(path_parts) <= 1
    except Exception:
        return True


def get_cloudinary_folders(folder_path=''):
    """Obtiene subfolders de Cloudinary para un path dado."""
    try:
        if folder_path:
            result = cloudinary.api.subfolders(folder_path)
        else:
            result = cloudinary.api.root_folders()
        return result.get('folders', [])
    except Exception as e:
        logger.error(f"[CLOUDINARY] Error obteniendo folders: {e}")
        return []


def get_cloudinary_resources(folder_path='', max_results=30):
    """Obtiene recursos (imágenes) de Cloudinary para un path dado."""
    try:
        params = {
            'max_results': max_results,
            'resource_type': 'image',
            'type': 'upload',
        }
        if folder_path:
            params['prefix'] = folder_path
        result = cloudinary.api.resources(**params)
        return result.get('resources', [])
    except Exception as e:
        logger.error(f"[CLOUDINARY] Error obteniendo recursos: {e}")
        return []


def build_folder_breadcrumbs(folder_path):
    """Construye breadcrumbs de navegación para un path de folder."""
    if not folder_path:
        return []
    parts = folder_path.strip('/').split('/')
    breadcrumbs = []
    current_path = ''
    for part in parts:
        current_path = f"{current_path}/{part}" if current_path else part
        breadcrumbs.append({
            'name': part,
            'path': current_path,
        })
    return breadcrumbs

