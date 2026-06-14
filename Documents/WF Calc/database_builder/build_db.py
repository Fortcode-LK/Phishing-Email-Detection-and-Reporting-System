import json
import sqlite3
import os

def build_database(json_file='Warframes.json', db_file='warframes.db'):
    if os.path.exists(db_file):
        os.remove(db_file)
        
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Create the warframes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS warframes (
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
        warframes = json.load(f)
        
    inserted_count = 0
    for wf in warframes:
        uniqueName = str(wf.get('uniqueName', ''))
        name = str(wf.get('name', ''))
        description = str(wf.get('description', ''))
        health = int(wf.get('health', 0) or 0)
        shield = int(wf.get('shield', 0) or 0)
        armor = int(wf.get('armor', 0) or 0)
        power = int(wf.get('power', 0) or 0)
        try:
            sprintSpeed = float(wf.get('sprintSpeed', 1.0) or 1.0)
        except ValueError:
            sprintSpeed = 1.0
        aura = str(wf.get('aura', ''))
        polarities = json.dumps(wf.get('polarities', []))
        abilities = json.dumps(wf.get('abilities', []))
        isPrime = bool(wf.get('isPrime', False))
        
        try:
            cursor.execute('''
                INSERT INTO warframes (
                    uniqueName, name, description, health, shield, armor, power, sprintSpeed, aura, polarities, abilities, isPrime
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (uniqueName, name, description, health, shield, armor, power, sprintSpeed, aura, polarities, abilities, isPrime))
            inserted_count += 1
        except sqlite3.IntegrityError:
            # Handle potential duplicates in uniqueName
            pass
        except Exception as e:
            print(f"Failed on warframe: {name}. Error: {e}")
            print(f"Values: aura={aura} type={type(aura)}, sprintSpeed={sprintSpeed} type={type(sprintSpeed)}")
            
    conn.commit()
    conn.close()
    print(f"Successfully inserted {inserted_count} warframes into {db_file}.")

if __name__ == '__main__':
    build_database()
