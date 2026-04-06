import streamlit as st
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO

# ============================================================================
# 1. 页面配置 (恢复高级黑蓝主题 - Deep Dark & Cyber Blue)
# ============================================================================
st.set_page_config(page_title="AIV Supply Chain Risk Assessment", page_icon="⚖️", layout="centered")

st.markdown("""
<style>
    /* 全局暗黑背景 */
    .stApp, [data-testid="stAppViewContainer"] { background-color: #0e1117 !important; }
    [data-testid="stHeader"] { background-color: transparent !important; }
    * { color: #e2e8f0 !important; }
    
    /* 赛博蓝标题 */
    h1, h2, h3, h4, h5 { color: #00d4ff !important; font-weight: 800 !important; letter-spacing: 0.5px; }
    
    /* 选项按钮文字 */
    .stRadio label, div[role="radiogroup"] label { color: #cbd5e1 !important; font-size: 16px !important; line-height: 1.6 !important; }
    
    /* 表单背景深邃灰黑，带发光边框 */
    div[data-testid="stForm"] { 
        background-color: #1a1c23 !important; 
        border-left: 4px solid #00d4ff !important; 
        padding: 2.5rem !important; 
        border-radius: 8px !important; 
        border-top: 1px solid #2d3748 !important;
        border-right: 1px solid #2d3748 !important;
        border-bottom: 1px solid #2d3748 !important;
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.1) !important; 
    }
    
    /* CRM与数据鸿沟警告横幅 */
    .warning-banner { background: linear-gradient(90deg, rgba(26,28,35,1) 0%, rgba(0,50,70,1) 100%) !important; border-left: 5px solid #00d4ff !important; border-radius: 8px !important; padding: 1.5rem !important; margin-bottom: 2rem !important; }
    .warning-banner h3 { color: #00d4ff !important; }
    .warning-banner p { color: #a0aec0 !important; font-size: 15px !important;}
    .highlight-red { color: #ff4a4a !important; font-weight: bold; }
    
    /* 支付钩子框 */
    .hook-box { background-color: #1a1c23 !important; border: 1px dashed #00d4ff !important; border-radius: 8px !important; padding: 2rem !important; margin-top: 2rem !important; margin-bottom: 2rem !important; }
    
    /* 结果判定框 - 红色极度醒目 */
    .result-box { background-color: rgba(217, 48, 37, 0.1) !important; border-left: 6px solid #ff4a4a !important; padding: 2rem !important; border-radius: 8px !important; margin-top: 2rem !important; margin-bottom: 2rem !important;}
    .result-box h2 { color: #ff4a4a !important; font-size: 32px !important; margin-bottom: 10px !important;}
    .result-box h3, .result-box h4 { color: #00d4ff !important; }
    
    .contact-note { color: #a0aec0 !important; font-size: 14px !important; line-height: 1.6 !important; background-color: #1a1c23 !important; padding: 15px !important; border-radius: 6px !important; border-left: 3px solid #718096 !important; margin-bottom: 15px !important;}
    
    /* PDF长文展示区 */
    .report-content { background-color: #1a1c23; padding: 20px; border-radius: 8px; border: 1px solid #2d3748; margin-top: 20px; font-family: monospace; color: #a0aec0; line-height: 1.8;}
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
# 3. 万字终极报告数据库 (均颐独家硬核 B2B 英文版)
# ============================================================================
TIER_1_TEXT = """Report No.: AIV-2026-FULL-108
Evaluation Level: Level 1: Secure (Strategic Robust)
Applicable Scenarios: Full-process procurement, risk control, cost optimization and rights protection of 200kW-2500kW+ industrial diesel/gas generators for global buyers.

Preface:
This report is a complete practical manual that can be directly programmed into Python, without any redundant content. All content is actionable, verifiable and data-based hardcore information. It deeply reveals the truth of China's generator industry production capacity, tax refund dividends, payment risk control, and supply chain stability.

1. Core Data of China's Generator Industry: The Shocking Truth of Overcapacity
There are 5,217 registered generator companies in China, among which only 712 are real foreign trade factories (13.65%). The remaining more than 86% are trading companies, shell companies and small workshops without production capacity. From 2025 to 2026, the total annual production capacity reaches 1.28 million units, while global demand is only 570,000 units (utilization rate 44.5%).

2. Precise Distribution of Core Industrial Clusters
- Jiangdu, Yangzhou: Core Foreign Trade Area (50-1000kW). 1126 factories, 283 real exporters.
- Weifang, Shandong: Heavy Power Area (500-2500kW). 317 factories, 142 real exporters.
- Jiangjin, Chongqing: Heavy Units/Gas (Above 1000kW). 164 factories, 89 real exporters.

3. Complete Contract Compliance & Tax Refund (13%)
- Balance Payment Strategy: Regardless of cooperation duration, retain 15%-20% balance payment. The balance payment condition is payment within 7 working days after the goods arrive + 72-hour continuous load test qualified.
- Tax Refund: China's unified export tax refund rate for generators is 13%. If settled in RMB, clarify that 5%-8% of the 13% export tax refund will be returned to the buyer.

4. Top Industry Insider Stories
- Refurbished Engine Heads: Second-hand Cummins/Perkins sold as new. Scrapped after 1000 hours.
- Copper-clad Aluminum: Cost 45% lower than pure copper. Winding burnout rate reaches 80%.
- Solution: Third-party SGS/AIV on-site supervision before loading. Disassemble core parts to verify serial numbers.

CRM Optimization & AI Feeding Tips: This report can be imported into the enterprise procurement CRM system as a core standard database. All data indicators and screening rules can be used for AI model training to realize automatic supplier grading and cost accounting.
$19 Value Score: 9.8/10 (Full hardcore data, complete practical strategies)"""

TIER_2_TEXT = """Report No.: AIV-2026-LEVEL2-109
Evaluation Level: Level 2: Controlled Illusion
Applicable Scenarios: Full-process procurement, risk control remediation, and emergency rights protection of industrial generators.

Preface:
For global Tier 2 buyers who have established a basic supply chain cooperation system and completed payment before inspection. You are trapped in a controlled illusion and have systematic risk control loopholes.

1. Core Data & Tier 2 Exclusive Traps
Overcapacity brings 20%-35% bargaining space. However, due to completed payment before inspection, losing the initiative of fund constraints, factory cooperation degree drops sharply. 42% of cooperative factories will replace non-original parts, falsely label power and simplify quality inspection process after payment and before loading. Later O&M costs are 2.5 times higher.

2. Tier 2 Real Factory Remedial Screening
Must ask after payment: "Please provide the load test bench equipment number of our order unit, the original data curve of 72-hour continuous test. Can you remotely view the test workshop in real time?" Workshops without professional test benches cannot provide this.

3. Tier 2 Fund Risk Control Remediation Plan
- For unfinished orders: Immediately sign a balance payment supplementary agreement, convert the remaining 15%-20% payment into arrival acceptance balance payment.
- Emergency Rights Protection: Shorten the claim limitation for quality problems to 15 days after arrival. Factory must respond within 24 hours.

4. Tier 2 Core Insider Stories
- Parts Replacement After Payment: The factory replaces original controllers and starting motors with high-imitation parts, cost reduced by 30%.
- Simplified Quality Inspection: Skip 72-hour continuous load test, only do no-load test.
- Ultimate Solution: Arrange a third-party supervision institution (AIV) to follow up the whole loading process.

CRM Optimization & AI Feeding Tips: Import this report into the procurement CRM as a Tier 2 special risk control standard. Extract post-payment remediation rules for AI training to realize automatic early warning of paid order risks.
$19 Value Score: 9.5/10 (Targeted remedial strategies, complete risk control system)"""

TIER_3_TEXT = """Report No.: AIV-2026-LEVEL3-110
Evaluation Level: Level 3: Medium Risk (Edge of Jiangsu Trap)
Headline: Medium Risk Alert: You are on the Edge of the Jiangsu Industrial Chain Trap.

1. Tier 3 Diagnosis Summary
You are in a medium-risk procurement control state. The supply chain is not completely out of control, but there are many fatal systematic loopholes. You rely entirely on past cooperation experience and have not established a data-based management system.

2. The Jiangsu Trap: Delay Cost vs. Rectification Cost
In Jiangsu and national generator industrial belts, the core hidden danger is: strong risk concealment and delayed outbreak. If loopholes are not filled in time, it is easy to slide to high-risk tiers, facing fund loss and production stagnation. 

3. Immediate Data-Driven Intervention
You must immediately implement the AIV Dual-Verification protocol. Your current supplier has a 47% statistical probability of substituting domestic equivalents for core pump assemblies to extract an illicit 12%-18% margin.

CRM Optimization & AI Feeding Tips: Directly data input into computers, programming embedded into procurement CRM to build a standardized and automatic procurement management process, completely avoiding all traps.
$19 Value Score: 9.2/10 (Critical intervention protocol)"""

TIER_4_TEXT = """Report No.: AIV-2026-LEVEL4-111
Evaluation Level: Level 4: Systemic Bleeding
Headline: Systemic Bleeding: Your Capital is at the Mercy of Trading Shells.

1. Critical Vulnerability Diagnosis
CRITICAL CRISIS. The algorithm has determined an 85% probability that your current supplier is a high-level trading office masquerading as a factory. You possess zero foundational data; every technical requirement you send is being filtered, diluted, and subcontracted.

2. Industry Truth: The Shell Game
Over 86% of Alibaba/Made-in-China listings for heavy generators are shell companies. They possess zero manufacturing capacity and outsource entirely to unregulated back-alley workshops. Contracts provided by these entities are laced with maritime exemption clauses. Your chance of winning an international claim is below 12%.

3. Emergency Override Plan
- Immediate Payment Freeze: Halt any pending TT transfers.
- Demand Deep Verification: Force the supplier to provide their ISO9001 and factory Social Security contribution records.

CRM Optimization & AI Feeding Tips: Embed these strict parameters into your CRM to instantly red-flag and block payments to any vendor matching the "Trading Shell" data signature.
$19 Value Score: 10/10 (Emergency capital preservation)"""

TIER_5_TEXT = """Report No.: AIV-2026-LEVEL5-112
Evaluation Level: Level 5: Fatal Exposure
Headline: FATAL EXPOSURE: The 'Ghost Factory' Trap. Immediate Paralysis Imminent.

1. Maximum Alert Diagnosis
Your supply chain is entirely exposed. You have zero redundancy, no true identity verification, and operate on pure faith. You are playing Russian Roulette with corporate capital.

2. The Cyclical Harvesting Model
Ghost Factories execute 2-3 small, flawless orders at a loss to gain trust. Once a large capital order is placed, they either abscond with the funds or deliver completely unstartable, cosmetically refurbished industrial scrap metal.

3. Total Extraction Protocol
- CEASE ALL OPERATIONS. Do not pay another cent.
- Dispatch an AIV On-Site Investigator to their registered address to secure evidence for local economic police (ECID).
- Rebuild your network exclusively using AIV's vetted whitelist of the 712 verified export-grade factories.

CRM Optimization & AI Feeding Tips: Hardcode this Ghost Factory signature into your procurement AI. Any supplier lacking a 3-year verified customs export record must be autonomously blacklisted by the CRM.
$19 Value Score: 10/10 (Immediate disaster prevention)"""

REPORT_DATA = {
    1: {"level": "Level 1: SECURE", "full_text": TIER_1_TEXT},
    2: {"level": "Level 2: CONTROLLED ILLUSION", "full_text": TIER_2_TEXT},
    3: {"level": "Level 3: ELEVATED RISK", "full_text": TIER_3_TEXT},
    4: {"level": "Level 4: SYSTEMIC BLEEDING", "full_text": TIER_4_TEXT},
    5: {"level": "Level 5: FATAL EXPOSURE", "full_text": TIER_5_TEXT}
}

# ============================================================================
# 4. 强大的长文 PDF 生成引擎
# ============================================================================
def generate_pdf_report(avg_score, risk_level_key):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#005580'), alignment=1)
    normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=10, textColor=colors.black, spaceAfter=8, leading=14)
    alert_style = ParagraphStyle('Alert', parent=styles['Normal'], fontSize=14, textColor=colors.red, spaceAfter=15, fontName='Helvetica-Bold')
    
    # 写入抬头
    story.append(Paragraph("AIV Supply Chain Truth Report & Risk Audit", title_style))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(f"SCRI Score (Supply Chain Risk Index): {avg_score:.1f} / 10.0", alert_style))
    story.append(Spacer(1, 0.2*inch))
    
    # 写入长文内容 (自动换行与段落处理)
    raw_text = REPORT_DATA[risk_level_key]['full_text']
    paragraphs = raw_text.split('\n')
    for p in paragraphs:
        if p.strip() == "":
            story.append(Spacer(1, 0.1*inch))
        else:
            story.append(Paragraph(p, normal_style))
            
    doc.build(story)
    buffer.seek(0)
    return buffer

# ============================================================================
# 5. 前端交互逻辑与无 Bug 状态机
# ============================================================================
# 初始化状态管理 (解决按钮一按就消失的Bug)
if "step" not in st.session_state:
    st.session_state.step = "form" # 状态分为: form (填表), paywall (诱饵页), result (看报告)

st.markdown("### ⚙️ Axiom Industrial Verification (AIV)")

# 第一步：填写表单
if st.session_state.step == "form":
    st.markdown("""
    <div class="warning-banner">
        <h3>🚨 [AIV DIRECTIVE] THE DATA GAP WARNING</h3>
        <p>
            90% of global procurement failures happen in the blind spot between the Chinese factory floor and your office.<br>
            <span class="highlight-red">Run your supply chain through the AIV Proprietary Algorithm to reveal your true risk exposure.</span><br><br>
            <i>本阐述结果将帮您大幅度优化 CRM 审计，跑通关键底层数据，避免灾难性的资金断裂。</i>
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("aiv_audit_form"):
        st.markdown("<h4 style='color: #00d4ff;'>SCRI Factor Assessment</h4>", unsafe_allow_html=True)
        
        answers = []
        for key, q_data in QUESTIONS.items():
            st.markdown(f"<h5 style='color: #00d4ff;'>{q_data['title']}</h5>", unsafe_allow_html=True)
            ans = st.radio("Select an option:", q_data['options'], key=key, label_visibility="collapsed")
            answers.append((ans, q_data['options'], q_data['scores']))
            st.markdown("<br>", unsafe_allow_html=True)
            
        st.markdown("---")
        st.markdown("""
        <div class="contact-note">
            Provide your Business Email to receive your personalized audit results and the [2026 China Heavy Machinery Risk Matrix].
        </div>
        """, unsafe_allow_html=True)
        
        contact_info = st.text_input("Business Email or WhatsApp:")
        
        submitted = st.form_submit_button("Run AI Proprietary Algorithm 🔍", use_container_width=True)

        if submitted:
            if not contact_info:
                st.error("⚠️ Please enter your Email or WhatsApp.")
            else:
                # 算法计算逻辑
                total_score = sum(scores[opts.index(ans)] for ans, opts, scores in answers)
                avg_score = total_score / 10.0
                
                if avg_score < 3.0: risk_level_key = 1
                elif avg_score < 5.0: risk_level_key = 2
                elif avg_score < 7.0: risk_level_key = 3
                elif avg_score < 9.0: risk_level_key = 4
                else: risk_level_key = 5
                    
                # 存入 session_state 并切换状态
                st.session_state.avg_score = avg_score
                st.session_state.risk_level_key = risk_level_key
                st.session_state.user_contact = contact_info
                st.session_state.step = "paywall"
                st.rerun()

# 第二步：显示 Paywall 收银台和你的测试按钮
elif st.session_state.step == "paywall":
    st.success("✅ Assessment Complete! Algorithm has finalized your score.")
    
    st.markdown("""
    <div class="hook-box">
        <h3 style="color: #00d4ff; margin-top:0;">🔓 Unlock Your Precision Risk Score ($19)</h3>
        <p style="color: #e2e8f0; font-size: 16px;">This data can be directly programmed into your CRM system for automatic supplier screening.</p>
        <ul style="color: #cbd5e1; font-size: 15px; line-height: 1.8;">
            <li><b>Your Exact SCRI Score (1.0 - 10.0) & Classification</b></li>
            <li><b>Complete Analysis of China Generator Industry In-depth Rules</b></li>
            <li><b>Tax Refund Dividend Mining & Profit Control Manual</b></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.link_button("💳 Pay $19 to Unlock Full Report", "https://your-payment-link-here.com", type="primary", use_container_width=True)
    with col2:
        # 这个测试按钮现在独立在外面，绝对不会出现一闪而过的问题
        if st.button("👁️ 内部免费测试：预览完整报告 (绝对可用)", use_container_width=True):
            st.session_state.step = "result"
            st.rerun()

# 第三步：完美展示打分和万字报告全文
elif st.session_state.step == "result":
    avg_score = st.session_state.avg_score
    risk_level_key = st.session_state.risk_level_key
    report_text = REPORT_DATA[risk_level_key]['full_text']
    
    st.markdown(f"""
    <div class="result-box">
        <h2>Your SCRI Score: {avg_score:.1f} / 10.0</h2>
        <h3>{REPORT_DATA[risk_level_key]['level']}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # 网页端展示那万字长文
    st.markdown("#### 📜 Full AIV Proprietary Report ($19 Value)")
    
    # 用 html 的 pre 标签保持你英文原稿的换行和格式
    st.markdown(f"""
    <div class="report-content">
        {report_text.replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 生成终极版 PDF 提供下载
    pdf_buffer = generate_pdf_report(avg_score, risk_level_key)
    st.download_button(
        label="📄 Download B2B Full PDF Report & CRM Code",
        data=pdf_buffer,
        file_name=f"AIV_Full_Report_Score_{avg_score}.pdf",
        mime="application/pdf",
        type="primary"
    )
    
    if st.button("⬅️ Back to Start"):
        st.session_state.step = "form"
        st.rerun()
