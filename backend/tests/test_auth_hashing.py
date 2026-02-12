from app.auth import hash_password, verify_password


def test_hash_and_verify_roundtrip():
    password = 'password123'
    hashed = hash_password(password)

    assert hashed.startswith('pbkdf2_sha256$')
    assert verify_password(password, hashed) is True
    assert verify_password('wrong-pass', hashed) is False
