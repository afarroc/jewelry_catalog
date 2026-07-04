import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jewelry_catalog.settings')
django.setup()

import pytest
from decimal import Decimal
from products.models import Category, Product
from products.grid_packer import pack_products
from products.grid_items import GenericSlot


@pytest.fixture
def category(db):
    return Category.objects.create(
        name='Test Category',
        slug='test-category',
        description='A test category for testing'
    )


def _make_product(name, bento_size, rating=4.0, reviews=0, available=True, category=None):
    return Product.objects.create(
        name=name,
        slug=name.lower().replace(' ', '-'),
        description='Test product',
        price=Decimal('10.00'),
        jewelry_type='ring',
        material='metal',
        category=category,
        stock=1,
        available=available,
        bento_size=bento_size,
        average_rating=rating,
        review_count=reviews,
    )


def _products(result):
    return [p for _, _, _, _, p in result]


class TestPackProductsOrdering:
    def test_empty_list(self, db):
        assert pack_products([], columns=6) == []

    def test_single_item(self, db):
        p = _make_product('A', 'standard', rating=5.0)
        result = pack_products([p], columns=6)
        assert _products(result) == [p]

    def test_hero_fits_dynamically_in_6_columns(self, db):
        hero = _make_product('Hero', 'hero', rating=5.0)
        std = _make_product('B', 'standard', rating=4.0)
        result = pack_products([hero, std], columns=6)
        assert _products(result)[0] == hero
        assert len(result) == 2

    def test_preserves_input_order_for_equal_size(self, db):
        a = _make_product('A', 'standard', rating=5.0, reviews=10)
        b = _make_product('B', 'standard', rating=5.0, reviews=10)
        result = pack_products([a, b], columns=6)
        assert _products(result) == [a, b]

    def test_dense_packing_6_columns(self, db):
        products = [
            _make_product('A', 'standard', rating=5.0),
            _make_product('B', 'wide', rating=4.5),
            _make_product('C', 'tall', rating=4.0),
            _make_product('D', 'standard', rating=3.5),
            _make_product('E', 'featured', rating=3.0),
            _make_product('F', 'standard', rating=2.5),
        ]
        result = pack_products(products, columns=6)
        assert len(result) == len(products)
        assert {p.id for p in _products(result)} == {p.id for p in products}

    def test_mobile_two_columns(self, db):
        products = [
            _make_product('A', 'standard', rating=5.0),
            _make_product('B', 'standard', rating=4.0),
            _make_product('C', 'wide', rating=3.0),
        ]
        result = pack_products(products, columns=2)
        assert len(result) == len(products)
        assert {p.id for p in _products(result)} == {p.id for p in products}

    def test_does_not_filter_unavailable(self, db):
        a = _make_product('A', 'standard', rating=5.0, available=True)
        b = _make_product('B', 'standard', rating=4.0, available=False)
        result = pack_products([a, b], columns=6)
        assert len(result) == 2
        assert {p.id for p in _products(result)} == {a.id, b.id}

    def test_skips_oversized_when_narrower_than_width(self, db):
        p = _make_product('A', 'standard', rating=5.0)
        result = pack_products([p], columns=1)
        assert _products(result) == [p]

    def test_filler_pool_accepts_any_fit_size(self, db):
        main = [_make_product('A', 'wide', rating=5.0)]
        fillers = [_make_product('F1', 'wide', rating=1.0)]
        result = pack_products(main, columns=4, filler_pool=fillers)
        assert any(p.id == fillers[0].id for p in _products(result))

    def test_filler_pool_respects_limit(self, db):
        main = [_make_product('A', 'standard', rating=5.0)]
        fillers = [
            _make_product('F1', 'standard', rating=1.0),
            _make_product('F2', 'standard', rating=1.0),
        ]
        result = pack_products(main, columns=2, filler_pool=fillers[:1])
        assert any(p.id == fillers[0].id for p in _products(result))
        assert not any(p.id == fillers[1].id for p in _products(result))

    def test_filler_pool_skips_when_no_space(self, db):
        main = [_make_product('A', 'hero', rating=5.0)]
        fillers = [_make_product('F1', 'standard', rating=1.0)]
        result = pack_products(main, columns=4, filler_pool=fillers)
        assert not any(p.id == fillers[0].id for p in _products(result))
        assert len(result) == 1

    def test_generic_slot_packs_as_filler(self, db):
        main = [_make_product('A', 'wide', rating=5.0)]
        filler = GenericSlot(slot_type='subscription', label='News')
        result = pack_products(main, columns=4, filler_pool=[filler])
        assert any(getattr(p, 'is_filler', False) for p in _products(result))

    def test_generic_slots_mix_with_products(self, db):
        products = [_make_product('A', 'standard', rating=5.0)]
        fillers = [
            GenericSlot(slot_type='ad', label='Oferta'),
            GenericSlot(slot_type='icon_grid', label='Servicios'),
        ]
        result = pack_products(products, columns=4, filler_pool=fillers)
        assert any(getattr(p, 'slot_type', None) == 'ad' for p in _products(result))
        assert any(getattr(p, 'slot_type', None) == 'icon_grid' for p in _products(result))
