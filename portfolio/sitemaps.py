from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from . import models


class StaticViewSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.8

    def items(self):
        return ['index', 'research', 'publications', 'contact']

    def location(self, item):
        return reverse(f'portfolio:{item}')


class PublicationSitemap(Sitemap):
    changefreq = 'yearly'
    priority = 0.6

    def items(self):
        return models.Publication.objects.all()

    # Uses Publication.get_absolute_url().


SITEMAPS = {
    'static': StaticViewSitemap,
    'publications': PublicationSitemap,
}
