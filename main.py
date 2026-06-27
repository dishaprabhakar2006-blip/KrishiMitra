import os
import base64
import uuid
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load env variables before importing agents/tools
load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part, Blob

# Import Orchestrator and translation helpers
from agents.orchestrator_agent import (
    orchestrator_agent,
    detect_language,
    translate_to_english,
    translate_from_english
)
from agents.memory_agent import get_farmer_profile, update_farmer_profile

app = FastAPI(title="KrishiMitra Backend API")

# Enable CORS for file:// browser requests or multi-port testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate the shared session service and runner for ADK
session_service = InMemorySessionService()
runner = Runner(
    agent=orchestrator_agent,
    session_service=session_service,
    app_name="krishnamitra",
    auto_create_session=True
)

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    language: Optional[str] = "auto"  # 'auto', 'english', 'hindi', 'kannada'

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    land_size_acres: Optional[float] = None
    crop_history: Optional[list] = None

@app.get("/")
def serve_frontend():
    """Serves the single-file HTML frontend."""
    frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return {"message": "KrishiMitra Backend is running. Frontend file index.html is missing."}

@app.get("/api/profile")
def get_profile(user_id: str = "default_farmer"):
    """Fetches the registered farmer profile details."""
    return get_farmer_profile(user_id)

@app.post("/api/profile")
def update_profile(req: ProfileUpdateRequest, user_id: str = "default_farmer"):
    """Updates the farmer profile details."""
    res = update_farmer_profile(
        name=req.name,
        location=req.location,
        land_size_acres=req.land_size_acres,
        crop_history=req.crop_history,
        user_id=user_id
    )
    return res

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """Processes chat queries using the ADK Orchestrator and specialized sub-agents."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query is required.")
        
    session_id = req.session_id or str(uuid.uuid4())
    
    # 1. Determine Language
    user_lang = req.language
    if not user_lang or user_lang == "auto":
        # Detect language using Gemini translation helper
        user_lang = detect_language(req.query)
        
    # 2. Translate text query to English if needed
    english_query = req.query
    if user_lang in ["hindi", "kannada"]:
        english_query = translate_to_english(req.query, user_lang)
        
    # 3. Construct parts for the Gemini content object
    parts = []
    
    # Add textual query
    if english_query:
        parts.append(Part(text=english_query))
            
    msg = Content(role="user", parts=parts)
    
    # 4. Execute the multi-agent pipeline
    response_english = ""
    responding_agent = "OrchestratorAgent"
    
    try:
        async for event in runner.run_async(user_id="default_farmer", session_id=session_id, new_message=msg):
            # Capture the current responding agent node name
            if event.node_name:
                responding_agent = event.node_name
                
            # Capture response text
            if event.message and event.message.parts:
                text_part = "".join([p.text for p in event.message.parts if getattr(p, "text", None)])
                if text_part:
                    response_english = text_part
                    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ADK Execution Error: {str(e)}")
        
    if not response_english:
        response_english = "I apologize, but I could not formulate a response. Please try again."
        
    # 5. Translate English response back to original user language
    final_response = response_english
    if user_lang in ["hindi", "kannada"]:
        final_response = translate_from_english(response_english, user_lang)
        
    # Return formatted JSON response
    return {
        "session_id": session_id,
        "response": final_response,
        "original_response": response_english,
        "agent": responding_agent,
        "language": user_lang
    }

if __name__ == "__main__":
    import uvicorn
    # If run directly, launch the API server on port 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
