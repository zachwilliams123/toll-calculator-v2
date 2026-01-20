"""
Battery Toll Calculator v3.0
Modo Energy - German BESS Educational Tool

Redesign based on feedback:
- 2 modes: Manual + Optimise (dropdown)
- Structure inputs at top
- Separate Equity Returns vs Debt Feasibility
- Risk-adjusted hurdle rate
- Auto-adjusting financing terms
- Removed bankability map
- Low Case / High Case naming
"""

import streamlit as st
import pandas as pd
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
    .block-container {padding: 1.25rem 2rem 2rem 2rem; max-width: 1100px;}
    
    .main-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.1rem;
        letter-spacing: -0.02em;
    }
    .subtitle {
        font-size: 0.8rem;
        color: #64748b;
        margin-bottom: 0.5rem;
    }
    .brand-text {
        font-size: 0.8rem;
        color: #0d9488;
        font-weight: 600;
    }
    
    .section-card {
        background: #ffffff;
        border-radius: 10px;
        padding: 1rem 1.15rem;
        border: 1px solid #e2e8f0;
        margin-bottom: 0.75rem;
    }
    .section-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: #334155;
        margin-bottom: 0.7rem;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid #f1f5f9;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    
    /* Result cards */
    .result-pass {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        color: white;
        margin-bottom: 0.6rem;
    }
    .result-warn {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        color: white;
        margin-bottom: 0.6rem;
    }
    .result-fail {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        color: white;
        margin-bottom: 0.6rem;
    }
    .result-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .result-title {
        font-size: 0.7rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .result-main {
        font-size: 1.8rem;
        font-weight: 700;
        line-height: 1.1;
    }
    .result-sub {
        font-size: 0.8rem;
        opacity: 0.9;
        margin-top: 0.2rem;
    }
    .result-badge {
        font-size: 0.65rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 6px;
        background: rgba(255,255,255,0.2);
    }
    
    /* Scenario rows */
    .scenario-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }
    .scenario-box {
        border-radius: 8px;
        padding: 0.6rem 0.8rem;
        border: 1px solid #e2e8f0;
    }
    .scenario-box.green {
        background: #ecfdf5;
        border-color: #a7f3d0;
    }
    .scenario-box.amber {
        background: #fffbeb;
        border-color: #fde68a;
    }
    .scenario-box.red {
        background: #fef2f2;
        border-color: #fecaca;
    }
    .scenario-label {
        font-size: 0.7rem;
        color: #64748b;
    }
    .scenario-value {
        font-size: 1.05rem;
        font-weight: 600;
    }
    .scenario-value.green { color: #059669; }
    .scenario-value.amber { color: #d97706; }
    .scenario-value.red { color: #dc2626; }
    
    /* Financing terms */
    .terms-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.5rem;
    }
    .term-box {
        background: #f8fafc;
        border-radius: 6px;
        padding: 0.5rem 0.7rem;
        text-align: center;
    }
    .term-value {
        font-size: 0.95rem;
        font-weight: 600;
        color: #1e293b;
    }
    .term-label {
        font-size: 0.6rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    
    /* Summary metrics */
    .metrics-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.5rem;
        margin-bottom: 0.6rem;
    }
    .metric-box {
        background: #f8fafc;
        border-radius: 8px;
        padding: 0.55rem 0.7rem;
        text-align: center;
        border: 1px solid #e2e8f0;
    }
    .metric-value {
        font-size: 1rem;
        font-weight: 700;
        color: #1e293b;
    }
    .metric-label {
        font-size: 0.6rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.02em;
    }
    
    /* Solving indicator */
    .solving-box {
        background: #eff6ff;
        border: 2px solid #3b82f6;
        border-radius: 8px;
        padding: 0.5rem 0.8rem;
        margin-bottom: 0.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .solving-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: #1e40af;
    }
    .solving-badge {
        background: #3b82f6;
        color: white;
        font-size: 0.55rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
        letter-spacing: 0.04em;
    }
    
    /* Sliders */
    div[data-testid="stSlider"] {
        padding-top: 0 !important;
        padding-bottom: 0.4rem !important;
    }
    div[data-testid="stSlider"] label p {
        font-size: 0.75rem !important;
        color: #475569 !important;
        margin-bottom: 0.1rem !important;
    }
    div[data-testid="stNumberInput"] label p {
        font-size: 0.75rem !important;
        color: #475569 !important;
    }
    div[data-testid="stSelectbox"] label p {
        font-size: 0.75rem !important;
        color: #475569 !important;
    }
    div[data-testid="stCheckbox"] label p {
        font-size: 0.75rem !important;
        color: #475569 !important;
    }
    
    .footer {
        text-align: center;
        font-size: 0.65rem;
        color: #94a3b8;
        margin-top: 0.75rem;
        padding-top: 0.6rem;
        border-top: 1px solid #f1f5f9;
    }
    
    .leverage-note {
        background: #fefce8;
        border-radius: 6px;
        padding: 0.5rem 0.7rem;
        border: 1px solid #fef08a;
        font-size: 0.75rem;
        color: #854d0e;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA & CONSTANTS
# ============================================================================
REVENUE_DATA = {
    'year': list(range(2026, 2036)),
    'p10': [85, 78, 72, 68, 65, 63, 61, 59, 58, 57],   # Low case
    'p50': [115, 108, 102, 97, 93, 90, 87, 85, 83, 81], # Base case
    'p90': [155, 145, 138, 132, 127, 123, 119, 116, 113, 110]  # High case
}

# Risk-adjusted hurdle rates based on toll coverage
def get_hurdle_rate(toll_pct):
    """Return equity hurdle rate based on contracted revenue percentage"""
    if toll_pct >= 80:
        return 10.0  # Low risk - highly contracted
    elif toll_pct >= 50:
        return 12.0  # Medium risk - partial toll
    elif toll_pct >= 20:
        return 14.0  # Higher risk - mostly merchant
    else:
        return 16.0  # Full merchant - highest risk

def get_risk_label(toll_pct):
    """Return risk profile label"""
    if toll_pct >= 80:
        return "Low risk"
    elif toll_pct >= 50:
        return "Medium risk"
    elif toll_pct >= 20:
        return "Higher risk"
    else:
        return "Merchant"

# Auto financing terms based on ABN AMRO term sheet
def get_financing_terms(toll_pct):
    """Return max gearing, DSCR target, and margin based on toll coverage"""
    if toll_pct >= 80:
        return {'max_gearing': 85, 'dscr': 1.80, 'margin': 200, 'label': 'Highly contracted'}
    elif toll_pct >= 40:
        return {'max_gearing': 75, 'dscr': 1.90, 'margin': 250, 'label': 'Partly contracted'}
    else:
        return {'max_gearing': 50, 'dscr': 2.50, 'margin': 310, 'label': 'Merchant'}

EURIBOR = 3.5  # Base rate assumption

# ============================================================================
# FINANCIAL MODEL
# ============================================================================
@st.cache_data
def calculate_project(capex, opex, gearing, toll_pct, toll_level, dscr_target, debt_rate, tenor, deg_on, deg_rate):
    years = REVENUE_DATA['year']
    n_years = len(years)
    
    deg_factors = [(1 - deg_rate) ** i if deg_on else 1.0 for i in range(n_years)]
    
    p10_rev = [REVENUE_DATA['p10'][i] * deg_factors[i] for i in range(n_years)]
    p50_rev = [REVENUE_DATA['p50'][i] * deg_factors[i] for i in range(n_years)]
    p90_rev = [REVENUE_DATA['p90'][i] * deg_factors[i] for i in range(n_years)]
    
    toll_frac = toll_pct / 100
    
    def calc_total_rev(merchant_rev):
        return [toll_level * toll_frac + merchant_rev[i] * (1 - toll_frac) for i in range(n_years)]
    
    total_p10 = calc_total_rev(p10_rev)
    total_p50 = calc_total_rev(p50_rev)
    total_p90 = calc_total_rev(p90_rev)
    
    total_capex = capex * 1000
    debt = total_capex * (gearing / 100)
    equity = total_capex - debt
    
    # Sculpted debt service
    net_cf_p50 = [total_p50[i] * 1000 - opex * 1000 for i in range(n_years)]
    total_debt_capacity = sum([cf / dscr_target for cf in net_cf_p50[:tenor]])
    
    if total_debt_capacity <= 0 or equity <= 0:
        return None
    
    scale = min(1.0, debt / total_debt_capacity)
    debt_service = [(net_cf_p50[i] / dscr_target) * scale if i < tenor else 0 for i in range(n_years)]
    
    def calc_scenario(total_rev):
        net_cf = [(total_rev[i] * 1000 - opex * 1000) for i in range(n_years)]
        equity_cf = [net_cf[i] - debt_service[i] for i in range(n_years)]
        
        dscr = [net_cf[i] / debt_service[i] if debt_service[i] > 0 else 99 for i in range(n_years)]
        min_dscr = min([d for d in dscr if d < 99]) if any(d < 99 for d in dscr) else 99
        
        equity_cf_with_invest = [-equity] + equity_cf
        irr = npf.irr(equity_cf_with_invest) * 100 if equity > 0 else 0
        
        return {
            'net_cf': net_cf,
            'equity_cf': equity_cf,
            'dscr': dscr,
            'min_dscr': min_dscr,
            'irr': irr if not np.isnan(irr) else -99
        }
    
    p10_result = calc_scenario(total_p10)
    p50_result = calc_scenario(total_p50)
    p90_result = calc_scenario(total_p90)
    
    unlev_cf = [-total_capex] + [(total_p50[i] * 1000 - opex * 1000) for i in range(n_years)]
    unlev_irr = npf.irr(unlev_cf) * 100
    
    hurdle = get_hurdle_rate(toll_pct)
    debt_feasible = p10_result['min_dscr'] >= dscr_target
    
    return {
        'debt_feasible': debt_feasible,
        'gearing': gearing,
        'toll_pct': toll_pct,
        'toll_level': toll_level,
        'debt': debt / 1000,
        'equity': equity / 1000,
        'debt_service': sum(debt_service[:tenor]) / tenor / 1000 if tenor > 0 else 0,
        'unlev_irr': unlev_irr if not np.isnan(unlev_irr) else 0,
        'min_dscr': p10_result['min_dscr'],
        'dscr_target': dscr_target,
        'hurdle': hurdle,
        'low_case': {'irr': p10_result['irr'], 'min_dscr': p10_result['min_dscr']},
        'base_case': {'irr': p50_result['irr'], 'min_dscr': p50_result['min_dscr']},
        'high_case': {'irr': p90_result['irr'], 'min_dscr': p90_result['min_dscr']},
    }

@st.cache_data
def find_max_gearing(capex, opex, toll_pct, toll_level, dscr_target, debt_rate, tenor, deg_on, deg_rate):
    lo, hi = 0, 85
    best = 0
    for _ in range(20):
        mid = (lo + hi) / 2
        result = calculate_project(capex, opex, mid, toll_pct, toll_level, dscr_target, debt_rate, tenor, deg_on, deg_rate)
        if result and result['debt_feasible']:
            best = mid
            lo = mid
        else:
            hi = mid
    return round(best, 1)

@st.cache_data
def find_min_toll_pct(capex, opex, gearing, toll_level, dscr_target, debt_rate, tenor, deg_on, deg_rate):
    lo, hi = 0, 100
    best = 100
    for _ in range(20):
        mid = (lo + hi) / 2
        result = calculate_project(capex, opex, gearing, mid, toll_level, dscr_target, debt_rate, tenor, deg_on, deg_rate)
        if result and result['debt_feasible']:
            best = mid
            hi = mid
        else:
            lo = mid
    return round(best, 1)

@st.cache_data
def find_min_toll_level(capex, opex, gearing, toll_pct, dscr_target, debt_rate, tenor, deg_on, deg_rate):
    lo, hi = 50, 200
    best = 200
    for _ in range(20):
        mid = (lo + hi) / 2
        result = calculate_project(capex, opex, gearing, toll_pct, mid, dscr_target, debt_rate, tenor, deg_on, deg_rate)
        if result and result['debt_feasible']:
            best = mid
            hi = mid
        else:
            lo = mid
    return round(best, 1)

# ============================================================================
# HEADER
# ============================================================================
header_cols = st.columns([4, 1])
with header_cols[0]:
    st.markdown("<div class='main-title'>Battery Toll Calculator</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>German BESS · Educational tool</div>", unsafe_allow_html=True)
with header_cols[1]:
    st.markdown("<div class='brand-text'>Modo Energy</div>", unsafe_allow_html=True)

# ============================================================================
# MODE SELECTOR
# ============================================================================
mode_cols = st.columns([1, 2, 3])
with mode_cols[0]:
    mode = st.selectbox("Mode", ["Manual", "Optimise"], label_visibility="collapsed")
with mode_cols[1]:
    if mode == "Optimise":
        solve_for = st.selectbox("Solve for", ["Max Gearing", "Min Toll %", "Min Toll €"], label_visibility="collapsed")
    else:
        solve_for = None

st.markdown("<div style='height: 0.3rem;'></div>", unsafe_allow_html=True)

# ============================================================================
# MAIN LAYOUT
# ============================================================================
left_col, right_col = st.columns([1, 1.1], gap="medium")

# ============================================================================
# LEFT COLUMN - INPUTS
# ============================================================================
with left_col:
    # Structure section (main inputs at top)
    st.markdown("<div class='section-card'><div class='section-title'>Structure</div>", unsafe_allow_html=True)
    
    if mode == "Optimise" and solve_for == "Max Gearing":
        st.markdown("<div class='solving-box'><span class='solving-label'>Gearing %</span><span class='solving-badge'>SOLVING →</span></div>", unsafe_allow_html=True)
        toll_pct = st.slider("Toll Coverage %", 0, 100, 65, key="toll_pct")
        toll_level = st.slider("Toll Level (€k/MW/yr)", 50, 150, 95, key="toll_level")
    elif mode == "Optimise" and solve_for == "Min Toll %":
        gearing = st.slider("Gearing %", 10, 85, 55, key="gearing")
        st.markdown("<div class='solving-box'><span class='solving-label'>Toll Coverage %</span><span class='solving-badge'>SOLVING →</span></div>", unsafe_allow_html=True)
        toll_level = st.slider("Toll Level (€k/MW/yr)", 50, 150, 95, key="toll_level")
    elif mode == "Optimise" and solve_for == "Min Toll €":
        gearing = st.slider("Gearing %", 10, 85, 55, key="gearing")
        toll_pct = st.slider("Toll Coverage %", 0, 100, 65, key="toll_pct")
        st.markdown("<div class='solving-box'><span class='solving-label'>Toll Level (€k/MW/yr)</span><span class='solving-badge'>SOLVING →</span></div>", unsafe_allow_html=True)
    else:
        gearing = st.slider("Gearing %", 10, 85, 55, key="gearing")
        toll_pct = st.slider("Toll Coverage %", 0, 100, 65, key="toll_pct")
        toll_level = st.slider("Toll Level (€k/MW/yr)", 50, 150, 95, key="toll_level")
    
    # Show toll as % of P50
    year1_p50 = REVENUE_DATA['p50'][0]
    if 'toll_level' in dir():
        toll_pct_of_p50 = (toll_level / year1_p50) * 100
        st.caption(f"Toll = {toll_pct_of_p50:.0f}% of Year 1 P50 (€{year1_p50}k)")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Project section
    st.markdown("<div class='section-card'><div class='section-title'>Project</div>", unsafe_allow_html=True)
    proj_cols = st.columns(2)
    with proj_cols[0]:
        capex = st.number_input("CapEx (€k/MW)", min_value=300, max_value=1000, value=600, step=25)
    with proj_cols[1]:
        opex = st.number_input("Opex (€k/yr)", min_value=0, max_value=30, value=7, step=1)
    
    deg_on = st.checkbox("Capacity degradation (2.5%/yr)", value=True)
    deg_rate = 0.025
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Financing terms (auto or manual)
    st.markdown("<div class='section-card'><div class='section-title'>Financing Terms</div>", unsafe_allow_html=True)
    
    # Get auto terms based on toll %
    if 'toll_pct' in dir():
        auto_terms = get_financing_terms(toll_pct)
    else:
        auto_terms = get_financing_terms(65)
    
    override = st.checkbox("Override default terms", value=False)
    
    if override:
        fin_cols = st.columns(3)
        with fin_cols[0]:
            dscr_target = st.number_input("DSCR Target", min_value=1.0, max_value=3.0, value=auto_terms['dscr'], step=0.05, format="%.2f")
        with fin_cols[1]:
            margin = st.number_input("Margin (bps)", min_value=100, max_value=500, value=auto_terms['margin'], step=25)
        with fin_cols[2]:
            tenor = st.number_input("Tenor (yrs)", min_value=5, max_value=15, value=10, step=1)
        debt_rate = EURIBOR + (margin / 100)
    else:
        dscr_target = auto_terms['dscr']
        margin = auto_terms['margin']
        debt_rate = EURIBOR + (margin / 100)
        tenor = 10
        
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
        st.caption(f"Based on {auto_terms['label'].lower()} revenue stack ({toll_pct}% toll)")
    
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================================
# SOLVE (if optimising)
# ============================================================================
if mode == "Optimise":
    if solve_for == "Max Gearing":
        gearing = find_max_gearing(capex, opex, toll_pct, toll_level, dscr_target, debt_rate, tenor, deg_on, deg_rate)
    elif solve_for == "Min Toll %":
        toll_pct = find_min_toll_pct(capex, opex, gearing, toll_level, dscr_target, debt_rate, tenor, deg_on, deg_rate)
    elif solve_for == "Min Toll €":
        toll_level = find_min_toll_level(capex, opex, gearing, toll_pct, dscr_target, debt_rate, tenor, deg_on, deg_rate)

# Calculate results
result = calculate_project(capex, opex, gearing, toll_pct, toll_level, dscr_target, debt_rate, tenor, deg_on, deg_rate)

# ============================================================================
# RIGHT COLUMN - RESULTS
# ============================================================================
with right_col:
    if result:
        hurdle = result['hurdle']
        base_irr = result['base_case']['irr']
        low_irr = result['low_case']['irr']
        high_irr = result['high_case']['irr']
        
        # Determine equity result status
        irr_vs_hurdle = base_irr - hurdle
        if irr_vs_hurdle >= 0:
            equity_class = "result-pass"
            equity_badge = "✓ MEETS HURDLE"
        elif irr_vs_hurdle >= -3:
            equity_class = "result-warn"
            equity_badge = "~ NEAR HURDLE"
        else:
            equity_class = "result-fail"
            equity_badge = "✗ BELOW HURDLE"
        
        # EQUITY RETURNS card
        risk_label = get_risk_label(toll_pct)
        sign = "+" if irr_vs_hurdle >= 0 else ""
        
        equity_html = f"""
        <div class="{equity_class}">
            <div class="result-header">
                <div>
                    <div class="result-title">Equity Returns (Base Case)</div>
                    <div class="result-main">{base_irr:.1f}%</div>
                    <div class="result-sub">vs {hurdle:.0f}% hurdle ({risk_label}) → {sign}{irr_vs_hurdle:.1f}%</div>
                </div>
                <div class="result-badge">{equity_badge}</div>
            </div>
        </div>
        """
        st.markdown(equity_html, unsafe_allow_html=True)
        
        # Scenario boxes (Low Case / High Case)
        def get_scenario_class(irr, hurdle):
            if irr >= hurdle:
                return "green"
            elif irr >= hurdle - 3:
                return "amber"
            else:
                return "red"
        
        low_class = get_scenario_class(low_irr, hurdle)
        high_class = get_scenario_class(high_irr, hurdle)
        
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
        
        st.markdown("<div style='height: 0.4rem;'></div>", unsafe_allow_html=True)
        
        # DEBT FEASIBILITY card
        min_dscr = result['min_dscr']
        dscr_pass = result['debt_feasible']
        
        if dscr_pass:
            debt_class = "result-pass"
            debt_badge = "✓ FEASIBLE"
        else:
            debt_class = "result-fail"
            debt_badge = "✗ NOT FEASIBLE"
        
        dscr_margin = min_dscr - dscr_target
        dscr_sign = "+" if dscr_margin >= 0 else ""
        
        debt_html = f"""
        <div class="{debt_class}">
            <div class="result-header">
                <div>
                    <div class="result-title">Debt Feasibility (Min DSCR)</div>
                    <div class="result-main">{min_dscr:.2f}x</div>
                    <div class="result-sub">vs {dscr_target:.2f}x target → {dscr_sign}{dscr_margin:.2f}x</div>
                </div>
                <div class="result-badge">{debt_badge}</div>
            </div>
        </div>
        """
        st.markdown(debt_html, unsafe_allow_html=True)
        
        # Summary metrics
        metrics_html = f"""
        <div class="metrics-row">
            <div class="metric-box">
                <div class="metric-value">€{result['debt']:.0f}k</div>
                <div class="metric-label">Debt</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">€{result['equity']:.0f}k</div>
                <div class="metric-label">Equity</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">€{result['debt_service']:.0f}k/yr</div>
                <div class="metric-label">Debt Service</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{result['unlev_irr']:.1f}%</div>
                <div class="metric-label">Unlev IRR</div>
            </div>
        </div>
        """
        st.markdown(metrics_html, unsafe_allow_html=True)
        
        # Leverage effect note
        lev_effect = base_irr - result['unlev_irr']
        lev_sign = "+" if lev_effect >= 0 else ""
        st.markdown(f"<div class='leverage-note'>Leverage effect: {result['unlev_irr']:.1f}% unlevered → {base_irr:.1f}% levered ({lev_sign}{lev_effect:.1f}%)</div>", unsafe_allow_html=True)
        
        # Show solved value if optimising
        if mode == "Optimise":
            st.markdown("<div style='height: 0.4rem;'></div>", unsafe_allow_html=True)
            if solve_for == "Max Gearing":
                st.info(f"**Solved:** Maximum gearing = **{gearing:.1f}%** at {toll_pct}% toll coverage")
            elif solve_for == "Min Toll %":
                st.info(f"**Solved:** Minimum toll coverage = **{toll_pct:.1f}%** at {gearing:.0f}% gearing")
            elif solve_for == "Min Toll €":
                st.info(f"**Solved:** Minimum toll level = **€{toll_level:.0f}k** at {gearing:.0f}% gearing")
    else:
        st.error("Unable to calculate. Check inputs.")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("<div class='footer'>1.5 cycle · 2hr duration · German BESS Forecasts 2026–2035 · Educational purposes only · Not financial advice</div>", unsafe_allow_html=True)
