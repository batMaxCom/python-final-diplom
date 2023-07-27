from django.urls import path

from frontend.views import products, register, basket, auth, log_out, email_verified

app_name = 'frontend'
urlpatterns = [
    path('register/', register, name='register'),
    path('login/', auth, name='login'),
    path('logout/', log_out, name='logout'),

    path('products/<int:product_id>', products, name='products'),
    path('products/', products, name='products'),
    path('basket/', basket, name='basket'),
    path('email-verified/', email_verified, name='email-verified'),



]