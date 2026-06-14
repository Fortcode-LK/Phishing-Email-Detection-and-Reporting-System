import json
import sqlite3
import os

def parse_float(val, default=0.0):
    try:
        if val is None:
            return default
        return float(val)
    except (ValueError, TypeError):
        return default

def parse_int(val, default=0):
    try:
        if val is None:
            return default
        return int(val)
    except (ValueError, TypeError):
        return default

def build_weapons_database(db_file='weapons.db'):
    if os.path.exists(db_file):
        os.remove(db_file)
        
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Create the weapons table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weapons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uniqueName TEXT UNIQUE,
            name TEXT,
            category TEXT,
            type TEXT,
            criticalChance REAL,
            criticalMultiplier REAL,
            procChance REAL,
            fireRate REAL,
            totalDamage REAL,
            damage TEXT,
            polarities TEXT,
            attacks TEXT,
            isPrime BOOLEAN,
            magazineSize INTEGER,
            reloadTime REAL,
            multishot INTEGER,
            stancePolarity TEXT,
            range REAL,
            comboDuration INTEGER,
            heavyAttackDamage INTEGER
        )
    ''')
    
    files_to_parse = [
        ('Primary.json', 'Primary'),
        ('Secondary.json', 'Secondary'),
        ('Melee.json', 'Melee')
    ]
    
    inserted_count = 0
    
    for file_name, category in files_to_parse:
        if not os.path.exists(file_name):
            print(f"Skipping {file_name}, file not found.")
            continue
            
        with open(file_name, 'r', encoding='utf-8') as f:
            weapons_data = json.load(f)
            
        for wp in weapons_data:
            uniqueName = str(wp.get('uniqueName', ''))
            name = str(wp.get('name', ''))
            w_type = str(wp.get('type', ''))
            criticalChance = parse_float(wp.get('criticalChance', 0.0))
            criticalMultiplier = parse_float(wp.get('criticalMultiplier', 0.0))
            procChance = parse_float(wp.get('procChance', 0.0))
            fireRate = parse_float(wp.get('fireRate', 0.0))
            totalDamage = parse_float(wp.get('totalDamage', 0.0))
            
            damage = json.dumps(wp.get('damage', {}))
            polarities = json.dumps(wp.get('polarities', []))
            attacks = json.dumps(wp.get('attacks', []))
            isPrime = bool(wp.get('isPrime', False))
            
            # Gun specific
            magazineSize = parse_int(wp.get('magazineSize', None)) if wp.get('magazineSize') is not None else None
            reloadTime = parse_float(wp.get('reloadTime', None)) if wp.get('reloadTime') is not None else None
            multishot = parse_int(wp.get('multishot', None)) if wp.get('multishot') is not None else None
            
            # Melee specific
            stancePolarity = str(wp.get('stancePolarity', '')) if wp.get('stancePolarity') else None
            range_val = parse_float(wp.get('range', None)) if wp.get('range') is not None else None
            comboDuration = parse_int(wp.get('comboDuration', None)) if wp.get('comboDuration') is not None else None
            heavyAttackDamage = parse_int(wp.get('heavyAttackDamage', None)) if wp.get('heavyAttackDamage') is not None else None
            
            try:
                cursor.execute('''
                    INSERT INTO weapons (
                        uniqueName, name, category, type, criticalChance, criticalMultiplier, procChance, fireRate,
                        totalDamage, damage, polarities, attacks, isPrime, magazineSize, reloadTime, multishot,
                        stancePolarity, range, comboDuration, heavyAttackDamage
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    uniqueName, name, category, w_type, criticalChance, criticalMultiplier, procChance, fireRate,
                    totalDamage, damage, polarities, attacks, isPrime, magazineSize, reloadTime, multishot,
                    stancePolarity, range_val, comboDuration, heavyAttackDamage
                ))
                inserted_count += 1
            except sqlite3.IntegrityError:
                # Handle potential duplicates
                pass
            except Exception as e:
                print(f"Failed on weapon: {name}. Error: {e}")
                
    conn.commit()
    conn.close()
    print(f"Successfully inserted {inserted_count} weapons into {db_file}.")

if __name__ == '__main__':
    build_weapons_database()
