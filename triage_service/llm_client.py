import json
import os
import hashlib
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:1234/v1"),
    api_key="not-needed"
)

MODEL = os.getenv("LLM_MODEL", "local-model")


def load_prompt(failure: dict) -> list:
    """
    Loads the prompt template and fills in failure details.
    We use manual string replacement instead of .format()
    because the prompt contains JSON examples with {curly braces}
    that would confuse Python's format() method.
    """
    prompt_path = os.path.join(
        os.path.dirname(__file__), "prompts", "v1.txt"
    )

    with open(prompt_path, "r") as f:
        template = f.read()

    # Replace only our actual placeholders manually
    # This avoids .format() choking on the JSON schema curly braces
    user_content = template \
        .replace("{test_name}",        str(failure.get("test_name", "unknown"))) \
        .replace("{suite}",            str(failure.get("suite", "unknown"))) \
        .replace("{history}",          str(failure.get("history", []))) \
        .replace("{exception_type}",   str(failure.get("exception_type", ""))) \
        .replace("{exception_message}",str(failure.get("exception_message", ""))[:500]) \
        .replace("{stack_trace}",      str(failure.get("stack_trace", ""))[:2000]) \
        .replace("{logs_tail}",        str(failure.get("logs_tail", ""))[:1000])

    return [
        {
            "role": "system",
            "content": "You are a QA triage assistant. Output only valid JSON. No markdown. No explanation."
        },
        {
            "role": "user",
            "content": user_content
        }
    ]

def call_llm(messages: list) -> dict:
    """
    Calls the local LLM and parses its JSON response.
    Retries once if JSON parsing fails.
    """
    for attempt in range(2):  # try twice before giving up
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.1,    # low = deterministic classification
                max_tokens=512,
            )

            raw = resp.choices[0].message.content.strip()

            # Strip markdown fences if the model wraps output anyway
            if raw.startswith("```"):
                parts = raw.split("```")
                raw = parts[1] if len(parts) > 1 else raw
                if raw.startswith("json"):
                    raw = raw[4:].strip()

            return json.loads(raw)

        except json.JSONDecodeError:
            if attempt == 1:
                # Both attempts failed — return a safe fallback
                return {
                    "category": "UNKNOWN",
                    "confidence": 0.0,
                    "root_cause_summary": "LLM returned unparseable output",
                    "evidence": [],
                    "suggested_owner": "qa-lead",
                    "suggested_fix": "Check LLM service and prompt",
                    "is_real_bug": False,
                    "rerun_recommended": False,
                    "parse_error": True
                }
            # First attempt failed — retry
            continue


def triage(failure: dict) -> dict:
    """
    Main entry point.
    Sends failure to LLM, gets back AI decision, adds signature hash.
    The AI output fields (is_real_bug, rerun_recommended, suggested_owner)
    drive all downstream actions — no category checks anywhere else.
    """
    messages = load_prompt(failure)
    result = call_llm(messages)

    # If AI is not confident, force UNKNOWN
    # (AI should do this itself per prompt rules, but we enforce it here too)
    if result.get("confidence", 1.0) < 0.7:
        result["category"] = "UNKNOWN"

    # Add a unique signature hash for deduplication (used in Phase 3 for Jira)
    result["signature"] = hashlib.sha1(
        (
            failure.get("test_name", "") +
            failure.get("exception_message", "")
        ).encode()
    ).hexdigest()

    # Tag whether this was escalated (Phase 4 adds 70B escalation here)
    result["escalated"] = False

    return result
