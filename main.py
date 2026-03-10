import os
from typing import Dict, Optional, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from graph import run_pipeline_async


class RunRequest(BaseModel):
    user_input: str = Field(..., min_length=1)
    mode: Literal["parallel", "sequential"] = "parallel"
    model: Optional[str] = None
    include_intermediate: bool = True


class RunResponse(BaseModel):
    final: str
    outputs: Optional[Dict[str, str]] = None


app = FastAPI(title="dev-team-orchestrator", version="0.1.0")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/run", response_model=RunResponse)
async def run_pipeline(req: RunRequest) -> RunResponse:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set")

    model = req.model or os.getenv("OPENAI_MODEL", "gpt-5-mini")
    outputs = await run_pipeline_async(req.user_input, model, req.mode)

    final = outputs.get("manager", "")
    if not final:
        raise HTTPException(status_code=500, detail="Manager output missing")

    return RunResponse(
        final=final,
        outputs=outputs if req.include_intermediate else None,
    )
