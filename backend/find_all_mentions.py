import os
import json

brain_dir = "C:/Users/saksh/.gemini/antigravity-ide/brain"
found_transcripts = []

for root, dirs, files in os.walk(brain_dir):
    for file in files:
        if file in ["transcript.jsonl", "transcript_full.jsonl"]:
            found_transcripts.append(os.path.join(root, file))

print(f"Scanning {len(found_transcripts)} transcripts...")

for path in found_transcripts:
    try:
        with open(path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if "RevenuePlans.jsx" in line:
                    # Let's see what kind of event this is
                    data = json.loads(line)
                    source = data.get("source", "")
                    type_val = data.get("type", "")
                    tool_calls = data.get("tool_calls", [])
                    content_len = len(data.get("content", ""))
                    
                    tools_str = ", ".join([tc.get("name", "") for tc in tool_calls]) if isinstance(tool_calls, list) else str(tool_calls)
                    print(f"Match in {os.path.basename(os.path.dirname(os.path.dirname(path)))} L{idx}: source={source}, type={type_val}, tools=[{tools_str}], len={content_len}, line_len={len(line)}")
    except Exception as e:
        pass
