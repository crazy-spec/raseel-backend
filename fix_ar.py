import re

with open("app/api/routes/products.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i in range(len(lines)):
    if "iPhone 16 Pro Max" in lines[i]:
        old_ar = "\u0622\u064a\u0641\u0648\u0646 15 \u0628\u0631\u0648"
        new_ar = "\u0622\u064a\u0641\u0648\u0646 16 \u0628\u0631\u0648 \u0645\u0627\u0643\u0633"
        lines[i] = lines[i].replace(old_ar, new_ar)

    if "PS5 Pro" in lines[i]:
        old_ps = "\u0628\u0644\u0627\u064a\u0633\u062a\u064a\u0634\u0646 5"
        new_ps = "\u0628\u0644\u0627\u064a\u0633\u062a\u064a\u0634\u0646 5 \u0628\u0631\u0648"
        if new_ps not in lines[i]:
            lines[i] = lines[i].replace(old_ps, new_ps)

    if "iPad Air M3" in lines[i]:
        lines[i] = lines[i].replace("\u0628\u0645\u0639\u0627\u0644\u062c M1", "\u0628\u0645\u0639\u0627\u0644\u062c M3")

with open("app/api/routes/products.py", "w", encoding="utf-8") as f:
    f.writelines(lines)

with open("app/api/routes/products.py", "r", encoding="utf-8") as f:
    content = f.read()

print("=== VERIFICATION ===")
checks = {
    "\u0622\u064a\u0641\u0648\u0646 16": "iPhone 16 AR",
    "\u0628\u0631\u0648 \u0645\u0627\u0643\u0633": "Pro Max AR",
    "S25": "Galaxy S25",
    "M3": "M3 chip",
}

for text, label in checks.items():
    status = "PASS" if text in content else "FAIL"
    print(status + ": " + label)
