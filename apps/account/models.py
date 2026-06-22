from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=11, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    receive_newsletter = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    title = models.CharField(max_length=50, verbose_name='عنوان (مثلاً خانه، محل کار)')
    full_name = models.CharField(max_length=100, verbose_name='نام و نام خانوادگی گیرنده')
    phone = models.CharField(max_length=15, verbose_name='شماره تماس')
    address = models.TextField(verbose_name='آدرس کامل')
    city = models.CharField(max_length=50, verbose_name='شهر')
    postal_code = models.CharField(max_length=20, verbose_name='کد پستی')
    created_at = models.DateTimeField(auto_now_add=True)

    def str(self):
        return f"{self.user.username} - {self.title}"