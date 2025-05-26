from sqlalchemy.orm import Session
from models.property_model import Property

def get_all_properties(db: Session):
    return db.query(Property).all()

def get_property_by_id(db: Session, prop_id: str):
    return db.query(Property).filter(Property.id == prop_id).first()

def create_property(db: Session, property_data):
    db_property = Property(**property_data.dict())
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    return db_property

def update_property(db: Session, prop_id: str, property_data):
    db_property = get_property_by_id(db, prop_id)
    if not db_property:
        return None
    for key, value in property_data.dict().items():
        setattr(db_property, key, value)
    db.commit()
    db.refresh(db_property)
    return db_property

def delete_property(db: Session, prop_id: str):
    db_property = get_property_by_id(db, prop_id)
    if not db_property:
        return None
    db.delete(db_property)
    db.commit()
    return {"message": "Property deleted"}