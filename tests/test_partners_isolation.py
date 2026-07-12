import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def superuser():
    return User.objects.create_superuser(
        username='admin',
        email='admin@miluxious.com',
        password='adminpass123'
    )


@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def partner_a():
    from partners.models import Partner
    return Partner.objects.create(
        name='Muñecas y Peluches',
        slug='munecas-peluches',
        description='Socio de muñecas y peluches artesanales.',
        is_active=True
    )


@pytest.fixture
def partner_b():
    from partners.models import Partner
    return Partner.objects.create(
        name='Tazas Impresas',
        slug='tazas',
        description='Tazas con diseños artísticos impresos.',
        is_active=True
    )


@pytest.fixture
def partner_user_a_manager(user, partner_a):
    from partners.models import PartnerUser
    return PartnerUser.objects.create(
        user=user,
        partner=partner_a,
        role='manager',
        can_manage_products=True,
        can_manage_images=True,
        can_manage_orders=True
    )


@pytest.fixture
def category():
    from products.models import Category
    return Category.objects.create(
        name='General',
        slug='general',
        description='Categoría general'
    )


@pytest.fixture
def product_partner_a(partner_a, category):
    from products.models import Product
    return Product.objects.create(
        name='Muñeco Artesanal',
        slug='muneco-artesanal',
        description='Muñeco artesanal',
        price=100,
        jewelry_type='other',
        material='fabric',
        category=category,
        stock=5,
        available=True,
        partner=partner_a
    )


@pytest.fixture
def product_partner_b(partner_b, category):
    from products.models import Product
    return Product.objects.create(
        name='Taza Diseño Exclusivo',
        slug='taza-diseno',
        description='Taza impresa',
        price=50,
        jewelry_type='other',
        material='other',
        category=category,
        stock=10,
        available=True,
        partner=partner_b
    )


@pytest.fixture
def product_global(category):
    from products.models import Product
    return Product.objects.create(
        name='Anillo Oro',
        slug='anillo-oro',
        description='Anillo de oro Miluxious',
        price=500,
        jewelry_type='ring',
        material='metal',
        category=category,
        stock=3,
        available=True,
        partner=None
    )


@pytest.mark.django_db
def test_superuser_sees_all_partners(client, superuser, partner_a, partner_b):
    client.force_login(superuser)
    response = client.get(reverse('partners:list'))
    assert response.status_code == 200
    assert partner_a.name in response.content.decode()
    assert partner_b.name in response.content.decode()


@pytest.mark.django_db
def test_directory_public_for_logged_in_non_member(client, user):
    # La vitrina es pública: un cliente logueado sin membresía ve todas las tiendas.
    client.force_login(user)
    response = client.get(reverse('partners:list'))
    assert response.status_code == 200
    assert 'Muñecas y Peluches' in response.content.decode()
    assert 'Tazas Impresas' in response.content.decode()


@pytest.mark.django_db
def test_directory_public_for_partner_user(client, user, partner_a, partner_b, partner_user_a_manager):
    # Un partner user también ve el directorio completo (la vitrina no se filtra por membresía).
    client.force_login(user)
    response = client.get(reverse('partners:list'))
    assert response.status_code == 200
    assert partner_a.name in response.content.decode()
    assert partner_b.name in response.content.decode()


@pytest.mark.django_db
def test_global_products_are_visible_to_all(client, user, product_global):
    client.force_login(user)
    response = client.get(reverse('products:product_list'))
    assert response.status_code == 200
    assert product_global.name in response.content.decode()


@pytest.mark.django_db
def test_superuser_sees_all_products_in_admin(client, superuser, product_partner_a, product_partner_b):
    client.force_login(superuser)
    response = client.get(reverse('admin:products_product_changelist'))
    assert response.status_code == 200
    assert product_partner_a.name in response.content.decode()
    assert product_partner_b.name in response.content.decode()


@pytest.mark.django_db
def test_user_without_partner_cannot_access_admin(client, user):
    client.force_login(user)
    response = client.get(reverse('admin:index'))
    assert response.status_code == 302
