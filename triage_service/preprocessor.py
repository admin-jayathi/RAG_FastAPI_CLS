def preprocess(failure: dict) -> dict:
    """
    Cleans and truncates raw failure data before sending to LLM.
    Keeps token budget under 4K for the 8B model.
    No category logic here — the AI decides everything.
    """

    # --- Stack trace: keep top 20 lines, remove duplicate frames ---
    stack = failure.get("stack_trace", "")
    lines = stack.splitlines()[:20]

    seen = set()
    deduped = []
    for line in lines:
        stripped = line.strip()
        if stripped not in seen:
            seen.add(stripped)
            deduped.append(line)

    failure["stack_trace"] = "\n".join(deduped)

    # --- Logs: keep last 2000 characters only ---
    logs = failure.get("logs_tail", "")
    failure["logs_tail"] = logs[-2000:] if len(logs) > 2000 else logs

    # --- Exception message: cap at 500 chars ---
    msg = failure.get("exception_message", "")
    failure["exception_message"] = msg[:500]

    return failure
