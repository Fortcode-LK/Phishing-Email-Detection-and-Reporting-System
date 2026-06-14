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

def build_companions_database(db_file='companions.db'):
    if os.path.exists(db_file):
        os.remove(db_file)
        
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Create the companions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uniqueName TEXT UNIQUE,
            name TEXT,
            category TEXT,
            description TEXT,
            health INTEGER,
            shield INTEGER,
            armor INTEGER,
            power INTEGER,
            polarities TEXT,
            isPrime BOOLEAN,
            isExalted BOOLEAN
        )
    ''')
    
    inserted_count = 0
    
    # 1. Parse Sentinels
    if os.path.exists('Sentinels.json'):
        with open('Sentinels.json', 'r', encoding='utf-8') as f:
            sentinels = json.load(f)
            
        for s in sentinels:
            uniqueName = str(s.get('uniqueName', ''))
            name = str(s.get('name', ''))
            category = 'Sentinel'
            description = str(s.get('description', ''))
            health = parse_int(s.get('health', 0))
            shield = parse_int(s.get('shield', 0))
            armor = parse_int(s.get('armor', 0))
            power = parse_int(s.get('power', 0))
            polarities = json.dumps(s.get('polarities', []))
            isPrime = bool(s.get('isPrime', False))
            isExalted = False
            
            try:
                cursor.execute('''
                    INSERT INTO companions (
                        uniqueName, name, category, description, health, shield, armor, power, polarities, isPrime, isExalted
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (uniqueName, name, category, description, health, shield, armor, power, polarities, isPrime, isExalted))
                inserted_count += 1
            except sqlite3.IntegrityError:
                pass
                
    # 2. Parse Pets (Filter organic)
    allowed_keywords = ['kubrow', 'kavat', 'predasite', 'vulpaphyla', 'charger', 'venari']
    
    if os.path.exists('Pets.json'):
        with open('Pets.json', 'r', encoding='utf-8') as f:
            pets = json.load(f)
            
        for p in pets:
            name = str(p.get('name', ''))
            name_lower = name.lower()
            
            # Filter condition
            if not any(kw in name_lower for kw in allowed_keywords):
                continue
                
            uniqueName = str(p.get('uniqueName', ''))
            description = str(p.get('description', ''))
            health = parse_int(p.get('health', 0))
            shield = parse_int(p.get('shield', 0))
            armor = parse_int(p.get('armor', 0))
            power = parse_int(p.get('power', 0))
            polarities = json.dumps(p.get('polarities', []))
            isPrime = bool(p.get('isPrime', False))
            
            isExalted = 'venari' in name_lower
            
            # Determine specific category based on name
            category = 'Pet'
            if 'kubrow' in name_lower or 'charger' in name_lower:
                category = 'Kubrow'
            elif 'kavat' in name_lower or 'venari' in name_lower:
                category = 'Kavat'
            elif 'predasite' in name_lower:
                category = 'Predasite'
            elif 'vulpaphyla' in name_lower:
                category = 'Vulpaphyla'
                
            try:
                cursor.execute('''
                    INSERT INTO companions (
                        uniqueName, name, category, description, health, shield, armor, power, polarities, isPrime, isExalted
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (uniqueName, name, category, description, health, shield, armor, power, polarities, isPrime, isExalted))
                inserted_count += 1
            except sqlite3.IntegrityError:
                pass

    conn.commit()
    conn.close()
    print(f"Successfully inserted {inserted_count} companions into {db_file}.")

if __name__ == '__main__':
    build_companions_database()
