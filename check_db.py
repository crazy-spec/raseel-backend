import sqlite3
conn = sqlite3.connect("raseel_dev.db")
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
for t in c.fetchall():
    name = t[0]
    c.execute("SELECT COUNT(*) FROM [" + name + "]")
    print(name + ": " + str(c.fetchone()[0]))
print()
c.execute("SELECT id, name_en, sector, is_active FROM businesses")
for r in c.fetchall():
    print(str(r[1]) + " | sector=" + str(r[2]) + " | active=" + str(r[3]))
print()
c.execute("SELECT DISTINCT category FROM products")
for r in c.fetchall():
    print("category: " + str(r[0]))
print()
c.execute("SELECT email, role FROM users")
for r in c.fetchall():
    print(str(r[0]) + " | " + str(r[1]))
conn.close()
