"""
Battery Toll Calculator v6.0
Modo Energy - German BESS Educational Tool

Simplified version:
- Fixed DSCR tiers (not formula)
- Optimiser finds max equity IRR at given toll level
- Gearing range: 40-80%
- Clean 2-column layout
"""

import streamlit as st
import numpy as np
import numpy_financial as npf

st.set_page_config(page_title="Battery Toll Calculator | Modo Energy", layout="wide", initial_sidebar_state="collapsed")

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
    .block-container {padding: 1rem 1.5rem 1rem 1.5rem; max-width: 950px;}
    
    .header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #e2e8f0;
    }
    .main-title { font-size: 1.25rem; font-weight: 700; color: #1a1a2e; }
    .brand-text { font-size: 0.75rem; color: #1a1a2e; font-weight: 600; }
    
    .section-card {
        background: #fff;
        border-radius: 8px;
        padding: 0.7rem 0.9rem;
        border: 1px solid #e2e8f0;
        margin-bottom: 0.5rem;
    }
    .section-title {
        font-size: 0.6rem;
        font-weight: 600;
        color: #64748b;
        margin-bottom: 0.4rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .result-pass {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        border-radius: 8px;
        padding: 0.65rem 0.85rem;
        color: white;
        margin-bottom: 0.4rem;
    }
    .result-warn {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        border-radius: 8px;
        padding: 0.65rem 0.85rem;
        color: white;
        margin-bottom: 0.4rem;
    }
    .result-fail {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        border-radius: 8px;
        padding: 0.65rem 0.85rem;
        color: white;
        margin-bottom: 0.4rem;
    }
    .result-header { display: flex; justify-content: space-between; align-items: center; }
    .result-label { font-size: 0.55rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 0.03em; }
    .result-value { font-size: 1.3rem; font-weight: 700; line-height: 1.1; }
    .result-detail { font-size: 0.65rem; opacity: 0.9; }
    .result-badge { font-size: 0.5rem; font-weight: 600; padding: 3px 6px; border-radius: 4px; background: rgba(255,255,255,0.2); }
    
    .scenario-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.35rem; margin-bottom: 0.35rem; }
    .scenario-box { border-radius: 6px; padding: 0.4rem 0.5rem; text-align: center; }
    .scenario-box.green { background: #ecfdf5; border: 1px solid #a7f3d0; }
    .scenario-box.amber { background: #fffbeb; border: 1px solid #fde68a; }
    .scenario-box.red { background: #fef2f2; border: 1px solid #fecaca; }
    .scenario-label { font-size: 0.55rem; color: #64748b; }
    .scenario-value { font-size: 0.9rem; font-weight: 600; }
    .scenario-value.green { color: #059669; }
    .scenario-value.amber { color: #d97706; }
    .scenario-value.red { color: #dc2626; }
    
    .metrics-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.3rem; }
    .metric-box { background: #f8fafc; border-radius: 5px; padding: 0.35rem 0.4rem; text-align: center; border: 1px solid #e2e8f0; }
    .metric-value { font-size: 0.8rem; font-weight: 700; color: #1e293b; }
    .metric-label { font-size: 0.45rem; color: #64748b; text-transform: uppercase; }
    
    .terms-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.3rem; }
    .term-item { background: #f8fafc; border-radius: 5px; padding: 0.35rem 0.4rem; text-align: center; }
    .term-value { font-size: 0.8rem; font-weight: 600; color: #1e293b; }
    .term-label { font-size: 0.45rem; color: #64748b; text-transform: uppercase; }
    
    .gearing-warn { background: #fef3c7; border-left: 3px solid #f59e0b; padding: 0.25rem 0.4rem; margin-top: 0.15rem; font-size: 0.6rem; color: #92400e; border-radius: 0 4px 4px 0; }
    
    .footer { text-align: center; font-size: 0.5rem; color: #94a3b8; margin-top: 0.4rem; padding-top: 0.3rem; border-top: 1px solid #f1f5f9; }
    
    div[data-testid="stSlider"] { padding-top: 0 !important; padding-bottom: 0.2rem !important; }
    div[data-testid="stSlider"] label p { font-size: 0.65rem !important; color: #475569 !important; }
    div[data-testid="stNumberInput"] label p { font-size: 0.65rem !important; color: #475569 !important; }
    div[data-testid="stSelectbox"] label p { font-size: 0.65rem !important; color: #475569 !important; }
    div[data-testid="stCheckbox"] label p { font-size: 0.6rem !important; color: #475569 !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA
# ============================================================================
REVENUE_DATA = {
    'year': list(range(2026, 2041)),
    'low':  [142, 94, 76, 72, 69, 68, 68, 70, 67, 67, 69, 72, 73, 79, 75],
    'base': [240, 155, 129, 124, 119, 117, 118, 118, 117, 114, 115, 119, 119, 118, 114],
    'high': [319, 205, 168, 163, 158, 154, 157, 155, 151, 154, 154, 156, 150, 147, 135]
}

def get_revenue(cod_year):
    idx = cod_year - 2026
    return {k: REVENUE_DATA[k][idx:idx+10] for k in ['year', 'low', 'base', 'high']}

EURIBOR = 2.25

# ============================================================================
# SIMPLE FINANCING TIERS
# ============================================================================
def get_dscr(toll_pct):
    """Fixed DSCR tiers"""
    if toll_pct >= 80: return 1.20
    elif toll_pct >= 40: return 1.90
    else: return 2.50

def get_max_gearing(toll_pct):
    if toll_pct >= 80: return 80
    elif toll_pct >= 40: return 75
    else: return 50

def get_margin(toll_pct):
    if toll_pct >= 80: return 200
    elif toll_pct >= 40: return 250
    else: return 310

def get_tenor(toll_pct):
    if toll_pct >= 80: return 12
    elif toll_pct >= 40: return 10
    else: return 7

def get_hurdle(toll_pct):
    if toll_pct >= 80: return 10.0
    elif toll_pct >= 50: return 12.0
    elif toll_pct >= 20: return 14.0
    else: return 16.0

def get_tier_label(toll_pct):
    if toll_pct >= 80: return "Contracted"
    elif toll_pct >= 40: return "Partial"
    else: return "Merchant"

# ============================================================================
# FINANCIAL MODEL
# ============================================================================
@st.cache_data
def calculate(capex, opex, gearing, toll_pct, toll_level, cod_year, deg_on):
    rev = get_revenue(cod_year)
    n = len(rev['year'])
    deg = 0.025 if deg_on else 0
    
    # Degradation factors
    df = [(1 - deg) ** i for i in range(n)]
    
    # Revenue scenarios
    toll_frac = toll_pct / 100
    low = [toll_level * toll_frac + rev['low'][i] * df[i] * (1 - toll_frac) for i in range(n)]
    base = [toll_level * toll_frac + rev['base'][i] * df[i] * (1 - toll_frac) for i in range(n)]
    high = [toll_level * toll_frac + rev['high'][i] * df[i] * (1 - toll_frac) for i in range(n)]
    
    # Capital
    total_capex = capex * 1000
    debt = total_capex * gearing / 100
    equity = total_capex - debt
    if equity <= 0: return None
    
    # Debt service
    dscr_target = get_dscr(toll_pct)
    rate = (EURIBOR + get_margin(toll_pct) / 100) / 100
    tenor = get_tenor(toll_pct)
    pmt = debt * (rate * (1 + rate)**tenor) / ((1 + rate)**tenor - 1) if debt > 0 else 0
    ds = [pmt if i < tenor else 0 for i in range(n)]
    
    def calc(rev_scenario):
        ncf = [rev_scenario[i] * 1000 - opex * 1000 for i in range(n)]
        ecf = [ncf[i] - ds[i] for i in range(n)]
        dscr_vals = [ncf[i] / ds[i] if ds[i] > 0 else 99 for i in range(n)]
        min_dscr = min([d for d in dscr_vals if d < 99]) if any(d < 99 for d in dscr_vals) else 99
        try:
            irr = npf.irr([-equity] + ecf) * 100
            if np.isnan(irr) or irr < -50 or irr > 100: irr = -99
        except: irr = -99
        return {'min_dscr': min_dscr, 'irr': irr}
    
    low_r = calc(low)
    base_r = calc(base)
    high_r = calc(high)
    
    # Unlevered IRR
    try:
        unlev = npf.irr([-total_capex] + [base[i] * 1000 - opex * 1000 for i in range(n)]) * 100
        if np.isnan(unlev): unlev = 0
    except: unlev = 0
    
    return {
        'feasible': low_r['min_dscr'] >= dscr_target,
        'gearing': gearing,
        'toll_pct': toll_pct,
        'toll_level': toll_level,
        'debt': debt / 1000,
        'equity': equity / 1000,
        'unlev_irr': unlev,
        'dscr_target': dscr_target,
        'low': low_r,
        'base': base_r,
        'high': high_r,
    }

def find_optimal(capex, opex, toll_level, cod_year, deg_on):
    """Find gearing + toll_pct that maximises equity IRR while staying feasible"""
    best_irr = -999
    best_g = 40
    best_t = 0
    
    # Grid search
    for toll_pct in range(0, 101, 5):
        max_g = min(80, get_max_gearing(toll_pct))
        for gearing in range(40, max_g + 1, 5):
            r = calculate(capex, opex, gearing, toll_pct, toll_level, cod_year, deg_on)
            if r and r['feasible'] and r['base']['irr'] > best_irr:
                best_irr = r['base']['irr']
                best_g = gearing
                best_t = toll_pct
    
    return best_g, best_t

# ============================================================================
# HEADER
# ============================================================================
st.markdown('<div class="header-row"><div class="main-title">Battery Toll Calculator</div><div class="brand-text">Modo Energy</div></div>', unsafe_allow_html=True)

# ============================================================================
# MAIN LAYOUT
# ============================================================================
left, right = st.columns([1, 1.1], gap="medium")

with left:
    st.markdown('<div class="section-card"><div class="section-title">Structure</div>', unsafe_allow_html=True)
    
    mode = st.selectbox("Mode", ["Manual", "Optimise"], label_visibility="collapsed")
    
    if mode == "Manual":
        gearing = st.slider("Gearing %", 40, 80, 65)
        toll_pct = st.slider("Toll Coverage %", 0, 100, 65)
        toll_level = st.slider("Toll Level (€k/MW/yr)", 70, 130, 100)
        
        # Gearing warning
        max_g = get_max_gearing(toll_pct)
        if gearing > max_g:
            st.markdown(f'<div class="gearing-warn">Exceeds {max_g}% max for {get_tier_label(toll_pct).lower()} tier</div>', unsafe_allow_html=True)
    else:
        toll_level = st.slider("Toll Level (€k/MW/yr)", 70, 130, 100)
        st.caption("Optimising gearing and toll coverage for max equity IRR...")
        gearing = None
        toll_pct = None
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Project settings
    st.markdown('<div class="section-card"><div class="section-title">Project</div>', unsafe_allow_html=True)
    p1, p2, p3 = st.columns(3)
    with p1: capex = st.number_input("CapEx (€k)", 300, 1000, 600, 25)
    with p2: opex = st.number_input("Opex (€k/yr)", 0, 30, 7, 1)
    with p3: cod_year = st.selectbox("COD", [2026, 2027, 2028], index=1)
    deg_on = st.checkbox("Degradation 2.5%/yr", True)
    st.markdown('</div>', unsafe_allow_html=True)

# Solve if optimising
if mode == "Optimise":
    gearing, toll_pct = find_optimal(capex, opex, toll_level, cod_year, deg_on)

# Get financing terms
dscr_target = get_dscr(toll_pct)
margin = get_margin(toll_pct)
rate = EURIBOR + margin / 100
tenor = get_tenor(toll_pct)
max_gear = get_max_gearing(toll_pct)
tier = get_tier_label(toll_pct)

# Calculate
result = calculate(capex, opex, gearing, toll_pct, toll_level, cod_year, deg_on)

with right:
    st.markdown('<div class="section-card"><div class="section-title">Results</div>', unsafe_allow_html=True)
    
    if result:
        hurdle = get_hurdle(toll_pct)
        base_irr = result['base']['irr']
        low_irr = result['low']['irr']
        high_irr = result['high']['irr']
        min_dscr = result['low']['min_dscr']
        
        # Debt card
        dscr_margin = min_dscr - dscr_target
        debt_class = "result-pass" if result['feasible'] else "result-fail"
        debt_badge = "FEASIBLE" if result['feasible'] else "NOT FEASIBLE"
        dscr_sign = "+" if dscr_margin >= 0 else ""
        
        st.markdown(f'''
        <div class="{debt_class}">
            <div class="result-header">
                <div>
                    <div class="result-label">Debt (Low Case DSCR)</div>
                    <div class="result-value">{min_dscr:.2f}x</div>
                    <div class="result-detail">vs {dscr_target:.2f}x target ({dscr_sign}{dscr_margin:.2f}x)</div>
                </div>
                <div class="result-badge">{debt_badge}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Equity card
        irr_delta = base_irr - hurdle
        if irr_delta >= 0:
            eq_class, eq_badge = "result-pass", "MEETS HURDLE"
        elif irr_delta >= -3:
            eq_class, eq_badge = "result-warn", "NEAR HURDLE"
        else:
            eq_class, eq_badge = "result-fail", "BELOW HURDLE"
        
        sign = "+" if irr_delta >= 0 else ""
        st.markdown(f'''
        <div class="{eq_class}">
            <div class="result-header">
                <div>
                    <div class="result-label">Equity IRR (Base Case)</div>
                    <div class="result-value">{base_irr:.1f}%</div>
                    <div class="result-detail">vs {hurdle:.0f}% hurdle ({sign}{irr_delta:.1f}%)</div>
                </div>
                <div class="result-badge">{eq_badge}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Scenarios
        def get_cls(irr, h):
            if irr >= h: return "green"
            elif irr >= h - 3: return "amber"
            else: return "red"
        
        st.markdown(f'''
        <div class="scenario-row">
            <div class="scenario-box {get_cls(low_irr, hurdle)}">
                <div class="scenario-label">Low Case</div>
                <div class="scenario-value {get_cls(low_irr, hurdle)}">{low_irr:.1f}%</div>
            </div>
            <div class="scenario-box {get_cls(high_irr, hurdle)}">
                <div class="scenario-label">High Case</div>
                <div class="scenario-value {get_cls(high_irr, hurdle)}">{high_irr:.1f}%</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Metrics
        st.markdown(f'''
        <div class="metrics-grid">
            <div class="metric-box"><div class="metric-value">{result['unlev_irr']:.1f}%</div><div class="metric-label">Unlev</div></div>
            <div class="metric-box"><div class="metric-value">{gearing:.0f}%</div><div class="metric-label">Gearing</div></div>
            <div class="metric-box"><div class="metric-value">{toll_pct:.0f}%</div><div class="metric-label">Toll %</div></div>
            <div class="metric-box"><div class="metric-value">{result['equity']:.0f}k</div><div class="metric-label">Equity</div></div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Financing terms
    st.markdown('<div class="section-card"><div class="section-title">Financing Terms</div>', unsafe_allow_html=True)
    st.markdown(f'''
    <div class="terms-row">
        <div class="term-item"><div class="term-value">{dscr_target:.2f}x</div><div class="term-label">DSCR</div></div>
        <div class="term-item"><div class="term-value">{rate:.1f}%</div><div class="term-label">Rate</div></div>
        <div class="term-item"><div class="term-value">{tenor}yr</div><div class="term-label">Tenor</div></div>
        <div class="term-item"><div class="term-value">{max_gear}%</div><div class="term-label">Max Gear</div></div>
    </div>
    ''', unsafe_allow_html=True)
    st.caption(f"{tier} tier")
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown('<div class="footer">1.5 cycle · 2hr · German BESS · Modo forecasts 2026-2040 · Educational only</div>', unsafe_allow_html=True)
