import pytest
from django.urls import reverse
from gallery.models import ImageUpload


@pytest.mark.django_db
def test_image_list_requires_login(client):
    url = reverse('gallery:image_list')
    response = client.get(url)
    assert response.status_code == 302
    assert 'login' in response.url


@pytest.mark.django_db
def test_image_upload_requires_login(client):
    url = reverse('gallery:image_upload')
    response = client.get(url)
    assert response.status_code == 302
    assert 'login' in response.url


@pytest.mark.django_db
def test_image_list_renders_for_authenticated_user(client, user):
    client.force_login(user)
    url = reverse('gallery:image_list')
    response = client.get(url)
    assert response.status_code == 200
    assert 'Imágenes Subidas' in response.content.decode()


@pytest.mark.django_db
def test_image_detail_view(client, user):
    img = ImageUpload.objects.create(
        title='Detail Test',
        image='https://res.cloudinary.com/dwidzc3k/image/upload/v123/detail.jpg',
    )
    client.force_login(user)
    url = reverse('gallery:image_detail', args=[img.id])
    response = client.get(url)
    assert response.status_code == 200
    assert 'Detail Test' in response.content.decode()


@pytest.mark.django_db
def test_image_delete_post_redirects(client, user):
    img = ImageUpload.objects.create(
        title='Delete Test',
        image='https://res.cloudinary.com/dwidzc3k/image/upload/v123/delete.jpg',
    )
    client.force_login(user)
    url = reverse('gallery:image_delete', args=[img.id])
    response = client.post(url)
    assert response.status_code == 302
    assert ImageUpload.objects.filter(id=img.id).exists() is False
