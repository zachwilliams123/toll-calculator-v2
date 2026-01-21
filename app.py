"""
Battery Toll Calculator v12
Modo Energy - German BESS

Option A layout:
- Two separate result cards with rounded corners
- Unlevered as plain text
- No project title
- No min indicator under slider
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
    .block-container {padding: 1rem 2rem 0.5rem 2rem; max-width: 950px;}
    
    .header-row {
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 0.6rem; padding-bottom: 0.5rem; border-bottom: 2px solid #e2e8f0;
    }
    .main-title { font-size: 1.3rem; font-weight: 700; color: #1a1a2e; }
    .brand-text { font-size: 0.8rem; color: #1a1a2e; font-weight: 600; }
    
    .section-card {
        background: #fff; border-radius: 10px; padding: 0.9rem 1.1rem;
        border: 1px solid #e2e8f0; margin-bottom: 0.5rem;
    }
    .section-title {
        font-size: 0.6rem; font-weight: 600; color: #64748b;
        margin-bottom: 0.6rem; text-transform: uppercase; letter-spacing: 0.05em;
    }
    
    /* Gearing bar */
    .gearing-row {
        display: flex; align-items: center; gap: 0.6rem; margin: 0.5rem 0 0.3rem 0;
    }
    .gearing-label { font-size: 0.65rem; color: #64748b; min-width: 50px; }
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
    
    /* Debt/Equity under gearing */
    .capital-row {
        display: flex; justify-content: flex-end; gap: 1rem;
        font-size: 0.6rem; color: #64748b; margin-bottom: 0.5rem;
    }
    .capital-row span { font-weight: 500; }
    
    /* Terms row */
    .terms-row {
        display: flex; gap: 0.6rem; padding-top: 0.5rem;
        border-top: 1px solid #f1f5f9; margin-top: 0.3rem;
    }
    .term-chip {
        font-size: 0.6rem; color: #475569;
    }
    .term-chip strong { color: #1e293b; }
    
    /* Result cards - separate with rounded corners */
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
    
    /* Unlevered text */
    .unlev-text {
        font-size: 0.65rem; color: #64748b; margin-top: 0.3rem; margin-bottom: 0.6rem;
    }
    .unlev-text strong { color: #475569; }
    
    /* Project inputs - plain */
    .project-inputs {
        margin-top: 0.5rem;
    }
    
    .footer { 
        text-align: center; font-size: 0.55rem; color: #94a3b8; 
        margin-top: 0.6rem; padding-top: 0.5rem; border-top: 1px solid #f1f5f9; 
    }
    
    /* Streamlit overrides */
    div[data-testid="stSlider"] { padding-top: 0 !important; padding-bottom: 0.3rem !important; }
    div[data-testid="stSlider"] label p { font-size: 0.65rem !important; color: #475569 !important; }
    div[data-testid="stNumberInput"] label p { font-size: 0.65rem !important; color: #475569 !important; }
    div[data-testid="stNumberInput"] { margin-bottom: 0.15rem; }
    div[data-testid="stNumberInput"] > div { max-width: 130px; }
    div[data-testid="stSelectbox"] > div { max-width: 95px; }
    div[data-testid="stSelectbox"] label p { font-size: 0.65rem !important; color: #475569 !important; }
    
    /* Subtle button */
    div[data-testid="stButton"] button {
        font-size: 0.6rem !important; 
        padding: 0.4rem 0.7rem !important;
        background-color: transparent !important; 
        color: #64748b !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
    }
    div[data-testid="stButton"] button:hover {
        background-color: #f1f5f9 !important;
        border-color: #94a3b8 !important;
        color: #475569 !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA
# ============================================================================
REVENUE_DATA = {
    2026: {'low': [142, 94, 76, 72, 69, 68, 68, 70, 67, 67], 'base': [240, 155, 129, 124, 119, 117, 118, 118, 117, 114], 'high': [319, 205, 168, 163, 158, 154, 157, 155, 151, 154]},
    2027: {'low': [94, 76, 72, 69, 68, 68, 70, 67, 67, 69], 'base': [155, 129, 124, 119, 117, 118, 118, 117, 114, 115], 'high': [205, 168, 163, 158, 154, 157, 155, 151, 154, 154]},
    2028: {'low': [76, 72, 69, 68, 68, 70, 67, 67, 69, 72], 'base': [129, 124, 119, 117, 118, 118, 117, 114, 115, 119], 'high': [168, 163, 158, 154, 157, 155, 151, 154, 154, 156]},
}

EURIBOR = 2.25
TENOR = 7

# ============================================================================
# FINANCING FORMULAS
# ============================================================================
def get_gearing(toll_pct):
    return 45 + toll_pct * 0.35  # 45% at 0% coverage → 80% at 100% coverage

def get_dscr(toll_pct):
    return 2.00 - toll_pct * 0.008

def get_margin(toll_pct):
    return 280 - toll_pct * 0.80

def get_hurdle(toll_pct):
    if toll_pct >= 80: return 10.0
    elif toll_pct >= 50: return 12.0
    elif toll_pct >= 20: return 14.0
    else: return 16.0

# ============================================================================
# FINANCIAL MODEL
# ============================================================================
@st.cache_data
def calculate(capex, opex, toll_pct, toll_level, cod):
    revenue = REVENUE_DATA.get(cod, REVENUE_DATA[2027])
    
    gearing = get_gearing(toll_pct)
    dscr_target = get_dscr(toll_pct)
    rate = (EURIBOR + get_margin(toll_pct) / 100) / 100
    
    n = 10
    deg = 0.025
    df = [(1 - deg) ** i for i in range(n)]
    tf = toll_pct / 100
    
    low = [toll_level * tf + revenue['low'][i] * df[i] * (1 - tf) for i in range(n)]
    base = [toll_level * tf + revenue['base'][i] * df[i] * (1 - tf) for i in range(n)]
    high = [toll_level * tf + revenue['high'][i] * df[i] * (1 - tf) for i in range(n)]
    
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

def find_min_coverage(capex, opex, toll_level, cod):
    for t in range(0, 101):
        r = calculate(capex, opex, t, toll_level, cod)
        if r and r['feasible']:
            return t
    return None

# ============================================================================
# SESSION STATE
# ============================================================================
if 'toll_slider' not in st.session_state:
    st.session_state.toll_slider = 80
if 'capex' not in st.session_state:
    st.session_state.capex = 600
if 'opex' not in st.session_state:
    st.session_state.opex = 7
if 'cod' not in st.session_state:
    st.session_state.cod = 2027

# ============================================================================
# HEADER
# ============================================================================
st.markdown('<div class="header-row"><div class="main-title">Battery Toll Calculator</div><div class="brand-text">Modo Energy</div></div>', unsafe_allow_html=True)

# ============================================================================
# LAYOUT
# ============================================================================
left, right = st.columns([1, 1.1], gap="large")

with left:
    st.markdown('<div class="section-card"><div class="section-title">Structure</div>', unsafe_allow_html=True)
    
    # Toll level + subtle find minimum button
    col1, col2 = st.columns([1.2, 1])
    with col1:
        toll_level = st.number_input("Toll Level (€k/MW/yr)", min_value=80, max_value=120, value=100, step=5)
    with col2:
        st.markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
        if st.button("Minimum coverage ▸", use_container_width=True):
            min_cov = find_min_coverage(st.session_state.capex, st.session_state.opex, toll_level, st.session_state.cod)
            if min_cov is not None:
                st.session_state.toll_slider = min_cov
                st.rerun()
    
    # Coverage slider
    toll_pct = st.slider("Toll Coverage %", 0, 100, key="toll_slider")
    
    # Gearing bar
    gearing = get_gearing(toll_pct)
    bar_pct = (gearing - 45) / 35 * 100  # Scale 45-80% to 0-100%
    
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
    
    # Debt/Equity under gearing
    result = calculate(st.session_state.capex, st.session_state.opex, toll_pct, toll_level, st.session_state.cod)
    if result:
        st.markdown(f'''
        <div class="capital-row">
            <span>€{result['debt']:.0f}k debt</span>
            <span>€{result['equity']:.0f}k equity</span>
        </div>
        ''', unsafe_allow_html=True)
    
    # Terms row
    dscr_target = get_dscr(toll_pct)
    margin = get_margin(toll_pct)
    rate = EURIBOR + margin / 100
    
    st.markdown(f'''
    <div class="terms-row">
        <span class="term-chip"><strong>{dscr_target:.2f}x</strong> DSCR</span>
        <span class="term-chip"><strong>{rate:.1f}%</strong> rate</span>
        <span class="term-chip"><strong>7yr</strong> tenor</span>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# RESULTS
# ============================================================================
with right:
    st.markdown('<div class="section-title" style="margin-bottom: 0.5rem;">Results</div>', unsafe_allow_html=True)
    
    if result:
        hurdle = get_hurdle(toll_pct)
        base_irr = result['base']['irr']
        low_irr = result['low']['irr']
        high_irr = result['high']['irr']
        min_dscr = result['low']['min_dscr']
        dscr_target = result['dscr_target']
        
        # DEBT card
        dscr_margin = min_dscr - dscr_target
        debt_class = "pass" if result['feasible'] else "fail"
        debt_badge = "FEASIBLE" if result['feasible'] else "NOT FEASIBLE"
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
                    <div class="result-label">Equity IRR</div>
                    <div class="result-value">{base_irr:.1f}%</div>
                    <div class="result-detail">vs {hurdle:.0f}% hurdle ({sign}{irr_delta:.1f}%)</div>
                </div>
                <div class="result-badge">{eq_badge}</div>
            </div>
            <div class="result-scenarios">
                {low_irr:.1f}% low case · {high_irr:.1f}% high case
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Unlevered text
        st.markdown(f'''
        <div class="unlev-text">
            <strong>{result['unlev_irr']:.1f}%</strong> unlevered project IRR
        </div>
        ''', unsafe_allow_html=True)
    
    # Project inputs - plain
    st.markdown('<div class="project-inputs">', unsafe_allow_html=True)
    
    pc1, pc2, pc3 = st.columns([1.1, 1, 0.9])
    with pc1:
        capex = st.number_input("CapEx (€k)", 300, 1000, st.session_state.capex, 25, key="capex_input")
        st.session_state.capex = capex
    with pc2:
        opex = st.number_input("OpEx (€k/yr)", 0, 30, st.session_state.opex, 1, key="opex_input")
        st.session_state.opex = opex
    with pc3:
        cod = st.selectbox("COD", [2026, 2027, 2028], index=[2026,2027,2028].index(st.session_state.cod), key="cod_input")
        st.session_state.cod = cod
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# FOOTER
# ============================================================================
st.markdown('<div class="footer">2hr · 1.5 cycle · 7yr tenor · 2.5% degradation · Modo forecasts · Educational only</div>', unsafe_allow_html=True)
