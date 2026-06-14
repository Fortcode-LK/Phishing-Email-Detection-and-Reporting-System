import json
import sqlite3
import os
import urllib.request

def build_arcanes_database(db_file='arcanes.db'):
    if os.path.exists(db_file):
        os.remove(db_file)
        
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Create the arcanes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS arcanes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uniqueName TEXT UNIQUE,
            name TEXT,
            type TEXT,
            rarity TEXT,
            levelStats TEXT
        )
    ''')
    
    print("Downloading Arcanes.json...")
    url = "https://raw.githubusercontent.com/WFCD/warframe-items/master/data/json/Arcanes.json"
    response = urllib.request.urlopen(url)
    arcanes = json.loads(response.read().decode('utf-8'))
        
    # Save the downloaded JSON file as well for reference
    with open('Arcanes.json', 'w', encoding='utf-8') as f:
        json.dump(arcanes, f, indent=2)

    inserted_count = 0
    for a in arcanes:
        uniqueName = str(a.get('uniqueName', ''))
        name = str(a.get('name', ''))
        a_type = str(a.get('type', ''))
        rarity = str(a.get('rarity', ''))
        
        levelStats = json.dumps(a.get('levelStats', []))
        
        try:
            cursor.execute('''
                INSERT INTO arcanes (
                    uniqueName, name, type, rarity, levelStats
                ) VALUES (?, ?, ?, ?, ?)
            ''', (uniqueName, name, a_type, rarity, levelStats))
            inserted_count += 1
        except sqlite3.IntegrityError:
            pass
        except Exception as e:
            print(f"Failed on arcane: {name}. Error: {e}")
            
    conn.commit()
    conn.close()
    print(f"Successfully inserted {inserted_count} arcanes into {db_file}.")

if __name__ == '__main__':
    build_arcanes_database()
