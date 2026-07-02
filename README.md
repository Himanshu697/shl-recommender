# SHL Assessment Recommender

A conversational AI agent that helps hiring managers find the right SHL assessments through dialogue.

## Features
- Clarifies vague queries before recommending
- Recommends 1–10 assessments from the SHL catalog
- Refines shortlist when constraints change mid-conversation
- Compares assessments using catalog data only
- Refuses off-topic requests and prompt injection attempts

## API

### GET /health
```json
{"status": "ok"}
```

### POST /chat
**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "I need to hire a Java developer"}
  ]
}
```

**Response:**
```json
{
  "reply": "What seniority level are you targeting?",
  "recommendations": [],
  "end_of_conversation": false
}
```

## Tech Stack
- **Framework:** FastAPI (Python)
- **LLM:** Groq (llama-3.3-70b-versatile)
- **Retrieval:** TF-IDF via scikit-learn
- **Catalog:** SHL Individual Test Solutions (377 assessments)

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python fetch_catalog.py
```

Add `.env` file:
