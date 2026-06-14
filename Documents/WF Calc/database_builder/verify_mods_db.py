import sqlite3

def verify_mods_db(db_file='mods.db'):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM mods")
    count = cursor.fetchone()[0]
    print(f"Total mods in DB: {count}")
    
    cursor.execute("SELECT name, polarity, rarity, baseDrain, fusionLimit, compatName FROM mods WHERE name='Serration' OR name='Vitality' LIMIT 2")
    mods = cursor.fetchall()
    print("\nSample Mods:")
    for m in mods:
        print(f"  - {m[0]} | Polarity: {m[1]} | Rarity: {m[2]} | Drain: {m[3]} | MaxRank: {m[4]} | Compat: {m[5]}")
        
    conn.close()

if __name__ == '__main__':
    verify_mods_db()
