import logging

from src.core.enums import UserRole
from src.utils.logger import SecretMaskingFilter
from src.utils.security import (
    is_moderator,
    sanitize_text,
    validate_file_size,
    validate_telegram_id,
)


def test_validate_telegram_id():
    assert validate_telegram_id(12345) is True
    assert validate_telegram_id(0) is False
    assert validate_telegram_id(-1) is False
    assert validate_telegram_id("123") is False  # type: ignore[arg-type]


def test_validate_file_size():
    one_mb = 1024 * 1024
    assert validate_file_size(one_mb, max_mb=10) is True
    assert validate_file_size(11 * one_mb, max_mb=10) is False
    assert validate_file_size(0, max_mb=10) is False


def test_sanitize_text():
    assert sanitize_text("  hello  ") == "hello"
    assert sanitize_text(None) is None
    assert sanitize_text("") == ""


def test_is_moderator():
    assert is_moderator(1, UserRole.MODERATOR) is True
    assert is_moderator(1, UserRole.USER) is False
    assert is_moderator(1, UserRole.ADMIN) is False


def test_secret_masking_filter_msg():
    filter_obj = SecretMaskingFilter(["secret_token_123"])

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Token is secret_token_123 here",
        args=None,
        exc_info=None,
    )

    filter_obj.filter(record)
    assert "secret_token_123" not in record.msg
    assert "***" in record.msg


def test_secret_masking_filter_args():
    filter_obj = SecretMaskingFilter(["my_password"])

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="User logged in with %s",
        args=("my_password",),
        exc_info=None,
    )

    filter_obj.filter(record)
    assert "my_password" not in record.args