import pytest
from django.contrib.admin.sites import AdminSite
from gallery.admin import ImageUploadAdmin
from gallery.models import ImageUpload


@pytest.mark.django_db
def test_imageupload_admin_registered():
    from django.contrib import admin
    assert admin.site.is_registered(ImageUpload)


@pytest.mark.django_db
def test_imageupload_admin_list_display():
    ma = ImageUploadAdmin(ImageUpload, AdminSite())
    assert 'title' in ma.list_display
    assert 'partner' in ma.list_display
    assert 'image_preview' in ma.list_display
    assert 'uploaded_at' in ma.list_display


@pytest.mark.django_db
def test_imageupload_admin_search_fields():
    ma = ImageUploadAdmin(ImageUpload, AdminSite())
    assert 'title' in ma.search_fields
    assert 'description' in ma.search_fields


@pytest.mark.django_db
def test_imageupload_admin_list_filter():
    ma = ImageUploadAdmin(ImageUpload, AdminSite())
    assert 'partner' in ma.list_filter
    assert 'uploaded_at' in ma.list_filter


@pytest.mark.django_db
def test_imageupload_admin_autocomplete_fields():
    ma = ImageUploadAdmin(ImageUpload, AdminSite())
    assert 'partner' in ma.autocomplete_fields
