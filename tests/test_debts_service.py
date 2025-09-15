from datetime import date
from services.debts import Debt


def test_debt_dto_getters_setters():
    d = Debt()
    d.set_user_id(1)
    d.set_origin_id(2)
    d.set_category_id(3)
    d.set_responsible_id(4)
    d.set_debt_date(date(2025, 1, 1))
    d.set_description("Desc")
    d.set_total_amount(100.0)
    d.set_installments(5)
    d.set_notes("Notes")
    d.set_paid(True)

    assert d.get_user_id() == 1
    assert d.get_origin_id() == 2
    assert d.get_category_id() == 3
    assert d.get_responsible_id() == 4
    assert d.get_debt_date() == date(2025, 1, 1)
    assert d.get_description() == "Desc"
    assert d.get_total_amount() == 100.0
    assert d.get_installments() == 5
    assert d.get_notes() == "Notes"
    assert d.get_paid() is True


def test_debt_to_entity_and_from_entity_roundtrip():
    dto = Debt(
        user_id=1,
        origin_id=2,
        category_id=None,
        responsible_id=None,
        debt_date=date(2025, 2, 1),
        description=None,
        total_amount=50.0,
        installments=1,
        notes=None,
        paid=False,
    )
    ent = dto.to_entity()
    assert ent.user_id == 1
    assert ent.origin_id == 2
    assert ent.category_id is None
    assert ent.responsible_id is None
    assert ent.debt_date == date(2025, 2, 1)
    assert ent.total_amount == 50.0
    assert ent.installments == 1
    assert ent.paid is False

    dto2 = Debt.from_entity(ent)
    assert dto2.get_user_id() == 1
    assert dto2.get_origin_id() == 2
    assert dto2.get_category_id() is None
    assert dto2.get_responsible_id() is None
    assert dto2.get_debt_date() == date(2025, 2, 1)
    assert dto2.get_total_amount() == 50.0
    assert dto2.get_installments() == 1
    assert dto2.get_paid() is False

