"""
test_security.py
----------------
Unit tests for SecurityManager.
"""

from app.utils.security import SecurityManager


def test_encryption_decryption():
    sec = SecurityManager()
    plaintext = "my_secret_api_key_12345"

    token = sec.encrypt(plaintext)
    if token is not None:
        decrypted = sec.decrypt(token)
        assert decrypted == plaintext


def test_dangerous_action_detection():
    sec = SecurityManager()

    assert sec.is_dangerous("shutdown my computer") is True
    assert sec.is_dangerous("delete resume.pdf") is True
    assert sec.is_dangerous("what is the weather today") is False


def test_confirmation_parsing():
    sec = SecurityManager()

    assert sec.is_confirmed("yes") is True
    assert sec.is_confirmed("yeah go ahead") is True
    assert sec.is_confirmed("no stop") is False
    assert sec.is_confirmed("") is False
