from django.core.exceptions import ValidationError
from django.test import TestCase

from ironcage import validators


class ValidatorTests(TestCase):
    def test_validate_max_words_when_valid(self):
        validator = validators.validate_max_words(5)
        validator('cat sat on the mat')

    def test_validate_max_words_when_not_valid(self):
        validator = validators.validate_max_words(5)
        with self.assertRaises(ValidationError):
            validator('the cat sat on the mat')
