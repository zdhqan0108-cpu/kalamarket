from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils import timezone



class Category(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True, allow_unicode=True) # فیلد ساده
    image=models.ImageField(upload_to='category/')
    icon=models.ImageField(upload_to='category_icons/')

    def save(self, *args,**kwargs):
        if not self.slug:
            self.slug = slugify(self.title,allow_unicode=True)
        super().save(*args,**kwargs)

    

    def __str__(self):
        return self.title


class Subcategory(models.Model):
    category = models.ForeignKey(Category, related_name='subcategories', on_delete=models.CASCADE)
    parent=models.ForeignKey('self', on_delete=models.CASCADE,related_name='children',blank=True,null=True)
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True, allow_unicode=True) # فیلد ساده


    def save(self, *args,**kwargs):
        if not self.slug:
            self.slug = slugify(self.title,allow_unicode=True)
        super().save(*args,**kwargs)

    def __str__(self):
        return self.title

class Brand(models.Model):
    subcategory = models.ForeignKey(Subcategory, related_name='brands', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True, allow_unicode=True) # فیلد ساده

    def save(self, *args,**kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args,**kwargs)

    def __str__(self):
        return self.title


class ProductType(models.Model):
    subcategory = models.ForeignKey(Subcategory, related_name='product_type', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True, allow_unicode=True) # فیلد ساده

    def save(self, *args,**kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args,**kwargs)

    def __str__(self):
        return self.title


class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    subcategory = models.ForeignKey(Subcategory, related_name='products', on_delete=models.CASCADE,blank=True,null=True)
    product_type = models.ForeignKey(ProductType, related_name='products', on_delete=models.CASCADE,null=True,blank=True)
    brand = models.ForeignKey(Brand, related_name='products', on_delete=models.CASCADE,null=True,blank=True)
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=100, allow_unicode=True,blank=True) # فیلد ساده
    description = models.TextField(blank=True, null=True)
    average_rating = models.FloatField(default=0.0, editable=False)
    total_ratings = models.PositiveIntegerField(default=0, editable=False)
    price = models.DecimalField(max_digits=12, decimal_places=2,blank=True, null=True)
    stock = models.PositiveIntegerField(default=0 , blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_amazing = models.BooleanField(default=False, verbose_name="نمایش در بخش شگفت‌انگیز")
    is_moment = models.BooleanField(default=False, verbose_name="نمایش در پیشنهاد لحظه‌ای")
    moment_expiry = models.DateTimeField(blank=True, null=True, verbose_name="تاریخ انقضای پیشنهاد")

    @property
    def total_stock(self):
        """مجموع موجودی همه رنگ‌ها یا موجودی خود محصول"""
        if self.variants.exists():
            return sum(variant.stock for variant in self.variants.all())
        return self.stock

    def get_discount_percent(self):
       if self.discount_price and self.price > 0:
        return int(((self.price - self.discount_price) / self.price) * 100)
       return 0
    

    def save(self, *args,**kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args,**kwargs)

    def __str__(self):
        return self.title
        
class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)],help_text="درصد تخفیف (0 تا 100)")
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.code
    

class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # هر کاربر فقط یک بار می‌تواند لایک کند


class ProductNotification(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    method = models.CharField(max_length=10)  # 'email', 'sms', 'site'
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'email', 'phone', 'method')

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color = models.CharField(max_length=50)  # اسم رنگ (مثلاً مشکی، سفید)
    stock = models.PositiveIntegerField(default=0)  # موجودی این رنگ
    image = models.ImageField(upload_to='variants/', blank=True, null=True)  # عکس مخصوص این رنگ

    def __str__(self):
        return f"{self.product.title} - {self.color}"
    


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']  # نظرات جدیدتر اول نمایش داده شوند
        # هر کاربر فقط یک نظر می‌تواند برای هر محصول بدهد
        unique_together = ('user', 'product')

    def __str__(self):
        return f'{self.user} - {self.product} - {self.rating}⭐️'

class ProductSpecification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specs')
    key = models.CharField(max_length=100)    # مثلاً "ابعاد"
    value = models.CharField(max_length=200)  # مثلاً "7.9 × 71.8 × 151 میلی‌متر"

    def str(self):
        return f"{self.key}: {self.value}"
    


class ProductDiscount(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='discounts')
    discount_percent = models.PositiveIntegerField(verbose_name='درصد تخفیف')
    start_time = models.DateTimeField(verbose_name='زمان شروع',blank=True,null=True)
    end_time = models.DateTimeField(verbose_name='زمان پایان',blank=True,null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'تخفیف محصول'
        verbose_name_plural = 'تخفیف‌های محصولات'
    
    def is_valid(self):
        now = timezone.now()
        return self.is_active and self.start_time <= now <= self.end_time
    
    def __str__(self):
        return f'{self.product.title} - {self.discount_percent}%'
    
