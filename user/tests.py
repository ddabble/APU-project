import string
from itertools import combinations_with_replacement

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from projects.models import ProjectCategory
from user.forms import SignUpForm


class SignUpTests(TestCase):

    def setUp(self):
        self.base_password = "pJoGzCbFzi8aXLQs"
        self.category1 = ProjectCategory.objects.create(name="Category 1")

    def test_sign_up_boundaries(self):
        username_gen = combinations_with_replacement(string.ascii_lowercase, 3)

        def test_valid_sign_up(fields: dict, valid: bool):
            num_users_before = User.objects.count()
            supposed_num_users_after = num_users_before + 1 if valid else num_users_before

            username = "".join(username_gen.__next__())
            email = f"{username}@email.com"
            password = fields.pop('password', self.base_password)
            form_dict = {
                'username':              username,
                'first_name':            "First",
                'last_name':             "Last",
                'competence_categories': [self.category1.pk],
                'email':                 email,
                'email_confirmation':    email,
                'password1':             password,
                'password2':             password,
                'phone_number':          "12345678",
                'country':               "Rohan",
                'state':                 "Null Island",
                'city':                  "Funkytown",
                'postal_code':           "1111",
                'street_address':        "Uptown New York 1",
                **fields,  # will overwrite any duplicate fields above
            }
            self.client.post(reverse('signup'), form_dict)

            self.assertEqual(User.objects.count(), supposed_num_users_after)

        username_max_length = SignUpForm.base_fields['username'].max_length
        test_valid_sign_up({'username': ""}, False)
        test_valid_sign_up({'username': "a"}, True)
        test_valid_sign_up({'username': "a" * username_max_length}, True)
        test_valid_sign_up({'username': "a" * (username_max_length + 1)}, False)

        password_min_length = 8
        test_valid_sign_up({'password': self._gen_password_of_length(password_min_length - 1)}, False)
        test_valid_sign_up({'password': self._gen_password_of_length(password_min_length)}, True)

    def _gen_password_of_length(self, length: int):
        repeated_base_password = self.base_password * (length // len(self.base_password) + 1)
        password = repeated_base_password[:length]
        self.assertEqual(len(password), length)
        return password
