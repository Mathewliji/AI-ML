import base64
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Receipt
from agent.graph import graph

router = APIRouter(prefix="/receipts", tags=["receipts"])


class ChatRequest(BaseModel):
    message: str


@router.post("/upload", summary="Upload a receipt image for AI extraction")
async def upload_receipt(file: UploadFile = File(...)):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP, or GIF images are accepted.")

    contents = await file.read()
    result = graph.invoke({
        "task": "upload",
        "image_b64": base64.standard_b64encode(contents).decode(),
        "image_media_type": file.content_type,
        "receipt_data": None,
        "category": None,
        "receipt_id": None,
        "user_message": None,
        "response": None,
        "error": None,
    })

    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])

    return {
        "receipt_id": result["receipt_id"],
        "receipt": result["receipt_data"],
        "category": result["category"],
        "message": result["response"],
    }


@router.post("/chat", summary="Ask a natural-language question about your spending")
async def chat(request: ChatRequest):
    result = graph.invoke({
        "task": "query",
        "image_b64": None,
        "image_media_type": None,
        "receipt_data": None,
        "category": None,
        "receipt_id": None,
        "user_message": request.message,
        "response": None,
        "error": None,
    })

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    return {"response": result["response"]}


@router.get("/", summary="List all saved receipts")
def list_receipts(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(Receipt).order_by(Receipt.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{receipt_id}", summary="Get a specific receipt")
def get_receipt(receipt_id: int, db: Session = Depends(get_db)):
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt
