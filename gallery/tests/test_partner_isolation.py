import pytest
from django.contrib.auth import get_user_model
from partners.models import Partner, PartnerUser
from gallery.models import ImageUpload
from gallery.admin import ImageUploadAdmin
from django.contrib.admin.sites import AdminSite

User = get_user_model()


@pytest.mark.django_db
def test_superuser_sees_all_images_in_admin():
    partner = Partner.objects.create(name='Test Partner', slug='test-partner')
    img1 = ImageUpload.objects.create(title='Global 1', image='https://example.com/1.jpg')
    img2 = ImageUpload.objects.create(title='Partner 1', image='https://example.com/2.jpg', partner=partner)

    admin_site = ImageUploadAdmin(ImageUpload, AdminSite())
    request = type('Request', (), {'user': User.objects.create_superuser('admin', 'admin@test.com', 'pass')})()
    qs = admin_site.get_queryset(request)
    assert qs.count() == 2


@pytest.mark.django_db
def test_partner_user_sees_only_their_partner_images():
    partner_a = Partner.objects.create(name='Partner A', slug='partner-a')
    partner_b = Partner.objects.create(name='Partner B', slug='partner-b')
    user = User.objects.create_user('editor_a', 'a@test.com', 'pass')
    PartnerUser.objects.create(user=user, partner=partner_a, role='editor', can_manage_images=True)
    img_global = ImageUpload.objects.create(title='Global', image='https://example.com/g.jpg')
    img_a = ImageUpload.objects.create(title='A', image='https://example.com/a.jpg', partner=partner_a)
    ImageUpload.objects.create(title='B', image='https://example.com/b.jpg', partner=partner_b)

    request = type('Request', (), {'user': user})()
    request.user_partners = {partner_a}

    admin_site = ImageUploadAdmin(ImageUpload, AdminSite())
    qs = admin_site.get_queryset(request)
    assert qs.count() == 1
    assert qs.first().partner == partner_a


@pytest.mark.django_db
def test_user_without_partner_sees_empty_queryset():
    user = User.objects.create_user('solo', 'solo@test.com', 'pass')
    ImageUpload.objects.create(title='X', image='https://example.com/x.jpg')

    request = type('Request', (), {'user': user})()
    request.user_partners = set()

    admin_site = ImageUploadAdmin(ImageUpload, AdminSite())
    qs = admin_site.get_queryset(request)
    assert qs.count() == 0
