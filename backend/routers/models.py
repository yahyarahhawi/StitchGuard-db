from typing import List
from datetime import datetime
import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import backend.schemas as schemas
from backend.deps import get_db
from db.models import Model

router = APIRouter(prefix="/models", tags=["models"])

# Model files directory
MODEL_FILES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "model_files")

@router.get("/", response_model=List[schemas.Model])
def list_models(
    model_type: str = None,
    platform: str = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Model)
    
    if model_type:
        query = query.filter(Model.type == model_type)
    if platform:
        query = query.filter(Model.platform == platform)
    
    return query.offset(offset).limit(limit).all()


@router.get("/files/{filename}")
def download_model_file(filename: str):
    """
    Serve model files for download
    Endpoint: /api/v1/models/files/{filename}
    """
    file_path = os.path.join(MODEL_FILES_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Model file '{filename}' not found")
    
    # Determine media type based on file extension
    media_type = "application/octet-stream"  # Default for .mlmodelc files
    
    if filename.endswith('.mlmodel'):
        media_type = "application/x-mlmodel"
    elif filename.endswith('.mlpackage'):
        media_type = "application/x-mlpackage"
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/", response_model=schemas.Model, status_code=status.HTTP_201_CREATED)
def create_model(payload: schemas.ModelCreate, db: Session = Depends(get_db)):
    model = Model(**payload.model_dump(), created_at=datetime.utcnow())
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


@router.get("/{model_id}", response_model=schemas.Model)
def get_model(model_id: int, db: Session = Depends(get_db)):
    model = db.query(Model).get(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.put("/{model_id}", response_model=schemas.Model)
def update_model(
    model_id: int,
    payload: schemas.ModelCreate,
    db: Session = Depends(get_db)
):
    model = db.query(Model).get(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(model, field, value)
    
    model.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(model)
    return model


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(model_id: int, db: Session = Depends(get_db)):
    model = db.query(Model).get(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    db.delete(model)
    db.commit() 