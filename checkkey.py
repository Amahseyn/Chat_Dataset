import google.generativeai as genai
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import pandas as pd
print(os.getenv("GOOGLE_API_KEY"))
genai.configure(api_key=os.getenv("GOOGLE_API_KEY")) # Make sure your API key is set

