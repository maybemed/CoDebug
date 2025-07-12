from fastapi import APIRouter
import json
from pathlib import Path
from pydantic import BaseModel
from backend.utils.rte import rte_from_text

router = APIRouter()

class KGRequest(BaseModel):
    text: str

@router.get("/")
async def get_knowledge_graph():
    # 修正为绝对路径，确保无论工作目录如何都能找到文件
    base_dir = Path(__file__).resolve().parent.parent.parent
    triples_path = base_dir / "knowledge" / "triples.json"
    if not triples_path.exists():
        return {"triples": []}
    with open(triples_path, "r", encoding="utf-8") as f:
        triples = json.load(f)
    return {"triples": triples}

@router.post("/extract")
async def extract_kg(req: KGRequest):
    triples = await rte_from_text(req.text)
    return {"triples": triples} 