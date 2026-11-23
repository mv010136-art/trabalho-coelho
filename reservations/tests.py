from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from core.factories import day, make_customer, make_reservation, make_user, make_vehicle

from .models import Reservation

S = Reservation.Status


class ReservationModelTests(TestCase):
    def setUp(self):
        self.customer = make_customer()
        self.vehicle = make_vehicle(daily_rate=Decimal("100.00"))

    def test_total_is_days_times_daily_rate(self):
        reservation = make_reservation(self.customer, self.vehicle, start=1, end=4)
        self.assertEqual(reservation.days, 3)
        self.assertEqual(reservation.daily_rate, Decimal("100.00"))
        self.assertEqual(reservation.total_price, Decimal("300.00"))

    def test_daily_rate_is_frozen_when_vehicle_price_changes(self):
        reservation = make_reservation(self.customer, self.vehicle, start=1, end=3)
        self.vehicle.daily_rate = Decimal("250.00")
        self.vehicle.save()
        reservation = Reservation.objects.get(pk=reservation.pk)
        reservation.notes = "alterado"
        reservation.save()
        reservation.refresh_from_db()
        self.assertEqual(reservation.daily_rate, Decimal("100.00"))
        self.assertEqual(reservation.total_price, Decimal("200.00"))

    def test_total_is_recalculated_when_dates_change(self):
        reservation = make_reservation(self.customer, self.vehicle, start=1, end=3)
        reservation.end_date = day(6)
        reservation.save()
        reservation.refresh_from_db()
        self.assertEqual(reservation.total_price, Decimal("500.00"))

    def test_conflicts_detects_every_kind_of_overlap(self):
        make_reservation(self.customer, self.vehicle, start=10, end=15)
        overlapping = [(8, 11), (14, 18), (11, 13), (8, 18), (10, 15)]
        for start, end in overlapping:
            with self.subTest(start=start, end=end):
                self.assertTrue(
                    Reservation.conflicts(self.vehicle.pk, day(start), day(end)).exists()
                )

    def test_back_to_back_reservations_do_not_conflict(self):
        make_reservation(self.customer, self.vehicle, start=10, end=15)
        self.assertFalse(Reservation.conflicts(self.vehicle.pk, day(15), day(18)).exists())
        self.assertFalse(Reservation.conflicts(self.vehicle.pk, day(7), day(10)).exists())

    def test_cancelled_and_other_vehicle_do_not_conflict(self):
        make_reservation(self.customer, self.vehicle, start=10, end=15, status=S.CANCELLED)
        self.assertFalse(Reservation.conflicts(self.vehicle.pk, day(11), day(13)).exists())
        other = make_vehicle()
        make_reservation(self.customer, other, start=10, end=15)
        self.assertFalse(Reservation.conflicts(self.vehicle.pk, day(11), day(13)).exists())

    def test_full_clean_rejects_overlap(self):
        make_reservation(self.customer, self.vehicle, start=10, end=15)
        duplicate = Reservation(
            customer=self.customer, vehicle=self.vehicle, start_date=day(12), end_date=day(14)
        )
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_full_clean_ignores_itself_when_editing(self):
        reservation = make_reservation(self.customer, self.vehicle, start=10, end=15)
        reservation.end_date = day(16)
        reservation.full_clean()  # não deve levantar

    def test_full_clean_rejects_end_not_after_start(self):
        reservation = Reservation(
            customer=self.customer, vehicle=self.vehicle, start_date=day(5), end_date=day(5)
        )
        with self.assertRaises(ValidationError) as context:
            reservation.full_clean()
        self.assertIn("end_date", context.exception.message_dict)

    def test_full_clean_rejects_new_reservation_for_inactive_vehicle(self):
        inactive = make_vehicle(is_active=False)
        reservation = Reservation(
            customer=self.customer, vehicle=inactive, start_date=day(5), end_date=day(7)
        )
        with self.assertRaises(ValidationError):
            reservation.full_clean()

    def test_database_constraint_blocks_inverted_dates(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Reservation.objects.create(
                customer=self.customer, vehicle=self.vehicle, start_date=day(5), end_date=day(3)
            )

    def test_vehicle_and_customer_are_protected_from_deletion(self):
        make_reservation(self.customer, self.vehicle)
        with self.assertRaises(ProtectedError):
            self.vehicle.delete()
        with self.assertRaises(ProtectedError):
            self.customer.delete()

    def test_relationships(self):
        reservation = make_reservation(self.customer, self.vehicle)
        self.assertIn(reservation, self.customer.reservations.all())
        self.assertIn(reservation, self.vehicle.reservations.all())


def booking_data(start=5, end=8, **extra):
    data = {"start_date": day(start).isoformat(), "end_date": day(end).isoformat(), "notes": ""}
    data.update(extra)
    return data


class ReservationCreateViewTests(TestCase):
    def setUp(self):
        self.customer = make_customer("cliente")
        self.vehicle = make_vehicle(daily_rate=Decimal("120.00"))
        self.url = reverse("reservations:create", args=[self.vehicle.pk])

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.url}")

    def test_form_page_loads_and_prefills_dates_from_query(self):
        self.client.force_login(self.customer.user)
        response = self.client.get(self.url, {"pickup": day(5).isoformat(), "dropoff": day(8).isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, day(5).isoformat())

    def test_customer_can_book_a_vehicle(self):
        self.client.force_login(self.customer.user)
        response = self.client.post(self.url, booking_data(5, 8))
        reservation = Reservation.objects.get()
        self.assertRedirects(response, reservation.get_absolute_url())
        self.assertEqual(reservation.customer, self.customer)
        self.assertEqual(reservation.vehicle, self.vehicle)
        self.assertEqual(reservation.status, S.CONFIRMED)
        self.assertEqual(reservation.total_price, Decimal("360.00"))

    def test_overlapping_booking_is_rejected(self):
        make_reservation(make_customer(), self.vehicle, start=5, end=10)
        self.client.force_login(self.customer.user)
        response = self.client.post(self.url, booking_data(8, 12))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "já está reservado")
        self.assertEqual(Reservation.objects.count(), 1)

    def test_same_period_is_rejected_for_a_second_customer(self):
        self.client.force_login(self.customer.user)
        self.client.post(self.url, booking_data(5, 8))
        self.client.force_login(make_customer("outro").user)
        response = self.client.post(self.url, booking_data(5, 8))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_back_to_back_booking_is_allowed(self):
        make_reservation(make_customer(), self.vehicle, start=5, end=8)
        self.client.force_login(self.customer.user)
        self.client.post(self.url, booking_data(8, 10))
        self.assertEqual(Reservation.objects.count(), 2)

    def test_cancelled_period_can_be_booked_again(self):
        make_reservation(make_customer(), self.vehicle, start=5, end=8, status=S.CANCELLED)
        self.client.force_login(self.customer.user)
        self.client.post(self.url, booking_data(5, 8))
        self.assertEqual(Reservation.objects.filter(status=S.CONFIRMED).count(), 1)

    def test_same_period_on_another_vehicle_is_allowed(self):
        make_reservation(make_customer(), make_vehicle(), start=5, end=8)
        self.client.force_login(self.customer.user)
        self.client.post(self.url, booking_data(5, 8))
        self.assertEqual(Reservation.objects.filter(vehicle=self.vehicle).count(), 1)

    def test_past_pickup_date_is_rejected(self):
        self.client.force_login(self.customer.user)
        response = self.client.post(self.url, booking_data(-2, 3))
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"], "start_date", "A data de retirada não pode estar no passado."
        )
        self.assertEqual(Reservation.objects.count(), 0)

    def test_return_must_be_after_pickup(self):
        self.client.force_login(self.customer.user)
        for start, end in [(5, 5), (8, 5)]:
            with self.subTest(start=start, end=end):
                response = self.client.post(self.url, booking_data(start, end))
                self.assertEqual(response.status_code, 200)
                self.assertIn("end_date", response.context["form"].errors)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_missing_dates_are_rejected(self):
        self.client.force_login(self.customer.user)
        response = self.client.post(self.url, {"notes": "x"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_inactive_vehicle_cannot_be_booked(self):
        inactive = make_vehicle(is_active=False)
        self.client.force_login(self.customer.user)
        url = reverse("reservations:create", args=[inactive.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, booking_data()).status_code, 404)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_user_without_customer_profile_gets_one(self):
        user = make_user("semperfil")
        self.client.force_login(user)
        self.client.post(self.url, booking_data())
        self.assertEqual(Reservation.objects.get().customer.user, user)


class ReservationManageViewTests(TestCase):
    def setUp(self):
        self.owner = make_customer("dono")
        self.other = make_customer("outro")
        self.staff = make_user("equipe", staff=True)
        self.vehicle = make_vehicle()
        self.reservation = make_reservation(self.owner, self.vehicle, start=5, end=8)

    def test_list_shows_only_own_reservations(self):
        make_reservation(self.other, make_vehicle(), start=5, end=8)
        self.client.force_login(self.owner.user)
        response = self.client.get(reverse("reservations:list"))
        self.assertEqual([r.pk for r in response.context["page_obj"]], [self.reservation.pk])

    def test_list_requires_login(self):
        self.assertEqual(self.client.get(reverse("reservations:list")).status_code, 302)

    def test_detail_visible_to_owner_and_staff_but_not_to_others(self):
        url = self.reservation.get_absolute_url()
        self.client.force_login(self.owner.user)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.other.user)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_owner_can_change_dates(self):
        self.client.force_login(self.owner.user)
        url = reverse("reservations:update", args=[self.reservation.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url, booking_data(6, 10))
        self.assertRedirects(response, self.reservation.get_absolute_url())
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.start_date, day(6))
        self.assertEqual(self.reservation.end_date, day(10))
        self.assertEqual(self.reservation.total_price, Decimal("400.00"))

    def test_changing_dates_inside_own_period_does_not_conflict_with_itself(self):
        self.client.force_login(self.owner.user)
        url = reverse("reservations:update", args=[self.reservation.pk])
        self.client.post(url, booking_data(6, 7))
        self.reservation.refresh_from_db()
        self.assertEqual((self.reservation.start_date, self.reservation.end_date), (day(6), day(7)))

    def test_changing_dates_into_another_reservation_is_rejected(self):
        make_reservation(self.other, self.vehicle, start=10, end=14)
        self.client.force_login(self.owner.user)
        response = self.client.post(
            reverse("reservations:update", args=[self.reservation.pk]), booking_data(9, 12)
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "já está reservado")
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.end_date, day(8))

    def test_other_customer_cannot_change_or_cancel(self):
        self.client.force_login(self.other.user)
        update = reverse("reservations:update", args=[self.reservation.pk])
        cancel = reverse("reservations:cancel", args=[self.reservation.pk])
        self.assertEqual(self.client.post(update, booking_data(6, 9)).status_code, 404)
        self.assertEqual(self.client.post(cancel).status_code, 404)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, S.CONFIRMED)

    def test_reservation_starting_today_cannot_be_changed_by_customer(self):
        started = make_reservation(self.owner, make_vehicle(), start=0, end=3)
        self.client.force_login(self.owner.user)
        for name in ("update", "cancel"):
            with self.subTest(name=name):
                response = self.client.post(
                    reverse(f"reservations:{name}", args=[started.pk]), booking_data(1, 5)
                )
                self.assertRedirects(response, started.get_absolute_url())
        started.refresh_from_db()
        self.assertEqual(started.status, S.CONFIRMED)
        self.assertEqual(started.end_date, day(3))

    def test_cancel_requires_post_and_frees_the_vehicle(self):
        self.client.force_login(self.owner.user)
        url = reverse("reservations:cancel", args=[self.reservation.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, S.CONFIRMED)
        response = self.client.post(url)
        self.assertRedirects(response, reverse("reservations:list"))
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, S.CANCELLED)
        self.assertTrue(self.vehicle.is_available_between(day(5), day(8)))

    def test_staff_can_edit_in_progress_reservation_without_changing_start(self):
        started = make_reservation(self.owner, make_vehicle(), start=-1, end=2)
        original_start = started.start_date
        self.client.force_login(self.staff)
        url = reverse("reservations:update", args=[started.pk])
        response = self.client.post(
            url,
            {
                "start_date": original_start.isoformat(),
                "end_date": day(3).isoformat(),
                "notes": "Observação alterada pela equipe",
            },
        )
        self.assertRedirects(response, started.get_absolute_url())
        started.refresh_from_db()
        self.assertEqual(started.start_date, original_start)
        self.assertEqual(started.end_date, day(3))
        self.assertEqual(started.notes, "Observação alterada pela equipe")

    def test_staff_can_cancel_and_complete(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("reservations:complete", args=[self.reservation.pk]),
            {"next": reverse("core:panel_reservations")},
        )
        self.assertRedirects(response, reverse("core:panel_reservations"))
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, S.COMPLETED)

        other = make_reservation(self.owner, make_vehicle(), start=5, end=8)
        self.client.post(reverse("reservations:cancel", args=[other.pk]))
        other.refresh_from_db()
        self.assertEqual(other.status, S.CANCELLED)

    def test_complete_is_staff_only_and_post_only(self):
        url = reverse("reservations:complete", args=[self.reservation.pk])
        self.client.force_login(self.owner.user)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(url).status_code, 405)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, S.CONFIRMED)


class ReservationHistoryTests(TestCase):
    def setUp(self):
        self.owner = make_customer("dono")
        self.other = make_customer("outro")
        self.vehicle = make_vehicle(daily_rate=Decimal("100.00"))
        mk = lambda start, end, status=S.CONFIRMED: make_reservation(
            self.owner, make_vehicle(daily_rate=Decimal("100.00")), start, end, status
        )
        self.upcoming = mk(2, 4)
        self.in_progress = mk(-1, 2)
        self.ended = mk(-5, -2)
        self.completed = mk(-9, -6, S.COMPLETED)
        self.cancelled = mk(3, 6, S.CANCELLED)
        make_reservation(self.other, self.vehicle, 2, 4)

    def test_queryset_phases(self):
        qs = Reservation.objects.filter(customer=self.owner)
        self.assertEqual(list(qs.upcoming()), [self.upcoming])
        self.assertEqual(list(qs.in_progress()), [self.in_progress])
        self.assertCountEqual(qs.past(), [self.ended, self.completed])
        self.assertEqual(list(qs.cancelled()), [self.cancelled])

    def test_phase_properties(self):
        self.assertEqual(self.upcoming.phase_label, "Próxima")
        self.assertEqual(self.in_progress.phase_label, "Em andamento")
        self.assertEqual(self.ended.phase_label, "Encerrada")
        self.assertEqual(self.completed.phase_label, "Concluída")
        self.assertEqual(self.cancelled.phase_label, "Cancelada")

    def pks(self, response):
        return [r.pk for r in response.context["page_obj"]]

    def test_history_tabs_filter_the_list(self):
        self.client.force_login(self.owner.user)
        url = reverse("reservations:list")
        self.assertEqual(len(self.pks(self.client.get(url))), 5)
        expected = {
            "upcoming": [self.upcoming.pk],
            "in_progress": [self.in_progress.pk],
            "cancelled": [self.cancelled.pk],
        }
        for key, pks in expected.items():
            with self.subTest(filter=key):
                self.assertEqual(self.pks(self.client.get(url, {"f": key})), pks)
        past = self.pks(self.client.get(url, {"f": "past"}))
        self.assertCountEqual(past, [self.ended.pk, self.completed.pk])

    def test_history_counts_total_and_invalid_filter(self):
        self.client.force_login(self.owner.user)
        response = self.client.get(reverse("reservations:list"), {"f": "xyz"})
        self.assertEqual(response.context["current"], "all")
        counts = {tab["key"]: tab["count"] for tab in response.context["tabs"]}
        self.assertEqual(counts, {"all": 5, "upcoming": 1, "in_progress": 1, "past": 2, "cancelled": 1})
        # 2 + 3 + 3 + 3 diárias × R$ 100, sem a cancelada
        self.assertEqual(response.context["total_booked"], Decimal("1100.00"))

    def test_history_never_shows_other_customers(self):
        self.client.force_login(self.other.user)
        response = self.client.get(reverse("reservations:list"))
        self.assertEqual(len(self.pks(response)), 1)
        self.assertEqual(response.context["total_booked"], Decimal("200.00"))
