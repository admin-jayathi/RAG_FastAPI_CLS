from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from preprocessor import preprocess
from llm_client import triage
from router import route

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
    try:
        failure = event.dict()
        failure = preprocess(failure)
        result = triage(failure)
        route(failure, result)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()  # prints full error in your uvicorn terminal
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
