# Agentic Customer Support System

A group mini-project for the Artificial Intelligence and Applications (AAI) subject.

> **Disclaimer & Fictional Data Notice**:
> All e-commerce data (products, orders, customers, payments), support tickets, return requests, and troubleshooting policies in the knowledge base are entirely **fictional sample data** designed solely for demonstrating this academic mini-project. They do not represent real-world timelines, guarantees, or merchant terms and are stored in-memory, resetting when the server restarts. No real financial transactions, payment reversals, or credit card debits are executed.

---

## System Architecture

```text
+-----------------------------------------------------------+
|               NextStore Frontend (Next.js 14)             |
|  - App Router, JavaScript, Responsive Vanilla CSS         |
|  - Modern Navigation, Hero, Product & Support Placeholders|
|  - Reusable API Client (lib/api.js)                       |
+-----------------------------+-----------------------------+
                              | HTTP / JSON (port 3000 -> 8000)
                              v
+-----------------------------------------------------------+
|                 FastAPI Backend Service                   |
|  - CORS enabled for http://localhost:3000                 |
|  - Deterministic Intent Classifier (8 categories)          |
|  - Support Knowledge Base & Keyword Relevance Retriever   |
|  - Read-Only Order & Payment Support Investigator         |
|  - Safe Support Actions (Cancel Processing, Return Order) |
|  - Human Support Escalation & In-Memory Ticket Service    |
|  - LangGraph Orchestrated Support Workflow (7 Nodes)      |
+-----------------------------------------------------------+
```

---

## Prerequisites

- **Python**: 3.10 or higher (added to PATH)
- **Node.js**: v18.0.0 or higher
- **npm**: v9.0.0 or higher

---

## Quick Start (Two Terminals)

### Terminal 1: Start FastAPI Backend

1. Navigate to the `backend` folder:
   ```powershell
   cd backend
   ```
2. Create & activate Python virtual environment:
   - **PowerShell**:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - **Command Prompt**:
     ```cmd
     python -m venv .venv
     .\.venv\Scripts\activate.bat
     ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. (Optional) Configure Gemini LLM API Key:
   ```powershell
   cp .env.example .env
   # Edit .env and set GEMINI_API_KEY (System automatically uses rule-based fallback if unset)
   ```
5. Run all unit tests (112 tests):
   ```powershell
   python -m unittest discover -p "test_*.py"
   ```
6. Start development server:
   ```powershell
   uvicorn main:app --reload --port 8000
   ```
   *Backend will run at: `http://127.0.0.1:8000` (Docs: `http://127.0.0.1:8000/docs`)*

---

### Terminal 2: Start Next.js Frontend

1. Navigate to the `frontend` folder:
   ```powershell
   cd frontend
   ```
2. Verify environment configuration in `frontend/.env.local`:
   ```properties
   NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
   ```
3. Install dependencies:
   ```powershell
   npm install
   ```
4. (Optional) Run production build:
   ```powershell
   npm run build
   ```
5. Start development server:
   ```powershell
   npm run dev
   ```
   *Frontend will run at: `http://localhost:3000`*

---

## Frontend Architecture

- **Framework**: Next.js 14 (App Router, JavaScript)
- **Directory Structure**:
  - `frontend/app/layout.js`: Global root layout with responsive navigation and footer.
  - `frontend/app/page.js`: Homepage featuring dynamic product catalog with real-time fetching from `/products`, shimmer loading skeletons, error states with retry, interactive product detail modal (`/products/{product_id}`), and integrated live AI Support Chat panel.
  - `frontend/app/orders/page.js`: Dedicated My Orders page displaying customer orders (`GET /customers/{customer_id}/orders`), demo customer persona selector, status badges, and interactive order detail modal (`GET /orders/{order_id}`).
  - `frontend/components/ChatPanel.js`: Interactive AI support chat interface connected to `POST /chat`, managing conversation sessions, loading indicators, intent/decision tags, and confirmed structured support cards (actions, tickets, order investigation, policy references).
  - `frontend/app/globals.css`: Modern, responsive CSS styling tokens, product and order cards, status badges, chat bubbles, skeleton animations, modals, and mobile breakpoints.
  - `frontend/lib/api.js`: Reusable API client reading `NEXT_PUBLIC_API_BASE_URL` with structured error handling.
  - `frontend/.env.local`: Local environment variable pointing to the FastAPI backend.

---

## Backend Features & Workflows

1. **FastAPI Web Service**: Core endpoints for health monitoring, conversational customer chat, mock e-commerce operations, support tickets, and safe actions.
2. **CORS Middleware**: Explicitly configured for `http://localhost:3000` and `http://127.0.0.1:3000`.
3. **Conversation Understanding Agent (LLM + Fallback)**: The first specialized agent of the 11-agent architecture. Employs Google Gemini (`langchain-google-genai`) with structured output validation (intent, category, priority, sentiment, confidence, needs_clarification, explanation) while preserving seamless deterministic rule-based fallback when no API key is configured.
4. **Customer Context Agent (Safe, Read-Only & Isolated)**: The second specialized agent of the 11-agent architecture. Resolves verified vs. unverified customer identity, correlates customer orders and tickets, identifies missing or ambiguous customer data, enforces privacy (strictly preventing cross-customer data exposure), and operates in a strictly read-only manner.
5. **Knowledge Retrieval / Knowledge Base Agent (Grounded & Reranked)**: The third specialized agent of the 11-agent architecture. Retrieves verified policy and troubleshooting articles from the approved knowledge base using keyword/intent matching, with optional Gemini-assisted candidate reranking and zero-hallucination guarantees. Deterministic fallback ensures full offline functionality.
6. **Troubleshooting Agent (Grounded Diagnosis & Read-Only Recommendations)**: The fourth specialized agent of the 11-agent architecture. Synthesizes order/payment facts, customer context, and approved knowledge articles into a structured diagnosis with evidence, recommended next steps, and escalation signals. Strictly read-only with deterministic rule-based fallback.
7. **Action Execution Agent (Guarded & Safe Mutation Execution)**: The fifth specialized agent of the 11-agent architecture. Safely executes permitted e-commerce operations (order cancellation for processing orders and return/replacement requests for delivered orders) with strict ownership validation, duplicate prevention, confirmation-required handling, and zero financial mutation guarantees.
8. **Multi-Turn Memory Agent (Isolated Session State & Anaphoric Resolution)**: The sixth specialized agent of the 11-agent architecture. Maintains isolated, bounded conversational memory across turns for each session ID. Resolves anaphoric references ('it', 'that order', 'the same order') to active order context, detects ambiguous or conflicting order mentions, enforces strict action confirmation tying affirmative customer responses ('yes') to exact pending confirmation requests, and distinguishes unverified customer claims from verified data records.
9. **Escalation Decision Agent (Safety-Guarded Human Handoff)**: The seventh specialized agent of the 11-agent architecture. Evaluates whether a customer inquiry can be resolved automatically or requires escalation to a human support specialist. Combines Gemini-assisted contextual sentiment and urgency reasoning with strict, deterministic hard safety rules (explicit human/supervisor requests, verified payment failures, unrecognized order payment deductions, financial disputes) that cannot be overridden by the LLM. Integrates duplicate ticket prevention within multi-turn sessions and assigns cases to appropriate support departments (`billing_support`, `logistics_support`, `technical_support`, `senior_support`, `general_support`).
10. **Local Support Knowledge Base**: Fictional knowledge articles covering payment troubleshooting, tracking delays, cancellation policies, returns, refunds, account security, and product inquiries.
11. **Read-Only Support Investigator**: Extracts order IDs (e.g. `ORD1001`), looks up associated order details and payment records directly from mock data, and supplies a factual summary without mutating data.
12. **Safe E-Commerce Action Service**:
   - **Cancellation**: Permitted only for `processing` orders (`ORD1002`). Rejected for `shipped` (`ORD1003`) and `delivered` (`ORD1001`).
   - **Return / Replacement**: Permitted only for `delivered` orders (`ORD1001`). Creates a unique `RET-<hex>` request. Prevents duplicate active returns.
   - **Payment Safety**: Payment records are strictly read-only and never modified.
13. **In-Memory Ticket Service**: Manages ticket lifecycle (`open`, `in_progress`, `resolved`), priorities (`low`, `medium`, `high`, `urgent`), and filtering.
14. **LangGraph Support Workflow (9 Nodes)**:
   - `classify_intent_node` &rarr; `resolve_customer_context_node` &rarr; `retrieve_knowledge_node` &rarr; `investigate_order_node` &rarr; `troubleshoot_node` &rarr; `decide_next_step_node` &rarr; `execute_action_node` / `escalate_node` &rarr; `compose_response_node`.

---

## API Endpoints Reference

### 1. Conversational Chat
- `POST /chat` — Full LangGraph workflow execution returning `assistant_message`, `intent`, `decision`, `knowledge_results`, `investigation`, `action_result`, and `ticket`.

### 2. Action Endpoints
- `POST /orders/{order_id}/cancel` — Cancel processing order (`200 OK`, `400 Bad Request` if ineligible, `404 Not Found` if missing).
- `POST /orders/{order_id}/return` — Record return/replacement request (`201 Created`, `400 Bad Request` if ineligible/duplicate, `404 Not Found`).

### 3. Support Ticket Endpoints
- `POST /tickets` — Create ticket manually (`201 Created`).
- `GET /tickets/{ticket_id}` — Get ticket by ID (`404 Not Found` if missing).
- `GET /tickets` — List tickets with optional `status` and `category` filters.

### 4. Mock E-Commerce Endpoints
- `GET /products` — List all products.
- `GET /products/{product_id}` — Retrieve a single product by ID.
- `GET /orders/{order_id}` — Retrieve an order by ID.
- `GET /customers/{customer_id}/orders` — Retrieve all orders belonging to a customer ID.
- `GET /payments/{order_id}` — Retrieve payment transaction records for an order.
- `GET /health` — Health check endpoint.
- `GET /docs` — Interactive Swagger documentation.
