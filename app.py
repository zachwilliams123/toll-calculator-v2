"""
Battery Toll Calculator v4.0
Modo Energy - German BESS Educational Tool

MAJOR FIXES from v3:
1. DSCR scales correctly: 100% toll = 1.20x, 0% toll = 2.80x (linear)
2. Gearing limits enforced per ABN AMRO term sheet
3. Min Toll % solver fixed (recalculates terms inside loop)
4. UI overhaul: proper columns, clearer mode selector
5. Modo Energy black
6. Clearer labeling throughout
"""

import streamlit as st
import numpy as np
import numpy_financial as npf

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="Battery Toll Calculator | Modo Energy",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"], .stMarkdown, p, div, span, label {
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding: 1rem 1.5rem 1.5rem 1.5rem; max-width: 1000px;}
    
    /* Header */
    .header-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 0.75rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
    }
    .main-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #1a1a2e;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .subtitle {
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 0.1rem;
    }
    .brand-text {
        font-size: 0.85rem;
        color: #1a1a2e;
        font-weight: 600;
    }
    
    /* Mode selector */
    .mode-container {
        background: #f8fafc;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.75rem;
        border: 1px solid #e2e8f0;
    }
    .mode-title {
        font-size: 0.65rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    .mode-btn-row {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    /* Section cards */
    .section-card {
        background: #ffffff;
        border-radius: 10px;
        padding: 0.9rem 1rem;
        border: 1px solid #e2e8f0;
        margin-bottom: 0.6rem;
    }
    .section-title {
        font-size: 0.7rem;
        font-weight: 600;
        color: #475569;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    
    /* Result cards */
    .result-pass {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        border-radius: 10px;
        padding: 0.85rem 1rem;
        color: white;
        margin-bottom: 0.5rem;
    }
    .result-warn {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        border-radius: 10px;
        padding: 0.85rem 1rem;
        color: white;
        margin-bottom: 0.5rem;
    }
    .result-fail {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        border-radius: 10px;
        padding: 0.85rem 1rem;
        color: white;
        margin-bottom: 0.5rem;
    }
    .result-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .result-label {
        font-size: 0.65rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .result-value {
        font-size: 1.6rem;
        font-weight: 700;
        line-height: 1.1;
    }
    .result-detail {
        font-size: 0.75rem;
        opacity: 0.9;
        margin-top: 0.15rem;
    }
    .result-badge {
        font-size: 0.6rem;
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 5px;
        background: rgba(255,255,255,0.2);
    }
    
    /* Scenario grid */
    .scenario-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.4rem;
        margin-top: 0.4rem;
    }
    .scenario-box {
        border-radius: 7px;
        padding: 0.5rem 0.7rem;
        border: 1px solid #e2e8f0;
    }
    .scenario-box.green { background: #ecfdf5; border-color: #a7f3d0; }
    .scenario-box.amber { background: #fffbeb; border-color: #fde68a; }
    .scenario-box.red { background: #fef2f2; border-color: #fecaca; }
    .scenario-label { font-size: 0.65rem; color: #64748b; }
    .scenario-value { font-size: 0.95rem; font-weight: 600; }
    .scenario-value.green { color: #059669; }
    .scenario-value.amber { color: #d97706; }
    .scenario-value.red { color: #dc2626; }
    
    /* Metrics row */
    .metrics-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.4rem;
        margin-bottom: 0.5rem;
    }
    .metric-box {
        background: #f8fafc;
        border-radius: 7px;
        padding: 0.45rem 0.6rem;
        text-align: center;
        border: 1px solid #e2e8f0;
    }
    .metric-value {
        font-size: 0.9rem;
        font-weight: 700;
        color: #1e293b;
    }
    .metric-label {
        font-size: 0.55rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.02em;
    }
    
    /* Terms grid */
    .terms-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.4rem;
    }
    .term-box {
        background: #f1f5f9;
        border-radius: 6px;
        padding: 0.45rem 0.6rem;
        text-align: center;
    }
    .term-value {
        font-size: 0.85rem;
        font-weight: 600;
        color: #1e293b;
    }
    .term-label {
        font-size: 0.55rem;
        color: #64748b;
        text-transform: uppercase;
    }
    
    /* Solving indicator */
    .solved-box {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        border-radius: 8px;
        padding: 0.6rem 0.9rem;
        margin-bottom: 0.5rem;
        color: white;
    }
    .solved-label {
        font-size: 0.6rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .solved-value {
        font-size: 1.3rem;
        font-weight: 700;
    }
    .solved-context {
        font-size: 0.7rem;
        opacity: 0.9;
    }
    
    /* Warning box */
    .warning-box {
        background: #fef3c7;
        border: 1px solid #f59e0b;
        border-radius: 6px;
        padding: 0.5rem 0.7rem;
        margin-top: 0.4rem;
        font-size: 0.7rem;
        color: #92400e;
    }
    
    /* Note box */
    .note-box {
        background: #fefce8;
        border-radius: 6px;
        padding: 0.45rem 0.65rem;
        border: 1px solid #fef08a;
        font-size: 0.7rem;
        color: #854d0e;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        font-size: 0.6rem;
        color: #94a3b8;
        margin-top: 0.6rem;
        padding-top: 0.5rem;
        border-top: 1px solid #f1f5f9;
    }
    
    /* Streamlit overrides */
    div[data-testid="stSlider"] { padding-top: 0 !important; padding-bottom: 0.3rem !important; }
    div[data-testid="stSlider"] label p { font-size: 0.7rem !important; color: #475569 !important; }
    div[data-testid="stNumberInput"] label p { font-size: 0.7rem !important; color: #475569 !important; }
    div[data-testid="stCheckbox"] label p { font-size: 0.7rem !important; color: #475569 !important; }
    div[data-testid="stRadio"] label p { font-size: 0.7rem !important; }
    div[data-testid="stRadio"] > div { gap: 0.3rem !important; }
    .stButton button {
        font-size: 0.75rem !important;
        padding: 0.4rem 0.8rem !important;
        border-radius: 6px !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA & CONSTANTS
# ============================================================================
# Modo Energy German BESS Revenue Forecasts (€k/MW/year)
# Full forecast 2026-2040, user selects COD year
REVENUE_DATA_FULL = {
    'year': list(range(2026, 2041)),
    'low':  [142, 94, 76, 72, 69, 68, 68, 70, 67, 67, 69, 72, 73, 79, 75],      # Gas Low
    'base': [240, 155, 129, 124, 119, 117, 118, 118, 117, 114, 115, 119, 119, 118, 114], # Central
    'high': [319, 205, 168, 163, 158, 154, 157, 155, 151, 154, 154, 156, 150, 147, 135]  # Gas High
}

def get_revenue_data(cod_year):
    """Get 10-year revenue forecast starting from COD year"""
    start_idx = cod_year - 2026
    end_idx = start_idx + 10
    return {
        'year': REVENUE_DATA_FULL['year'][start_idx:end_idx],
        'low': REVENUE_DATA_FULL['low'][start_idx:end_idx],
        'base': REVENUE_DATA_FULL['base'][start_idx:end_idx],
        'high': REVENUE_DATA_FULL['high'][start_idx:end_idx]
    }

EURIBOR = 2.25  # Current 6-month EURIBOR (Jan 2026)

# ============================================================================
# FINANCING LOGIC (from ABN AMRO term sheet)
# ============================================================================
def get_dscr_target(toll_pct):
    """
    DSCR target by revenue structure (ABN AMRO term sheet):
    - Highly contracted (80-100%): 1.20x (fixed) to 1.75x (blended)
    - Partly contracted (40-79%): 1.75x to 2.00x
    - Fully merchant (0-39%): 2.00x to 2.80x
    
    Uses piecewise linear interpolation to match market practice.
    Higher merchant exposure = higher DSCR buffer required.
    """
    if toll_pct >= 80:
        # 80-100%: scales from 1.75x (at 80%) down to 1.20x (at 100%)
        return 1.75 - (toll_pct - 80) / 20 * 0.55
    elif toll_pct >= 40:
        # 40-79%: scales from 2.00x (at 40%) down to 1.75x (at 80%)
        return 2.00 - (toll_pct - 40) / 40 * 0.25
    else:
        # 0-39%: scales from 2.80x (at 0%) down to 2.00x (at 40%)
        return 2.80 - toll_pct / 40 * 0.80

def get_max_gearing(toll_pct):
    """
    Maximum gearing by revenue structure (ABN AMRO):
    - Highly contracted (80-100%): 75-85%
    - Partly contracted (40-79%): 60-75%
    - Fully merchant (0-39%): 40-50%
    """
    if toll_pct >= 80:
        return 85
    elif toll_pct >= 40:
        return 75
    else:
        return 50

def get_margin_bps(toll_pct):
    """
    Debt margin over EURIBOR (ABN AMRO):
    - Highly contracted: 185-220 bps
    - Partly contracted: 220-275 bps
    - Fully merchant: 275-350 bps
    """
    if toll_pct >= 80:
        return 200
    elif toll_pct >= 40:
        return 250
    else:
        return 310

def get_tenor(toll_pct):
    """
    Loan tenor (ABN AMRO):
    - Highly contracted: up to warranty (10-15 yrs)
    - Partly contracted: up to warranty (7-10 yrs)  
    - Fully merchant: 5-7 years
    """
    if toll_pct >= 80:
        return 12
    elif toll_pct >= 40:
        return 10
    else:
        return 7

def get_hurdle_rate(toll_pct):
    """
    Equity hurdle rate by risk profile:
    - Highly contracted: 10% (infrastructure-like)
    - Partly contracted: 12% (moderate risk)
    - Merchant-heavy: 14%
    - Full merchant: 16%
    """
    if toll_pct >= 80:
        return 10.0
    elif toll_pct >= 50:
        return 12.0
    elif toll_pct >= 20:
        return 14.0
    else:
        return 16.0

def get_risk_label(toll_pct):
    if toll_pct >= 80:
        return "Low risk"
    elif toll_pct >= 50:
        return "Medium risk"
    elif toll_pct >= 20:
        return "Higher risk"
    else:
        return "Merchant"

def get_structure_label(toll_pct):
    if toll_pct >= 80:
        return "Highly contracted"
    elif toll_pct >= 40:
        return "Partly contracted"
    else:
        return "Fully merchant"

# ============================================================================
# FINANCIAL MODEL
# ============================================================================
@st.cache_data
def calculate_project(capex, opex, gearing, toll_pct, toll_level, dscr_target, debt_rate, tenor, deg_on, cod_year):
    deg_rate = 0.025
    revenue_data = get_revenue_data(cod_year)
    years = revenue_data['year']
    n_years = len(years)
    
    # Degradation factors
    deg_factors = [(1 - deg_rate) ** i if deg_on else 1.0 for i in range(n_years)]
    
    # Apply degradation to merchant revenues
    low_rev = [revenue_data['low'][i] * deg_factors[i] for i in range(n_years)]
    base_rev = [revenue_data['base'][i] * deg_factors[i] for i in range(n_years)]
    high_rev = [revenue_data['high'][i] * deg_factors[i] for i in range(n_years)]
    
    toll_frac = toll_pct / 100
    
    def calc_total_rev(merchant_rev):
        # Toll portion: fixed at toll_level
        # Merchant portion: variable at merchant_rev
        return [toll_level * toll_frac + merchant_rev[i] * (1 - toll_frac) for i in range(n_years)]
    
    total_low = calc_total_rev(low_rev)
    total_base = calc_total_rev(base_rev)
    total_high = calc_total_rev(high_rev)
    
    # Capital structure
    total_capex = capex * 1000  # Convert to €/MW
    debt = total_capex * (gearing / 100)
    equity = total_capex - debt
    
    if equity <= 0:
        return None
    
    # Annual debt service (amortizing loan)
    if tenor > 0 and debt > 0:
        annual_rate = debt_rate / 100
        pmt = debt * (annual_rate * (1 + annual_rate)**tenor) / ((1 + annual_rate)**tenor - 1)
        debt_service = [pmt if i < tenor else 0 for i in range(n_years)]
    else:
        debt_service = [0] * n_years
    
    def calc_scenario(total_rev):
        # Net cashflow = Revenue - Opex
        net_cf = [(total_rev[i] * 1000 - opex * 1000) for i in range(n_years)]
        
        # Equity cashflow = Net CF - Debt Service
        equity_cf = [net_cf[i] - debt_service[i] for i in range(n_years)]
        
        # DSCR = Net CF / Debt Service
        dscr = [net_cf[i] / debt_service[i] if debt_service[i] > 0 else 99 for i in range(n_years)]
        min_dscr = min([d for d in dscr if d < 99]) if any(d < 99 for d in dscr) else 99
        
        # IRR
        equity_cf_with_invest = [-equity] + equity_cf
        try:
            irr = npf.irr(equity_cf_with_invest) * 100
            if np.isnan(irr) or irr < -50 or irr > 100:
                irr = -99
        except:
            irr = -99
        
        return {
            'net_cf': net_cf,
            'equity_cf': equity_cf,
            'dscr': dscr,
            'min_dscr': min_dscr,
            'irr': irr
        }
    
    low_result = calc_scenario(total_low)
    base_result = calc_scenario(total_base)
    high_result = calc_scenario(total_high)
    
    # Unlevered IRR (base case, no debt)
    unlev_cf = [-total_capex] + [(total_base[i] * 1000 - opex * 1000) for i in range(n_years)]
    try:
        unlev_irr = npf.irr(unlev_cf) * 100
        if np.isnan(unlev_irr):
            unlev_irr = 0
    except:
        unlev_irr = 0
    
    # Debt feasibility: test LOW CASE against DSCR target
    debt_feasible = low_result['min_dscr'] >= dscr_target
    
    return {
        'debt_feasible': debt_feasible,
        'gearing': gearing,
        'toll_pct': toll_pct,
        'toll_level': toll_level,
        'debt': debt / 1000,
        'equity': equity / 1000,
        'avg_debt_service': sum(debt_service[:tenor]) / tenor / 1000 if tenor > 0 else 0,
        'unlev_irr': unlev_irr,
        'dscr_target': dscr_target,
        'low_case': low_result,
        'base_case': base_result,
        'high_case': high_result,
    }

def find_max_gearing(capex, opex, toll_pct, toll_level, deg_on, cod_year):
    """Binary search for max gearing that passes DSCR"""
    dscr_target = get_dscr_target(toll_pct)
    margin = get_margin_bps(toll_pct)
    debt_rate = EURIBOR + margin / 100
    tenor = get_tenor(toll_pct)
    max_allowed = get_max_gearing(toll_pct)
    
    lo, hi = 0, max_allowed
    best = 0
    
    for _ in range(25):
        mid = (lo + hi) / 2
        result = calculate_project(capex, opex, mid, toll_pct, toll_level, dscr_target, debt_rate, tenor, deg_on, cod_year)
        if result and result['debt_feasible']:
            best = mid
            lo = mid
        else:
            hi = mid
    
    return round(best, 1)

def find_min_toll_pct(capex, opex, gearing, toll_level, deg_on, cod_year):
    """Binary search for minimum toll % that passes DSCR at given gearing"""
    lo, hi = 0, 100
    best = 100
    
    for _ in range(25):
        mid = (lo + hi) / 2
        
        # Recalculate financing terms for THIS toll %
        dscr_target = get_dscr_target(mid)
        margin = get_margin_bps(mid)
        debt_rate = EURIBOR + margin / 100
        tenor = get_tenor(mid)
        
        result = calculate_project(capex, opex, gearing, mid, toll_level, dscr_target, debt_rate, tenor, deg_on, cod_year)
        if result and result['debt_feasible']:
            best = mid
            hi = mid
        else:
            lo = mid
    
    return round(best, 1)

def find_min_toll_level(capex, opex, gearing, toll_pct, deg_on, cod_year):
    """Binary search for minimum toll level that passes DSCR"""
    dscr_target = get_dscr_target(toll_pct)
    margin = get_margin_bps(toll_pct)
    debt_rate = EURIBOR + margin / 100
    tenor = get_tenor(toll_pct)
    
    lo, hi = 50, 200
    best = 300
    
    for _ in range(25):
        mid = (lo + hi) / 2
        result = calculate_project(capex, opex, gearing, toll_pct, mid, dscr_target, debt_rate, tenor, deg_on, cod_year)
        if result and result['debt_feasible']:
            best = mid
            hi = mid
        else:
            lo = mid
    
    return round(best, 1)

# ============================================================================
# HEADER
# ============================================================================
st.markdown("""
<div class="header-row">
    <div>
        <div class="main-title">Battery Toll Calculator</div>
        <div class="subtitle">German BESS · Educational tool</div>
    </div>
    <div class="brand-text">Modo Energy</div>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# MODE SELECTOR
# ============================================================================
st.markdown('<div class="mode-container">', unsafe_allow_html=True)
st.markdown('<div class="mode-title">Calculator Mode</div>', unsafe_allow_html=True)

mode_cols = st.columns([1, 1, 2])
with mode_cols[0]:
    manual_btn = st.button("Manual", use_container_width=True, type="secondary" if st.session_state.get('mode', 'Manual') == 'Optimise' else "primary")
with mode_cols[1]:
    optimise_btn = st.button("Optimise", use_container_width=True, type="primary" if st.session_state.get('mode', 'Manual') == 'Optimise' else "secondary")

if manual_btn:
    st.session_state['mode'] = 'Manual'
if optimise_btn:
    st.session_state['mode'] = 'Optimise'

mode = st.session_state.get('mode', 'Manual')

# Solve-for selector (only if Optimise mode)
if mode == "Optimise":
    with mode_cols[2]:
        solve_for = st.radio(
            "Solve for:",
            ["Max Gearing", "Min Toll %", "Min Toll €"],
            horizontal=True,
            label_visibility="visible"
        )
else:
    solve_for = None

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# MAIN LAYOUT - TWO COLUMNS
# ============================================================================
left_col, right_col = st.columns([1, 1], gap="medium")

# ============================================================================
# LEFT COLUMN - INPUTS
# ============================================================================
with left_col:
    # STRUCTURE section
    st.markdown('<div class="section-card"><div class="section-title">Structure</div>', unsafe_allow_html=True)
    
    # Determine which inputs to show based on mode
    if mode == "Optimise" and solve_for == "Max Gearing":
        toll_pct = st.slider("Toll Coverage %", 0, 100, 65, help="% of asset capacity under toll agreement")
        toll_level = st.slider("Toll Level (€k/MW/yr)", 75, 150, 100, help="Annual payment per MW for tolled capacity")
        gearing = None  # Will be solved
    elif mode == "Optimise" and solve_for == "Min Toll %":
        gearing = st.slider("Gearing %", 10, 85, 65, help="Debt as % of total CapEx")
        toll_level = st.slider("Toll Level (€k/MW/yr)", 75, 150, 100)
        toll_pct = None  # Will be solved
    elif mode == "Optimise" and solve_for == "Min Toll €":
        gearing = st.slider("Gearing %", 10, 85, 65)
        toll_pct = st.slider("Toll Coverage %", 0, 100, 65)
        toll_level = None  # Will be solved
    else:  # Manual mode
        gearing = st.slider("Gearing %", 10, 85, 65)
        toll_pct = st.slider("Toll Coverage %", 0, 100, 65)
        toll_level = st.slider("Toll Level (€k/MW/yr)", 75, 150, 100)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # PROJECT section
    st.markdown('<div class="section-card"><div class="section-title">Project</div>', unsafe_allow_html=True)
    proj_cols = st.columns(3)
    with proj_cols[0]:
        capex = st.number_input("CapEx (€k/MW)", 300, 1000, 600, 25)
    with proj_cols[1]:
        opex = st.number_input("Opex (€k/yr)", 0, 30, 7, 1)
    with proj_cols[2]:
        cod_year = st.selectbox("COD Year", [2026, 2027, 2028], index=1, help="Commercial Operation Date")
    deg_on = st.checkbox("Capacity degradation (2.5%/yr)", True)
    
    # Show toll as % of COD year base revenue
    if toll_level is not None:
        cod_revenue = get_revenue_data(cod_year)
        year1_base = cod_revenue['base'][0]
        toll_pct_of_base = (toll_level / year1_base) * 100
        st.caption(f"Toll = {toll_pct_of_base:.0f}% of {cod_year} base case (€{year1_base}k)")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # FINANCING TERMS section
    st.markdown('<div class="section-card"><div class="section-title">Financing Terms</div>', unsafe_allow_html=True)
    
    # Calculate auto terms (use toll_pct if available, else default)
    display_toll_pct = toll_pct if toll_pct is not None else 65
    dscr_target = get_dscr_target(display_toll_pct)
    margin = get_margin_bps(display_toll_pct)
    debt_rate = EURIBOR + margin / 100
    tenor = get_tenor(display_toll_pct)
    max_gear = get_max_gearing(display_toll_pct)
    structure_label = get_structure_label(display_toll_pct)
    
    terms_html = f"""
    <div class="terms-grid">
        <div class="term-box">
            <div class="term-value">{dscr_target:.2f}x</div>
            <div class="term-label">DSCR Target</div>
        </div>
        <div class="term-box">
            <div class="term-value">{debt_rate:.1f}%</div>
            <div class="term-label">Rate (E+{margin})</div>
        </div>
        <div class="term-box">
            <div class="term-value">{tenor} yrs</div>
            <div class="term-label">Tenor</div>
        </div>
    </div>
    """
    st.markdown(terms_html, unsafe_allow_html=True)
    st.caption(f"{structure_label} · Max gearing {max_gear}%")
    
    # Gearing warning
    if gearing is not None and gearing > max_gear:
        st.markdown(f'<div class="warning-box">Gearing ({gearing}%) exceeds typical max ({max_gear}%) for {structure_label.lower()} structures</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# SOLVE (if optimising)
# ============================================================================
if mode == "Optimise":
    if solve_for == "Max Gearing":
        gearing = find_max_gearing(capex, opex, toll_pct, toll_level, deg_on, cod_year)
    elif solve_for == "Min Toll %":
        toll_pct = find_min_toll_pct(capex, opex, gearing, toll_level, deg_on, cod_year)
    elif solve_for == "Min Toll €":
        toll_level = find_min_toll_level(capex, opex, gearing, toll_pct, deg_on, cod_year)

# Recalculate final financing terms with solved values
final_toll_pct = toll_pct if toll_pct is not None else 65
final_dscr_target = get_dscr_target(final_toll_pct)
final_margin = get_margin_bps(final_toll_pct)
final_debt_rate = EURIBOR + final_margin / 100
final_tenor = get_tenor(final_toll_pct)

# Calculate results
result = calculate_project(capex, opex, gearing, final_toll_pct, toll_level, final_dscr_target, final_debt_rate, final_tenor, deg_on, cod_year)

# ============================================================================
# RIGHT COLUMN - RESULTS
# ============================================================================
with right_col:
    if result:
        hurdle = get_hurdle_rate(final_toll_pct)
        risk_label = get_risk_label(final_toll_pct)
        
        base_irr = result['base_case']['irr']
        low_irr = result['low_case']['irr']
        high_irr = result['high_case']['irr']
        min_dscr = result['low_case']['min_dscr']
        
        # Show solved value prominently if optimising
        if mode == "Optimise":
            if solve_for == "Max Gearing":
                solved_html = f"""
                <div class="solved-box">
                    <div class="solved-label">Maximum Gearing</div>
                    <div class="solved-value">{gearing:.1f}%</div>
                    <div class="solved-context">at {toll_pct}% toll coverage, {cod_year} COD</div>
                </div>
                """
            elif solve_for == "Min Toll %":
                solved_html = f"""
                <div class="solved-box">
                    <div class="solved-label">Minimum Toll Coverage</div>
                    <div class="solved-value">{toll_pct:.1f}%</div>
                    <div class="solved-context">at {gearing}% gearing, {cod_year} COD</div>
                </div>
                """
            elif solve_for == "Min Toll €":
                solved_html = f"""
                <div class="solved-box">
                    <div class="solved-label">Minimum Toll Level</div>
                    <div class="solved-value">{toll_level:.0f}k/MW/yr</div>
                    <div class="solved-context">at {gearing}% gearing, {toll_pct}% coverage</div>
                </div>
                """
            st.markdown(solved_html, unsafe_allow_html=True)
        
        # ---- DEBT FEASIBILITY (top) ----
        dscr_margin = min_dscr - final_dscr_target
        if result['debt_feasible']:
            debt_class = "result-pass"
            debt_badge = "FEASIBLE"
        else:
            debt_class = "result-fail"
            debt_badge = "NOT FEASIBLE"
        
        dscr_sign = "+" if dscr_margin >= 0 else ""
        debt_html = f"""
        <div class="{debt_class}">
            <div class="result-header">
                <div>
                    <div class="result-label">Debt Feasibility (Low Case DSCR)</div>
                    <div class="result-value">{min_dscr:.2f}x</div>
                    <div class="result-detail">vs {final_dscr_target:.2f}x target ({dscr_sign}{dscr_margin:.2f}x buffer)</div>
                </div>
                <div class="result-badge">{debt_badge}</div>
            </div>
        </div>
        """
        st.markdown(debt_html, unsafe_allow_html=True)
        
        # ---- EQUITY RETURNS ----
        irr_vs_hurdle = base_irr - hurdle
        if irr_vs_hurdle >= 0:
            equity_class = "result-pass"
            equity_badge = "MEETS HURDLE"
        elif irr_vs_hurdle >= -3:
            equity_class = "result-warn"
            equity_badge = "NEAR HURDLE"
        else:
            equity_class = "result-fail"
            equity_badge = "BELOW HURDLE"
        
        sign = "+" if irr_vs_hurdle >= 0 else ""
        equity_html = f"""
        <div class="{equity_class}">
            <div class="result-header">
                <div>
                    <div class="result-label">Equity IRR (Base Case)</div>
                    <div class="result-value">{base_irr:.1f}%</div>
                    <div class="result-detail">vs {hurdle:.0f}% hurdle ({sign}{irr_vs_hurdle:.1f}%)</div>
                </div>
                <div class="result-badge">{equity_badge}</div>
            </div>
        </div>
        """
        st.markdown(equity_html, unsafe_allow_html=True)
        
        # ---- SCENARIO BOXES (Low/High) ----
        def get_class(irr, h):
            if irr >= h: return "green"
            elif irr >= h - 3: return "amber"
            else: return "red"
        
        low_class = get_class(low_irr, hurdle)
        high_class = get_class(high_irr, hurdle)
        
        scenario_html = f"""
        <div class="scenario-grid">
            <div class="scenario-box {low_class}">
                <div class="scenario-label">Low Case IRR</div>
                <div class="scenario-value {low_class}">{low_irr:.1f}%</div>
            </div>
            <div class="scenario-box {high_class}">
                <div class="scenario-label">High Case IRR</div>
                <div class="scenario-value {high_class}">{high_irr:.1f}%</div>
            </div>
        </div>
        """
        st.markdown(scenario_html, unsafe_allow_html=True)
        
        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
        
        # ---- FINANCIAL SUMMARY ----
        metrics_html = f"""
        <div class="metrics-row">
            <div class="metric-box">
                <div class="metric-value">{result['unlev_irr']:.1f}%</div>
                <div class="metric-label">Unlev IRR</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{result['gearing']:.0f}%</div>
                <div class="metric-label">Gearing</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{result['debt']:.0f}k</div>
                <div class="metric-label">Debt</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{result['equity']:.0f}k</div>
                <div class="metric-label">Equity</div>
            </div>
        </div>
        """
        st.markdown(metrics_html, unsafe_allow_html=True)
        
        # Leverage effect note
        lev_effect = base_irr - result['unlev_irr']
        lev_sign = "+" if lev_effect >= 0 else ""
        st.markdown(f'<div class="note-box">Leverage effect: {result["unlev_irr"]:.1f}% unlevered to {base_irr:.1f}% levered ({lev_sign}{lev_effect:.1f}%)</div>', unsafe_allow_html=True)
        
    else:
        st.error("Unable to calculate. Check inputs.")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown('<div class="footer">1.5 cycle · 2hr duration · German BESS · Modo forecasts 2026–2040 · Educational only · Not financial advice</div>', unsafe_allow_html=True)
