import os
import re

backup_path = r'C:\Users\jkiri\Documents\WF Calc\complete_implementation_history_backup.md'
output_dir = r'C:\Users\jkiri\Documents\WF Calc\historical_versions'

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

with open(backup_path, 'r', encoding='utf-8') as f:
    text = f.read()

matches = re.split(r'=== VERSION (\d+) ===', text)

# matches[0] is everything before the first '=== VERSION X ==='
for i in range(1, len(matches), 2):
    version = matches[i]
    content = matches[i+1].strip()
    
    file_path = os.path.join(output_dir, f'version_{version}.md')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

print(f"Successfully split into {len(matches)//2} files in {output_dir}")
