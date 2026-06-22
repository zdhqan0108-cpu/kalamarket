from django.urls import path
from django.urls import re_path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('category/<str:cat_slug>/', views.category_products, name='category_products'),  # دسته اصلی
    path('subcategory/<str:sub_slug>/', views.subcategory_products, name='subcategory_products'),  # زیرمجموعه
    path('brand/<str:brand_slug>/', views.brand_products, name='brand_products'),
    path('product-type/<str:pt_slug>/', views.product_type_products, name='product_type'),
    path('add-to-cart/<int:product_id>/<int:variant_id>/', views.add_to_cart,name='add_to_cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart,name='remove_from_cart'),
    path('update-cart/<int:product_id>/', views.update_cart,name='update_cart'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),
    path('cart-detail/', views.cart_detail, name='cart_detail'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon, name='remove_coupon'),
    re_path(r'^product-detail/(?P<slug>[^/]+)/$', views.product_detail, name='product_detail'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    re_path(r'^share-email/(?P<slug>.+)/$', views.send_share_email, name='send_share_email'),
    path('notify/<int:product_id>/', views.notify_me, name='notify_me'),
    path('add-to-compare/<int:product_id>/', views.add_to_compare, name='add_to_compare'),
    path('remove-from-compare/<int:product_id>/', views.remove_from_compare, name='remove_from_compare'),
    path('compare/', views.comparison_page, name='comparison_page'),
    path('submit-review/', views.submit_review, name='submit_review'),
    path('wishlist/', views.wishlist, name='wishlist'),    
    
    ]