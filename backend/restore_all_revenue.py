import os
import json

brain_dir = "C:/Users/saksh/.gemini/antigravity-ide/brain"
found_transcripts = []

for root, dirs, files in os.walk(brain_dir):
    for file in files:
        if file in ["transcript.jsonl", "transcript_full.jsonl"]:
            found_transcripts.append(os.path.join(root, file))

print(f"Scanning {len(found_transcripts)} transcripts...")

targets = ["aggregation.py", "repository.py", "schemas.py", "service.py", "router.py"]
restored = {}

# Scan transcripts backwards (most recent first) to find the latest valid code content
for path in reversed(found_transcripts):
    try:
        with open(path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if any(t in line for t in targets) and "PLANNER_RESPONSE" in line and "write_to_file" in line:
                    data = json.loads(line)
                    tool_calls = data.get("tool_calls", [])
                    for tc in tool_calls:
                        if tc.get("name") == "write_to_file":
                            target_file = tc.get("args", {}).get("TargetFile", "")
                            for t in targets:
                                if t in target_file and t not in restored:
                                    code = tc.get("args", {}).get("CodeContent", "")
                                    if code:
                                        dest_path = f"c:/Users/saksh/OneDrive/Desktop/unified/Unified-Dashboard/backend/src/modules/revenue/{t}"
                                        with open(dest_path, "w", encoding="utf-8") as out:
                                            out.write(code)
                                        restored[t] = path
                                        print(f"Successfully restored {t} from {os.path.basename(path)}!")
    except Exception as e:
        pass

print("Restoration finished. Restored files:", list(restored.keys()))
