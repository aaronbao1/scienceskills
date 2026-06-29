from __future__ import annotations

import re

# Ordered: candidate-controlled text that could hijack a judge prompt template.
_INJECTION_PATTERNS = {
    "role_marker": r"(?i)\b(?:system|assistant|user)\s*:",
    "xml_role_tag": r"(?i)<\s*/?\s*(?:system|assistant|user|instructions?)\s*>",
    "inst_tag": r"(?i)\[/?(?:INST|SYS)\]",
    "ignore_previous": r"(?i)ignore (?:the )?(?:above|previous|prior)",
    "appoint_judge": r"(?i)you are (?:now )?the judge",
    "code_fence": r"```",
    "preset_verdict": r"(?i)\b(?:verdict|winner|score)\s*[:=]",
}


def detect_injection(text: str) -> list[str]:
    """Names of injection / role-marker patterns present in candidate-controlled text."""
    if not isinstance(text, str):
        return []
    return [name for name, pat in _INJECTION_PATTERNS.items() if re.search(pat, text)]


def sanitize_for_judge_template(text: str) -> str:
    """Neutralize delimiter/role markers so candidate text cannot hijack the judge prompt."""
    if not isinstance(text, str):
        return ""
    out = text.replace("```", "'''")  # defuse code fences
    # escape the colon after a role word so 'System:' no longer parses as a role line
    out = re.sub(r"(?i)\b(system|assistant|user)\s*:", r"\1&#58;", out)
    # turn role/instruction tags into inert parentheticals
    out = re.sub(r"<(\s*/?\s*(?:system|assistant|user|instructions?)\s*)>", r"(\1)", out, flags=re.I)
    out = re.sub(r"\[/?(?:INST|SYS)\]", "(redacted-tag)", out, flags=re.I)
    return out
