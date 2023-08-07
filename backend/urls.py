from django.urls import path

from backend.views import CategoryView, ShopView, ProductView, PartnerUpdate, BasketView, OrderView, PartnerOrders, \
    PartnerState, PartnerOrdersList, ProductViewRetrieve

app_name = 'backend'
urlpatterns = [
    path('partner/update/', PartnerUpdate.as_view(), name='partner-update'),
    path('partner/status/<int:order_items_id>', PartnerState.as_view(), name='partner-state'), #изменение статуса заказа
    path('partner/orders/', PartnerOrdersList.as_view(), name='partner-orders_list'),
    path('partner/orders/<int:order_id>', PartnerOrders.as_view(), name='partner-orders'),
    path('categories/', CategoryView.as_view(), name='categories'),
    path('shops/', ShopView.as_view(), name='shops'),
    path('products/<int:product_id>', ProductViewRetrieve.as_view(), name='products'),
    path('products/', ProductView.as_view(), name='products'),
    path('basket/', BasketView.as_view(), name='basket'),
    path('order/', OrderView.as_view(), name='order'),

]
