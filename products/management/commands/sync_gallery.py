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

        def sync_resource(secure_url, public_id, asset_folder):
            nonlocal created, updated, existing, errors
            if not secure_url or secure_url in seen_urls:
                return
            seen_urls.add(secure_url)
            try:
                obj, was_created = ImageUpload.objects.get_or_create(
                    image=secure_url,
                    defaults={
                        'title': public_id.split('/')[-1] or secure_url.split('/')[-1],
                        'description': '',
                        'asset_folder': asset_folder or '',
                    }
                )
                if was_created:
                    created += 1
                else:
                    if obj.asset_folder != (asset_folder or ''):
                        obj.asset_folder = asset_folder or ''
                        obj.save(update_fields=['asset_folder'])
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
                    sync_resource(
                        res.get('secure_url', ''),
                        res.get('public_id', ''),
                        res.get('asset_folder', ''),
                    )
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
