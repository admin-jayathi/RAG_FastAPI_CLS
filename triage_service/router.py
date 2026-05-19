from notifier import notify_slack


def route(failure: dict, result: dict):
    """
    Routes the triage result to the right action.

    IMPORTANT — there is NO category logic here.
    We never check 'if category == X'.
    The AI already decided everything via its output fields:
      - suggested_owner  → who gets notified
      - rerun_recommended → whether to trigger CI rerun
      - is_real_bug       → whether to file a Jira ticket
      - confidence        → whether to escalate to manual review

    Adding a new failure category tomorrow?
    Update the prompt only. This file needs zero changes.
    """

    confidence = result.get("confidence", 0)

    # --- Low confidence: AI is unsure, send to manual queue ---
    if confidence < 0.7:
        notify_slack(
            failure,
            result,
            urgent=True,
            note="🚨 AI confidence too low — manual review needed"
        )
        return  # stop here, don't take any automated action

    # --- Build action notes based purely on AI output fields ---
    notes = []

    if result.get("rerun_recommended"):
        # AI decided a rerun is worth it
        # Phase 3 will add: trigger_ci_rerun(failure)
        notes.append("🔁 AI recommends a CI rerun")

    if result.get("is_real_bug"):
        # AI decided this is a real product defect
        # Phase 3 will add: file_jira_ticket(failure, result)
        notes.append("🐛 Real bug detected — Jira auto-filing in Phase 3")

    # --- Send ONE Slack message with all notes combined ---
    # suggested_owner is already in the result so Slack shows it
    notify_slack(
        failure,
        result,
        note=" | ".join(notes) if notes else ""
    )
