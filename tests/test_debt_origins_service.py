from services.debt_origins import DebtOrigin


def test_debt_origin_dto_getters_setters():
    d = DebtOrigin()
    d.set_user_id(1)
    d.set_name("Salary")

    assert d.get_user_id() == 1
    assert d.get_name() == "Salary"


def test_debt_origin_to_entity_and_from_entity_roundtrip():
    dto = DebtOrigin(user_id=1, name="Loan")
    ent = dto.to_entity()
    assert ent.user_id == 1
    assert ent.name == "Loan"

    dto2 = DebtOrigin.from_entity(ent)
    assert dto2.get_user_id() == 1
    assert dto2.get_name() == "Loan"

