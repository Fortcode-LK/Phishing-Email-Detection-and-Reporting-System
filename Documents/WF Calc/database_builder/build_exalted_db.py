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

def build_exalted_database(db_file='exalted_weapons.db'):
    # Step 1: Collect exalted uniqueNames from Warframes.json
    exalted_ids = set()
    with open('Warframes.json', 'r', encoding='utf-8') as f:
        warframes = json.load(f)
        for wf in warframes:
            exalted_list = wf.get('exalted', [])
            for e_id in exalted_list:
                exalted_ids.add(e_id)
                
    print(f"Found {len(exalted_ids)} exalted weapon IDs in Warframes.json.")

    # Step 2: Initialize Database
    if os.path.exists(db_file):
        os.remove(db_file)
        
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Create the unified weapons table
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
    
    inserted_count = 0
    
    # Step 3: Parse Misc.json and insert matches
    with open('Misc.json', 'r', encoding='utf-8') as f:
        misc_data = json.load(f)
        
    for wp in misc_data:
        uniqueName = str(wp.get('uniqueName', ''))
        if uniqueName not in exalted_ids:
            continue
            
        name = str(wp.get('name', ''))
        category = 'Exalted'
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
            pass
        except Exception as e:
            print(f"Failed on weapon: {name}. Error: {e}")
            
    conn.commit()
    conn.close()
    print(f"Successfully inserted {inserted_count} exalted weapons into {db_file}.")

if __name__ == '__main__':
    build_exalted_database()
