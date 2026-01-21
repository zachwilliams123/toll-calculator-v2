"""
Battery Toll Calculator v8.0
Modo Energy - German BESS

Final version:
- 7-year tenor (standard for German tolls)
- Toll level 80-120k (realistic market range)
- Linear financing relationships
- Gearing derived from toll structure
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
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 0.5rem; padding-bottom: 0.4rem; border-bottom: 2px solid #e2e8f0;
    }
    .main-title { font-size: 1.25rem; font-weight: 700; color: #1a1a2e; }
    .brand-text { font-size: 0.75rem; color: #1a1a2e; font-weight: 600; }
    
    .section-card {
        background: #fff; border-radius: 8px; padding: 0.7rem 0.9rem;
        border: 1px solid #e2e8f0; margin-bottom: 0.5rem;
    }
    .section-title {
        font-size: 0.6rem; font-weight: 600; color: #64748b;
        margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.05em;
    }
    
    .gearing-container { margin: 0.4rem 0; }
    .gearing-label { font-size: 0.65rem; color: #475569; margin-bottom: 0.2rem; }
    .gearing-bar-bg {
        background: #e2e8f0; border-radius: 4px; height: 24px;
        position: relative; overflow: hidden;
    }
    .gearing-bar-fill {
        background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%);
        height: 100%; border-radius: 4px;
        display: flex; align-items: center; justify-content: flex-end; padding-right: 8px;
        transition: width 0.3s ease;
    }
    .gearing-value { font-size: 0.75rem; font-weight: 600; color: white; }
    .gearing-scale {
        display: flex; justify-content: space-between;
        font-size: 0.5rem; color: #94a3b8; margin-top: 2px;
    }
    
    .result-pass {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        border-radius: 8px; padding: 0.65rem 0.85rem; color: white; margin-bottom: 0.4rem;
    }
    .result-warn {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        border-radius: 8px; padding: 0.65rem 0.85rem; color: white; margin-bottom: 0.4rem;
    }
    .result-fail {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        border-radius: 8px; padding: 0.65rem 0.85rem; color: white; margin-bottom: 0.4rem;
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
    
    .optimal-box {
        background: #dbeafe; border: 1px solid #3b82f6; border-radius: 6px;
        padding: 0.4rem 0.6rem; margin-top: 0.4rem;
    }
    .optimal-label { font-size: 0.55rem; color: #1d4ed8; text-transform: uppercase; }
    .optimal-value { font-size: 1rem; font-weight: 700; color: #1d4ed8; }
    
    .footer { text-align: center; font-size: 0.5rem; color: #94a3b8; margin-top: 0.5rem; padding-top: 0.3rem; border-top: 1px solid #f1f5f9; }
    
    div[data-testid="stSlider"] { padding-top: 0 !important; padding-bottom: 0.15rem !important; }
    div[data-testid="stSlider"] label p { font-size: 0.65rem !important; color: #475569 !important; }
    div[data-testid="stNumberInput"] label p { font-size: 0.65rem !important; color: #475569 !important; }
    div[data-testid="stNumberInput"] { margin-bottom: 0.3rem; }
    div[data-testid="stSelectbox"] label p { font-size: 0.65rem !important; color: #475569 !important; }
    div[data-testid="stCheckbox"] label p { font-size: 0.6rem !important; color: #475569 !important; }
    div[data-testid="stNumberInput"] > div { max-width: 140px; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA - Modo Energy German BESS Forecasts (COD 2027)
# ============================================================================
REVENUE = {
    'year': list(range(2027, 2037)),
    'low':  [94, 76, 72, 69, 68, 68, 70, 67, 67, 69],
    'base': [155, 129, 124, 119, 117, 118, 118, 117, 114, 115],
    'high': [205, 168, 163, 158, 154, 157, 155, 151, 154, 154],
}

EURIBOR = 2.25
TENOR = 7  # Fixed 7-year tenor (standard for German tolls)

# ============================================================================
# LINEAR FINANCING RELATIONSHIPS
# ============================================================================
def get_gearing(toll_pct):
    """Gearing = 45% + (toll_pct × 0.25) → 45% to 70%"""
    return 45 + toll_pct * 0.25

def get_dscr(toll_pct):
    """DSCR = 2.00 - (toll_pct × 0.008) → 2.00x to 1.20x"""
    return 2.00 - toll_pct * 0.008

def get_margin(toll_pct):
    """Margin = 280 - (toll_pct × 0.80) bps → 280bps to 200bps"""
    return 280 - toll_pct * 0.80

def get_hurdle(toll_pct):
    """Hurdle rate by risk profile"""
    if toll_pct >= 80: return 10.0
    elif toll_pct >= 50: return 12.0
    elif toll_pct >= 20: return 14.0
    else: return 16.0

def get_tier_label(toll_pct):
    if toll_pct >= 80: return "Contracted"
    elif toll_pct >= 40: return "Partly contracted"
    else: return "Merchant"

# ============================================================================
# FINANCIAL MODEL
# ============================================================================
@st.cache_data
def calculate(capex, opex, toll_pct, toll_level):
    gearing = get_gearing(toll_pct)
    dscr_target = get_dscr(toll_pct)
    margin = get_margin(toll_pct)
    rate = (EURIBOR + margin / 100) / 100
    
    n = len(REVENUE['year'])
    deg = 0.025
    df = [(1 - deg) ** i for i in range(n)]
    
    tf = toll_pct / 100
    low = [toll_level * tf + REVENUE['low'][i] * df[i] * (1 - tf) for i in range(n)]
    base = [toll_level * tf + REVENUE['base'][i] * df[i] * (1 - tf) for i in range(n)]
    high = [toll_level * tf + REVENUE['high'][i] * df[i] * (1 - tf) for i in range(n)]
    
    total_capex = capex * 1000
    debt = total_capex * gearing / 100
    equity = total_capex - debt
    if equity <= 0: return None
    
    pmt = debt * (rate * (1 + rate)**TENOR) / ((1 + rate)**TENOR - 1) if debt > 0 else 0
    ds = [pmt if i < TENOR else 0 for i in range(n)]
    
    def scenario(rev):
        ncf = [rev[i] * 1000 - opex * 1000 for i in range(n)]
        ecf = [ncf[i] - ds[i] for i in range(n)]
        dscr_vals = [ncf[i] / ds[i] if ds[i] > 0 else 99 for i in range(n)]
        min_dscr = min([d for d in dscr_vals if d < 99]) if any(d < 99 for d in dscr_vals) else 99
        try:
            irr = npf.irr([-equity] + ecf) * 100
            if np.isnan(irr) or irr < -50 or irr > 200: irr = -99
        except: irr = -99
        return {'min_dscr': min_dscr, 'irr': irr}
    
    low_r = scenario(low)
    base_r = scenario(base)
    high_r = scenario(high)
    
    try:
        unlev = npf.irr([-total_capex] + [base[i] * 1000 - opex * 1000 for i in range(n)]) * 100
        if np.isnan(unlev): unlev = 0
    except: unlev = 0
    
    return {
        'feasible': low_r['min_dscr'] >= dscr_target,
        'gearing': gearing,
        'dscr_target': dscr_target,
        'debt': debt / 1000,
        'equity': equity / 1000,
        'unlev_irr': unlev,
        'low': low_r,
        'base': base_r,
        'high': high_r,
    }

def find_min_coverage(capex, opex, toll_level):
    """Find minimum toll coverage % for feasible financing"""
    for t in range(0, 101):
        r = calculate(capex, opex, t, toll_level)
        if r and r['feasible']:
            return t
    return 100

# ============================================================================
# HEADER
# ============================================================================
st.markdown('<div class="header-row"><div class="main-title">Battery Toll Calculator</div><div class="brand-text">Modo Energy</div></div>', unsafe_allow_html=True)

# ============================================================================
# LAYOUT
# ============================================================================
left, right = st.columns([1, 1.1], gap="medium")

with left:
    st.markdown('<div class="section-card"><div class="section-title">Structure</div>', unsafe_allow_html=True)
    
    toll_level = st.number_input("Toll Level (€k/MW/yr)", min_value=80, max_value=120, value=100, step=5)
    toll_pct = st.slider("Toll Coverage %", 0, 100, 80)
    
    # Derived gearing bar
    gearing = get_gearing(toll_pct)
    bar_pct = (gearing - 45) / 25 * 100  # Scale 45-70% to 0-100%
    
    st.markdown(f'''
    <div class="gearing-container">
        <div class="gearing-label">Gearing (derived)</div>
        <div class="gearing-bar-bg">
            <div class="gearing-bar-fill" style="width: {min(bar_pct, 100)}%;">
                <span class="gearing-value">{gearing:.0f}%</span>
            </div>
        </div>
        <div class="gearing-scale"><span>45%</span><span>57%</span><span>70%</span></div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Optimiser
    if st.button("Find minimum viable coverage", use_container_width=True):
        optimal = find_min_coverage(600, 7, toll_level)
        st.session_state['min_coverage'] = optimal
        st.session_state['min_toll_level'] = toll_level
    
    if 'min_coverage' in st.session_state:
        st.markdown(f'''
        <div class="optimal-box">
            <div class="optimal-label">Minimum at €{st.session_state['min_toll_level']}k toll</div>
            <div class="optimal-value">{st.session_state['min_coverage']}%</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Project
    st.markdown('<div class="section-card"><div class="section-title">Project</div>', unsafe_allow_html=True)
    p1, p2 = st.columns(2)
    with p1: capex = st.number_input("CapEx (€k/MW)", 300, 1000, 600, 25)
    with p2: opex = st.number_input("OpEx (€k/yr)", 0, 30, 7, 1)
    st.caption("COD 2027 · 2.5% degradation · 7-year tenor")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Financing terms
    st.markdown('<div class="section-card"><div class="section-title">Financing Terms</div>', unsafe_allow_html=True)
    
    dscr_target = get_dscr(toll_pct)
    margin = get_margin(toll_pct)
    rate = EURIBOR + margin / 100
    tier = get_tier_label(toll_pct)
    
    st.markdown(f'''
    <div class="terms-row">
        <div class="term-item"><div class="term-value">{dscr_target:.2f}x</div><div class="term-label">DSCR</div></div>
        <div class="term-item"><div class="term-value">{rate:.2f}%</div><div class="term-label">Rate</div></div>
        <div class="term-item"><div class="term-value">7yr</div><div class="term-label">Tenor</div></div>
        <div class="term-item"><div class="term-value">{gearing:.0f}%</div><div class="term-label">Gearing</div></div>
    </div>
    ''', unsafe_allow_html=True)
    st.caption(f"{tier}")
    st.markdown('</div>', unsafe_allow_html=True)

# Calculate
result = calculate(capex, opex, toll_pct, toll_level)

# ============================================================================
# RESULTS
# ============================================================================
with right:
    st.markdown('<div class="section-card"><div class="section-title">Results</div>', unsafe_allow_html=True)
    
    if result:
        hurdle = get_hurdle(toll_pct)
        base_irr = result['base']['irr']
        low_irr = result['low']['irr']
        high_irr = result['high']['irr']
        min_dscr = result['low']['min_dscr']
        dscr_target = result['dscr_target']
        
        # Debt card
        dscr_margin = min_dscr - dscr_target
        debt_class = "result-pass" if result['feasible'] else "result-fail"
        debt_badge = "FEASIBLE" if result['feasible'] else "NOT FEASIBLE"
        dscr_sign = "+" if dscr_margin >= 0 else ""
        
        st.markdown(f'''
        <div class="{debt_class}">
            <div class="result-header">
                <div>
                    <div class="result-label">Debt Sizing (Low Case DSCR)</div>
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
                <div class="scenario-label">Low Case IRR</div>
                <div class="scenario-value {get_cls(low_irr, hurdle)}">{low_irr:.1f}%</div>
            </div>
            <div class="scenario-box {get_cls(high_irr, hurdle)}">
                <div class="scenario-label">High Case IRR</div>
                <div class="scenario-value {get_cls(high_irr, hurdle)}">{high_irr:.1f}%</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Metrics
        st.markdown(f'''
        <div class="metrics-grid">
            <div class="metric-box"><div class="metric-value">{result['unlev_irr']:.1f}%</div><div class="metric-label">Unlev IRR</div></div>
            <div class="metric-box"><div class="metric-value">{result['gearing']:.0f}%</div><div class="metric-label">Gearing</div></div>
            <div class="metric-box"><div class="metric-value">{result['debt']:.0f}k</div><div class="metric-label">Debt</div></div>
            <div class="metric-box"><div class="metric-value">{result['equity']:.0f}k</div><div class="metric-label">Equity</div></div>
        </div>
        ''', unsafe_allow_html=True)
    else:
        st.error("Unable to calculate. Check inputs.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown('<div class="footer">2hr duration · German BESS · Modo forecasts · Educational only</div>', unsafe_allow_html=True)
