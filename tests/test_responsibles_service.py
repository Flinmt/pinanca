from services.responsibles import Responsible


def test_responsible_dto_getters_setters():
    r = Responsible()
    r.set_user_id(1)
    r.set_name("Ana")
    r.set_related_user_id(2)

    assert r.get_user_id() == 1
    assert r.get_name() == "Ana"
    assert r.get_related_user_id() == 2


def test_responsible_to_entity_and_from_entity_roundtrip():
    dto = Responsible(user_id=1, name=None, related_user_id=None)
    ent = dto.to_entity()
    assert ent.user_id == 1
    assert ent.name is None
    assert ent.related_user_id is None

    dto2 = Responsible.from_entity(ent)
    assert dto2.get_user_id() == 1
    assert dto2.get_name() is None
    assert dto2.get_related_user_id() is None

