import streamlit as st
import stripe
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO

# ============================================================================
# 1. 核心配置与 Stripe 秘钥
# ============================================================================
st.set_page_config(page_title="AIV Supply Chain Risk Assessment", page_icon="⚙️", layout="centered")

# 🔑 Stripe 秘钥配置
STRIPE_SECRET_KEY = "sk_test_XXXXXXXXXXXXXXXXXXXXXXXX"
stripe.api_key = STRIPE_SECRET_KEY
YOUR_APP_URL = "https://aiv-audit.streamlit.app" 

# ============================================================================
# 2. 顶级工业黑金 UI 样式
# ============================================================================
st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"] { background-color: #1a1c23 !important; }
    [data-testid="stHeader"] { background-color: transparent !important; }
    * { color: #e0e0e0 !important; }
    h1, h2, h3, h4, h5 { color: #00d4ff !important; font-weight: 700 !important; }
    .stRadio label, div[role="radiogroup"] label { color: #ffffff !important; font-size: 16px !important; line-height: 1.6 !important; }
    div[data-testid="stForm"] { background-color: #252a33 !important; border-left: 5px solid #00d4ff !important; padding: 2.5rem !important; border-radius: 10px !important; border: 1px solid #444 !important; }
    .warning-banner { background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(176, 176, 176, 0.05) 100%); border: 1px solid #00d4ff; border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem; }
    .hook-box { background-color: #1a1c23; border: 2px dashed #00d4ff; border-radius: 10px; padding: 2rem; margin-top: 1rem; }
    .result-box { background-color: rgba(255, 0, 0, 0.1); border-left: 4px solid #ff4444; padding: 2rem; border-radius: 8px; margin-top: 2rem; }
    .contact-note { color: #b0b0b0; font-size: 14px; line-height: 1.6; background-color: #1a1c23; padding: 15px; border-radius: 6px; border-left: 3px solid #b0b0b0; margin-bottom: 15px;}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 3. 题目与计分权重
# ============================================================================
QUESTIONS = {
    "q1": {"title": "1. Delivery Stability & Satisfaction (交付稳定性与满意度)", "options": ["A. Perfect delivery every time with zero quality or communication disputes.", "B. Occasional delays or minor spec adjustments, but generally manageable.", "C. Frequent disruptions, requiring extremely high communication and management costs.", "D. Severe long-term quality disputes or unresolved major failures."], "scores": [1, 3, 7, 10]},
    "q2": {"title": "2. Root Cause of Critical Failures (核心痛点诊断)", "options": ["A. Bait & Switch: The factory delivered products that did not match the contract or sample.", "B. Logistics & Liability Trap: Frequent shipping issues blocked by exemption clauses.", "C. Core Component Fraud: Refurbished or swapped core parts discovered after long-term use.", "D. Compliance Failure: Equipment failed to meet local grid or environmental standards."], "scores": [10, 8, 9, 10]},
    "q3": {"title": "3. Primary Generator Power Range (战略资产能级)", "options": ["A. 200kW-300kW: Standard Commercial Application.", "B. 500kW-800kW: Heavy Duty Industrial Application.", "C. 1000kW-2000kW+: Critical Strategic/Energy Application."], "scores": [5, 7, 9]},
    "q4": {"title": "4. Environmental & Climate Compliance (环境耐受度合规)", "options": ["A. Strictly custom-built and reinforced for our specific local climate.", "B. Standard export model, assuming it meets general global requirements.", "C. Unsure. We solely rely on the factory's verbal guarantee."], "scores": [2, 6, 9]},
    "q5": {"title": "5. Supplier Redundancy Strategy (供应商冗余与退路)", "options": ["A. We maintain a solid, pre-vetted 'Plan B' factory ready to produce immediately.", "B. We are 100% reliant on one single long-term supplier.", "C. We only start searching for new suppliers when a crisis or breakdown occurs."], "scores": [2, 8, 10]},
    "q6": {"title": "6. True Identity Penetration (供应商真实身份穿透)", "options": ["A. Deep Audit: We have legally verified their social security numbers and export customs data.", "B. 3rd-Party Only: We blindly trust certificates like SGS, assuming they act as full audits.", "C. Surface Level: We only checked their website, Alibaba profile, or had a video call.", "D. Never verified. We take their 'source factory' claims at face value."], "scores": [1, 5, 8, 10]},
    "q7": {"title": "7. Claim Evidence Traceability (理赔证据链完整度)", "options": ["A. We possess an unbreakable chain of physical and data evidence for successful full compensation.", "B. We only possess factory-signed PDF test reports. Claims are often difficult and discounted.", "C. We have almost zero valid evidence. We bear the total financial loss when things go wrong."], "scores": [1, 6, 10]},
    "q8": {"title": "8. Communication & Technical Audit (技术过滤与沟通暗角)", "options": ["A. Native Chinese Technical Audit: We employ trusted local Chinese engineers to interrogate the factory.", "B. English Trading Agent: We rely on a middleman or trading agent to relay our requirements.", "C. Factory Translator: We rely entirely on the factory's own sales rep to translate our critical specs."], "scores": [1, 6, 9]},
    "q9": {"title": "9. Loading & Sealing Trap Awareness (装柜掉包风险监控)", "options": ["A. Full Stream: We maintain continuous video/data monitoring from final assembly to container sealing.", "B. Snapshot Inspection: We trust 3rd-party inspectors who only take 'snapshot' photos before leaving.", "C. Blind Spot: We are aware factories can swap parts after inspection, but we have no control over it."], "scores": [2, 6, 9]},
    "q10": {"title": "10. Digital Genome Value (数字化测试基因图谱)", "options": ["A. Invaluable: Unedited factory test curves (Vibration/Heat/Current) are our core decision genome.", "B. Secondary: We find them interesting, but we rely more on the factory's brand reputation.", "C. Irrelevant: We do not have the expert capacity to analyze raw data, so we ignore it."], "scores": [1, 5, 8]}
}

# ============================================================================
# 4. PDF 生成引擎
# ============================================================================
def generate_pdf_report(avg_score, risk_level, recommendation):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#00d4ff'), alignment=1)
    normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=11, textColor=colors.black, spaceAfter=8)
    alert_style = ParagraphStyle('Alert', parent=styles['Normal'], fontSize=12, textColor=colors.red, spaceAfter=10, fontName='Helvetica-Bold')
    
    story.append(Paragraph("AIV Supply Chain Truth Report & Risk Audit", title_style))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"<b>Your Exact Risk Score:</b> {avg_score:.1f} / 10.0", normal_style))
    story.append(Paragraph(f"<b>Your 5-Tier Classification:</b> {risk_level}", normal_style))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("<b>🚨 AIV Expert Verdict:</b>", alert_style))
    story.append(Paragraph(recommendation, normal_style))
    story.append(Spacer(1, 0.4*inch))
    
    story.append(Paragraph("🛡️ AIV Action Plan & Professional Services:", styles['Heading2']))
    story.append(Paragraph("The $19 you paid today is fully credited toward our advanced audit packages below to secure your investment.", normal_style))
    story.append(Spacer(1, 0.1*inch))
    
    services_data = [
        ["Service Tier", "Investment", "What We Execute for You"],
        ["Tier 1: Complete Verification", "$700", "Deep Social Security Audit, Export Customs Trace, Real Factory ID Check."],
        ["Tier 2: Premium On-Site Audit", "$3,500", "Physical Engineer Dispatch, Unedited Live Video, Core Parts Authentication."]
    ]
    t = Table(services_data, colWidths=[2*inch, 1*inch, 4*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00d4ff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("<b>Contact AIV Chief Auditor Immediately:</b>", normal_style))
    story.append(Paragraph("Email: audit@axiomiv.com", normal_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ============================================================================
# 5. 路由与主逻辑 (加入免单测试通道)
# ============================================================================

if 'show_results' not in st.session_state:
    st.session_state.show_results = False

query_params = st.query_params
if query_params.get("payment") == "success":
    st.session_state.show_results = True

if st.session_state.show_results and "avg_score" in st.session_state:
    # 🌟 支付成功/绕过测试后的结果页面
    st.markdown("### 🔓 AIV Truth Report Unlocked")
    st.success("Verification complete. Your proprietary supply chain analysis is ready.")
    
    avg_score = st.session_state.avg_score
    risk_level = st.session_state.risk_level
    recommendation = st.session_state.recommendation
    user_contact = st.session_state.user_contact
    
    st.markdown(f"""
    <div class="result-box">
        <h2 style='color:#ff4444; margin-top:0;'>Your SCRI Score: {avg_score:.1f} / 10.0</h2>
        <h3 style='color:#ffffff;'>Classification: {risk_level}</h3>
        <p style='color:#e0e0e0; font-size:18px; line-height:1.6;'>{recommendation}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info(f"Thank you. Your customized Deep-Tier Whitepaper will also be dispatched to: **{user_contact}**")
    
    pdf_buffer = generate_pdf_report(avg_score, risk_level, recommendation)
    st.download_button(
        label="📄 Download Full PDF Report & Action Plan",
        data=pdf_buffer,
        file_name=f"AIV_Risk_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        type="primary"
    )
    
    st.markdown("---")
    st.markdown("#### 🛡️ Secure Your Investment Today")
    st.write("Contact us now to deploy an AIV engineer to your factory.")
    st.markdown("**1. Complete Verification ($700):** Deep Background & Customs Audit.")
    st.markdown("**2. Premium On-Site Audit ($3,500):** Physical Inspection & 'Parts-Swap' Prevention.")
    
    if st.button("⬅️ Back to Home"):
        st.session_state.show_results = False
        st.rerun()

else:
    # 📝 正常填表页面
    st.markdown("### ⚙️ Axiom Industrial Verification (AIV)")
    st.markdown("""
    <div class="warning-banner">
        <h3 style="color: #00d4ff; margin-top: 0;">🚨 [AIV AUDIT WARNING]</h3>
        <p style="color: #ffffff; margin: 1rem 0 0 0; font-size: 16px; line-height: 1.6;">
            <strong>90% of global procurement failures happen in the 'Data Gap' between the Chinese factory floor and your office.</strong><br><br>
            Stop relying on surface-level checks. Complete this assessment to run your strategy through the <strong>AIV Proprietary Risk Algorithm</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("aiv_audit_form"):
        st.markdown("<h4 style='color: #ffffff;'>Comprehensive Supply Chain Risk Assessment</h4>", unsafe_allow_html=True)
        st.markdown("---")
        
        answers = []
        for key, q_data in QUESTIONS.items():
            st.markdown(f"<h5 style='color: #00d4ff;'>{q_data['title']}</h5>", unsafe_allow_html=True)
            ans = st.radio("Select an option:", q_data['options'], key=key, label_visibility="collapsed")
            answers.append((ans, q_data['options'], q_data['scores']))
            st.markdown("<br>", unsafe_allow_html=True)
            
        st.markdown("---")
        # 👑 升级版的温柔留资文案
        st.markdown("<h5 style='color: #00d4ff;'>📩 Where should we send your customized intelligence?</h5>", unsafe_allow_html=True)
        st.markdown("""
        <div class="contact-note">
            Please provide your Business Email or WhatsApp. As a complimentary bonus, our audit team will manually send you the highly classified <b>[2026 China Generator Regional Power Matrix & Deep-Tier Supply Whitepaper]</b> (中国发电机产区底层战力分析白皮书), fully customized based on your specific power range answers today.<br><br>
            <i>* Note: A valid contact is required to ensure successful delivery of your documents. If left blank, you may not receive the full customized intelligence.</i>
        </div>
        """, unsafe_allow_html=True)
        
        contact_info = st.text_input("Business Email or WhatsApp Number:")
        
        submitted = st.form_submit_button("Run AI Proprietary Algorithm 🔍", use_container_width=True)

    if submitted:
        if not contact_info:
            st.error("⚠️ Please enter your Email or WhatsApp to receive your complimentary Whitepaper and report.")
        else:
            total_score = sum(scores[opts.index(ans)] for ans, opts, scores in answers)
            avg_score = total_score / 10.0
            
            if avg_score <= 2.9:
                risk_level, recommendation = "🟢 Level 1: SECURE (极度安全)", "Your supply chain demonstrates robust verification protocols. However, even top-tier setups require quarterly random verification to maintain integrity."
            elif avg_score <= 4.9:
                risk_level, recommendation = "🟡 Level 2: MONITORED (需监控)", "You have basic protections, but significant blind spots remain. Factories often exploit these gaps during high-volume periods."
            elif avg_score <= 6.9:
                risk_level, recommendation = "🟠 Level 3: ELEVATED RISK (中高风险)", "Warning: The 'Jiangsu Parts-Swap' trap is highly probable. Relying on your current evidence chain will result in failed claims."
            elif avg_score <= 8.9:
                risk_level, recommendation = "🔴 Level 4: HIGH RISK (极高危)", "URGENT: Your procurement is severely exposed. Do not release final payment. You are likely dealing with a sophisticated trading company masquerading as a source factory."
            else:
                risk_level, recommendation = "💀 Level 5: CRITICAL / GHOST FACTORY (幽灵工厂)", "CRITICAL ALERT: Your investment is in immediate danger. Halt all operations. An immediate AIV Premium On-Site Physical Audit ($3,500) is required to salvage your capital."
                
            st.session_state.avg_score = avg_score
            st.session_state.risk_level = risk_level
            st.session_state.recommendation = recommendation
            st.session_state.user_contact = contact_info
            
            st.success("✅ Assessment Complete! Algorithm has finalized your score.")
            
            st.markdown("""
            <div class="hook-box">
                <h3 style="color: #00d4ff; margin-top:0;">🔓 Unlock Your Exact Risk Score & Action Plan</h3>
                <p style="color: #ffffff; font-size: 16px;"><b>Pay just $19 to instantly reveal:</b></p>
                <ul style="color: #e0e0e0; font-size: 15px;">
                    <li><b>Your Exact SCRI Score (1.0 - 10.0)</b></li>
                    <li><b>Your 5-Tier Risk Classification</b></li>
                    <li><b>Actionable PDF Report</b></li>
                    <li>🎁 <b>Bonus:</b> 2026 China Regional Power Matrix Whitepaper</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.link_button("💳 Pay $19 to Unlock Full Report", "https://your-payment-link-here.com", type="primary", use_container_width=True)
            with col2:
                # 专门留给你的测试按钮！上线前可以把这行删掉
                if st.button("🛠️ Admin Bypass (跳过支付直接看报告)", use_container_width=True):
                    st.session_state.show_results = True
                    st.rerun()
