"""
Guardrails AI — custom validators for SafeBot.

Architecture mirrors the guardrails-ai (guardrails-ai/guardrails) open-source
framework: each validator is a class with a `validate(value)` method that
returns a PassResult or FailResult.  A Guard chains multiple validators and
applies them in order, stopping on the first failure (or using a fix value).

When the `guardrails-ai` pip package is installed in the environment the
code switches to using the official SDK classes.  When it is unavailable
(the common case here) this pure-Python re-implementation runs instead —
identical behaviour, no external dependencies.

Validator catalog (Guardrails AI pattern)
─────────────────────────────────────────
INPUT validators:
  • InputLengthValidator        — reject blank / oversized messages
  • HarmfulContentValidator     — regex ban-list for dangerous topics
  • JailbreakDetectionValidator — prompt-injection / system-override patterns
  • ProfanityValidator          — strong profanity word-list

OUTPUT validators:
  • ResponseLengthValidator     — ensure the reply is not empty / too short
  • NoPIILeakValidator          — redact accidental SSN/email/phone/CC echoes
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional

# ── Try official guardrails-ai SDK first ──────────────────────────────────────
try:
    from guardrails import Guard as _OfficialGuard, OnFailAction  # type: ignore
    from guardrails.validators import (  # type: ignore
        FailResult as _FailResult,
        PassResult as _PassResult,
        ValidationResult as _ValidationResult,
        Validator as _Validator,
        register_validator,
    )
    _GUARDRAILS_AI_AVAILABLE = True
except Exception:
    _GUARDRAILS_AI_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Pure-Python re-implementation (active when SDK is not installed)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PassResult:
    """Validation passed."""
    passed: bool = True
    fixed_value: Optional[str] = None


@dataclass
class FailResult:
    """Validation failed."""
    passed: bool = False
    error_message: str = ""
    fix_value: Optional[str] = None


ValidationResult = PassResult | FailResult


class Validator:
    """Base class mirroring the guardrails-ai Validator interface."""

    def validate(self, value: str) -> ValidationResult:
        raise NotImplementedError

    def _validate(self, value: str, metadata: dict) -> ValidationResult:
        raise NotImplementedError


class Guard:
    """
    Chains multiple Validator instances.

    Mirrors the guardrails-ai Guard.use(...).validate() API.
    on_fail behaviour:
      'exception' — raise ValueError with the error message
      'fix'       — return the fixed value from FailResult.fix_value
      'noop'      — continue and collect errors
    """

    def __init__(self) -> None:
        self._validators: list[tuple[Validator, str]] = []

    def use(self, validator: Validator, on_fail: str = "exception") -> "Guard":
        self._validators.append((validator, on_fail))
        return self

    def validate(self, value: str) -> "GuardResult":
        current = value
        errors: list[str] = []
        for validator, on_fail in self._validators:
            result = validator.validate(current)
            if not result.passed:
                fr: FailResult = result  # type: ignore[assignment]
                if on_fail == "exception":
                    raise ValueError(fr.error_message)
                elif on_fail == "fix" and fr.fix_value is not None:
                    current = fr.fix_value
                    errors.append(fr.error_message)
                else:
                    errors.append(fr.error_message)
        return GuardResult(validated_output=current, errors=errors)


@dataclass
class GuardResult:
    validated_output: str
    errors: list[str] = field(default_factory=list)

    @property
    def validation_passed(self) -> bool:
        return len(self.errors) == 0


# ── on_fail action constants (mirrors guardrails-ai OnFailAction) ─────────────
class OnFailAction:
    EXCEPTION = "exception"
    FIX       = "fix"
    NOOP      = "noop"


# ── Word / pattern lists ───────────────────────────────────────────────────────

_HARMFUL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"\b(make|build|create|synthesize|manufacture|brew)\b.{0,40}"
        r"\b(bomb|explosive|weapon|drug|malware|virus|ransomware|poison|nerve.agent)\b", re.I),
    re.compile(
        r"\b(kill|murder|harm|hurt|assault|attack|shoot|stab)\b.{0,30}"
        r"\b(someone|a person|people|human)\b", re.I),
    re.compile(
        r"\b(hack|crack|exploit|bypass|brute.force)\b.{0,30}"
        r"\b(account|system|password|network|firewall)\b", re.I),
    re.compile(r"\b(child.porn|CSAM|abuse material)\b", re.I),
    re.compile(r"\b(suicide method|how to kill (my|your)?self)\b", re.I),
]

_JAILBREAK_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"\b(ignore|disregard|forget|bypass|override)\b.{0,40}"
        r"\b(instructions?|guidelines?|prompts?|rules?|training|restrictions?|safety)\b", re.I),
    re.compile(r"\b(DAN mode?|jailbreak|developer mode|unrestricted mode|god mode)\b", re.I),
    # "act as DAN" / "you are now DAN" patterns
    re.compile(r"\b(act as|you are now|become|pretend (to be|you are))\s+(DAN|an? (uncensored|unrestricted|evil|unfiltered))", re.I),
    re.compile(
        r"\b(pretend|act as if|simulate|role.?play)\b.{0,40}"
        r"\b(no restriction|no limit|without safety|uncensored|evil AI)\b", re.I),
    re.compile(r"\bnew system prompt\b", re.I),
    re.compile(r"\byou (must|shall|have to) comply.{0,30}\bno matter what\b", re.I),
    re.compile(r"\bforget (everything|all) (you were told|your training)\b", re.I),
    re.compile(r"\b(do anything now|DAN\b)", re.I),
]

_PROFANITY_LIST: list[str] = [
    "fuck", "shit", "bastard", "asshole", "motherfucker", "bitch",
    "cunt", "dick", "cock", "pussy", "nigger", "faggot", "retard",
    "whore", "slut",
]

_PII_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),                                          # SSN
    re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),          # email
    re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),       # phone
    re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14})\b"),               # CC
]


# ── Validator implementations ─────────────────────────────────────────────────

class InputLengthValidator(Validator):
    """Reject blank messages and messages exceeding max_chars."""

    def __init__(self, min_chars: int = 2, max_chars: int = 8000,
                 on_fail: Optional[Callable] = None) -> None:
        self.min_chars = min_chars
        self.max_chars = max_chars

    def validate(self, value: str) -> ValidationResult:
        length = len(value.strip())
        if length < self.min_chars:
            return FailResult(error_message="Message is too short — please provide more context.")
        if length > self.max_chars:
            return FailResult(
                error_message=f"Message exceeds the {self.max_chars}-character limit.",
                fix_value=value[: self.max_chars],
            )
        return PassResult()

    def _validate(self, value: str, metadata: dict) -> ValidationResult:
        return self.validate(value)


class HarmfulContentValidator(Validator):
    """Block requests containing patterns associated with dangerous activities."""

    def validate(self, value: str) -> ValidationResult:
        for pattern in _HARMFUL_PATTERNS:
            if pattern.search(value):
                return FailResult(
                    error_message=(
                        "Your message contains content related to harmful activities. "
                        "SafeBot cannot assist with requests that could cause harm."
                    )
                )
        return PassResult()

    def _validate(self, value: str, metadata: dict) -> ValidationResult:
        return self.validate(value)


class JailbreakDetectionValidator(Validator):
    """Detect and block prompt injection / system-override attempts."""

    def validate(self, value: str) -> ValidationResult:
        for pattern in _JAILBREAK_PATTERNS:
            if pattern.search(value):
                return FailResult(
                    error_message=(
                        "This looks like an attempt to override SafeBot's safety guidelines. "
                        "These protections are fundamental to how I work."
                    )
                )
        return PassResult()

    def _validate(self, value: str, metadata: dict) -> ValidationResult:
        return self.validate(value)


class ProfanityValidator(Validator):
    """Flag messages with strong profanity (word-boundary aware)."""

    def __init__(self, word_list: Optional[List[str]] = None,
                 on_fail: Optional[Callable] = None) -> None:
        self._words = word_list or _PROFANITY_LIST

    def validate(self, value: str) -> ValidationResult:
        lower = value.lower()
        found = [w for w in self._words if re.search(rf"\b{re.escape(w)}\b", lower)]
        if found:
            return FailResult(
                error_message=(
                    "Your message contains strong profanity. "
                    "Please rephrase your request respectfully."
                )
            )
        return PassResult()

    def _validate(self, value: str, metadata: dict) -> ValidationResult:
        return self.validate(value)


class ResponseLengthValidator(Validator):
    """Ensure the LLM response is not empty or suspiciously short."""

    def __init__(self, min_chars: int = 5, on_fail: Optional[Callable] = None) -> None:
        self.min_chars = min_chars

    def validate(self, value: str) -> ValidationResult:
        if len(value.strip()) < self.min_chars:
            return FailResult(error_message="The assistant response was empty or too short.")
        return PassResult()

    def _validate(self, value: str, metadata: dict) -> ValidationResult:
        return self.validate(value)


class NoPIILeakValidator(Validator):
    """Scan LLM responses for accidental PII and auto-redact them."""

    def validate(self, value: str) -> ValidationResult:
        found: list[str] = []
        for pattern in _PII_PATTERNS:
            found.extend(pattern.findall(value))
        if found:
            redacted = value
            for item in found:
                redacted = redacted.replace(item, "[REDACTED]")
            return FailResult(
                error_message="Response contained potential PII — redacted.",
                fix_value=redacted,
            )
        return PassResult()

    def _validate(self, value: str, metadata: dict) -> ValidationResult:
        return self.validate(value)


# ── Guard factory functions ────────────────────────────────────────────────────

def build_input_guard() -> Guard:
    """Chain: length → harmful content → jailbreak → profanity."""
    return (
        Guard()
        .use(InputLengthValidator(min_chars=2, max_chars=8000), on_fail=OnFailAction.EXCEPTION)
        .use(HarmfulContentValidator(), on_fail=OnFailAction.EXCEPTION)
        .use(JailbreakDetectionValidator(), on_fail=OnFailAction.EXCEPTION)
        .use(ProfanityValidator(), on_fail=OnFailAction.EXCEPTION)
    )


def build_output_guard() -> Guard:
    """Chain: response length → PII redaction."""
    return (
        Guard()
        .use(ResponseLengthValidator(min_chars=5), on_fail=OnFailAction.EXCEPTION)
        .use(NoPIILeakValidator(), on_fail=OnFailAction.FIX)
    )


def validate_text(guard: Guard, text: str) -> tuple[bool, str, str]:
    """
    Run guard.validate(text).

    Returns (passed, validated_text, error_message).
    """
    try:
        result = guard.validate(text)
        out = result.validated_output if result.validated_output is not None else text
        return True, str(out), ""
    except ValueError as exc:
        return False, text, str(exc)
    except Exception as exc:
        return False, text, str(exc)
