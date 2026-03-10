# dev-team

Multi-agent orchestration service (PM -> Architect -> Dev/Test/Debug/Review -> Manager).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="..."
# optional
export OPENAI_MODEL="gpt-5-mini"
```

## Run

```bash
uvicorn main:app --reload
```

## API

POST `/run`

```json
{
  "user_input": "Build a feature X...",
  "mode": "parallel",
  "model": "gpt-5-mini",
  "include_intermediate": true
}
```

Response:

```json
{
  "final": "...",
  "outputs": {
    "project_manager": "...",
    "architect": "...",
    "developer": "...",
    "tester": "...",
    "debugger": "...",
    "reviewer": "...",
    "manager": "..."
  }
}
```
