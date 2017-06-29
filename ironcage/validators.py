from django.core.exceptions import ValidationError


def validate_max_words(max_words):
    def validator(value):
        num_words = len(value.split())
        if num_words > max_words:
            raise ValidationError(f'Field is too long: {num_words} words / {max_words} limit')
    return validator


#  https://code.djangoproject.com/ticket/28346
validate_max_300_words = validate_max_words(300)
validate_max_300_words.__name__ = 'validate_max_300_words'
