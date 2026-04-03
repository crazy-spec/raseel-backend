import re
from typing import Dict, Tuple
from dataclasses import dataclass, field


@dataclass
class SanitizationContext:
    mappings: Dict[str, str] = field(default_factory=dict)
    reverse_mappings: Dict[str, str] = field(default_factory=dict)

    def add_mapping(self, real_value: str, category: str) -> str:
        if real_value in self.mappings:
            return self.mappings[real_value]
        placeholder = f"[{category}_{len(self.mappings) + 1:03d}]"
        self.mappings[real_value] = placeholder
        self.reverse_mappings[placeholder] = real_value
        return placeholder

    def restore(self, text: str) -> str:
        result = text
        for placeholder, real_value in self.reverse_mappings.items():
            result = result.replace(placeholder, real_value)
        return result


class DataSanitizer:
    PHONE_PATTERNS = [r'\+966\s?\d{1,2}\s?\d{3}\s?\d{4}', r'05\d{8}']
    EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    def sanitize(self, text: str, business_context: dict = None) -> Tuple[str, SanitizationContext]:
        context = SanitizationContext()
        sanitized = text
        for pattern in self.PHONE_PATTERNS:
            for match in re.finditer(pattern, sanitized):
                phone = match.group()
                placeholder = context.add_mapping(phone, "PHONE")
                sanitized = sanitized.replace(phone, placeholder)
        for match in re.finditer(self.EMAIL_PATTERN, sanitized):
            email = match.group()
            placeholder = context.add_mapping(email, "EMAIL")
            sanitized = sanitized.replace(email, placeholder)
        return sanitized, context

    def restore_response(self, text: str, context: SanitizationContext) -> str:
        return context.restore(text)

    def is_safe_for_external(self, text: str) -> bool:
        for pattern in self.PHONE_PATTERNS:
            if re.search(pattern, text):
                return False
        return True


data_sanitizer = DataSanitizer()