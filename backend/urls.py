from django.urls import path

from backend.views import CategoryView, ShopView, ProductView, PartnerUpdate

app_name = 'backend'
urlpatterns = [
    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
    # path('partner/state', PartnerState.as_view(), name='partner-state'), #получить статус получения заказов
    # path('partner/orders', PartnerOrders.as_view(), name='partner-orders'), #показать все заказы поставщика, а также получить состав отдельно каждого заказа
    path('categories', CategoryView.as_view(), name='categories'),
    path('shops', ShopView.as_view(), name='shops'),
    path('products', ProductView.as_view(), name='products'),
    # path('basket', BasketView.as_view(), name='basket'),
    # path('order', OrderView.as_view(), name='order'),

]