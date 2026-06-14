import json

with open('Melee.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total warframes: {len(data)}")
if len(data) > 0:
    wf = data[0]
    print("Keys in a warframe object:")
    for key in wf.keys():
        val = wf[key]
        print(f"  - {key} ({type(val).__name__})")
    
    # Print the first item for reference
    print("\nFirst warframe sample:")
    print(json.dumps(wf, indent=2)[:500] + "...")
