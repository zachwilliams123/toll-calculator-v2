"""
Battery Toll Calculator v19
Modo Energy - German BESS

v17 LOGIC + v18 UI (Streamlit version)
- Fixed 7yr tenor
- Gearing: 45% → 80% continuous
- DSCR: 2.00× → 1.20× continuous
- Margin: 280 → 200 bps continuous
"""

import streamlit as st
import numpy as np
import numpy_financial as npf

st.set_page_config(
    page_title="Battery Toll Calculator | Modo Energy", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# CONSTANTS
# ============================================================================
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

# ============================================================================
# CSS - Matching React aesthetic
# ============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    
    /* Global font */
    html, body, [class*="css"], .stMarkdown, p, div, span, label, .stSlider label {
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Hide Streamlit chrome */
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}
    div[data-testid="stToolbar"] {display: none;}
    div[data-testid="stDecoration"] {display: none;}
    
    /* Container */
    .block-container {
        padding: 1rem 1.5rem 1rem 1.5rem !important;
        max-width: 900px !important;
    }
    
    /* Disclaimer */
    .disclaimer {
        font-size: 11px;
        color: #64748b;
        text-align: center;
        padding: 8px 12px;
        background: #f8fafc;
        border-radius: 6px;
        margin-bottom: 12px;
        border: 1px solid #e2e8f0;
    }
    .disclaimer a {
        color: #3b82f6;
        text-decoration: none;
    }
    .disclaimer a:hover {
        text-decoration: underline;
    }
    
    /* Header */
    .header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 2px solid #e2e8f0;
    }
    .main-title {
        font-size: 22px;
        font-weight: 700;
        color: #1a1a2e;
        margin: 0;
    }
    .brand-text {
        font-size: 13px;
        color: #1a1a2e;
        font-weight: 600;
    }
    
    /* Section labels */
    .section-label {
        font-size: 11px;
        font-weight: 600;
        color: #64748b;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Input labels */
    .input-label {
        font-size: 13px;
        color: #475569;
        margin-bottom: 6px;
    }
    
    /* Gearing bar */
    .gearing-container {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 16px 0 8px 0;
    }
    .gearing-label {
        font-size: 12px;
        color: #64748b;
        min-width: 50px;
    }
    .gearing-bar-bg {
        flex: 1;
        background: #e2e8f0;
        border-radius: 5px;
        height: 24px;
        position: relative;
        overflow: hidden;
    }
    .gearing-bar-fill {
        background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%);
        height: 100%;
        border-radius: 5px;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding-right: 10px;
        min-width: 50px;
        transition: width 0.2s ease;
    }
    .gearing-value {
        font-size: 12px;
        font-weight: 600;
        color: white;
    }
    
    /* Capital row */
    .capital-row {
        display: flex;
        justify-content: flex-end;
        gap: 16px;
        font-size: 12px;
        color: #64748b;
        margin-bottom: 12px;
    }
    
    /* Terms row */
    .terms-row {
        display: flex;
        gap: 12px;
        padding-top: 10px;
        border-top: 1px solid #f1f5f9;
    }
    .term-chip {
        font-size: 12px;
        color: #475569;
    }
    .term-chip strong {
        color: #1e293b;
    }
    
    /* Result cards */
    .result-card {
        border-radius: 10px;
        padding: 14px 16px;
        color: white;
        margin-bottom: 8px;
    }
    .result-card.pass {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    }
    .result-card.warn {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    }
    .result-card.fail {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    }
    .result-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
    }
    .result-label {
        font-size: 10px;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        margin-bottom: 4px;
    }
    .result-value {
        font-size: 28px;
        font-weight: 700;
        line-height: 1.1;
    }
    .result-detail {
        font-size: 12px;
        opacity: 0.9;
        margin-top: 4px;
    }
    .result-badge {
        font-size: 9px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 4px;
        background: rgba(255,255,255,0.2);
    }
    .result-footer {
        font-size: 12px;
        opacity: 0.85;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid rgba(255,255,255,0.2);
    }
    
    /* DSCR note */
    .dscr-note {
        font-size: 10px;
        color: #64748b;
        margin-bottom: 12px;
    }
    
    /* Spread indicator */
    .spread-indicator {
        font-size: 11px;
        color: #64748b;
        padding: 8px 12px;
        background: #f8fafc;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
    }
    .spread-indicator strong {
        color: #1e293b;
    }
    
    /* Min viable label */
    .min-viable {
        font-size: 12px;
        color: #64748b;
    }
    .min-viable strong {
        color: #1e293b;
    }
    .min-viable .not-viable {
        color: #ef4444;
    }
    
    /* Slider row */
    .slider-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        font-size: 10px;
        color: #94a3b8;
        margin-top: 12px;
        padding-top: 10px;
        border-top: 1px solid #f1f5f9;
    }
    
    /* Streamlit input overrides */
    div[data-testid="stNumberInput"] label {display: none !important;}
    div[data-testid="stNumberInput"] input {
        font-family: 'DM Sans', sans-serif !important;
        font-size: 14px !important;
        padding: 8px 12px !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        background: #f8fafc !important;
    }
    div[data-testid="stNumberInput"] > div {
        max-width: 120px;
    }
    div[data-testid="stNumberInput"] button {
        background: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
    }
    
    /* Slider overrides */
    div[data-testid="stSlider"] {padding-top: 0 !important; padding-bottom: 0 !important;}
    div[data-testid="stSlider"] label {display: none !important;}
    div[data-testid="stSlider"] > div > div > div {
        background: #e2e8f0 !important;
    }
    div[data-testid="stSlider"] > div > div > div > div {
        background: #3b82f6 !important;
    }
    
    /* Expander */
    div[data-testid="stExpander"] {
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        background: white !important;
    }
    div[data-testid="stExpander"] summary {
        font-size: 13px !important;
        font-weight: 500 !important;
        color: #475569 !important;
    }
    div[data-testid="stExpander"] > div > div {
        border-top: 1px solid #f1f5f9;
    }
    
    /* Method content */
    .method-title {
        font-size: 12px;
        font-weight: 600;
        color: #1e293b;
        margin-top: 12px;
        margin-bottom: 4px;
    }
    .method-section {
        font-size: 11px;
        color: #475569;
        line-height: 1.6;
    }
    .method-section strong {
        color: #1e293b;
    }
    .fixed-assumptions {
        font-size: 10px;
        color: #94a3b8;
        margin-top: 12px;
        padding-top: 8px;
        border-top: 1px solid #f1f5f9;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# FORMULAS (v17 logic)
# ============================================================================
def get_gearing(toll_pct: float) -> float:
    return 45 + toll_pct * 0.35

def get_dscr_target(toll_pct: float) -> float:
    return 2.00 - toll_pct * 0.008

def get_margin_bps(toll_pct: float) -> float:
    return 280 - toll_pct * 0.80

def calculate_project(toll_pct: float, toll_price: float) -> dict:
    gearing = get_gearing(toll_pct)
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
    
    if debt > 0 and all_in_rate > 0:
        r = all_in_rate
        n = TOLL_TENOR
        annual_ds = debt * (r * (1 + r)**n) / ((1 + r)**n - 1)
    else:
        annual_ds = 0
    
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
        'margin_bps': margin_bps,
        'all_in_rate': all_in_rate * 100,
        'debt': debt / 1000,
        'equity': equity / 1000,
        'debt_feasible': low['min_dscr'] >= dscr_target,
        'low': low,
        'base': base,
        'high': high,
        'irr_spread': high['irr'] - low['irr'],
    }

def find_min_viable(toll_price: float) -> int | None:
    for t in range(0, 101):
        if calculate_project(t, toll_price)['debt_feasible']:
            return t
    return None

# ============================================================================
# DISCLAIMER
# ============================================================================
st.markdown('''
<div class="disclaimer">
    Model for educational purposes only. 
    <a href="mailto:zach.williams@modoenergy.com">zach.williams@modoenergy.com</a> for detailed project analysis.
</div>
''', unsafe_allow_html=True)

# ============================================================================
# HEADER
# ============================================================================
st.markdown('''
<div class="header-row">
    <div class="main-title">Battery Toll Calculator</div>
    <div class="brand-text">Modo Energy</div>
</div>
''', unsafe_allow_html=True)

# ============================================================================
# LAYOUT
# ============================================================================
left_col, right_col = st.columns([1, 1.1], gap="large")

with left_col:
    st.markdown('<div class="section-label">Structure</div>', unsafe_allow_html=True)
    
    # Toll price input
    st.markdown('<div class="input-label">Toll Price (€k/MW/yr)</div>', unsafe_allow_html=True)
    toll_price = st.number_input(
        "Toll Price",
        min_value=80,
        max_value=140,
        value=120,
        step=5,
        label_visibility="collapsed"
    )
    
    # Min viable calculation
    min_viable = find_min_viable(toll_price)
    if min_viable is not None:
        min_text = f'Min viable: <strong>{min_viable}%</strong>'
    else:
        min_text = '<span class="not-viable">Not viable</span>'
    
    # Slider header
    st.markdown(f'''
    <div class="slider-header">
        <span class="input-label">Toll Coverage %</span>
        <span class="min-viable">{min_text}</span>
    </div>
    ''', unsafe_allow_html=True)
    
    # Slider
    toll_pct = st.slider(
        "Toll Coverage",
        0, 100,
        value=80,
        label_visibility="collapsed"
    )
    
    # Calculate results
    result = calculate_project(toll_pct, toll_price)
    
    # Gearing bar
    gearing = result['gearing']
    bar_pct = (gearing - 45) / 35 * 100
    
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
    
    # Capital row
    st.markdown(f'''
    <div class="capital-row">
        <span>€{result['debt']:.0f}k debt</span>
        <span>€{result['equity']:.0f}k equity</span>
    </div>
    ''', unsafe_allow_html=True)
    
    # Terms row
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
    low_irr = result['low']['irr']
    base_irr = result['base']['irr']
    high_irr = result['high']['irr']
    min_dscr = result['low']['min_dscr']
    dscr_target = result['dscr_target']
    irr_spread = result['irr_spread']
    
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
    
    # Equity card
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
                <div class="result-value">{low_irr:.0f}% – {high_irr:.0f}%</div>
                <div class="result-detail">vs {hurdle}% hurdle</div>
            </div>
            <div class="result-badge">{eq_badge}</div>
        </div>
        <div class="result-footer">Base case: {base_irr:.1f}%</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Spread indicator
    spread_msg = "Higher toll = narrower spread" if toll_pct < 50 else "More certainty, less upside"
    st.markdown(f'''
    <div class="spread-indicator">
        <strong>{irr_spread:.0f}pp</strong> IRR spread (high − low) · {spread_msg}
    </div>
    ''', unsafe_allow_html=True)

# ============================================================================
# METHODOLOGY
# ============================================================================
with st.expander("Methodology & Assumptions"):
    st.markdown('''
    <div class="method-title">Revenue</div>
    <div class="method-section">
        <strong>Years 1–7:</strong> (Toll price × Toll %) + (Modo merchant forecast × (1 − Toll %))<br>
        <strong>Years 8–10:</strong> 100% merchant (toll expired, debt repaid)
    </div>
    
    <div class="method-title">Debt</div>
    <div class="method-section">
        Sized at <strong>45–80% gearing</strong> (scales with toll coverage). 7-year amortising loan at EURIBOR + 200–280 bps. 
        DSCR covenant tested against Modo low case: <strong>2.0×</strong> at 0% toll → <strong>1.2×</strong> at 100% toll.
    </div>
    
    <div class="method-title">Equity</div>
    <div class="method-section">
        IRR calculated over <strong>10 years</strong> (includes 3-year merchant tail post-toll). 
        Range shows Modo low/high revenue scenarios. Hurdle rate: <strong>10%</strong>.
    </div>
    
    <div class="method-title">Glossary</div>
    <div class="method-section">
        <strong>IRR</strong> — Internal Rate of Return. Annualised return on equity, accounting for timing of cash flows.<br>
        <strong>DSCR</strong> — Debt Service Coverage Ratio. Operating cash flow ÷ debt payments. A 1.5× means 50% headroom.<br>
        <strong>Gearing</strong> — Debt as % of total capital. Contracted revenue supports higher leverage.
    </div>
    
    <div class="fixed-assumptions">
        €625k/MW CapEx (inc. BKZ) · €10k/MW/yr OpEx · 2hr · 1.5 cycles/day · COD 2027
    </div>
    ''', unsafe_allow_html=True)

# ============================================================================
# FOOTER
# ============================================================================
st.markdown('''
<div class="footer">
    2hr · 1.5 cycle · 7yr toll/debt · 10yr equity IRR · COD 2027 · Modo forecasts
</div>
''', unsafe_allow_html=True)
