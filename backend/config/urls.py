from django.conf import settings
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path, re_path

from apps.common.views import api_not_found

api_v1: list[URLPattern | URLResolver] = [
    path("", include("apps.common.api.urls")),
    path("", include("apps.accounts.api.urls")),
    path("", include("apps.geo.api.urls")),
    path("", include("apps.collector.api.urls")),
    path("", include("apps.chat.api.urls")),
    re_path(r"^(?P<path>.*)$", api_not_found),
]

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("_allauth/", include("allauth.headless.urls")),
    # With HEADLESS_ONLY this mounts only the provider callbacks (e.g. Google's).
    path("accounts/", include("allauth.urls")),
    path("api/v1/", include(api_v1)),
]

handler404 = "apps.common.views.not_found"
handler500 = "apps.common.views.server_error"
