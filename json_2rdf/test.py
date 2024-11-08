import json

with open("pred_mapping.json", "r") as f:
    json_data = json.load(f)

count = 0
for k, v in json_data.items():
    for kv, vv in v.items():
        kv = "wdt"
        vv = f"P{count}"
        v = {kv:vv}
        json_data[k] = v
        count += 1

with open("pred_mapping2.json", "w") as f:
    json.dump(json_data, f, ensure_ascii=False, indent=4)
