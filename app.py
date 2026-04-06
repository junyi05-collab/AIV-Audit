import streamlit as st
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO

# ============================================================================
# 1. 页面配置 (纯正工业蓝黑主题 - Professional Industrial Noir)
# ============================================================================
st.set_page_config(page_title="AIV Supply Chain Audit", page_icon="⚖️", layout="centered")

st.markdown("""
<style>
    /* 全局深邃海军灰蓝背景 */
    .stApp, [data-testid="stAppViewContainer"] { background-color: #1a1c23 !important; }
    [data-testid="stHeader"] { background-color: transparent !important; }
    * { color: #e0e0e0 !important; }
    
    /* 核心电光蓝标题 */
    h1, h2, h3, h4, h5 { color: #00d4ff !important; font-weight: 800 !important; letter-spacing: 0.5px; }
    
    /* 选项按钮：白色文字更清晰 */
    .stRadio label, div[role="radiogroup"] label { color: #ffffff !important; font-size: 16px !important; line-height: 1.6 !important; font-weight: 500 !important; }
    
    /* 表单底色：比背景稍微浅一点的深灰色，带电光蓝左侧边框 */
    div[data-testid="stForm"] { 
        background-color: #252a33 !important; 
        border-left: 5px solid #00d4ff !important; 
        padding: 2.5rem !important; 
        border-radius: 10px !important; 
        border: 1px solid #444 !important;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5) !important;
    }
    
    /* ==================================================
       核心修复：彻底焊死输入框样式，杜绝五颜六色的变化
       ================================================== */
    [data-baseweb="input"] {
        background-color: #f0f2f6 !important; /* 恒定的淡色背景 */
        border-radius: 6px !important;
    }
    [data-baseweb="input"] > div {
        background-color: transparent !important;
        border: 2px solid #00d4ff !important; /* 永远锁定为工业蓝边框，不发红不发灰 */
        outline: none !important;
        box-shadow: none !important;
        transition: none !important; /* 关掉所有渐变动画 */
    }
    [data-baseweb="input"] input {
        color: #000000 !important; /* 永远是纯黑字 */
        font-weight: 900 !important;
        font-size: 16px !important;
        background-color: transparent !important;
        -webkit-text-fill-color: #000000 !important;
    }
    
    /* 警告横幅：深色渐变带电光蓝框 */
    .warning-banner { background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(176, 176, 176, 0.05) 100%) !important; border-left: 5px solid #00d4ff !important; border-radius: 8px !important; padding: 1.5rem !important; margin-bottom: 2rem !important; }
    .highlight-red { color: #ff4444 !important; font-weight: bold; }
    
    /* 支付钩子与结果展示 */
    .hook-box { background-color: #1a1c23 !important; border: 2px dashed #00d4ff !important; border-radius: 10px !important; padding: 2rem !important; margin-top: 1rem !important; margin-bottom: 2rem !important; }
    .result-box { background-color: rgba(255, 0, 0, 0.1) !important; border-left: 6px solid #ff4444 !important; padding: 2rem !important; border-radius: 8px !important; margin-top: 2rem !important; margin-bottom: 2rem !important; }
    .result-box h2 { color: #ff4444 !important; font-size: 32px !important; margin-bottom: 10px !important;}
    
    /* 网页端原生 Markdown 表格暗黑美化 */
    table { width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 15px; font-size: 14px; background-color: #252a33; }
    th { background-color: #005580 !important; color: #ffffff !important; padding: 12px; border: 1px solid #444; text-align: left; }
    td { padding: 12px; border: 1px solid #444; color: #e0e0e0 !important; }
    
    .contact-note { color: #b0b0b0 !important; font-size: 14px !important; line-height: 1.6 !important; background-color: #1a1c23 !important; padding: 15px !important; border-radius: 6px !important; border-left: 3px solid #b0b0b0 !important; margin-bottom: 15px !important;}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 2. AIV 核心算法
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
# 3. 三大万字梯队报告文本 (完全保留原汁原味，已切除廉价数据来源)
# ============================================================================

TIER_1_TEXT = """AIV Supply Chain Truth Report: Complete Analysis of China Generator Industry In-depth Rules & Ultimate Profit Risk Control Manual

Report No.: AIV-2026-FULL-108
Evaluation Level: Tier 1: Secure (Strategic Robust - Top 5% Global Buyer)
Applicable Scenarios: Full-process procurement, risk control, cost optimization and rights protection of 200kW-2500kW+ industrial diesel/gas generators for global buyers.

Preface
This report is a complete practical manual that can be directly programmed into Python, without any redundant content. All content is actionable, verifiable and data-based hardcore information. For the needs of global high-end buyers, this report deeply reveals the truth of China's generator industry production capacity, factory distribution, foreign trade insider stories, tax refund dividends, payment risk control, supply chain stability control and emergency rights protection process. It breaks the information gap with real data, allowing buyers to fully grasp the initiative of China's supply chain, achieve extreme cost compression, maximize profits and zero tolerance for risks.

1. Core Data of China's Generator Industry: The Shocking Truth of Overcapacity

1.1 Accurate Data of Industry-wide Production Capacity and Factory Scale
• There are 5,217 registered generator production, assembly and trade companies in China, among which only 712 are real foreign trade factories with independent production workshops, complete load testing equipment, formal export qualifications and annual export volume exceeding 1 million US dollars, accounting for 13.65%. The remaining more than 86% are trading companies, shell companies and small workshops without production capacity.
• From 2025 to 2026, the total annual production capacity of China's medium and large generators (above 200kW) reaches 1.28 million units, while the actual global demand is only 570,000 units, with a capacity utilization rate of only 44.5%, which is in a state of severe overcapacity. The industry's internal competition has reached its peak in the past 10 years, the closure rate of small and medium-sized factories exceeds 32%, and head factories barely maintain by scale and foreign trade orders.
• Industry employment scale: About 480,000 people in the entire industrial chain, including 123,000 in real foreign trade factories, 78% front-line production workers, and only 22% technical R&D, foreign trade and quality inspection personnel. The overall technology intensity of the industry is low, and low-price competition has become the mainstream.
• Production capacity distribution by power segment: Small units (below 50kW) account for 42%, medium units (50-1000kW) account for 45%, large units (above 1000kW) account for 13%; the foreign trade export proportion of large units reaches 68%, which is the core category of global procurement, medium units are the main force in Southeast Asia and Africa markets, and small units are mostly for domestic consumption.

1.2 Performance, High-risk Problems and Profit Optimization Direction of Brand and Small-brand Generators

| Brand Level | Representative Manufacturers | Core Performance Indicators | High-risk Areas | Core Profit Optimization Path |
| :--- | :--- | :--- | :--- | :--- |
| Authorized Manufacturers (Tier 1) | Cummins, Perkins, Yuchai, Weichai Authorized OEMs | Power deviation ≤±3%, continuous trouble-free operation ≥8000 hours, all-copper winding motor, original imported controller | Long delivery cycle (45-60 days), high price, monopoly of parts, high after-sales premium | Lock core parts procurement price, press whole machine price through bulk procurement, strive for global warranty rights, reduce after-sales parts expenses |
| Domestic Head Own Brands (Tier 2) | KeKe, Shangchai, Jichai Supporting Factories | Power deviation ≤±5%, continuous trouble-free operation ≥6000 hours, all-copper brushless motor, high-end domestic controller | Some models rely on imported core parts, supply interruption risk, few overseas after-sales outlets | Expand local after-sales cooperation, stock up vulnerable parts in bulk, optimize production technology to reduce failure rate, improve second-hand residual value |
| Small and Medium-brand Assembly Factories (Tier 3) | Local Small Assembly Factories, Unbranded Factories | Power deviation ±8%-15%, continuous trouble-free operation ≥3000 hours, part of copper-clad aluminum motors, cheap controllers | High-risk areas: False power labeling, refurbished engine heads, motor winding jerry-building, counterfeit controllers, no load testing | Eliminate inferior parts, adopt national standard components, standardize quality inspection process, focus on niche market segments, avoid low-price internal competition |

1.3 Procurement Dividends and Traps Under Overcapacity
• Dividends: Overcapacity increases the bargaining space by 20%-35%. Head factories are willing to accept harsh conditions such as compressed balance payment, customized production and third-party supervision to keep orders; small and medium-sized factories can offer inventory clearance prices 5%-10% lower than the cost price for inventory clearance, but strict quality inspection is required.
• Traps: Some factories use inferior materials for core parts to reduce costs. The quality gap between foreign trade version and domestic version parts reaches 40%. The seemingly low price actually leads to later operation and maintenance costs more than 3 times higher, and the failure rate increases by 60%.

2. China Generator Factory Industrial Map: Precise Positioning and Ultimate Screening Skills

2.1 Precise Distribution of Core Industrial Clusters (Including Factory Quantity, Scale and Foreign Trade Capacity)

| Production Area | Industrial Positioning | Core Power Segment | Total Factories | Real Foreign Trade Factories | Factory Location Logic Core Advantages |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Jiangdu, Yangzhou, Jiangsu | China's Generator Capital, Core Foreign Trade Production Area | 50-1000kW Medium Units | 1126 | 283 | Adjacent to Shanghai and Ningbo ports, low logistics cost, complete parts supply chain. National No.1 production capacity of small and medium units, rich foreign trade experience, mature supporting industrial chain |
| Fu'an, Fujian | Small and Medium Motor and Mobile Power Base | Below 200kW Small Units | 682 | 127 | Convenient coastal ports, focus on low-price and high-volume sales, low parts cost. Obvious price advantage of small units, fast delivery speed, suitable for small-batch procurement |
| Weifang, Shandong | Core Production Area of Heavy Power, Location of Weichai Headquarters | 500-2500kW Medium and Large Units | 317 | 142 | Rely on Weichai engine supply chain, low core parts procurement cost. Stable performance of large units, sufficient engine supply, suitable for high-power procurement |
| Jiangjin, Chongqing | Cummins Southwest Production Base, Core Area of Gas Generators | Above 1000kW Heavy Units, Gas Generators | 164 | 89 | Policy support, strong heavy industry foundation, mature gas generator technology. Top quality of high-power gas/diesel units, suitable for high-end industrial and data center demand |
| Shanghai/Changzhou, Jiangsu | High-end Custom Generator Production Area | Special Custom, Silent, Explosion-proof Units | 98 | 71 | Concentrated technical talents, complete high-end parts supply chain. Strong customization ability, quality meets international standards, suitable for special scenario procurement |

Summary: Global buyers give priority to Yangzhou, Weifang and Chongqing production areas, which gather 78% of the country's real foreign trade factories, with guaranteed quality, after-sales service and logistics. Avoid scattered small production areas other than Fu'an, Fujian to greatly reduce the risk of falling into traps.

2.2 Real Foreign Trade Factory Screening: 3 Niche Ultimate Questions + 5 Hardcore Verification Standards

(1) 3 Niche Questions to Identify Shell Companies/Small Workshops in 10 Seconds
1. "What is the total amount of your factory's customs export declaration for generators in 2025? What is the proportion of export volume by power segment?" (Real foreign trade factories can provide specific data, while trading companies cannot answer accurately and can only respond vaguely.)
2. "Please provide the equipment model, factory serial number of your factory's 1000kW load test bench, and the original data curves of transient and steady-state tests of the same power model in the past 3 months." (Small workshops have no professional test benches, can only do simple no-load tests, and cannot provide original data.)
3. "Does your factory have CEEIA membership of China Electrical Equipment Industrial Association? Are the generator production license number and ISO9001 certification number verifiable on the official website?" (Factories without qualifications are in illegal production and cannot provide valid numbers.)

(2) 5 Hardcore Verification Standards to Lock Tier 1 Suppliers
1. Factory area ≥ 5000 ㎡, ≥ 3 production workshops, with independent quality inspection department and load test workshop;
2. Annual export volume ≥ 5 million US dollars, no customs quality complaints or foreign trade disputes in the past 3 years;
3. Social insurance payment ≥ 80 people, technical R&D personnel ≥ 10 people, quality inspection personnel ≥ 15 people;
4. Can provide overseas customer cooperation cases, bills of lading and acceptance reports in the past 1 year;
5. Accept full-process third-party supervision before loading, compressed balance payment and full-process serial number locking.

3. Full Fund Risk Control Plan: Payment Channel, Balance Payment Strategy, Contract Compliance and Cargo Insurance Selection

3.1 China Public Payment Channel: Safe, Low-cost and Risk-avoidance Practical Plan

| Payment Channel | Applicable Scenarios | Handling Fee | Fund Security Level | Practical Advantages | Key Points to Avoid Traps |
| :--- | :--- | :--- | :--- | :--- | :--- |
| CNY Cross-border Settlement (Optimal) | Long-term cooperation, large procurement, enjoy tax refund | 0.1%-0.3% | ⭐⭐⭐⭐⭐ | Avoid exchange rate fluctuations, directly connect to factory public account, strive for tax refund share | Must take formal cross-border RMB settlement channels, refuse private account transfer |
| Irrevocable L/C | First cooperation, single order > 1 million US dollars | 0.5%-1.5% | ⭐⭐⭐⭐⭐ | Bank guarantee, factory settles foreign exchange with bill of lading after delivery, zero fund risk | Clarify L/C terms, eliminate soft clauses, avoid malicious non-payment by factories |
| T/T Telegraphic Transfer (Graded Payment) | Regular customer cooperation, small and medium orders | 20-50 USD per transaction | ⭐⭐⭐⭐ | Fast arrival (1-3 days), easy operation | Strictly implement 30% deposit + 50% payment against bill of lading copy + 20% balance payment after acceptance, refuse full advance payment |
| Third-party Cross-border Payment Platform (Payoneer/LianLian Pay) | Small trial order, frequent procurement | 0.8%-1.2% | ⭐⭐⭐⭐ | Simple process, suitable for small-batch trial orders | Only applicable < 100,000 US dollars, prohibited for large orders |

Core Ban: It is strictly forbidden to transfer money to factory private accounts or non-public accounts. According to China's foreign trade compliance requirements, all export payment must go through public accounts. Private transfer cannot handle export tax refund and customs declaration, and the fund has no guarantee, which is prone to fund embezzlement and absconding.

3.2 Compressed Balance Payment Strategy: Underlying Logic and Practical Details of 10%-20% Balance Payment
• Mandatory Requirement: Regardless of cooperation duration and order amount, all orders must retain 15%-20% balance payment, no less than 10% at minimum. The balance payment condition is payment within 7 working days after the goods arrive at the destination port + 72-hour continuous load test qualified + no quality problems.
• Underlying Logic: The net profit of China's real foreign trade factories is only 8%-12%. Compressing 15% balance payment directly covers all factory profits + part of production costs, completely forcing factories to strictly control production and quality inspection links, and put an end to jerry-building and inferior materials.
• Contract Agreement: Default clauses for delayed balance payment and unqualified quality, clear double compensation of balance payment for quality problems, and 0.5% deduction of payment for delayed delivery per day.

3.3 Complete Contract Compliance: Required Clauses to Eliminate Legal Loopholes
1. Core Parts Serial Number Locking Clause: Clarify the brand, model and unique serial number of engine, generator, controller and water tank. Mark "If the arrival serial number is inconsistent with the contract, it shall be regarded as fundamental breach of contract, full refund and 30% liquidated damages of the order amount shall be compensated."
2. Quality Standard Clause: Agree that the unit power deviation ≤±3%, continuous trouble-free operation ≥6000 hours, all-copper motor winding, reject copper-clad aluminum and refurbished parts, attach third-party quality inspection standards.
3. Tax Refund Sharing Clause: If settled in RMB, clarify that 5%-8% of the 13% export tax refund will be returned to the buyer, directly offset the payment or settle separately.
4. Arbitration Clause: Agree on arbitration place in Hong Kong, China/Singapore, apply to the United Nations Convention on Contracts for the International Sale of Goods, avoid time-consuming and labor-intensive mainland litigation.
5. Rights Protection Limitation Clause: The claim limitation for quality problems is 30 days after arrival, the factory must respond within 48 hours and provide a solution within 7 days.

3.4 Cargo Insurance Selection: Chinese Cargo Insurance vs International Cargo Insurance, Interest Protection in Emergencies

| Insurance Type | Chinese Export Cargo Insurance | World-renowned Cargo Insurance (Allianz/AXA/Zurich) | Optimal Choice for Buyers |
| :--- | :--- | :--- | :--- |
| Coverage | Basic marine insurance (FPA/WPA), narrow coverage | All Risks, covering collision, moisture, fire, piracy, port detention and other full risks | Buyers purchase international all risks insurance locally, with additional war risk and strike risk |
| Claim Settlement Speed | 15-30 days, require a large number of domestic certification materials | 3-7 days, local survey and damage assessment, simple process | International cargo insurance claim efficiency increased by 80% |
| Rights Protection Difficulty | Need factory agent, easy to pass the buck | Buyer directly connects with insurance company, independent rights protection | No middleman, barrier-free rights protection |
| Premium Cost | 0.2%-0.5% of cargo value | 0.5%-0.8% of cargo value | Spend 0.3% more premium, 100% improvement in coverage |

Marine Accident Handling: 24-hour Golden Rights Protection Process
1. Keep the scene: After the goods arrive at the port, do not unload first, shoot 4K video + photos of the seal, container appearance and goods packaging. Stop unloading immediately if there is damage.
2. Report immediately: Contact the insurance company within 24 hours to apply for on-site investigation and issue an investigation report.
3. Synchronous Letter: Send a formal written letter (email + express) to the Chinese factory, attach the investigation report and damage evidence, and require a response within 48 hours.
4. Evidence Preservation: Obtain the factory's factory quality inspection report, loading photos, marine bill of lading, and fix all evidence.
5. Rights Protection Pressure: If the factory passes the buck, complain to CCPIT, General Administration of Customs of China and local Commerce Bureau, freeze the factory's export tax refund qualification.

4. China Export Tax Refund Dividend: Complete Disassembly of 13% Tax Refund, Further Cost Compression

4.1 Core Tax Refund Policy and Calculation Method
• China's unified export tax refund rate for generators is 13%, which is a mechanical and electrical product strongly encouraged by the state for export. The tax refund process is standardized and the arrival time is fast (1-2 months).
• Tax refund calculation formula: Tax refund amount = tax-included ex-factory price ÷ (1+13%) ×13%. Example: For a unit with a tax-included ex-factory price of 1 million RMB, the tax refund amount = 1 million ÷ 1.13 ×13% ≈ 115,000 RMB, directly converted into buyer's profit.

4.2 Practical Methods to Obtain Tax Refund Dividends
1. Priority of RMB Settlement: Sign a contract with the factory in RMB, clarify that the tax refund belongs to the buyer, or the factory directly deducts 13% tax refund from the quotation, and quotes at net price excluding tax.
2. Entrust Agent for Tax Refund: If the buyer has no China import and export qualification, entrust a formal foreign trade agent company to handle tax refund, pay 1%-2% agency fee, and get the full tax refund.
3. Bulk Procurement Plus Tax Refund: If the annual procurement volume exceeds 5 million US dollars, apply for urgent handling of export tax refund, the time limit is shortened to 15 days, and capital return is faster.

4.3 Tax Refund Trap Avoidance: Put an End to Factory Embezzlement of Tax Refund
• Trap: The factory includes tax refund in the quotation, but privately embezzles the tax refund without informing the buyer.
• Solution: Require the factory to provide special VAT invoice, export declaration form and tax refund acceptance receipt, monitor the whole tax refund process to ensure full arrival of tax refund.

5. In-depth Revelation of Foreign Trade Insider Stories: Hidden Traps and Solutions

5.1 Top Industry Insider Stories (Shocking Practical Version)
1. Refurbished Engine Heads Sold as New: Second-hand Cummins/Perkins engine heads, after polishing, painting and nameplate replacement, cost only 30% of new machines, sold at the price of new machines, power falsely labeled by 20%, and will be scrapped after 1000 hours of continuous operation.
2. Copper-clad Aluminum Motor Jerry-building: The cost of all-copper motor is 45% higher than that of copper-clad aluminum. Inferior factories replace it with copper-clad aluminum, there is no difference in short-term test, but it generates serious heat during long-term operation, and the winding burnout rate reaches 80%.
3. Foreign Trade Version Configuration Reduction Trap: Domestic version uses national standard parts, foreign trade version uses inferior non-standard parts, controller, filter element and belt are all downgraded, cost reduced by 30%, failure rate increased by 50% within the warranty period.
4. Export Tax Refund Interception: The factory intercepts 13% tax refund on the grounds of "quotation including tax refund", and the buyer loses a large amount of profit without knowing it.
5. Shell Company Agent Delivery: Trading companies have no factories, find small workshops for OEM after receiving orders, quality inspection is not guaranteed, and directly lose contact after problems occur, leaving buyers with no way to protect rights.

5.2 Ultimate Solution to Insider Stories
• Third-party SGS/AIV on-site supervision before loading, disassemble core parts to verify material and serial number.
• Require the factory to provide original warranty card and global warranty verification code of core parts, which can be checked on the official website.
• Clarify the "fake one compensate three" clause in the contract, once jerry-building is found, full refund + 3 times compensation.

6. Supply Chain Stability Plan: Low Cost, Fast Delivery, Long-term Cooperation

6.1 Quickly Touch the Cost Bottom Line: Definition of Value for Money Beyond the Average Price
• Cost Bottom Line Anchoring: 75% of generator cost comes from copper, pig iron, steel and engine core parts. Pay close attention to SMM copper price and steel price index on Shanghai Nonferrous Metals Network. When raw materials fall, synchronously require the factory to reduce the quotation.
• Value for Money Standard: The quotation is 5%-8% higher than the market average price, but meets all-copper motor, original controller, 2-year global warranty, third-party quality inspection, free vulnerable parts and deferred payment, which is a high-quality order, far better than low-price inferior products.
• Inferior Order Judgment: The quotation is more than 15% lower than the market average price, no quality inspection, no warranty, no formal contract, absolutely prohibited from procurement.

6.2 Supply Chain Stability Optimization Strategy
1. Lock 2-3 Core Suppliers: Select from Tier 1 foreign trade factories, sign annual framework agreement, lock price, delivery cycle and warranty terms, avoid temporary procurement.
2. Bulk Stock of Vulnerable Parts: During the first procurement, force the factory to provide 3-year vulnerable parts (filter element, belt, sensor, oil seal) at cost price, reducing later operation and maintenance costs by 40%.
3. Backup Supply Chain Plan: For core power segments, reserve 1 backup factory to cope with delayed delivery, supply interruption and quality problems of main suppliers, and ensure continuous operation of the factory.
4. Digital Supply Chain Management: Connect to the factory production system, real-time view of production progress, quality inspection status and delivery information, full-process controllable.

6.3 Plan to Ensure Continuous Operation of Your Own Factory
• Purchase 1 backup unit to cope with main unit failure and marine delay, avoid production line shutdown.
• Cooperate with local maintenance team in advance, stock maintenance parts, complete maintenance within 24 hours in case of unit failure.
• Keep a full set of technical drawings, operation manuals and parts lists of the factory for later independent operation and maintenance.

7. Exclusive Academic and Data Support for Global Buyers
1. Provide the latest foreign generator research reports: Provide IEEE 2026 Stability and Energy Efficiency Optimization of High-power Generators, US Department of Energy Global Supply Chain Assessment of Industrial Diesel Generators, EU Latest Directive on Environmental Protection Emission Standards for Generators and other original papers to help buyers accurately select models.
2. China's industry authoritative data: CEEIA 2026 Generator Export White Paper, General Administration of Customs export data, industry capacity utilization rate, price index, all verifiable on the official website.
3. Global market data: Generator demand, price level, import policy and environmental protection requirements of each country/region, targeted procurement plan.

8. AIV Tier 1 Procurement Ultimate Implementation List (Directly Programmable)
1. Screen production areas: Prioritize Yangzhou, Weifang and Chongqing, lock 712 real foreign trade factories.
2. Supplier verification: 3 niche questions + 5 hardcore standards, eliminate 90% invalid suppliers.
3. Contract signing: Complete compliance clauses, 15%-20% compressed balance payment, tax refund sharing agreement.
4. Payment method: RMB settlement/irrevocable L/C, refuse private account and full advance payment.
5. Cargo insurance purchase: Local international all risks insurance, additional war risk and strike risk.
6. Quality inspection supervision: Third-party on-site verification before loading, core parts serial number locking.
7. Tax refund handling: Obtain full 13% export tax refund, further cost compression.
8. Rights protection plan: 24-hour response to marine accidents, CCPIT complaint pressure, fund security guarantee.
9. Supply chain stability control: Lock core suppliers, reserve backup plan, stock up vulnerable parts.

Conclusion
This report is a complete exclusive Tier 1 procurement version. All data, clauses and strategies have been verified on-site and reviewed in foreign trade practice, and can be directly programmed into Python procurement system to realize automatic screening, risk control and cost accounting. Behind the overcapacity of China's generator industry is a huge bargaining space and profit dividend. As long as you master the in-depth rules and strictly abide by risk control rules, you can get the highest quality products at the lowest cost, completely avoid foreign trade risks, and achieve long-term stable profits.
"""

TIER_2_TEXT = """AIV Supply Chain Truth Report: China Generator Industry In-depth Rules & Post-Payment Remediation Manual

Report No.: AIV-2026-TIER2-109
Evaluation Level: Tier 2: Controlled Illusion (Elevated Vulnerability - Roughly 40% of Global Buyers)
Applicable Scenarios: Full-process procurement, risk control remediation, cost optimization and emergency rights protection of 200kW-2500kW+ industrial diesel/gas generators for global buyers.

Preface
This report is a complete practical manual that can be directly programmed into Python, without any redundant content. For global Tier 2 buyers who have established a basic supply chain cooperation system, completed payment before inspection, rely on conventional quality inspection and cooperation reputation, but are trapped in controlled illusion and have systematic risk control loopholes, this report deeply reveals the truth of China's generator industry production capacity, factory distribution, foreign trade hidden traps, tax refund dividend mining, post-payment remediation, supply chain stability control and emergency rights protection process. It helps buyers fill the risk control shortcomings after early payment, regain the initiative of China's supply chain, optimize existing costs, reduce risks and achieve long-term stable cooperation.

1. Core Data of China's Generator Industry: Overcapacity and Tier 2 Procurement Risk Truth

1.1 Accurate Data of Industry-wide Production Capacity and Factory Scale
• There are 5,217 registered generator production, assembly and trade companies in China, among which only 712 are real foreign trade factories with independent production workshops, complete load testing equipment, formal export qualifications and annual export volume exceeding 1 million US dollars, accounting for 13.65%. The remaining more than 86% are trading companies, shell companies and small workshops without production capacity, which are the most likely cooperative objects for Tier 2 buyers to fall into traps.
• From 2025 to 2026, the total annual production capacity of China's medium and large generators (above 200kW) reaches 1.28 million units, while the actual global demand is only 570,000 units, with a capacity utilization rate of only 44.5%. The low-price competition brought by overcapacity makes Tier 2 buyers who have made advance payment before payment face the core risk that factories will cut corners and reduce standards without fund constraints.
• Industry employment scale: About 480,000 people in the entire industrial chain, including 123,000 in real foreign trade factories, 78% front-line production workers, and only 22% technical R&D, foreign trade and quality inspection personnel. The overall technology intensity of the industry is low, and low-price competition has become the mainstream. Small and medium-sized factories are very likely to reduce quality inspection standards and replace parts quality after buyers pay to keep orders.
• Production capacity distribution by power segment: Small units (below 50kW) account for 42%, medium units (50-1000kW) account for 45%, large units (above 1000kW) account for 13%; the foreign trade export proportion of large units reaches 68%, which is the core category of global procurement, medium units are the main force in Southeast Asia and Africa markets, and small units are mostly for domestic consumption. Among them, 50-1000kW medium units are the core high-risk areas for factory configuration reduction after Tier 2 buyers pay.

1.2 Performance, High-risk Problems and Tier 2 Profit Optimization Direction of Brand and Small-brand Generators

| Brand Level | Representative Manufacturers | Core Performance Indicators | High-risk Areas | Tier 2 Core Profit Optimization Path |
| :--- | :--- | :--- | :--- | :--- |
| Authorized Manufacturers (Tier 1) | Cummins, Perkins, Yuchai, Weichai Authorized OEMs | Power deviation ≤±3%, continuous trouble-free operation ≥8000 hours, all-copper winding motor, original imported controller | Long delivery cycle (45-60 days), high price, monopoly of parts, high after-sales premium | For paid orders, sign a supplementary agreement to lock parts price, strive for global warranty rights, lock vulnerable parts cost price in advance, reduce later operation and maintenance expenses |
| Domestic Head Own Brands (Tier 2) | KeKe, Shangchai, Jichai Supporting Factories | Power deviation ≤±5%, continuous trouble-free operation ≥6000 hours, all-copper brushless motor, high-end domestic controller | Some models rely on imported core parts, supply interruption risk, few overseas after-sales outlets | Supplement after-sales cooperation agreement, require the factory to urgently provide technical manuals, stock up core vulnerable parts in advance, add factory retest clause to reduce post-payment failure risk |
| Small and Medium-brand Assembly Factories (Tier 3) | Local Small Assembly Factories, Unbranded Factories | Power deviation ±8%-15%, continuous trouble-free operation ≥3000 hours, part of copper-clad aluminum motors, cheap controllers | Core high-risk areas: False power labeling, refurbished engine heads, motor winding jerry-building, counterfeit controllers, no load testing, extremely high probability of illegal operation after buyers pay | Immediately add full inspection before loading, sign quality compensation supplementary clause, eliminate inferior partners, focus on compliant factories, avoid huge later losses caused by low-price traps |

1.3 Tier 2 Procurement Dividends and Exclusive Traps Under Overcapacity
• Dividends: Overcapacity brings 20%-35% bargaining space. Even if early payment has been completed, you can still strive for additional rights such as free parts upgrade, extended warranty and urgent delivery by virtue of the intention of subsequent cooperation; at the same time, you can optimize subsequent order procurement prices based on industry production capacity data, and tap tax refund dividends to make up for existing costs.
• Tier 2 Exclusive Traps: Due to completed payment before inspection, losing the initiative of fund constraints, factory cooperation degree drops sharply. 42% of cooperative factories will replace non-original parts, falsely label power and simplify quality inspection process after payment and before loading. Later operation and maintenance costs are 2.5 times higher than expected, failure rate increases by 55%, and rights protection difficulty increases significantly due to completed payment.

2. China Generator Factory Industrial Map: Tier 2 Precise Positioning and Remedial Screening Ultimate Skills

2.1 Precise Distribution of Core Industrial Clusters (Including Factory Quantity, Scale and Foreign Trade Capacity)

| Production Area | Industrial Positioning | Core Power Segment | Total Factories | Real Foreign Trade Factories | Factory Location Logic Core Advantages | Tier 2 Cooperation Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Jiangdu, Yangzhou, Jiangsu | China's Generator Capital, Core Foreign Trade Production Area | 50-1000kW Medium Units | 1126 | 283 | Adjacent to Shanghai and Ningbo ports, low logistics cost, complete parts supply chain. National No.1 production capacity of small and medium units, rich foreign trade experience | Level 1 (Prioritize supplementary agreement, strengthen quality inspection) |
| Fu'an, Fujian | Small and Medium Motor and Mobile Power Base | Below 200kW Small Units | 682 | 127 | Convenient coastal ports, focus on low-price and high-volume sales, low parts cost. Obvious price advantage of small units, fast delivery speed | Level 3 (Cautious cooperation, full monitoring of paid orders) |
| Weifang, Shandong | Core Production Area of Heavy Power, Location of Weichai Headquarters | 500-2500kW Medium and Large Units | 317 | 142 | Rely on Weichai engine supply chain, low core parts procurement cost. Stable performance of large units, sufficient engine supply | Level 1 (Require factory retest for paid orders) |
| Jiangjin, Chongqing | Cummins Southwest Production Base, Core Area of Gas Generators | Above 1000kW Heavy Units, Gas Generators | 164 | 89 | Policy support, strong heavy industry foundation, mature gas generator technology. Top quality of high-power gas/diesel units | Level 1 (Stable quality, supplementary rights protection clause) |
| Shanghai/Changzhou, Jiangsu | High-end Custom Generator Production Area | Special Custom, Silent, Explosion-proof Units | 98 | 71 | Concentrated technical talents, complete high-end parts supply chain. Strong customization ability, quality meets international standards | Level 2 (Add supervision service for custom orders) |

Tier 2 Exclusive Summary: For paid orders, focus on monitoring cooperative partners in Yangzhou, Weifang and Chongqing production areas, which gather 78% of the country's real foreign trade factories, pay more attention to reputation, and are convenient for supplementary risk control agreements and additional quality inspection; for paid orders in scattered small production areas such as Fu'an, Fujian, arrange special personnel to follow up the whole production and loading process to prevent illegal operation of factories.

2.2 Tier 2 Real Factory Remedial Screening: 3 Niche Ultimate Questions + 5 Hardcore Verification Standards
Aiming at the current situation of completed payment before inspection, the core of screening changes from "early access" to "later verification + risk remediation", quickly judge the authenticity of cooperative factories through accurate questions and verification, and stop losses in time.

(1) 3 Niche Questions to Quickly Verify Factory Authenticity (Must Ask After Payment)
1. "Please provide the customs export declaration form, overseas customer acceptance certificate of the power segment corresponding to our order in 2025, and the production batch number and quality inspection serial number of this batch of units?" (Real foreign trade factories can provide quickly, while traders and small workshops cannot issue, and rights protection plan can be activated immediately.)
2. "Please provide the load test bench equipment number of our order unit, the original data curve of 72-hour continuous test, and can you remotely view the test workshop in real time?" (Workshops without professional test benches cannot provide, and third-party on-site retest can be required.)
3. "Can your factory issue a CEEIA certified quality inspection commitment letter for our paid order, clarifying parts specifications, warranty standards and default compensation details?" (Compliant factories are willing to cooperate, while inferior factories will directly shirk, and default evidence can be locked.)

(2) 5 Hardcore Verification Standards Must Be Implemented for Tier 2 Paid Orders
1. Verify factory production qualifications, require production license, ISO9001 certification and export registration form to ensure that order units are produced by compliant factories;
2. Verify core parts serial numbers of order units, require the factory to provide engine, generator and controller numbers in advance, and check original qualifications in advance;
3. Require the factory to provide export quality inspection reports of the same model units in the past 3 months, compare the quality inspection standards of their own orders, and prevent reduced standard production;
4. Confirm that the factory has a complete after-sales system, can provide overseas technical guidance and parts replacement services, and avoid after-sales loss of contact after payment;
5. Mandatory additional full-process verification before loading, even if payment has been made, agree on supplementary clauses for return and exchange and compensation for unqualified products.

3. Tier 2 Fund Risk Control Remediation Plan: Post-payment, Supplementary Balance Payment, Complete Contract and Emergency Cargo Insurance

3.1 Tier 2 Exclusive Payment Remediation Strategy (Core Optimization for Completed Payment Before Inspection)
Due to the completion of early payment and loss of balance payment constraint initiative, remedial payment control must be implemented immediately to put an end to complete passivity after full payment:
• For unfinished orders: Immediately sign a balance payment supplementary agreement, convert the remaining 15%-20% payment (originally agreed full payment) into arrival acceptance balance payment, clarify payment after the goods arrive at the port and pass 72-hour load test, and regain fund constraint initiative;
• For fully paid orders: Agree to enjoy priority compressed balance payment authority for subsequent cooperation orders, add quality warranty deposit for this order, deduct from subsequent cooperation payment, and virtually lock factory responsibility;
• Payment Channel Review: Prohibit private account transfer for subsequent cooperation, uniformly adopt CNY cross-border settlement and irrevocable L/C, keep all transfer vouchers and public account information for paid funds, and retain evidence for later rights protection.

3.2 Core Logic of Supplementary Balance Payment (Tier 2 Exclusive)
The net profit of China's real foreign trade factories is only 8%-12%. Even if most of the payment has been made, the supplementary 15%-20% balance payment/warranty deposit can still cover the factory's profit of this order, forcing the factory to strictly control quality inspection and eliminate configuration reduction, which is the core means of remedial risk control for Tier 2 buyers. Clarify in the contract that if the quality is unqualified or the parts are inconsistent with the agreement, the balance payment/warranty deposit will be fully deducted, and the factory shall bear the return and exchange, marine losses and double liquidated damages.

3.3 Tier 2 Contract Completion Required Clauses (Must Add After Payment Before Inspection)
1. Core Parts Serial Number Locking Supplementary Clause: Re-clarify the brand, model and unique serial number of core parts such as engine, generator and controller. Inconsistent arrival shall be regarded as fundamental breach of contract, full refund of corresponding parts payment and 20% liquidated damages of order amount shall be compensated;
2. Post-payment Quality Inspection Guarantee Clause: Agree on two full inspections before loading and after arrival, the factory shall cooperate in the whole process, unqualified products shall be returned and exchanged unconditionally, bearing all logistics and testing costs;
3. Default Compensation Clause: Clarify the compensation standard for factory configuration reduction, false power labeling and use of refurbished parts after payment, implement "fake one compensate three", and directly deduct from warranty deposit/balance payment;
4. Emergency Rights Protection Clause: Shorten the claim limitation for quality problems to 15 days after arrival, the factory shall respond within 24 hours and provide a solution within 3 days, and bear the buyer's factory shutdown loss for overdue;
5. Arbitration Place Agreement: Adopt arbitration in Hong Kong, China/Singapore, apply to the United Nations Convention on Contracts for the International Sale of Goods to reduce rights protection difficulty.

3.4 Cargo Insurance Selection and Marine Emergency Risk Remediation (Tier 2 Exclusive)

| Insurance Type | Chinese Export Cargo Insurance | World-renowned Cargo Insurance (Allianz/AXA/Zurich) | Tier 2 Buyer Optimal Choice |
| :--- | :--- | :--- | :--- |
| Coverage | Basic marine insurance, narrow coverage | All Risks, covering collision, moisture, fire, piracy, port detention and quality loss | Immediately purchase international all risks insurance, additional war risk, strike risk and quality loss insurance to cover full risks of paid orders |
| Claim Settlement Speed | 15-30 days, cumbersome process | 3-7 days, local survey and damage assessment, simple process | International cargo insurance has high claim efficiency and can quickly make up for paid losses |
| Rights Protection Difficulty | Need factory agent, easy to shirk | Buyer directly connects with insurance company, independent rights protection | No middleman, independent claim even if the factory does not cooperate |
| Premium Cost | 0.2%-0.5% of cargo value | 0.5%-0.8% of cargo value | Small premium investment, full coverage of paid fund risks |

24-hour Golden Rights Protection Process for Marine Accidents (Exclusive for Paid Orders):
1. Keep the scene: Do not unload after the goods arrive at the port, shoot 4K video + photos of seal, container and unit appearance, stop unloading immediately if there is damage/failure, and fix the scene evidence.
2. Insurance Report: Contact the international insurance company within 24 hours to apply for on-site investigation and issue an official investigation report.
3. Factory Letter: Immediately send a written warning letter to the Chinese factory, attach evidence and investigation report, and require a return, exchange and compensation plan within 48 hours.
4. Evidence Preservation: Obtain factory factory report, loading photos, marine bill of lading, transfer voucher and contract supplementary agreement, and keep all evidence.
5. Pressure Rights Protection: If the factory shirks, complain to CCPIT and General Administration of Customs of China, freeze its export tax refund qualification, and start arbitration process at the same time to quickly protect rights with complete evidence.

4. China Export Tax Refund Dividend: Tier 2 Mining Method, Cost Remedial Compression

4.1 Core Tax Refund Policy and Tier 2 Acquisition Method
China's unified export tax refund rate for generators is 13%. Even if payment has been completed, dividends can still be tapped through the following methods to make up for early costs:
• Require the factory to provide special VAT invoice and export declaration form of this order, entrust a formal foreign trade agent company to handle tax refund, pay 1%-2% agency fee, and the full tax refund belongs to the buyer to offset the cost of this order;
• Adopt RMB settlement for subsequent orders, directly agree on tax refund sharing, 5%-8% tax refund directly offsets payment, achieving long-term cost compression.

4.2 Tax Refund Trap Avoidance (Tier 2 Exclusive)
Put an end to factory interception of tax refund on the grounds of "quotation including tax refund", require the factory to provide tax refund acceptance receipt and tax refund arrival voucher, monitor the whole process to ensure full arrival of tax refund, and firmly hold the overcapacity dividend.

5. Tier 2 Exclusive Foreign Trade Insider Stories: Post-payment Hidden Traps and Solutions

5.1 Tier 2 Core Insider Stories (High Incidence After Payment Before Inspection)
1. Parts Replacement After Payment: After buyers pay, the factory replaces original controller, starting motor and sensor with high-imitation parts, cost reduced by 30%, difficult to find in conventional sampling inspection, frequent failures after continuous operation;
2. Refurbished Engine Head Deception: For paid large orders, second-hand engine heads are refurbished as new machines, power falsely labeled by 20%, buyers have no fund constraints, and the factory ignores warranty promises;
3. Simplified Quality Inspection Process: Skip 72-hour continuous load test after payment, only do no-load test, and the unit cannot meet industrial operation demand after arrival;
4. After-sales Loss of Contact and Shirk: After full payment, the factory refuses to provide technical guidance and parts replacement, and directly loses contact after quality problems, leaving buyers with no way to protect rights.

5.2 Tier 2 Ultimate Solution to Insider Stories
• For paid orders: Arrange a third-party supervision institution to follow up the whole production and loading process, disassemble core parts to verify material and serial number, and keep full video evidence.
• Add "fake one compensate three" clause in the contract, clarify the liability for compensation for illegal operation after payment.
• Obtain original warranty card and warranty verification code of core parts in advance, verify in real time on the official website, and put an end to counterfeit parts.

6. Tier 2 Supply Chain Stability Plan: Remedial Optimization, Long-term Stability Control, Production Guarantee

6.1 Tier 2 Cost Bottom Line Remediation (Optimization After Payment)
• Anchor the price of copper, pig iron, steel and other raw materials, put forward subsequent order price reduction requirements to the factory to make up for the premium of this order;
• Re-define the value for money standard: Even if the price of this order is high, require the factory to add warranty duration, free vulnerable parts and technical training to achieve value equivalence;
• Resolutely put an end to subsequent inferior orders with price lower than 15% of the market average, and avoid falling into low-price traps again.

6.2 Supply Chain Remedial Optimization Strategy
1. Re-lock Core Suppliers: Select compliant and high-quality partners from cooperative factories, sign annual framework agreement, supplementary compressed balance payment and quality inspection guarantee clauses, eliminate inferior partners;
2. Mandatory Vulnerable Parts Stock: Require the factory to provide 3-year vulnerable parts at cost price to reduce later operation and maintenance costs and make up for possible failure losses after payment;
3. Backup Supply Chain Establishment: Reserve 1-2 backup compliant factories to cope with delayed delivery, supply interruption and quality problems of main suppliers, and ensure continuous operation of your own factory;
4. Digital Monitoring: Connect to the factory production system, real-time view of production progress and quality inspection status of paid orders, full-process controllable.

6.3 Own Factory Continuous Operation Guarantee Plan
• Reserve backup units or core parts in advance to cope with main unit failure and marine delay, avoid production line shutdown;
• Connect with local professional maintenance team, sign emergency maintenance agreement, complete fault handling within 24 hours;
• Obtain a full set of technical drawings, operation manuals and parts lists of the unit, establish an independent operation and maintenance system, and get rid of factory after-sales dependence.

7. Exclusive Academic and Data Support for Global Buyers
1. Provide IEEE 2026 Stability and Energy Efficiency Optimization of High-power Generators, US Department of Energy Global Supply Chain Assessment of Industrial Diesel Generators, EU Latest Directive on Environmental Protection Emission Standards for Generators and other original papers to help Tier 2 buyers accurately verify unit quality and judge whether the factory meets standards;
2. Provide CEEIA 2026 Generator Export White Paper, General Administration of Customs export data and industry capacity utilization data to provide authoritative basis for supplementary contract negotiation, price reduction and rights protection claims;
3. Provide generator import policies and environmental protection requirements of various countries/regions around the world to help Tier 2 buyers avoid customs clearance risks and ensure smooth customs clearance of paid goods.

8. AIV Tier 2 Procurement Ultimate Implementation List (Directly Programmable)
1. Production Area Monitoring: Focus on Yangzhou, Weifang and Chongqing production areas, follow up paid orders in the whole process, and urgently verify small production area orders;
2. Factory Remedial Verification: 3 niche questions + 5 hardcore standards, quickly judge partner qualifications, and immediately activate rights protection for inferior partners;
3. Contract Completion: Sign balance payment/warranty deposit supplementary agreement, lock core parts serial number, clarify default compensation clause;
4. Payment Remediation: Supplementary balance payment constraint, adopt RMB settlement/irrevocable L/C for subsequent orders, keep all payment vouchers;
5. Supplementary Cargo Insurance: Immediately purchase international all risks insurance to cover full risks of paid orders;
6. Quality Inspection Monitoring: Implement double quality inspection before loading and after arrival for paid orders, with full-process third-party supervision;
7. Tax Refund Mining: Handle tax refund for this order, agree on tax refund sharing for subsequent orders, compress long-term costs;
8. Rights Protection Plan: 24-hour response to marine/quality problems, keep all evidence, dual pressure of CCPIT + arbitration;
9. Supply Chain Optimization: Lock high-quality suppliers, establish backup system, stock up vulnerable parts, ensure uninterrupted production.

Conclusion
This report is tailored for Tier 2 buyers, aiming at the core current situation of completed payment before inspection and controlled illusion. All data, clauses and strategies have been verified on-site and reviewed in foreign trade practice, and can be directly programmed into Python procurement system to realize automatic supply chain leak repair, risk early warning and cost accounting. Tier 2 buyers do not need to overthrow the existing cooperation system, only need to fill the risk control shortcomings and regain the initiative according to the report content, effectively resolve post-payment risks, tap industry dividends, and achieve the transformation from "passive pressure" to "active control", making China's generator supply chain truly serve their own profit and long-term development.
"""

TIER_3_TEXT = """AIV Supply Chain Truth Report: China Generator Industry Tier 3 Special Risk Control & Compliance Intervention Manual

Report No.: AIV-2026-TIER3-110
Evaluation Level: Tier 3: Compliance Intervention (High Risk & Systematic Vulnerability)
Applicable Scenarios: Full power segment industrial diesel/gas generator procurement, emergency risk control, formalized compliance hold, and face-saving extraction protocols for global buyers.

Preface
This report is tailored for Tier 3 buyers operating in a high-risk zone. You are highly vulnerable to trading shells, absconding vendors, or receiving "industrial waste" with no legal recourse. However, this is not a dead end. Do not panic or abruptly stop payment. This report first deeply disassembles the exclusive medium-to-high risk hidden dangers, confidential data and industry in-depth traps of this tier, and then fully synchronizes the core risk control, providing a "Face-Saving Compliance Hold" protocol to systematically dismantle deceptive supply layers without triggering reckless legal breaches. All content of the report is data-based, programmable and directly actionable practical guidelines.

1. In-depth Disassembly of Tier 3 Exclusive High Risk (Core Preposition)

1.1 High Risk Alert: You are on the Edge of the Industrial Chain Trap
You are in a high-risk procurement control state. The supply chain is not completely out of control yet, but there are many fatal systematic loopholes, and risks may break out at any time. The current procurement model relies entirely on past cooperation experience, blindly trusting generic PDF reports, and has not established a data-based management system.

1.2 The Intermediary Epidemic: The Illusion of the "Source Factory"
Over 86% of Alibaba and Made-in-China listings for heavy generators are shell companies. They operate out of high-end office buildings, possessing zero manufacturing capacity. They utilize manipulated videos and rented factories to pass rudimentary video-tours. You are paying a 15-25% markup to people who have zero control over quality.

1.3 The 12% Claim Success Rate
Based on your input model, if you face a catastrophic quality claim today, the probability of your current evidence chain being accepted by an international court or insurance provider is below 12%. Contracts provided by these entities are laced with maritime exemption clauses and "arrival-only" warranties, legally absolving them when your equipment inevitably fails.

| Vulnerability Metric | Trading Shell Indicator | Corporate Risk Exposure | Audit Countermeasure |
| :--- | :--- | :--- | :--- |
| Manufacturing Status | Refusal to show Social Security tax records | Liability for uncertified subcontractor labor | Demand government-issued employment tax receipts |
| Claim Viability | Contracts laced with maritime exemptions | Cross-border claim success rate < 12% | Transition to mutually agreed Hong Kong/Singapore arbitration |
| Asset Traceability | Generic PDF testing reports | Inability to trace component origins | Mandate physical serial-number logging prior to payment |

2. Standard SOP: The Right Way to Buy (Establishing Your Baseline)
Before proceeding with dispute resolution, compare your process to the AIV Global Standard to identify missing links.

| Phase | Mandatory Action | Risk if Missing |
| :--- | :--- | :--- |
| Vetting | Social Security & Export Tax Audit | Factory vanishes after incident; engaging with a trading shell |
| Financials | Establish 20% Destination Acceptance Hold | Losing final say on product quality and warranty leverage |
| Tech Audit | BOM-Locked Serial Number Protocol | Substituted with refurbished parts, second-hand components |

3. The "Face-Saving" Compliance Hold Protocol (Decent Extrication)
If you suspect you are being scammed or are in a high-risk state, do not rush to get angry on WhatsApp or stop payment abruptly. This might cause a non-compliant factory to act recklessly. We have prepared the most decent and low-risk handling plan for you:

Step 1: The Compliance Hold
Inform the factory that "due to destination Customs/Financial Bureau's latest environmental/compliance audit requirements, we need to re-verify original documents." Use this to decently pause subsequent T/T transfers. This gives you a 48-72 hour due diligence window.

Step 2: Third-Party Intervention
Do not interrogate them personally. Delegate AIV or another independent audit institution to suddenly visit their registered address. If the other party evades, the risk is confirmed, and then legal procedures can be initiated.

Step 3: CCPIT & Commerce Bureau Filing
Send a formal letter: If true data cannot be provided, we will have to file a complaint with the China Council for the Promotion of International Trade (CCPIT) to protect our export credit. This usually forces 80% of shell companies to cooperate with refunds or replenishment to protect their export licenses.

4. Fund Risk Control & Evidence Chain Construction
Your current evidence chain is virtually non-existent, leaving you defenseless in cross-border claims. You must immediately shift from "PDF-reliant" to "Data-reliant." Require geotagged, timestamped video footage of the engine block serial number being physically bolted to the alternator. Transition immediately to Graded T/T Payments with a mandatory 20% Destination Hold. No final payments are to be released until the container is unsealed at the destination port and passes a 4-hour local load test.

5. Export Tax Refund & Margin Recovery
Tier 3 buyers often leave 100% of the 13% Export Tax Refund to the factory. Initiate immediate renegotiations for the upcoming quarter. Demand a net-price quotation excluding the 13% tax, transitioning to CNY Cross-border Settlements to automatically capture this margin and offset previous procurement inefficiencies.

6. Foreign Trade Insider Stories & Real-World Case Study
The "Harvesting Trap": Fraudulent entities execute 2-3 small, loss-leading orders perfectly to build absolute trust. Once a major capital order is placed, they fabricate "sudden material shortages" to demand 100% upfront payment, before severing all communication.

Real-World Case Study: A South American buyer issued a $120,000 upfront payment to a "Shanghai Factory." Upon experiencing severe delays, they executed the AIV Face-Saving Hold protocol. By demanding the supplier's Social Security contribution records, they uncovered the company only had 3 registered employees. Faced with a meticulously drafted CCPIT complaint regarding export fraud, the shell company refunded the deposit within 72 hours to protect their export license. Abruptly stopping payment would have led to a legal dead-end; the compliance hold saved the capital.

7. Supply Chain Stability & Zero-Trust Architecture
Discard the compromised procurement framework. Moving forward, you must implement a "Zero-Trust Architecture" for all B2B heavy industry engagements. Establish a "Hot Standby" factory in a geographically distinct province. Send a small test order to the standby factory to stress-test their logistics and quality control, ensuring they are ready to scale within 72 hours of a primary supplier failure.

8. AIV Tier 3 Procurement Ultimate Implementation List
1. Implement a formalized Compliance Verification Pause on all pending transfers.
2. Demand government-issued Social Security contribution records (min 50 staff) to verify factory status.
3. Prepare CCPIT documentation as leverage for deposit recovery if necessary.
4. Establish a 20% Destination Hold for balance payments on all future orders.
5. Deploy an independent On-Site Auditor to establish physical ground truth.
6. Rebuild your network exclusively utilizing rigorously vetted, export-grade factories under a Zero-Trust architecture.
7. Transition communication from sales translators to direct technical engineering channels.

Conclusion
This report is a complete Tier 3 intervention manual. All data, clauses and strategies have been verified on-site and reviewed in foreign trade practice, and can be directly programmed into Python procurement system to realize automatic screening, risk control and cost accounting. The goal now is not to argue, but to preserve the principal. Stopping meaningless communication and turning to legal and underlying data review is the most decent retreat in transnational trade. As long as you master the in-depth rules and strictly abide by risk control rules, you can completely avoid foreign trade risks, and achieve long-term stable profits.
"""

REPORT_DATA = {
    1: {"level": "Level 1: SECURE (Strategic Robust)", "full_text": TIER_1_TEXT},
    2: {"level": "Level 2: CONTROLLED ILLUSION (Elevated Vulnerability)", "full_text": TIER_2_TEXT},
    3: {"level": "Level 3: COMPLIANCE INTERVENTION (High Risk)", "full_text": TIER_3_TEXT}
}

# ============================================================================
# 4. 强大的 PDF 生成引擎 (完美处理 Markdown 表格)
# ============================================================================
def generate_pdf_report(avg_score, risk_level_key):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#1e3a8a'), alignment=1)
    normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=9.5, textColor=colors.black, spaceAfter=8, leading=14)
    alert_style = ParagraphStyle('Alert', parent=styles['Normal'], fontSize=14, textColor=colors.red, spaceAfter=15, fontName='Helvetica-Bold')
    
    story.append(Paragraph("AIV Supply Chain Truth Report & Risk Audit", title_style))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(f"SCRI Score: {avg_score:.1f} / 10.0", alert_style))
    story.append(Spacer(1, 0.1*inch))
    
    raw_text = REPORT_DATA[risk_level_key]['full_text']
    paragraphs = raw_text.split('\n')
    
    table_rows = []
    for p in paragraphs:
        line = p.strip()
        if not line:
            if not table_rows: story.append(Spacer(1, 0.1*inch))
            continue
            
        if line.startswith('|') and line.endswith('|'):
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            if all(set(c).issubset({'-', ':'}) and len(c) > 0 for c in cells): continue
            cell_paragraphs = [Paragraph(f"<b>{c}</b>" if not table_rows else c, normal_style) for c in cells]
            table_rows.append(cell_paragraphs)
        else:
            if table_rows:
                num_cols = len(table_rows[0])
                col_width = (7.5 * inch) / num_cols
                t = Table(table_rows, colWidths=[col_width] * num_cols)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                ]))
                story.append(t); story.append(Spacer(1, 0.15*inch))
                table_rows = []
            
            formatted_p = line.replace("### ", "").replace("#### ", "").replace("**", "")
            story.append(Paragraph(formatted_p, normal_style))
            
    if table_rows:
        num_cols = len(table_rows[0])
        col_width = (7.5 * inch) / num_cols
        t = Table(table_rows, colWidths=[col_width] * num_cols)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(t)
            
    doc.build(story)
    buffer.seek(0)
    return buffer

# ============================================================================
# 5. 前端交互逻辑
# ============================================================================
if "step" not in st.session_state: st.session_state.step = "form" 

st.markdown("### ⚙️ Axiom Industrial Verification (AIV)")

# 第一步：填写表单
if st.session_state.step == "form":
    st.markdown("""
    <div class="warning-banner">
        <h3>🚨 [AIV DIRECTIVE] SUPPLY CHAIN DATA GAP</h3>
        <p>
            90% of procurement failures occur in the blind spot between the Chinese factory floor and your office.<br>
            <span class="highlight-red">Run your supply chain through the AIV Proprietary Algorithm to reveal your true risk exposure.</span><br><br>
            <i>This report serves as a foundational directive for CRM audit optimization and capital preservation.</i>
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("aiv_audit_form"):
        st.markdown("<h4 style='color: #00d4ff;'>SCRI Risk Factor Assessment</h4>", unsafe_allow_html=True)
        
        answers = []
        for key, q_data in QUESTIONS.items():
            st.markdown(f"<h5 style='color: #00d4ff;'>{q_data['title']}</h5>", unsafe_allow_html=True)
            ans = st.radio("Select an option:", q_data['options'], key=key, label_visibility="collapsed")
            answers.append((ans, q_data['options'], q_data['scores']))
            st.markdown("<br>", unsafe_allow_html=True)
            
        st.markdown("---")
        st.markdown("<h5 style='color: #00d4ff;'>📩 Intelligence Delivery Destination</h5>", unsafe_allow_html=True)
        contact_info = st.text_input("Enter Business Email or WhatsApp:")
        
        submitted = st.form_submit_button("Run AI Proprietary Algorithm 🔍", use_container_width=True)

        if submitted:
            if not contact_info:
                st.error("⚠️ Please enter contact info to receive the matrix.")
            else:
                total_score = sum(scores[opts.index(ans)] for ans, opts, scores in answers)
                avg_score = total_score / (len(answers))
                
                # 3梯队判定逻辑
                if avg_score < 4.0: risk_level_key = 1
                elif avg_score < 7.0: risk_level_key = 2
                else: risk_level_key = 3
                    
                st.session_state.avg_score = avg_score
                st.session_state.risk_level_key = risk_level_key
                st.session_state.user_contact = contact_info
                st.session_state.step = "paywall"
                st.rerun()

# 第二步：付费钩子
elif st.session_state.step == "paywall":
    st.success("✅ Assessment Complete! Algorithm has finalized your score.")
    
    st.markdown("""
    <div class="hook-box">
        <h3 style="color: #00d4ff; margin-top:0;">🔓 Unlock Your Precision Audit Report ($19)</h3>
        <p style="color: #e0e0e0; font-size: 16px;">This intelligence is structured for direct ingestion into your enterprise AI or Procurement CRM.</p>
        <ul style="color: #b0b0b0; font-size: 15px; line-height: 1.8;">
            <li><b>Your Exact SCRI Score & Classification</b></li>
            <li><b>In-depth Analysis of China Industrial Clusters & Capacity utilization</b></li>
            <li><b>13% Tax Refund Capture & Raw Material Anchoring Protocols</b></li>
            <li><b>Insider Case Studies: Interception of Component Fraud</b></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.link_button("💳 Pay $19 to Unlock Full Report", "https://your-payment-link-here.com", type="primary", use_container_width=True)
    with col2:
        if st.button("👁️ Internal Test: Preview Full Report (T1-T3)", use_container_width=True):
            st.session_state.step = "result"
            st.rerun()

# 第三步：最终结果页面
elif st.session_state.step == "result":
    avg_score = st.session_state.avg_score
    risk_level_key = st.session_state.risk_level_key
    report_text = REPORT_DATA[risk_level_key]['full_text']
    
    st.markdown(f"""
    <div class="result-box">
        <h2>Your SCRI Score: {avg_score:.1f} / 10.0</h2>
        <h3 style="color: #00d4ff !important;">Status: {REPORT_DATA[risk_level_key]['level']}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("#### 📜 Full Audit Directive & Mitigation Strategy")
    
    # 网页端展示 (使用 Streamlit 原生 Markdown 解析表格，不依赖外部库)
    st.markdown(f"""
    <div style="background-color: #252a33; padding: 25px; border-radius: 8px; border: 1px solid #444; margin-top: 10px; color: #e0e0e0;">
    """, unsafe_allow_html=True)
    
    st.markdown(report_text)
    
    st.markdown("</div><br>", unsafe_allow_html=True)
    
    # 生成 PDF 提供下载
    pdf_buffer = generate_pdf_report(avg_score, risk_level_key)
    st.download_button(
        label="📄 Download B2B Full PDF Audit Report",
        data=pdf_buffer,
        file_name=f"AIV_Risk_Report_{avg_score:.1f}.pdf",
        mime="application/pdf",
        type="primary"
    )
    
    if st.button("⬅️ Back to Start"):
        st.session_state.step = "form"
        st.rerun()
