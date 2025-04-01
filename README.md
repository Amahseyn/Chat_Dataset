# Chat with Dataset

A local-only property search system using semantic similarity.

## Features
- Processes all property features (price, beds, amenities, etc.)
- Fast similarity search with FAISS
- No LLM/API dependencies

## Setup
1. Clone repo
2. Install requirements and run code:
```bash
pip install -r requirements.txt

python preprocess.ipynb
python search.ipynb
