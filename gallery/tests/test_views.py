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


@pytest.mark.django_db
def test_bulk_delete_requires_post(client, user):
    client.force_login(user)
    url = reverse('gallery:image_bulk_delete')
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_bulk_delete_removes_selected_images(client, user):
    img1 = ImageUpload.objects.create(title='A', image='https://example.com/a.jpg')
    img2 = ImageUpload.objects.create(title='B', image='https://example.com/b.jpg')
    img3 = ImageUpload.objects.create(title='C', image='https://example.com/c.jpg')

    client.force_login(user)
    url = reverse('gallery:image_bulk_delete')
    response = client.post(url, data={'selected_images': [str(img1.id), str(img2.id)]})
    assert response.status_code == 302
    assert ImageUpload.objects.filter(id=img1.id).exists() is False
    assert ImageUpload.objects.filter(id=img2.id).exists() is False
    assert ImageUpload.objects.filter(id=img3.id).exists() is True


@pytest.mark.django_db
def test_bulk_delete_empty_selection_redirects_with_message(client, user):
    client.force_login(user)
    url = reverse('gallery:image_bulk_delete')
    response = client.post(url, data={'selected_images': []})
    assert response.status_code == 302
