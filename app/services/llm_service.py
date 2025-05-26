import google.generativeai as genai
from vectorstore.faiss_utils import retrieve_relevant_property_info
from core.config import get_settings

genai.configure(api_key=get_settings().GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def generate_real_estate_response(user_query):
    retrieved_context_list = retrieve_relevant_property_info(user_query)
    context_str = "\n\n".join(retrieved_context_list) if retrieved_context_list else "No specific property information found."

    prompt = f"""You are a helpful AI assistant specializing in real estate.
    Answer the user's question based ONLY on the following property information.
    If the information is not in the provided context, clearly state that the information is not available.
    Do not make up information outside of the provided context.

    Context:
    {context_str}

    User Question: {user_query}

    Answer:"""

    response = model.generate_content(prompt)
    return response.text