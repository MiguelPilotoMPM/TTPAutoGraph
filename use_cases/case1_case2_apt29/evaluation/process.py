import csv
import json
import os

json_dir = "."  # carpeta con los .json
output_file = "ttps_por_informe.csv"

with open(output_file, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["title", "ttps"])

    for fname in sorted(os.listdir(json_dir)):
        if not fname.endswith(".json"):
            continue

        with open(os.path.join(json_dir, fname)) as f:
            data = json.load(f)

        title = os.path.splitext(fname)[0]
        ttps_raw = data.get("ttp_info", {}).get("ttps", [])

        # TTPs únicas, manteniendo orden de aparición
        seen = set()
        ttps = []
        for entry in ttps_raw:
            t = entry.get("technique", "").strip()
            if t and t not in seen:
                seen.add(t)
                ttps.append(t)

        writer.writerow([title, " ".join(ttps)])

print(f"CSV generado: {output_file}")