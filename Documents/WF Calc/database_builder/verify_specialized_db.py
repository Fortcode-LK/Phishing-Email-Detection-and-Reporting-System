import sqlite3

def verify_dbs():
    # Check arch_weapons.db
    conn_arch = sqlite3.connect('arch_weapons.db')
    c_arch = conn_arch.cursor()
    c_arch.execute("SELECT COUNT(*) FROM weapons")
    print(f"Total arch-weapons: {c_arch.fetchone()[0]}")
    
    c_arch.execute("SELECT name, category FROM weapons LIMIT 3")
    print("Sample Arch-Weapons:")
    for row in c_arch.fetchall():
        print(f"  - {row[0]} ({row[1]})")
    conn_arch.close()
    
    print("\n")
    
    # Check companion_weapons.db
    conn_comp = sqlite3.connect('companion_weapons.db')
    c_comp = conn_comp.cursor()
    c_comp.execute("SELECT COUNT(*) FROM weapons")
    print(f"Total companion weapons: {c_comp.fetchone()[0]}")
    
    c_comp.execute("SELECT name, category FROM weapons WHERE name LIKE '%Akaten%' OR name LIKE '%Sweeper%' LIMIT 3")
    print("Sample Companion Weapons:")
    for row in c_comp.fetchall():
        print(f"  - {row[0]} ({row[1]})")
    conn_comp.close()

if __name__ == '__main__':
    verify_dbs()
