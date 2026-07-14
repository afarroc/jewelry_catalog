import pytest
from django.urls import reverse
from django.conf import settings

from home.models import Banner
from partners.models import Partner
from home.hero_utils import TIENDAS_HERO_DEFAULTS


@pytest.mark.django_db
class TestPartnerListViewHero:
    def test_injects_hero_defaults_when_no_banners(self, client):
        Partner.objects.create(
            name='Tienda Test',
            slug='tienda-test',
            description='Test',
            is_active=True,
        )
        response = client.get(reverse('partners:list'))
        assert response.status_code == 200
        assert 'hero' in response.context
        assert response.context['hero']['title'] == TIENDAS_HERO_DEFAULTS['title']

    def test_uses_tiendas_banner_when_present(self, client, settings):
        settings.CLOUDINARY_CLOUD_NAME = 'dwidzc3k'
        Partner.objects.create(
            name='Tienda Test',
            slug='tienda-test',
            description='Test',
            is_active=True,
        )
        Banner.objects.create(
            title='Tiendas Hero',
            subtitle='Ecosistema custom',
            description='Subtítulo custom',
            button_text='Ver ahora',
            button_url='/products/',
            image_filename='tiendas-hero.jpg',
            page='tiendas',
            is_active=True,
        )
        response = client.get(reverse('partners:list'))
        assert response.status_code == 200
        hero = response.context['hero']
        assert hero['title'] == 'Tiendas Hero'
        assert hero['eyebrow'] == 'Ecosistema custom'
        assert hero['subtitle'] == 'Subtítulo custom'
        assert hero['primary_cta_text'] == 'Ver ahora'
        assert hero['primary_cta_url'] == '/products/'
        assert hero['background_image_url'] == 'https://res.cloudinary.com/dwidzc3k/image/upload/tiendas-hero.jpg'

    def test_ignores_home_banner(self, client, settings):
        settings.CLOUDINARY_CLOUD_NAME = 'dwidzc3k'
        Partner.objects.create(
            name='Tienda Test',
            slug='tienda-test',
            description='Test',
            is_active=True,
        )
        Banner.objects.create(
            title='Home Banner',
            subtitle='Home eyebrow',
            description='Home subtitle',
            button_text='Home CTA',
            button_url='/',
            image_filename='home-banner.jpg',
            page='home',
            is_active=True,
        )
        response = client.get(reverse('partners:list'))
        assert response.status_code == 200
        hero = response.context['hero']
        assert hero['title'] == TIENDAS_HERO_DEFAULTS['title']
        assert 'Home Banner' not in hero['title']

    def test_renders_hero_section_in_template(self, client):
        Partner.objects.create(
            name='Tienda Test',
            slug='tienda-test',
            description='Test',
            is_active=True,
        )
        response = client.get(reverse('partners:list'))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'class="hero"' in content
        assert TIENDAS_HERO_DEFAULTS['title'] in content

    def test_renders_custom_hero_in_template(self, client, settings):
        settings.CLOUDINARY_CLOUD_NAME = 'dwidzc3k'
        partner = Partner.objects.create(
            name='Tienda Test',
            slug='tienda-test',
            description='Test',
            is_active=True,
        )
        Banner.objects.create(
            title='Banner Custom Tiendas',
            subtitle='Eyebrow custom',
            description='Subtítulo custom',
            button_text='CTA custom',
            button_url='/custom/',
            image_filename='custom.jpg',
            page='tiendas',
            is_active=True,
        )
        response = client.get(reverse('partners:list'))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Banner Custom Tiendas' in content
        assert 'Eyebrow custom' in content
        assert 'Subtítulo custom' in content
        assert 'CTA custom' in content

    def test_partners_grid_still_visible(self, client):
        partner_a = Partner.objects.create(
            name='Tienda A',
            slug='tienda-a',
            description='A',
            is_active=True,
        )
        partner_b = Partner.objects.create(
            name='Tienda B',
            slug='tienda-b',
            description='B',
            is_active=True,
        )
        response = client.get(reverse('partners:list'))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Tienda A' in content
        assert 'Tienda B' in content
