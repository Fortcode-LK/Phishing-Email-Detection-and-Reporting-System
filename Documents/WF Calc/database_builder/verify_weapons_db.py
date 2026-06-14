import sqlite3

def verify_weapons_db(db_file='weapons.db'):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM weapons")
    count = cursor.fetchone()[0]
    print(f"Total weapons in DB: {count}")
    
    # Check a Primary weapon
    cursor.execute("SELECT name, category, magazineSize, criticalChance FROM weapons WHERE name='Soma Prime'")
    row = cursor.fetchone()
    if row:
        print(f"\nPrimary Sample: {row[0]} | Category: {row[1]} | Magazine: {row[2]} | Crit Chance: {row[3]}")
    
    # Check a Secondary weapon
    cursor.execute("SELECT name, category, multishot, procChance FROM weapons WHERE name='Lex Prime'")
    row = cursor.fetchone()
    if row:
        print(f"Secondary Sample: {row[0]} | Category: {row[1]} | Multishot: {row[2]} | Status Chance: {row[3]}")
        
    # Check a Melee weapon
    cursor.execute("SELECT name, category, comboDuration, stancePolarity FROM weapons WHERE name='Nikana Prime'")
    row = cursor.fetchone()
    if row:
        print(f"Melee Sample: {row[0]} | Category: {row[1]} | Combo Duration: {row[2]} | Stance Polarity: {row[3]}")
        
    conn.close()

if __name__ == '__main__':
    verify_weapons_db()
