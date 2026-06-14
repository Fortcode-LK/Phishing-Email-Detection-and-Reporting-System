import json
import sqlite3
import os

def parse_int(val, default=0):
    try:
        if val is None:
            return default
        return int(val)
    except (ValueError, TypeError):
        return default

def build_mods_database(json_file='Mods.json', db_file='mods.db'):
    if os.path.exists(db_file):
        os.remove(db_file)
        
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Create the mods table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uniqueName TEXT UNIQUE,
            name TEXT,
            type TEXT,
            polarity TEXT,
            rarity TEXT,
            baseDrain INTEGER,
            fusionLimit INTEGER,
            compatName TEXT,
            levelStats TEXT,
            isAugment BOOLEAN,
            isPrime BOOLEAN
        )
    ''')
    
    with open(json_file, 'r', encoding='utf-8') as f:
        mods = json.load(f)
        
    inserted_count = 0
    for m in mods:
        uniqueName = str(m.get('uniqueName', ''))
        name = str(m.get('name', ''))
        w_type = str(m.get('type', ''))
        polarity = str(m.get('polarity', ''))
        rarity = str(m.get('rarity', ''))
        baseDrain = parse_int(m.get('baseDrain', 0))
        fusionLimit = parse_int(m.get('fusionLimit', 0))
        compatName = str(m.get('compatName', ''))
        
        levelStats = json.dumps(m.get('levelStats', []))
        isAugment = bool(m.get('isAugment', False))
        isPrime = bool(m.get('isPrime', False))
        
        try:
            cursor.execute('''
                INSERT INTO mods (
                    uniqueName, name, type, polarity, rarity, baseDrain, fusionLimit, compatName, levelStats, isAugment, isPrime
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (uniqueName, name, w_type, polarity, rarity, baseDrain, fusionLimit, compatName, levelStats, isAugment, isPrime))
            inserted_count += 1
        except sqlite3.IntegrityError:
            pass
        except Exception as e:
            print(f"Failed on mod: {name}. Error: {e}")
            
    conn.commit()
    conn.close()
    print(f"Successfully inserted {inserted_count} mods into {db_file}.")

if __name__ == '__main__':
    build_mods_database()
