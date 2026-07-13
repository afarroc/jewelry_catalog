import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from products.models import Category, Product
from orders.models import Order, OrderItem
from decimal import Decimal


@pytest.fixture
def api_client():
    """API client fixture for testing."""
    return APIClient()


@pytest.fixture
def user():
    """Create a test user."""
    User = get_user_model()
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def category():
    """Create a test category."""
    return Category.objects.create(
        name='Test Category',
        slug='test-category',
        description='A test category for testing'
    )


@pytest.fixture
def product(category):
    """Create a test product."""
    return Product.objects.create(
        name='Test Product',
        slug='test-product',
        description='A test product for testing',
        price=Decimal('29.99'),
        jewelry_type='ring',
        material='metal',
        category=category,
        stock=10,
        available=True
    )


@pytest.fixture
def unavailable_product(category):
    """Create an unavailable test product."""
    return Product.objects.create(
        name='Unavailable Product',
        slug='unavailable-product',
        description='An unavailable test product',
        price=Decimal('19.99'),
        jewelry_type='bracelet',
        material='resin',
        category=category,
        stock=0,
        available=False
    )


@pytest.fixture
def order(user, product):
    """Create a test order."""
    order = Order.objects.create(
        user=user,
        subtotal=product.price,
        tax=product.price * Decimal('0.08'),
        shipping_cost=Decimal('5.00'),
        total=product.price + (product.price * Decimal('0.08')) + Decimal('5.00'),
        shipping_address='Test Address 123',
        billing_address='Test Billing Address 123',
        payment_method='credit_card'
    )

    # Create order item
    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=1,
        price=product.price
    )

    return order


@pytest.fixture
def authenticated_client(api_client, user):
    """API client authenticated as test user."""
    api_client.force_authenticate(user=user)
    return api_client