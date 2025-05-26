from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.session import get_db
from schemas.property_schema import PropertyCreate, Property
from services.property_service import get_all_properties, get_property_by_id, create_property, update_property, delete_property

router = APIRouter()

@router.get("/properties", response_model=list[Property])
def read_properties(db: Session = Depends(get_db)):
    return get_all_properties(db)

@router.get("/properties/{prop_id}", response_model=Property)
def read_property(prop_id: str, db: Session = Depends(get_db)):
    prop = get_property_by_id(db, prop_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop

@router.post("/properties", response_model=Property)
def create_new_property(property: PropertyCreate, db: Session = Depends(get_db)):
    return create_property(db, property)

@router.put("/properties/{prop_id}", response_model=Property)
def update_existing_property(prop_id: str, property: PropertyCreate, db: Session = Depends(get_db)):
    updated = update_property(db, prop_id, property)
    if not updated:
        raise HTTPException(status_code=404, detail="Property not found")
    return updated

@router.delete("/properties/{prop_id}")
def delete_existing_property(prop_id: str, db: Session = Depends(get_db)):
    result = delete_property(db, prop_id)
    if not result:
        raise HTTPException(status_code=404, detail="Property not found")
    return result