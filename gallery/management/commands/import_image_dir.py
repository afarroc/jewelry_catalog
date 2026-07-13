import os
import logging
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from gallery.models import ImageUpload
from partners.models import Partner
import cloudinary.uploader

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Importa imágenes desde un directorio local hacia Cloudinary y crea registros ImageUpload. Uso: python manage.py import_image_dir <ruta_directorio> [--partner <partner_slug>]'

    def add_arguments(self, parser):
        parser.add_argument(
            'directory',
            type=str,
            help='Ruta absoluta o relativa del directorio con imágenes a importar'
        )
        parser.add_argument(
            '--partner',
            type=str,
            default=None,
            help='Slug del partner al que se asignarán las imágenes importadas. Si no se indica, las imágenes quedan sin partner (galería global).'
        )
        parser.add_argument(
            '--folder',
            type=str,
            default='gallery/imported',
            help='Carpeta destino en Cloudinary (default: gallery/imported)'
        )
        parser.add_argument(
            '--recursive',
            action='store_true',
            help='Buscar imágenes en subdirectorios recursivamente'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular la importación sin subir archivos ni crear registros'
        )

    def handle(self, *args, **options):
        directory = options['directory']
        partner_slug = options.get('partner')
        cloudinary_folder = options.get('folder', 'gallery/imported')
        recursive = options.get('recursive', False)
        dry_run = options.get('dry-run', False)

        # Validar directorio
        dir_path = Path(directory)
        if not dir_path.exists():
            self.stdout.write(self.style.ERROR(f'El directorio no existe: {directory}'))
            return
        if not dir_path.is_dir():
            self.stdout.write(self.style.ERROR(f'La ruta no es un directorio: {directory}'))
            return

        # Validar partner
        partner = None
        if partner_slug:
            try:
                partner = Partner.objects.get(slug=partner_slug)
                self.stdout.write(self.style.SUCCESS(f'Partner detectado: {partner.name} (slug={partner.slug})'))
            except Partner.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Partner no encontrado con slug: {partner_slug}'))
                self.stdout.write('Partners disponibles:')
                for p in Partner.objects.all():
                    self.stdout.write(f'  - {p.slug}: {p.name}')
                return

        # Extensiones de imagen soportadas
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'}

        # Recolectar archivos
        if recursive:
            image_files = []
            for root, dirs, files in os.walk(dir_path):
                for f in files:
                    if Path(f).suffix.lower() in image_extensions:
                        image_files.append(Path(root) / f)
        else:
            image_files = [
                f for f in dir_path.iterdir()
                if f.is_file() and f.suffix.lower() in image_extensions
            ]

        if not image_files:
            self.stdout.write(self.style.WARNING(f'No se encontraron imágenes en: {directory}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Encontradas {len(image_files)} imágenes para importar.'))
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: no se subirán archivos ni se crearán registros.'))

        created = 0
        skipped = 0
        errors = 0

        for img_path in image_files:
            filename = img_path.name
            self.stdout.write(f'Procesando: {filename}')

            if dry_run:
                created += 1
                continue

            try:
                # Subir a Cloudinary
                result = cloudinary.uploader.upload(
                    str(img_path),
                    folder=cloudinary_folder,
                    overwrite=True,
                    resource_type='image',
                )
                secure_url = result.get('secure_url', '')
                public_id = result.get('public_id', '')

                if not secure_url:
                    self.stdout.write(self.style.WARNING(f'  ⚠ No se obtuvo URL para {filename}'))
                    skipped += 1
                    continue

                # Crear registro ImageUpload
                title = img_path.stem.replace('_', ' ').replace('-', ' ').title()
                asset_folder = cloudinary_folder

                image_upload, was_created = ImageUpload.objects.get_or_create(
                    image=secure_url,
                    defaults={
                        'title': title,
                        'description': f'Importado desde {directory}',
                        'asset_folder': asset_folder,
                        'partner': partner,
                    }
                )

                if was_created:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Creado: {title} (ID={image_upload.id})'))
                    created += 1
                else:
                    self.stdout.write(self.style.WARNING(f'  ⚠ Ya existía: {title} (ID={image_upload.id})'))
                    skipped += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error importando {filename}: {e}'))
                logger.error(f'Error importando {filename}: {e}', exc_info=True)
                errors += 1

        # Resumen
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Resumen de importación ==='))
        self.stdout.write(f'  Creados: {created}')
        self.stdout.write(f'  Omitidos: {skipped}')
        self.stdout.write(f'  Errores: {errors}')
        self.stdout.write(f'  Total procesados: {len(image_files)}')

        if dry_run:
            self.stdout.write(self.style.WARNING('(dry-run: no se realizaron cambios reales)'))
