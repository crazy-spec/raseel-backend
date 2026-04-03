import sqlite3
conn = sqlite3.connect("raseel_dev.db")
c = conn.cursor()
c.execute("PRAGMA table_info(businesses)")
columns = c.fetchall()
print("=== BUSINESS TABLE COLUMNS ===")
for col in columns:
    print(str(col[1]) + " (" + str(col[2]) + ")")
conn.close()
