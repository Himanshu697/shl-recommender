# SHL Assessment Recommender — Approach Document

## Design Choices

**Architecture: Stateless RAG + LLM Agent**

Each POST /chat call receives the full conversation history. No server-side session storage. The agent follows a Retrieve → Prompt → Validate loop on every turn.

**Retrieval: TF-IDF with bigrams**

The SHL catalog (~400 items) is small enough that TF-IDF over name + description + keys + job_levels + languages outperforms embedding models in latency while remaining highly accurate for keyword-rich hiring queries. The top-20 matches are injected into the system prompt as the agent's only knowledge source — this eliminates hallucinated URLs by construction.

Considered sentence-transformers (semantic embeddings via FAISS) but rejected due to: (a) cold-start load time on free hosting tiers, (b) TF-IDF at this catalog size achieves comparable recall for structured domain queries, (c) no GPU needed.

**LLM: Groq (llama-3.3-70b-versatile)**

Groq's inference speed (~300 tok/s) keeps responses well within the 30-second timeout even with large prompts. The model is prompted to return strict JSON (json_object response format) with the exact schema: `reply`, `recommendations`, `end_of_conversation`.

**Agent Behavior**

Four behaviors are enforced via the system prompt + code-level guardrails:

- *Clarify*: Prompt instructs the model to ask one question on vague input. Vague is defined explicitly (no role, no skill, no level). Code does not gate on this — the LLM handles it with few-shot examples baked into the prompt.
- *Recommend*: Model is given the top-20 retrieved assessments and instructed to select 1–10. All returned URLs are validated against the retrieved set before returning — any hallucinated URL is silently dropped.
- *Refine*: Stateless design means the full history is resent each turn. The model sees all prior recommendations and the new constraint, and updates accordingly. No special code needed.
- *Compare*: Prompt explicitly states "answer comparisons only from catalog data provided". Retrieved items include description, duration, languages, and job levels — sufficient for grounded comparisons.

**Scope Enforcement**

Regex-based pre-filter catches prompt injection patterns, salary/legal keywords, and jailbreak phrases before the LLM is called. System prompt reinforces refusal for off-topic requests.

---

## Retrieval Setup

1. On startup, `catalog.json` is loaded and each item is converted to a document string: `name + description + keys + job_levels + languages`.
2. TF-IDF matrix is built once (cached in memory).
3. Per request, the last 4 user messages are concatenated as the query.
4. Top-20 cosine-similar items are passed to the LLM as the candidate pool.

---

## Prompt Design

System prompt has four sections:
1. Role + strict rules (numbered, unambiguous)
2. Definition of vague vs. sufficient context
3. Output format — exact JSON schema with examples
4. Catalog context (injected top-20 items per request)

Key decisions: temperature=0.2 (deterministic behavior), json_object response format (schema compliance), final-turn system injection to force end_of_conversation=true on turn 7+.

---

## Evaluation Approach

Tested against all 10 public traces by replaying them against the running server:
- Turn 1 vague → confirmed recommendations=[] 
- Turn 1 with JD → confirmed recommendations populated immediately
- Mid-conversation refinement → confirmed shortlist updated, not reset
- Compare question → confirmed catalog-grounded answer, not model prior

**What didn't work initially:**
- LLM occasionally returned recommendations as objects with mismatched keys → fixed by adding a secondary name-fuzzy-match fallback in `_validate_and_clean()`
- Turn cap not enforced → fixed by injecting a final-turn system message at turn 7

**AI tools used:** Claude was used for code scaffolding and prompt iteration. All design decisions and trade-offs (TF-IDF vs. embeddings, stateless architecture, validation logic) were made and are fully understood by the author.

---

## Stack Summary

| Component | Choice | Reason |
|-----------|--------|--------|
| API framework | FastAPI | Assignment requirement |
| LLM | Groq llama-3.3-70b | Free, fast, JSON mode |
| Retrieval | scikit-learn TF-IDF | Low latency, no GPU, good recall at this catalog size |
| Deployment | Render free tier | Cold start <2 min, /health endpoint compatible |
| Catalog | SHL JSON endpoint | Direct, no scraping needed |
