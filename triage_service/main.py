from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from triage_service.preprocessor import preprocess
from triage_service.llm_client import triage
from triage_service.router import route

app = FastAPI(
    title="Test Auto-Triage Service",
    description="AI-driven triage for failed automation tests. The LLM makes all decisions."
)


class FailureEvent(BaseModel):
    test_name: str
    suite: str
    exception_type: str
    exception_message: str
    stack_trace: Optional[str] = ""
    logs_tail: Optional[str] = ""
    history: Optional[List[str]] = []


@app.get("/health")
def health():
    """Jenkins and monitoring ping this to check the service is up."""
    return {"status": "ok"}


@app.post("/triage")
def triage_failure(event: FailureEvent):
    """
    Main endpoint. Receives a failure event from Jenkins,
    sends it to the LLM, and routes based on AI output.
    Returns the full AI decision as JSON.
    """
    try:
        failure = event.dict()

        # Step 1 — clean and truncate inputs
        failure = preprocess(failure)

        # Step 2 — AI makes all decisions
        result = triage(failure)

        # Step 3 — act on what AI decided
        route(failure, result)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Triage failed: {str(e)}"
        )
