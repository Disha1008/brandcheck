"""Small labelled evaluation of the BrandCheck rule checker on the fictional FreshSip brand.
Run: python tests/labelled_eval.py
Each case = one sentence + the issue types a human expects. This is a SMALL, team-written set
(not representative); it deliberately includes paraphrases the rule engine is expected to miss."""
import os, sys, tempfile
from pathlib import Path

fd, db = tempfile.mkstemp(suffix=".db"); os.close(fd); os.unlink(db)
os.environ["DATABASE_URL"] = "sqlite:///" + db
os.environ["SECRET_KEY"] = "labelled-eval-secret-key-long-enough-123"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from fastapi.testclient import TestClient
from main import app

CASES = [
 ("FreshSip is packed with vitamin C to support your day.", set()),
 ("Try FreshSip today!", set()),
 ("FreshSip Orange is made from 100% pressed oranges with no added sugar.", set()),
 ("FreshSip Orange comes in a 300 ml recyclable bottle.", set()),
 ("FreshSip makes you feel fantastic.", set()),
 ("Fresh Sip tastes great.", {"product_name"}),
 ("Freshsip Orange comes in a 300 ml recyclable bottle.", {"product_name"}),
 ("FRESHSIP is on sale this week.", {"product_name"}),
 ("FreshSip cures colds in one day.", {"unsupported_claim"}),
 ("Our juice heals your cough.", {"unsupported_claim"}),
 ("FreshSip is clinically proven to boost immunity.", {"unsupported_claim"}),
 ("FreshSip is a miracle in a bottle!", {"unsupported_claim"}),
 ("We detox your body daily.", {"unsupported_claim"}),
 ("FreshSip eliminates colds overnight.", {"unsupported_claim"}),
 ("FreshSip helps prevent the flu.", {"unsupported_claim"}),
 ("FreshSip is the only juice that boosts immunity by 50%.", {"unsupported_claim"}),
 ("FreshSip is cheap and cheerful.", {"banned_term"}),
 ("Made with artificial flavours.", {"banned_term"}),
 ("Enjoy a chemical-free refreshing drink.", {"banned_term"}),
 ("FreshSip is better than JuiceCo.", {"banned_term"}),
]
TARGET = {"product_name", "banned_term", "unsupported_claim"}

with TestClient(app) as c:
    t = c.post("/auth/login", json={"email": "creator@freshsip.com", "password": "creator123"}).json()["access_token"]
    h = {"Authorization": f"Bearer {t}"}
    tp = fp = fn = 0; rows = []
    for text, expected in CASES:
        d = c.post("/drafts", headers=h, json={"title": "eval", "content": text}).json()
        found = {f["issue_type"] for f in c.post(f"/drafts/{d['id']}/check", headers=h).json()} & TARGET
        a, b, m = len(found & expected), len(found - expected), len(expected - found)
        tp += a; fp += b; fn += m
        rows.append((text, sorted(expected), sorted(found), "OK" if (b == 0 and m == 0) else ("MISSED" if m else "FALSE FLAG")))
for r in rows: print(f"{r[3]:10} exp={r[1]} got={r[2]} | {r[0]}")
prec = tp / (tp + fp) if tp + fp else 0; rec = tp / (tp + fn) if tp + fn else 0
print(f"\nCases: {len(CASES)}  TP={tp} FP={fp} FN={fn}  precision={prec:.2f} recall={rec:.2f}")
