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
    for attempt in range(2):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.1,
                max_tokens=1024,  # increased — reasoning models need more tokens
            )

            choice = resp.choices[0].message

            # Gemma 4 is a reasoning model — it puts output in reasoning_content
            # and leaves content empty. We check both.
            raw = ""
            if choice.content and choice.content.strip():
                raw = choice.content.strip()
            elif hasattr(choice, "reasoning_content") and choice.reasoning_content:
                # Extract JSON from inside the reasoning text
                reasoning = choice.reasoning_content
                print(f"\n[LLM REASONING]:\n{reasoning[:500]}\n")
                # Find the last JSON object in the reasoning
                start = reasoning.rfind("{")
                end = reasoning.rfind("}") + 1
                if start != -1 and end > start:
                    raw = reasoning[start:end]

            print(f"\n[LLM RAW OUTPUT]: {raw}\n")

            if not raw:
                raise json.JSONDecodeError("Empty response", "", 0)

            # Strip markdown fences if present
            if "```" in raw:
                parts = raw.split("```")
                for part in parts:
                    part = part.strip()
                    if part.startswith("json"):
                        part = part[4:].strip()
                    if part.startswith("{"):
                        raw = part
                        break

            # Extract JSON if there's text around it
            if not raw.startswith("{"):
                start = raw.find("{")
                end = raw.rfind("}") + 1
                if start != -1 and end > start:
                    raw = raw[start:end]

            return json.loads(raw)

        except json.JSONDecodeError as e:
            print(f"[LLM] JSON parse failed attempt {attempt + 1}: {e}")
            print(f"[LLM] Raw was: '{raw}'")
            if attempt == 1:
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
