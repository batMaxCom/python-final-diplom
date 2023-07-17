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

"""
/api/v1/partner/update
GET /api/v1/partner/state
GET /api/v1/partner/order?token=b39d0f93f9e895b82f1724832b7c186a,
GET /api/v1/partner/order/124/?token=b39d0f93f9e895b82f1724832b7c186a,
"""

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('backend.urls', namespace='backend')),
    path('api/v1/', include('users.urls', namespace='users')),
    path('', include('frontend.urls', namespace='frontend')),
]
