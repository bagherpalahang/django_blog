from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from post.sitemaps import PostSitemap

sitemaps = {
    'posts' : PostSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('blog/', include('post.urls')),
    path('sitemap.xml', sitemap, {'sitemaps':sitemaps}, name='django.contrib.sitemaps.views.sitemap')
]
