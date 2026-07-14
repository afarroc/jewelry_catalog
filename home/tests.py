import pytest
from django.urls import reverse
from django.conf import settings

from home.models import Banner
from home.hero_utils import build_hero_from_banners, HOME_HERO_DEFAULTS, TIENDAS_HERO_DEFAULTS


@pytest.mark.django_db
class TestBannerModel:
    def test_default_page_is_home(self):
        banner = Banner.objects.create(
            title='Test Banner',
            image='test.jpg',
        )
        assert banner.page == 'home'

    def test_page_choices(self):
        assert 'home' in dict(Banner.PAGE_CHOICES)
        assert 'tiendas' in dict(Banner.PAGE_CHOICES)

    def test_get_image_url_uses_cloudinary(self, settings):
        settings.CLOUDINARY_CLOUD_NAME = 'dwidzc3k'
        banner = Banner.objects.create(
            title='Cloudinary Banner',
            image='v1234567890/banner.jpg',
            page='home',
        )
        assert banner.get_image_url == 'https://res.cloudinary.com/dwidzc3k/image/upload/v1234567890/banner.jpg'

    def test_get_image_url_fallback_when_empty(self, settings):
        settings.CLOUDINARY_CLOUD_NAME = 'dwidzc3k'
        banner = Banner.objects.create(
            title='No Image Banner',
            image='',
            page='home',
        )
        assert banner.get_image_url == 'https://res.cloudinary.com/dwidzc3k/image/upload/placeholder-banner.jpg'


@pytest.mark.django_db
class TestBuildHeroFromBanners:
    def test_returns_defaults_when_no_banners(self):
        qs = Banner.objects.filter(page='home')
        hero = build_hero_from_banners(qs, HOME_HERO_DEFAULTS)
        assert hero == HOME_HERO_DEFAULTS

    def test_overrides_defaults_with_banner(self, settings):
        settings.CLOUDINARY_CLOUD_NAME = 'dwidzc3k'
        banner = Banner.objects.create(
            title='Custom Hero',
            subtitle='Custom eyebrow',
            description='Custom subtitle',
            button_text='Custom CTA',
            button_url='/custom/',
            image='custom.jpg',
            page='home',
            is_active=True,
        )
        qs = Banner.objects.filter(page='home')
        hero = build_hero_from_banners(qs, HOME_HERO_DEFAULTS)
        assert hero['title'] == 'Custom Hero'
        assert hero['eyebrow'] == 'Custom eyebrow'
        assert hero['subtitle'] == 'Custom subtitle'
        assert hero['primary_cta_text'] == 'Custom CTA'
        assert hero['primary_cta_url'] == '/custom/'
        assert hero['background_image_url'] == 'https://res.cloudinary.com/dwidzc3k/image/upload/custom.jpg'

    def test_partial_banner_keeps_other_defaults(self, settings):
        settings.CLOUDINARY_CLOUD_NAME = 'dwidzc3k'
        Banner.objects.create(
            title='Only Title',
            image='only-title.jpg',
            page='home',
            is_active=True,
        )
        qs = Banner.objects.filter(page='home')
        hero = build_hero_from_banners(qs, HOME_HERO_DEFAULTS)
        assert hero['title'] == 'Only Title'
        assert hero['eyebrow'] == HOME_HERO_DEFAULTS['eyebrow']
        assert hero['primary_cta_text'] == HOME_HERO_DEFAULTS['primary_cta_text']


@pytest.mark.django_db
class TestHomeViewHero:
    def test_home_returns_hero_defaults(self, client):
        response = client.get(reverse('home:index'))
        assert response.status_code == 200
        assert 'hero' in response.context
        assert response.context['hero']['title'] == HOME_HERO_DEFAULTS['title']

    def test_home_uses_home_banner_when_present(self, client, settings):
        settings.CLOUDINARY_CLOUD_NAME = 'dwidzc3k'
        Banner.objects.create(
            title='Home Banner',
            subtitle='Home eyebrow',
            description='Home subtitle',
            button_text='Shop',
            button_url='/shop/',
            image='home-banner.jpg',
            page='home',
            is_active=True,
        )
        response = client.get(reverse('home:index'))
        assert response.status_code == 200
        hero = response.context['hero']
        assert hero['title'] == 'Home Banner'
        assert hero['eyebrow'] == 'Home eyebrow'
        assert hero['background_image_url'] == 'https://res.cloudinary.com/dwidzc3k/image/upload/home-banner.jpg'

    def test_home_ignores_tiendas_banner(self, client, settings):
        settings.CLOUDINARY_CLOUD_NAME = 'dwidzc3k'
        Banner.objects.create(
            title='Tiendas Banner',
            subtitle='Tiendas eyebrow',
            description='Tiendas subtitle',
            button_text='Tiendas CTA',
            button_url='/tiendas/',
            image='tiendas-banner.jpg',
            page='tiendas',
            is_active=True,
        )
        response = client.get(reverse('home:index'))
        assert response.status_code == 200
        hero = response.context['hero']
        assert hero['title'] == HOME_HERO_DEFAULTS['title']
        assert 'Tiendas Banner' not in hero['title']
