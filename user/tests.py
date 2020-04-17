import string
from itertools import combinations_with_replacement

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from projects.models import ProjectCategory
from user.forms import SignUpForm


class SignUpTests(TestCase):

    def setUp(self):
        self.base_password = "5PmS9zRSc7gdkC8J4tnotiEBHQDn"
        username_gen = combinations_with_replacement(string.ascii_lowercase, 3)
        self.next_username = lambda: "".join(username_gen.__next__())
        self.category1 = ProjectCategory.objects.create(name="Category 1")

    def test_sign_up_boundaries(self):
        def test_valid_sign_up(fields: dict, valid: bool):
            num_users_before = User.objects.count()
            supposed_num_users_after = num_users_before + 1 if valid else num_users_before

            username = self.next_username()
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
                'phone_number':          "98765432",
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

    def test_sign_up_form_two_way_domains(self):
        def test_field_combination(fields: dict, valid: bool):
            form_dict = {
                'username':              self.next_username(),
                'first_name':            "First",
                'last_name':             "Last",
                'competence_categories': [self.category1.pk],
                'phone_number':          "98765432",
                'country':               "Rohan",
                'state':                 "Null Island",
                'city':                  "Funkytown",
                'postal_code':           "1111",
                'street_address':        "Uptown New York 1",
                **fields,  # will overwrite any duplicate fields above
            }
            form = SignUpForm(form_dict)
            self.assertEqual(form.is_valid(), valid)

        # Longer strings make the passwords more similar to fields based on the same values
        a_token, b_token = "AAAA" * 5, "BBBB" * 5
        a_password, b_password = f"x1{a_token}1x", f"x1{b_token}1x"
        a_mail, b_mail = f"{a_token}@ma.il", f"{b_token}@ma.il"

        # The only two valid combinations
        test_field_combination({'password1': a_password, 'email': b_mail,
                                'password2': a_password, 'email_confirmation': b_mail, 'first_name': b_token}, True)
        test_field_combination({'password1': b_password, 'email': a_mail,
                                'password2': b_password, 'email_confirmation': a_mail, 'first_name': a_token}, True)

        # first_name is similar to password
        test_field_combination({'password1': a_password, 'email': b_mail,
                                'password2': a_password, 'email_confirmation': b_mail, 'first_name': a_token}, False)
        # email is similar to password
        test_field_combination({'password1': b_password, 'email': b_mail,
                                'password2': b_password, 'email_confirmation': b_mail, 'first_name': a_token}, False)
        # Both first_name and email are similar to password
        test_field_combination({'password1': a_password, 'email': a_mail,
                                'password2': a_password, 'email_confirmation': a_mail, 'first_name': a_token}, False)

        # Passwords are different
        test_field_combination({'password1': a_password, 'email': b_mail,
                                'password2': b_password, 'email_confirmation': b_mail, 'first_name': b_token}, False)
        # FIXME: it's never checked that email and email_confirmation are equal!
        # Emails are different
        # test_field_combination({'password1': b_password, 'email': a_mail,
        #                         'password2': b_password, 'email_confirmation': b_mail, 'first_name': a_token}, False)
        # Both passwords and emails are different
        test_field_combination({'password1': a_password, 'email': a_mail,
                                'password2': b_password, 'email_confirmation': b_mail, 'first_name': a_token}, False)

        # Emails are different and first_name is similar to password
        test_field_combination({'password1': a_password, 'email': a_mail,
                                'password2': a_password, 'email_confirmation': b_mail, 'first_name': a_token}, False)
