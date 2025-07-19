from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import backend.schemas as schemas
from backend.deps import get_db
from db.models import Tutorial, TutorialStep, Product

router = APIRouter(prefix="/tutorials", tags=["tutorials"])


# ------------------------------------------------------------------ #
#  GET all tutorials for a specific product
# ------------------------------------------------------------------ #
@router.get("/product/{product_id}", response_model=List[schemas.TutorialWithSteps])
def get_product_tutorials(product_id: int, db: Session = Depends(get_db)):
    """Get all tutorials for a specific product with their steps"""
    # Verify product exists
    product = db.query(Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get tutorials with steps
    tutorials = db.query(Tutorial).filter(Tutorial.product_id == product_id).all()
    return tutorials


# ------------------------------------------------------------------ #
#  GET active tutorial for a specific product
# ------------------------------------------------------------------ #
@router.get("/product/{product_id}/active", response_model=schemas.TutorialWithSteps)
def get_active_product_tutorial(product_id: int, db: Session = Depends(get_db)):
    """Get the active tutorial for a specific product with all steps"""
    # Verify product exists
    product = db.query(Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get active tutorial
    tutorial = db.query(Tutorial).filter(
        Tutorial.product_id == product_id,
        Tutorial.is_active == True
    ).first()
    
    if not tutorial:
        raise HTTPException(status_code=404, detail="No active tutorial found for this product")
    
    return tutorial


# ------------------------------------------------------------------ #
#  GET specific tutorial with steps
# ------------------------------------------------------------------ #
@router.get("/{tutorial_id}", response_model=schemas.TutorialWithSteps)
def get_tutorial(tutorial_id: int, db: Session = Depends(get_db)):
    """Get a specific tutorial with all its steps"""
    tutorial = db.query(Tutorial).get(tutorial_id)
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial not found")
    
    return tutorial


# ------------------------------------------------------------------ #
#  GET steps for a specific tutorial
# ------------------------------------------------------------------ #
@router.get("/{tutorial_id}/steps", response_model=List[schemas.TutorialStep])
def get_tutorial_steps(tutorial_id: int, db: Session = Depends(get_db)):
    """Get all steps for a specific tutorial"""
    # Verify tutorial exists
    tutorial = db.query(Tutorial).get(tutorial_id)
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial not found")
    
    # Get steps ordered by step_number
    steps = db.query(TutorialStep).filter(
        TutorialStep.tutorial_id == tutorial_id
    ).order_by(TutorialStep.step_number).all()
    
    return steps


# ------------------------------------------------------------------ #
#  CREATE a new tutorial
# ------------------------------------------------------------------ #
@router.post("/", response_model=schemas.Tutorial, status_code=status.HTTP_201_CREATED)
def create_tutorial(payload: schemas.TutorialCreate, db: Session = Depends(get_db)):
    """Create a new tutorial for a product"""
    # Verify product exists
    product = db.query(Product).get(payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    tutorial = Tutorial(**payload.model_dump())
    db.add(tutorial)
    db.commit()
    db.refresh(tutorial)
    return tutorial


# ------------------------------------------------------------------ #
#  CREATE a new tutorial step
# ------------------------------------------------------------------ #
@router.post("/steps", response_model=schemas.TutorialStep, status_code=status.HTTP_201_CREATED)
def create_tutorial_step(payload: schemas.TutorialStepCreate, db: Session = Depends(get_db)):
    """Create a new step for a tutorial"""
    # Verify tutorial exists
    tutorial = db.query(Tutorial).get(payload.tutorial_id)
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial not found")
    
    # Check if step number already exists for this tutorial
    existing_step = db.query(TutorialStep).filter(
        TutorialStep.tutorial_id == payload.tutorial_id,
        TutorialStep.step_number == payload.step_number
    ).first()
    
    if existing_step:
        raise HTTPException(
            status_code=400, 
            detail=f"Step {payload.step_number} already exists for this tutorial"
        )
    
    step = TutorialStep(**payload.model_dump())
    db.add(step)
    db.commit()
    db.refresh(step)
    return step


# ------------------------------------------------------------------ #
#  UPDATE tutorial
# ------------------------------------------------------------------ #
@router.put("/{tutorial_id}", response_model=schemas.Tutorial)
def update_tutorial(
    tutorial_id: int, 
    payload: schemas.TutorialCreate, 
    db: Session = Depends(get_db)
):
    """Update a tutorial"""
    tutorial = db.query(Tutorial).get(tutorial_id)
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tutorial, field, value)
    
    db.commit()
    db.refresh(tutorial)
    return tutorial


# ------------------------------------------------------------------ #
#  UPDATE tutorial step
# ------------------------------------------------------------------ #
@router.put("/steps/{step_id}", response_model=schemas.TutorialStep)
def update_tutorial_step(
    step_id: int, 
    payload: schemas.TutorialStepCreate, 
    db: Session = Depends(get_db)
):
    """Update a tutorial step"""
    step = db.query(TutorialStep).get(step_id)
    if not step:
        raise HTTPException(status_code=404, detail="Tutorial step not found")
    
    # Check if we're changing step_number and it conflicts
    if payload.step_number != step.step_number:
        existing_step = db.query(TutorialStep).filter(
            TutorialStep.tutorial_id == step.tutorial_id,
            TutorialStep.step_number == payload.step_number,
            TutorialStep.id != step_id
        ).first()
        
        if existing_step:
            raise HTTPException(
                status_code=400, 
                detail=f"Step {payload.step_number} already exists for this tutorial"
            )
    
    update_data = payload.model_dump(exclude_unset=True)
    # Remove tutorial_id from update data to prevent conflicts
    update_data.pop('tutorial_id', None)
    
    for field, value in update_data.items():
        setattr(step, field, value)
    
    db.commit()
    db.refresh(step)
    return step


# ------------------------------------------------------------------ #
#  DELETE tutorial
# ------------------------------------------------------------------ #
@router.delete("/{tutorial_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tutorial(tutorial_id: int, db: Session = Depends(get_db)):
    """Delete a tutorial and all its steps"""
    tutorial = db.query(Tutorial).get(tutorial_id)
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial not found")
    
    db.delete(tutorial)
    db.commit()


# ------------------------------------------------------------------ #
#  DELETE tutorial step
# ------------------------------------------------------------------ #
@router.delete("/steps/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tutorial_step(step_id: int, db: Session = Depends(get_db)):
    """Delete a tutorial step"""
    step = db.query(TutorialStep).get(step_id)
    if not step:
        raise HTTPException(status_code=404, detail="Tutorial step not found")
    
    db.delete(step)
    db.commit()


# ------------------------------------------------------------------ #
#  TOGGLE tutorial active status
# ------------------------------------------------------------------ #
@router.patch("/{tutorial_id}/toggle-active", response_model=schemas.Tutorial)
def toggle_tutorial_active(tutorial_id: int, db: Session = Depends(get_db)):
    """Toggle the active status of a tutorial"""
    tutorial = db.query(Tutorial).get(tutorial_id)
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial not found")
    
    tutorial.is_active = not tutorial.is_active
    db.commit()
    db.refresh(tutorial)
    return tutorial