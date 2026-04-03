import re

with open("app/api/routes/products.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix Arabic product names to match 2026
content = content.replace("\u0622\u064a\u0641\u0648\u0646 15 \u0628\u0631\u0648", "\u0622\u064a\u0641\u0648\u0646 16 \u0628\u0631\u0648 \u0645\u0627\u0643\u0633")
content = content.replace("\u062c\u0627\u0644\u0643\u0633\u064a S24", "\u062c\u0627\u0644\u0643\u0633\u064a S25 \u0623\u0644\u062a\u0631\u0627")
content = content.replace("\u0628\u0644\u0627\u064a\u0633\u062a\u064a\u0634\u0646 5\"", "\u0628\u0644\u0627\u064a\u0633\u062a\u064a\u0634\u0646 5 \u0628\u0631\u0648\"")
content = content.replace("\u062c\u0647\u0627\u0632 \u0628\u0644\u0627\u064a\u0633\u062a\u064a\u0634\u0646 5\"", "\u062c\u0647\u0627\u0632 \u0628\u0644\u0627\u064a\u0633\u062a\u064a\u0634\u0646 5 \u0628\u0631\u0648\"")
content = content.replace("\u0628\u0645\u0639\u0627\u0644\u062c M1", "\u0628\u0645\u0639\u0627\u0644\u062c M3")

with open("app/api/routes/products.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Arabic names fixed to 2026!")
print()

# Verify
lines = content.split("\n")
for i, line in enumerate(lines):
    if any(w in line for w in ["iPhone", "Samsung", "PS5", "iPad", "M3"]):
        print(f"Line {i+1}: {line.strip()[:120]}")
