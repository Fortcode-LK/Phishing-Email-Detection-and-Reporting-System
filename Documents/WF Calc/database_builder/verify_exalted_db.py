import sqlite3

def verify_exalted_db(db_file='exalted_weapons.db'):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM weapons")
    count = cursor.fetchone()[0]
    print(f"Total exalted weapons in DB: {count}")
    
    # Check Excalibur's Exalted Blade
    cursor.execute("SELECT name, category, criticalChance, totalDamage FROM weapons WHERE name='Exalted Blade'")
    row = cursor.fetchone()
    if row:
        print(f"\nMelee Exalted Sample: {row[0]} | Category: {row[1]} | Crit Chance: {row[2]} | Total Damage: {row[3]}")
    
    # Check Mesa's Regulators
    cursor.execute("SELECT name, category, fireRate, multishot FROM weapons WHERE name='Regulators'")
    row = cursor.fetchone()
    if row:
        print(f"Gun Exalted Sample: {row[0]} | Category: {row[1]} | Fire Rate: {row[2]} | Multishot: {row[3]}")
        
    conn.close()

if __name__ == '__main__':
    verify_exalted_db()
