import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
CATALOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "catalog.json")
MAX_TURNS = 8
TOP_K_RETRIEVAL = 20
MAX_RECOMMENDATIONS = 10
