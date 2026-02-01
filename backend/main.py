
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from services.mongo_service import (
    verify_driver, get_driver_details, get_driver_by_phone, verify_phone, 
    create_escalation, get_escalations,
    save_message, get_chat_history, update_escalation_status, check_active_escalation
)
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

class PhoneRequest(BaseModel):
    phone: str

class AgentAcceptRequest(BaseModel):
    ticket_id: str

class AgentMessageRequest(BaseModel):
    driver_id: str
    message: str

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


@app.post("/validate-phone")
def validate_phone_endpoint(request: PhoneRequest):
    # Lookup driver by phone; return the linked driver id if present
    driver = get_driver_by_phone(request.phone)
    if driver:
        driver_id = driver.get('driver_id') or driver.get('driverId') or None
        return {"valid": True, "driver_id": driver_id, "message": "Phone number linked to driver."}
    else:
        raise HTTPException(status_code=404, detail={"valid": False, "message": "Phone number not found."})

@app.get("/agent/escalations")
def get_escalations_endpoint(status: str = "OPEN"):
    return get_escalations(status)

@app.post("/agent/accept")
def agent_accept_endpoint(request: AgentAcceptRequest):
    success = update_escalation_status(request.ticket_id, "IN_PROGRESS")
    if success:
        return {"status": "success", "message": "Escalation accepted"}
    raise HTTPException(status_code=500, detail="Failed to accept escalation")

@app.post("/agent/message")
def agent_message_endpoint(request: AgentMessageRequest):
    msg_id = save_message(request.driver_id, "agent", request.message)
    if msg_id:
        return {"status": "success", "message_id": msg_id}
    raise HTTPException(status_code=500, detail="Failed to send message")

class AgentResolveRequest(BaseModel):
    driver_id: str

@app.post("/agent/resolve")
def agent_resolve_endpoint(request: AgentResolveRequest):
    driver_id = request.driver_id
    ticket_id = check_active_escalation(driver_id)
    
    if not ticket_id:
         raise HTTPException(status_code=404, detail="No active escalation found for this driver.")
         
    success = update_escalation_status(ticket_id, "RESOLVED")
    if success:
        save_message(driver_id, "system", "Chat ended by agent.")
        return {"status": "success", "message": "Escalation resolved"}
    
    raise HTTPException(status_code=500, detail="Failed to resolve escalation")

@app.get("/chat/history/{driver_id}")
def get_history_endpoint(driver_id: str):
    return get_chat_history(driver_id)

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    driver_id = str(request.driver_id) if request.driver_id else "unknown"
    
    # 1. Save User Message
    save_message(driver_id, "user", request.message)

    # 2. Check for Active Live Agent Session
    active_ticket = check_active_escalation(driver_id)
    if active_ticket:
        logger.info(f"Active escalation for {driver_id}, skipping AI response.")
        return {
            "intent": "live_chat", 
            "confidence": 1.0, 
            "response": "Message sent to agent.", 
            "escalate": True,
            "live_mode": True
        }

    # 3. Standard AI Logic
    context = None
    if request.driver_id:
        context = get_driver_details(request.driver_id)
        if context:
            logger.info(f"Found context for driver {request.driver_id}")
        else:
            logger.warning(f"No details found for driver {request.driver_id}")
            
    import time
    start_time = time.time()
    result = detect_intent(request.message, context=context)
    logger.info(f"Intent detection took {time.time() - start_time:.2f}s")
    
    # Handle Escalation
    if result.get("escalate"):
        create_escalation(
            driver_id=driver_id,
            intent=result.get("intent", "unknown"),
            confidence=float(result.get("confidence", 0.0)),
            summary=result.get("response")
        )

    # Generate Audio and Save Bot Response
    if result.get("response"):
        try:
            # Save bot response to DB
            save_message(driver_id, "bot", result["response"])

            tts_start = time.time()
            detected_lang = result.get("language", "English")
            audio_data = generate_audio_base64(result["response"], language=detected_lang)
            result["audio"] = audio_data # Add base64 audio to response
            logger.info(f"TTS generation took {time.time() - tts_start:.2f}s")
        except Exception as e:
            logger.error(f"TTS failed: {e}")
            
    logger.info(f"Total request processed in {time.time() - start_time:.2f}s")
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
