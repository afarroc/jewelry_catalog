import pytest
from gallery.models import ImageUpload


def test_str_uses_title():
    img = ImageUpload(title='My Image')
    assert str(img) == 'My Image'


def test_str_fallback_uses_id():
    img = ImageUpload()
    assert str(img) == 'Image None'


@pytest.mark.django_db
def test_create_with_url():
    img = ImageUpload.objects.create(
        title='Test',
        image='https://res.cloudinary.com/dwidzc3k/image/upload/v123/test.jpg',
        asset_folder='gallery/2026/07',
    )
    assert img.id is not None
    assert img.asset_folder == 'gallery/2026/07'
