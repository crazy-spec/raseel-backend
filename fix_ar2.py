
import json

with open('app/api/routes/products.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed = 0
for i in range(len(lines)):
    if 'iPhone 16 Pro Max' in lines[i]:
        # Find current Arabic and replace
        old = chr(1570)+chr(1610)+chr(1601)+chr(1608)+chr(1606)+' 15 '+chr(1576)+chr(1585)+chr(1608)
        new = chr(1570)+chr(1610)+chr(1601)+chr(1608)+chr(1606)+' 16 '+chr(1576)+chr(1585)+chr(1608)+' '+chr(1605)+chr(1575)+chr(1603)+chr(1587)
        if old in lines[i]:
            lines[i] = lines[i].replace(old, new)
            fixed += 1
            print('FIXED iPhone Arabic')

    if 'PS5 Pro' in lines[i]:
        old2 = chr(1576)+chr(1604)+chr(1575)+chr(1610)+chr(1587)+chr(1578)+chr(1610)+chr(1588)+chr(1606)+' 5'
        new2 = chr(1576)+chr(1604)+chr(1575)+chr(1610)+chr(1587)+chr(1578)+chr(1610)+chr(1588)+chr(1606)+' 5 '+chr(1576)+chr(1585)+chr(1608)
        if old2 in lines[i] and new2 not in lines[i]:
            lines[i] = lines[i].replace(old2, new2)
            fixed += 1
            print('FIXED PS5 Arabic')

with open('app/api/routes/products.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Total fixes: ' + str(fixed))

# Verify
with open('app/api/routes/products.py', 'r', encoding='utf-8') as f:
    content = f.read()

target_iphone = chr(1570)+chr(1610)+chr(1601)+chr(1608)+chr(1606)+' 16'
target_max = chr(1605)+chr(1575)+chr(1603)+chr(1587)

print()
print('=== VERIFY ===')
print(('PASS' if target_iphone in content else 'FAIL') + ': iPhone 16 AR')
print(('PASS' if target_max in content else 'FAIL') + ': Pro Max AR')
print(('PASS' if 'S25' in content else 'FAIL') + ': Galaxy S25')
print(('PASS' if 'M3' in content else 'FAIL') + ': M3 chip')
