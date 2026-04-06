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

# 🔑 Stripe 秘钥配置 (这里填你真实的，测试阶段用 test key)
STRIPE_SECRET_KEY = "sk_test_XXXXXXXXXXXXXXXXXXXXXXXX"
stripe.api_key = STRIPE_SECRET_KEY

# 你的 Streamlit 网页最终地址 (用于支付完跳回来)
YOUR_APP_URL = "https://aiv-audit.streamlit.app" 

# ============================================================================
# 2. 顶级工业黑金 UI 样式
# ============================================================================
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #1a1c23; color: #ffffff; }
    [data-testid="stHeader"] { background-color: transparent; }
    h1, h2, h3, h4 { color: #00d4ff !important; font-weight: 700; }
    .stRadio label { color: #e0e0e0 !important; font-size: 16px; }
    div[data-testid="stForm"] { background-color: #252a33; border-left: 4px solid #00d4ff; padding: 2rem; border-radius: 8px; border: 1px solid #333; }
    .warning-banner { background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(176, 176, 176, 0.05) 100%); border: 1px solid #00d4ff; border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem; }
    .result-box { background-color: rgba(255, 0, 0, 0.1); border-left: 4px solid #ff4444; padding: 2rem; border-radius: 8px; margin-top: 2rem;}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 3. PDF 生成引擎 (纯后台逻辑)
# ============================================================================
def generate_pdf_report(avg_score, risk_level, recommendation):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#00d4ff'), alignment=1)
    normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=11, textColor=colors.black, spaceAfter=8)
    
    story.append(Paragraph("AIV Supply Chain Risk Assessment Report", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph(f"<b>Overall Risk Index:</b> {avg_score:.1f}/10", normal_style))
    story.append(Paragraph(f"<b>Risk Level:</b> {risk_level}", normal_style))
    story.append(Paragraph(f"<b>Expert Recommendation:</b> {recommendation}", normal_style))
    story.append(Spacer(1, 0.5*inch))
    
    story.append(Paragraph("Next Steps & Audit Packages:", styles['Heading2']))
    story.append(Paragraph("- Complete Verification ($700): Factory audit + Social security check", normal_style))
    story.append(Paragraph("- Premium On-Site ($3,500): Physical inspection + Video evidence", normal_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ============================================================================
# 4. 路由逻辑：判断是“刚进网页”还是“刚付完款回来”
# ============================================================================
query_params = st.query_params
is_success = query_params.get("payment") == "success"

if is_success and "avg_score" in st.session_state:
    # 🌟 支付成功页面：直接展示结果并提供 PDF 下载
    st.markdown("### 🔓 AIV Truth Report Unlocked")
    st.success("Payment verified. Your proprietary supply chain analysis is complete.")
    
    avg_score = st.session_state.avg_score
    risk_level = st.session_state.risk_level
    recommendation = st.session_state.recommendation
    
    # 屏幕直接输出震撼结果
    st.markdown(f"""
    <div class="result-box">
        <h2 style='color:#ff4444; margin-top:0;'>Your Risk Score: {avg_score:.1f}/10</h2>
        <h3 style='color:#ffffff;'>Status: {risk_level}</h3>
        <p style='color:#e0e0e0; font-size:16px;'>{recommendation}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 生成 PDF 并提供下载按钮
    pdf_buffer = generate_pdf_report(avg_score, risk_level, recommendation)
    st.download_button(
        label="📄 Download Detailed PDF Report",
        data=pdf_buffer,
        file_name=f"AIV_Risk_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        type="primary"
    )
    
    st.markdown("---")
    st.markdown("#### Ready to secure your supply chain?")
    st.markdown("Contact our lead auditor via WhatsApp or Email to execute the $700 Complete Verification.")

else:
    # 📝 正常填表页面
    st.markdown("### ⚙️ Axiom Industrial Verification (AIV)")
    st.markdown("""
    <div class="warning-banner">
        <h3 style="color: #00d4ff; margin-top: 0;">🚨 [AIV AUDIT WARNING]</h3>
        <p style="color: #d0d0d0; margin: 1rem 0 0 0; line-height: 1.6;">
            <strong>90% of global procurement failures happen in the 'Data Gap'.</strong> 
            Complete this assessment to run your procurement strategy through the <strong>AIV Proprietary Heavy Industry Risk Algorithm</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("aiv_audit_form"):
        st.markdown("#### Supply Chain Risk Assessment")
        
        q1 = st.radio("1. Delivery Stability", ["Zero disputes", "Minor issues", "High stress", "Unresolved failures"])
        q2 = st.radio("2. Critical Failure Type", ["Bait & Switch", "Logistics loopholes", "Refurbished components", "Compliance failure"])
        q3 = st.radio("3. Generator Power Range", ["200kW-300kW", "500kW-800kW", "1000kW-2000kW+"])
        q4 = st.radio("4. Environmental Compliance", ["Yes, custom high-spec", "Standard export model", "Not sure"])
        q5 = st.radio("5. Supplier Redundancy", ["Solid backup", "Rely on one source", "Crisis-based search"])
        q6 = st.radio("6. Identity Audit", ["Never verified", "Video only", "Trust 3rd-party only", "Deep data audit"])
        q7 = st.radio("7. Evidence Traceability", ["Full physical evidence", "Factory PDF only", "No evidence"])
        q8 = st.radio("8. Communication Audit", ["Factory translator", "English agent", "Native Chinese Technical Audit"])
        q9 = st.radio("9. Loading Process Control", ["Aware but no control", "Trust 3rd-party snapshot", "Full process data stream"])
        q10 = st.radio("10. Digital Genome Value", ["Invaluable", "Secondary to brand", "Need expert analysis"])
        
        submitted = st.form_submit_button("Analyze My Supply Chain 🔍", use_container_width=True)

    if submitted:
        # 算分逻辑
        answers = [q1, q2, q3, q4, q5, q6, q7, q8, q9, q10]
        risk_scores = {"Zero disputes": 1, "Minor issues": 3, "High stress": 7, "Unresolved failures": 10, "Bait & Switch": 10, "Logistics loopholes": 8, "Refurbished components": 9, "Compliance failure": 10, "200kW-300kW": 5, "500kW-800kW": 6, "1000kW-2000kW+": 7, "Yes, custom high-spec": 2, "Standard export model": 5, "Not sure": 8, "Solid backup": 2, "Rely on one source": 8, "Crisis-based search": 10, "Never verified": 10, "Video only": 6, "Trust 3rd-party only": 5, "Deep data audit": 1, "Full physical evidence": 1, "Factory PDF only": 6, "No evidence": 10, "Factory translator": 7, "English agent": 5, "Native Chinese Technical Audit": 1, "Aware but no control": 8, "Trust 3rd-party snapshot": 6, "Full process data stream": 2, "Invaluable": 1, "Secondary to brand": 6, "Need expert analysis": 8}
        
        scores = [risk_scores.get(answer, 5) for answer in answers]
        avg_score = sum(scores) / len(scores)
        
        if avg_score <= 4:
            risk_level, recommendation = "🟡 MODERATE RISK", "Your supply chain shows resilience, but hidden blind spots remain. Monitor closely."
        elif avg_score <= 7:
            risk_level, recommendation = "🔴 HIGH RISK", "Vulnerabilities detected. The 'Jiangsu Parts-Swap' trap is a high probability. Upgrade to $700 Complete Verification."
        else:
            risk_level, recommendation = "🚨 CRITICAL RISK", "Your procurement is highly exposed to 'Ghost Factory' fraud. Immediate physical on-site audit ($3,500) required."
            
        # 把算好的分数存入 session_state，等客户付完钱回来还要用
        st.session_state.avg_score = avg_score
        st.session_state.risk_level = risk_level
        st.session_state.recommendation = recommendation
        
        st.success("✅ Assessment Complete! Algorithm analysis finished.")
        st.markdown("### 🔒 Unlock Your Truth Report")
        st.markdown("Pay $19 to reveal your exact SCRI score, risk level, and download the full PDF report.")
        
        # Stripe 支付跳转
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": "AIV SCRI Risk Report"},
                        "unit_amount": 1900,
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url=f"{YOUR_APP_URL}/?payment=success",
                cancel_url=f"{YOUR_APP_URL}/?payment=cancelled",
            )
            st.link_button("💳 Pay $19 to Unlock Result", session.url, type="primary")
        except Exception as e:
            st.error("Payment system currently configuring. Please try again later.")
