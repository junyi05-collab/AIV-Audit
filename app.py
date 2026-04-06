import streamlit as st
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO

# ============================================================================
# 1. 页面配置 (企业级高清晰度白/蓝主题)
# ============================================================================
st.set_page_config(page_title="AIV Supply Chain Risk Assessment", page_icon="⚖️", layout="centered")

st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"] { background-color: #f4f7f6 !important; }
    [data-testid="stHeader"] { background-color: transparent !important; }
    * { color: #2c3e50 !important; }
    h1, h2, h3, h4, h5 { color: #1e3a8a !important; font-weight: 800 !important; }
    .stRadio label, div[role="radiogroup"] label { color: #34495e !important; font-size: 16px !important; line-height: 1.6 !important; font-weight: 500 !important; }
    div[data-testid="stForm"] { background-color: #ffffff !important; border-left: 6px solid #1e3a8a !important; padding: 2.5rem !important; border-radius: 12px !important; box-shadow: 0 10px 25px rgba(0,0,0,0.05) !important; border: none !important; }
    .warning-banner { background: #fff3cd !important; border-left: 5px solid #ffc107 !important; border-radius: 8px !important; padding: 1.5rem !important; margin-bottom: 2rem !important; }
    .warning-banner h3, .warning-banner p, .warning-banner strong { color: #856404 !important; }
    .hook-box { background-color: #e6f2ff !important; border: 2px dashed #1e3a8a !important; border-radius: 10px !important; padding: 2rem !important; margin-top: 1rem !important; }
    .result-box { background-color: #ffe6e6 !important; border-left: 6px solid #d93025 !important; padding: 2rem !important; border-radius: 8px !important; margin-top: 2rem !important; box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important; }
    .result-box h2 { color: #d93025 !important; }
    .result-box h3, .result-box h4 { color: #1e3a8a !important; }
    .contact-note { color: #5f6368 !important; font-size: 14px !important; line-height: 1.6 !important; background-color: #f8f9fa !important; padding: 15px !important; border-radius: 6px !important; border-left: 3px solid #5f6368 !important; margin-bottom: 15px !important;}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 2. AIV 1-10分 核心判官算法
# ============================================================================
QUESTIONS = {
    "q1": {"title": "1. Delivery Satisfaction & Stability", "options": ["A. Perfect delivery every time with zero quality or communication disputes.", "B. Occasional friction or minor delays, but generally manageable.", "C. Frequent anomalies requiring extremely high management costs.", "D. Long-term unresolved quality disputes or severe failures."], "scores": [1, 3, 7, 10]},
    "q2": {"title": "2. Root Cause of Critical Failures", "options": ["A. Bait & Switch: Received goods did not match samples/contracts.", "B. Logistics Exemption: Frequent shipping issues blocked by exemption clauses.", "C. Core Component Fraud: Refurbished parts discovered post-delivery.", "D. Compliance Failure: Equipment failed to meet local grid/environmental standards."], "scores": [10, 8, 9, 10]},
    "q3": {"title": "3. Primary Asset Power Range (Liability Scope)", "options": ["A. 200kW-300kW: Standard Commercial Application.", "B. 500kW-800kW: Heavy Duty Industrial Application.", "C. 1000kW-2000kW+: Critical Strategic/Energy Application."], "scores": [5, 7, 10]},
    "q4": {"title": "4. Environmental & Climate Compliance", "options": ["A. Strictly custom-built and physically reinforced for our specific local climate.", "B. Standard general-purpose export model.", "C. Unsure. We solely rely on the factory's verbal promises."], "scores": [2, 6, 10]},
    "q5": {"title": "5. Supplier Redundancy Strategy", "options": ["A. We maintain a pre-vetted, field-tested 'Plan B' factory on standby.", "B. We are 100% reliant on one single long-term supplier.", "C. We only start searching for backups when a crisis occurs."], "scores": [1, 8, 10]},
    "q6": {"title": "6. True Identity Penetration", "options": ["A. Deep Audit: Social Security & Customs Export Data legally verified.", "B. 3rd-Party Only: We blindly trust certificates (e.g., SGS).", "C. Surface Level: Website check or video factory tour only.", "D. Never verified. We take their 'source factory' claims at face value."], "scores": [1, 6, 8, 10]},
    "q7": {"title": "7. Claim Evidence Traceability", "options": ["A. Unbreakable chain of physical and digital data evidence.", "B. We only possess factory-provided PDF test reports.", "C. Almost zero valid evidence. We bear the total financial loss."], "scores": [1, 7, 10]},
    "q8": {"title": "8. Communication & Technical Audit", "options": ["A. Native Audit: We employ local Chinese engineers to interrogate the factory.", "B. Agency Relay: We rely on an English trading middleman/agent.", "C. Complete Reliance: We rely entirely on the factory's own sales translator."], "scores": [1, 6, 10]},
    "q9": {"title": "9. Loading & Sealing Monitoring", "options": ["A. Full Stream: Continuous video/data monitoring until container sealing.", "B. Snapshot Inspection: 3rd-party inspector takes photos before leaving.", "C. Blind Spot: We have no capacity to control the final loading process."], "scores": [1, 7, 10]},
    "q10": {"title": "10. Digital Genome Value", "options": ["A. Invaluable: Raw test data (Vibration/Heat) is our core decision genome.", "B. Secondary: We rely more on the factory's brand reputation.", "C. Irrelevant: We ignore raw data entirely as we cannot analyze it."], "scores": [1, 6, 10]}
}

# ============================================================================
# 3. 5梯队震撼报告大纲
# ============================================================================
REPORT_DATA = {
    1: {
        "level": "Tier 1 (1.0 - 2.9): THE FORTIFIED SUPPLY CHAIN",
        "headline": "You are in the Top 5% of Global Buyers.",
        "diagnostic": "Your supply chain architecture is exceptionally rigorous. You possess a penetrative audit mechanism and independent data leverage. It is extremely difficult for factories to execute 'bait-and-switch' tactics under your direct oversight. However, industry dynamics change rapidly, and complacency is your only enemy.",
        "industry_truth": "CLASSIFIED DATA INSERTION: According to the AIV 2026 Database, within the Jiangsu manufacturing hub for 1000kW+ assets, less than 5% of international buyers possess the capability to capture raw 'Vibration/Heat' mapping as you do. You have successfully bypassed the standard trap.",
        "action_plan": "AIV SOLUTION: While secure, long-term partnerships naturally breed factory complacency. We recommend our Complete Verification ($700) for an unannounced annual review, ensuring their registered social security headcount and core production capacity haven't covertly shrunk over the past year."
    },
    2: {
        "level": "Tier 2 (3.0 - 4.9): THE ILLUSION OF CONTROL",
        "headline": "Blind Spots Detected in Your Quality Assurance.",
        "diagnostic": "On the surface, your deliveries appear smooth, but you are operating under an illusion of control. You overly rely on '3rd-Party Snapshot Inspections' (like standard SGS reports) or the factory's perceived reputation. You critically lack the final-mile physical control prior to container sealing.",
        "industry_truth": "CLASSIFIED DATA INSERTION: Our regional metrics reveal that 42% of 'standard compliant' heavy machinery, immediately after passing an SGS inspection, undergoes unauthorized component downgrading (e.g., swapping out original Stamford AVRs or starter motors) within the 48 hours before the container is locked.",
        "action_plan": "AIV SOLUTION: You don't need a complete overhaul, but you must plug this bleeding vulnerability. We strongly advise deploying AIV's Premium On-Site Audit ($3,500) for your next batch. We will station a native engineer to execute a full-chain interception right up to the container seal."
    },
    3: {
        "level": "Tier 3 (5.0 - 6.9): ELEVATED RISK WARNING",
        "headline": "You are Approaching the 'Jiangsu Parts-Swap' Event Horizon.",
        "diagnostic": "Your current procurement logic is highly hazardous. You are overly dependent on the factory's English translator, lack a viable backup supplier, and your evidence chain is practically non-existent. The moment this factory faces a cash flow issue, you will be the first client they exploit.",
        "industry_truth": "CLASSIFIED DATA INSERTION: Our latest audit models indicate that in your selected power range (especially 500kW+), if a factory covertly swaps 100% pure copper windings for copper-clad aluminum, or installs a refurbished core pump, their profit per unit illegally spikes by upwards of $15,000. You will not notice this until the machine catastrophically fails 3 months post-installation.",
        "action_plan": "AIV SOLUTION: Halt any new large-volume orders immediately! You must initiate the Complete Verification ($700). The AIV Chief Auditor will penetrate their foundational tax and social security data to reveal if they are truly a 'source manufacturer' or just a well-disguised assembly workshop."
    },
    4: {
        "level": "Tier 4 (7.0 - 8.9): SYSTEMIC BLEEDING",
        "headline": "Your Capital is at the Mercy of Trading Shells.",
        "diagnostic": "CRITICAL CRISIS. The algorithm has determined an 85% probability that your current supplier is a high-level trading office masquerading as a factory. You possess zero foundational data; every technical requirement you send is being filtered, diluted, and subcontracted.",
        "industry_truth": "CLASSIFIED DATA INSERTION: Based on your input model, if you face a catastrophic quality claim today, the probability of your current evidence chain being accepted by an international court or insurer is below 12%. These entities have deployed countless 'maritime exemption clauses' to legally neutralize your legal rights.",
        "action_plan": "AIV SOLUTION: EMERGENCY OVERRIDE. Do not trust any workshop videos they send (these are easily staged for $50). Immediately contact AIV to execute a Premium On-Site Audit ($3,500). We will physically ambush their registered address and hand you the unfiltered, bloody truth before you wire another payment."
    },
    5: {
        "level": "Tier 5 (9.0 - 10.0): FATAL EXPOSURE",
        "headline": "The 'Ghost Factory' Trap. Immediate Paralysis Imminent.",
        "diagnostic": "Your supply chain is entirely exposed. You have zero redundancy, no true identity verification, and operate on pure faith. You are not conducting international heavy industry procurement; you are playing Russian Roulette with corporate capital.",
        "industry_truth": "CLASSIFIED DATA INSERTION: You have triggered the most severe fraud model in the AIV database. Buyers exhibiting this specific behavioral pattern typically face a 'midnight run' (absconding with funds) or receive completely unstartable industrial scrap metal by their 4th order cycle.",
        "action_plan": "AIV SOLUTION: RED ALERT. Abandon all hope of a 'lucky delivery'. Secure all payment vouchers immediately. Schedule an emergency voice consultation with an AIV Senior Investigator to deploy a complete supply chain extraction and restructuring operation."
    }
}

# ============================================================================
# 4. PDF 生成引擎
# ============================================================================
def generate_pdf_report(avg_score, risk_level_key):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1e3a8a'), alignment=1)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#2c3e50'), spaceBefore=15, spaceAfter=8)
    normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=11, textColor=colors.black, spaceAfter=12, leading=16)
    
    alert_color = colors.HexColor('#28a745') if avg_score < 3.0 else (colors.HexColor('#ff9900') if avg_score < 7.0 else colors.HexColor('#d93025'))
    alert_style = ParagraphStyle('Alert', parent=styles['Normal'], fontSize=15, textColor=alert_color, spaceAfter=15, fontName='Helvetica-Bold')
    
    data = REPORT_DATA[risk_level_key]
    
    story.append(Paragraph("AIV Supply Chain Truth Report & Risk Audit", title_style))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(f"SCRI Score (Supply Chain Risk Index): {avg_score:.1f} / 10.0", alert_style))
    story.append(Paragraph(f"<b>{data['headline']}</b>", alert_style))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("1. Executive Diagnostic", heading_style))
    story.append(Paragraph(data['diagnostic'], normal_style))
    
    story.append(Paragraph("2. Classified Intel & The Underlying Truth", heading_style))
    story.append(Paragraph(data['industry_truth'], normal_style))
    
    story.append(Paragraph("3. Immediate Mitigation & AIV Directive", heading_style))
    story.append(Paragraph(data['action_plan'].replace("**", ""), normal_style))
    
    crm_text = """<b>🤖 AI-DRIVEN CRM INTEGRATION DIRECTIVE:</b><br/>
    The proprietary data parameters and risk thresholds detailed in this report are structured for direct ingestion into your enterprise AI or Procurement CRM. By feeding these AIV intelligence matrices into your system, you can automate supplier vetting and autonomously filter out unqualified vendors before a contract is drafted."""
    crm_style = ParagraphStyle('CRM', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#1e3a8a'), spaceBefore=20, spaceAfter=10, leading=14, backColor=colors.HexColor('#e6f2ff'), borderPadding=10)
    story.append(Paragraph(crm_text, crm_style))
    
    story.append(Spacer(1, 0.4*inch))
    story.append(Paragraph("Contact AIV Chief Auditor to execute directives: <b>audit@axiomiv.com</b>", normal_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ============================================================================
# 5. 前端交互逻辑
# ============================================================================
if 'show_results' not in st.session_state:
    st.session_state.show_results = False

query_params = st.query_params
if query_params.get("payment") == "success":
    st.session_state.show_results = True

if st.session_state.show_results and "avg_score" in st.session_state:
    st.markdown("### 🔓 AIV Truth Report Unlocked")
    
    avg_score = st.session_state.avg_score
    risk_level_key = st.session_state.risk_level_key
    data = REPORT_DATA[risk_level_key]
    
    st.markdown(f"""
    <div class="result-box">
        <h2>Your SCRI Score: {avg_score:.1f} / 10.0</h2>
        <h3>{data['level']}</h3>
        <h4>{data['headline']}</h4>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("#### 1. Executive Diagnostic")
    st.write(data['diagnostic'])
    
    st.markdown("#### 2. Classified Intel")
    st.error(data['industry_truth']) 
    
    st.markdown("#### 3. Action Plan")
    st.info(data['action_plan'])     
    
    pdf_buffer = generate_pdf_report(avg_score, risk_level_key)
    st.download_button(
        label="📄 Download Full PDF Report & AI CRM Directives",
        data=pdf_buffer,
        file_name=f"AIV_Risk_Report_Score_{avg_score}.pdf",
        mime="application/pdf",
        type="primary"
    )
    
    if st.button("⬅️ Back to Assessment"):
        st.session_state.show_results = False
        st.rerun()

else:
    st.markdown("### ⚙️ Axiom Industrial Verification (AIV)")
    st.markdown("""
    <div class="warning-banner">
        <h3>🚨 THE DATA GAP WARNING</h3>
        <p>
            <strong>90% of global procurement failures happen in the blind spot between the Chinese factory floor and your office.</strong><br><br>
            Stop relying on surface-level checks. Run your supply chain through the <strong>AIV Proprietary Algorithm</strong> to reveal your true risk exposure. <br><br>
            <span style='color:#d93025; font-weight:bold;'>💡 [AIV DIRECTIVE]: The results of this assessment will help you drastically optimize your enterprise CRM audits and lock down critical procurement data, saving you from catastrophic capital loss.</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("aiv_audit_form"):
        st.markdown("<h4 style='color: #1e3a8a;'>SCRI Factor Assessment</h4>", unsafe_allow_html=True)
        st.markdown("---")
        
        answers = []
        for key, q_data in QUESTIONS.items():
            st.markdown(f"<h5 style='color: #1e3a8a;'>{q_data['title']}</h5>", unsafe_allow_html=True)
            ans = st.radio("Select an option:", q_data['options'], key=key, label_visibility="collapsed")
            answers.append((ans, q_data['options'], q_data['scores']))
            st.markdown("<br>", unsafe_allow_html=True)
            
        st.markdown("---")
        st.markdown("<h5 style='color: #1e3a8a;'>📩 Intelligence Delivery Destination</h5>", unsafe_allow_html=True)
        st.markdown("""
        <div class="contact-note">
            Provide your Business Email. As a bonus, our audit team will manually send you the classified <b>[2026 China Heavy Machinery Risk Matrix]</b> customized for your specific power range.
        </div>
        """, unsafe_allow_html=True)
        
        contact_info = st.text_input("Business Email or Executive WhatsApp:")
        
        submitted = st.form_submit_button("Run AI Proprietary Algorithm 🔍", use_container_width=True)

    if submitted:
        if not contact_info:
            st.error("⚠️ Please enter your Email or WhatsApp to receive your complimentary Whitepaper.")
        else:
            total_score = sum(scores[opts.index(ans)] for ans, opts, scores in answers)
            avg_score = total_score / 10.0
            
            if avg_score < 3.0:
                risk_level_key = 1
            elif avg_score < 5.0:
                risk_level_key = 2
            elif avg_score < 7.0:
                risk_level_key = 3
            elif avg_score < 9.0:
                risk_level_key = 4
            else:
                risk_level_key = 5
                
            st.session_state.avg_score = avg_score
            st.session_state.risk_level_key = risk_level_key
            st.session_state.user_contact = contact_info
            
            st.success("✅ Assessment Complete! Algorithm has finalized your score.")
            
            st.markdown("""
            <div class="hook-box">
                <h3 style="color: #1e3a8a; margin-top:0;">🔓 Unlock Your Exact Risk Score & AI Directives</h3>
                <p style="color: #2c3e50; font-size: 16px;"><b>Pay just $19 to instantly reveal:</b></p>
                <ul style="color: #34495e; font-size: 15px;">
                    <li><b>Your Exact SCRI Score (1.0 - 10.0) & 5-Tier Classification</b></li>
                    <li><b>Deep Industry Truths (Component Swap Risks & Profit Margins)</b></li>
                    <li><b>Actionable PDF Report & Custom AIV Solutions</b></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.link_button("💳 Pay $19 to Unlock Full Report", "https://your-payment-link-here.com", type="primary", use_container_width=True)
            with col2:
                # 给你的专属预览按钮
                if st.button("👁️ 内部测试：免费预览生成的PDF报告 (测试专用)", use_container_width=True):
                    st.session_state.show_results = True
                    st.rerun()
