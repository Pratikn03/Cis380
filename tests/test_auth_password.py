from app.core.auth import hash_password, verify_password


def test_password_hash_roundtrip():
    password = "sentifargo-secret"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
