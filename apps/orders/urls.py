from django.urls import path
from . import views

app_name="orders"

urlpatterns = [
    path('checkout/',views.checkout,name='checkout'),
    path('order/<int:order_id>/',views.order_detail,name='order_detail'),
    path('checkout-complate-buy/<int:order_id>/',views.checkout_complate_buy,name='checkout-complate-buy'),
    path('my-orders/',views.user_orders,name='user_orders')

]
