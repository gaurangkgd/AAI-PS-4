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
4. Run all unit tests (57 tests):
   ```powershell
   python -m unittest discover -p "test_*.py"
   ```
5. Start development server:
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
3. **Deterministic Intent Classifier**: Rule-based system categorizing customer messages into 8 specific e-commerce intents (`payment_issue`, `order_tracking`, `cancellation`, `return_or_replacement`, `refund_status`, `account_issue`, `product_inquiry`, `general_inquiry`).
4. **Local Support Knowledge Base**: Fictional knowledge articles covering payment troubleshooting, tracking delays, cancellation policies, returns, refunds, account security, and product inquiries.
5. **Keyword & Intent-Based Knowledge Retriever**: Ranks and extracts the most relevant support policies matching the customer's query.
6. **Read-Only Support Investigator**: Extracts order IDs (e.g. `ORD1001`), looks up associated order details and payment records directly from mock data, and supplies a factual summary without mutating data.
7. **Safe E-Commerce Action Service**:
   - **Cancellation**: Permitted only for `processing` orders (`ORD1002`). Rejected for `shipped` (`ORD1003`) and `delivered` (`ORD1001`).
   - **Return / Replacement**: Permitted only for `delivered` orders (`ORD1001`). Creates a unique `RET-<hex>` request. Prevents duplicate active returns.
   - **Payment Safety**: Payment records are strictly read-only and never modified.
8. **In-Memory Ticket Service**: Manages ticket lifecycle (`open`, `in_progress`, `resolved`), priorities (`low`, `medium`, `high`, `urgent`), and filtering.
9. **LangGraph Support Workflow (7 Nodes)**:
   - `classify_intent_node` &rarr; `retrieve_knowledge_node` &rarr; `investigate_order_node` &rarr; `decide_next_step_node` &rarr; `execute_action_node` / `escalate_node` &rarr; `compose_response_node`.

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
