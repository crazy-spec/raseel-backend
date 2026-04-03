from pathlib import Path

path = Path("app/api/routes/products.py")
text = path.read_text(encoding="utf-8")

text = text.replace(
    '{"name_en": "iPhone 16 Pro Max", "name_ar": "\\u0622\\u064a\\u0641\\u0648\\u0646 15 \\u0628\\u0631\\u0648"',
    '{"name_en": "iPhone 16 Pro Max", "name_ar": "آيفون 16 برو ماكس"'
)

text = text.replace(
    '{"name_en": "Samsung Galaxy S25 Ultra", "name_ar": "\\u0633\\u0627\\u0645\\u0633\\u0648\\u0646\\u062c \\u062c\\u0627\\u0644\\u0643\\u0633\\u064a S24"',
    '{"name_en": "Samsung Galaxy S25 Ultra", "name_ar": "سامسونج جالكسي S25 ألترا"'
)

text = text.replace(
    '"description_en": "iPad Air M3 2026 model", "description_ar": "\\u0622\\u064a\\u0628\\u0627\\u062f \\u0625\\u064a\\u0631 \\u0628\\u0645\\u0639\\u0627\\u0644\\u062c M1"',
    '"description_en": "iPad Air M3 2026 model", "description_ar": "آيباد إير بمعالج M3"'
)

text = text.replace(
    '{"name_en": "PS5 Pro", "name_ar": "\\u0628\\u0644\\u0627\\u064a\\u0633\\u062a\\u064a\\u0634\\u0646 5"',
    '{"name_en": "PS5 Pro", "name_ar": "بلايستيشن 5 برو"'
)

path.write_text(text, encoding="utf-8")
print("Manual Arabic fix applied.")
