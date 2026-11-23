import io

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from reservations.models import Reservation
from vehicles.models import Vehicle

from .factories import day, make_customer, make_reservation, make_user, make_vehicle
from .models import ContactMessage


class PublicPagesTests(TestCase):
    def test_home_lists_recent_vehicles(self):
        make_vehicle(name="Fusca Teste")
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fusca Teste")

    def test_home_shows_fleet_numbers_and_category_links(self):
        make_vehicle(category="suv")
        make_vehicle(category="suv", is_active=False)
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.context["fleet_count"], 1)
        tiles = {tile["value"]: tile["count"] for tile in response.context["tiles"]}
        self.assertEqual(tiles["suv"], 1)
        self.assertEqual(tiles["van"], 0)
        self.assertContains(response, reverse("vehicles:list") + "?category=suv")

    def test_home_without_vehicles(self):
        self.assertContains(self.client.get(reverse("core:home")), "Nenhum veículo cadastrado")

    def test_contact_form_saves_message(self):
        response = self.client.post(
            reverse("core:contact"),
            {"name": "Ana", "email": "ana@example.com", "message": "Olá!"},
        )
        self.assertRedirects(response, reverse("core:contact"))
        message = ContactMessage.objects.get()
        self.assertEqual((message.name, message.email), ("Ana", "ana@example.com"))

    def test_contact_form_validates(self):
        response = self.client.post(reverse("core:contact"), {"name": "", "email": "x", "message": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_error_pages_use_site_templates(self):
        response = self.client.get("/pagina-que-nao-existe/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Página não encontrada", status_code=404)


class StaffPanelTests(TestCase):
    def setUp(self):
        self.staff = make_user("equipe", staff=True)
        self.customer = make_customer("cliente")
        self.urls = [
            reverse("core:dashboard"),
            reverse("core:panel_vehicles"),
            reverse("core:panel_reservations"),
            reverse("core:panel_messages"),
        ]

    def test_panel_requires_login(self):
        for url in self.urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}")

    def test_panel_is_forbidden_for_customers(self):
        self.client.force_login(self.customer.user)
        for url in self.urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_panel_pages_load_for_staff(self):
        vehicle = make_vehicle()
        make_reservation(self.customer, vehicle, start=1, end=3)
        ContactMessage.objects.create(name="Ana", email="ana@example.com", message="Oi")
        self.client.force_login(self.staff)
        for url in self.urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_dashboard_numbers(self):
        rented = make_vehicle()
        make_vehicle()
        make_vehicle(is_active=False)
        make_reservation(self.customer, rented, start=-1, end=2)
        make_reservation(self.customer, make_vehicle(), start=0, end=3)
        self.client.force_login(self.staff)
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.context["vehicles_total"], 4)
        self.assertEqual(response.context["vehicles_active"], 3)
        self.assertEqual(response.context["rented_now"], 2)
        self.assertEqual(response.context["reservations_confirmed"], 2)
        self.assertEqual(len(response.context["pickups_today"]), 1)
        self.assertEqual(response.context["daily_sales"][0]["total_reservations"], 2)

    def test_panel_vehicle_search_includes_inactive(self):
        make_vehicle(name="Escondido", is_active=False)
        make_vehicle(name="Outro")
        self.client.force_login(self.staff)
        response = self.client.get(reverse("core:panel_vehicles"), {"q": "escond"})
        self.assertEqual([v.name for v in response.context["page_obj"]], ["Escondido"])

    def test_panel_reservations_filters(self):
        confirmed = make_reservation(self.customer, make_vehicle(name="Alfa"), start=1, end=3)
        cancelled = make_reservation(
            self.customer, make_vehicle(name="Beta"), start=1, end=3, status=Reservation.Status.CANCELLED
        )
        self.client.force_login(self.staff)
        url = reverse("core:panel_reservations")
        by_status = self.client.get(url, {"status": "cancelled"})
        self.assertEqual([r.pk for r in by_status.context["page_obj"]], [cancelled.pk])
        by_name = self.client.get(url, {"q": "alfa"})
        self.assertEqual([r.pk for r in by_name.context["page_obj"]], [confirmed.pk])

    def test_message_delete_is_staff_only_and_post_only(self):
        message = ContactMessage.objects.create(name="Ana", email="ana@example.com", message="Oi")
        url = reverse("core:message_delete", args=[message.pk])
        self.client.force_login(self.customer.user)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertTrue(ContactMessage.objects.exists())
        response = self.client.post(url)
        self.assertRedirects(response, reverse("core:panel_messages"))
        self.assertFalse(ContactMessage.objects.exists())


class DjangoAdminTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser("admin", "admin@example.com", "Senha-Forte-123")
        self.customer = make_customer("cliente")
        self.vehicle = make_vehicle()
        self.client.force_login(self.admin)

    def test_admin_pages_load(self):
        for model in ("accounts_customer", "vehicles_vehicle", "reservations_reservation", "core_contactmessage"):
            for kind in ("changelist", "add"):
                url = reverse(f"admin:{model}_{kind}")
                with self.subTest(url=url):
                    self.assertEqual(self.client.get(url).status_code, 200)

    def test_admin_change_pages_load(self):
        reservation = make_reservation(self.customer, self.vehicle)
        for url in (
            reverse("admin:reservations_reservation_change", args=[reservation.pk]),
            reverse("admin:vehicles_vehicle_change", args=[self.vehicle.pk]),
            reverse("admin:accounts_customer_change", args=[self.customer.pk]),
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_admin_rejects_overlapping_reservation(self):
        make_reservation(self.customer, self.vehicle, start=5, end=10)
        response = self.client.post(
            reverse("admin:reservations_reservation_add"),
            {
                "customer": self.customer.pk,
                "vehicle": self.vehicle.pk,
                "start_date": day(7).isoformat(),
                "end_date": day(9).isoformat(),
                "status": Reservation.Status.CONFIRMED,
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "já está reservado")
        self.assertEqual(Reservation.objects.count(), 1)

    def test_admin_cancel_action(self):
        reservation = make_reservation(self.customer, self.vehicle)
        self.client.post(
            reverse("admin:reservations_reservation_changelist"),
            {"action": "mark_cancelled", "_selected_action": [reservation.pk], "index": 0},
        )
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.CANCELLED)

    def test_admin_cancel_action_does_not_reopen_completed_reservations(self):
        reservation = make_reservation(
            self.customer, self.vehicle, status=Reservation.Status.COMPLETED
        )
        self.client.post(
            reverse("admin:reservations_reservation_changelist"),
            {"action": "mark_cancelled", "_selected_action": [reservation.pk], "index": 0},
        )
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.COMPLETED)


class ProjectHealthTests(TestCase):
    def test_django_system_check_passes(self):
        call_command("check", verbosity=0)

    def test_models_have_no_missing_migrations(self):
        try:
            call_command("makemigrations", "--check", "--dry-run", verbosity=0)
        except SystemExit:
            self.fail(
                "Há alterações nos modelos sem migração. "
                "Rode: python manage.py makemigrations"
            )

    def test_seed_demo_is_idempotent(self):
        out = io.StringIO()
        call_command("seed_demo", stdout=out)
        count = Vehicle.objects.count()
        self.assertGreaterEqual(count, 5)
        call_command("seed_demo", stdout=out)
        self.assertEqual(Vehicle.objects.count(), count)

    def test_seed_demo_customer_option(self):
        call_command("seed_demo", "--demo-customer", stdout=io.StringIO())
        user = get_user_model().objects.get(username="cliente_demo")
        self.assertTrue(user.customer.phone)
        self.assertTrue(user.check_password("demo12345"))
