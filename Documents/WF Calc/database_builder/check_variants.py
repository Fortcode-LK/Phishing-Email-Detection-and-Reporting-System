import sqlite3
conn = sqlite3.connect('weapons.db')
c = conn.cursor()
c.execute("SELECT name FROM weapons WHERE name LIKE 'Kuva%' OR name LIKE 'Tenet%' OR name LIKE '%Wraith%' OR name LIKE '%Vandal%' LIMIT 10")
print([row[0] for row in c.fetchall()])
conn.close()
