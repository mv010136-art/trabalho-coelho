import io
import shutil
import tempfile
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from core.factories import day, make_customer, make_reservation, make_user, make_vehicle
from reservations.models import Reservation

from .models import Vehicle


def names(response):
    return [vehicle.name for vehicle in response.context["page_obj"]]


class VehicleModelTests(TestCase):
    def test_plate_is_normalized_on_save(self):
        vehicle = make_vehicle(plate="abc-1d23")
        vehicle.refresh_from_db()
        self.assertEqual(vehicle.plate, "ABC1D23")

    def test_search_by_name_brand_plate_and_seats(self):
        gol = make_vehicle(name="Gol", brand="Volkswagen", plate="AAA1111", seats=5)
        van = make_vehicle(name="Master", brand="Renault", plate="BBB2222", seats=15)
        self.assertEqual(list(Vehicle.objects.search("gol")), [gol])
        self.assertEqual(list(Vehicle.objects.search("renault")), [van])
        self.assertEqual(list(Vehicle.objects.search("bbb-2222")), [van])
        self.assertEqual(list(Vehicle.objects.search("15")), [van])
        self.assertEqual(Vehicle.objects.search("").count(), 2)

    def test_available_between_excludes_overlapping_reservations(self):
        busy, free = make_vehicle(), make_vehicle()
        make_reservation(make_customer(), busy, start=2, end=6)
        available = Vehicle.objects.available_between(day(4), day(8))
        self.assertIn(free, available)
        self.assertNotIn(busy, available)

    def test_back_to_back_period_is_available(self):
        vehicle = make_vehicle()
        make_reservation(make_customer(), vehicle, start=2, end=6)
        self.assertTrue(vehicle.is_available_between(day(6), day(9)))
        self.assertTrue(vehicle.is_available_between(day(0), day(2)))
        self.assertFalse(vehicle.is_available_between(day(5), day(7)))

    def test_cancelled_reservation_does_not_block(self):
        vehicle = make_vehicle()
        make_reservation(make_customer(), vehicle, start=2, end=6, status=Reservation.Status.CANCELLED)
        self.assertTrue(vehicle.is_available_between(day(3), day(5)))

    def test_inactive_vehicle_is_never_available(self):
        vehicle = make_vehicle(is_active=False)
        self.assertFalse(vehicle.is_available_between(day(3), day(5)))
        self.assertNotIn(vehicle, Vehicle.objects.available_between(day(3), day(5)))

    def test_is_rented_now_and_label(self):
        vehicle = make_vehicle()
        self.assertEqual(vehicle.availability_label, "Disponível")
        make_reservation(make_customer(), vehicle, start=-1, end=2)
        self.assertTrue(vehicle.is_rented_now)
        self.assertEqual(vehicle.availability_label, "Alugado agora")
        annotated = Vehicle.objects.with_rented_now().get(pk=vehicle.pk)
        self.assertTrue(annotated.rented_now)
        vehicle.is_active = False
        self.assertEqual(vehicle.availability_label, "Fora da frota")


class VehiclePublicViewsTests(TestCase):
    def test_list_shows_only_active_vehicles(self):
        make_vehicle(name="Ativo")
        make_vehicle(name="Inativo", is_active=False)
        response = self.client.get(reverse("vehicles:list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(names(response), ["Ativo"])

    def test_list_search_by_text(self):
        make_vehicle(name="Gol", brand="Volkswagen")
        make_vehicle(name="Onix", brand="Chevrolet")
        response = self.client.get(reverse("vehicles:list"), {"q": "chev"})
        self.assertEqual(names(response), ["Onix"])

    def test_list_date_filter_hides_reserved_vehicles(self):
        busy = make_vehicle(name="Ocupado")
        make_vehicle(name="Livre")
        make_reservation(make_customer(), busy, start=2, end=6)
        response = self.client.get(
            reverse("vehicles:list"), {"pickup": day(3).isoformat(), "dropoff": day(5).isoformat()}
        )
        self.assertEqual(names(response), ["Livre"])

    def test_list_date_filter_requires_both_dates(self):
        make_vehicle(name="Gol")
        response = self.client.get(reverse("vehicles:list"), {"pickup": day(3).isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertEqual(names(response), ["Gol"])

    def test_list_date_filter_rejects_inverted_period(self):
        response = self.client.get(
            reverse("vehicles:list"), {"pickup": day(5).isoformat(), "dropoff": day(3).isoformat()}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A devolução deve ser posterior à retirada.")

    def test_new_and_popular_pages(self):
        first = make_vehicle(name="Primeiro")
        second = make_vehicle(name="Segundo")
        fan_a, fan_b = make_user(), make_user()
        first.likes.add(fan_a, fan_b)
        second.likes.add(fan_a)
        popular = self.client.get(reverse("vehicles:popular"))
        self.assertEqual(names(popular), ["Primeiro", "Segundo"])
        newest = self.client.get(reverse("vehicles:new"))
        self.assertEqual(names(newest), ["Segundo", "Primeiro"])

    def test_detail_page(self):
        vehicle = make_vehicle(name="Gol")
        response = self.client.get(vehicle.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gol")

    def test_detail_hides_inactive_vehicle_from_public_but_not_staff(self):
        vehicle = make_vehicle(is_active=False)
        self.assertEqual(self.client.get(vehicle.get_absolute_url()).status_code, 404)
        self.client.force_login(make_user(staff=True))
        self.assertEqual(self.client.get(vehicle.get_absolute_url()).status_code, 200)

    def test_unknown_vehicle_returns_404(self):
        self.assertEqual(self.client.get(reverse("vehicles:detail", args=[9999])).status_code, 404)


def vehicle_post_data(**overrides):
    data = {
        "name": "Gol",
        "brand": "Volkswagen",
        "plate": "abc-1234",
        "category": "sedan",
        "transmission": "automatic",
        "fuel": "flex",
        "seats": "5",
        "daily_rate": "99.90",
        "description": "Econômico",
        "is_active": "on",
    }
    data.update(overrides)
    return data


class VehicleStaffViewsTests(TestCase):
    def setUp(self):
        self.staff = make_user("equipe", staff=True)
        self.customer = make_customer("cliente")

    def test_create_requires_login(self):
        url = reverse("vehicles:create")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}")

    def test_create_is_forbidden_for_customers(self):
        self.client.force_login(self.customer.user)
        self.assertEqual(self.client.get(reverse("vehicles:create")).status_code, 403)
        response = self.client.post(reverse("vehicles:create"), vehicle_post_data())
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Vehicle.objects.count(), 0)

    def test_staff_can_create_vehicle(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("vehicles:create"), vehicle_post_data())
        self.assertRedirects(response, reverse("core:panel_vehicles"))
        vehicle = Vehicle.objects.get()
        self.assertEqual(vehicle.plate, "ABC1234")
        self.assertEqual(vehicle.daily_rate, Decimal("99.90"))
        self.assertEqual((vehicle.category, vehicle.transmission, vehicle.fuel), ("sedan", "automatic", "flex"))
        self.assertTrue(vehicle.is_active)

    def test_create_rejects_invalid_plate(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("vehicles:create"), vehicle_post_data(plate="12"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("plate", response.context["form"].errors)
        self.assertEqual(Vehicle.objects.count(), 0)

    def test_create_rejects_duplicate_plate(self):
        make_vehicle(plate="ABC1234")
        self.client.force_login(self.staff)
        response = self.client.post(reverse("vehicles:create"), vehicle_post_data(plate="abc 1234"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("plate", response.context["form"].errors)
        self.assertEqual(Vehicle.objects.count(), 1)

    def test_create_rejects_non_positive_rate_and_seats(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("vehicles:create"), vehicle_post_data(daily_rate="0", seats="0")
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("daily_rate", response.context["form"].errors)
        self.assertIn("seats", response.context["form"].errors)

    def test_staff_can_update_vehicle(self):
        vehicle = make_vehicle(name="Antigo", plate="AAA1111")
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("vehicles:update", args=[vehicle.pk]),
            vehicle_post_data(name="Novo", plate="AAA1111", daily_rate="150.00"),
        )
        self.assertRedirects(response, reverse("core:panel_vehicles"))
        vehicle.refresh_from_db()
        self.assertEqual(vehicle.name, "Novo")
        self.assertEqual(vehicle.daily_rate, Decimal("150.00"))

    def test_unchecking_active_removes_vehicle_from_public_list(self):
        vehicle = make_vehicle(name="Some", plate="AAA1111")
        self.client.force_login(self.staff)
        data = vehicle_post_data(name="Some", plate="AAA1111")
        del data["is_active"]
        self.client.post(reverse("vehicles:update", args=[vehicle.pk]), data)
        vehicle.refresh_from_db()
        self.assertFalse(vehicle.is_active)
        self.client.logout()
        self.assertEqual(names(self.client.get(reverse("vehicles:list"))), [])

    def test_delete_requires_post_to_delete(self):
        vehicle = make_vehicle()
        self.client.force_login(self.staff)
        url = reverse("vehicles:delete", args=[vehicle.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertTrue(Vehicle.objects.filter(pk=vehicle.pk).exists())
        response = self.client.post(url)
        self.assertRedirects(response, reverse("core:panel_vehicles"))
        self.assertFalse(Vehicle.objects.filter(pk=vehicle.pk).exists())

    def test_delete_is_forbidden_for_customers(self):
        vehicle = make_vehicle()
        self.client.force_login(self.customer.user)
        response = self.client.post(reverse("vehicles:delete", args=[vehicle.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Vehicle.objects.filter(pk=vehicle.pk).exists())

    def test_vehicle_with_reservations_cannot_be_deleted(self):
        vehicle = make_vehicle()
        make_reservation(self.customer, vehicle)
        self.client.force_login(self.staff)
        response = self.client.post(reverse("vehicles:delete", args=[vehicle.pk]), follow=True)
        self.assertTrue(Vehicle.objects.filter(pk=vehicle.pk).exists())
        self.assertContains(response, "possui reservas")

    def test_image_upload(self):
        buffer = io.BytesIO()
        Image.new("RGB", (4, 4), "red").save(buffer, format="PNG")
        upload = SimpleUploadedFile("foto.png", buffer.getvalue(), content_type="image/png")
        media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media_root, ignore_errors=True)
        with override_settings(MEDIA_ROOT=media_root):
            self.client.force_login(self.staff)
            response = self.client.post(
                reverse("vehicles:create"), {**vehicle_post_data(), "image": upload}
            )
            self.assertRedirects(response, reverse("core:panel_vehicles"))
            self.assertTrue(Vehicle.objects.get().image.name.startswith("vehicles/"))


class VehicleLikeTests(TestCase):
    def test_like_toggles_for_logged_user(self):
        vehicle = make_vehicle()
        user = make_user()
        self.client.force_login(user)
        url = reverse("vehicles:like", args=[vehicle.pk])
        self.client.post(url)
        self.assertEqual(vehicle.likes.count(), 1)
        self.client.post(url)
        self.assertEqual(vehicle.likes.count(), 0)

    def test_like_requires_login_and_post(self):
        vehicle = make_vehicle()
        url = reverse("vehicles:like", args=[vehicle.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response["Location"])
        self.assertEqual(vehicle.likes.count(), 0)
        self.client.force_login(make_user())
        self.assertEqual(self.client.get(url).status_code, 405)

    def test_like_does_not_follow_external_next(self):
        vehicle = make_vehicle()
        self.client.force_login(make_user())
        response = self.client.post(
            reverse("vehicles:like", args=[vehicle.pk]), {"next": "https://evil.example.com/"}
        )
        self.assertRedirects(response, vehicle.get_absolute_url())


class VehicleCatalogFilterTests(TestCase):
    def setUp(self):
        self.url = reverse("vehicles:list")
        make_vehicle(name="Mobi", brand="Fiat", category="economy", transmission="manual", seats=4, daily_rate=Decimal("80.00"))
        make_vehicle(name="Compass", brand="Jeep", category="suv", transmission="automatic", seats=5, daily_rate=Decimal("300.00"))
        make_vehicle(name="Master", brand="Renault", category="van", transmission="manual", seats=15, daily_rate=Decimal("430.00"))
        make_vehicle(name="Antigo", brand="Fiat", category="economy", is_active=False)

    def result(self, **params):
        response = self.client.get(self.url, params)
        self.assertEqual(response.status_code, 200)
        return names(response)

    def test_filter_by_category_brand_and_transmission(self):
        self.assertEqual(self.result(category="suv"), ["Compass"])
        self.assertEqual(self.result(brand="Fiat"), ["Mobi"])
        self.assertEqual(self.result(transmission="manual"), ["Master", "Mobi"])

    def test_filter_by_seats_and_price(self):
        self.assertEqual(self.result(min_seats=5), ["Compass", "Master"])
        self.assertEqual(self.result(max_price="300.00"), ["Compass", "Mobi"])
        self.assertEqual(self.result(min_seats=5, max_price="300"), ["Compass"])

    def test_filters_combine_with_text_search(self):
        self.assertEqual(self.result(q="o", transmission="manual"), ["Master", "Mobi"])
        self.assertEqual(self.result(q="jeep", transmission="manual"), [])

    def test_ordering_options(self):
        self.assertEqual(self.result(order="price_asc"), ["Mobi", "Compass", "Master"])
        self.assertEqual(self.result(order="price_desc"), ["Master", "Compass", "Mobi"])
        self.assertEqual(self.result(order="name"), ["Compass", "Master", "Mobi"])

    def test_invalid_filter_value_does_not_break_the_page(self):
        response = self.client.get(self.url, {"category": "invalido", "min_seats": "abc"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(len(names(response)), 3)

    def test_brand_choices_only_list_active_fleet(self):
        form = self.client.get(self.url).context["form"]
        brands = [value for value, _ in form.fields["brand"].choices if value]
        self.assertEqual(brands, ["Fiat", "Jeep", "Renault"])

    def test_filters_combine_with_availability_dates(self):
        compass = Vehicle.objects.get(name="Compass")
        make_reservation(make_customer(), compass, start=2, end=6)
        params = {"pickup": day(3).isoformat(), "dropoff": day(5).isoformat()}
        self.assertEqual(self.result(category="suv", **params), [])
        self.assertEqual(self.result(category="economy", **params), ["Mobi"])

    def test_result_count_and_clear_link(self):
        response = self.client.get(self.url, {"category": "suv"})
        self.assertContains(response, "1 veículo encontrado")
        self.assertContains(response, "Limpar filtros")

    def test_detail_shows_specs(self):
        vehicle = Vehicle.objects.get(name="Compass")
        response = self.client.get(vehicle.get_absolute_url())
        self.assertContains(response, "SUV")
        self.assertContains(response, "Automático")
