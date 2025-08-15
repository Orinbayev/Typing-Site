from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from typingapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("healthz", views.healthz, name="healthz"),
    path("", include(("typingapp.urls", "typingapp"), namespace="typingapp"))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
