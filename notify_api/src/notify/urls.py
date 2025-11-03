from django.urls import path

from notify.views import NotifyViewSet

from .apps import NotifyConfig

app_name = NotifyConfig.name

urlpatterns = [
    path("", NotifyViewSet.as_view({"post": "create"}), name="notify"),
]
