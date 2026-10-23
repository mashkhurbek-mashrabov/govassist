"""Constants of the accounts app (AGENTS.md: no constant values elsewhere in the app)."""

DISPLAY_NAME_MAX_LENGTH = 80

TURNSTILE_TOKEN_MAX_LENGTH = 2048

TURNSTILE_FAILED = "turnstile_failed"

TURNSTILE_MESSAGE = "Bot check failed. Reload the page and try again."

# allauth's rate-limit action for verification emails (per email, ACCOUNT_RATE_LIMITS).
CONFIRM_EMAIL_ACTION = "confirm_email"
