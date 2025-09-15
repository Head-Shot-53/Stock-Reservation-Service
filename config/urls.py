"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from config.health import (
    health_view,
    readiness_view,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/v1/", include("apps.inventory.api.v1.urls")),
    path("api/schema/",SpectacularAPIView.as_view(),name="api-schema"),
    path("api/docs/",SpectacularSwaggerView.as_view(url_name="api-schema"),name="api-docs"),
    path("api/redoc/",SpectacularRedocView.as_view(url_name="api-schema"),name="api-redoc"),

    path("health/",health_view,name="health"),
    path("ready/",readiness_view,name="ready"),
]
