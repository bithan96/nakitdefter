import sqlite3

conn = sqlite3.connect("finance.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM users")

rows = cursor.fetchall()

print("USERS IN DATABASE:")
for r in rows:
    print(r)

conn.close()