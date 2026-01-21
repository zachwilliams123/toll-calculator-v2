"""
Battery Toll Calculator v20
"""

import streamlit as st
import numpy as np
import numpy_financial as npf

st.set_page_config(page_title="Battery Toll Calculator | Modo Energy", layout="centered", initial_sidebar_state="collapsed")

CAPEX = 625
OPEX = 10
EURIBOR = 2.25
TOLL_TENOR = 7
PROJECT_LIFE = 10

REVENUE_DATA = {
    'low':  [94, 76, 72, 69, 68, 68, 70, 67, 67, 69],
    'base': [155, 129, 124, 119, 117, 118, 118, 117, 114, 115],
    'high': [205, 168, 163, 158, 154, 157, 155, 151, 154, 154],
}

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    html, body, [class*="css"], .stMarkdown, p, div, span, label {
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}
    div[data-testid="stToolbar"] {display: none;}
    .block-container {padding: 1rem 1.5rem !important; max-width: 900px !important;}
    
    .disclaimer {
        font-size: 11px; color: #64748b; text-align: center;
        padding: 8px 12px; background: #f8fafc; border-radius: 6px;
        margin-bottom: 12px; border: 1px solid #e2e8f0;
    }
    .disclaimer a {color: #3b82f6; text-decoration: none;}
    
    .header-row {
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 16px; padding-bottom: 12px; border-bottom: 2px solid #e2e8f0;
    }
    .main-title {font-size: 22px; font-weight: 700; color: #1a1a2e;}
    .brand-text {font-size: 13px; color: #1a1a2e; font-weight: 600;}
    
    .section-label {
        font-size: 11px; font-weight: 600; color: #64748b;
        margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.05em;
    }
    .input-label {font-size: 13px; color: #475569; margin-bottom: 6px;}
    
    .gearing-container {display: flex; align-items: center; gap: 10px; margin: 12px 0 8px 0;}
    .gearing-label {font-size: 12px; color: #64748b; min-width: 50px;}
    .gearing-bar-bg {
        flex: 1; background: #e2e8f0; border-radius: 5px; height: 24px;
        position: relative; overflow: hidden;
    }
    .gearing-bar-fill {
        background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%);
        height: 100%; border-radius: 5px; display: flex; align-items: center;
        justify-content: flex-end; padding-right: 10px; min-width: 50px;
    }
    .gearing-value {font-size: 12px; font-weight: 600; color: white;}
    
    .capital-row {
        display: flex; justify-content: flex-end; gap: 16px;
        font-size: 12px; color: #64748b; margin-bottom: 12px;
    }
    
    .terms-row {display: flex; gap: 12px; padding-top: 10px; border-top: 1px solid #f1f5f9;}
    .term-chip {font-size: 12px; color: #475569;}
    .term-chip strong {color: #1e293b;}
    
    .result-card {border-radius: 10px; padding: 14px 16px; color: white; margin-bottom: 8px;}
    .result-card.pass {background: linear-gradient(135deg, #10b981 0%, #059669 100%);}
    .result-card.warn {background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);}
    .result-card.fail {background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);}
    .result-header {display: flex; justify-content: space-between; align-items: flex-start;}
    .result-label {font-size: 10px; opacity: 0.9; text-transform: uppercase; letter-spacing: 0.03em; margin-bottom: 4px;}
    .result-value {font-size: 28px; font-weight: 700; line-height: 1.1;}
    .result-detail {font-size: 12px; opacity: 0.9; margin-top: 4px;}
    .result-badge {font-size: 9px; font-weight: 600; padding: 4px 10px; border-radius: 4px; background: rgba(255,255,255,0.2);}
    .result-footer {font-size: 12px; opacity: 0.85; margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.2);}
    
    .dscr-note {font-size: 10px; color: #64748b; margin-bottom: 12px;}
    
    .slider-header {display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;}
    .min-viable {font-size: 12px; color: #64748b;}
    .min-viable strong {color: #1e293b;}
    
    .footer {
        text-align: center; font-size: 10px; color: #94a3b8;
        margin-top: 12px; padding-top: 10px; border-top: 1px solid #f1f5f9;
    }
    
    div[data-testid="stNumberInput"] label {display: none !important;}
    div[data-testid="stNumberInput"] input {
        font-family: 'DM Sans', sans-serif !important; font-size: 14px !important;
        padding: 8px 12px !important; border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important; background: #f8fafc !important;
    }
    div[data-testid="stNumberInput"] > div {max-width: 120px;}
    div[data-testid="stSlider"] {padding-top: 0 !important; padding-bottom: 0 !important;}
    div[data-testid="stSlider"] label {display: none !important;}
</style>
""", unsafe_allow_html=True)

def get_dscr_target(toll_pct: float) -> float:
    return 2.00 - toll_pct * 0.008

def get_margin_bps(toll_pct: float) -> float:
    return 280 - toll_pct * 0.80

def calculate_project(toll_pct: float, toll_price: float, gearing: float) -> dict:
    dscr_target = get_dscr_target(toll_pct)
    margin_bps = get_margin_bps(toll_pct)
    all_in_rate = (EURIBOR + margin_bps / 100) / 100
    
    total_capex = CAPEX * 1000
    debt = total_capex * gearing / 100
    equity = total_capex - debt
    toll_fraction = toll_pct / 100
    
    def build_revenue(forecast):
        return [
            toll_price * toll_fraction + forecast[i] * (1 - toll_fraction) if i < TOLL_TENOR else forecast[i]
            for i in range(PROJECT_LIFE)
        ]
    
    annual_ds = 0
    if debt > 0 and all_in_rate > 0:
        r, n = all_in_rate, TOLL_TENOR
        annual_ds = debt * (r * (1 + r)**n) / ((1 + r)**n - 1)
    
    debt_service = [annual_ds if i < TOLL_TENOR else 0 for i in range(PROJECT_LIFE)]
    
    def calc_scenario(revenue):
        net_cf = [revenue[i] * 1000 - OPEX * 1000 for i in range(PROJECT_LIFE)]
        equity_cf = [net_cf[i] - debt_service[i] for i in range(PROJECT_LIFE)]
        dscr_vals = [net_cf[i] / debt_service[i] for i in range(TOLL_TENOR) if debt_service[i] > 0]
        min_dscr = min(dscr_vals) if dscr_vals else 99.0
        try:
            irr = npf.irr([-equity] + equity_cf) * 100
            if np.isnan(irr) or irr < -50 or irr > 200:
                irr = -99.0
        except:
            irr = -99.0
        return {'irr': irr, 'min_dscr': min_dscr}
    
    low = calc_scenario(build_revenue(REVENUE_DATA['low']))
    base = calc_scenario(build_revenue(REVENUE_DATA['base']))
    high = calc_scenario(build_revenue(REVENUE_DATA['high']))
    
    return {
        'gearing': gearing,
        'dscr_target': dscr_target,
        'all_in_rate': all_in_rate * 100,
        'debt': debt / 1000,
        'equity': equity / 1000,
        'debt_feasible': low['min_dscr'] >= dscr_target,
        'low': low, 'base': base, 'high': high,
    }

# Disclaimer
st.markdown('''
<div class="disclaimer">
    Model for educational purposes only. 
    <a href="mailto:zach.williams@modoenergy.com">zach.williams@modoenergy.com</a> for detailed project analysis.
</div>
''', unsafe_allow_html=True)

# Header
st.markdown('''
<div class="header-row">
    <div class="main-title">Battery Toll Calculator</div>
    <div class="brand-text">Modo Energy</div>
</div>
''', unsafe_allow_html=True)

# Layout
left_col, right_col = st.columns([1, 1.1], gap="large")

with left_col:
    st.markdown('<div class="section-label">Structure</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="input-label">Toll Price (€k/MW/yr)</div>', unsafe_allow_html=True)
    toll_price = st.number_input("Toll Price", min_value=80, max_value=140, value=120, step=5, label_visibility="collapsed")
    
    st.markdown('<div class="slider-header"><span class="input-label">Toll Coverage %</span></div>', unsafe_allow_html=True)
    toll_pct = st.slider("Toll Coverage", 0, 100, value=80, label_visibility="collapsed")
    
    st.markdown('<div class="slider-header"><span class="input-label">Gearing %</span></div>', unsafe_allow_html=True)
    gearing = st.slider("Gearing", 30, 85, value=70, label_visibility="collapsed")
    
    result = calculate_project(toll_pct, toll_price, gearing)
    
    bar_pct = (gearing - 30) / 55 * 100
    st.markdown(f'''
    <div class="gearing-container">
        <span class="gearing-label">Gearing</span>
        <div class="gearing-bar-bg">
            <div class="gearing-bar-fill" style="width: {bar_pct}%;">
                <span class="gearing-value">{gearing:.0f}%</span>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown(f'''
    <div class="capital-row">
        <span>€{result['debt']:.0f}k debt</span>
        <span>€{result['equity']:.0f}k equity</span>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown(f'''
    <div class="terms-row">
        <span class="term-chip"><strong>{result['dscr_target']:.2f}×</strong> DSCR</span>
        <span class="term-chip"><strong>{result['all_in_rate']:.1f}%</strong> rate</span>
        <span class="term-chip"><strong>7yr</strong> tenor</span>
    </div>
    ''', unsafe_allow_html=True)

with right_col:
    st.markdown('<div class="section-label">Returns</div>', unsafe_allow_html=True)
    
    hurdle = 10
    low_irr, base_irr, high_irr = result['low']['irr'], result['base']['irr'], result['high']['irr']
    min_dscr, dscr_target = result['low']['min_dscr'], result['dscr_target']
    
    # Debt card
    debt_class = "pass" if result['debt_feasible'] else "fail"
    debt_badge = "FEASIBLE" if result['debt_feasible'] else "NOT FEASIBLE"
    dscr_margin = min_dscr - dscr_target
    dscr_sign = "+" if dscr_margin >= 0 else ""
    
    st.markdown(f'''
    <div class="result-card {debt_class}">
        <div class="result-header">
            <div>
                <div class="result-label">Debt</div>
                <div class="result-value">{min_dscr:.2f}×</div>
                <div class="result-detail">vs {dscr_target:.2f}× target ({dscr_sign}{dscr_margin:.2f}×)</div>
            </div>
            <div class="result-badge">{debt_badge}</div>
        </div>
    </div>
    <div class="dscr-note">DSCR tested against Modo low case</div>
    ''', unsafe_allow_html=True)
    
    # Equity card - base case as main
    if low_irr >= hurdle:
        eq_class, eq_badge = "pass", "MEETS HURDLE"
    elif base_irr >= hurdle:
        eq_class, eq_badge = "warn", "BASE MEETS HURDLE"
    else:
        eq_class, eq_badge = "fail", "BELOW HURDLE"
    
    st.markdown(f'''
    <div class="result-card {eq_class}">
        <div class="result-header">
            <div>
                <div class="result-label">Equity IRR (10yr)</div>
                <div class="result-value">{base_irr:.1f}%</div>
                <div class="result-detail">vs {hurdle}% hurdle</div>
            </div>
            <div class="result-badge">{eq_badge}</div>
        </div>
        <div class="result-footer">Range: {low_irr:.0f}% – {high_irr:.0f}%</div>
    </div>
    ''', unsafe_allow_html=True)

# Methodology - using st.markdown inside expander to avoid text rendering issues
with st.expander("Methodology & Assumptions"):
    st.markdown("""
**Revenue**  
Years 1–7: (Toll price × Toll %) + (Modo merchant forecast × (1 − Toll %))  
Years 8–10: 100% merchant (toll expired, debt repaid)

**Debt**  
7-year amortising loan at EURIBOR + 200–280 bps. DSCR covenant tested against Modo low case: 2.0× at 0% toll → 1.2× at 100% toll.

**Equity**  
IRR calculated over 10 years (includes 3-year merchant tail post-toll). Range shows Modo low/high revenue scenarios. Hurdle rate: 10%.

**Glossary**  
- **IRR** — Internal Rate of Return. Annualised return on equity.
- **DSCR** — Debt Service Coverage Ratio. Operating cash flow ÷ debt payments.
- **Gearing** — Debt as % of total capital.

---
€625k/MW CapEx (inc. BKZ) · €10k/MW/yr OpEx · 2hr · 1.5 cycles/day · COD 2027
    """)

# Footer
st.markdown('''
<div class="footer">
    2hr · 1.5 cycle · 7yr toll/debt · 10yr equity IRR · COD 2027 · Modo forecasts
</div>
''', unsafe_allow_html=True)
