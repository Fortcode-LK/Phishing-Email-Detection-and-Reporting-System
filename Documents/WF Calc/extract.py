import json
import sys
import os

log_path = r'C:\Users\jkiri\.gemini\antigravity-ide\brain\776cabf1-7380-466b-a6de-1d89b1087402\.system_generated\logs\transcript.jsonl'
files = {}

def unescape_arg(v):
    if isinstance(v, str):
        if v.startswith('"') and v.endswith('"'):
            try:
                return json.loads(v)
            except:
                pass
    return v

with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            obj = json.loads(line)
        except: continue
        
        if 'tool_calls' in obj:
            for call in obj['tool_calls']:
                name = call.get('name', '')
                args = call.get('args', {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except:
                        continue
                
                parsed = {k: unescape_arg(v) for k, v in args.items()}
                
                tf = parsed.get('TargetFile')
                if tf and isinstance(tf, str) and 'src/lib/engine' in tf.replace('\\', '/'):
                    if 'write_to_file' in name:
                        files[tf] = parsed.get('CodeContent', '')
                    elif 'replace_file_content' in name:
                        if tf in files:
                            tc = parsed.get('TargetContent', '')
                            rc = parsed.get('ReplacementContent', '')
                            files[tf] = files[tf].replace(tc, rc, -1 if parsed.get('AllowMultiple') else 1)
                    elif 'multi_replace_file_content' in name:
                        if tf in files:
                            chunks = parsed.get('ReplacementChunks', [])
                            if isinstance(chunks, str):
                                try:
                                    chunks = json.loads(chunks)
                                except:
                                    pass
                            if isinstance(chunks, list):
                                for chunk in chunks:
                                    if isinstance(chunk, str):
                                        try:
                                            chunk = json.loads(chunk)
                                        except:
                                            continue
                                    if isinstance(chunk, dict):
                                        tc = chunk.get('TargetContent', '')
                                        rc = chunk.get('ReplacementContent', '')
                                        files[tf] = files[tf].replace(tc, rc, -1 if chunk.get('AllowMultiple') else 1)

for target, content in files.items():
    if content:
        out_path = target
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print('Restored:', out_path)
