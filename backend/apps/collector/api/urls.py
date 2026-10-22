from django.urls import path

from apps.collector.api.views import SourceListView

urlpatterns = [path("sources", SourceListView.as_view(), name="sources")]
