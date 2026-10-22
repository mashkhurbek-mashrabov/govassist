"""Tests for the PII scrubber: positive and negative cases for each placeholder."""

from apps.common.pii import scrub


class TestPassport:
    """Tests for passport number scrubbing."""

    def test_passport_uppercase(self) -> None:
        """Standard uppercase passport ``AB1234567`` is scrubbed."""
        assert scrub("My passport is AB1234567.") == "My passport is [PASSPORT]."

    def test_passport_with_space(self) -> None:
        """Passport with space between letters and digits ``AB 1234567``."""
        assert scrub("Passport: AB 1234567") == "Passport: [PASSPORT]"

    def test_passport_lowercase(self) -> None:
        """Lowercase passport letters ``ab1234567`` are scrubbed (case-insensitive)."""
        assert scrub("ab1234567 is mine") == "[PASSPORT] is mine"

    def test_passport_in_sentence(self) -> None:
        """Passport embedded in a sentence."""
        assert scrub("Passport AA0000001 was issued.") == "Passport [PASSPORT] was issued."

    def test_not_passport_short_digits(self) -> None:
        """Only 6 digits after 2 letters: not a passport."""
        result = scrub("AB123456 text")
        assert "[PASSPORT]" not in result

    def test_not_passport_three_letters(self) -> None:
        """Three letters before digits: not a passport."""
        result = scrub("ABC1234567 text")
        assert "[PASSPORT]" not in result


class TestPinfl:
    """Tests for PINFL scrubbing."""

    def test_14_digit_pinfl(self) -> None:
        """A 14-digit number is a PINFL."""
        assert scrub("PINFL: 12345678901234") == "PINFL: [PINFL]"

    def test_13_digits_not_pinfl(self) -> None:
        """13 digits are not a PINFL (too short)."""
        result = scrub("Number 1234567890123 here")
        assert "[PINFL]" not in result

    def test_15_digits_not_pinfl(self) -> None:
        """15 digits are not a PINFL (too long)."""
        result = scrub("Number 123456789012345 here")
        assert "[PINFL]" not in result


class TestPhone:
    """Tests for phone number scrubbing."""

    def test_phone_plus_998_spaced(self) -> None:
        """Full international format ``+998 90 123 45 67``."""
        assert scrub("Call +998 90 123 45 67") == "Call [PHONE]"

    def test_phone_998_no_plus(self) -> None:
        """Without plus sign: ``998901234567``."""
        assert scrub("Phone: 998901234567") == "Phone: [PHONE]"

    def test_phone_city_with_parens(self) -> None:
        """City code in parentheses: ``(71) 200-00-00``."""
        assert scrub("Tel: (71) 200-00-00") == "Tel: [PHONE]"

    def test_phone_short_local(self) -> None:
        """Local format without country code: ``90 123 45 67``."""
        assert scrub("Call 90 123 45 67 now") == "Call [PHONE] now"

    def test_plain_year_not_phone(self) -> None:
        """A 4-digit year like ``2024`` must not be scrubbed as a phone."""
        result = scrub("The year is 2024.")
        assert result == "The year is 2024."

    def test_plain_number_not_phone(self) -> None:
        """Short numbers like ``12345`` must not be scrubbed."""
        result = scrub("Order 12345 confirmed")
        assert result == "Order 12345 confirmed"

    def test_phone_with_dashes(self) -> None:
        """Phone with dashes: ``+998-90-123-45-67``."""
        assert scrub("Call +998-90-123-45-67") == "Call [PHONE]"


class TestEmail:
    """Tests for email scrubbing."""

    def test_simple_email(self) -> None:
        """A standard email address is scrubbed."""
        assert scrub("Email me at user@example.com") == "Email me at [EMAIL]"

    def test_email_with_dots_and_plus(self) -> None:
        """Email with dots and plus in the local part."""
        assert scrub("Contact: first.last+tag@domain.co.uk") == "Contact: [EMAIL]"

    def test_not_email_no_at(self) -> None:
        """Text without @ is not an email."""
        result = scrub("Just a word.com")
        assert "[EMAIL]" not in result


class TestMultiple:
    """Tests for scrubbing multiple PII types in one string."""

    def test_passport_and_phone(self) -> None:
        """Both passport and phone are scrubbed."""
        text = "Passport AB1234567, phone +998 90 123 45 67"
        result = scrub(text)
        assert "[PASSPORT]" in result
        assert "[PHONE]" in result

    def test_email_and_pinfl(self) -> None:
        """Both email and PINFL are scrubbed."""
        text = "Email a@b.com PINFL 12345678901234"
        result = scrub(text)
        assert "[EMAIL]" in result
        assert "[PINFL]" in result

    def test_no_pii(self) -> None:
        """Clean text passes through unchanged."""
        text = "This is a clean sentence with no personal data."
        assert scrub(text) == text
