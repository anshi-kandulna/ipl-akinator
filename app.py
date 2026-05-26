from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.game import new_game, process_answer, process_feedback, get_session_state, cleanup_session

app = FastAPI(title="IPL Akinator")

# ── CORS CONFIGURATION ────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # vite default port
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── SCHEMAS ───────────────────────────────────────────────────────────────────

class AnswerRequest(BaseModel):
    session_id: str
    answer: str  # yes | no | maybe | dont_know

class FeedbackRequest(BaseModel):
    session_id: str
    was_correct: bool

# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.post("/game/new")
def start_game():
    """Start a new game session."""
    try:
        return new_game()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/game/answer")
def answer(req: AnswerRequest):
    """Submit answer to current question."""
    if req.answer not in ('yes', 'no', 'maybe', 'dont_know'):
        raise HTTPException(status_code=400, detail="answer must be yes/no/maybe/dont_know")
    try:
        return process_answer(req.session_id, req.answer)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/game/feedback")
def feedback(req: FeedbackRequest):
    """Submit feedback on whether the guess was correct."""
    try:
        return process_feedback(req.session_id, req.was_correct)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/game/state/{session_id}")
def state(session_id: str):
    """Get current session state — for debugging."""
    try:
        return get_session_state(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/game/{session_id}")
def cleanup(session_id: str):
    """Clean up session from memory."""
    cleanup_session(session_id)
    return {"message": "Session cleaned up"}


# ── RUN ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)