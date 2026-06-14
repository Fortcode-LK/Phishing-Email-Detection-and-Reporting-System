import sqlite3

def verify_archwings_db(db_file='archwings.db'):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM archwings")
    count = cursor.fetchone()[0]
    print(f"Total archwings in DB: {count}")
    
    cursor.execute("SELECT name, health, shield, armor, power, sprintSpeed FROM archwings")
    archwings = cursor.fetchall()
    print("\nArchwings:")
    for aw in archwings:
        print(f"  - {aw[0]} | Health: {aw[1]}, Shield: {aw[2]}, Armor: {aw[3]}, Sprint: {aw[5]}")
        
    conn.close()

if __name__ == '__main__':
    verify_archwings_db()
