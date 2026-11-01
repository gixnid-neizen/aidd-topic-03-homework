from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class UserAuthenticationTests(TestCase):
    def test_registration_normalizes_email_and_logs_user_in(self):
        response = self.client.post(
            reverse("user:registration"),
            {
                "email": " Investor@Example.com ",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(response, reverse("dashboard:index"))
        user = get_user_model().objects.get(email="investor@example.com")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_registration_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse("user:registration"),
            {
                "email": "investor@example.com",
                "password1": "StrongPass123!",
                "password2": "DifferentPass123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            get_user_model().objects.filter(email="investor@example.com").exists()
        )

    def test_login_accepts_email_case_insensitively(self):
        user = get_user_model().objects.create_user(
            username="investor@example.com",
            email="investor@example.com",
            password="StrongPass123!",
        )
        response = self.client.post(
            reverse("user:auth"),
            {"email": "INVESTOR@EXAMPLE.COM", "password": "StrongPass123!"},
        )

        self.assertRedirects(response, reverse("dashboard:index"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
