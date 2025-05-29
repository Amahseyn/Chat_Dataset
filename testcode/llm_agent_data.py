import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import pandas as pd
from langchain.vectorstores import FAISS # Or Chroma, etc.
import os

# --- Configuration ---
file_path = 'app/data/data.csv' # IMPORTANT: Make sure this path is correct
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") # Ensure this environment variable is set
SAMPLE_SIZE = 3
TOP_K_RESULTS = 3 # Number of relevant documents to retrieve for context
print("Google API Key:", GOOGLE_API_KEY) # For debugging, ensure this is set
# --- Initialize Google Generative AI ---
if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    exit()
genai.configure(api_key=GOOGLE_API_KEY, transport='rest')
# --- LLM Models ---
# Model for embeddings
embeddings_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
# Model for generation and inference
generative_model = genai.GenerativeModel('gemini-1.5-flash')

def load_dataframe(file_path):
    """Loads a DataFrame from CSV, Excel, or JSON based on file extension."""
    ext = os.path.splitext(file_path)[-1].lower()
    try:
        if ext in ['.csv']:
            return pd.read_csv(file_path)
        elif ext in ['.xlsx', '.xls']:
            return pd.read_excel(file_path)
        elif ext in ['.json']:
            return pd.read_json(file_path)
        else:
            print(f"Unsupported file extension: {ext}")
            return None
    except Exception as e:
        print(f"Error loading file '{file_path}': {e}")
        return None

def infer_dataset_domain(df_sample, model):
    """Infers the domain of the dataset using an LLM."""
    if df_sample.empty:
        return "General Data (No data in sample)"

    sample_data_preview = ""
    # Create a string representation of the first few rows for the LLM
    for i, row in df_sample.head(min(3, len(df_sample))).iterrows(): # Show at most 3 rows from the sample
        row_str = ", ".join([f"{col.replace('_', ' ').title()}: {val}" for col, val in row.items() if pd.notna(val) and str(val).strip()])
        if row_str: # Only add if there's actual content
            sample_data_preview += f"Row {i+1}: {row_str}\n"

    if not sample_data_preview:
        sample_data_preview = "Sample rows contain mostly empty values or could not be processed for preview."

    column_names = ", ".join([col.replace('_', ' ').title() for col in df_sample.columns])

    prompt = f"""Analyze the following column names and a sample of the data to determine the primary subject or domain.
Provide a concise label for this domain (e.g., "Real Estate Properties", "E-commerce Product Listings", "Customer Service Interactions", "Book Inventory", "Vehicle Sales Data").

Column Names:
{column_names}

Data Sample Preview:
{sample_data_preview}

Based on this information, the most likely domain of this dataset is: """

    print("\n--- Sending prompt to LLM for domain inference ---")
    print(prompt)
    print("--- End of domain inference prompt ---\n")

    try:
        response = model.generate_content(prompt)
        inferred_domain = response.text.strip()
        # Basic cleaning
        if "is:" in inferred_domain:
            inferred_domain = inferred_domain.split("is:")[-1].strip()
        if inferred_domain.startswith('"') and inferred_domain.endswith('"'):
            inferred_domain = inferred_domain[1:-1]
        if not inferred_domain or len(inferred_domain) > 50: # Basic sanity check
            print(f"Warning: Unusual domain inference result: '{inferred_domain}'. Falling back.")
            return "General Data (inference unclear)"
        return inferred_domain
    except Exception as e:
        print(f"Error during domain inference with LLM: {e}")
        return "General Data (error in inference)" # Fallback

def create_generic_documents_from_sample(df_sample):
    """Creates descriptive text documents from a DataFrame sample."""
    documents = []
    if df_sample.empty:
        print("Warning: The data sample is empty. No documents will be created.")
        return documents

    for index, row in df_sample.iterrows():
        row_description_parts = []
        for col_name, value in row.items():
            if pd.notna(value) and str(value).strip(): # Ensure value is not NaN and not just whitespace
                # Sanitize column name for better readability
                readable_col_name = col_name.replace('_', ' ').lower()
                row_description_parts.append(f"The {readable_col_name} is {value}")
        if row_description_parts:
            documents.append(". ".join(row_description_parts) + ".")
        else:
            documents.append(f"Row {index} contains no displayable data.")
    return documents

def retrieve_relevant_info_from_sample(query, vector_store, k=3):
    """Retrieves relevant documents from the vector store based on the query."""
    if not vector_store:
        print("Error: Vector store not initialized for retrieval.")
        return []
    try:
        # Ensure k is not greater than the number of documents in the store
        num_docs_in_store = vector_store.index.ntotal
        actual_k = min(k, num_docs_in_store)
        if actual_k == 0:
            return []
        relevant_docs = vector_store.similarity_search(query, k=actual_k)
        return [doc.page_content for doc in relevant_docs]
    except Exception as e:
        print(f"Error during similarity search: {e}")
        return []

def generate_dynamic_agent_response(user_query, vector_store, inferred_domain, llm_model, chat_history=None, k=3):
    """Generates a response from the LLM agent based on retrieved context and inferred domain."""
    retrieved_context_list = retrieve_relevant_info_from_sample(user_query, vector_store, k=k)

    if not retrieved_context_list:
        context_str = f"No specific information matching your query was found within the {SAMPLE_SIZE}-row data sample."
    else:
        context_str = "\n\n".join(retrieved_context_list)

    prompt = f"""You are an AI assistant. Your current expertise is in '{inferred_domain}', based on a small data sample provided to you.
    Answer the user's question based ONLY on the following information extracted from the {SAMPLE_SIZE}-row data sample.
    If the information is not in the provided context, clearly state that the information is not available in the loaded data sample.
    Do not make up information or use external knowledge.

    Context from the data sample:
    {context_str}

    User Question: {user_query}

    Answer:"""

    if chat_history:
        # For multi-turn, ensure the model object supports start_chat (genai.GenerativeModel does)
        chat_session = llm_model.start_chat(history=chat_history)
        response = chat_session.send_message(prompt)
        updated_history = chat_session.history
    else: # For single turn or first turn
        response = llm_model.generate_content(prompt)
        updated_history = [
            {'role': 'user', 'parts': [{'text': user_query}]},
            {'role': 'model', 'parts': [{'text': response.text}]}
        ]
    return response.text, updated_history

# --- Main Workflow ---
def main():
    # 1. Load Data (CSV, Excel, or JSON)
    df = load_dataframe(file_path)
    if df is None:
        print(f"Error: Could not load data from '{file_path}'. Please check the file and format.")
        return

    if df.empty:
        print(f"Error: The file '{file_path}' is empty.")
        return

    # 2. Take a small sample
    df_sample = df.head(SAMPLE_SIZE)
    print(f"--- Taken a sample of {len(df_sample)} rows from the CSV. ---")
    if not df_sample.empty:
        print("Sample Data Preview (first row):")
        print(df_sample.iloc[0])
    else:
        print("The sample is empty. Cannot proceed with inference or agent creation.")
        return

    # 3. Infer Data Type/Domain
    inferred_domain = infer_dataset_domain(df_sample, generative_model)
    print(f"\n==> Inferred Dataset Domain: {inferred_domain} <==")

    # 4. Create Generic Documents from the SAMPLE
    print(f"\n--- Creating documents from the {SAMPLE_SIZE}-row sample... ---")
    documents = create_generic_documents_from_sample(df_sample)

    if not documents:
        print("No documents were created from the data sample. Cannot build agent knowledge base.")
        return

    print(f"Successfully created {len(documents)} text documents from the sample.")
    if documents:
        print("\nExample document (from the first row of the sample):")
        print(documents[0])

    # 5. Create Vector Store from these SAMPLE documents
    print("\n--- Creating vector store from sample documents... ---")
    try:
        vector_store = FAISS.from_texts(texts=documents, embedding=embeddings_model)
        print("Vector store created successfully from the sample data.")
    except Exception as e:
        print(f"Error creating vector store: {e}")
        return

    # 6. Interact with the Dynamic Agent
    print("\n--- Dynamic LLM Agent Ready ---")
    print(f"The agent is now configured to answer questions about '{inferred_domain}' based on the {SAMPLE_SIZE}-row sample.")

    # Example Usage:
    # Adjust the question to be more generic or relevant to what might be in a typical CSV
    # (or what you know is in your specific 'data.csv' for testing)
    user_question = f"What can you tell me about the items in this {inferred_domain} sample?"
    if inferred_domain.lower().startswith("real estate"):
        user_question = "Are there any properties with more than 2 bedrooms in the sample?"
    elif "product" in inferred_domain.lower():
        user_question = "What are some of the product names or types in the sample?"


    print(f"\nUser Question: {user_question}")
    answer, current_history = generate_dynamic_agent_response(user_question, vector_store, inferred_domain, generative_model, k=TOP_K_RESULTS)
    print(f"AI Agent: {answer}")

    # Example follow-up (optional)
    # if "not available" not in answer.lower() and "no specific information" not in answer.lower():
    #     user_question_2 = "Tell me more about the first item mentioned."
    #     print(f"\nUser Question: {user_question_2}")
    #     answer_2, current_history = generate_dynamic_agent_response(user_question_2, vector_store, inferred_domain, generative_model, chat_history=current_history, k=TOP_K_RESULTS)
    #     print(f"AI Agent: {answer_2}")

if __name__ == '__main__':
    main()