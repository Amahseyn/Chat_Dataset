import google.generativeai as genai
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import pandas as pd
print(os.getenv("GOOGLE_API_KEY"))
genai.configure(api_key=os.getenv("GOOGLE_API_KEY")) # Make sure your API key is set


# Load your CSV
try:
    df = pd.read_csv('data.csv')
except FileNotFoundError:
    print("Error: 'your_real_estate_dataset.csv' not found. Make sure the file path is correct.")
    exit()
except Exception as e:
    print(f"Error loading CSV: {e}")
    exit()


# Select the first 100 rows
df_subset = df.head(100)

# Convert each row into a descriptive text string
documents = []
for index, row in df_subset.iterrows():
    # Start building the description
    desc_parts = []

    # Basic Information
    if pd.notna(row.get('building_type')) and pd.notna(row.get('area')):
        desc_parts.append(f"This is a {row.get('building_type')} with an area of {row.get('area')} square feet.")
    elif pd.notna(row.get('building_type')):
        desc_parts.append(f"This is a {row.get('building_type')}.")
    elif pd.notna(row.get('area')):
        desc_parts.append(f"This property has an area of {row.get('area')} square feet.")

    if pd.notna(row.get('property_description')):
        desc_parts.append(f"Description: {row.get('property_description')}")
    elif pd.notna(row.get('property_overview')): # Fallback to overview if description is missing
        desc_parts.append(f"Overview: {row.get('property_overview')}")

    # Location
    location_parts = []
    if pd.notna(row.get('address')) and str(row.get('address')).strip(): # Check if address is not NaN and not just whitespace
        location_parts.append(f"Address: {row.get('address')}")
    if pd.notna(row.get('locality')):
        location_parts.append(f"located in {row.get('locality')}")
    if pd.notna(row.get('city')):
        location_parts.append(f"{row.get('city')}")
    if pd.notna(row.get('division')):
        location_parts.append(f"{row.get('division')}")
    if location_parts:
        desc_parts.append(", ".join(filter(None, location_parts)) + ".")


    # Rooms and Price
    if pd.notna(row.get('num_bed_rooms')):
        desc_parts.append(f"It has {int(row.get('num_bed_rooms', 0))} bedroom(s).") # Convert to int for cleaner text
    if pd.notna(row.get('num_bath_rooms')):
        desc_parts.append(f"and {int(row.get('num_bath_rooms', 0))} bathroom(s).") # Convert to int

    if pd.notna(row.get('price')) and pd.notna(row.get('purpose')):
        desc_parts.append(f"The property is for {row.get('purpose')} at a price of {row.get('price')}.") # Assuming price is in local currency
    elif pd.notna(row.get('price')):
        desc_parts.append(f"The price is {row.get('price')}.")
    elif pd.notna(row.get('purpose')):
        desc_parts.append(f"The purpose is {row.get('purpose')}.")


    # Amenities (count only if > 0)
    amenities = []
    if pd.notna(row.get('relaxation_amenity_count')) and row.get('relaxation_amenity_count') > 0:
        amenities.append(f"{int(row.get('relaxation_amenity_count'))} relaxation amenities")
    if pd.notna(row.get('security_amenity_count')) and row.get('security_amenity_count') > 0:
        amenities.append(f"{int(row.get('security_amenity_count'))} security amenities")
    if pd.notna(row.get('maintenance_or_cleaning_amenity_count')) and row.get('maintenance_or_cleaning_amenity_count') > 0:
        amenities.append(f"{int(row.get('maintenance_or_cleaning_amenity_count'))} maintenance/cleaning amenities")
    if pd.notna(row.get('social_amenity_count')) and row.get('social_amenity_count') > 0:
        amenities.append(f"{int(row.get('social_amenity_count'))} social amenities")
    # Add other amenity counts as needed

    if amenities:
        desc_parts.append(f"It includes: {', '.join(amenities)}.")

    # You might not need to include URLs or IDs in the text for chat,
    # unless you specifically want to retrieve them. The property_url could be useful metadata though.
    # For this example, we'll keep it focused on descriptive text.
    # You could also add:
    # if pd.notna(row.get('id')):
    #     desc_parts.append(f"Property ID: {row.get('id')}")

    # Join all parts into a single string
    doc_text = " ".join(desc_parts)
    documents.append(doc_text)

# 'documents' now contains a list of detailed strings.
# print(f"Created {len(documents)} text documents from the CSV.")
# if documents:
#     print("\nExample document from your first row:")
#     print(documents[0])
# else:
#     print("No documents created.")



embeddings_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001",google_api_key=os.getenv("GOOGLE_API_KEY"))

from langchain.vectorstores import FAISS # Or Chroma, etc.

if not documents:
    print("No documents were created from the CSV. Cannot proceed with embedding.")
    exit()

vector_store = FAISS.from_texts(texts=documents, embedding=embeddings_model)
print("Vector store created successfully.")

def retrieve_relevant_property_info(query, vector_store, k=3): # Retrieve top 3 relevant rows
    relevant_docs = vector_store.similarity_search(query, k=k)
    return [doc.page_content for doc in relevant_docs]

model = genai.GenerativeModel('gemini-1.5-flash') # Or gemini-1.5-flash, gemini-1.5-pro for more advanced features


def generate_real_estate_response(user_query, chat_history=None):
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

    # For multi-turn chat, use model.start_chat()
    if chat_history:
        chat_session = model.start_chat(history=chat_history)
        response = chat_session.send_message(prompt)
        updated_history = chat_session.history
    else: # For single turn or first turn
        response = model.generate_content(prompt)
        # Manually construct history for the first turn if you plan to continue the chat
        updated_history = [
            {'role': 'user', 'parts': [{'text': user_query}]},
            {'role': 'model', 'parts': [{'text': response.text}]}
        ]

    return response.text, updated_history

# Example Usage:
# Ensure API key and vector_store are configured before this.
# Make sure 'documents' was populated and vector_store was created.
if 'vector_store' in globals() and vector_store:
    user_question = "Are there any properties with 3 bedrooms?"
    # user_question = "Tell me about the property at [some address from your first 100 rows]"
    answer, current_history = generate_real_estate_response(user_question)
    print(f"User: {user_question}")
    print(f"AI: {answer}")

    # Example follow-up
    # user_question_2 = "What's the price of the first one you mentioned?"
    # answer_2, current_history = generate_real_estate_response(user_question_2, current_history)
    # print(f"User: {user_question_2}")
    # print(f"AI: {answer_2}")
else:
    print("Vector store not initialized. Please check previous steps.")
