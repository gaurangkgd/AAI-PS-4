# NextSupport AI — Autonomous Agentic Customer Support System (PS-04)

## Problem Definition

Traditional e-commerce customer support systems predominantly rely on rigid decision trees, keyword-triggered FAQs, and static rule-based chatbots. When shoppers encounter common post-purchase dilemmas—such as delayed deliveries, return authorizations, payment discrepancies, and order cancellations—they are forced to navigate brittle menu trees that fail to grasp conversational nuances, multi-turn contexts, or evolving customer intent.

Existing conversational bot solutions struggle with context retention across multiple turns, frequently suffering from anaphoric amnesia (losing track of references like *"it"* or *"my order"*). More critically, conventional Retrieval-Augmented Generation (RAG) and standalone Large Language Model (LLM) chatbots lack secure, real-time bindings to operational databases. In unconstrained environments, naive LLM bots pose severe operational risks: they can hallucinate non-existent refund guarantees or execute destructive, irreversible transactional actions (e.g., immediate database cancellations) without human verification or policy validation. Furthermore, when complex issues or payment gateway failures arise, traditional systems fail to capture structured diagnostic logs or escalate cases systematically to human support staff.

Therefore, there is an urgent need for an intelligent, autonomous agentic customer support platform capable of understanding conversational dialogue, verifying customer identity and entitlements, diagnosing order and payment anomalies, executing policy-compliant transactional operations behind strict safety guardrails, and managing human escalations with clear Service Level Agreements (SLAs).

**NextSupport AI (PS-04)** addresses this challenge by introducing an enterprise-grade, hierarchical multi-agent customer support architecture powered by LangGraph ReAct state machines, FastAPI, Google Gemini, and Next.js 14. The platform transforms unstructured customer complaints into deterministic, policy-governed resolution workflows. It guarantees strict multi-turn state retention, enforces interactive two-phase confirmation guards for destructive mutations, detects systemic gateway anomalies, and provides complete human-in-the-loop (HITL) operational oversight.

---

## Project Scope

The scope of NextSupport AI is to design, develop, and evaluate an autonomous, multi-agent conversational customer support system that serves as an intelligent customer service and operations layer over an e-commerce platform. The system ingests natural language customer queries across the post-purchase lifecycle and orchestrates specialized autonomous agents to investigate records, answer policy questions, execute guarded modifications, collect customer satisfaction metrics, and escalate unresolved incidents to human specialists.

The project encompasses the following core functional modules:

### 1. Multi-Turn Conversation Understanding & Intent Routing
- Ingest typed natural language queries from an interactive customer chat interface.
- Classify customer intent dynamically across critical domains: order tracking, return eligibility, order cancellation, payment disputes, warranty inquiries, policy FAQs, and human escalation requests.
- Detect customer sentiment (e.g., neutral, frustrated, urgent) to dynamically elevate ticket urgency and adjust agent conversational tone.
- Perform robust anaphoric pronoun resolution across conversational turns (e.g., resolving *"cancel it"* or *"what is its tracking number?"* to previously discussed order IDs).

### 2. Customer Context & Persona Grounding
- Authenticate and bind user sessions to distinct customer profiles via a realistic persona switcher (VIP, Premium, Standard, and Expired subscription tiers).
- Retrieve customer history, purchase tier benefits, past support interactions, and active order records to personalize resolution strategies.
- Enforce tier-specific Service Level Agreements (SLAs), granting expedited handling to high-tier customers.

### 3. Policy Retrieval & Knowledge Base Guidance
- Index and retrieve official enterprise policies across 12 distinct operational guides (return windows, non-returnable categories, warranty terms, shipping timeframes, payment dispute protocols, and cancellation rules).
- Ground conversational responses in verified knowledge base entries to prevent policy hallucination.
- Support runtime policy hot-reloading by administrators without requiring server restarts.

### 4. Diagnostic Troubleshooting & Order Investigation
- Perform non-destructive read operations to inspect real-time order states (`processing`, `shipped`, `delivered`, `cancelled`, `payment_failed`).
- Correlate carrier tracking codes (FedEx, UPS, USPS) with delivery timelines and flag transit delays.
- Cross-reference payment transaction logs (`completed`, `pending`, `failed`) and provide transparent diagnostic explanations for checkout failures.

### 5. Guarded Action Execution & Two-Phase Confirmation
- Execute guarded transactional mutations: order cancellations, return label generations, and refund authorizations.
- Enforce strict two-phase interactive confirmation safety guards: destructive mutations cannot execute in a single prompt and instead present interactive confirmation UI cards (`Yes, Confirm` / `No, Cancel`).
- Validate hard business policy rules before execution (e.g., verifying that an order is in `processing` status prior to cancellation, checking the 30-day return window, and enforcing a $200 high-value threshold requiring human manager review).

### 6. Automated Escalation & Structured Ticket Lifecycle Management
- Automatically trigger escalation workflows when automated resolution is unviable (e.g., repeated payment gateway anomalies, customer requests for human supervisors, or policy exceptions).
- Generate structured support tickets containing unique ticket IDs, affected order IDs, customer tiers, calculated SLA deadlines, assigned departments (Billing, Logistics, Tech Support), and issue summaries.
- Track tickets across a complete five-stage lifecycle: `open` &rarr; `assigned` &rarr; `in_progress` &rarr; `resolved` &rarr; `closed`.
- Provide bidirectional updates, dispatching resolution notices to the customer's personal notification inbox.

### 7. Root Cause Discovery & Anomaly Detection
- Monitor transaction failure rates and courier transit logs to detect systemic anomalies in real time.
- Flag operational alerts (e.g., `PAYMENT_GATEWAY_ANOMALY`) when recurring payment drop-offs occur, shielding support agents from redundant manual triage.

### 8. Customer Satisfaction (CSAT) & Sentiment Feedback
- Provide an interactive 5-star rating and written feedback submission widget upon conversation conclusion.
- Compute rolling CSAT averages and feed ratings into operations telemetry.

### 9. Full-Stack Web Interface & Supervisor Operations Desk
- Deliver a modern storefront interface built with Next.js 14 and Tailwind CSS, featuring product catalogs, order investigation drawers, and an interactive AI chat interface.
- Provide a dedicated Supervisor Operations Desk (`/admin`) displaying real-time KPI metrics (Auto-Resolution Rate %, Escalation Rate %, Average CSAT, SLA Breaches), an interactive Kanban ticket board, and a human-in-the-loop (HITL) resolution modal.

---

## Project Boundaries

- **In-Memory Demonstration Dataset**: The system operates on a predefined, strongly typed in-memory mock dataset (`backend/mock_data.py`) spanning 5 customer personas, 6 products, 6 realistic multi-state orders, 6 payment transactions, and initial support tickets.
- **Zero Financial Transactions**: All order operations, payment records, and refund disbursements are simulated mock transactions for safe academic demonstration; no real banking networks, payment gateways, or credit card charges are touched.
- **Simulated Logistics Tracking**: Carrier parcel tracking (FedEx, UPS, USPS) relies on simulated event histories and timestamps rather than live commercial carrier webhooks.
- **Ephemeral State Persistence**: Thread states, ticket updates, and newly created return records reside in RAM (managed by LangGraph `MemorySaver`) and reset upon server restart.
- **Deterministic Offline Fallback Engine**: While the primary system uses Google Gemini 3.5 Flash-Lite function calling for conversational intelligence, a deterministic pattern-matching engine is fully integrated to guarantee 100% functionality and offline testability when API keys are absent or rate limits are reached.
- **Monolingual Focus**: Conversational understanding, policy retrieval, and agent dialogue are optimized exclusively for English natural language interactions.

---

## Project Objectives

1. **To develop** an autonomous, multi-agent conversational customer support platform capable of understanding unstructured natural language queries across the post-purchase e-commerce lifecycle.
2. **To implement** a hierarchical multi-agent architecture utilizing LangGraph ReAct state machines to coordinate specialized agents (Supervisor, Triage, Action Execution, and Escalation).
3. **To eliminate conversational amnesia** by integrating thread-level state checkpointing (`MemorySaver`) that automatically resolves anaphoric pronouns and maintains context across multi-turn dialogues.
4. **To ground agent guidance in verified policies**, indexing 12 enterprise knowledge base documents to eliminate policy hallucination while supporting live runtime policy hot-reloading.
5. **To implement deterministic two-phase confirmation guards** that prevent unauthorized or accidental database mutations during destructive operations (order cancellations and refunds).
6. **To automate intelligent diagnostic investigations**, allowing non-destructive inspection of live order statuses, carrier tracking events, and payment transaction logs.
7. **To engineer a systematic escalation and ticket tracking subsystem** that dynamically assigns departments, priorities, and tier-based SLA resolution deadlines (VIP: 2h, High: 4h, Standard: 8h).
8. **To provide systemic operational monitoring** through automated root cause discovery that detects and flags payment gateway anomalies in real time.
9. **To construct a full-stack user and supervisory experience**, incorporating a responsive Next.js 14 customer portal with persona switching and an administrative operations desk (`/admin`) with real-time KPI telemetry and Kanban lifecycle management.
10. **To validate system reliability and safety** through a comprehensive test suite of automated unit and integration tests, coupled with a deterministic offline fallback engine ensuring zero downtime.
