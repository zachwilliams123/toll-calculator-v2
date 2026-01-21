"""
Battery Toll Calculator v21
Auto gearing that follows toll, with manual override option
"""

import streamlit as st
import numpy as np
import numpy_financial as npf

st.set_page_config(page_title="Battery Toll Calculator | Modo Energy", layout="centered", initial_sidebar_state="collapsed")

CAPEX, OPEX, EURIBOR, TOLL_TENOR, PROJECT_LIFE = 625, 10, 2.25, 7, 10
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
    #MainMenu, footer, header, .stDeployButton, div[data-testid="stToolbar"] {visibility: hidden; display: none;}
    .block-container {padding: 1rem 1.5rem !important; max-width: 900px !important;}
    
    .disclaimer {font-size: 11px; color: #64748b; text-align: center; padding: 8px 12px; background: #f8fafc; border-radius: 6px; margin-bottom: 12px; border: 1px solid #e2e8f0;}
    .disclaimer a {color: #3b82f6; text-decoration: none;}
    
    .header-row {display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 2px solid #e2e8f0;}
    .main-title {font-size: 22px; font-weight: 700; color: #1a1a2e;}
    .brand-text {font-size: 13px; color: #1a1a2e; font-weight: 600;}
    
    .section-label {font-size: 11px; font-weight: 600; color: #64748b; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.05em;}
    .input-label {font-size: 13px; color: #475569; margin-bottom: 6px;}
    
    .gearing-header {display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;}
    .reset-link {font-size: 12px; color: #3b82f6; cursor: pointer; text-decoration: none;}
    .reset-link:hover {text-decoration: underline;}
    
    .capital-row {display: flex; justify-content: flex-end; gap: 16px; font-size: 12px; color: #64748b; margin: 8px 0 12px 0;}
    
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
    .footer {text-align: center; font-size: 10px; color: #94a3b8; margin-top: 12px; padding-top: 10px; border-top: 1px solid #f1f5f9;}
    
    div[data-testid="stNumberInput"] label {display: none !important;}
    div[data-testid="stNumberInput"] input {font-size: 14px !important; padding: 8px 12px !important; border: 1px solid #e2e8f0 !important; border-radius: 8px !important; background: #f8fafc !important;}
    div[data-testid="stNumberInput"] > div {max-width: 120px;}
    div[data-testid="stSlider"] {padding-top: 0 !important; padding-bottom: 0 !important;}
    div[data-testid="stSlider"] label {display: none !important;}
    
    div[data-testid="stExpander"] {border: 1px solid #e2e8f0 !important; border-radius: 8px !important; margin-top: 16px;}
    div[data-testid="stExpander"] details {border: none !important;}
    div[data-testid="stExpander"] summary p {font-size: 13px !important; font-weight: 500 !important; color: #475569 !important;}
</style>
""", unsafe_allow_html=True)

def get_auto_gearing(toll_pct): return 45 + toll_pct * 0.35
def get_dscr_target(toll_pct): return 2.00 - toll_pct * 0.008
def get_margin_bps(toll_pct): return 280 - toll_pct * 0.80

def calculate_project(toll_pct, toll_price, gearing):
    dscr_target, margin_bps = get_dscr_target(toll_pct), get_margin_bps(toll_pct)
    all_in_rate = (EURIBOR + margin_bps / 100) / 100
    debt, equity = CAPEX * 10 * gearing, CAPEX * 1000 - CAPEX * 10 * gearing
    toll_fraction = toll_pct / 100
    
    def build_revenue(f):
        return [toll_price * toll_fraction + f[i] * (1 - toll_fraction) if i < TOLL_TENOR else f[i] for i in range(PROJECT_LIFE)]
    
    r, n = all_in_rate, TOLL_TENOR
    annual_ds = debt * (r * (1+r)**n) / ((1+r)**n - 1) if debt > 0 else 0
    
    def calc(f):
        net = [build_revenue(f)[i] * 1000 - OPEX * 1000 for i in range(PROJECT_LIFE)]
        ecf = [net[i] - (annual_ds if i < TOLL_TENOR else 0) for i in range(PROJECT_LIFE)]
        dscr = min([net[i]/annual_ds for i in range(TOLL_TENOR)]) if annual_ds > 0 else 99
        try:
            irr = npf.irr([-equity] + ecf) * 100
            irr = irr if not np.isnan(irr) and -50 < irr < 200 else -99
        except: irr = -99
        return {'irr': irr, 'min_dscr': dscr}
    
    low, base, high = calc(REVENUE_DATA['low']), calc(REVENUE_DATA['base']), calc(REVENUE_DATA['high'])
    return {
        'dscr_target': dscr_target, 'all_in_rate': all_in_rate * 100,
        'debt': debt / 1000, 'equity': equity / 1000,
        'debt_feasible': low['min_dscr'] >= dscr_target,
        'low': low, 'base': base, 'high': high,
    }

# Session state for gearing override
if 'gearing_override' not in st.session_state:
    st.session_state.gearing_override = None

# Disclaimer & Header
st.markdown('<div class="disclaimer">Model for educational purposes only. <a href="mailto:zach.williams@modoenergy.com">zach.williams@modoenergy.com</a> for detailed project analysis.</div>', unsafe_allow_html=True)
st.markdown('<div class="header-row"><div class="main-title">Battery Toll Calculator</div><div class="brand-text">Modo Energy</div></div>', unsafe_allow_html=True)

left_col, right_col = st.columns([1, 1.1], gap="large")

with left_col:
    st.markdown('<div class="section-label">Structure</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="input-label">Toll Price (€k/MW/yr)</div>', unsafe_allow_html=True)
    toll_price = st.number_input("price", 80, 140, 120, 5, label_visibility="collapsed")
    
    st.markdown('<div class="input-label">Toll Coverage %</div>', unsafe_allow_html=True)
    toll_pct = st.slider("toll", 0, 100, 80, label_visibility="collapsed")
    
    auto_gearing = int(round(get_auto_gearing(toll_pct)))
    
    # Gearing header with optional reset
    if st.session_state.gearing_override is not None:
        gcol1, gcol2 = st.columns([3, 2])
        with gcol1:
            st.markdown('<div class="input-label">Gearing %</div>', unsafe_allow_html=True)
        with gcol2:
            if st.button(f"({auto_gearing}% typical)", key="reset_btn", type="tertiary"):
                st.session_state.gearing_override = None
                st.rerun()
    else:
        st.markdown('<div class="input-label">Gearing %</div>', unsafe_allow_html=True)
    
    # Determine current gearing value
    current_gearing = st.session_state.gearing_override if st.session_state.gearing_override is not None else auto_gearing
    
    # Gearing slider
    new_gearing = st.slider("gearing", 30, 85, current_gearing, label_visibility="collapsed", key="gearing_slider")
    
    # Check if user changed gearing
    if new_gearing != current_gearing:
        if new_gearing != auto_gearing:
            st.session_state.gearing_override = new_gearing
        else:
            st.session_state.gearing_override = None
        st.rerun()
    
    gearing = new_gearing
    result = calculate_project(toll_pct, toll_price, gearing)
    
    st.markdown(f'<div class="capital-row"><span>€{result["debt"]:.0f}k debt</span><span>€{result["equity"]:.0f}k equity</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="terms-row"><span class="term-chip"><strong>{result["dscr_target"]:.2f}×</strong> DSCR</span><span class="term-chip"><strong>{result["all_in_rate"]:.1f}%</strong> rate</span><span class="term-chip"><strong>7yr</strong> tenor</span></div>', unsafe_allow_html=True)

with right_col:
    st.markdown('<div class="section-label">Returns</div>', unsafe_allow_html=True)
    
    hurdle = 10
    low_irr, base_irr, high_irr = result['low']['irr'], result['base']['irr'], result['high']['irr']
    min_dscr, dscr_target = result['low']['min_dscr'], result['dscr_target']
    
    debt_class = "pass" if result['debt_feasible'] else "fail"
    debt_badge = "FEASIBLE" if result['debt_feasible'] else "NOT FEASIBLE"
    dscr_margin = min_dscr - dscr_target
    
    st.markdown(f'''
    <div class="result-card {debt_class}">
        <div class="result-header">
            <div>
                <div class="result-label">Debt</div>
                <div class="result-value">{min_dscr:.2f}×</div>
                <div class="result-detail">vs {dscr_target:.2f}× target ({"+" if dscr_margin >= 0 else ""}{dscr_margin:.2f}×)</div>
            </div>
            <div class="result-badge">{debt_badge}</div>
        </div>
    </div>
    <div class="dscr-note">DSCR tested against Modo low case</div>
    ''', unsafe_allow_html=True)
    
    eq_class = "pass" if low_irr >= hurdle else "warn" if base_irr >= hurdle else "fail"
    eq_badge = "MEETS HURDLE" if low_irr >= hurdle else "BASE MEETS HURDLE" if base_irr >= hurdle else "BELOW HURDLE"
    
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
**IRR** — Internal Rate of Return. Annualised return on equity.  
**DSCR** — Debt Service Coverage Ratio. Operating cash flow ÷ debt payments.  
**Gearing** — Debt as % of total capital.

---
€625k/MW CapEx (inc. BKZ) · €10k/MW/yr OpEx · 2hr · 1.5 cycles/day · COD 2027
    """)

st.markdown('<div class="footer">2hr · 1.5 cycle · 7yr toll/debt · 10yr equity IRR · COD 2027 · Modo forecasts</div>', unsafe_allow_html=True)
