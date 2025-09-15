from datetime import datetime, date, timezone
from services.transactions import Transaction


def test_transaction_dto_getters_setters():
    t = Transaction()
    t.set_user_id(1)
    t.set_category_id(2)
    t.set_amount(123.45)
    t.set_type("expense")
    t.set_fixed(True)
    t.set_periodicity("monthly")
    t.set_next_execution(date(2025, 1, 10))
    t.set_description("Desc")
    t.set_notes("Notes")
    now = datetime.now(timezone.utc)
    t.set_occurred_at(now)
    t.set_installment_id(3)

    assert t.get_user_id() == 1
    assert t.get_category_id() == 2
    assert t.get_amount() == 123.45
    assert t.get_type() == "expense"
    assert t.get_fixed() is True
    assert t.get_periodicity() == "monthly"
    assert t.get_next_execution() == date(2025, 1, 10)
    assert t.get_description() == "Desc"
    assert t.get_notes() == "Notes"
    assert t.get_occurred_at() == now
    assert t.get_installment_id() == 3


def test_transaction_to_entity_and_from_entity_roundtrip():
    due = date(2025, 2, 1)
    t = Transaction(user_id=1, category_id=None, amount=10.0, type="income", fixed=False, periodicity="none", next_execution=None, description=None, notes=None, occurred_at=None, installment_id=None)
    ent = t.to_entity()

    assert ent.user_id == 1
    assert ent.category_id is None
    assert ent.amount == 10.0
    assert ent.type == "income"
    assert ent.fixed is False
    assert ent.periodicity == "none"

    back = Transaction.from_entity(ent)
    assert back.get_user_id() == 1
    assert back.get_amount() == 10.0
    assert back.get_type() == "income"
    assert back.get_fixed() is False
    assert back.get_periodicity() == "none"
