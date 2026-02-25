"""
Input Sanitization and Validation for AI Prompts.

Provides security against:
1. Prompt injection attacks
2. Malicious input characters
3. Content policy violations
"""

import re

import structlog

logger = structlog.get_logger()


# =============================================================================
# PROMPT INJECTION DETECTION PATTERNS
# =============================================================================

PROMPT_INJECTION_PATTERNS = [
    # Instruction override attempts
    r"ignore\s+(previous|all|above|prior)\s+(instructions?|prompts?|rules?)",
    r"forget\s+(everything|all|previous|above)",
    r"disregard\s+(previous|all|above|prior)",
    r"override\s+(previous|all|system)",
    # Role manipulation
    r"you\s+are\s+(now|no\s+longer)",
    r"act\s+as\s+(if|a|an)",
    r"pretend\s+(to\s+be|you\s+are)",
    r"switch\s+(to|into)\s+(a|an|the)",
    # System prompt extraction
    r"(show|reveal|tell|output|print|display)\s+(me\s+)?(your|the|system)\s+(prompt|instructions?|rules?)",
    r"what\s+(are|is)\s+your\s+(instructions?|prompt|rules?|system)",
    # Delimiter injection
    r"```\s*(system|user|assistant)",
    r"<\|?(system|user|assistant|im_start|im_end)\|?>",
    r"\[INST\]|\[/INST\]",
    # Data exfiltration
    r"(output|print|show|reveal)\s+(the\s+)?(api|secret|key|password|token|credential)",
    r"(env|environment|config|settings?)\s*[\[\.]",
    # Code injection
    r"(exec|eval|import|require|include)\s*\(",
    r"__[a-z]+__",  # Python dunder methods
    # Turkish variants
    r"(önceki|tüm|yukarıdaki)\s+(talimatları?|kuralları?)\s+(unut|yoksay|görmezden\s+gel)",
    r"(sistem|asistan)\s+(promptunu?|talimatlarını?)\s+(göster|yaz|söyle)",
]

# Compile patterns for performance
COMPILED_INJECTION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE | re.UNICODE) for pattern in PROMPT_INJECTION_PATTERNS
]


# =============================================================================
# DANGEROUS CHARACTERS
# =============================================================================

# Characters that could break prompt structure or enable injection
DANGEROUS_CHARS = {
    # Control characters
    "\x00",
    "\x01",
    "\x02",
    "\x03",
    "\x04",
    "\x05",
    "\x06",
    "\x07",
    "\x08",
    "\x0b",
    "\x0c",
    "\x0e",
    "\x0f",
    "\x10",
    "\x11",
    "\x12",
    "\x13",
    "\x14",
    "\x15",
    "\x16",
    "\x17",
    "\x18",
    "\x19",
    "\x1a",
    "\x1b",
    "\x1c",
    "\x1d",
    "\x1e",
    "\x1f",
    "\x7f",
    # Potential delimiter characters
    "`",  # Code blocks
    "|",  # Pipe (used in some prompt formats)
}

# Characters to escape rather than remove
ESCAPE_CHARS = {
    '"': '\\"',
    "'": "\\'",
    "\\": "\\\\",
}


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================


def detect_prompt_injection(text: str) -> tuple[bool, str | None]:
    """
    Detect potential prompt injection attempts.

    Args:
        text: Input text to check

    Returns:
        Tuple of (is_injection_detected, matched_pattern_description)
    """
    if not text:
        return False, None

    text_lower = text.lower()

    for i, pattern in enumerate(COMPILED_INJECTION_PATTERNS):
        if pattern.search(text_lower):
            logger.warning(
                "Prompt injection detected",
                pattern_index=i,
                pattern=PROMPT_INJECTION_PATTERNS[i],
                input_preview=text[:100],
            )
            return True, PROMPT_INJECTION_PATTERNS[i]

    return False, None


def validate_child_name(name: str) -> tuple[bool, str]:
    """
    Validate a child's name for safe use in prompts.

    Args:
        name: The child's name to validate

    Returns:
        Tuple of (is_valid, sanitized_name_or_error_message)
    """
    if not name or not name.strip():
        return False, "İsim boş olamaz"

    name = name.strip()

    # Check length
    if len(name) > 50:
        return False, "İsim 50 karakterden uzun olamaz"

    if len(name) < 2:
        return False, "İsim en az 2 karakter olmalı"

    # Check for injection
    is_injection, pattern = detect_prompt_injection(name)
    if is_injection:
        logger.warning("Injection attempt in child_name", name=name)
        return False, "Geçersiz isim formatı"

    # Allow only letters (including Turkish), spaces, and common name characters
    # Turkish: ğüşıöçĞÜŞİÖÇ
    allowed_pattern = r"^[a-zA-ZğüşıöçĞÜŞİÖÇ\s\-']+$"
    if not re.match(allowed_pattern, name):
        return False, "İsim sadece harf içerebilir"

    # Check for excessive spaces
    if "  " in name:
        name = re.sub(r"\s+", " ", name)

    return True, name


def sanitize_for_prompt(
    text: str,
    max_length: int = 500,
    allow_newlines: bool = False,
    field_name: str = "input",
) -> str:
    """
    Sanitize user input for safe inclusion in AI prompts.

    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        allow_newlines: Whether to preserve newlines
        field_name: Name of field for logging

    Returns:
        Sanitized text safe for prompt inclusion
    """
    if not text:
        return ""

    original_length = len(text)

    # Remove dangerous characters
    for char in DANGEROUS_CHARS:
        text = text.replace(char, "")

    # Handle newlines
    if not allow_newlines:
        text = text.replace("\n", " ").replace("\r", " ")
    else:
        # Normalize newlines
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Limit consecutive newlines
        text = re.sub(r"\n{3,}", "\n\n", text)

    # Escape special characters
    for char, escaped in ESCAPE_CHARS.items():
        text = text.replace(char, escaped)

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()

    # Truncate if needed
    if len(text) > max_length:
        text = text[:max_length].rsplit(" ", 1)[0]  # Don't cut words
        logger.info(
            "Input truncated",
            field=field_name,
            original_length=original_length,
            truncated_to=len(text),
        )

    return text


def sanitize_scenario_prompt(prompt: str) -> str:
    """
    Sanitize scenario/story prompt input.

    Args:
        prompt: The scenario prompt text

    Returns:
        Sanitized prompt text
    """
    # Check for injection first
    is_injection, pattern = detect_prompt_injection(prompt)
    if is_injection:
        logger.warning(
            "Injection attempt in scenario_prompt blocked",
            prompt_preview=prompt[:100],
        )
        # Return a safe default instead of the malicious input
        return "Büyülü bir macera"

    return sanitize_for_prompt(
        prompt,
        max_length=500,
        allow_newlines=False,
        field_name="scenario_prompt",
    )


def sanitize_visual_style(style: str) -> str:
    """
    Sanitize visual style description.

    Args:
        style: Visual style text

    Returns:
        Sanitized style text
    """
    is_injection, _ = detect_prompt_injection(style)
    if is_injection:
        logger.warning("Injection attempt in visual_style blocked")
        return "Children's book illustration style"

    return sanitize_for_prompt(
        style,
        max_length=200,
        allow_newlines=False,
        field_name="visual_style",
    )


def sanitize_learning_outcomes(outcomes: list[str]) -> list[str]:
    """
    Sanitize learning outcome values.

    Args:
        outcomes: List of learning outcome strings

    Returns:
        Sanitized list
    """
    sanitized = []
    for outcome in outcomes:
        if not outcome:
            continue

        # Simple sanitization for enum-like values
        clean = sanitize_for_prompt(outcome, max_length=100, field_name="learning_outcome")

        # Check for injection
        is_injection, _ = detect_prompt_injection(clean)
        if not is_injection and clean:
            sanitized.append(clean)

    return sanitized


# =============================================================================
# INPUT VALIDATION RESULT
# =============================================================================


class ValidationResult:
    """Result of input validation."""

    def __init__(self, is_valid: bool, value: any = None, error: str = None):
        self.is_valid = is_valid
        self.value = value
        self.error = error

    def __bool__(self):
        return self.is_valid


def validate_story_inputs(
    child_name: str,
    child_age: int,
    scenario_prompt: str,
    visual_style: str = None,
    learning_outcomes: list[str] = None,
) -> ValidationResult:
    """
    Validate all story generation inputs.

    Args:
        child_name: Child's name
        child_age: Child's age
        scenario_prompt: Story scenario/theme
        visual_style: Visual style description
        learning_outcomes: Educational values

    Returns:
        ValidationResult with sanitized values or error
    """
    # Validate child name
    is_valid, result = validate_child_name(child_name)
    if not is_valid:
        return ValidationResult(False, error=f"İsim hatası: {result}")
    sanitized_name = result

    # Validate age
    if not isinstance(child_age, int) or child_age < 2 or child_age > 12:
        return ValidationResult(False, error="Yaş 2-12 arasında olmalı")

    # Sanitize scenario prompt
    sanitized_scenario = sanitize_scenario_prompt(scenario_prompt)
    if not sanitized_scenario:
        return ValidationResult(False, error="Senaryo açıklaması gerekli")

    # Sanitize visual style
    sanitized_style = sanitize_visual_style(visual_style) if visual_style else None

    # Sanitize learning outcomes
    sanitized_outcomes = sanitize_learning_outcomes(learning_outcomes) if learning_outcomes else []

    return ValidationResult(
        True,
        value={
            "child_name": sanitized_name,
            "child_age": child_age,
            "scenario_prompt": sanitized_scenario,
            "visual_style": sanitized_style,
            "learning_outcomes": sanitized_outcomes,
        },
    )
