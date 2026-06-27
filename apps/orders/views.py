from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .forms import CheckoutForm
from .models import Order, OrderItem
from apps.catalog.models import Product,ProductVariant,ProductDiscount
from django.db.models import F
from apps.orders.forms import CheckoutForm


@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, 'سبد خرید شما خالی است.')
        return redirect('catalog:cart_detail')

    cart_items = []
    subtotal = 0
    total_product_discount = 0

    for key, item in cart.items():
        # استخراج product_id و variant_id از کلید ترکیبی
        if '-' in key:
            parts = key.split('-')
            product_id = int(parts[0])
            variant_id = int(parts[1]) if len(parts) > 1 else None
        else:
            product_id = int(key)
            variant_id = None

        product = get_object_or_404(Product, id=product_id)
        quantity = item.get('quantity', 1)
        price = int(product.price)

        # پیدا کردن واریانت (اگر وجود داشته باشد)
        variant = None
        if variant_id:
            variant = product.variants.filter(id=variant_id).first()
            stock = variant.stock if variant else product.stock
        else:
            stock = product.stock

        # ====== بررسی موجودی ======
        if quantity > stock:
            messages.error(request, f'موجودی {product.title} کافی نیست.')
            return redirect('catalog:cart_detail')

        # تخفیف
        discount_obj = product.discounts.filter(
            is_active=True,
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now()
        ).first()

        if discount_obj:
            discount_percent = discount_obj.discount_percent
            discounted_price = price - (price * discount_percent // 100)
        else:
            discounted_price = price

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'price': discounted_price,
            'variant': variant,
            'stock': stock,
        })

        subtotal += price * quantity
        total_product_discount += (price - discounted_price) * quantity

    # ====== بقیه محاسبات ======
    after_product_discount = subtotal - total_product_discount
    coupon_percent = request.session.get('coupon_percent', 0)
    coupon_discount = after_product_discount * coupon_percent // 100 if coupon_percent else 0
    after_coupon = after_product_discount - coupon_discount
    tax = after_coupon * 9 // 100
    grand_total = after_coupon + tax

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.subtotal = subtotal
            order.discount = total_product_discount + coupon_discount
            order.shipping_cost = 0
            order.tax = tax
            order.total = grand_total
            order.save()

            # ذخیره آیتم‌های سفارش
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product_name=item['product'].title,
                    quantity=item['quantity'],
                    price=item['price'],
                )

            # ====== کاهش موجودی (بر اساس رنگ) ======
            for item in cart_items:
                if item['variant']:
                    # کاهش موجودی رنگ
                    variant = item['variant']
                    variant.stock = F('stock') - item['quantity']
                    variant.save(update_fields=['stock'])
                else:
                    # کاهش موجودی اصلی محصول
                    product = item['product']
                    product.stock = F('stock') - item['quantity']
                    product.save(update_fields=['stock'])

            request.session.pop('cart', None)
            request.session.pop('coupon_percent', None)
            
            messages.success(request, f'سفارش شما ثبت شد. شماره: {order.id}')
            return redirect('orders:checkout-complate-buy', order_id=order.id)
    else:
        form = CheckoutForm()

    context = {
        'form': form,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'total_product_discount': total_product_discount,
        'coupon_discount': coupon_discount,
        'coupon_percent': coupon_percent,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'orders/checkout.html', context)



def order_detail(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


def checkout_complate_buy(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    after_discount = order.subtotal - order.discount
    tax = after_discount * 9 // 100

    # ====== درصد تخفیف ======
    discount_percent = int((order.discount / order.subtotal) * 100) if order.subtotal > 0 else 0

    context = {
        'order': order,
        'discount_percent': discount_percent,
        'discount_amount': order.discount,
        'tax': tax,
        'final_total': order.total,  # همان grand_total از checkout
    }
    return render(request, 'orders/checkout_complate_buy.html', context)

@login_required

def user_orders(request):
        return render(request, 'orders/user_orders.html')




