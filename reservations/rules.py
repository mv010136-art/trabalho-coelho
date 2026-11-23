"""Regras de negócio puras (sem Django) das reservas.

Ficam isoladas para poderem ser testadas sem banco de dados e para que o
modelo, os formulários e os testes usem exatamente a mesma definição.

Convenção: um período é o intervalo semiaberto [retirada, devolução).
"""
from decimal import ROUND_HALF_UP, Decimal

CENTS = Decimal("0.01")


def rental_days(start, end):
    """Número de diárias entre retirada e devolução (nunca negativo)."""
    if not start or not end:
        return 0
    return max((end - start).days, 0)


def periods_overlap(a_start, a_end, b_start, b_end):
    """True se [a_start, a_end) e [b_start, b_end) têm algum dia em comum."""
    return a_start < b_end and a_end > b_start


def calculate_total(daily_rate, start, end):
    """Valor total = diárias × valor da diária, arredondado em centavos."""
    return (Decimal(daily_rate) * rental_days(start, end)).quantize(CENTS, rounding=ROUND_HALF_UP)


def can_self_service(is_confirmed, start, today):
    """Cliente só altera/cancela reserva confirmada antes do dia da retirada."""
    return bool(is_confirmed) and start > today


def phase(status, start, end, today):
    """Fase da reserva para o histórico do cliente.

    status: 'confirmed' | 'cancelled' | 'completed'
    Retorna: 'cancelled' | 'completed' | 'upcoming' | 'in_progress' | 'ended'
    ('ended' = confirmada cuja devolução já passou e ainda não foi concluída).
    """
    if status == "cancelled":
        return "cancelled"
    if status == "completed":
        return "completed"
    if start > today:
        return "upcoming"
    if end > today:
        return "in_progress"
    return "ended"
