"""
Run all 10 sample conversation traces locally to check agent behavior.
Usage:
    python tests/test_traces.py
Make sure server is running first:
    uvicorn app.main:app --reload
"""
import requests
import json

BASE_URL = "http://localhost:8000"

traces = [
    {
        "name": "C1 - Senior Leadership (CXO)",
        "turns": [
            "We need a solution for senior leadership.",
            "The pool consists of CXOs, director-level positions; people with more than 15 years of experience.",
            "Selection — comparing candidates against a leadership benchmark.",
            "Perfect, that's what we need.",
        ],
    },
    {
        "name": "C2 - Senior Rust Engineer",
        "turns": [
            "I'm hiring a senior Rust engineer for high-performance networking infrastructure. What assessments should I use?",
            "Yes, go ahead. Should I also add a cognitive test for this level?",
            "That works. Thanks.",
        ],
    },
    {
        "name": "C3 - Contact Centre Agents",
        "turns": [
            "We're screening 500 entry-level contact centre agents. Inbound calls, customer service focus. What should we use?",
            "English.",
            "Yes, include that.",
            "Looks good.",
        ],
    },
    {
        "name": "C4 - Graduate Financial Analysts",
        "turns": [
            "Hiring graduate financial analysts — final-year students, no work experience. We need numerical reasoning and a finance knowledge test.",
            "Yes that covers it.",
        ],
    },
    {
        "name": "C5 - Sales Organization Reskilling",
        "turns": [
            "As part of our restructuring and annual talent audit, we need to re-skill our Sales organization. What solutions do you recommend?",
            "Include first-line managers too.",
            "That looks complete.",
        ],
    },
    {
        "name": "C6 - Chemical Plant Operators (Safety Critical)",
        "turns": [
            "We're hiring plant operators for a chemical facility. Safety is absolute top priority — reliability, procedure compliance, never cutting corners. What do you recommend?",
            "Yes, add a cognitive screen too.",
            "That's good.",
        ],
    },
    {
        "name": "C7 - Bilingual Healthcare Admin (Spanish)",
        "turns": [
            "We're hiring bilingual healthcare admin staff in South Texas — they handle patient records and need to be assessed in Spanish. HIPAA compliance is critical. What assessments work?",
            "Go with option (a), the hybrid approach.",
            "Okay that works.",
        ],
    },
    {
        "name": "C8 - Admin Assistants Excel and Word",
        "turns": [
            "I need to quickly screen admin assistants for Excel and Word daily.",
            "Skip the personality test, just knowledge.",
            "Good.",
        ],
    },
    {
        "name": "C9 - Senior Full-Stack Engineer JD",
        "turns": [
            'Here\'s the JD for an engineer we need to fill. "Senior Full-Stack Engineer — 5+ years across Core Java, Spring, REST API design, Angular, SQL/relational databases, AWS deployment, and Docker."',
            "Backend-leaning. Java and SQL are the priority.",
            "Add Angular as well.",
            "That looks right.",
        ],
    },
    {
        "name": "C10 - Graduate Management Trainee Battery",
        "turns": [
            "We run a graduate management trainee scheme. We need a full battery — cognitive, personality, and situational judgement. All recent graduates.",
            "Yes, include all three.",
            "Perfect.",
        ],
    },
]


def run_trace(trace):
    print(f"\n{'='*60}")
    print(f"TRACE: {trace['name']}")
    print("="*60)

    messages = []
    for i, user_turn in enumerate(trace["turns"]):
        messages.append({"role": "user", "content": user_turn})
        print(f"\n[Turn {i+1}] USER: {user_turn[:100]}")

        resp = requests.post(f"{BASE_URL}/chat", json={"messages": messages}, timeout=35)
        if resp.status_code != 200:
            print(f"ERROR {resp.status_code}: {resp.text}")
            break

        data = resp.json()
        reply = data.get("reply", "")
        recs = data.get("recommendations", [])
        eoc = data.get("end_of_conversation", False)

        print(f"AGENT: {reply[:200]}")
        if recs:
            print(f"RECOMMENDATIONS ({len(recs)}):")
            for r in recs:
                print(f"  - {r['name']} [{r['test_type']}] {r['url']}")
        print(f"end_of_conversation: {eoc}")

        messages.append({"role": "assistant", "content": reply})

        if eoc:
            print(">> Conversation ended by agent")
            break

    print(f"\nFinal recommendation count: {len(recs) if 'recs' in dir() else 0}")


def main():
    print("Testing /health...")
    r = requests.get(f"{BASE_URL}/health")
    assert r.json() == {"status": "ok"}, f"Health check failed: {r.text}"
    print("Health OK\n")

    for trace in traces:
        try:
            run_trace(trace)
        except Exception as e:
            print(f"ERROR in {trace['name']}: {e}")


if __name__ == "__main__":
    main()
