import cloudinary.api
from django.core.management.base import BaseCommand
from products.models import ImageUpload
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sincroniza la tabla ImageUpload con el contenido real de Cloudinary.'

    def add_arguments(self, parser):
        parser.add_argument('--folder', type=str, default='', help='Sincronizar solo este folder (ej: products, gallery)')
        parser.add_argument('--reset', action='store_true', help='Borrar todos los ImageUpload antes de sincronizar')

    def handle(self, *args, **options):
        folder_filter = options.get('folder', '').strip()
        do_reset = options.get('reset', False)

        if do_reset:
            deleted, _ = ImageUpload.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Reset: eliminados {deleted} registros de ImageUpload.'))

        created = 0
        updated = 0
        existing = 0
        errors = 0
        seen_urls = set()

        def extract_folder_path(secure_url):
            """Extrae folder_path desde URL de Cloudinary."""
            try:
                url_path = secure_url.split('/image/upload/')[-1]
                parts = url_path.split('/')
                # Quitar versión si existe (v1783627893)
                real_parts = parts[1:] if len(parts) > 1 and parts[0].startswith('v') and parts[0][1:].isdigit() else parts
                # folder_path es todo menos el último segmento (archivo)
                if len(real_parts) > 1:
                    return '/'.join(real_parts[:-1])
                return ''
            except Exception:
                return ''

        def sync_resource(secure_url, public_id):
            nonlocal created, updated, existing, errors
            if secure_url in seen_urls:
                return
            seen_urls.add(secure_url)
            try:
                folder_path = extract_folder_path(secure_url)
                obj, was_created = ImageUpload.objects.get_or_create(
                    image=secure_url,
                    defaults={
                        'title': public_id.split('/')[-1] or secure_url.split('/')[-1],
                        'description': '',
                        'folder_path': folder_path,
                    }
                )
                if was_created:
                    created += 1
                else:
                    if obj.folder_path != folder_path:
                        obj.folder_path = folder_path
                        obj.save(update_fields=['folder_path'])
                        updated += 1
                    existing += 1
            except Exception as e:
                logger.error(f"Error creando ImageUpload para {secure_url}: {e}")
                errors += 1

        def sync_folder(path):
            # Recursos en este folder
            try:
                result = cloudinary.api.resources(
                    prefix=path if path else None,
                    max_results=500,
                    resource_type='image',
                    type='upload',
                )
                for res in result.get('resources', []):
                    sync_resource(res.get('secure_url', ''), res.get('public_id', ''))
            except Exception as e:
                logger.error(f"Error listando recursos en '{path}': {e}")

            # Subfolders
            try:
                if path:
                    folders = cloudinary.api.subfolders(path)
                else:
                    folders = cloudinary.api.root_folders()
                for folder in folders.get('folders', []):
                    folder_path = folder.get('path')
                    if folder_path:
                        sync_folder(folder_path)
            except Exception as e:
                logger.error(f"Error listando subfolders de '{path}': {e}")

        self.stdout.write('Sincronizando galería con Cloudinary...')
        sync_folder(folder_filter)

        self.stdout.write(self.style.SUCCESS(f'Sincronización completada:'))
        self.stdout.write(f'  Creados: {created}')
        self.stdout.write(f'  Ya existían: {existing}')
        self.stdout.write(f'  Actualizados: {updated}')
        self.stdout.write(f'  Errores: {errors}')
