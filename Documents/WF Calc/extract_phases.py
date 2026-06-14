import re

path = r'C:\Users\jkiri\Documents\WF Calc\complete_implementation_history_backup.md'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

matches = re.split(r'=== VERSION (\d+) ===', text)

phases = []
for i in range(1, len(matches), 2):
    version = matches[i]
    content = matches[i+1].strip()
    
    for line in content.split('\n'):
        line = line.strip(' "\r')
        if line.startswith('# '):
            phases.append(f'Version {version}: {line}')
            break

with open(r'C:\Users\jkiri\Documents\WF Calc\phases_list.txt', 'w', encoding='utf-8') as f:
    for p in phases:
        f.write(p + '\n')
