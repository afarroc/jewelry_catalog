import json
import io

import pytest
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from gallery.forms import SimpleImageUploadForm, ProductImageCropForm


def _minimal_jpeg_bytes():
    buf = io.BytesIO()
    Image.new('RGB', (10, 10), color='red').save(buf, format='JPEG')
    buf.seek(0)
    return buf.getvalue()


def test_simple_image_upload_form_requires_image():
    form = SimpleImageUploadForm(data={'title': 'Test'})
    assert not form.is_valid()
    assert 'image' in form.errors


def test_simple_image_upload_form_valid():
    form = SimpleImageUploadForm(
        data={'title': 'Test', 'description': 'Desc'},
        files={'image': SimpleUploadedFile('test.jpg', _minimal_jpeg_bytes(), content_type='image/jpeg')}
    )
    assert form.is_valid()


def test_product_image_crop_form_requires_crop_data():
    form = ProductImageCropForm(data={})
    assert not form.is_valid()
    assert 'crop_data' in form.errors


def test_product_image_crop_form_valid_crop_data():
    crop_data = {
        'ratio': 'card',
        'x': 0, 'y': 0,
        'width': 100, 'height': 100,
        'scale': 1,
    }
    form = ProductImageCropForm(data={'crop_data': json.dumps(crop_data)})
    assert form.is_valid()


def test_product_image_crop_form_rejects_bad_crop_data():
    form = ProductImageCropForm(data={'crop_data': 'not-json'})
    assert not form.is_valid()
    assert 'crop_data' in form.errors



def test_product_image_crop_form_valid_crop_data():
    crop_data = {
        'ratio': 'card',
        'x': 0, 'y': 0,
        'width': 100, 'height': 100,
        'scale': 1,
    }
    import json
    form = ProductImageCropForm(data={'crop_data': json.dumps(crop_data)})
    assert form.is_valid()


def test_product_image_crop_form_rejects_bad_crop_data():
    form = ProductImageCropForm(data={'crop_data': 'not-json'})
    assert not form.is_valid()
    assert 'crop_data' in form.errors
