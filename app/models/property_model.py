from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
class Property(Base):
    __tablename__ = 'properties'

    id = Column(String, primary_key=True)
    area = Column(Float)
    building_type = Column(String)
    building_nature = Column(String)
    image_url = Column(String)
    num_bath_rooms = Column(Float)
    num_bed_rooms = Column(Float)
    price = Column(Float)
    property_description = Column(Text)
    property_overview = Column(Text)
    property_url = Column(String)
    purpose = Column(String)
    city = Column(String)
    locality = Column(String)
    address = Column(String)
    relaxation_amenity_count = Column(Integer)
    security_amenity_count = Column(Integer)
    maintenance_or_cleaning_amenity_count = Column(Integer)
    social_amenity_count = Column(Integer)
    expendable_amenity_count = Column(Integer)
    service_staff_amenity_count = Column(Integer)
    unclassify_amenity_count = Column(Integer)
    division = Column(String)
    zone = Column(String)


