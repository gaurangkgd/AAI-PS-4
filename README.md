

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
  1. **Supervisor Agent** inspects `CUST001`'s order history via `lookup_order` and discovers pending order `ORD1002` (Thermal Water Bottle x2, `$49.90`, status: `processing`).
  2. **Confirmation Guard** activates: Because order cancellation is an irreversible destructive action, the AI does *not* immediately execute it. Instead, it presents an interactive confirmation card with two buttons (`Confirm Cancellation` / `Keep Order`). Once you answer, the buttons lock.
  3. **User Action**: Click **"Confirm Cancellation"** (or type `"yes"`).
  4. **Action Agent** calls `cancel_order(order_id="ORD1002")`, changing the order status to `cancelled`. A message also lands in Alice's Inbox, and the **Linked Orders** panel and the chat header update to `cancelled` within seconds (they are live, not hardcoded).
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
* **Active Customer Persona**: Select **Diana Lee (`CUST004`)**
* **Prompt**:
  ```text
  My card was charged $149 for order ORD1005 but the order failed and I need this sorted immediately!
  ```
* **Multi-Agent Execution**:
  1. **Supervisor Agent** detects high urgency and financial distress (`PAYMENT_GATEWAY_ANOMALY`).
  2. **Triage Agent** executes `lookup_order("ORD1005")` and `lookup_payment("ORD1005")`, observing order status `pending_payment` and payment `PAY2005` still `pending`.
  3. **Escalation Agent** automatically triggers `create_support_ticket`:
     - Department: `Billing Support`
     - Priority: `high` (VIP tier gets a 2-hour SLA deadline)
     - Ticket Reference: `TKT-xxxxxxxx`
  4. **Supervisor Alert**: Ticket is logged on the `/admin` Operations Desk, and an alert is raised under the Root Cause / Incident panel.
* **Expected Outcome**:
  - Structured support ticket `TKT-xxxxxxxx` created with team and SLA deadline. The chat says the answer will arrive in the customer's **Inbox**.
  - Reassuring, empathetic tone explaining that billing operations will review the bank trace.
  - Ticket immediately visible on the Supervisor Desk board (`http://localhost:3000/admin`). Click **Take Case** to finish the loop (see *Human-in-the-Loop* below).

---

### Test 4: Return Authorization, UPS Pre-Paid Label & CSAT Rating
* **Active Customer Persona**: Select **Alice Johnson (`CUST001`)**
* **Prompt**:
  ```text
  I received my order ORD1001 but the headphones have a buzzing noise. Can I return them?
  ```
* **Multi-Agent Execution**:
  1. **Supervisor Agent** invokes `lookup_order("ORD1001")` and `check_return_eligibility("ORD1001")`.
  2. **Eligibility Verification**: Order was delivered 9 days ago (within the standard 30-day return window). Item condition qualifies for return.
  3. **Action Agent** calls `request_return(order_id="ORD1001", reason="Defective - buzzing sound")`.
  4. Generates a formal return authorization ID (`RET-xxxxxxxx`) and a pre-paid return label tracking number.
  5. Explains return instructions: pack item, affix label, and drop off at any authorized carrier depot for inspection and refund processing.
  6. **CSAT Star Rating Widget**: Appears underneath the resolution card.
* **Expected Outcome**:
  - Official Return ID (`RET-xxxxxxxx`) and return label issued (also posted to Alice's Inbox).
  - Follow-up check: *"Is there anything else I can help you with today?"*
  - Rating the transaction with 5 stars persists the score and increases the Average CSAT Rating KPI on `/admin`.

---

### Test 5: Dynamic Policy Hot-Reload & Conversational Lifecycle Completion
* **Part A: Supervisor Policy Update**
  1. Open the **Supervisor Desk** at `http://localhost:3000/admin`.
  2. In the **AI Policies & Rules** tab, find **Return Window Policy** (`KB-RET-003`).
  3. Click **Edit Policy**, change `30 days` to `60 days` in the guidance, and click **Save & Publish to AI**.
* **Part B: Customer Chat Invalidation Test**
  1. Return to the AI Support Chat (`http://localhost:3000`).
  2. Ask:
     ```text
     What is your current return policy window?
     ```
  3. **Expected Outcome**: The AI immediately cites the updated **60-day** window retrieved dynamically from the active knowledge base without requiring a server reboot! The 60 also changes real behaviour: see Test 6 below.
* **Part C: Warm Conversational Lifecycle Completion**
  1. Send a closing message:
     ```text
     No, that's everything. Thank you so much for your help!
     ```
  2. **Expected Outcome**: The AI recognizes the satisfaction and closing sentiment, gracefully terminating the session with a warm goodbye (e.g., *"You're very welcome! Thank you for choosing NextStore. Have a wonderful day!"*).

---

---

### Test 6: Human-in-the-Loop, Return Outside the Window (the hot-reload payoff)
* **Active Customer Persona**: **Bob Smith (`CUST002`)**
* **Prompt**: `I want to return my hoodie from order ORD1006`
* **Expected Outcome**:
  - ORD1006 was delivered 45 days ago, outside the 30-day window, so the AI does **not** approve or refuse. It opens a ticket for **Senior Support** and says the answer will arrive in Bob's Inbox.
  - Now edit `KB-RET-003` to say `60 days` (as in Test 5), click **New Chat**, and send the same prompt again. The return is **auto-approved** (45 days is inside 60). The policy edit changed the AI's decision, not just its wording.

---

## 🛒 Cart & Demo Checkout

1. Browse `/products`, click **Add to Cart** on any card (or inside the product popup). The navbar **Cart** badge counts items.
2. Open `/cart` to change quantities or remove lines, then **Proceed to Checkout**.
3. On `/checkout` pick the customer you are ordering as, edit the address, choose a payment method, and press **Pay $X**. This is a **demo gateway**: nothing is charged and no card details are collected.
4. A success screen shows the new order (`ORD1007`, ...) with a transaction reference. Stock drops, the order appears under **My Orders** as `processing`, and a confirmation lands in the Inbox. The new order can then be cancelled through the AI chat.
5. Tick **Simulate a payment failure** to create a `payment_failed` order instead. Ask the AI about it to trigger the payment human-review flow below.

---

## 🧑‍💼 Human-in-the-Loop (HITL)

The AI agents answer what they can verify. When policy says a human must decide, or when no policy matches, the Escalation Agent opens a ticket and the customer is told the answer will arrive in their **Inbox** (`My Orders > Inbox`, also the navbar **Inbox** link with an unread badge).

**Supervisor Desk flow (`/admin` > Support Tickets):**
1. Click **Take Case** on an `open` ticket. The customer is told a specialist took it, and a popup opens with the full case file: what the customer said, why the AI escalated, the governing policy, customer tier, order and payments, and case history.
2. Type the final answer in the response box.
3. Click **Resolve & Send to Customer** at the bottom. The ticket becomes `resolved` and the answer appears in the customer's Inbox, where they can rate it 1-5 stars (feeds the CSAT KPI).
4. Cases you took but did not finish show **Open Case** to continue later.

**Cases that go to a human** (each is a policy in the *AI Policies & Rules* tab with an ID):

| # | Case | Policy | Team | Try this (persona) |
|---|------|--------|------|--------------------|
| 1 | Payment deducted but order failed / pending | KB-HR-001 | Billing | `My card was charged $149 for order ORD1005 but the order failed` (Diana) |
| 2 | Duplicate / double charge | KB-HR-002 | Billing | `I was charged twice for order ORD1001` (Alice) |
| 3 | Suspected fraud / unauthorized charge | KB-HR-003 | Senior (urgent) | `I did not authorize this charge, it looks like fraud` (Diana) |
| 4 | Delivered-but-not-received / lost package | KB-HR-004 | Logistics | `Order ORD1003 never arrived and the tracking is stuck` (Bob) |
| 5 | Cancel or return of an order of $200 or more | KB-HR-005 | Senior | Buy 2 headphones ($259.98), then ask `Can you cancel my order?` |
| 6 | Return outside the return window | KB-HR-006 | Senior | `I want to return my hoodie from order ORD1006` (Bob) |
| 7 | Safety hazard or legal threat | KB-HR-007 | Senior (urgent) | `My headphones from ORD1001 are overheating and smoking` (Alice) |
| 8 | Missing or delayed refund | KB-HR-008 | Billing | `My refund for order ORD1001 has not been received yet` (Alice) |
| 9 | No matching policy (AI must not guess) | KB-HR-009 | Senior | `Can you gift wrap my purchase and add a handwritten note?` (Evan) |
| 10 | Customer asks for a human | n/a | Senior | `I want to speak with a human manager` |

Thresholds are read from the policies themselves: edit `$200` in KB-HR-005 or `30 days` in KB-RET-003 and the AI's behaviour changes immediately. Reset Demo DB restores the original policies.

---

## 🎬 Human Review Demo Playbook

Use this section to demo the "AI first, human for the final decision" story. Every case below follows the same loop, so you can run two or three of them live rather than all ten.

**The loop (about 90 seconds per case):**
1. **Customer side** (`/support`): pick the persona, send the prompt. The chat replies that a human will decide, names the ticket (`TKT-xxxxxxxx`), and says **"Why a human is involved: ..."**.
2. **Supervisor side** (`/admin`): the ticket is at the top of **Support Tickets** as `open`. Click **Take Case**. The popup shows the customer's words, the AI's reason, the governing policy and the order and payment facts.
3. Type the human decision in the response box (suggested replies below) and click **Resolve & Send to Customer**.
4. **Customer side again**: the navbar **Inbox** badge shows a new message. Open **My Orders > Inbox**, read the specialist's reply, and rate it with the stars. The CSAT number on `/admin` moves.

Run **Reset Demo DB** on `/admin` before a fresh demo so ticket numbers and policies start clean. Asking about the same order and issue twice while its ticket is still active replies "already tracked under Ticket..." instead of creating a duplicate; that is intended.

### Case-by-case script

| # | Persona | Prompt to send | Ticket you should see | Suggested human reply |
|---|---------|----------------|-----------------------|-----------------------|
| 1 | Diana Lee (`CUST004`) | `My card was charged $149 for order ORD1005 but the order failed and I need this sorted immediately!` | Billing Support, `high`, `payment_issue`, order `ORD1005`, 2-hour SLA (VIP) | "I checked the gateway trace: the charge is a pending authorization and will drop off in 3 business days. Your order stays reserved, and you can pay again now without waiting." |
| 2 | Alice Johnson (`CUST001`) | `I was charged twice for order ORD1001` | Billing Support, `high`, `payment_issue`, order `ORD1001` | "Confirmed: one duplicate charge. We reversed it today, and your bank should show it within 5 to 7 business days." |
| 3 | Diana Lee (`CUST004`) | `I did not authorize this charge, it looks like fraud` | Senior Support, `urgent`, `fraud_dispute` | "We have frozen the payment method on file and opened a fraud review. Please change your password, and watch for an email from our security team." |
| 4 | Bob Smith (`CUST002`) | `Order ORD1003 never arrived and the tracking is stuck` | Logistics Support, `high`, `delivery_dispute`, order `ORD1003` (a new ticket, separate from the seeded tracking one) | "The courier lost the parcel in transit. We are shipping a replacement keyboard today at no cost; tracking will arrive by email." |
| 5 | Evan Wright (`CUST999`) | First buy 2x Wireless Noise-Canceling Headphones ($259.98) via the cart, then in chat: `Can you cancel my order?` | Senior Support, `high`, `high_value_approval`; the AI does not even ask for the usual yes/no confirmation | "Approved. The order was cancelled and the full $259.98 goes back to your original payment method." |
| 6 | Bob Smith (`CUST002`) | `I want to return my hoodie from order ORD1006` | Senior Support, `medium`, `return_exception` (delivered 45 days ago, window is 30) | "This is outside our 30-day window, but as a one-time goodwill exception we approved the return. Use the prepaid label sent to you." |
| 7 | Alice Johnson (`CUST001`) | `My headphones from ORD1001 are overheating and smoking` | Senior Support, `urgent`, `safety_or_legal` | "Please stop using the headphones right away. We are sending a prepaid return box and a full replacement, and our safety team will contact you." |
| 8 | Alice Johnson (`CUST001`) | `My refund for order ORD1001 has not been received yet` | Billing Support, `high`, `refund_dispute`, order `ORD1001` | "We traced the refund with your bank: it was issued on the 20th and is in their clearing queue. It will post within 2 business days." |
| 9 | Evan Wright (`CUST999`) | `Can you gift wrap my purchase and add a handwritten note?` | Senior Support, `medium`, `unresolved_query`: the AI says it found no policy and will not guess | "Gift wrapping with a handwritten note is not offered yet, but we have noted your request for the product team." |
| 10 | Any | `I want to speak with a human manager` | Senior Support, `high`, `human_request` | "Hi, I am the support manager. I have reviewed your account and I am here to help. Please tell me what went wrong." |

### Demo tips

- **Best 3-case run (about 5 minutes):** case 1 (money problem), case 6 (policy exception) and case 9 (the AI refuses to guess). Finish with the policy edit below.
- **Policy edit wow moment:** after case 6, open the **AI Policies & Rules** tab, edit **Return Window Policy** (`KB-RET-003`) from `30 days` to `60 days`, click **New Chat**, and send the case 6 prompt again as Bob. The AI now approves the return by itself, because 45 days is inside 60. Reset the DB afterwards to put `30 days` back.
- **High-value threshold:** edit the `$200` in `KB-HR-005` to a higher number and case 5 stops going to a human.
- **Failure cases from checkout:** tick **Simulate a payment failure** at checkout, then ask the chat `My card was charged for the order I just placed but it failed`; this runs case 1 on an order you just created.
- **What to point out to the audience:** the AI never promises a refund or a fix on these cases. It states why a human is needed, cites the policy ID, and hands over a full case file, so the human can decide in one popup.

---

## 🔄 Supervisor Desk Database Reset

During comprehensive testing, orders are cancelled, returns are created, and support tickets are logged. To instantly restore the database to its pristine demo baseline:
1. Navigate to `http://localhost:3000/admin`.
2. In the header bar, click **"Reset Demo DB"** (located next to "Refresh Data").
3. Confirm the prompt to restore orders (including ones placed through checkout), product stock, tickets, Inbox messages, return requests, CSAT scores and AI policies to their original baseline state. The cart lives in your browser; use **Clear cart** if needed.

