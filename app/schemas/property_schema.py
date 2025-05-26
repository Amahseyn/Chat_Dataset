from pydantic import BaseModel
from typing import Optional

class PropertyBase(BaseModel):
    id: str
    area: Optional[float]
    building_type: Optional[str]
    building_nature: Optional[str]
    image_url: Optional[str]
    num_bath_rooms: Optional[float]
    num_bed_rooms: Optional[float]
    price: Optional[float]
    property_description: Optional[str]
    property_overview: Optional[str]
    property_url: Optional[str]
    purpose: Optional[str]
    city: Optional[str]
    locality: Optional[str]
    address: Optional[str]
    relaxation_amenity_count: Optional[int]
    security_amenity_count: Optional[int]
    maintenance_or_cleaning_amenity_count: Optional[int]
    social_amenity_count: Optional[int]
    expendable_amenity_count: Optional[int]
    service_staff_amenity_count: Optional[int]
    unclassify_amenity_count: Optional[int]
    division: Optional[str]
    zone: Optional[str]

class PropertyCreate(PropertyBase):
    pass

class Property(PropertyBase):
    class Config:
        from_attributes = True