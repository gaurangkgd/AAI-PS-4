"""FastAPI Main Application for Autonomous Agentic Customer Support."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from backend.schemas import ChatRequest, ChatResponse
    from backend.ecommerce_routes import router as ecommerce_router
    from backend.ticket_routes import router as ticket_router
    from backend.action_routes import router as action_router
    from backend.admin_routes import router as admin_router
    from backend.checkout_routes import router as checkout_router
    from backend.notification_routes import router as notification_router
    from backend.graph import run_support_workflow
except ImportError:
    from schemas import ChatRequest, ChatResponse
    from ecommerce_routes import router as ecommerce_router
    from ticket_routes import router as ticket_router
    from action_routes import router as action_router
    from admin_routes import router as admin_router
    from checkout_routes import router as checkout_router
    from notification_routes import router as notification_router
    from graph import run_support_workflow

app = FastAPI(
    title="Agentic Customer Support API",
    description="Multi-Agent Customer Support System leveraging LangGraph, MemorySaver, and ReAct tools.",
    version="2.0.0",
)

# Configure CORS for local Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ecommerce_router)
app.include_router(ticket_router)
app.include_router(action_router)
app.include_router(admin_router)
app.include_router(checkout_router)
app.include_router(notification_router)


@app.get("/")
def read_root():
    return {
        "message": "Autonomous Agentic Customer Support API is running",
        "version": "2.0.0",
        "framework": "LangGraph",
    }


@app.get("/health")
def read_health():
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    workflow_result = run_support_workflow(
        request.message,
        request.session_id,
        customer_id=request.customer_id,
    )
    return ChatResponse(**workflow_result)
