from database.session import SessionLocal, init_db
from models.property_model import Property

def insert_sample_property():
    db = SessionLocal()

    sample_property = Property(
        id="bproperty-0",
        area=1185.0,
        building_type="Apartment",
        building_nature="Residential",
        image_url="https://images-cdn.bproperty.com/thumbnails/1579849-800x600.jpeg ",
        num_bath_rooms=0.0,
        num_bed_rooms=3.0,
        price=6100000.0,
        property_description="Grab This 1185 Sq Ft Beautiful Flat Is Vacant For Sale In Khilgaon",
        property_overview="This flat consists of facilities you can think of for a proper living standards...",
        property_url="https://www.bproperty.com/en/property/details-5567061.html ",
        purpose="Sale",
        city="Dhaka",
        locality="Khilgaon",
        address="",
        relaxation_amenity_count=0,
        security_amenity_count=1,
        maintenance_or_cleaning_amenity_count=2,
        social_amenity_count=0,
        expendable_amenity_count=2,
        service_staff_amenity_count=0,
        unclassify_amenity_count=3,
        division="Dhaka",
        zone="Khilgaon"
    )

    db.add(sample_property)
    db.commit()
    db.refresh(sample_property)
    print("✅ Sample property inserted successfully!")

if __name__ == "__main__":
    init_db()
    insert_sample_property()