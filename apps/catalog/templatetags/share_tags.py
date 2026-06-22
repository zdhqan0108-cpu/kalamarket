from django import template
from django.template.defaultfilters import urlencode
from urllib.parse import quote

register = template.Library()

@register.simple_tag
def facebook_share_url(url, title=None):
    base_url = "https://www.facebook.com/sharer/sharer.php?u="
    return base_url + quote(url)

@register.simple_tag
def twitter_share_url(url, text):
    base_url = "https://twitter.com/intent/tweet?text="
    return base_url + quote(text) + "&url=" + quote(url)

@register.simple_tag
def whatsapp_share_url(url, text):
    base_url = "https://wa.me/?text="
    full_text = text + " " + url
    return base_url + quote(full_text)

@register.simple_tag
def telegram_share_url(url, text):
    base_url = "https://t.me/share/url?url="
    return base_url + quote(url) + "&text=" + quote(text)