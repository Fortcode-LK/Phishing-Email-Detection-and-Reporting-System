import urllib.request
import json
import sqlite3
import os
import subprocess
from slpp import slpp as lua

FACTIONS = [
    'grineer', 'corpus', 'infestation', 'orokin', 'sentient', 
    'stalker', 'narmer', 'themurmur', 'techrot', 'scaldra', 'unaffiliated'
]

def fetch_and_parse_lua(faction):
    url = f"https://warframe.fandom.com/wiki/Module:Enemies/data/{faction}?action=raw"
    try:
        print(f"Curling {url}...")
        result = subprocess.run(['curl', '-s', '-A', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36', url], capture_output=True, text=True, check=True)
        content = result.stdout
    except Exception as e:
        print(f"Failed to fetch {faction}: {e}")
        return {}

    lines = content.split('\n')
    clean_lines = []
    for line in lines:
        if line.strip().startswith('--'):
            continue
        if '--' in line:
            if '"--"' not in line and "'--'" not in line:
                line = line.split('--')[0]
        clean_lines.append(line)
    
    clean_lua = "\n".join(clean_lines)
    clean_lua = clean_lua.replace("return {", "{", 1)

    try:
        data = lua.decode(clean_lua)
        return data
    except Exception as e:
        print(f"Failed to parse Lua for {faction}: {e}")
        with open(f"failed_{faction}.lua", "w", encoding="utf-8") as f:
            f.write(clean_lua)
        return {}

def build_enemies_db():
    all_enemies = []
    
    for faction in FACTIONS:
        print(f"Fetching {faction}...")
        data = fetch_and_parse_lua(faction)
        if not data or not isinstance(data, dict):
            print(f"Skipping {faction} (data is not a dict)")
            continue
            
        for name, details in data.items():
            general = details.get('General', {})
            stats = details.get('Stats', {})
            
            enemy = {
                'name': name,
                'faction': general.get('Faction', faction.capitalize()),
                'type': general.get('Type', ''),
                'health': stats.get('Health', 0),
                'armor': stats.get('Armor', 0),
                'shields': stats.get('Shield', 0),
                'baseLevel': stats.get('BaseLevel', 1),
                'description': general.get('Description', '')
            }
            all_enemies.append(enemy)

    with open('Enemies.json', 'w', encoding='utf-8') as f:
        json.dump(all_enemies, f, indent=4)
        
    db_file = 'enemies.db'
    if os.path.exists(db_file):
        os.remove(db_file)
        
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enemies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            faction TEXT,
            type TEXT,
            health INTEGER,
            armor INTEGER,
            shields INTEGER,
            baseLevel INTEGER,
            description TEXT
        )
    ''')
    
    inserted = 0
    for e in all_enemies:
        try:
            cursor.execute('''
                INSERT INTO enemies (name, faction, type, health, armor, shields, baseLevel, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (e['name'], e['faction'], e['type'], e['health'], e['armor'], e['shields'], e['baseLevel'], e['description']))
            inserted += 1
        except Exception as err:
            print(f"Failed to insert {e['name']}: {err}")
            
    conn.commit()
    conn.close()
    
    print(f"Successfully processed {inserted} enemies.")

if __name__ == '__main__':
    build_enemies_db()
