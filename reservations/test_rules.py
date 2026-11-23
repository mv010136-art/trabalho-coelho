"""Testes das regras puras. Rodam com ou sem Django:

    python -m unittest reservations.test_rules
"""
import datetime
import itertools
import unittest
from decimal import Decimal

from reservations import rules

D = datetime.date


def d(n):
    return D(2026, 11, 1) + datetime.timedelta(days=n)


class RentalDaysTests(unittest.TestCase):
    def test_counts_nights(self):
        self.assertEqual(rules.rental_days(d(1), d(4)), 3)
        self.assertEqual(rules.rental_days(d(1), d(2)), 1)

    def test_never_negative_and_handles_missing(self):
        self.assertEqual(rules.rental_days(d(5), d(5)), 0)
        self.assertEqual(rules.rental_days(d(5), d(2)), 0)
        self.assertEqual(rules.rental_days(None, d(2)), 0)
        self.assertEqual(rules.rental_days(d(2), None), 0)

    def test_across_month_and_leap_year(self):
        self.assertEqual(rules.rental_days(D(2028, 2, 27), D(2028, 3, 1)), 3)
        self.assertEqual(rules.rental_days(D(2026, 12, 30), D(2027, 1, 2)), 3)


class CalculateTotalTests(unittest.TestCase):
    def test_total(self):
        self.assertEqual(rules.calculate_total(Decimal("100.00"), d(1), d(4)), Decimal("300.00"))
        self.assertEqual(rules.calculate_total(Decimal("129.90"), d(1), d(4)), Decimal("389.70"))

    def test_accepts_string_and_float_free_inputs(self):
        self.assertEqual(rules.calculate_total("89.90", d(0), d(2)), Decimal("179.80"))

    def test_rounds_to_cents(self):
        self.assertEqual(rules.calculate_total(Decimal("10.005"), d(0), d(1)), Decimal("10.01"))

    def test_zero_when_period_invalid(self):
        self.assertEqual(rules.calculate_total(Decimal("100"), d(3), d(3)), Decimal("0.00"))
        self.assertEqual(rules.calculate_total(Decimal("100"), d(5), d(3)), Decimal("0.00"))


class OverlapTests(unittest.TestCase):
    def test_known_cases(self):
        base = (d(10), d(15))
        cases = {
            (8, 11): True, (14, 18): True, (11, 13): True, (8, 18): True, (10, 15): True,
            (15, 18): False, (7, 10): False, (0, 5): False, (20, 25): False,
        }
        for (s, e), expected in cases.items():
            with self.subTest(s=s, e=e):
                self.assertEqual(rules.periods_overlap(d(s), d(e), *base), expected)

    def test_is_symmetric_and_matches_day_by_day_definition(self):
        """Prova exaustiva: sobrepõe ⇔ existe pelo menos um dia (noite) em comum."""
        def nights(s, e):
            return {s + datetime.timedelta(days=i) for i in range((e - s).days)}

        periods = [(s, e) for s, e in itertools.product(range(0, 9), repeat=2) if e > s]
        for (a1, a2), (b1, b2) in itertools.product(periods, repeat=2):
            expected = bool(nights(d(a1), d(a2)) & nights(d(b1), d(b2)))
            got = rules.periods_overlap(d(a1), d(a2), d(b1), d(b2))
            self.assertEqual(got, expected, f"{(a1, a2)} x {(b1, b2)}")
            self.assertEqual(got, rules.periods_overlap(d(b1), d(b2), d(a1), d(a2)))


class SelfServiceAndPhaseTests(unittest.TestCase):
    def test_self_service_until_the_day_before(self):
        today = d(0)
        self.assertTrue(rules.can_self_service(True, d(1), today))
        self.assertFalse(rules.can_self_service(True, d(0), today))
        self.assertFalse(rules.can_self_service(True, d(-3), today))
        self.assertFalse(rules.can_self_service(False, d(5), today))

    def test_phase(self):
        today = d(0)
        self.assertEqual(rules.phase("cancelled", d(1), d(3), today), "cancelled")
        self.assertEqual(rules.phase("completed", d(-5), d(-2), today), "completed")
        self.assertEqual(rules.phase("confirmed", d(1), d(3), today), "upcoming")
        self.assertEqual(rules.phase("confirmed", d(0), d(3), today), "in_progress")
        self.assertEqual(rules.phase("confirmed", d(-2), d(1), today), "in_progress")
        self.assertEqual(rules.phase("confirmed", d(-5), d(0), today), "ended")
        self.assertEqual(rules.phase("confirmed", d(-5), d(-1), today), "ended")


if __name__ == "__main__":
    unittest.main()
