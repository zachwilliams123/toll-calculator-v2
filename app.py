"""
Battery Toll Calculator v14
Modo Energy - German BESS

7-year aligned horizon (toll, debt, equity IRR)
Disclaimer at top
Tighter methodology/glossary
"""

import streamlit as st
import numpy as np
import numpy_financial as npf

st.set_page_config(page_title="Battery Toll Calculator | Modo Energy", layout="wide", initial_sidebar_state="collapsed")

# ============================================================================
# FIXED ASSUMPTIONS
# ============================================================================
CAPEX = 625  # €k/MW (including BKZ)
OPEX = 7     # €k/MW/yr
EURIBOR = 2.25  # %
TENOR = 7    # years (debt, toll, and equity IRR horizon)
DURATION = 2  # hours
CYCLES = 1.5  # per day
DEGRADATION = 0.025  # 2.5% per year

# Revenue forecasts (€k/MW/yr) - Modo Energy German BESS merchant forecasts
# Only need 7 years now
REVENUE_DATA = {
    'low':  [94, 76, 72, 69, 68, 68, 70],
    'base': [155, 129, 124, 119, 117, 118, 118],
    'high': [205, 168, 163, 158, 154, 157, 155],
}

# ============================================================================
# CSS
# ============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"], .stMarkdown, p, div, span, label {
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding: 1rem 2rem 0.5rem 2rem; max-width: 950px;}
    
    /* Disclaimer banner */
    .disclaimer {
        font-size: 0.65rem; color: #64748b; text-align: center;
        padding: 0.4rem 0.8rem; background: #f8fafc; border-radius: 6px;
        margin-bottom: 0.6rem; border: 1px solid #e2e8f0;
    }
    .disclaimer a { color: #3b82f6; text-decoration: none; }
    
    .header-row {
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 0.6rem; padding-bottom: 0.5rem; border-bottom: 2px solid #e2e8f0;
    }
    .main-title { font-size: 1.3rem; font-weight: 700; color: #1a1a2e; }
    .brand-text { font-size: 0.8rem; color: #1a1a2e; font-weight: 600; }
    
    .section-label {
        font-size: 0.7rem; font-weight: 600; color: #64748b;
        margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.05em;
    }
    
    /* Gearing bar */
    .gearing-row {
        display: flex; align-items: center; gap: 0.6rem; margin: 0.5rem 0 0.3rem 0;
    }
    .gearing-label { font-size: 0.75rem; color: #64748b; min-width: 50px; }
    .gearing-bar-bg {
        flex: 1; background: #e2e8f0; border-radius: 5px; height: 22px;
        position: relative; overflow: hidden;
    }
    .gearing-bar-fill {
        background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%);
        height: 100%; border-radius: 5px;
        display: flex; align-items: center; justify-content: flex-end; padding-right: 10px;
    }
    .gearing-value { font-size: 0.75rem; font-weight: 600; color: white; }
    
    /* Capital row under gearing */
    .capital-row {
        display: flex; justify-content: flex-end; gap: 1rem;
        font-size: 0.7rem; color: #64748b; margin-bottom: 0.5rem;
    }
    .capital-row span { font-weight: 500; }
    
    /* Terms row */
    .terms-row {
        display: flex; gap: 0.6rem; padding-top: 0.5rem;
        border-top: 1px solid #f1f5f9; margin-top: 0.3rem;
    }
    .term-chip {
        font-size: 0.7rem; color: #475569;
    }
    .term-chip strong { color: #1e293b; }
    
    /* Result cards */
    .result-card {
        border-radius: 10px; padding: 0.9rem 1rem; color: white; margin-bottom: 0.5rem;
    }
    .result-card.pass { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
    .result-card.warn { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }
    .result-card.fail { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }
    
    .result-header { display: flex; justify-content: space-between; align-items: flex-start; }
    .result-label { font-size: 0.55rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 0.03em; margin-bottom: 0.2rem; }
    .result-value { font-size: 1.6rem; font-weight: 700; line-height: 1.1; }
    .result-detail { font-size: 0.7rem; opacity: 0.9; margin-top: 0.15rem; }
    .result-badge { 
        font-size: 0.5rem; font-weight: 600; padding: 4px 10px; 
        border-radius: 4px; background: rgba(255,255,255,0.2); 
        align-self: flex-start; margin-top: 0.2rem;
    }
    
    .result-scenarios {
        font-size: 0.7rem; opacity: 0.85; margin-top: 0.5rem;
        padding-top: 0.5rem; border-top: 1px solid rgba(255,255,255,0.2);
    }
    
    .footer { 
        text-align: center; font-size: 0.55rem; color: #94a3b8; 
        margin-top: 0.6rem; padding-top: 0.5rem; border-top: 1px solid #f1f5f9; 
    }
    
    /* Streamlit overrides */
    div[data-testid="stSlider"] { padding-top: 0 !important; padding-bottom: 0.3rem !important; }
    div[data-testid="stSlider"] label p { font-size: 0.75rem !important; color: #475569 !important; }
    div[data-testid="stNumberInput"] label p { font-size: 0.75rem !important; color: #475569 !important; }
    div[data-testid="stNumberInput"] { margin-bottom: 0.15rem; }
    div[data-testid="stNumberInput"] input { 
        font-size: 0.85rem !important; 
        background-color: #f1f5f9 !important;
        border: none !important;
    }
    div[data-testid="stNumberInput"] > div { max-width: 130px; }
    div[data-testid="stNumberInput"] > div > div { 
        background-color: #f1f5f9 !important; 
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        overflow: hidden;
    }
    div[data-testid="stNumberInput"] button {
        background-color: #f1f5f9 !important;
        border: none !important;
        border-left: 1px solid #e2e8f0 !important;
        color: #64748b !important;
        border-radius: 0 !important;
    }
    
    /* Expander styling */
    div[data-testid="stExpander"] {
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        margin-top: 0.5rem;
    }
    div[data-testid="stExpander"] summary {
        font-size: 0.7rem !important;
        color: #64748b !important;
        padding: 0.5rem 0.8rem !important;
    }
    div[data-testid="stExpander"] summary span {
        font-size: 0.7rem !important;
    }
    div[data-testid="stExpander"] > div > div {
        padding: 0 0.8rem 0.8rem 0.8rem !important;
    }
    
    /* Methodology content */
    .method-section {
        font-size: 0.68rem; color: #475569; line-height: 1.5;
        margin-bottom: 0.6rem;
    }
    .method-section strong { color: #1e293b; }
    .method-title {
        font-size: 0.7rem; font-weight: 600; color: #1e293b;
        margin-bottom: 0.3rem; margin-top: 0.5rem;
    }
    .method-title:first-child { margin-top: 0; }
    .glossary-term {
        font-size: 0.68rem; margin-bottom: 0.4rem;
    }
    .glossary-term strong { color: #1e293b; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# FINANCING FORMULAS
# ============================================================================
def get_gearing(toll_pct: float) -> float:
    """Gearing: 45% at 0% toll → 80% at 100% toll"""
    return 45 + toll_pct * 0.35

def get_dscr_target(toll_pct: float) -> float:
    """DSCR covenant: 2.00× at 0% toll → 1.20× at 100% toll"""
    return 2.00 - toll_pct * 0.008

def get_margin_bps(toll_pct: float) -> float:
    """Debt margin: 280 bps at 0% toll → 200 bps at 100% toll"""
    return 280 - toll_pct * 0.80

def get_equity_hurdle(toll_pct: float) -> float:
    """Equity hurdle: 16% (<20% toll) → 10% (80%+ toll)"""
    if toll_pct >= 80:
        return 10.0
    elif toll_pct >= 50:
        return 12.0
    elif toll_pct >= 20:
        return 14.0
    else:
        return 16.0

# ============================================================================
# FINANCIAL MODEL (7-YEAR HORIZON)
# ============================================================================
def calculate_project(toll_pct: float, toll_price: float) -> dict:
    """Calculate project financials over 7-year toll/debt tenor"""
    
    # Financing terms
    gearing = get_gearing(toll_pct)
    dscr_target = get_dscr_target(toll_pct)
    margin_bps = get_margin_bps(toll_pct)
    all_in_rate = (EURIBOR + margin_bps / 100) / 100
    
    # Capital structure
    total_capex = CAPEX * 1000  # €/MW
    debt = total_capex * gearing / 100
    equity = total_capex - debt
    
    # Degradation factors
    degradation_factors = [(1 - DEGRADATION) ** i for i in range(TENOR)]
    
    # Revenue: toll + merchant (7 years)
    toll_fraction = toll_pct / 100
    
    def build_revenue_series(merchant_forecast: list) -> list:
        return [
            toll_price * toll_fraction + 
            merchant_forecast[i] * degradation_factors[i] * (1 - toll_fraction)
            for i in range(TENOR)
        ]
    
    rev_low = build_revenue_series(REVENUE_DATA['low'])
    rev_base = build_revenue_series(REVENUE_DATA['base'])
    rev_high = build_revenue_series(REVENUE_DATA['high'])
    
    # Debt service (7-year amortizing)
    if debt > 0 and all_in_rate > 0:
        r = all_in_rate
        n = TENOR
        annual_debt_service = debt * (r * (1 + r)**n) / ((1 + r)**n - 1)
    else:
        annual_debt_service = 0
    
    debt_service = [annual_debt_service for _ in range(TENOR)]
    
    def calculate_scenario(revenue_series: list) -> dict:
        """Calculate IRR and DSCR for a scenario"""
        # Net cash flow = Revenue - OpEx
        net_cash_flow = [revenue_series[i] * 1000 - OPEX * 1000 for i in range(TENOR)]
        
        # Equity cash flow = NCF - Debt Service
        equity_cash_flow = [net_cash_flow[i] - debt_service[i] for i in range(TENOR)]
        
        # DSCR for each year
        dscr_values = [net_cash_flow[i] / debt_service[i] if debt_service[i] > 0 else 99 for i in range(TENOR)]
        min_dscr = min(dscr_values)
        
        # Equity IRR over 7 years
        try:
            irr = npf.irr([-equity] + equity_cash_flow) * 100
            if np.isnan(irr) or irr < -50 or irr > 200:
                irr = -99.0
        except:
            irr = -99.0
        
        return {'irr': irr, 'min_dscr': min_dscr}
    
    low_result = calculate_scenario(rev_low)
    base_result = calculate_scenario(rev_base)
    high_result = calculate_scenario(rev_high)
    
    # Debt feasibility: DSCR vs covenant in LOW case
    debt_feasible = low_result['min_dscr'] >= dscr_target
    
    return {
        'gearing': gearing,
        'debt': debt / 1000,
        'equity': equity / 1000,
        'dscr_target': dscr_target,
        'margin_bps': margin_bps,
        'all_in_rate': all_in_rate * 100,
        'debt_feasible': debt_feasible,
        'low': low_result,
        'base': base_result,
        'high': high_result,
    }

def find_minimum_viable_coverage(toll_price: float) -> int | None:
    """Find minimum toll coverage % that passes debt feasibility"""
    for t in range(0, 101):
        result = calculate_project(t, toll_price)
        if result['debt_feasible']:
            return t
    return None

# ============================================================================
# DISCLAIMER
# ============================================================================
st.markdown('''
<div class="disclaimer">
    Model for educational purposes only. <a href="https://modoenergy.com/contact">Contact Modo Energy</a> for detailed project analysis.
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
left, right = st.columns([1, 1.1], gap="large")

with left:
    st.markdown('<div class="section-label">Structure</div>', unsafe_allow_html=True)
    
    # Toll price
    toll_price = st.number_input(
        "Toll Price (€k/MW/yr)", 
        min_value=80, 
        max_value=140, 
        value=120, 
        step=5,
        key="toll_price"
    )
    
    # Min viable coverage
    min_cov = find_minimum_viable_coverage(toll_price)
    if min_cov is not None:
        min_text = f'Min viable: <strong>{min_cov}%</strong>'
    else:
        min_text = '<span style="color: #ef4444;">Not viable</span>'
    
    st.markdown(f'''
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.2rem;">
        <span style="font-size: 0.75rem; color: #475569;">Toll Coverage %</span>
        <span style="font-size: 0.7rem; color: #64748b;">{min_text}</span>
    </div>
    ''', unsafe_allow_html=True)
    
    toll_pct = st.slider(
        "Toll Coverage %", 
        0, 100, 
        value=80,
        key="toll_pct",
        label_visibility="collapsed"
    )
    
    # Calculate
    result = calculate_project(toll_pct, toll_price)
    
    # Gearing bar
    gearing = result['gearing']
    bar_pct = (gearing - 45) / 35 * 100
    
    st.markdown(f'''
    <div class="gearing-row">
        <span class="gearing-label">Gearing</span>
        <div class="gearing-bar-bg">
            <div class="gearing-bar-fill" style="width: {bar_pct}%;">
                <span class="gearing-value">{gearing:.0f}%</span>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Debt/Equity
    st.markdown(f'''
    <div class="capital-row">
        <span>€{result['debt']:.0f}k debt</span>
        <span>€{result['equity']:.0f}k equity</span>
    </div>
    ''', unsafe_allow_html=True)
    
    # Terms
    st.markdown(f'''
    <div class="terms-row">
        <span class="term-chip"><strong>{result['dscr_target']:.2f}x</strong> DSCR</span>
        <span class="term-chip"><strong>{result['all_in_rate']:.1f}%</strong> rate</span>
        <span class="term-chip"><strong>{TENOR}yr</strong> tenor</span>
    </div>
    ''', unsafe_allow_html=True)

# ============================================================================
# RESULTS
# ============================================================================
with right:
    st.markdown('<div class="section-label">Results</div>', unsafe_allow_html=True)
    
    hurdle = get_equity_hurdle(toll_pct)
    base_irr = result['base']['irr']
    low_irr = result['low']['irr']
    high_irr = result['high']['irr']
    min_dscr = result['low']['min_dscr']
    dscr_target = result['dscr_target']
    
    # DEBT card
    dscr_margin = min_dscr - dscr_target
    debt_class = "pass" if result['debt_feasible'] else "fail"
    debt_badge = "FEASIBLE" if result['debt_feasible'] else "NOT FEASIBLE"
    dscr_sign = "+" if dscr_margin >= 0 else ""
    
    st.markdown(f'''
    <div class="result-card {debt_class}">
        <div class="result-header">
            <div>
                <div class="result-label">Debt</div>
                <div class="result-value">{min_dscr:.2f}x</div>
                <div class="result-detail">vs {dscr_target:.2f}x DSCR target ({dscr_sign}{dscr_margin:.2f}x)</div>
            </div>
            <div class="result-badge">{debt_badge}</div>
        </div>
    </div>
    <div style="font-size: 0.6rem; color: #64748b; margin-top: -0.3rem; margin-bottom: 0.5rem;">
        DSCR tested against Modo low case
    </div>
    ''', unsafe_allow_html=True)
    
    # EQUITY card
    irr_delta = base_irr - hurdle
    if irr_delta >= 0:
        eq_class, eq_badge = "pass", "MEETS HURDLE"
    elif irr_delta >= -3:
        eq_class, eq_badge = "warn", "NEAR HURDLE"
    else:
        eq_class, eq_badge = "fail", "BELOW HURDLE"
    
    sign = "+" if irr_delta >= 0 else ""
    st.markdown(f'''
    <div class="result-card {eq_class}">
        <div class="result-header">
            <div>
                <div class="result-label">Equity IRR ({TENOR}yr)</div>
                <div class="result-value">{base_irr:.1f}%</div>
                <div class="result-detail">vs {hurdle:.0f}% hurdle ({sign}{irr_delta:.1f}%)</div>
            </div>
            <div class="result-badge">{eq_badge}</div>
        </div>
        <div class="result-scenarios">
            {low_irr:.1f}% low · {high_irr:.1f}% high
        </div>
    </div>
    ''', unsafe_allow_html=True)

# ============================================================================
# METHODOLOGY (spans full width)
# ============================================================================
with st.expander("Methodology & Assumptions"):
    st.markdown(f'''
<div class="method-title">Revenue</div>
<div class="method-section">
Total = (Toll price × Toll %) + (Modo merchant forecast × (1 − Toll %) × degradation factor)
</div>

<div class="method-title">Debt</div>
<div class="method-section">
Sized at <strong>45–80% gearing</strong> (scales with toll coverage). DSCR covenant tested against Modo low case: <strong>2.0×</strong> at 0% toll → <strong>1.2×</strong> at 100% toll. 7-year amortising loan at EURIBOR + 200–280 bps.
</div>

<div class="method-title">Equity</div>
<div class="method-section">
IRR calculated over <strong>7-year toll tenor</strong> using Modo base case. Hurdle rates reflect risk: <strong>10%</strong> (≥80% toll), <strong>12%</strong> (50–79%), <strong>14%</strong> (20–49%), <strong>16%</strong> (&lt;20%).
</div>

<div class="method-title">Glossary</div>
<div class="glossary-term">
<strong>IRR (Internal Rate of Return)</strong> — The annualised return on equity capital. Measures what investors earn on their investment over the project life, accounting for the timing of cash flows.
</div>
<div class="glossary-term">
<strong>DSCR (Debt Service Coverage Ratio)</strong> — How many times operating cash flow covers debt payments. A 1.5× DSCR means the project generates 50% more cash than needed to service debt. Lenders set minimum covenants as a buffer against underperformance.
</div>
<div class="glossary-term">
<strong>Gearing</strong> — Debt as a percentage of total capital. Higher gearing amplifies equity returns but increases risk. Contracted revenue supports higher leverage.
</div>

<div class="method-title">Fixed Assumptions</div>
<div class="method-section">
€{CAPEX}k/MW CapEx (inc. BKZ) · €{OPEX}k/MW/yr OpEx · {DURATION}hr duration · {CYCLES} cycles/day · {DEGRADATION*100:.1f}% annual degradation · COD 2027
</div>
    ''', unsafe_allow_html=True)

# ============================================================================
# FOOTER
# ============================================================================
st.markdown(f'''
<div class="footer">
    {DURATION}hr · {CYCLES} cycle · {TENOR}yr tenor · {DEGRADATION*100:.1f}% degradation · COD 2027 · Modo forecasts
</div>
''', unsafe_allow_html=True)
