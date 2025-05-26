import os 
import pandas as pd
from langchain_community.vectorstores import FAISS
from vectorstore.embeddings import get_embeddings
from database.session import SessionLocal
from models.property_model import Property
from core.config import get_settings

def retrieve_relevant_property_info(query, vector_store, k=3): # Retrieve top 3 relevant rows
    vector_store = FAISS.load_local(get_settings().VECTOR_STORE_PATH, get_embeddings(),allow_downcast=True)
    results = vector_store.similarity_search(query, k=k)
    return [doc.page_content for doc in results]

def generate_documents_from_db():
    
    db = SessionLocal()
    properties = db.query(Property).all()
    
    documents = []
    for prop in properties:
        desc_parts = []
        if prop.building_type and prop.area:
            desc_parts.append(f"This is a {prop.building_type} with an area of {prop.area} square feet.")
        if prop.property_description:
            desc_parts.append(f"Description: {prop.property_description}")
        elif prop.property_overview:
            desc_parts.append(f"Overview: {prop.property_overview}")
        if prop.address:
            desc_parts.append(f"Address: {prop.address}")
        if prop.locality:
            desc_parts.append(f"located in {prop.locality}")
        if prop.city:
            desc_parts.append(prop.city)
        if prop.num_bed_rooms:
            desc_parts.append(f"It has {int(prop.num_bed_rooms)} bedroom(s).")
        if prop.num_bath_rooms:
            desc_parts.append(f"and {int(prop.num_bath_rooms)} bathroom(s).")
        if prop.price and prop.purpose:
            desc_parts.append(f"The property is for {prop.purpose} at a price of {prop.price}.")
        elif prop.price:
            desc_parts.append(f"The price is {prop.price}.")
        elif prop.purpose:
            desc_parts.append(f"The purpose is {prop.purpose}.")

        amenities = []
        if prop.relaxation_amenity_count > 0:
            amenities.append(f"{prop.relaxation_amenity_count} relaxation amenities")
        if prop.security_amenity_count > 0:
            amenities.append(f"{prop.security_amenity_count} security amenities")
        if prop.maintenance_or_cleaning_amenity_count > 0:
            amenities.append(f"{prop.maintenance_or_cleaning_amenity_count} maintenance/cleaning amenities")

        if amenities:
            desc_parts.append(f"It includes: {', '.join(amenities)}.")

        doc_text = " ".join(desc_parts)
        documents.append(doc_text)

    return documents

def build_vectorstore(force_rebuild=False):
    settings = get_settings()
    vectorstore_dir = settings.VECTORSTORE_DIR

    if not force_rebuild and os.path.exists(vectorstore_dir):
        return FAISS.load_local(vectorstore_dir, get_embeddings(), allow_dangerous_deserialization=True)

    documents = generate_documents_from_db()
    vectorstore = FAISS.from_texts(texts=documents, embedding=get_embeddings())
    vectorstore.save_local(vectorstore_dir)
    return vectorstore