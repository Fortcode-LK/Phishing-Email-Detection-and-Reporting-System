import json
import sqlite3
import os

def build_archwings_database(json_file='Archwing.json', db_file='archwings.db'):
    if os.path.exists(db_file):
        os.remove(db_file)
        
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Create the archwings table using the warframes schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS archwings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uniqueName TEXT UNIQUE,
            name TEXT,
            description TEXT,
            health INTEGER,
            shield INTEGER,
            armor INTEGER,
            power INTEGER,
            sprintSpeed REAL,
            aura TEXT,
            polarities TEXT,
            abilities TEXT,
            isPrime BOOLEAN
        )
    ''')
    
    # Load JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        archwings = json.load(f)
        
    inserted_count = 0
    for aw in archwings:
        uniqueName = str(aw.get('uniqueName', ''))
        name = str(aw.get('name', ''))
        description = str(aw.get('description', ''))
        health = int(aw.get('health', 0) or 0)
        shield = int(aw.get('shield', 0) or 0)
        armor = int(aw.get('armor', 0) or 0)
        power = int(aw.get('power', 0) or 0)
        try:
            sprintSpeed = float(aw.get('sprintSpeed', 1.0) or 1.0)
        except ValueError:
            sprintSpeed = 1.0
        aura = str(aw.get('aura', ''))
        polarities = json.dumps(aw.get('polarities', []))
        abilities = json.dumps(aw.get('abilities', []))
        isPrime = bool(aw.get('isPrime', False))
        
        try:
            cursor.execute('''
                INSERT INTO archwings (
                    uniqueName, name, description, health, shield, armor, power, sprintSpeed, aura, polarities, abilities, isPrime
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (uniqueName, name, description, health, shield, armor, power, sprintSpeed, aura, polarities, abilities, isPrime))
            inserted_count += 1
        except sqlite3.IntegrityError:
            pass
        except Exception as e:
            print(f"Failed on archwing: {name}. Error: {e}")
            
    conn.commit()
    conn.close()
    print(f"Successfully inserted {inserted_count} archwings into {db_file}.")

if __name__ == '__main__':
    build_archwings_database()
