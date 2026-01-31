
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from services.mongo_service import verify_driver, get_driver_details, create_escalation, get_pending_escalations
from services.bedrock_service import detect_intent
from services.polly_service import generate_audio_base64

# 1. App Initialization
app = FastAPI()

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 4. Pydantic Models
class DriverRequest(BaseModel):
    driver_id: str | int

class ChatRequest(BaseModel):
    message: str
    driver_id: str | int | None = None

# 5. Endpoints

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/validate-driver")
def validate_driver_endpoint(request: DriverRequest):
    is_valid = verify_driver(request.driver_id)
    
    if is_valid:
        return {"valid": True, "message": "Driver ID verified safely."}
    else:
        raise HTTPException(status_code=404, detail={"valid": False, "message": "Driver ID not found."})

@app.get("/agent/escalations")
def get_escalations_endpoint():
    return get_pending_escalations()

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    context = None
    if request.driver_id:
        context = get_driver_details(request.driver_id)
        if context:
            logger.info(f"Found context for driver {request.driver_id}")
        else:
            logger.warning(f"No details found for driver {request.driver_id}")
            
    result = detect_intent(request.message, context=context)
    
    # Handle Escalation
    if result.get("escalate"):
        create_escalation(
            driver_id=str(request.driver_id) if request.driver_id else "Unknown",
            intent=result.get("intent", "unknown"),
            confidence=float(result.get("confidence", 0.0)),
            summary=result.get("response")
        )

    # Generate Audio for the response
    if result.get("response"):
        detected_lang = result.get("language", "English")
        audio_data = generate_audio_base64(result["response"], language=detected_lang)
        result["audio"] = audio_data # Add base64 audio to response
        
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
