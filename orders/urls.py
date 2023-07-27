"""orders URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import to include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularRedocView, SpectacularSwaggerView
from drf_spectacular.views import SpectacularAPIView



"""
/api/v1/partner/update
GET /api/v1/partner/state
GET /api/v1/partner/order?token=b39d0f93f9e895b82f1724832b7c186a,
GET /api/v1/partner/order/124/?token=b39d0f93f9e895b82f1724832b7c186a,
"""

urlpatterns = [
    # admin and reontend
    path('admin/', admin.site.urls),
    path('', include('frontend.urls', namespace='frontend')),
    path('social/', include('social_django.urls', namespace='social')),
    # API
    path('api/v1/', include('backend.urls', namespace='backend')),
    path('api/v1/', include('users.urls', namespace='users')),
    # Documentation
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Swagger UI:
    path('api/v1/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # Redoc UI:
    path('api/v1/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
