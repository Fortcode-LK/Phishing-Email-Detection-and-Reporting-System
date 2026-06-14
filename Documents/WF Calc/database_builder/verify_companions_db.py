import sqlite3

def verify_companions_db(db_file='companions.db'):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM companions")
    count = cursor.fetchone()[0]
    print(f"Total companions in DB: {count}")
    
    cursor.execute("SELECT name, category, health, isExalted FROM companions WHERE isExalted = 1")
    exalted_pets = cursor.fetchall()
    print("\nExalted Pets:")
    for pet in exalted_pets:
        print(f"  - Name: {pet[0]} | Category: {pet[1]} | Health: {pet[2]} | isExalted: {pet[3]}")
        
    cursor.execute("SELECT name, category, armor FROM companions WHERE category = 'Sentinel' LIMIT 2")
    sentinels = cursor.fetchall()
    print("\nSample Sentinels:")
    for s in sentinels:
        print(f"  - {s[0]} (Armor: {s[2]})")
        
    cursor.execute("SELECT name, category, shield FROM companions WHERE category = 'Kubrow' LIMIT 2")
    kubrows = cursor.fetchall()
    print("\nSample Kubrows:")
    for k in kubrows:
        print(f"  - {k[0]} (Shield: {k[2]})")
        
    conn.close()

if __name__ == '__main__':
    verify_companions_db()
