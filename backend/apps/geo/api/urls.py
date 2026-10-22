from django.urls import path

from apps.geo.api.views import DistrictListView, RegionListView

urlpatterns = [
    path("geo/regions", RegionListView.as_view(), name="geo-regions"),
    path("geo/regions/<int:region_id>/districts", DistrictListView.as_view(), name="geo-districts"),
]
