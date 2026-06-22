from django.db import models

class Order(models.Model):
    PAYMENT_METHODS = (
        ('credit_wallet', 'افزایش اعتبار و پرداخت از کیف پول'),
        ('online', 'پرداخت اینترنتی هوشمند'),
        ('cod', 'پرداخت هنگام دریافت'),
    )

    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=11)
    postal_code = models.CharField(max_length=20)
    address = models.TextField()
    description = models.TextField(blank=True, null=True)

    # مبالغ
    subtotal = models.IntegerField()  
    discount = models.IntegerField(default=0)   
    tax = models.IntegerField(default=0)          # ← این رو اضافه کن
    shipping_cost = models.IntegerField(default=0) # ← این رو اضافه کن       
    total = models.IntegerField()                       

    # روش پرداخت و شرایط
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    terms_accepted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"سفارش #{self.id} - {self.full_name}"
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=200)
    quantity = models.IntegerField()
    price = models.IntegerField() 

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"