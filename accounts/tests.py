from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.factories import PASSWORD, make_customer, make_user

from .models import Customer

User = get_user_model()


def registration_data(**overrides):
    data = {
        "username": "maria",
        "first_name": "Maria",
        "last_name": "Silva",
        "email": "maria@example.com",
        "phone": "(86) 99999-0000",
        "address": "Rua das Flores, 10",
        "driver_license": "12345678900",
        "password1": PASSWORD,
        "password2": PASSWORD,
    }
    data.update(overrides)
    return data


class RegistrationTests(TestCase):
    def test_register_creates_user_and_customer_and_logs_in(self):
        response = self.client.post(reverse("accounts:register"), registration_data())
        self.assertRedirects(response, reverse("vehicles:list"))
        user = User.objects.get(username="maria")
        self.assertEqual(user.email, "maria@example.com")
        self.assertTrue(user.check_password(PASSWORD))
        self.assertEqual(user.customer.phone, "(86) 99999-0000")
        self.assertEqual(user.customer.driver_license, "12345678900")
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))

    def test_duplicate_email_is_rejected_case_insensitively(self):
        make_user("existente", email="maria@example.com")
        response = self.client.post(
            reverse("accounts:register"), registration_data(email="MARIA@example.com")
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "email", "Já existe uma conta com este e-mail.")
        self.assertFalse(User.objects.filter(username="maria").exists())

    def test_password_mismatch_is_rejected(self):
        response = self.client.post(
            reverse("accounts:register"), registration_data(password2="outra-senha-123")
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertFalse(User.objects.filter(username="maria").exists())

    def test_invalid_phone_is_rejected(self):
        response = self.client.post(reverse("accounts:register"), registration_data(phone="abc"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("phone", response.context["form"].errors)
        self.assertEqual(Customer.objects.count(), 0)

    def test_register_page_loads(self):
        self.assertEqual(self.client.get(reverse("accounts:register")).status_code, 200)

    def test_authenticated_user_is_redirected_away_from_register(self):
        self.client.force_login(make_user())
        response = self.client.get(reverse("accounts:register"))
        self.assertRedirects(response, reverse("vehicles:list"))


class LoginLogoutTests(TestCase):
    def test_customer_login_redirects_to_vehicle_list(self):
        customer = make_customer("cliente")
        response = self.client.post(
            reverse("accounts:login"), {"username": "cliente", "password": PASSWORD}
        )
        self.assertRedirects(response, reverse("vehicles:list"), fetch_redirect_response=False)
        self.assertEqual(self.client.session["_auth_user_id"], str(customer.user.pk))

    def test_staff_login_redirects_to_dashboard(self):
        make_user("equipe", staff=True)
        response = self.client.post(
            reverse("accounts:login"), {"username": "equipe", "password": PASSWORD}
        )
        self.assertRedirects(response, reverse("core:dashboard"), fetch_redirect_response=False)

    def test_login_respects_next_parameter(self):
        make_customer("cliente")
        target = reverse("reservations:list")
        response = self.client.post(
            reverse("accounts:login") + f"?next={target}",
            {"username": "cliente", "password": PASSWORD, "next": target},
        )
        self.assertRedirects(response, target, fetch_redirect_response=False)

    def test_wrong_password_shows_error(self):
        make_customer("cliente")
        response = self.client.post(
            reverse("accounts:login"), {"username": "cliente", "password": "errada"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Usuário ou senha incorretos")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_requires_post_and_logs_out(self):
        self.client.force_login(make_user())
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("core:home"))
        self.assertNotIn("_auth_user_id", self.client.session)


class ProfileTests(TestCase):
    def test_profile_requires_login(self):
        url = reverse("accounts:profile")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}")

    def test_profile_update(self):
        customer = make_customer("cliente")
        self.client.force_login(customer.user)
        response = self.client.post(
            reverse("accounts:profile"),
            {
                "user-first_name": "Novo",
                "user-last_name": "Nome",
                "user-email": "novo@example.com",
                "customer-phone": "(86) 98888-7777",
                "customer-address": "Rua Nova",
                "customer-driver_license": "999",
            },
        )
        self.assertRedirects(response, reverse("accounts:profile"))
        customer.refresh_from_db()
        customer.user.refresh_from_db()
        self.assertEqual(customer.user.first_name, "Novo")
        self.assertEqual(customer.user.email, "novo@example.com")
        self.assertEqual(customer.phone, "(86) 98888-7777")

    def test_profile_rejects_email_used_by_someone_else(self):
        make_user("outro", email="outro@example.com")
        customer = make_customer("cliente")
        self.client.force_login(customer.user)
        response = self.client.post(
            reverse("accounts:profile"),
            {
                "user-first_name": "A",
                "user-last_name": "B",
                "user-email": "outro@example.com",
                "customer-phone": "(86) 98888-7777",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["user_form"].errors)

    def test_profile_creates_missing_customer_for_staff_user(self):
        staff = make_user("equipe", staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse("accounts:profile")).status_code, 200)
        self.assertTrue(Customer.objects.filter(user=staff).exists())
