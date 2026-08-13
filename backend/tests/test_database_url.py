"""
Tests for the connection-string repair logic.

These tests do NOT touch the network or the real database. They only check
that a messy connection string is turned into a correct one, which is where
the setup went wrong in practice.
"""

from app.database import normalize_database_url

HOST = "aws-0-ap-south-1.pooler.supabase.com:5432/postgres"


def test_leftover_placeholder_brackets_are_removed():
    """Supabase writes [YOUR-PASSWORD]; the brackets are not part of it."""
    messy = f"postgresql://postgres:[secret123]@{HOST}"

    assert normalize_database_url(messy) == f"postgresql://postgres:secret123@{HOST}"


def test_at_sign_in_password_is_encoded():
    """
    An "@" inside the password used to break the host lookup, because the
    URL was split at the wrong "@".
    """
    result = normalize_database_url(f"postgresql://postgres:pa@ss@{HOST}")

    assert result == f"postgresql://postgres:pa%40ss@{HOST}"
    # The host must survive intact -- this is the bug that caused
    # "failed to resolve host".
    assert result.rsplit("@", 1)[1] == HOST


def test_brackets_and_special_characters_together():
    """The real-world case: brackets left in AND an "@" in the password."""
    result = normalize_database_url(f"postgresql://postgres:[Adaa@5pillars]@{HOST}")

    assert result == f"postgresql://postgres:Adaa%405pillars@{HOST}"


def test_already_encoded_password_is_left_alone():
    """Encoding twice would corrupt a password that was already correct."""
    good = f"postgresql://postgres:pa%40ss@{HOST}"

    assert normalize_database_url(good) == good


def test_plain_password_is_unchanged():
    good = f"postgresql://postgres:simplepassword@{HOST}"

    assert normalize_database_url(good) == good


def test_empty_string_does_not_crash():
    assert normalize_database_url("") == ""
