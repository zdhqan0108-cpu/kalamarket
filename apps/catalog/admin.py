from django.contrib import admin
from .models import Category, Subcategory, Product, ProductType, Brand, Coupon, Wishlist, ProductNotification, ProductVariant, Review, ProductSpecification,ProductDiscount

# --- ثبت مدل‌های ساده ---
admin.site.register(Category)
admin.site.register(Subcategory)
admin.site.register(ProductType)
admin.site.register(Brand)
admin.site.register(Wishlist)
admin.site.register(ProductNotification)


# --- کوپن تخفیف ---
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'valid_from', 'valid_to', 'active')

# --- Inline برای رنگ‌بندی (ProductVariant) ---
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('color', 'stock', 'image')

# --- Inline برای مشخصات فنی (ProductSpecification) ---
class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 5
    fields = ('key', 'value')

# --- ثبت نهایی مدل Product با هر دو Inline ---
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'price')
    inlines = [ProductVariantInline, ProductSpecificationInline]

# --- (اختیاری) ثبت مدل ProductVariant به صورت جدا ---
@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'color']

# --- ثبت مدل Review برای مدیریت نظرات ---
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'comment')

@admin.register(ProductDiscount)
class ProductDiscountAdmin(admin.ModelAdmin):
    list_display = ['product', 'discount_percent', 'start_time', 'end_time', 'is_active']
    list_filter = ['is_active']


