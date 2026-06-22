import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

def validate_english_password(value):
    if not re.match(r'^[A-Za-z0-9!@#$%^&*()_+{}|:<>?\-=\[\];\',./`~]+$', value):
        raise ValidationError(
            _('رمز عبور باید فقط شامل حروف انگلیسی، اعداد و کاراکترهای مجاز باشد.'),
            code='invalid_password'
        )