# 🤖 Agentic Customer Support System (PS-04)

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2014-black.svg?logo=next.js&logoColor=white)](https://nextjs.org/)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-blue.svg)](https://langchain-ai.github.io/langgraph/)
[![Google Gemini](https://img.shields.io/badge/LLM-Gemini%201.5%20Flash-4285F4.svg?logo=google&logoColor=white)](https://ai.google.dev/)
[![Tests](https://img.shields.io/badge/Unit%20Tests-151%20Passed-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://python.org/)

An academic group project for **Artificial Intelligence and Applications (AAI)** implementing **PS-04: Agentic Customer Support System**. 

The system implements a production-grade, multi-agent support architecture coordinating specialized AI agents to autonomously handle e-commerce customer support inquiries—from natural language understanding, customer identity resolution, and grounded policy retrieval to multi-step diagnosis, guarded action execution, intelligent escalation, and structured ticket generation.

---

> [!NOTE]
> **Academic Scope & Fictional Data Notice**:
> All e-commerce data (products, orders, customers, transactions), support tickets, return authorizations, and knowledge base policies are **fictional mock records** designed solely for demonstration and academic evaluation.
> - Data is stored strictly **in-memory** and resets upon server restart.
> - **Zero financial transactions**: No real credit card charges, refunds, or payment debits are executed.

---

## 🏛️ System Architecture

```text
+---------------------------------------------------------------------------------------+
|                            NextStore Frontend (Next.js 14)                            |
|  - Modern Storefront (Dynamic Catalog, Shimmer Skeletons, Interactive Detail Modals)  |
|  - My Orders Dashboard (Customer Switcher, Live Status Badges, Order Investigation)   |
|  - Interactive AI Support Chat (Session Memory, Confirmation Prompts, Ticket Badges)  |
+-------------------------------------------+-------------------------------------------+
                                            | HTTP / JSON (port 3000 -> 8000)
                                            v
+---------------------------------------------------------------------------------------+
|                               FastAPI Backend Service                                 |
|  - Multi-Turn Memory Agent: Session Bounding, Anaphoric Resolution ("it"), Context    |
|  - Deterministic Fallback Mode: Seamless offline capability without API keys         |
|                                                                                       |
|                 LangGraph Orchestrated Support Workflow (9 Nodes)                    |
|                                                                                       |
|   [1. Conversation Understanding]  -->  [2. Customer Context]                         |
|              |                                    |                                   |
|              v                                    v                                   |
|   [3. Knowledge Retrieval]         -->  [4. Order & Payment Investigation]             |
|              |                                    |                                   |
|              v                                    v                                   |
|   [5. Troubleshooting Diagnosis]   -->  [6. Escalation Decision Agent]                |
|                                                   |                                   |
|                    +------------------------------+------------------------------+     |
|                    |                                                             |     |
|                    v (Actionable Intent)                                         v (Escalated)
|        [7. Action Execution Agent]                                   [8. Ticket Generation Agent]
|        - Cancel (Processing Only)                                    - Deduplicated Session Reuse
|        - Return / Replacement                                        - Claims vs. Facts Partition
|                    |                                                             |     |
|                    +------------------------------+------------------------------+     |
|                                                   |                                   |
|                                                   v                                   |
|                                      [9. Response Composition]                        |
+---------------------------------------------------------------------------------------+
```

---

## 🧩 Multi-Agent Component Status (PS-04 Architecture)

The project specification outlines an **11-component multi-agent architecture** (10 specialized domain agents + 1 Master Orchestrator):

| # | Agent / Component | Phase | Status | Key Responsibilities |
| :---: | :--- | :---: | :---: | :--- |
| **1** | **Conversation Understanding Agent** | Phase 1 | ✅ **Complete** | Classifies customer intent (8 categories), detects urgency, sentiment, and extracts entity order IDs using Gemini with rule-based fallback. |
| **2** | **Customer Context Agent** | Phase 2A | ✅ **Complete** | Resolves verified vs. unverified customer identity, correlates past orders/tickets, and strictly prevents cross-customer data leakage. |
| **3** | **Knowledge Retrieval Agent** | Phase 2B | ✅ **Complete** | Retrieves official policy articles from the grounded knowledge base, verifies relevance, and performs optional LLM candidate reranking. |
| **4** | **Troubleshooting Agent** | Phase 2C | ✅ **Complete** | Synthesizes verified orders, payments, and policy articles into an actionable diagnosis with escalation triggers. Read-only. |
| **5** | **Action Execution Agent** | Phase 2D | ✅ **Complete** | Executes permitted actions (cancellation for processing orders, return/replacement for delivered items) with confirmation safety checks. |
| **6** | **Multi-Turn Memory Agent** | Phase 2E | ✅ **Complete** | Resolves anaphora ("it", "that order"), manages multi-turn session context, and links affirmative customer confirmations ("yes") to pending actions. |
| **7** | **Escalation Decision Agent** | Phase 2F | ✅ **Complete** | Evaluates automatic resolution vs. human handoff with hard safety policies (payment errors, supervisor requests) overriding LLM recommendations. |
| **8** | **Ticket Generation Agent** | Phase 2G | ✅ **Complete** | Generates deduplicated, structured support tickets for human review. Partitions unverified customer claims from verified database facts. |
| **9** | **Resolution Tracking Agent** | Phase 3 | ⏳ *Planned* | Tracks resolution lifecycles and human handoff states across session histories. |
| **10** | **Customer Satisfaction Agent** | Phase 3 | ⏳ *Planned* | Evaluates user sentiment progression, post-resolution CSAT ratings, and feedback. |
| **11** | **Master Orchestrator Agent** | Phase 3 | ⏳ *Planned* | Dynamically orchestrates multi-agent delegation, routing, and adaptive agent planning. |

---

## 🛡️ Core Safeguards & Security Rules

1. **Zero Financial Mutation**: Payment records (`PAYMENTS`) are strictly read-only. No agent can initiate financial debits, credit card refunds, or payment modifications.
2. **Deterministic Fallbacks**: If the Google Gemini API key is missing, rate-limited (HTTP 429), or throws an unexpected exception, all agents automatically fall back to deterministic rule engines without disrupting user workflows.
3. **Action Confirmation Guards**: Irreversible actions (order cancellations and returns) require explicit customer confirmation (`yes` / `proceed`) before execution.
4. **Order State Eligibility**:
   - **Cancellation**: Permitted **only** when an order status is `processing`. Rejected if `shipped` or `delivered`.
   - **Return / Replacement**: Permitted **only** when an order status is `delivered`. Rejects duplicate active returns.
5. **Claims vs. Verified Facts Partitioning**: Tickets explicitly separate unverified user claims (e.g. self-reported order IDs not in DB, customer statements) from verified system records (live database order status, transaction counts).
6. **Duplicate Prevention & Session Reuse**: The system reuses existing open tickets for the same unresolved issue within a session, while ensuring completely unrelated issues receive separate tickets.

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python**: 3.10+ (added to system PATH)
- **Node.js**: v18.0.0+ & **npm**: v9.0.0+

---

### Terminal 1: Backend Setup & Server

```powershell
# 1. Navigate to backend directory
cd backend

# 2. Create and activate virtual environment
python -m venv .venv

# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows Command Prompt:
.\.venv\Scripts\activate.bat

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. (Optional) Configure Gemini API Key
cp .env.example .env
# Open .env and set: GEMINI_API_KEY=your_key_here
# Note: If unset, the backend runs 100% offline via deterministic rule-based fallbacks!

# 5. Run the complete backend test suite (151 unit tests)
python -m unittest discover -p "test_*.py"

# 6. Start the FastAPI development server
uvicorn main:app --reload --port 8000
```
> **Backend URL**: `http://127.0.0.1:8000`  
> **Interactive Swagger API Docs**: `http://127.0.0.1:8000/docs`

---

### Terminal 2: Frontend Setup & Server

```powershell
# 1. Navigate to frontend directory
cd frontend

# 2. Verify frontend/.env.local contains:
# NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000

# 3. Install frontend dependencies
npm install

# 4. (Optional) Validate production build
npm run build

# 5. Launch Next.js development server
npm run dev
```
> **Frontend URL**: `http://localhost:3000`

---

## 🧪 Demo Personas & Test Scenarios

The system includes preloaded mock e-commerce data to demonstrate every agent capability:

### Fictional Orders

| Order ID | Customer | Items | Total | Status | Intended Test Case |
| :---: | :---: | :--- | :---: | :---: | :--- |
| `ORD1001` | `CUST001` | Noise-Canceling Headphones (x1) | $129.99 | `delivered` | **Return / Replacement**: Eligible for return request. Cancellation rejected. |
| `ORD1002` | `CUST001` | Thermal Water Bottle (x2) | $49.90 | `processing` | **Cancellation**: Eligible for cancellation with confirmation prompt. |
| `ORD1003` | `CUST002` | Ultra-Light Running Shoes (x1) | $74.99 | `shipped` | **Order Tracking**: In transit with tracking number `TRK-US-89211`. Cancellation rejected. |
| `ORD1004` | `CUST001` | Mechanical Keyboard (x1) | $49.99 | `cancelled` | **Payment Escalation**: Payment failed (`PAY-004`). Triggers escalation & ticket generation. |

### Sample Prompts to Try in Live Chat
- **Order Tracking**: `"Where is my order ORD1001?"`
- **Anaphoric Resolution (Memory)**: `"When was it ordered?"` &rarr; agent resolves "it" to `ORD1001`.
- **Cancellation with Guarded Confirmation**: `"I want to cancel order ORD1002."` &rarr; reply `"yes"` to execute.
- **Ineligible Cancellation**: `"Please cancel my order ORD1001."` &rarr; agent cites policy: delivered orders cannot be cancelled.
- **Return / Replacement**: `"I want to return order ORD1001 because it is defective."` &rarr; executes return authorization `RET-...`.
- **Payment Dispute & Escalation**: `"Payment was deducted for order ORD1004 but the order failed!"` &rarr; triggers Escalation Decision Agent and creates a deduplicated support ticket with Billing Support.
- **Explicit Human Agent Request**: `"I want to speak with a human supervisor right now."` &rarr; hard safety policy immediately escalates and creates a support ticket.

---

## 📡 API Reference Overview

| Endpoint | Method | Category | Description |
| :--- | :---: | :---: | :--- |
| `/chat` | `POST` | **Chat** | Full multi-agent workflow execution returning message, intent, decision, ticket, and action details. |
| `/orders/{order_id}/cancel` | `POST` | **Action** | Cancel processing order (strictly validates `processing` state). |
| `/orders/{order_id}/return` | `POST` | **Action** | Initiate return or replacement request for delivered items. |
| `/tickets` | `POST` | **Tickets** | Create a support ticket manually. |
| `/tickets` | `GET` | **Tickets** | List all support tickets with optional `status` and `category` filters. |
| `/tickets/{ticket_id}` | `GET` | **Tickets** | Retrieve a single support ticket by ID. |
| `/products` | `GET` | **Store** | Retrieve catalog of mock products. |
| `/products/{product_id}` | `GET` | **Store** | Retrieve single product details. |
| `/orders/{order_id}` | `GET` | **Store** | Retrieve order status and item list. |
| `/customers/{customer_id}/orders` | `GET` | **Store** | Retrieve all orders belonging to a customer account. |
| `/payments/{order_id}` | `GET` | **Store** | Retrieve payment transaction records for an order. |
| `/health` | `GET` | **System** | Service health status check. |

---

## 💻 Tech Stack Summary

- **Frontend**: Next.js 14, React 18, Vanilla CSS (Design Tokens, Glassmorphism, Micro-Animations).
- **Backend API**: FastAPI, Pydantic v2, Uvicorn.
- **Agent Orchestration**: LangGraph, StateGraph, TypedDict state schemas.
- **LLM Integration**: Google Gemini 1.5 Flash via `langchain-google-genai` with structured output schemas.
- **Testing**: Python `unittest`, FastAPI `TestClient`, Mock data harnesses (151 unit tests).

---

Developed with ❤️ for the **Artificial Intelligence and Applications (AAI)** Course.
