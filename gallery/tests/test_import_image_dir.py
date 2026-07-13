import pytest
import tempfile
import os
from pathlib import Path
from io import BytesIO
from PIL import Image
from django.core.management import call_command
from django.test import TestCase
from gallery.models import ImageUpload
from partners.models import Partner


@pytest.mark.django_db
def test_import_image_dir_creates_images():
    partner = Partner.objects.create(name='Test Partner', slug='test-partner')

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create two fake image files
        for i in range(2):
            buf = BytesIO()
            Image.new('RGB', (10, 10), color=['red', 'blue'][i]).save(buf, format='JPEG')
            buf.seek(0)
            with open(os.path.join(tmpdir, f'image_{i}.jpg'), 'wb') as f:
                f.write(buf.getvalue())

        call_command('import_image_dir', tmpdir, '--partner', partner.slug, '--dry-run')

        # In dry-run, no records should be created
        assert ImageUpload.objects.count() == 0


@pytest.mark.django_db
def test_import_image_dir_errors_on_missing_directory():
    with pytest.raises(SystemExit):
        call_command('import_image_dir', '/nonexistent/path/12345')


@pytest.mark.django_db
def test_import_image_dir_errors_on_invalid_partner():
    with tempfile.TemporaryDirectory() as tmpdir:
        buf = BytesIO()
        Image.new('RGB', (10, 10)).save(buf, format='JPEG')
        buf.seek(0)
        with open(os.path.join(tmpdir, 'img.jpg'), 'wb') as f:
            f.write(buf.getvalue())

        with pytest.raises(SystemExit):
            call_command('import_image_dir', tmpdir, '--partner', 'invalid-slug')