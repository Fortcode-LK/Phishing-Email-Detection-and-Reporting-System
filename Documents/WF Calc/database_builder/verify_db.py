import sqlite3
import json

def verify_db(db_file='warframes.db'):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM warframes")
    count = cursor.fetchone()[0]
    print(f"Total warframes in DB: {count}")
    
    # Check Excalibur
    cursor.execute("SELECT name, health, aura, polarities, abilities FROM warframes WHERE name='Excalibur'")
    row = cursor.fetchone()
    if row:
        name, health, aura, polarities_str, abilities_str = row
        polarities = json.loads(polarities_str)
        abilities = json.loads(abilities_str)
        
        print(f"\nSample Warframe: {name}")
        print(f"Health: {health}")
        print(f"Aura: {aura}")
        print(f"Polarities: {polarities}")
        print(f"Number of Abilities: {len(abilities)}")
        if len(abilities) > 0:
            print(f"First Ability: {abilities[0].get('name')}")
    else:
        print("Excalibur not found!")
        
    conn.close()

if __name__ == '__main__':
    verify_db()
