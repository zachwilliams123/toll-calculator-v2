"""
Battery Toll Calculator v5.0
Modo Energy - German BESS Educational Tool

Changes in v5:
- Dropdown for Manual/Optimise mode
- Frozen slider approach for solver (shows solved value inline)
- 3-column symmetric layout: Structure | Project | Financing Terms
- Gearing warning near slider
- Cleaner results section
- Toll level: 70-130, default 100
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
    .block-container {padding: 1rem 1.5rem 1.5rem 1.5rem; max-width: 1100px;}
    
    /* Header */
    .header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.6rem;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #e2e8f0;
    }
    .main-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #1a1a2e;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .brand-text {
        font-size: 0.8rem;
        color: #1a1a2e;
        font-weight: 600;
    }
    
    /* Section cards */
    .section-card {
        background: #ffffff;
        border-radius: 8px;
        padding: 0.7rem 0.9rem;
        border: 1px solid #e2e8f0;
        height: 100%;
    }
    .section-title {
        font-size: 0.65rem;
        font-weight: 600;
        color: #64748b;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Solved value display (frozen slider) */
    .solved-value {
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 0.35rem 0.6rem;
        margin-bottom: 0.35rem;
    }
    .solved-label {
        font-size: 0.6rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    .solved-number {
        font-size: 1rem;
        font-weight: 600;
        color: #3b82f6;
    }
    
    /* Gearing warning */
    .gearing-warning {
        background: #fef3c7;
        border-left: 3px solid #f59e0b;
        padding: 0.3rem 0.5rem;
        margin-top: 0.2rem;
        font-size: 0.65rem;
        color: #92400e;
        border-radius: 0 4px 4px 0;
    }
    
    /* Terms display */
    .terms-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.4rem;
    }
    .term-item {
        background: #f8fafc;
        border-radius: 5px;
        padding: 0.4rem 0.5rem;
        text-align: center;
    }
    .term-value {
        font-size: 0.9rem;
        font-weight: 600;
        color: #1e293b;
    }
    .term-label {
        font-size: 0.55rem;
        color: #64748b;
        text-transform: uppercase;
    }
    
    /* Result cards */
    .result-pass {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        border-radius: 8px;
        padding: 0.7rem 0.9rem;
        color: white;
        margin-bottom: 0.4rem;
    }
    .result-warn {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        border-radius: 8px;
        padding: 0.7rem 0.9rem;
        color: white;
        margin-bottom: 0.4rem;
    }
    .result-fail {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        border-radius: 8px;
        padding: 0.7rem 0.9rem;
        color: white;
        margin-bottom: 0.4rem;
    }
    .result-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .result-label {
        font-size: 0.6rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    .result-value {
        font-size: 1.4rem;
        font-weight: 700;
        line-height: 1.1;
    }
    .result-detail {
        font-size: 0.7rem;
        opacity: 0.9;
    }
    .result-badge {
        font-size: 0.55rem;
        font-weight: 600;
        padding: 3px 7px;
        border-radius: 4px;
        background: rgba(255,255,255,0.2);
    }
    
    /* Scenario boxes */
    .scenario-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.4rem;
        margin-bottom: 0.4rem;
    }
    .scenario-box {
        border-radius: 6px;
        padding: 0.45rem 0.6rem;
        text-align: center;
    }
    .scenario-box.green { background: #ecfdf5; border: 1px solid #a7f3d0; }
    .scenario-box.amber { background: #fffbeb; border: 1px solid #fde68a; }
    .scenario-box.red { background: #fef2f2; border: 1px solid #fecaca; }
    .scenario-label { font-size: 0.6rem; color: #64748b; }
    .scenario-value { font-size: 0.95rem; font-weight: 600; }
    .scenario-value.green { color: #059669; }
    .scenario-value.amber { color: #d97706; }
    .scenario-value.red { color: #dc2626; }
    
    /* Metrics grid */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.35rem;
    }
    .metric-box {
        background: #f8fafc;
        border-radius: 6px;
        padding: 0.4rem 0.5rem;
        text-align: center;
        border: 1px solid #e2e8f0;
    }
    .metric-value {
        font-size: 0.85rem;
        font-weight: 700;
        color: #1e293b;
    }
    .metric-label {
        font-size: 0.5rem;
        color: #64748b;
        text-transform: uppercase;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        font-size: 0.55rem;
        color: #94a3b8;
        margin-top: 0.5rem;
        padding-top: 0.4rem;
        border-top: 1px solid #f1f5f9;
    }
    
    /* Streamlit overrides */
    div[data-testid="stSlider"] { padding-top: 0 !important; padding-bottom: 0.25rem !important; }
    div[data-testid="stSlider"] label p { font-size: 0.7rem !important; color: #475569 !important; }
    div[data-testid="stNumberInput"] label p { font-size: 0.7rem !important; color: #475569 !important; }
    div[data-testid="stSelectbox"] label p { font-size: 0.7rem !important; color: #475569 !important; }
    div[data-testid="stCheckbox"] label p { font-size: 0.65rem !important; color: #475569 !important; }
    
    /* Make selectbox smaller */
    div[data-testid="stSelectbox"] { margin-bottom: 0.3rem; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA & CONSTANTS
# ============================================================================
REVENUE_DATA_FULL = {
    'year': list(range(2026, 2041)),
    'low':  [142, 94, 76, 72, 69, 68, 68, 70, 67, 67, 69, 72, 73, 79, 75],
    'base': [240, 155, 129, 124, 119, 117, 118, 118, 117, 114, 115, 119, 119, 118, 114],
    'high': [319, 205, 168, 163, 158, 154, 157, 155, 151, 154, 154, 156, 150, 147, 135]
}

def get_revenue_data(cod_year):
    start_idx = cod_year - 2026
    end_idx = start_idx + 10
    return {
        'year': REVENUE_DATA_FULL['year'][start_idx:end_idx],
        'low': REVENUE_DATA_FULL['low'][start_idx:end_idx],
        'base': REVENUE_DATA_FULL['base'][start_idx:end_idx],
        'high': REVENUE_DATA_FULL['high'][start_idx:end_idx]
    }

EURIBOR = 2.25

# ============================================================================
# FINANCING LOGIC
# ============================================================================
def get_dscr_target(toll_pct):
    if toll_pct >= 80:
        return 1.75 - (toll_pct - 80) / 20 * 0.55
    elif toll_pct >= 40:
        return 2.00 - (toll_pct - 40) / 40 * 0.25
    else:
        return 2.80 - toll_pct / 40 * 0.80

def get_max_gearing(toll_pct):
    if toll_pct >= 80: return 85
    elif toll_pct >= 40: return 75
    else: return 50

def get_margin_bps(toll_pct):
    if toll_pct >= 80: return 200
    elif toll_pct >= 40: return 250
    else: return 310

def get_tenor(toll_pct):
    if toll_pct >= 80: return 12
    elif toll_pct >= 40: return 10
    else: return 7

def get_hurdle_rate(toll_pct):
    if toll_pct >= 80: return 10.0
    elif toll_pct >= 50: return 12.0
    elif toll_pct >= 20: return 14.0
    else: return 16.0

def get_structure_label(toll_pct):
    if toll_pct >= 80: return "Highly contracted"
    elif toll_pct >= 40: return "Partly contracted"
    else: return "Merchant"

# ============================================================================
# FINANCIAL MODEL
# ============================================================================
@st.cache_data
def calculate_project(capex, opex, gearing, toll_pct, toll_level, dscr_target, debt_rate, tenor, deg_on, cod_year):
    deg_rate = 0.025
    revenue_data = get_revenue_data(cod_year)
    years = revenue_data['year']
    n_years = len(years)
    
    deg_factors = [(1 - deg_rate) ** i if deg_on else 1.0 for i in range(n_years)]
    
    low_rev = [revenue_data['low'][i] * deg_factors[i] for i in range(n_years)]
    base_rev = [revenue_data['base'][i] * deg_factors[i] for i in range(n_years)]
    high_rev = [revenue_data['high'][i] * deg_factors[i] for i in range(n_years)]
    
    toll_frac = toll_pct / 100
    
    def calc_total_rev(merchant_rev):
        return [toll_level * toll_frac + merchant_rev[i] * (1 - toll_frac) for i in range(n_years)]
    
    total_low = calc_total_rev(low_rev)
    total_base = calc_total_rev(base_rev)
    total_high = calc_total_rev(high_rev)
    
    total_capex = capex * 1000
    debt = total_capex * (gearing / 100)
    equity = total_capex - debt
    
    if equity <= 0:
        return None
    
    if tenor > 0 and debt > 0:
        annual_rate = debt_rate / 100
        pmt = debt * (annual_rate * (1 + annual_rate)**tenor) / ((1 + annual_rate)**tenor - 1)
        debt_service = [pmt if i < tenor else 0 for i in range(n_years)]
    else:
        debt_service = [0] * n_years
    
    def calc_scenario(total_rev):
        net_cf = [(total_rev[i] * 1000 - opex * 1000) for i in range(n_years)]
        equity_cf = [net_cf[i] - debt_service[i] for i in range(n_years)]
        dscr = [net_cf[i] / debt_service[i] if debt_service[i] > 0 else 99 for i in range(n_years)]
        min_dscr = min([d for d in dscr if d < 99]) if any(d < 99 for d in dscr) else 99
        
        equity_cf_with_invest = [-equity] + equity_cf
        try:
            irr = npf.irr(equity_cf_with_invest) * 100
            if np.isnan(irr) or irr < -50 or irr > 100:
                irr = -99
        except:
            irr = -99
        
        return {'min_dscr': min_dscr, 'irr': irr}
    
    low_result = calc_scenario(total_low)
    base_result = calc_scenario(total_base)
    high_result = calc_scenario(total_high)
    
    unlev_cf = [-total_capex] + [(total_base[i] * 1000 - opex * 1000) for i in range(n_years)]
    try:
        unlev_irr = npf.irr(unlev_cf) * 100
        if np.isnan(unlev_irr): unlev_irr = 0
    except:
        unlev_irr = 0
    
    return {
        'debt_feasible': low_result['min_dscr'] >= dscr_target,
        'gearing': gearing,
        'toll_pct': toll_pct,
        'toll_level': toll_level,
        'debt': debt / 1000,
        'equity': equity / 1000,
        'unlev_irr': unlev_irr,
        'dscr_target': dscr_target,
        'low_case': low_result,
        'base_case': base_result,
        'high_case': high_result,
    }

def find_max_gearing(capex, opex, toll_pct, toll_level, deg_on, cod_year):
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
    lo, hi = 0, 100
    best = 100
    for _ in range(25):
        mid = (lo + hi) / 2
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
    dscr_target = get_dscr_target(toll_pct)
    margin = get_margin_bps(toll_pct)
    debt_rate = EURIBOR + margin / 100
    tenor = get_tenor(toll_pct)
    
    lo, hi = 30, 200
    best = 200
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
    <div class="main-title">Battery Toll Calculator</div>
    <div class="brand-text">Modo Energy</div>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# MODE SELECTOR (simple row)
# ============================================================================
mode_cols = st.columns([1, 1, 3])
with mode_cols[0]:
    mode = st.selectbox("Mode", ["Manual", "Optimise"], label_visibility="collapsed")
with mode_cols[1]:
    if mode == "Optimise":
        solve_for = st.selectbox("Solve for", ["Gearing", "Toll %", "Toll Level"], label_visibility="collapsed")
    else:
        solve_for = None

# Initialize session state for solved values
if 'solved_gearing' not in st.session_state:
    st.session_state.solved_gearing = None
if 'solved_toll_pct' not in st.session_state:
    st.session_state.solved_toll_pct = None
if 'solved_toll_level' not in st.session_state:
    st.session_state.solved_toll_level = None

# ============================================================================
# THREE-COLUMN INPUT LAYOUT
# ============================================================================
col1, col2, col3 = st.columns(3, gap="small")

# Initialize variables
gearing = toll_pct = toll_level = None
capex = opex = cod_year = deg_on = None

# COLUMN 1: STRUCTURE
with col1:
    st.markdown('<div class="section-card"><div class="section-title">Structure</div>', unsafe_allow_html=True)
    
    if mode == "Optimise" and solve_for == "Gearing":
        # Gearing will be solved - show frozen display with last solved value
        solved_val = st.session_state.solved_gearing
        display_val = f"{solved_val:.0f}%" if solved_val else "--"
        st.markdown(f'<div class="solved-value"><div class="solved-label">Gearing % (solving)</div><div class="solved-number">{display_val}</div></div>', unsafe_allow_html=True)
        toll_pct = st.slider("Toll Coverage %", 0, 100, 65)
        toll_level = st.slider("Toll Level (€k/MW/yr)", 70, 130, 100)
        gearing = None
    elif mode == "Optimise" and solve_for == "Toll %":
        gearing = st.slider("Gearing %", 10, 85, 65)
        # Check gearing warning
        max_gear = get_max_gearing(50)
        if gearing > max_gear:
            st.markdown(f'<div class="gearing-warning">May require higher toll coverage</div>', unsafe_allow_html=True)
        # Toll % will be solved
        solved_val = st.session_state.solved_toll_pct
        display_val = f"{solved_val:.0f}%" if solved_val else "--"
        st.markdown(f'<div class="solved-value"><div class="solved-label">Toll Coverage % (solving)</div><div class="solved-number">{display_val}</div></div>', unsafe_allow_html=True)
        toll_level = st.slider("Toll Level (€k/MW/yr)", 70, 130, 100)
        toll_pct = None
    elif mode == "Optimise" and solve_for == "Toll Level":
        gearing = st.slider("Gearing %", 10, 85, 65)
        toll_pct = st.slider("Toll Coverage %", 0, 100, 65)
        # Check gearing warning
        max_gear = get_max_gearing(toll_pct)
        if gearing > max_gear:
            st.markdown(f'<div class="gearing-warning">Exceeds {max_gear}% max for this toll</div>', unsafe_allow_html=True)
        # Toll level will be solved
        solved_val = st.session_state.solved_toll_level
        display_val = f"{solved_val:.0f}k" if solved_val else "--"
        st.markdown(f'<div class="solved-value"><div class="solved-label">Toll Level (solving)</div><div class="solved-number">{display_val}</div></div>', unsafe_allow_html=True)
        toll_level = None
    else:  # Manual mode
        gearing = st.slider("Gearing %", 10, 85, 65)
        toll_pct = st.slider("Toll Coverage %", 0, 100, 65)
        # Check gearing warning
        max_gear = get_max_gearing(toll_pct)
        if gearing > max_gear:
            st.markdown(f'<div class="gearing-warning">Exceeds {max_gear}% max for this toll</div>', unsafe_allow_html=True)
        toll_level = st.slider("Toll Level (€k/MW/yr)", 70, 130, 100)
    
    st.markdown('</div>', unsafe_allow_html=True)

# COLUMN 2: PROJECT
with col2:
    st.markdown('<div class="section-card"><div class="section-title">Project</div>', unsafe_allow_html=True)
    
    capex = st.number_input("CapEx (€k/MW)", 300, 1000, 600, 25)
    opex = st.number_input("Opex (€k/yr)", 0, 30, 7, 1)
    cod_year = st.selectbox("COD Year", [2026, 2027, 2028], index=1)
    deg_on = st.checkbox("Degradation 2.5%/yr", True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# COLUMN 3: FINANCING TERMS (auto-calculated)
with col3:
    st.markdown('<div class="section-card"><div class="section-title">Financing Terms</div>', unsafe_allow_html=True)
    
    # Use toll_pct for terms calculation (default 65 if not set)
    display_toll_pct = toll_pct if toll_pct is not None else 65
    
    dscr_target = get_dscr_target(display_toll_pct)
    margin = get_margin_bps(display_toll_pct)
    debt_rate = EURIBOR + margin / 100
    tenor = get_tenor(display_toll_pct)
    max_gear = get_max_gearing(display_toll_pct)
    structure_label = get_structure_label(display_toll_pct)
    
    terms_html = f"""
    <div class="terms-grid">
        <div class="term-item">
            <div class="term-value">{dscr_target:.2f}x</div>
            <div class="term-label">DSCR</div>
        </div>
        <div class="term-item">
            <div class="term-value">{debt_rate:.1f}%</div>
            <div class="term-label">Rate</div>
        </div>
        <div class="term-item">
            <div class="term-value">{tenor}yr</div>
            <div class="term-label">Tenor</div>
        </div>
        <div class="term-item">
            <div class="term-value">{max_gear}%</div>
            <div class="term-label">Max Gear</div>
        </div>
    </div>
    """
    st.markdown(terms_html, unsafe_allow_html=True)
    st.caption(f"{structure_label}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# SOLVE (if optimising)
# ============================================================================
if mode == "Optimise":
    if solve_for == "Gearing":
        gearing = find_max_gearing(capex, opex, toll_pct, toll_level, deg_on, cod_year)
        st.session_state.solved_gearing = gearing
    elif solve_for == "Toll %":
        toll_pct = find_min_toll_pct(capex, opex, gearing, toll_level, deg_on, cod_year)
        st.session_state.solved_toll_pct = toll_pct
    elif solve_for == "Toll Level":
        toll_level = find_min_toll_level(capex, opex, gearing, toll_pct, deg_on, cod_year)
        st.session_state.solved_toll_level = toll_level

# Recalculate financing terms with solved values
final_toll_pct = toll_pct if toll_pct is not None else 65
final_dscr_target = get_dscr_target(final_toll_pct)
final_margin = get_margin_bps(final_toll_pct)
final_debt_rate = EURIBOR + final_margin / 100
final_tenor = get_tenor(final_toll_pct)

# Calculate results
result = calculate_project(capex, opex, gearing, final_toll_pct, toll_level, final_dscr_target, final_debt_rate, final_tenor, deg_on, cod_year)

# ============================================================================
# RESULTS SECTION
# ============================================================================
st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

if result:
    # Main results in two columns
    res_col1, res_col2 = st.columns(2, gap="small")
    
    hurdle = get_hurdle_rate(final_toll_pct)
    base_irr = result['base_case']['irr']
    low_irr = result['low_case']['irr']
    high_irr = result['high_case']['irr']
    min_dscr = result['low_case']['min_dscr']
    
    with res_col1:
        # Debt Feasibility
        dscr_margin = min_dscr - final_dscr_target
        if result['debt_feasible']:
            debt_class = "result-pass"
            debt_badge = "FEASIBLE"
        else:
            debt_class = "result-fail"
            debt_badge = "NOT FEASIBLE"
        
        dscr_sign = "+" if dscr_margin >= 0 else ""
        st.markdown(f"""
        <div class="{debt_class}">
            <div class="result-header">
                <div>
                    <div class="result-label">Debt (Low Case DSCR)</div>
                    <div class="result-value">{min_dscr:.2f}x</div>
                    <div class="result-detail">vs {final_dscr_target:.2f}x ({dscr_sign}{dscr_margin:.2f}x)</div>
                </div>
                <div class="result-badge">{debt_badge}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Low/High case
        def get_class(irr, h):
            if irr >= h: return "green"
            elif irr >= h - 3: return "amber"
            else: return "red"
        
        low_class = get_class(low_irr, hurdle)
        high_class = get_class(high_irr, hurdle)
        
        st.markdown(f"""
        <div class="scenario-row">
            <div class="scenario-box {low_class}">
                <div class="scenario-label">Low Case</div>
                <div class="scenario-value {low_class}">{low_irr:.1f}%</div>
            </div>
            <div class="scenario-box {high_class}">
                <div class="scenario-label">High Case</div>
                <div class="scenario-value {high_class}">{high_irr:.1f}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with res_col2:
        # Equity IRR
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
        st.markdown(f"""
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
        """, unsafe_allow_html=True)
        
        # Financial summary - include solved value if optimising
        if mode == "Optimise":
            if solve_for == "Gearing":
                solved_label = f"Gear: {gearing:.0f}%"
            elif solve_for == "Toll %":
                solved_label = f"Toll: {toll_pct:.0f}%"
            else:
                solved_label = f"Toll: {toll_level:.0f}k"
            
            st.markdown(f"""
            <div class="metrics-grid">
                <div class="metric-box" style="background: #dbeafe; border-color: #3b82f6;">
                    <div class="metric-value" style="color: #1d4ed8;">{solved_label.split(": ")[1]}</div>
                    <div class="metric-label" style="color: #1d4ed8;">Solved</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{result['unlev_irr']:.1f}%</div>
                    <div class="metric-label">Unlev</div>
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
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="metrics-grid">
                <div class="metric-box">
                    <div class="metric-value">{result['unlev_irr']:.1f}%</div>
                    <div class="metric-label">Unlev</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{result['gearing']:.0f}%</div>
                    <div class="metric-label">Gear</div>
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
            """, unsafe_allow_html=True)

else:
    st.error("Unable to calculate. Check inputs.")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown('<div class="footer">1.5 cycle · 2hr duration · German BESS · Modo forecasts 2026-2040 · Educational only</div>', unsafe_allow_html=True)
