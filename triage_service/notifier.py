import os
import requests
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL", "")


def notify_slack(
    failure: dict,
    result: dict,
    urgent: bool = False,
    note: str = ""
):
    """
    Sends ONE Slack message per triage result.
    All content comes from the AI result dict.
    No category-specific logic here.
    """

    # If no webhook configured yet, just print to terminal
    if not SLACK_WEBHOOK:
        print("\n[Slack - not configured yet] Triage result:")
        print(f"  Test     : {failure.get('test_name')}")
        print(f"  Category : {result.get('category')}")
        print(f"  Confidence: {result.get('confidence')}")
        print(f"  Owner    : {result.get('suggested_owner')}")
        print(f"  Summary  : {result.get('root_cause_summary')}")
        print(f"  Fix      : {result.get('suggested_fix')}")
        print(f"  Real bug : {result.get('is_real_bug')}")
        print(f"  Rerun    : {result.get('rerun_recommended')}")
        if note:
            print(f"  Note     : {note}")
        print()
        return

    # Format confidence as percentage
    confidence_pct = int(result.get("confidence", 0) * 100)

    # Build the Slack message
    # All fields come from the AI — we just display them
    lines = [
        f"*Test:* `{failure.get('test_name', 'unknown')}`",
        f"*Suite:* {failure.get('suite', 'unknown')}",
        f"*Category:* {result.get('category', 'UNKNOWN')}",
        f"*Confidence:* {confidence_pct}%",
        f"*Owner:* {result.get('suggested_owner', 'unknown')}",
        f"*Root cause:* {result.get('root_cause_summary', '')}",
        f"*Suggested fix:* {result.get('suggested_fix', '')}",
        f"*Real bug:* {'Yes' if result.get('is_real_bug') else 'No'}",
        f"*Rerun recommended:* {'Yes' if result.get('rerun_recommended') else 'No'}",
    ]

    if note:
        lines.append(f"\n_{note}_")

    text = "\n".join(lines)

    if urgent:
        text = "🚨 *NEEDS MANUAL REVIEW* 🚨\n\n" + text

    # Send to Slack
    try:
        resp = requests.post(
            SLACK_WEBHOOK,
            json={"text": text},
            timeout=5
        )
        if resp.status_code != 200:
            print(f"[Slack] Warning: got status {resp.status_code}")
    except Exception as e:
        print(f"[Slack] Failed to send notification: {e}")
