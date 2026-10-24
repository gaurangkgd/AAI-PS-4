

# 🤖 Autonomous Agentic Customer Support System (PS-04)

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](<https://img.shields.io/badge/Frontend-Next.js%2014-black.svg?logo=next.js&logoColor=white>)](https://nextjs.org/)
[![LangGraph](<https://img.shields.io/badge/Orchestration-LangGraph%20ReAct-blue.svg>)](https://langchain-ai.github.io/langgraph/)
[![Google Gemini](<https://img.shields.io/badge/LLM-Gemini%203.5%20Flash--Lite-4285F4.svg?logo=google&logoColor=white>)](https://ai.google.dev/)
[![Tests](<https://img.shields.io/badge/Unit%20Tests-31%20Passed-brightgreen.svg>)]()
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://python.org/)

An enterprise-ready, multi-agent AI system implementing **PS-04: Agentic Customer Support System** for e-commerce customer experience.

The platform coordinates specialized AI agents with tool access to autonomously handle multi-turn conversations, verify customer records, execute guarded actions, detect root-cause anomalies, escalate complex issues to human specialists, track ticket lifecycles, and monitor CSAT.

---

> [!NOTE]
> **Academic Scope & Fictional Data Notice**:
> All e-commerce data (products, orders, customers, transactions), support tickets, return authorizations, and policies are **fictional mock records** designed solely for demonstration and academic evaluation.
>
> - Data is stored in-memory via LangGraph memory checkpointers and resets upon server restart.
> - **Zero financial transactions**: No real credit card charges, refunds, or payment debits are executed.

---

## 🏛️ System Architecture

```text
+---------------------------------------------------------------------------------------+
|                            NextStore Frontend (Next.js 14)                            |
|  - Modern Storefront (Dynamic Catalog, Shimmer Skeletons, Interactive Modals)         |
|  - My Orders Dashboard (Customer Persona Switcher, Live Order Investigation)          |
|  - Interactive AI Support Chat (Session Memory, Confirmation Guards, CSAT Rating)    |
|  - Supervisor Operations Dashboard (/admin: Real-time KPIs, Root Cause Alerts, Kanban)|
+-------------------------------------------+-------------------------------------------+
                                            | HTTP / JSON (port 3000 -> 8000)
                                            v
+---------------------------------------------------------------------------------------+
|                               FastAPI Backend Service                                 |
|  - LangGraph MemorySaver: Multi-Turn Thread History & Automatic Anaphoric Resolution   |
|  - Deterministic Fallback Mode: 100% Offline Capability Without API Keys             |
|                                                                                       |
|                 Hierarchical Multi-Agent Supervisor Architecture                      |
|                                                                                       |
|                           [1. Master Supervisor Agent]                                |
|                        (Orchestrator & Dynamic Intent Router)                         |
|                                     |                                                 |
|          +--------------------------+--------------------------+                      |
|          |                          |                          |                      |
|          v                          v                          v                      |
|  [2. Support Triage Agent]  [3. Action Agent]     [4. Escalation & Ticket Agent]      |
|  - lookup_order             - cancel_order         - create_support_ticket            |
|  - lookup_payment           - request_return       - update_ticket_status             |
|  - lookup_customer          - initiate_refund      - search_tickets                   |
|  - search_knowledge_base                           - record_csat_rating               |
|  - check_return_eligibility                        - get_resolution_metrics           |
+---------------------------------------------------------------------------------------+
```

---

## 🧩 PS-04 Requirements Matrix

|      #      | PS-04 Core Component                   | Architecture Implementation                                                                                                           |   Status   |
| :----------: | :------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------ | :---------: |
| **1** | **Conversation Understanding**   | Supervisor Agent classifies intent, urgency, and customer sentiment.                                                                  | ✅ Complete |
| **2** | **Customer Context**             | `lookup_customer` tool retrieves customer tier (VIP, Premium), history, and tickets.                                                | ✅ Complete |
| **3** | **Knowledge Base**               | `search_knowledge_base` searches 12 official policy and troubleshooting guides.                                                     | ✅ Complete |
| **4** | **Troubleshooting**              | Support Triage Agent investigates live database orders and payment records.                                                           | ✅ Complete |
| **5** | **Action Execution**             | Action Agent executes cancellations, return labels, and refund authorizations.                                                        | ✅ Complete |
| **6** | **Multi-Turn Memory**            | Native LangGraph `MemorySaver` checkpointer preserves thread state and resolves anaphora.                                           | ✅ Complete |
| **7** | **Escalation Decision**          | Escalation Agent evaluates payment failures, manager requests, and assigns priority.                                                  | ✅ Complete |
| **8** | **Ticket Generation**            | Generates structured support tickets with SLA deadlines and assigned department.                                                      | ✅ Complete |
| **9** | **Resolution Tracking**          | `update_ticket_status` tracks lifecycle: `open` &rarr; `assigned` &rarr; `in_progress` &rarr; `resolved` &rarr; `closed`. | ✅ Complete |
| **10** | **Customer Satisfaction (CSAT)** | `record_csat_rating` tool + interactive 5-star rating widget in chat.                                                               | ✅ Complete |
| **11** | **Master Orchestrator**          | Master Supervisor Agent coordinates delegation and multi-agent workflow.                                                              | ✅ Complete |

---

## 🏆 Advanced Features (What Can Win)

1. **Supervisor Operations Dashboard (`/admin`)**:
   - Live KPI cards: Total Tickets, Auto-Resolution Rate %, Escalation Rate %, Average CSAT Rating, SLA Breaches.
   - Interactive Ticket Lifecycle Board to update statuses and assign specialists.
2. **Root Cause Discovery & Incident Detection**:
   - Anomaly detector flags spikes in payment failures or courier delays as `PAYMENT_GATEWAY_ANOMALY` with actionable ops alerts.
3. **Sentiment-Aware Empathy & Priority Boosting**:
   - Urgent/frustrated customer messages automatically elevate ticket priority and accelerate escalation.
4. **SLA Monitoring**:
   - Computes target resolution deadlines based on customer tiers: VIP/Premium (2h), High (4h), Standard (8h).
5. **Interactive Confirmation Safety Guards**:
   - Irreversible actions (order cancellations) render interactive confirmation prompt cards in chat (`Yes, Cancel` / `No, Keep`).

---

## 🚀 Quick Start Guide

### Prerequisites

- **Python**: 3.10+
- **Node.js**: v18.0.0+ & **npm**: v9.0.0+

---

### Terminal 1: Backend Setup & Server

```powershell
# 1. Navigate to backend directory
cd backend

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. (Optional) Configure Gemini API Key
# If unset, backend operates 100% offline via deterministic LangGraph supervisor fallback!
$env:GEMINI_API_KEY="your_key_here"

# 4. Run the test suite (31 unit & integration tests)
python -m unittest discover -s tests -p "test_*.py"

# 5. Launch FastAPI development server
uvicorn main:app --reload --port 8000
```

> **Backend URL**: `http://127.0.0.1:8000`
> **Interactive Swagger API Docs**: `http://127.0.0.1:8000/docs`

---

### Terminal 2: Frontend Setup & Server

```powershell
# 1. Navigate to frontend directory
cd frontend

# 2. Install frontend dependencies
npm install

# 3. Launch Next.js development server
npm run dev
```

> **Storefront & AI Chat**: `http://localhost:3000`
> **Customer Orders**: `http://localhost:3000/orders`
> **Supervisor Dashboard**: `http://localhost:3000/admin`

---

## 🧪 5 Evaluation Test Scenarios & Expected Outcomes

Use the **Customer Persona Switcher** dropdown in the top-right corner of the chat header to select the corresponding customer before entering each test question. This automatically supplies the active `customer_id` and customer profile to the AI agents.

If you ever wish to re-run the tests from a clean slate, click the **Reset Demo DB** button on the **Supervisor Desk** (`http://localhost:3000/admin`) at any time.

---

### Test 1: Cancellation Safety Guard & Confirmation Lifecycle
* **Active Customer Persona**: Select **Alice Johnson (`CUST001`)**
* **Prompt**:
  ```text
  Can you please cancel my pending order?
  ```
* **Multi-Agent Execution**:
  1. **Supervisor Agent** inspects `CUST001`'s order history via `lookup_order` and discovers pending order `ORD1002` (Thermal Water Bottle, `$49.90`, status: `processing`).
  2. **Confirmation Guard** activates: Because order cancellation is an irreversible destructive action, the AI does *not* immediately execute it. Instead, it presents an interactive confirmation dialog with action buttons (`Yes, Cancel Order` / `No, Keep Order`).
  3. **User Action**: Click **"Yes, Cancel Order"** (or type `"Yes, proceed with cancellation"`).
  4. **Action Agent** calls `cancel_order(order_id="ORD1002")`, successfully changing order status to `cancelled` and issuing an automated refund credit.
  5. **Conversational Follow-Up**: The AI inquires if there is anything else it can assist with.
  6. **CSAT Widget**: An interactive 1–5 star rating widget appears at the bottom of the card.
* **Expected Outcome**:
  - Response displays order `ORD1002` details and asks for explicit confirmation.
  - Upon confirmation, order status updates to `cancelled` with refund authorization.
  - Follow-up check: *"Is there anything else I can help you with today?"*
  - Submitting a 5-star rating dynamically updates the CSAT metrics on the Supervisor Desk (`/admin`).

---

### Test 2: In-Transit Courier Rescheduling & Policy Alternative
* **Active Customer Persona**: Select **Bob Smith (`CUST002`)**
* **Prompt**:
  ```text
  Can I reschedule the courier delivery for my order?
  ```
* **Multi-Agent Execution**:
  1. **Supervisor Agent** identifies Bob's order `ORD1003` (Mechanical Keyboard, `$89.50`, status: `shipped`, Carrier: `UPS`, Tracking: `UPS-TRK-98721`).
  2. **Triage Agent** checks policy via `search_knowledge_base(category="order_tracking")`.
  3. **Policy Determination**: Once an order has physically shipped, direct seller dispatch rescheduling is locked. The customer must use the carrier's self-service portal with their tracking number.
  4. **Agent Response**: AI explains that order `ORD1003` is already in transit with UPS (`UPS-TRK-98721`), explains why the merchant cannot edit the route directly, and provides carrier instructions to reschedule delivery via UPS My Choice or package holding.
* **Expected Outcome**:
  - Accurate carrier tracking number `UPS-TRK-98721` provided.
  - Transparent policy explanation (cannot cancel or reroute directly once shipped).
  - Proactive assistance offer: *"Let me know if you need carrier contact details or help with anything else!"*

---

### Test 3: Payment Anomaly & Automatic Human Escalation Ticket
* **Active Customer Persona**: Select **David Miller (`CUST004`)**
* **Prompt**:
  ```text
  My card was charged $149 for order ORD1005 but the order failed and I need this sorted immediately!
  ```
* **Multi-Agent Execution**:
  1. **Supervisor Agent** detects high urgency and financial distress (`PAYMENT_GATEWAY_ANOMALY`).
  2. **Triage Agent** executes `lookup_order("ORD1005")` and `lookup_payment("ORD1005")`, observing payment status `failed` with error code `card_declined / gateway_timeout`.
  3. **Escalation Agent** automatically triggers `create_support_ticket`:
     - Department: `Billing & Payment Operations`
     - Priority: `high` or `urgent` (with expedited 4-hour SLA deadline)
     - Ticket Reference: `TCK-xxxx`
  4. **Supervisor Alert**: Ticket is logged on the `/admin` Operations Desk, and an alert is raised under the Root Cause / Incident panel.
* **Expected Outcome**:
  - Structured support ticket `TCK-xxxx` created with assigned specialist and SLA deadline.
  - Reassuring, empathetic tone explaining that billing operations will review the bank trace.
  - Ticket immediately visible on the Supervisor Desk board (`http://localhost:3000/admin`).

---

### Test 4: Return Authorization, UPS Pre-Paid Label & CSAT Rating
* **Active Customer Persona**: Select **Charlie Brown (`CUST003`)**
* **Prompt**:
  ```text
  I received my order ORD1001 but the headphones have a buzzing noise. Can I return them?
  ```
* **Multi-Agent Execution**:
  1. **Supervisor Agent** invokes `lookup_order("ORD1001")` and `check_return_eligibility("ORD1001")`.
  2. **Eligibility Verification**: Order was delivered 9 days ago (within the standard 30-day return window). Item condition qualifies for return.
  3. **Action Agent** calls `request_return(order_id="ORD1001", reason="Defective - buzzing sound")`.
  4. Generates a formal return authorization ID (`RET-xxxx`) and pre-paid return shipping label (`UPS-LABEL-RET-xxxx`).
  5. Explains return instructions: pack item, affix label, and drop off at any authorized carrier depot for inspection and refund processing.
  6. **CSAT Star Rating Widget**: Appears underneath the resolution card.
* **Expected Outcome**:
  - Official Return ID (`RET-xxxx`) and return label issued.
  - Follow-up check: *"Is there anything else I can help you with today?"*
  - Rating the transaction with 5 stars persists the score and increases the Average CSAT Rating KPI on `/admin`.

---

### Test 5: Dynamic Policy Hot-Reload & Conversational Lifecycle Completion
* **Part A: Supervisor Policy Update**
  1. Open the **Supervisor Desk** at `http://localhost:3000/admin`.
  2. In the **Policy Knowledge Base** section, find the **Return Policy** (`KB001`).
  3. Click **Edit Policy**, change the return window from `30 days` to `60 days`, and click **Save Changes**.
* **Part B: Customer Chat Invalidation Test**
  1. Return to the AI Support Chat (`http://localhost:3000`).
  2. Ask:
     ```text
     What is your current return policy window?
     ```
  3. **Expected Outcome**: The AI immediately cites the updated **60-day** window retrieved dynamically from the active knowledge base without requiring a server reboot!
* **Part C: Warm Conversational Lifecycle Completion**
  1. Send a closing message:
     ```text
     No, that's everything. Thank you so much for your help!
     ```
  2. **Expected Outcome**: The AI recognizes the satisfaction and closing sentiment, gracefully terminating the session with a warm goodbye (e.g., *"You're very welcome! Thank you for choosing NextStore. Have a wonderful day!"*).

---

## 🔄 Supervisor Desk Database Reset

During comprehensive testing, orders are cancelled, returns are created, and support tickets are logged. To instantly restore the database to its pristine demo baseline:
1. Navigate to `http://localhost:3000/admin`.
2. In the header bar, click **"Reset Demo DB"** (located next to "Refresh Data").
3. Confirm the prompt to restore all orders, customers, tickets, return requests, and CSAT scores to their original baseline state.

