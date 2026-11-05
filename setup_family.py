"""Put this family's projects in the pool and register its health checks. Run by the Setup workflow. Safe to run again."""
from scrape_hub_client import register_project, seed_queue, set_pool, set_probes

from family import FAMILY, HOST, PROBES, PROJECTS

print("health checks:", set_probes(FAMILY, PROBES))
for p in PROJECTS:
    register_project(p["name"], title=p["title"], unit_label=p["unit_label"], record_label=p["record_label"])
    set_pool(p["name"], FAMILY, p["task"], target=HOST, probe=PROBES[0]["name"], geo="", max_workers=3, threads=1, delay_ms=1300)
    print(p["name"], "queue:", seed_queue(p["name"], p["items"]))
