from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
import json, uuid, random, os
from .models import AssessmentCreate, NextItem, ResponseIn

BASE = os.path.dirname(__file__)
with open(os.path.join(BASE, "items_seed.json")) as f:
    SEED = json.load(f)
ITEMS = {it["id"]: it for it in SEED["items"]}

app = FastAPI(title="CONFIVUE API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

ASSESSMENTS: Dict[str, Dict[str, Any]] = {}
RESPONSES: Dict[str, List[Dict[str, Any]]] = {}

def eligible_items(age_band: str, asked_ids: set):
    return [it for it in ITEMS.values() if it["age_band"] == age_band and it["id"] not in asked_ids]

def estimate_theta(resps: List[Dict[str, Any]]) -> float:
    if not resps: return 0.0
    mapped = [(r["category"] - 2) * 0.8 for r in resps]
    return sum(mapped) / len(mapped)

def scale_to_0_100(theta: float) -> int:
    z = max(-2.5, min(2.5, theta))
    return int(round((z + 2.5) / 5.0 * 100))

def band(score: int) -> str:
    return "Emerging" if score < 40 else "Growing" if score < 70 else "Thriving"

@app.post("/v1/assessments")
def create_assessment(payload: AssessmentCreate):
    a_id = str(uuid.uuid4())
    ASSESSMENTS[a_id] = {"id": a_id, "user_id": payload.user_id, "age_band": payload.age_band, "mode": payload.mode, "theta": 0.0, "sem": 1.0, "asked": [], "completed": False}
    RESPONSES[a_id] = []
    return {"assessment_id": a_id}

@app.get("/v1/assessments/{a_id}/next-item", response_model=NextItem)
def next_item(a_id: str):
    a = ASSESSMENTS.get(a_id)
    if not a or a["completed"]:
        raise HTTPException(404, "Assessment not found or complete")
    asked_ids = set(a["asked"])
    pool = eligible_items(a["age_band"], asked_ids)
    if not pool or len(a["asked"]) >= 8:
        a["completed"] = True
        return NextItem(item_id="", format="likert", stem="", options=[], domain="")
    it = random.choice(pool)
    return NextItem(item_id=it["id"], format=it["format"], stem=it["stem"], options=it["options"], domain=it["domain"])

@app.post("/v1/assessments/{a_id}/response")
def post_response(a_id: str, payload: ResponseIn):
    a = ASSESSMENTS.get(a_id)
    if not a: raise HTTPException(404, "Assessment not found")
    if a["completed"]: raise HTTPException(400, "Assessment already completed")
    if payload.item_id in a["asked"]: raise HTTPException(400, "Item already answered")
    a["asked"].append(payload.item_id)
    RESPONSES[a_id].append({"item_id": payload.item_id, "category": payload.category, "rt_ms": payload.rt_ms})
    theta = estimate_theta(RESPONSES[a_id])
    a["theta"] = theta
    a["sem"] = max(0.3, 1.2 - 0.1*len(a["asked"]))
    if len(a["asked"]) >= 8 or a["sem"] <= 0.35:
        a["completed"] = True
    return {"asked_count": len(a["asked"]), "theta": a["theta"], "sem": a["sem"], "completed": a["completed"]}

@app.get("/v1/assessments/{a_id}/report")
def get_report(a_id: str):
    a = ASSESSMENTS.get(a_id)
    if not a: raise HTTPException(404, "Assessment not found")
    score = scale_to_0_100(a["theta"])
    return {"assessment_id": a_id, "user_id": a["user_id"], "mode": a["mode"], "scaled_score": score, "band": band(score), "sem": a["sem"], "asked": a["asked"]}

@app.get("/v1/items")
def get_items(age_band: str = None, domain: str = None):
    data = list(ITEMS.values())
    if age_band: data = [d for d in data if d["age_band"] == age_band]
    if domain: data = [d for d in data if d["domain"].lower() == domain.lower()]
    return {"count": len(data), "items": data}
