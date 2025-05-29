import pandas as pd
from sentence_transformers import SentenceTransformer
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from transformers import BitsAndBytesConfig

import os


try:
    df = pd.read_csv('app/data/data.csv')
except FileNotFoundError:
    print("Error: 'data.csv' not found. Make sure the file path is correct.")
    exit()
except Exception as e:
    print(f"Error loading CSV: {e}")
    exit()

# Take first 100 rows
df_subset = df.head(1000)

# Convert each row into descriptive text
documents = []
for index, row in df_subset.iterrows():
    desc_parts = []

    # Basic info
    if pd.notna(row.get('building_type')) and pd.notna(row.get('area')):
        desc_parts.append(f"This is a {row.get('building_type')} with an area of {row.get('area')} square feet.")
    elif pd.notna(row.get('building_type')):
        desc_parts.append(f"This is a {row.get('building_type')}.")
    elif pd.notna(row.get('area')):
        desc_parts.append(f"This property has an area of {row.get('area')} square feet.")

    # Description / Overview
    if pd.notna(row.get('property_description')):
        desc_parts.append(f"Description: {row.get('property_description')}")
    elif pd.notna(row.get('property_overview')):
        desc_parts.append(f"Overview: {row.get('property_overview')}")

    # Location
    location_parts = []
    if pd.notna(row.get('address')):
        location_parts.append(f"Address: {row.get('address')}")
    if pd.notna(row.get('locality')):
        location_parts.append(f"located in {row.get('locality')}")
    if pd.notna(row.get('city')):
        location_parts.append(f"{row.get('city')}")
    if pd.notna(row.get('division')):
        location_parts.append(f"{row.get('division')}")
    if location_parts:
        desc_parts.append(", ".join(location_parts) + ".")

    # Rooms and Price
    if pd.notna(row.get('num_bed_rooms')):
        desc_parts.append(f"It has {int(row.get('num_bed_rooms', 0))} bedroom(s).")
    if pd.notna(row.get('num_bath_rooms')):
        desc_parts.append(f"and {int(row.get('num_bath_rooms', 0))} bathroom(s).")

    if pd.notna(row.get('price')) and pd.notna(row.get('purpose')):
        desc_parts.append(f"The property is for {row.get('purpose')} at a price of {row.get('price')}.")
    elif pd.notna(row.get('price')):
        desc_parts.append(f"The price is {row.get('price')}.")
    elif pd.notna(row.get('purpose')):
        desc_parts.append(f"The purpose is {row.get('purpose')}.")

    # Amenities
    amenities = []
    if pd.notna(row.get('relaxation_amenity_count')) and row.get('relaxation_amenity_count') > 0:
        amenities.append(f"{int(row.get('relaxation_amenity_count'))} relaxation amenities")
    if pd.notna(row.get('security_amenity_count')) and row.get('security_amenity_count') > 0:
        amenities.append(f"{int(row.get('security_amenity_count'))} security amenities")
    if pd.notna(row.get('maintenance_or_cleaning_amenity_count')) and row.get('maintenance_or_cleaning_amenity_count') > 0:
        amenities.append(f"{int(row.get('maintenance_or_cleaning_amenity_count'))} maintenance/cleaning amenities")
    if pd.notna(row.get('social_amenity_count')) and row.get('social_amenity_count') > 0:
        amenities.append(f"{int(row.get('social_amenity_count'))} social amenities")

    if amenities:
        desc_parts.append(f"It includes: {', '.join(amenities)}.")

    doc_text = " ".join(desc_parts)
    documents.append(doc_text)


embedding_model = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"}
)

if not documents:
    print("No documents were created from the CSV. Cannot proceed with embedding.")
    exit()

vector_store = FAISS.from_texts(texts=documents, embedding=embedding_model)
print("Vector store created successfully.")

def retrieve_relevant_property_info(query, vector_store, k=3):
    relevant_docs = vector_store.similarity_search(query, k=k)
    return [doc.page_content for doc in relevant_docs]

model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
device = "cuda" if torch.cuda.is_available() else "cpu"
tokenizer = AutoTokenizer.from_pretrained(model_name)
try:
    if device == "cuda":
        bnb_config = BitsAndBytesConfig(load_in_8bit=False, load_in_4bit=False)

        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            quantization_config=bnb_config
        )
        print("Running on GPU — loading with 8-bit quantization")
    else:
        print("Running on CPU — loading without 8-bit quantization")
        model = AutoModelForCausalLM.from_pretrained(model_name).to("cpu")
except Exception as e:
    print(f"Error loading model: {e}")
    print("Falling back to CPU mode without 8-bit.")
    model = AutoModelForCausalLM.from_pretrained(model_name).to("cpu")
def generate_prompt(user_input):
    return f"<|system|>\nYou are a helpful AI assistant specialized in real estate.\n<|user|>\n{user_input}\n<|assistant|>\n"

def tinyllama_generate(prompt, max_new_tokens=150):
    full_prompt = generate_prompt(prompt)
    inputs = tokenizer(full_prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs,
                             max_new_tokens=max_new_tokens,
                             eos_token_id=tokenizer.eos_token_id,
                             pad_token_id=tokenizer.pad_token_id)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response.split("<|assistant|>")[-1].strip()

# -------------------------
# 4. Query Handling Function
# -------------------------

def generate_real_estate_response(user_query):
    retrieved_context_list = retrieve_relevant_property_info(user_query, vector_store)
    if not retrieved_context_list:
        context_str = "No specific property information found in the first 100 rows for this query."
    else:
        context_str = "\n\n".join(retrieved_context_list)

    prompt = f"""You are a helpful AI assistant specializing in real estate from a provided dataset.
    Answer the user's question based ONLY on the following property information from the first 100 rows of the dataset.
    If the information is not in the provided context, clearly state that the information is not available in the loaded data.
    Do not make up information outside of the provided context.

    Context:
    {context_str}

    User Question: {user_query}

    Answer:"""

    response = tinyllama_generate(prompt)
    return response

# -------------------
# 5. Example Usage
# -------------------

if __name__ == "__main__":
    user_question = "Are there any properties with 3 bedrooms?"
    answer = generate_real_estate_response(user_question)
    print(f"User: {user_question}")
    print(f"AI: {answer}")

    # Uncomment for follow-up example
    # user_question_2 = "What's the price of the first one you mentioned?"
    # answer_2 = generate_real_estate_response(user_question_2)
    # print(f"User: {user_question_2}")
    # print(f"AI: {answer_2}")