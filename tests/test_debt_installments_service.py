from datetime import date, datetime, timezone
from services.debt_installments import DebtInstallment


def test_installment_dto_getters_setters():
    i = DebtInstallment()
    i.set_debt_id(1)
    i.set_number(3)
    i.set_amount(100.5)
    i.set_due_on(date(2025, 1, 31))
    i.set_paid(True)
    now = datetime.now(timezone.utc)
    i.set_paid_at(now)

    assert i.get_debt_id() == 1
    assert i.get_number() == 3
    assert i.get_amount() == 100.5
    assert i.get_due_on() == date(2025, 1, 31)
    assert i.get_paid() is True
    assert i.get_paid_at() == now


def test_installment_to_entity_and_from_entity_roundtrip():
    due = date(2025, 2, 28)
    dto = DebtInstallment(debt_id=1, number=1, amount=50.0, due_on=due, paid=False, paid_at=None)
    ent = dto.to_entity()
    assert ent.debt_id == 1
    assert ent.number == 1
    assert ent.amount == 50.0
    assert ent.due_on == due
    assert ent.paid is False
    assert ent.paid_at is None

    dto2 = DebtInstallment.from_entity(ent)
    assert dto2.get_debt_id() == 1
    assert dto2.get_number() == 1
    assert dto2.get_amount() == 50.0
    assert dto2.get_due_on() == due
    assert dto2.get_paid() is False
    assert dto2.get_paid_at() is None
