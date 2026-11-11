# NextSupport AI — Conceptual System Design and Architecture Specification

## 1. Executive Summary & Design Principles

The **NextSupport AI (PS-04)** platform is an enterprise-grade, autonomous conversational customer support architecture engineered to resolve post-purchase e-commerce inquiries. It replaces monolithic, unconstrained chatbots with a **hierarchical multi-agent state graph** governed by strict privilege separation, stateful thread checkpointing, two-phase confirmation guards, and human-in-the-loop (HITL) escalation mechanisms.

```text
+----------------------------------------------------------------------------------------------------+
|                                      Core Design Principles                                        |
+----------------------------------------------------------------------------------------------------+
| 1. Least Privilege Tool Isolation: Read-only investigative tools are strictly segregated from      |
|    destructive transactional mutation tools.                                                       |
| 2. Two-Phase Interactive Confirmation: Destructive mutations (cancellations/refunds) cannot        |
|    execute in a single turn without explicit customer UI card affirmation.                         |
| 3. Episodic Memory Checkpointing: Graph states are serialized at node boundaries, enabling         |
|    zero-loss multi-turn anaphora resolution and human-in-the-loop workflow resumption.              |
| 4. Deterministic Offline Resiliency: Complete functional dual-mode support—cloud agentic via       |
|    Google Gemini and 100% offline rule-based supervisor execution when API keys are absent.        |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Five-Tier System Architecture

The system is decoupled across five cohesive architectural tiers, ensuring linear scalability, high maintainability, and enterprise security:

```text
+----------------------------------------------------------------------------------------------------+
| Tier 1: Presentation Tier (Next.js 14, React, Tailwind CSS)                                       |
| Storefront Catalog | Support Chat Drawer | Confirmation Cards | Ops Desk (/admin) | Customer Inbox |
+----------------------------------------------------------------------------------------------------+
                                                  | HTTP / JSON REST (Port 3000 -> 8000)
                                                  v
+----------------------------------------------------------------------------------------------------+
| Tier 2: API Gateway & Session Orchestration (FastAPI Async)                                        |
| Pydantic Schema Validation | Persona Context Injection | Route Handlers | CORS & Rate Limiting     |
+----------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
| Tier 3: Hierarchical Multi-Agent State Machine (LangGraph & Gemini)                                |
| Master Supervisor (Router) | Support Triage Agent | Action Agent | Escalation & Ticket Agent        |
+----------------------------------------------------------------------------------------------------+
                                                  | Tool Execution Protocols
                                                  v
+----------------------------------------------------------------------------------------------------+
| Tier 4: Guarded Tool Modules & Policy Engine                                                       |
| Investigation Tools (Read) | Action Tools (Write/Guarded) | Ticket Tools | Policy Rules & Anomaly  |
+----------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
| Tier 5: Ephemeral Data & State Checkpoint Persistence                                              |
| LangGraph MemorySaver (Session RAM) | In-Memory Database (Customers, Orders, Payments, Tickets)   |
+----------------------------------------------------------------------------------------------------+
```

### Tier 1: Presentation Tier (Client)
- **Storefront & Dynamic Catalog**: Next.js 14 client rendering product listings, shopping cart, and live order tracking.
- **Support Chat Drawer**: Collapsible conversational interface with multi-turn message history, optimistic UI rendering, and customer sentiment awareness.
- **Interactive Action Cards**: Specialized UI widgets prompting two-phase confirmation (`Yes, Cancel Order` / `Keep Order`) and CSAT star rating widgets.
- **Supervisor Operations Desk (`/admin`)**: Administrative operations center featuring real-time KPI telemetry, an interactive Kanban ticket board, an anomaly alert feed, and a live policy editor.
- **Customer Notification Center**: In-app inbox receiving asynchronous updates when human specialists resolve escalated tickets.

### Tier 2: API Gateway & Routing Tier
- Built on **FastAPI (v0.100+)** delivering high-throughput asynchronous request handling.
- Validates inbound payloads using strict **Pydantic v2 schemas**.
- Dynamically extracts customer session headers (`X-Customer-Id`) via the **Persona Switcher** to ground dialogues in active customer records.
- Dispatches requests across dedicated route controllers (`ecommerce_routes.py`, `action_routes.py`, `ticket_routes.py`, `admin_routes.py`, `notification_routes.py`).

### Tier 3: Hierarchical Multi-Agent State Machine Tier
- Governed by **LangGraph cyclic state graphs** backed by Google Gemini 3.5 Flash-Lite function calling.
- **Master Supervisor Agent**: Evaluates conversational intent, detects urgency/sentiment, inspects thread history, and dynamically delegates to specialized domain subgraphs.
- **Support Triage Agent**: ReAct subagent dedicated to non-destructive order diagnostics, payment inspections, and policy lookups.
- **Action Execution Agent**: ReAct subagent executing transactional updates locked behind confirmation guards.
- **Escalation & Ticket Agent**: ReAct subagent managing human handoffs, SLA deadline calculations, and incident tracking.

### Tier 4: Tool Execution & Policy Engine Tier
- **Read-Only Investigative Tools**: `lookup_order`, `lookup_payment`, `lookup_customer`, `search_knowledge_base`, `check_return_eligibility`.
- **Guarded Action Mutation Tools**: `cancel_order`, `request_return`, `initiate_refund`.
- **Escalation & Telemetry Tools**: `create_support_ticket`, `update_ticket_status`, `search_tickets`, `record_csat_rating`, `get_resolution_metrics`.
- **Policy Engine (`policy_rules.py`)**: Programmatic business rule validator enforcing return windows (30 days), non-returnable categories, high-value transaction review ($200 cap), and gateway anomaly triggers.

### Tier 5: Ephemeral Data & State Persistence Tier
- **LangGraph `MemorySaver`**: In-memory episodic checkpointer storing serialized execution states keyed by `session_id` / `thread_id`.
- **In-Memory Operational Mock Database (`mock_data.py`)**: Strongly typed data structures maintaining customers, products, orders, payments, tickets, notifications, and CSAT scores with realistic relative timestamps.

---

## 3. System Architecture & Component Diagrams

### 3.1 End-to-End System Architecture

The following diagram illustrates the complete end-to-end component interaction flow across all architectural tiers:

```mermaid
flowchart TD
    subgraph ClientTier["Tier 1: Presentation Layer (Next.js 14)"]
        UI_Store["E-Commerce Storefront\n(Dynamic Catalog & Cart)"]
        UI_Chat["Support Chat Drawer\n(Multi-Turn Dialogue UI)"]
        UI_Guard["Interactive Cards\n(Confirmation & CSAT)"]
        UI_Admin["Supervisor Ops Desk (/admin)\n(KPIs, Kanban, Policy Editor)"]
        UI_Inbox["Customer Inbox\n(Specialist Ticket Alerts)"]
    end

    subgraph GatewayTier["Tier 2: API Gateway Layer (FastAPI Async)"]
        API_Router{"API Route Dispatcher"}
        MW_Persona["Customer Persona Injector\n(CUST001 - CUST999)"]
        MW_Schema["Pydantic Schema Validation"]
    end

    subgraph AgentTier["Tier 3: Multi-Agent State Machine (LangGraph)"]
        SUP["1. Master Supervisor Agent\n(Dynamic Intent & Sentiment Router)"]
        TRIAGE["2. Support Triage Agent\n(Non-destructive Diagnostics)"]
        ACTION["3. Action Execution Agent\n(Two-Phase Guarded Mutations)"]
        ESCALATE["4. Escalation & Ticket Agent\n(Human Handoff & SLAs)"]
    end

    subgraph ToolTier["Tier 4: Guarded Tools & Policy Engine"]
        T_Read["Read-Only Tools:\n- lookup_order\n- lookup_payment\n- lookup_customer\n- search_knowledge_base\n- check_return_eligibility"]
        T_Write["Guarded Mutation Tools:\n- cancel_order\n- request_return\n- initiate_refund"]
        T_Esc["Ticket & Metric Tools:\n- create_support_ticket\n- update_ticket_status\n- record_csat_rating"]
        PE["Policy & Anomaly Rules Engine:\n- Return Window (30 Days)\n- High-Value Cap ($200)\n- PAYMENT_GATEWAY_ANOMALY"]
    end

    subgraph StorageTier["Tier 5: Data & Memory Storage"]
        MEM["LangGraph MemorySaver\n(Episodic Session Thread Checkpointer)"]
        MOCK_DB[("In-Memory Database:\n- CUSTOMERS (5 Personas)\n- ORDERS (ORD1001-ORD1006)\n- PAYMENTS (PAY2001-PAY2006)\n- TICKETS & NOTIFICATIONS\n- 12 KB Policy Articles")]
    end

    %% Client to Gateway
    UI_Chat -->|"POST /api/chat"| API_Router
    UI_Guard -->|"POST /api/confirm-action"| API_Router
    UI_Admin -->|"GET/PUT /api/admin/*"| API_Router
    UI_Inbox -->|"GET /api/notifications"| API_Router

    %% Gateway to State Machine
    API_Router --> MW_Persona
    MW_Persona --> MW_Schema
    MW_Schema --> SUP

    %% Supervisor Delegation
    SUP -->|"Read / Diagnostic Intent"| TRIAGE
    SUP -->|"Transactional Intent"| ACTION
    SUP -->|"Escalation / Dispute Intent"| ESCALATE

    %% Agents to Tools
    TRIAGE --> T_Read
    ACTION --> PE
    PE -->|"Policy Validated"| T_Write
    ESCALATE --> T_Esc

    %% Tools to Storage
    T_Read --> MOCK_DB
    T_Write --> MOCK_DB
    T_Esc --> MOCK_DB
    SUP <-->|"State Checkpointing"| MEM

    %% Escalation and Notifications Feedback
    T_Esc -.->|"Push Updates"| UI_Inbox
    T_Esc -.->|"Sync Kanban"| UI_Admin

    classDef client fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef gateway fill:#ede7f6,stroke:#512da8,stroke-width:2px;
    classDef agent fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef tools fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    classDef storage fill:#fce4ec,stroke:#c2185b,stroke-width:2px;

    class UI_Store,UI_Chat,UI_Guard,UI_Admin,UI_Inbox client;
    class API_Router,MW_Persona,MW_Schema gateway;
    class SUP,TRIAGE,ACTION,ESCALATE agent;
    class T_Read,T_Write,T_Esc,PE tools;
    class MEM,MOCK_DB storage;
```

![Figure 1: Conceptual End-to-End System Architecture](./figures/figure1_system_architecture.jpg)

> **Figure 1:** Conceptual End-to-End System Architecture illustrating presentation components, API routing, multi-agent state machines, guarded tool modules, and in-memory persistence.

---

### 3.2 LangGraph State Machine & Agent Routing Workflow

The state machine is modeled as a cyclic state graph compiling conditional edges based on conversational intent, execution status, and safety policy checks:

```mermaid
stateDiagram-v2
    [*] --> START
    START --> SupervisorNode: User Prompt + Thread State

    state SupervisorNode {
        [*] --> IngestContext
        IngestContext --> ClassifyIntent
        ClassifyIntent --> CheckAnaphora: Resolve 'it', 'my order'
        CheckAnaphora --> AssessSentiment: Gauge Urgency / Frustration
    }

    SupervisorNode --> TriageAgentNode: Intent = Track / FAQ / Payment Check
    SupervisorNode --> ActionAgentNode: Intent = Cancel / Return / Refund
    SupervisorNode --> EscalationAgentNode: Intent = Manager / Dispute / Threat
    SupervisorNode --> END: General Greeting / Direct Answer

    state TriageAgentNode {
        [*] --> ExecuteReadTools
        ExecuteReadTools --> InspectOrder: lookup_order(order_id)
        ExecuteReadTools --> InspectPayment: lookup_payment(payment_id)
        ExecuteReadTools --> SearchKB: search_knowledge_base(query)
        InspectOrder --> SynthesizeDiagnosis
        InspectPayment --> SynthesizeDiagnosis
        SearchKB --> SynthesizeDiagnosis
    }

    TriageAgentNode --> EscalationAgentNode: Payment Anomaly / Complex Failure
    TriageAgentNode --> END: Query Resolved & Synthesized

    state ActionAgentNode {
        [*] --> EvaluatePolicyRules
        EvaluatePolicyRules --> CheckEligibility: check_return_eligibility()
        CheckEligibility --> VerifyConfirmation
        state VerifyConfirmation <<choice>>
        VerifyConfirmation --> PromptConfirmationCard: Unconfirmed Action (decision = confirmation_required)
        VerifyConfirmation --> ExecuteMutation: Customer Confirmed (decision = execute)
        ExecuteMutation --> cancel_order
        ExecuteMutation --> request_return
        ExecuteMutation --> initiate_refund
    }

    ActionAgentNode --> EscalationAgentNode: Policy Exception / >$200 High Value
    ActionAgentNode --> END: Return Label Generated / Action Complete / Card Emitted

    state EscalationAgentNode {
        [*] --> CalculateSLA: VIP=2h, High=4h, Std=8h
        CalculateSLA --> RouteDepartment: Billing / Logistics / Tech Support
        RouteDepartment --> create_support_ticket
        create_support_ticket --> DispatchNotification: Push to Customer Inbox
        DispatchNotification --> UpdateAdminKanban: Append to /admin board
    }

    EscalationAgentNode --> END: Ticket ID & SLA Confirmation Presented
```

![Figure 2: LangGraph State Machine & Agent Routing Workflow](./figures/figure2_fsm_state_machine.jpg)

> **Figure 2:** LangGraph Multi-Agent State Machine Workflow showing conditional routing across Supervisor, Triage, Action, and Escalation nodes.

---

### 3.3 Two-Phase Interactive Confirmation Sequence Diagram

Destructive transactional mutations are safeguarded by a two-phase confirmation protocol. The diagram below traces the interaction lifecycle when a customer requests an order cancellation:

```mermaid
sequenceDiagram
    autonumber
    actor Customer as Customer (NextStore Chat)
    participant ChatUI as Support Chat Drawer
    participant Gateway as FastAPI Gateway
    participant Supervisor as Master Supervisor
    participant ActionAgent as Action Execution Agent
    participant PolicyEngine as Policy Engine (policy_rules.py)
    participant Database as Mock Database (mock_data.py)

    Note over Customer,Database: Phase 1: Request & Confirmation Requirement
    Customer->>ChatUI: "Please cancel order ORD1001"
    ChatUI->>Gateway: POST /api/chat {message, session_id, customer_id}
    Gateway->>Supervisor: Ingest prompt & resolve entity (order_id="ORD1001")
    Supervisor->>ActionAgent: Delegate cancellation workflow
    ActionAgent->>PolicyEngine: cancel_review("ORD1001")
    PolicyEngine->>Database: Verify order status == "processing"
    Database-->>PolicyEngine: Status confirmed: "processing"
    PolicyEngine-->>ActionAgent: Policy Pass: Cancellation Eligible
    Note over ActionAgent: Check Confirmation State:\nNo prior customer token found
    ActionAgent-->>Supervisor: decision="confirmation_required", order_id="ORD1001"
    Supervisor-->>Gateway: Return state payload with pending_confirmation
    Gateway-->>ChatUI: 200 OK + Assistant Message + Confirmation Card Payload
    ChatUI->>Customer: Display Interactive Card: "Are you sure you want to cancel ORD1001?" [Yes, Cancel] [No, Keep]

    Note over Customer,Database: Phase 2: Affirmation & Transactional Execution
    Customer->>ChatUI: Clicks [Yes, Cancel]
    ChatUI->>Gateway: POST /api/confirm-action {action: "cancel_order", order_id: "ORD1001", confirmed: true}
    Gateway->>ActionAgent: Execute confirmed tool: cancel_order("ORD1001")
    ActionAgent->>Database: Mutate status: ORD1001 -> "cancelled"
    Database-->>ActionAgent: Mutation Success: ORD1001 cancelled
    ActionAgent-->>Gateway: {success: true, message: "Order ORD1001 has been cancelled successfully."}
    Gateway-->>ChatUI: 200 OK + Final Cancellation Confirmation
    ChatUI->>Customer: "Order ORD1001 has been cancelled. A confirmation receipt has been sent."
```

![Figure 3: Two-Phase Interactive Confirmation Sequence Diagram](./figures/figure3_two_phase_confirmation_sequence.jpg)

> **Figure 3:** Two-Phase Interactive Confirmation Sequence Diagram for destructive database operations.

---

### 3.4 Automated Escalation & Incident Management Workflow

When automated diagnosis encounters systemic failures or policy barriers, the system escalates cases seamlessly without losing context:

```mermaid
sequenceDiagram
    autonumber
    actor Customer as Customer (Charlie Davis - CUST003)
    participant ChatUI as Support Chat Drawer
    participant Gateway as FastAPI Gateway
    participant Triage as Support Triage Agent
    participant AnomalyEngine as Anomaly Monitor
    participant Escalation as Escalation & Ticket Agent
    participant OpsDesk as Supervisor Desk (/admin)
    participant Inbox as Customer Notification Inbox

    Customer->>ChatUI: "My payment for ORD1003 was debited but status says failed!"
    ChatUI->>Gateway: POST /api/chat {session_id, customer_id="CUST003"}
    Gateway->>Triage: Investigate payment record PAY2003
    Triage->>AnomalyEngine: Evaluate payment transaction stream
    Note over AnomalyEngine: Anomaly Check: 3+ failures in 1h window\nFlag: PAYMENT_GATEWAY_ANOMALY
    AnomalyEngine-->>Triage: Incident Alert Triggered
    Triage->>Escalation: Trigger automated handoff with incident diagnostics
    Note over Escalation: Calculate SLA:\nCustomer Tier: Standard\nPriority: High (Financial Debit)\nTarget SLA: 4 Hours
    Escalation->>OpsDesk: Create Support Ticket: TCK-8042 (Dept: Billing, Priority: High)
    Escalation->>Inbox: Dispatch Notification: "Support Ticket #TCK-8042 opened. SLA: 4 hours."
    Escalation-->>Gateway: Assistant response with Ticket ID and SLA guarantee
    Gateway-->>ChatUI: Deliver empathetic response + Ticket reference
    ChatUI->>Customer: "I have escalated this to our Senior Billing Team under Ticket #TCK-8042 (SLA: 4 hours)."

    Note over OpsDesk,Inbox: Human-in-the-Loop (HITL) Resolution
    actor Specialist as Human Billing Specialist
    Specialist->>OpsDesk: Inspects Kanban Board, selects TCK-8042
    Specialist->>OpsDesk: Enters resolution note: "Reconciled with payment gateway; order released."
    OpsDesk->>Gateway: PUT /api/admin/tickets/TCK-8042 {status: "resolved"}
    Gateway->>Inbox: Push resolved notification to customer inbox
    Customer->>Inbox: Views real-time resolution update in notification tray
```

![Figure 4: Automated Escalation & Incident Management Workflow](./figures/figure4_escalation_workflow.jpg)

> **Figure 4:** Sequence Diagram illustrating anomaly discovery, ticket generation with tier-based SLA, and HITL specialist resolution.

---

### 3.5 Entity-Relationship Diagram (ERD)

The data model for the in-memory enterprise database is structured as follows:

```mermaid
erDiagram
    CUSTOMERS ||--o{ ORDERS : places
    CUSTOMERS ||--o{ TICKETS : opens
    CUSTOMERS ||--o{ NOTIFICATIONS : receives
    CUSTOMERS ||--o{ CSAT_RATINGS : submits
    ORDERS ||--|| PAYMENTS : settled_by
    ORDERS ||--o{ ORDER_ITEMS : contains
    PRODUCTS ||--o{ ORDER_ITEMS : referenced_in
    ORDERS ||--o{ TICKETS : relates_to
    TICKETS ||--o{ NOTIFICATIONS : generates

    CUSTOMERS {
        string id PK "e.g., CUST001"
        string name "Customer Full Name"
        string email "alice@example.com"
        string tier "vip | premium | standard"
        string subscription "active | expired | none"
        string phone "+1-555-0101"
        string account_status "active | suspended"
        datetime joined_date "ISO 8601"
    }

    PRODUCTS {
        string id PK "e.g., PROD001"
        string name "Noise-Canceling Headphones"
        string category "Electronics"
        float price "129.99"
        int stock "45"
    }

    ORDERS {
        string id PK "e.g., ORD1001"
        string customer_id FK "References CUSTOMERS.id"
        float total_amount "Total Order Cost"
        string status "processing | shipped | delivered | cancelled | payment_failed"
        datetime created_at "ISO 8601"
        string carrier "FedEx | UPS | USPS"
        string tracking_id "TRK-9823412"
        string delivery_eta "Estimated Delivery Date"
    }

    ORDER_ITEMS {
        string order_id FK "References ORDERS.id"
        string product_id FK "References PRODUCTS.id"
        string product_name "Snapshot Name"
        int quantity "Item Quantity"
        float unit_price "Unit Purchase Price"
    }

    PAYMENTS {
        string payment_id PK "e.g., PAY2001"
        string order_id FK "References ORDERS.id"
        string customer_id FK "References CUSTOMERS.id"
        float amount "Transaction Amount"
        string status "completed | pending | failed"
        string method "Credit Card | PayPal"
        datetime created_at "ISO 8601"
        string failure_reason "Optional Gateway Error"
    }

    TICKETS {
        string id PK "e.g., TCK-101"
        string customer_id FK "References CUSTOMERS.id"
        string order_id FK "References ORDERS.id"
        string category "billing | logistics | return | general"
        string priority "urgent | high | medium | low"
        string status "open | assigned | in_progress | resolved | closed"
        string target_team "Billing | Logistics | Senior Support"
        datetime sla_deadline "Calculated Target Deadline"
        string escalation_reason "Diagnosis Summary"
        string resolution_notes "Human Specialist Notes"
        datetime created_at "ISO 8601"
    }

    NOTIFICATIONS {
        string id PK "UUID"
        string customer_id FK "References CUSTOMERS.id"
        string ticket_id FK "References TICKETS.id"
        string title "Notification Header"
        string message "Notification Body"
        string type "ticket_created | ticket_resolved | general"
        boolean read "true | false"
        datetime created_at "ISO 8601"
    }

    CSAT_RATINGS {
        string id PK "UUID"
        string session_id "Thread Session Identifier"
        string customer_id FK "References CUSTOMERS.id"
        int rating "1 to 5 Stars"
        string feedback "Optional Written Remarks"
        datetime created_at "ISO 8601"
    }

    KB_POLICIES {
        string id PK "POL-01 to POL-12"
        string intent "returns | shipping | warranty"
        string title "Policy Header"
        string guidance "Canonical Operational Rules"
        string keywords "Search Index Terms"
    }
```

![Figure 5: Entity-Relationship Diagram (ERD)](./figures/figure5_entity_relationship_diagram.jpg)

> **Figure 5:** Entity-Relationship Diagram detailing relational keys, foreign references, and attributes across mock data collections.

---

## 4. State Management & Schema Contracts

### 4.1 LangGraph State Schema (`SupportAgentState`)

The state shared across all nodes within the LangGraph state machine is strictly typed using `typing.TypedDict` and annotated message reducers:

```python
class SupportAgentState(TypedDict, total=False):
    # Core Message History (Annotated reducer appends new turns)
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Session & Customer Context
    session_id: str
    user_message: str
    customer_id: Optional[str]
    order_id: Optional[str]
    
    # Agent Routing & Intent Classification
    active_agent: Optional[str]        # 'triage_agent' | 'action_agent' | 'escalation_agent'
    intent: Optional[str]              # 'order_status' | 'cancel' | 'return' | 'escalation'
    sentiment: Optional[str]           # 'positive' | 'neutral' | 'frustrated' | 'urgent'
    priority: Optional[str]            # 'urgent' | 'high' | 'medium' | 'low'
    
    # Tool Evidence & Intermediate Data
    investigation: Optional[Dict[str, Any]]
    knowledge_results: Optional[List[Dict[str, Any]]]
    action_result: Optional[Dict[str, Any]]
    
    # Safety Guards & Confirmation State
    pending_confirmation: Optional[Dict[str, Any]]  # Stores {action, order_id, params}
    decision: Optional[str]                         # 'confirmation_required' | 'execute' | 'escalate'
    
    # Ticket & Escalation Data
    ticket: Optional[Dict[str, Any]]
    escalation_reason: Optional[str]
    target_team: Optional[str]
    policy_ref: Optional[str]
    
    # Output Synthesis
    assistant_message: str
```

### 4.2 REST API Interface Contracts

| Endpoint | Method | Input Payload | Output Response | Function / Purpose |
| :--- | :---: | :--- | :--- | :--- |
| `/api/chat` | `POST` | `{message: str, session_id: str, customer_id: str}` | `{response: str, active_agent: str, pending_confirmation: dict, ticket: dict}` | Core conversation turn submission and multi-agent synthesis. |
| `/api/confirm-action` | `POST` | `{action: str, order_id: str, confirmed: bool, session_id: str}` | `{success: bool, message: str, updated_order: dict}` | Submits user confirmation for two-phase guarded operations. |
| `/api/customers/{id}` | `GET` | *Path parameter: `id`* | `{customer: dict, active_orders: list, past_tickets: list}` | Retrieves customer context and order history for persona switching. |
| `/api/notifications` | `GET` | `?customer_id=CUST001` | `{notifications: list, unread_count: int}` | Fetches in-app customer notification tray items. |
| `/api/admin/metrics` | `GET` | *None* | `{total_tickets: int, auto_resolution_rate: float, escalation_rate: float, csat_avg: float}` | Real-time KPI feed for the Supervisor Operations Desk. |
| `/api/admin/tickets` | `GET/PUT` | `PUT: {ticket_id: str, status: str, resolution_notes: str}` | `{updated_ticket: dict}` | Fetches Kanban board tickets and supports human specialist case closure. |
| `/api/admin/policies` | `GET/POST` | `POST: {policy_id: str, guidance: str}` | `{policies: list, status: "updated"}` | Runtime hot-reloading of enterprise business policies. |

---

## 5. Security Boundaries, Safety Guards, and Resilience

```text
+----------------------------------------------------------------------------------------------------+
|                                    System Defense-in-Depth                                         |
+----------------------------------------------------------------------------------------------------+
| [Level 1: Least Privilege] Read tools cannot alter state; write tools locked behind policy.        |
| [Level 2: Interactive Guard] Irreversible operations halt for user UI confirmation.                |
| [Level 3: Policy Limits] Strict caps ($200 high-value threshold, 30-day return window).            |
| [Level 4: Anomaly Detection] Automated monitoring flags systemic failures (PAYMENT_GATEWAY_ANOMALY)|
| [Level 5: Dual-Mode Resilience] Deterministic offline fallback engine guarantees zero downtime.    |
+----------------------------------------------------------------------------------------------------+
```

### 5.1 Privilege Separation & Two-Phase Confirmation Guard
- **Read/Write Tool Isolation**: Investigative tools (`lookup_order`, `lookup_payment`, `search_knowledge_base`) operate in strict read-only mode and do not possess database update handles. Action tools (`cancel_order`, `request_return`, `initiate_refund`) reside in a segregated module.
- **Two-Phase Interactive Card Guard**: The Action Execution Agent is programmatically prohibited from executing mutations on the initial request. When an action intent is detected, the graph transitions to `decision='confirmation_required'`, halts tool execution, and returns structured metadata prompting the frontend to render an interactive confirmation card. The database mutation is only triggered once the user submits explicit affirmation via `/api/confirm-action`.

### 5.2 Deterministic Offline Fallback Architecture
To ensure continuous operation without cloud dependency, rate limit failures, or credential expiration:
- When `GEMINI_API_KEY` is present, the backend utilizes `ChatGoogleGenerativeAI` with function calling.
- When `GEMINI_API_KEY` is omitted or cloud connectivity degrades, the system initializes `build_deterministic_support_graph()`.
- The deterministic supervisor utilizes regex entity extractors (`ORDER_ID_RE`, `CUSTOMER_ID_RE`, `AFFIRMATIVE_RE`, `NEGATIVE_RE`) and routing tables to execute identical tool sequences, state checkpointing, and ticket generation with **100% feature parity and zero downtime**.

### 5.3 Anomaly Incident Detection & Operational Telemetry
- An automated anomaly detection engine monitors transaction logs in `mock_data.py`.
- If three or more payment failures occur within a rolling time window, the system automatically registers a `PAYMENT_GATEWAY_ANOMALY`.
- When an anomaly is detected, customer support requests regarding payment status are automatically prioritized, high-urgency tags are assigned, and operations incident alerts are pushed directly to the `/admin` Operations Desk.

---

## 6. Architectural Summary

The **NextSupport AI (PS-04)** architectural design establishes a robust, enterprise-grade paradigm for autonomous conversational customer support. By replacing monolithic, unconstrained conversational chatbots with a **hierarchical multi-agent state graph**, the system achieves an optimal balance between conversational fluidity, rigorous business policy enforcement, and transactional database safety.

```text
+----------------------------------------------------------------------------------------------------+
|                                  Architectural Summary Matrix                                      |
+----------------------------------------------------------------------------------------------------+
| Architectural Dimension   | Technical Implementation              | Operational Benefit            |
|---------------------------+---------------------------------------+--------------------------------|
| Orchestration & Routing   | LangGraph Master Supervisor Graph     | Eliminates unstructured chatter|
|                           |                                       | & guarantees clear delegation  |
| Transactional Safety      | Two-Phase Interactive Confirmation    | Prevents accidental or         |
|                           | Cards & Strict Privilege Boundaries   | hallucinated database writes   |
| Multi-Turn Memory         | LangGraph MemorySaver Checkpointing   | Resolves anaphoric pronouns    |
|                           |                                       | ("it", "my order") across turns|
| Policy Grounding          | 12-Policy Grounded Engine with Live   | Eliminates policy hallucination|
|                           | Runtime Admin Hot-Reloading           | with zero-downtime updates     |
| Human Handoff & Tracking  | 5-Stage Kanban Ticket Lifecycle &     | Enforces tier-based SLAs and   |
|                           | Direct Customer Inbox Notifications   | closes the escalation loop     |
| Incident Telemetry        | Automated Anomaly Discovery           | Flags systemic incidents       |
|                           | (PAYMENT_GATEWAY_ANOMALY)             | directly to operations staff   |
| Fault Tolerance           | Deterministic Regex & Pattern Engine  | 100% offline uptime & zero     |
|                           |                                       | dependency on cloud API keys   |
+----------------------------------------------------------------------------------------------------+
```

### Key Architectural Takeaways

1. **Guarded Multi-Agent Decomposition**: The system successfully segregates responsibilities across specialized functional nodes: non-destructive diagnostics (Triage), policy-constrained transactional execution (Action), and SLA-driven human handoffs (Escalation). This modular design prevents prompt distraction and enforces least-privilege tool execution.
2. **Deterministic Safety over Stochastic Execution**: While Large Language Models provide natural language understanding, transactional database state changes are strictly gated by programmatic policy engines (`policy_rules.py`) and explicit, two-phase human confirmation prompts.
3. **Continuous State & Anaphora Persistence**: Utilizing episodic graph checkpointing ensures that conversation state is serialized at every step, allowing users to refer naturally to past items, orders, or topics without context loss.
4. **End-to-End Operational Integration**: Beyond customer-facing chat, the architecture integrates full operational lifecycle management—featuring real-time supervisor KPI telemetry, Kanban-based specialist resolution, and automated incident alerting.
5. **Production Resiliency**: The dual-mode engine ensures that NextSupport AI operates reliably under all conditions: providing rich generative dialogue when cloud LLM APIs are accessible, and seamlessly falling back to a deterministic state machine for offline reliability, automated unit testing, and business continuity.

