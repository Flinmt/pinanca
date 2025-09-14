from services.users import User
from db.models import User as UserEntity


def test_user_dto_getters_setters():
    u = User()
    u.set_name("John")
    u.set_cpf("12345678901")
    u.set_password_hash(b"pw")
    u.set_profile_image("/pic.png")

    assert u.get_name() == "John"
    assert u.get_cpf() == "12345678901"
    assert u.get_password_hash() == b"pw"
    assert u.get_profile_image() == "/pic.png"


def test_user_to_entity_and_from_entity_roundtrip():
    dto = User(name="Jane", cpf="10987654321", password_hash=b"hash", profile_image=None)
    ent = dto.to_entity()

    # campos básicos devem ser iguais
    assert ent.name == dto.get_name()
    assert ent.cpf == dto.get_cpf()
    assert ent.password_hash == dto.get_password_hash()
    assert ent.profile_image == dto.get_profile_image()

    # from_entity deve popular timestamps do modelo
    dto2 = User.from_entity(ent)
    assert dto2.get_name() == dto.get_name()
    assert dto2.get_cpf() == dto.get_cpf()
    assert dto2.get_password_hash() == dto.get_password_hash()
    # created_at/updated_at vêm do default_factory do modelo
    assert dto2.get_created_at() is not None
    assert dto2.get_updated_at() is not None
