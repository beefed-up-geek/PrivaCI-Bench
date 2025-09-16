import json
from pathlib import Path

# 입력/출력 경로
in_path  = Path("/Users/taeyoonkwack/Documents/PrivaCI-Bench/HF_cache/KBs/GDPR/GDPR_with_reference.jsonl")
out_path = Path("GDPR_cleaned.jsonl")

keep_keys = [
    "regulation_id",
    "norm_type",
    "sender",
    "recipient",
    "subject",
    "information_type",
    "purpose",
    "reference", 
    "regulation_content"
]

with in_path.open("r", encoding="utf-8") as fin, out_path.open("w", encoding="utf-8") as fout:
    for line in fin:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        obj = json.loads(s)
        new_obj = {k: obj.get(k, None) for k in keep_keys}
        fout.write(json.dumps(new_obj, ensure_ascii=False, indent=2) + "\n")

print("변환 완료 →", out_path)
