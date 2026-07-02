import json
import re
from groq import Groq
from app.config import GROQ_API_KEY, GROQ_MODEL, MAX_TURNS, MAX_RECOMMENDATIONS
from app.retrieval import search, get_all
from app.prompts import build_system_prompt
from app.schemas import ChatResponse, Recommendation, Message

client = Groq(api_key=GROQ_API_KEY)

OFF_TOPIC_PATTERNS = [
    r"\bsalar[y|ies]\b", r"\blegal\b", r"\blawsuit\b", r"\bdiscrimination\b",
    r"\bignore (previous|above|all)\b", r"\bforget (your|all)\b",
    r"\bact as\b", r"\bpretend (you are|to be)\b", r"\byou are now\b",
    r"\bjailbreak\b", r"\bDAN\b",
]

REFUSAL_REPLY = {
    "reply": "I can only help with SHL assessment recommendations. Could you share the role you are hiring for?",
    "recommendations": [],
    "end_of_conversation": False,
}


def _is_off_topic(text: str) -> bool:
    t = text.lower()
    for pattern in OFF_TOPIC_PATTERNS:
        if re.search(pattern, t):
            return True
    return False


def _build_query_from_history(messages: list) -> str:
    user_msgs = [m.content for m in messages if m.role == "user"]
    return " ".join(user_msgs[-4:])


def _count_turns(messages: list) -> int:
    return len(messages)


def _parse_llm_response(raw: str) -> dict:
    raw = raw.strip()
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    return {
        "reply": raw[:500] if raw else "I couldn't process that. Please try again.",
        "recommendations": [],
        "end_of_conversation": False,
    }


def _validate_and_clean(parsed: dict, catalog_items: list) -> dict:
    valid_urls = {item["url"] for item in catalog_items}
    url_to_item = {item["url"]: item for item in catalog_items}

    raw_recs = parsed.get("recommendations", [])
    if not isinstance(raw_recs, list):
        raw_recs = []

    clean_recs = []
    for rec in raw_recs:
        if not isinstance(rec, dict):
            continue
        url = rec.get("url", "")
        if url in valid_urls:
            catalog_item = url_to_item[url]
            clean_recs.append({
                "name": catalog_item["name"],
                "url": catalog_item["url"],
                "test_type": catalog_item["test_type"],
            })
        else:
            name = rec.get("name", "")
            for item in catalog_items:
                if name.lower() in item["name"].lower() or item["name"].lower() in name.lower():
                    if item["url"] not in [r["url"] for r in clean_recs]:
                        clean_recs.append({
                            "name": item["name"],
                            "url": item["url"],
                            "test_type": item["test_type"],
                        })
                    break

    clean_recs = clean_recs[:MAX_RECOMMENDATIONS]

    return {
        "reply": parsed.get("reply", ""),
        "recommendations": clean_recs,
        "end_of_conversation": bool(parsed.get("end_of_conversation", False)),
    }


def handle_chat(messages: list) -> ChatResponse:
    last_user_msg = ""
    for m in reversed(messages):
        if m.role == "user":
            last_user_msg = m.content
            break

    if _is_off_topic(last_user_msg):
        return ChatResponse(**REFUSAL_REPLY)

    turn_count = _count_turns(messages)
    query = _build_query_from_history(messages)

    if len(query.strip()) < 5:
        return ChatResponse(
            reply="Could you tell me more about the role you are hiring for?",
            recommendations=[],
            end_of_conversation=False,
        )

    catalog_items = search(query)
    if not catalog_items:
        catalog_items = get_all()[:15]

    system_prompt = build_system_prompt(catalog_items)

    groq_messages = [{"role": "system", "content": system_prompt}]
    for m in messages:
        if m.role in ("user", "assistant"):
            groq_messages.append({"role": m.role, "content": m.content})

    if turn_count >= MAX_TURNS - 1:
        groq_messages.append({
            "role": "system",
            "content": "IMPORTANT: This is the final turn. You MUST provide your best shortlist now and set end_of_conversation to true."
        })

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=groq_messages,
            temperature=0.2,
            max_tokens=1500,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
    except Exception as e:
        return ChatResponse(
            reply=f"Service temporarily unavailable. Please try again.",
            recommendations=[],
            end_of_conversation=False,
        )

    parsed = _parse_llm_response(raw)
    cleaned = _validate_and_clean(parsed, catalog_items)

    return ChatResponse(
        reply=cleaned["reply"],
        recommendations=[Recommendation(**r) for r in cleaned["recommendations"]],
        end_of_conversation=cleaned["end_of_conversation"],
    )
