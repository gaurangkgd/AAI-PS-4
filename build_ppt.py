"""
Builds an enterprise-grade 10-slide PowerPoint presentation for NextSupport AI (PS-04).
Widescreen 16:9 format with custom styling, figures, and structured layouts.
"""

import os
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# Color Palette
DARK_BG = RGBColor(15, 23, 42)       # Slate 900
DARK_CARD = RGBColor(30, 41, 59)     # Slate 800
LIGHT_BG = RGBColor(255, 255, 255)   # White
LIGHT_CARD = RGBColor(248, 250, 252) # Slate 50
CARD_BORDER = RGBColor(226, 232, 240)# Slate 200
ACCENT_BLUE = RGBColor(14, 165, 233) # Sky 500
ACCENT_EMERALD = RGBColor(16, 185, 129) # Emerald 500
ACCENT_AMBER = RGBColor(245, 158, 11)   # Amber 500
ACCENT_ROSE = RGBColor(244, 63, 94)     # Rose 500
TEXT_MAIN = RGBColor(15, 23, 42)     # Slate 900
TEXT_MUTED = RGBColor(71, 85, 105)   # Slate 600
TEXT_LIGHT = RGBColor(241, 245, 249) # Slate 100
TEXT_LIGHT_MUTED = RGBColor(148, 163, 184) # Slate 400

FIGURES_DIR = Path("figures")

def add_header(slide, title_text, category_text, dark=False):
    # Category tag
    tb_cat = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
    p_cat = tb_cat.text_frame.paragraphs[0]
    p_cat.text = category_text.upper()
    p_cat.font.size = Pt(10)
    p_cat.font.bold = True
    p_cat.font.color.rgb = ACCENT_BLUE if dark else RGBColor(2, 132, 199)
    p_cat.font.name = "Arial"

    # Main Title
    tb_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.65))
    p_title = tb_title.text_frame.paragraphs[0]
    p_title.text = title_text
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = TEXT_LIGHT if dark else TEXT_MAIN
    p_title.font.name = "Arial"

def add_box(slide, left, top, width, height, bg_color=LIGHT_CARD, border_color=CARD_BORDER):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.2)
    else:
        shape.line.fill.background()
    return shape

# ==========================================
# SLIDE 1: Title Slide (Dark Theme)
# ==========================================
slide1 = prs.slides.add_slide(prs.slide_layouts[6])
bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
bg1.fill.solid()
bg1.fill.fore_color.rgb = DARK_BG
bg1.line.fill.background()

# Badge
badge = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.9), Inches(0.8), Inches(3.2), Inches(0.4))
badge.fill.solid()
badge.fill.fore_color.rgb = RGBColor(30, 41, 59)
badge.line.color.rgb = ACCENT_BLUE
badge.line.width = Pt(1)
p = badge.text_frame.paragraphs[0]
p.text = "PS-04 CAPSTONE SPECIFICATION"
p.font.size = Pt(10)
p.font.bold = True
p.font.color.rgb = ACCENT_BLUE
p.font.name = "Arial"
p.alignment = PP_ALIGN.CENTER

# Main Titles
tb = slide1.shapes.add_textbox(Inches(0.9), Inches(1.35), Inches(11.5), Inches(1.5))
tf = tb.text_frame
tf.word_wrap = True
p1 = tf.paragraphs[0]
p1.text = "NextSupport AI"
p1.font.size = Pt(40)
p1.font.bold = True
p1.font.color.rgb = TEXT_LIGHT
p1.font.name = "Arial"

p2 = tf.add_paragraph()
p2.text = "Autonomous Multi-Agent Customer Support System"
p2.font.size = Pt(22)
p2.font.bold = True
p2.font.color.rgb = ACCENT_BLUE
p2.font.name = "Arial"
p2.space_before = Pt(4)

p3 = tf.add_paragraph()
p3.text = "Bridging Generative AI Empathy with Deterministic Transactional Guardrails for Modern E-Commerce"
p3.font.size = Pt(14)
p3.font.color.rgb = TEXT_LIGHT_MUTED
p3.font.name = "Arial"
p3.space_before = Pt(8)

# Narrative Box
narrative1 = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.9), Inches(3.2), Inches(11.5), Inches(1.8))
narrative1.fill.solid()
narrative1.fill.fore_color.rgb = DARK_CARD
narrative1.line.color.rgb = RGBColor(51, 65, 85)
tf_n1 = narrative1.text_frame
tf_n1.word_wrap = True
tf_n1.margin_left = Inches(0.3)
tf_n1.margin_top = Inches(0.25)
tf_n1.margin_right = Inches(0.3)

pn1_title = tf_n1.paragraphs[0]
pn1_title.text = "EXECUTIVE VISION & PROBLEM LANDSCAPE"
pn1_title.font.size = Pt(11)
pn1_title.font.bold = True
pn1_title.font.color.rgb = ACCENT_BLUE

pn1_body = tf_n1.add_paragraph()
pn1_body.text = (
    "Customer support in digital commerce faces a classic dilemma: human helpdesks are slow and expensive "
    "to scale, while traditional chatbots frustrate shoppers with rigid, unhelpful menu trees. NextSupport AI "
    "introduces an enterprise-grade multi-agent architecture built on LangGraph, FastAPI, Google Gemini, and Next.js 14. "
    "It autonomously handles multi-turn support dialogues, executes non-destructive order diagnostics, enforces "
    "strict two-phase confirmation guards for destructive mutations, and escalates complex incidents with dynamic SLAs."
)
pn1_body.font.size = Pt(11.5)
pn1_body.font.color.rgb = TEXT_LIGHT
pn1_body.space_before = Pt(4)

# Metadata Cards (3 columns)
col_width = Inches(3.65)
card_lefts = [Inches(0.9), Inches(4.82), Inches(8.75)]

m_cards = [
    ("ACADEMIC STATEMENT", "Problem: PS-04\nSubject: Agentic AI & Enterprise Automation", ACCENT_BLUE),
    ("DEVELOPMENT TEAM", "Team: Soham Kamathi, Gaurav Khutwal,\nGaurang Gade, Shivam Jha", ACCENT_EMERALD),
    ("SYSTEM VERIFICATION", "Automated Tests: 37/37 Passed (100%)\nArchitecture: Dual-Mode (Cloud + Offline)", ACCENT_AMBER),
]

for i, (m_title, m_desc, m_color) in enumerate(m_cards):
    c_box = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, card_lefts[i], Inches(5.25), col_width, Inches(1.5))
    c_box.fill.solid()
    c_box.fill.fore_color.rgb = DARK_CARD
    c_box.line.color.rgb = m_color
    c_box.line.width = Pt(1.2)
    tf_c = c_box.text_frame
    tf_c.word_wrap = True
    tf_c.margin_left = Inches(0.2)
    tf_c.margin_top = Inches(0.2)
    
    pt = tf_c.paragraphs[0]
    pt.text = m_title
    pt.font.size = Pt(10)
    pt.font.bold = True
    pt.font.color.rgb = m_color
    
    pd = tf_c.add_paragraph()
    pd.text = m_desc
    pd.font.size = Pt(11)
    pd.font.color.rgb = TEXT_LIGHT
    pd.space_before = Pt(4)

# ==========================================
# SLIDE 2: Business & Technical Problem
# ==========================================
slide2 = prs.slides.add_slide(prs.slide_layouts[6])
add_header(slide2, "The Trillion-Dollar Support Dilemma: Why Current Systems Fail", "Problem Context & Operational Reality")

# Narrative Box
n2 = add_box(slide2, Inches(0.8), Inches(1.4), Inches(11.73), Inches(1.0), RGBColor(241, 245, 249), RGBColor(203, 213, 225))
tf_n2 = n2.text_frame
tf_n2.word_wrap = True
tf_n2.margin_left = Inches(0.25)
tf_n2.margin_top = Inches(0.15)
p_n2 = tf_n2.paragraphs[0]
p_n2.text = (
    "Modern e-commerce platforms process immense transaction volumes across order tracking, returns, cancellations, "
    "and payment disputes. Yet existing customer service tooling fails on two distinct fronts: ballooning operational costs "
    "for human helpdesks, and severe technological unreliability in automated chatbots."
)
p_n2.font.size = Pt(11.5)
p_n2.font.color.rgb = TEXT_MAIN

# Left Box: Business Pain
box_l = add_box(slide2, Inches(0.8), Inches(2.6), Inches(5.7), Inches(4.3), RGBColor(254, 242, 242), RGBColor(252, 165, 165))
tf_l = box_l.text_frame
tf_l.word_wrap = True
tf_l.margin_left = Inches(0.25)
tf_l.margin_top = Inches(0.2)

p_lt = tf_l.paragraphs[0]
p_lt.text = "🚨 THE BUSINESS & FINANCIAL BOTTLENECK"
p_lt.font.size = Pt(13)
p_lt.font.bold = True
p_lt.font.color.rgb = ACCENT_ROSE

items_l = [
    ("High Operational Overhead", "Human agent tickets cost enterprises between $8.00 and $25.00 per case, making peak holiday volume scaling economically unfeasible."),
    ("Severe Customer Churn", "Industry benchmarks show 68% of consumers switch brands after a single poor support experience involving repetitive transfers or slow resolution."),
    ("Operational Incident Blind Spots", "Frontline support queues spike exponentially when payment gateways fail, leaving DevOps and logistics teams unaware of systemic root causes.")
]
for title, desc in items_l:
    p_t = tf_l.add_paragraph()
    p_t.text = f"• {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(11)
    p_t.font.color.rgb = TEXT_MAIN
    p_t.space_before = Pt(8)
    p_d = tf_l.add_paragraph()
    p_d.text = f"  {desc}"
    p_d.font.size = Pt(10.5)
    p_d.font.color.rgb = TEXT_MUTED

# Right Box: Technical Failure Modes
box_r = add_box(slide2, Inches(6.83), Inches(2.6), Inches(5.7), Inches(4.3), RGBColor(254, 243, 199), RGBColor(252, 211, 77))
tf_r = box_r.text_frame
tf_r.word_wrap = True
tf_r.margin_left = Inches(0.25)
tf_r.margin_top = Inches(0.2)

p_rt = tf_r.paragraphs[0]
p_rt.text = "⚠️ THE TECHNOLOGICAL FAILURE MODES"
p_rt.font.size = Pt(13)
p_rt.font.bold = True
p_rt.font.color.rgb = RGBColor(180, 83, 9)

items_r = [
    ("Brittle Scripted Chatbots", "Static IVRs and keyword-based decision trees degrade when customers use colloquial phrasing, trapping shoppers in frustrating circular dead-ends."),
    ("Conversational State Amnesia", "Standalone LLMs evaluate each turn in isolation, immediately losing antecedent context (forgetting order IDs when users refer to 'it' or 'my order')."),
    ("Catastrophic Destructive Execution", "LLMs given direct tool access hallucinate warranty rules and can trigger irreversible state mutations (cancelling paid orders or issuing refunds) without verification.")
]
for title, desc in items_r:
    p_t = tf_r.add_paragraph()
    p_t.text = f"• {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(11)
    p_t.font.color.rgb = TEXT_MAIN
    p_t.space_before = Pt(8)
    p_d = tf_r.add_paragraph()
    p_d.text = f"  {desc}"
    p_d.font.size = Pt(10.5)
    p_d.font.color.rgb = TEXT_MUTED

# ==========================================
# SLIDE 3: Proposed Solution
# ==========================================
slide3 = prs.slides.add_slide(prs.slide_layouts[6])
add_header(slide3, "NextSupport AI: Guarded Autonomy for Customer Experience", "Proposed Solution & Value Proposition")

n3 = add_box(slide3, Inches(0.8), Inches(1.4), Inches(11.73), Inches(0.9), RGBColor(240, 249, 255), RGBColor(186, 230, 253))
tf_n3 = n3.text_frame
tf_n3.word_wrap = True
tf_n3.margin_left = Inches(0.25)
tf_n3.margin_top = Inches(0.12)
p_n3 = tf_n3.paragraphs[0]
p_n3.text = (
    "NextSupport AI replaces fragile single-prompt bots with a hierarchical multi-agent state graph. "
    "It decouples customer inquiries into specialized subgraphs, pairing natural language fluency with strict business policy "
    "validation and two-phase transactional confirmation safety."
)
p_n3.font.size = Pt(11.5)
p_n3.font.color.rgb = TEXT_MAIN

# 4 Key Pillars (Grid 2x2)
p_coords = [
    (Inches(0.8), Inches(2.45), Inches(5.7), Inches(2.1)),
    (Inches(6.83), Inches(2.45), Inches(5.7), Inches(2.1)),
    (Inches(0.8), Inches(4.7), Inches(5.7), Inches(2.1)),
    (Inches(6.83), Inches(4.7), Inches(5.7), Inches(2.1)),
]

pillars = [
    ("🎯 78.4% Autonomous Self-Service Resolution",
     "Autonomously diagnoses parcel tracking, retrieves verified warranty/return policies, and verifies return eligibility without human specialist intervention.",
     ACCENT_BLUE),
    ("🛡️ Zero Unauthorized Database Mutations",
     "Irreversible actions (order cancellations, refunds) are programmatically gated behind two-phase interactive confirmation cards, requiring explicit customer affirmation.",
     ACCENT_EMERALD),
    ("🔄 Continuous Multi-Turn Memory",
     "Employs LangGraph MemorySaver episodic state checkpointing, allowing customers to use pronouns ('Where is it being delivered?', 'Cancel it') without re-entering order IDs.",
     RGBColor(99, 102, 241)),
    ("🚨 Proactive Incident & Anomaly Discovery",
     "Monitors live transaction failure rates to detect systemic PAYMENT_GATEWAY_ANOMALY patterns, generating high-urgency alerts directly on supervisor Kanban desks.",
     ACCENT_AMBER)
]

for (x, y, w, h), (p_title, p_desc, p_col) in zip(p_coords, pillars):
    p_box = add_box(slide3, x, y, w, h, LIGHT_CARD, CARD_BORDER)
    tf_pb = p_box.text_frame
    tf_pb.word_wrap = True
    tf_pb.margin_left = Inches(0.2)
    tf_pb.margin_top = Inches(0.15)
    
    pt = tf_pb.paragraphs[0]
    pt.text = p_title
    pt.font.size = Pt(12.5)
    pt.font.bold = True
    pt.font.color.rgb = p_col
    
    pd = tf_pb.add_paragraph()
    pd.text = p_desc
    pd.font.size = Pt(11)
    pd.font.color.rgb = TEXT_MUTED
    pd.space_before = Pt(4)

# ==========================================
# SLIDE 4: System Architecture & Agent Specialization
# ==========================================
slide4 = prs.slides.add_slide(prs.slide_layouts[6])
add_header(slide4, "Hierarchical Multi-Agent Supervisor Pattern", "Technical Architecture & Agent Specialization")

# Left Column: Agent Roles & Descriptions
box_s4_l = add_box(slide4, Inches(0.8), Inches(1.4), Inches(6.0), Inches(5.6), LIGHT_CARD, CARD_BORDER)
tf_s4_l = box_s4_l.text_frame
tf_s4_l.word_wrap = True
tf_s4_l.margin_left = Inches(0.25)
tf_s4_l.margin_top = Inches(0.15)

p_s4_title = tf_s4_l.paragraphs[0]
p_s4_title.text = "🤖 SPECIALIZED MULTI-AGENT SUBGRAPHS"
p_s4_title.font.size = Pt(12)
p_s4_title.font.bold = True
p_s4_title.font.color.rgb = ACCENT_BLUE

agents = [
    ("1. Master Supervisor Agent", "Evaluates customer intent, detects emotional urgency/sentiment, resolves anaphoric pronouns, and routes requests across domain specialists deterministically."),
    ("2. Support Triage Agent", "Strict read-only permissions. Executes live database diagnostics (lookup_order, lookup_payment, lookup_customer) and searches 12 official policy manuals."),
    ("3. Action Execution Agent", "Governed by two-phase confirmation guards. Validates business policies (30-day window, $200 high-value cap) and executes verified cancellations and return labels."),
    ("4. Escalation & Ticket Agent", "Manages human handoffs. Dynamically assigns SLA resolution targets (VIP: 2h, Standard: 8h), routes to specialized departments (Billing/Logistics), and logs CSAT ratings.")
]

for a_title, a_desc in agents:
    pa_t = tf_s4_l.add_paragraph()
    pa_t.text = a_title
    pa_t.font.bold = True
    pa_t.font.size = Pt(11)
    pa_t.font.color.rgb = TEXT_MAIN
    pa_t.space_before = Pt(6)
    pa_d = tf_s4_l.add_paragraph()
    pa_d.text = a_desc
    pa_d.font.size = Pt(10)
    pa_d.font.color.rgb = TEXT_MUTED

# Right Column: Embed Figure 1
fig1_path = FIGURES_DIR / "figure1_system_architecture.jpg"
if fig1_path.exists():
    slide4.shapes.add_picture(str(fig1_path), Inches(7.0), Inches(1.4), width=Inches(5.53))
else:
    box_s4_r = add_box(slide4, Inches(7.0), Inches(1.4), Inches(5.53), Inches(5.6), LIGHT_CARD, CARD_BORDER)

# ==========================================
# SLIDE 5: Safe Execution & Guardrails
# ==========================================
slide5 = prs.slides.add_slide(prs.slide_layouts[6])
add_header(slide5, "Two-Phase Interactive Confirmation: Zero-Trust Action Execution", "Transactional Safety & Guardrails")

# Left Column: Detailed Step-by-Step
box_s5_l = add_box(slide5, Inches(0.8), Inches(1.4), Inches(6.0), Inches(5.6), LIGHT_CARD, CARD_BORDER)
tf_s5_l = box_s5_l.text_frame
tf_s5_l.word_wrap = True
tf_s5_l.margin_left = Inches(0.25)
tf_s5_l.margin_top = Inches(0.15)

p_s5_title = tf_s5_l.paragraphs[0]
p_s5_title.text = "🔒 THE TWO-PHASE CONFIRMATION PROTOCOL"
p_s5_title.font.size = Pt(12)
p_s5_title.font.bold = True
p_s5_title.font.color.rgb = ACCENT_EMERALD

steps_s5 = [
    ("Phase 1: Guard Evaluation & Prompt Card", "When a customer requests 'Cancel order ORD1001', the Action Agent checks order status in policy_rules.py. Because cancellation is irreversible and no prior token exists, the agent halts execution, sets decision='confirmation_required', and renders an interactive confirmation prompt card."),
    ("Interactive UI Card Prompt", "The chat UI renders: 'Are you sure you want to cancel Order ORD1001?' with interactive buttons [Yes, Cancel Order] and [No, Keep Order]."),
    ("Phase 2: Verified State Mutation", "Only upon receiving the customer's explicit click at /api/confirm-action, the mutation executes: order status updates to 'cancelled', inventory restocks, and a confirmation receipt is issued."),
    ("Hard Policy Enforcement", "Strict business caps: orders exceeding $200 automatically require human manager authorization, and returns beyond 30 days are deterministically rejected with policy citations.")
]

for st_title, st_desc in steps_s5:
    pst = tf_s5_l.add_paragraph()
    pst.text = st_title
    pst.font.bold = True
    pst.font.size = Pt(11)
    pst.font.color.rgb = TEXT_MAIN
    pst.space_before = Pt(6)
    psd = tf_s5_l.add_paragraph()
    psd.text = st_desc
    psd.font.size = Pt(10)
    psd.font.color.rgb = TEXT_MUTED

# Right Column: Embed Figure 3 (Sequence Diagram)
fig3_path = FIGURES_DIR / "figure3_two_phase_confirmation_sequence.jpg"
if fig3_path.exists():
    slide5.shapes.add_picture(str(fig3_path), Inches(7.0), Inches(1.65), width=Inches(5.53))

# ==========================================
# SLIDE 6: Memory & Anaphora Resolution
# ==========================================
slide6 = prs.slides.add_slide(prs.slide_layouts[6])
add_header(slide6, "Eliminating Conversational Amnesia via LangGraph MemorySaver", "Episodic State Checkpointing & Context Retention")

# Left Column: Conversation Turn Walkthrough
box_s6_l = add_box(slide6, Inches(0.8), Inches(1.4), Inches(6.0), Inches(5.6), LIGHT_CARD, CARD_BORDER)
tf_s6_l = box_s6_l.text_frame
tf_s6_l.word_wrap = True
tf_s6_l.margin_left = Inches(0.25)
tf_s6_l.margin_top = Inches(0.15)

p_s6_title = tf_s6_l.paragraphs[0]
p_s6_title.text = "💬 MULTI-TURN ANAPHORIC RESOLUTION IN PRACTICE"
p_s6_title.font.size = Pt(12)
p_s6_title.font.bold = True
p_s6_title.font.color.rgb = RGBColor(99, 102, 241)

turns = [
    ("Turn 1: Explicit Entity Binding", "User: 'Check the shipping details for my order ORD1002.'\nSystem: Triage Agent executes lookup_order('ORD1002') -> binds order_id='ORD1002' into session checkpoint RAM -> reports FedEx tracking number and arrival date."),
    ("Turn 2: Implicit Pronoun Resolution (Location)", "User: 'Where is it being delivered?'\nSystem: Supervisor resolves 'it' to ORD1002 from graph state -> retrieves shipping destination without asking the user to restate the order ID."),
    ("Turn 3: Implicit Pronoun Resolution (Action)", "User: 'Cancel it immediately.'\nSystem: Supervisor resolves 'it' to ORD1002 -> Action Agent checks policy rules -> informs user that shipped orders cannot be cancelled and guides them to the post-delivery return flow."),
    ("Technical Innovation", "Thread variables are saved in episodic MemorySaver checkpoints rather than stuffing raw conversation history repeatedly into LLM prompt contexts, preserving token economics.")
]

for t_title, t_desc in turns:
    pt_t = tf_s6_l.add_paragraph()
    pt_t.text = t_title
    pt_t.font.bold = True
    pt_t.font.size = Pt(11)
    pt_t.font.color.rgb = TEXT_MAIN
    pt_t.space_before = Pt(6)
    pt_d = tf_s6_l.add_paragraph()
    pt_d.text = t_desc
    pt_d.font.size = Pt(10)
    pt_d.font.color.rgb = TEXT_MUTED

# Right Column: Embed Figure 2 (FSM State Machine)
fig2_path = FIGURES_DIR / "figure2_fsm_state_machine.jpg"
if fig2_path.exists():
    slide6.shapes.add_picture(str(fig2_path), Inches(7.0), Inches(1.55), width=Inches(5.53))

# ==========================================
# SLIDE 7: Operations & Anomaly Discovery
# ==========================================
slide7 = prs.slides.add_slide(prs.slide_layouts[6])
add_header(slide7, "Frontline AI as an Early-Warning Sensor Network for Operations", "Root Cause Discovery & The Supervisor Desk (/admin)")

# Left Column: 3 Operational Pillars
box_s7_l = add_box(slide7, Inches(0.8), Inches(1.4), Inches(6.0), Inches(5.6), LIGHT_CARD, CARD_BORDER)
tf_s7_l = box_s7_l.text_frame
tf_s7_l.word_wrap = True
tf_s7_l.margin_left = Inches(0.25)
tf_s7_l.margin_top = Inches(0.15)

p_s7_title = tf_s7_l.paragraphs[0]
p_s7_title.text = "🚨 OPERATIONAL TELEMETRY & ESCALATION"
p_s7_title.font.size = Pt(12)
p_s7_title.font.bold = True
p_s7_title.font.color.rgb = ACCENT_AMBER

s7_items = [
    ("1. Root Cause Anomaly Detection", "An automated background engine monitors live transaction error frequencies. When 3 or more transaction failures occur within a rolling time window, it automatically flags PAYMENT_GATEWAY_ANOMALY, elevating customer disputes on the ops desk."),
    ("2. Dynamic Tier-Based SLA Deadlines", "Support tickets automatically assign resolution deadlines based on customer tiers:\n• VIP Accounts (Diana Lee - CUST004): 2-Hour SLA Target\n• Financial / Payment Debits: 4-Hour SLA Target\n• Standard Inquiries (Bob Smith - CUST002): 8-Hour SLA Target"),
    ("3. Closed-Loop Specialist Resolution", "Human specialists claim cases on the /admin Kanban board with pre-compiled diagnostic traces (order history, payment IDs, policy clauses). Resolving a ticket automatically pushes real-time alerts to the customer's in-app notification center.")
]

for s_title, s_desc in s7_items:
    ps7_t = tf_s7_l.add_paragraph()
    ps7_t.text = s_title
    ps7_t.font.bold = True
    ps7_t.font.size = Pt(11)
    ps7_t.font.color.rgb = TEXT_MAIN
    ps7_t.space_before = Pt(6)
    ps7_d = tf_s7_l.add_paragraph()
    ps7_d.text = s_desc
    ps7_d.font.size = Pt(10)
    ps7_d.font.color.rgb = TEXT_MUTED

# Right Column: Embed Figure 4 (Workflow Diagram)
fig4_path = FIGURES_DIR / "figure4_escalation_workflow.jpg"
if fig4_path.exists():
    slide7.shapes.add_picture(str(fig4_path), Inches(7.0), Inches(1.8), width=Inches(5.53))

# ==========================================
# SLIDE 8: Empirical Validation (Table)
# ==========================================
slide8 = prs.slides.add_slide(prs.slide_layouts[6])
add_header(slide8, "System Validation Across 5 Core Real-World Scenarios", "Empirical Evaluation & Scenario Results")

# Narrative
n8 = add_box(slide8, Inches(0.8), Inches(1.35), Inches(11.73), Inches(0.7), RGBColor(241, 245, 249), RGBColor(203, 213, 225))
p_n8 = n8.text_frame.paragraphs[0]
p_n8.text = "System behavior was verified across 37 automated unit and integration tests and evaluated across 5 core end-to-end scenarios reflecting realistic e-commerce customer support challenges:"
p_n8.font.size = Pt(11)
p_n8.font.color.rgb = TEXT_MAIN

# Table
table_shape = slide8.shapes.add_table(6, 4, Inches(0.8), Inches(2.2), Inches(11.73), Inches(4.0))
table = table_shape.table

# Set Column Widths
table.columns[0].width = Inches(2.3)
table.columns[1].width = Inches(2.5)
table.columns[2].width = Inches(3.2)
table.columns[3].width = Inches(3.73)

headers = ["Scenario Tested", "Customer Prompt / Event", "System Mechanism & Path", "Verified Operational Outcome"]
for col_idx, h_text in enumerate(headers):
    cell = table.cell(0, col_idx)
    cell.fill.solid()
    cell.fill.fore_color.rgb = DARK_CARD
    p = cell.text_frame.paragraphs[0]
    p.text = h_text
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_LIGHT

scenario_rows = [
    ("1. Non-Destructive Tracking", "'Where is order ORD1001?'", "Supervisor -> Triage Agent -> lookup_order()", "Verified FedEx tracking ID & delivery ETA; zero database mutations."),
    ("2. Guarded Cancellation", "'Cancel order ORD1001.'", "Supervisor -> Action Agent -> Two-Phase Guard", "Halted mutation; rendered UI prompt card; cancelled order only on explicit click."),
    ("3. Anaphora Follow-Up", "'Where is it being shipped?'", "Supervisor -> MemorySaver Entity Binding", "Resolved 'it' to ORD1002 across 3 consecutive turns without re-prompting."),
    ("4. High-Value Return Gate", "'Return $280 item in ORD1004.'", "Action Agent -> Policy Engine ($200 Cap)", "Halted automated refund; escalated to Human Manager Review with 4h SLA."),
    ("5. Payment Anomaly Alert", "'Money debited, order failed!'", "Anomaly Monitor -> Escalation Agent", "Flagged PAYMENT_GATEWAY_ANOMALY; created Ticket #TCK-8042 with 4h SLA.")
]

for row_idx, row_data in enumerate(scenario_rows, start=1):
    bg_c = LIGHT_CARD if row_idx % 2 == 1 else RGBColor(255, 255, 255)
    for col_idx, cell_data in enumerate(row_data):
        cell = table.cell(row_idx, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = bg_c
        p = cell.text_frame.paragraphs[0]
        p.text = cell_data
        p.font.size = Pt(10)
        p.font.color.rgb = TEXT_MAIN

# Bottom status banner
b_banner = add_box(slide8, Inches(0.8), Inches(6.4), Inches(11.73), Inches(0.65), RGBColor(236, 253, 245), RGBColor(167, 243, 208))
pb = b_banner.text_frame.paragraphs[0]
pb.text = "🏆 VERIFICATION STATUS: 37/37 Automated Pytest Suites Passed (100% Pass Rate) | 100% Deterministic Offline Fallback Resiliency"
pb.font.bold = True
pb.font.size = Pt(11)
pb.font.color.rgb = ACCENT_EMERALD

# ==========================================
# SLIDE 9: Commercial ROI & Sustainability (SDGs)
# ==========================================
slide9 = prs.slides.add_slide(prs.slide_layouts[6])
add_header(slide9, "Business Economics and Sustainable Development Alignment", "Commercial ROI & UN Sustainability (SDGs)")

col_w9 = Inches(3.65)
col_lefts9 = [Inches(0.8), Inches(4.82), Inches(8.75)]

# Col 1: Commercial ROI
box_roi = add_box(slide9, col_lefts9[0], Inches(1.5), col_w9, Inches(5.4), RGBColor(240, 249, 255), RGBColor(186, 230, 253))
tf_roi = box_roi.text_frame
tf_roi.word_wrap = True
tf_roi.margin_left = Inches(0.2)
tf_roi.margin_top = Inches(0.2)

pt_roi = tf_roi.paragraphs[0]
pt_roi.text = "💰 FINANCIAL VIABILITY & ROI"
pt_roi.font.size = Pt(12)
pt_roi.font.bold = True
pt_roi.font.color.rgb = ACCENT_BLUE

roi_points = [
    ("65% Support Cost Reduction", "Automating tracking lookups, returns, and policy FAQs slashes human ticket volumes by nearly two-thirds."),
    ("Ultra-Low Cost per Ticket", "Operating on Gemini 3.5 Flash-Lite tokens costs ~$0.075 per 1M tokens (<$0.01 per conversation vs. $12.00+ for human labor)."),
    ("Rapid Setup & Low TCO", "Runs efficiently in-memory via lightweight asynchronous microservices without heavy infrastructure overhead.")
]
for t, d in roi_points:
    p_t = tf_roi.add_paragraph()
    p_t.text = f"• {t}:"
    p_t.font.bold = True
    p_t.font.size = Pt(10.5)
    p_t.font.color.rgb = TEXT_MAIN
    p_t.space_before = Pt(8)
    p_d = tf_roi.add_paragraph()
    p_d.text = f"  {d}"
    p_d.font.size = Pt(9.5)
    p_d.font.color.rgb = TEXT_MUTED

# Col 2: UN SDGs
box_sdg = add_box(slide9, col_lefts9[1], Inches(1.5), col_w9, Inches(5.4), RGBColor(236, 253, 245), RGBColor(167, 243, 208))
tf_sdg = box_sdg.text_frame
tf_sdg.word_wrap = True
tf_sdg.margin_left = Inches(0.2)
tf_sdg.margin_top = Inches(0.2)

pt_sdg = tf_sdg.paragraphs[0]
pt_sdg.text = "🌍 UN SUSTAINABLE GOALS (SDGs)"
pt_sdg.font.size = Pt(12)
pt_sdg.font.bold = True
pt_sdg.font.color.rgb = ACCENT_EMERALD

sdg_points = [
    ("SDG 12: Responsible Consumption", "Paperless dispute tracking, digital return authorizations, and condition checking eliminate physical paperwork and reduce reverse-logistics freight emissions."),
    ("SDG 9: Industry & Innovation", "Provides a scalable, fail-safe AI architecture for enterprise e-commerce platforms."),
    ("SDG 8: Decent Work", "Relieves human representatives from repetitive manual triage, transforming them into high-empathy case specialists.")
]
for t, d in sdg_points:
    p_t = tf_sdg.add_paragraph()
    p_t.text = f"• {t}:"
    p_t.font.bold = True
    p_t.font.size = Pt(10.5)
    p_t.font.color.rgb = TEXT_MAIN
    p_t.space_before = Pt(8)
    p_d = tf_sdg.add_paragraph()
    p_d.text = f"  {d}"
    p_d.font.size = Pt(9.5)
    p_d.font.color.rgb = TEXT_MUTED

# Col 3: Roadmap
box_rd = add_box(slide9, col_lefts9[2], Inches(1.5), col_w9, Inches(5.4), RGBColor(254, 243, 199), RGBColor(252, 211, 77))
tf_rd = box_rd.text_frame
tf_rd.word_wrap = True
tf_rd.margin_left = Inches(0.2)
tf_rd.margin_top = Inches(0.2)

pt_rd = tf_rd.paragraphs[0]
pt_rd.text = "🚀 ENTERPRISE ROADMAP"
pt_rd.font.size = Pt(12)
pt_rd.font.bold = True
pt_rd.font.color.rgb = RGBColor(180, 83, 9)

rd_points = [
    ("PostgreSQL & pgvector", "Scale vector indices to search across millions of catalog SKUs and historical support policies."),
    ("Live Webhook Integrations", "Direct API connectivity to logistics couriers (FedEx, UPS) and payment gateways (Stripe, PayPal)."),
    ("Multilingual & Voice Support", "Expand natural language processing to regional languages (Hindi, Spanish) and speech-to-text voice interfaces.")
]
for t, d in rd_points:
    p_t = tf_rd.add_paragraph()
    p_t.text = f"• {t}:"
    p_t.font.bold = True
    p_t.font.size = Pt(10.5)
    p_t.font.color.rgb = TEXT_MAIN
    p_t.space_before = Pt(8)
    p_d = tf_rd.add_paragraph()
    p_d.text = f"  {d}"
    p_d.font.size = Pt(9.5)
    p_d.font.color.rgb = TEXT_MUTED

# ==========================================
# SLIDE 10: Conclusion & Wrap-Up
# ==========================================
slide10 = prs.slides.add_slide(prs.slide_layouts[6])
add_header(slide10, "Setting the Standard for Autonomous Customer Care", "Conclusion & Technical Summary")

# Left Column: Summary of Innovations
box_s10_l = add_box(slide10, Inches(0.8), Inches(1.4), Inches(5.7), Inches(4.6), LIGHT_CARD, CARD_BORDER)
tf_s10_l = box_s10_l.text_frame
tf_s10_l.word_wrap = True
tf_s10_l.margin_left = Inches(0.25)
tf_s10_l.margin_top = Inches(0.18)

pt_s10_l = tf_s10_l.paragraphs[0]
pt_s10_l.text = "🎯 ARCHITECTURAL CONTRIBUTIONS"
pt_s10_l.font.size = Pt(12)
pt_s10_l.font.bold = True
pt_s10_l.font.color.rgb = ACCENT_BLUE

c_innovations = [
    ("Separation of Privilege", "Read-only investigative triage is strictly segregated from guarded transactional mutations."),
    ("Two-Phase Interactive Guards", "Destructive operations halt for user UI confirmation, eliminating accidental state mutations."),
    ("Episodic Graph Checkpointing", "LangGraph MemorySaver ensures full anaphoric pronoun resolution across long sessions."),
    ("Early-Warning Sensor Network", "Transforms customer support complaints into automated DevOps anomaly alerts."),
    ("Dual-Mode Operational Resiliency", "100% offline uptime guaranteed via deterministic fallback engine.")
]
for t, d in c_innovations:
    p_t = tf_s10_l.add_paragraph()
    p_t.text = f"• {t}:"
    p_t.font.bold = True
    p_t.font.size = Pt(10.5)
    p_t.font.color.rgb = TEXT_MAIN
    p_t.space_before = Pt(5)
    p_d = tf_s10_l.add_paragraph()
    p_d.text = f"  {d}"
    p_d.font.size = Pt(9.5)
    p_d.font.color.rgb = TEXT_MUTED

# Right Column: Production Roadmap
box_s10_r = add_box(slide10, Inches(6.83), Inches(1.4), Inches(5.7), Inches(4.6), LIGHT_CARD, CARD_BORDER)
tf_s10_r = box_s10_r.text_frame
tf_s10_r.word_wrap = True
tf_s10_r.margin_left = Inches(0.25)
tf_s10_r.margin_top = Inches(0.18)

pt_s10_r = tf_s10_r.paragraphs[0]
pt_s10_r.text = "🗺️ PRODUCTION READINESS ROADMAP"
pt_s10_r.font.size = Pt(12)
pt_s10_r.font.bold = True
pt_s10_r.font.color.rgb = ACCENT_EMERALD

c_roadmap = [
    ("Enterprise Relational Database Scale", "Migrating from RAM checkpointers to PostgreSQL and pgvector for semantic retrieval across expansive catalogs."),
    ("Live Commercial Carrier & Payment Webhooks", "Connecting live third-party logistics APIs (FedEx, UPS) and payment webhooks (Stripe, PayPal) for banking reconciliation."),
    ("Multilingual Voice & Omnichannel Dispatch", "Deploying speech-to-text models and expanding support channels across mobile apps, WhatsApp, and SMS."),
    ("Distributed Tracing & Telemetry", "Integrating OpenTelemetry and Prometheus to monitor per-agent latency budgets and token consumption in real time.")
]
for t, d in c_roadmap:
    p_t = tf_s10_r.add_paragraph()
    p_t.text = f"• {t}:"
    p_t.font.bold = True
    p_t.font.size = Pt(10.5)
    p_t.font.color.rgb = TEXT_MAIN
    p_t.space_before = Pt(6)
    p_d = tf_s10_r.add_paragraph()
    p_d.text = f"  {d}"
    p_d.font.size = Pt(9.5)
    p_d.font.color.rgb = TEXT_MUTED

# Bottom Banner: Closing Remarks & Q&A
b_close = add_box(slide10, Inches(0.8), Inches(6.2), Inches(11.73), Inches(0.85), DARK_BG, None)
tf_close = b_close.text_frame
tf_close.word_wrap = True
tf_close.margin_left = Inches(0.3)
tf_close.margin_top = Inches(0.12)

p_c1 = tf_close.paragraphs[0]
p_c1.text = "\"NextSupport AI transforms customer support from an expensive cost center into a high-trust, data-driven operational asset.\""
p_c1.font.bold = True
p_c1.font.italic = True
p_c1.font.size = Pt(12)
p_c1.font.color.rgb = ACCENT_BLUE

p_c2 = tf_close.add_paragraph()
p_c2.text = "Thank you! Open for Questions & Live Interactive Demonstration."
p_c2.font.bold = True
p_c2.font.size = Pt(11)
p_c2.font.color.rgb = TEXT_LIGHT
p_c2.space_before = Pt(3)

# Save
output_path = Path("NextSupport_AI_Presentation.pptx")
prs.save(output_path)
print(f"PowerPoint Presentation successfully created: {output_path.resolve()} (Size: {output_path.stat().st_size} bytes)")
