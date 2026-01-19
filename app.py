"""
Battery Toll Calculator
Modo Energy - Brand styled with DM Sans
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="Battery Toll Calculator | Modo Energy",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ===== MODO ENERGY BRAND STYLING =====
# Colors extracted from Modo Energy terminal/website:
# - Primary dark: #1a1a2e (near black with slight blue)
# - Accent teal/green: #10b981, #0d9488
# - Neutral grays: #f8fafc, #e2e8f0, #64748b, #334155
# - Error/warning: #ef4444, #f97316
# - Font: DM Sans

st.markdown("""
<style>
    /* Import DM Sans from Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&display=swap');
    
    /* Apply DM Sans globally */
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }
    
    /* Hide Streamlit chrome */
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding: 1.5rem 2rem; max-width: 1200px;}
    
    /* Title styling - Modo uses clean, bold headers */
    .main-title {
        font-family: 'DM Sans', sans-serif;
        font-size: 1.75rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.25rem;
        letter-spacing: -0.02em;
    }
    .subtitle {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.875rem;
        color: #64748b;
        margin-bottom: 1.25rem;
        font-weight: 400;
    }
    .brand-text {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.875rem;
        color: #94a3b8;
        text-align: right;
        font-weight: 500;
    }
    
    /* Section cards - clean with subtle borders */
    .section-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.25rem;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    .section-title {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.9rem;
        font-weight: 600;
        color: #1a1a2e;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #f1f5f9;
        letter-spacing: -0.01em;
    }
    
    /* Hero card - Modo teal gradient */
    .hero-card {
        background: linear-gradient(135deg, #10b981 0%, #0d9488 100%);
        border-radius: 12px;
        padding: 1.5rem;
        color: white;
        margin-bottom: 1.25rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .hero-card.not-bankable {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    }
    .hero-status {
        font-family: 'DM Sans', sans-serif;
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    .hero-sub {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.8rem;
        opacity: 0.9;
        margin-top: 0.35rem;
        font-weight: 400;
    }
    .hero-irr-label {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.75rem;
        opacity: 0.85;
        text-align: right;
        font-weight: 500;
    }
    .hero-irr {
        font-family: 'DM Sans', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        text-align: right;
        letter-spacing: -0.03em;
    }
    
    /* Metrics row */
    .metrics-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.75rem;
        margin-bottom: 1.25rem;
    }
    .metric-box {
        background: #f8fafc;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #e2e8f0;
    }
    .metric-value {
        font-family: 'DM Sans', sans-serif;
        font-size: 1.35rem;
        font-weight: 700;
        color: #1a1a2e;
        letter-spacing: -0.02em;
    }
    .metric-label {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.7rem;
        color: #64748b;
        margin-top: 0.25rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    
    /* Financing grid */
    .fin-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    .fin-box {
        background: #f8fafc;
        border-radius: 8px;
        padding: 0.85rem;
    }
    .fin-label {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.7rem;
        color: #64748b;
        font-weight: 500;
    }
    .fin-value {
        font-family: 'DM Sans', sans-serif;
        font-size: 1.15rem;
        font-weight: 600;
        color: #1a1a2e;
        letter-spacing: -0.01em;
    }
    
    /* IRR scenario rows */
    .irr-section-title {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.85rem;
        font-weight: 600;
        color: #1a1a2e;
        margin-bottom: 0.6rem;
    }
    .irr-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.7rem 0.85rem;
        border-radius: 8px;
        margin-bottom: 0.4rem;
    }
    .irr-row.p99 { background: #fef2f2; }
    .irr-row.p50 { background: #ecfdf5; }
    .irr-row.p1 { background: #f0fdf4; }
    .irr-label { 
        font-family: 'DM Sans', sans-serif;
        font-size: 0.8rem; 
        font-weight: 500; 
    }
    .irr-label.p99 { color: #dc2626; }
    .irr-label.p50 { color: #059669; }
    .irr-label.p1 { color: #16a34a; }
    .irr-value { 
        font-family: 'DM Sans', sans-serif;
        font-size: 1.05rem; 
        font-weight: 700; 
        letter-spacing: -0.01em;
    }
    .irr-value.p99 { color: #dc2626; }
    .irr-value.p50 { color: #059669; }
    .irr-value.p1 { color: #16a34a; }
    
    /* Leverage box */
    .leverage-box {
        background: #fefce8;
        border-radius: 8px;
        padding: 0.85rem;
        margin-top: 0.75rem;
        border: 1px solid #fef08a;
    }
    .leverage-title {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.75rem;
        font-weight: 600;
        color: #a16207;
    }
    .leverage-text {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.8rem;
        color: #854d0e;
        font-weight: 500;
    }
    
    /* Solving badge - Modo uses clean blue accents */
    .solving-box {
        background: #eff6ff;
        border: 2px solid #3b82f6;
        border-radius: 10px;
        padding: 0.6rem 0.85rem;
        margin-bottom: 0.6rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .solving-label {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.85rem;
        font-weight: 600;
        color: #1e40af;
    }
    .solving-badge {
        font-family: 'DM Sans', sans-serif;
        background: #3b82f6;
        color: white;
        font-size: 0.65rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 6px;
        letter-spacing: 0.02em;
    }
    
    /* Button styling - Modo style */
    .stButton > button {
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.85rem !important;
        letter-spacing: -0.01em !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button[kind="primary"] {
        background: #1a1a2e !important;
        color: white !important;
        border: none !important;
    }
    .stButton > button[kind="secondary"] {
        background: white !important;
        color: #334155 !important;
        border: 1px solid #e2e8f0 !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }
    
    /* Slider styling */
    .stSlider label { 
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.8rem !important; 
        color: #334155 !important;
        font-weight: 500 !important;
    }
    .stSlider > div > div { padding-top: 0 !important; }
    
    /* Number input */
    .stNumberInput label { 
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.8rem !important; 
        color: #334155 !important;
        font-weight: 500 !important;
    }
    .stNumberInput input {
        font-family: 'DM Sans', sans-serif !important;
    }
    
    /* Checkbox */
    .stCheckbox label { 
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader { 
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        font-family: 'DM Sans', sans-serif;
        font-size: 0.75rem;
        color: #94a3b8;
        padding: 1.25rem 0;
        border-top: 1px solid #e2e8f0;
        margin-top: 1.5rem;
        font-weight: 400;
    }
    
    /* Caption styling */
    .stCaption {
        font-family: 'DM Sans', sans-serif !important;
    }
</style>
""", unsafe_allow_html=True)

# ===== DATA =====
REVENUE = {
    'P99': {2026: 159.1, 2027: 101.2, 2028: 83.3, 2029: 77.9, 2030: 72.9, 
            2031: 71.4, 2032: 70.0, 2033: 68.6, 2034: 67.2, 2035: 65.9},
    'P50': {2026: 256.0, 2027: 161.6, 2028: 129.4, 2029: 123.4, 2030: 116.4,
            2031: 114.1, 2032: 111.8, 2033: 109.6, 2034: 107.4, 2035: 105.2},
    'P1':  {2026: 333.1, 2027: 209.0, 2028: 164.6, 2029: 157.6, 2030: 149.2,
            2031: 146.2, 2032: 143.3, 2033: 140.4, 2034: 137.6, 2035: 134.9}
}

# ===== CALCULATIONS =====
def calc_irr(cfs, guess=0.1):
    irr = guess
    for _ in range(100):
        npv = sum(cf / (1 + irr)**i for i, cf in enumerate(cfs))
        dnpv = sum(-i * cf / (1 + irr)**(i+1) for i, cf in enumerate(cfs))
        if abs(dnpv) < 0.0001: break
        new_irr = irr - npv / dnpv
        if abs(new_irr - irr) < 0.0001: return new_irr * 100
        if new_irr < -0.99 or new_irr > 10: return np.nan
        irr = new_irr
    return irr * 100

def calc_pmt(rate, nper, pv):
    if rate == 0 or nper == 0: return pv / max(nper, 1)
    r = rate / 100
    return pv * (r * (1+r)**nper) / ((1+r)**nper - 1)

def calculate(capex, opex, gearing, toll_pct, toll_level, dscr_target, debt_rate, tenor, sculpting, deg_on, deg_rate):
    debt = capex * gearing / 100
    equity = capex - debt
    if equity <= 0 and gearing > 0: return None
    
    tp = toll_pct / 100
    rate = debt_rate / 100
    
    def get_cfads(revs):
        profile = []
        for i in range(tenor):
            yr = 2026 + i
            rev = revs.get(yr, revs[2035])
            deg = (1 - deg_rate/100)**i if deg_on else 1
            toll_rev = toll_level * tp
            merch_rev = rev * (1 - tp) * deg
            cfads = toll_rev + merch_rev - opex
            profile.append({'year': yr, 'cfads': cfads})
        return profile
    
    p99_profile = get_cfads(REVENUE['P99'])
    
    debt_schedule = []
    remaining = debt
    
    if sculpting and debt > 0:
        for i in range(tenor):
            target_ds = p99_profile[i]['cfads'] / dscr_target
            interest = remaining * rate
            principal = min(max(0, target_ds - interest), remaining)
            remaining = max(0, remaining - principal)
            debt_schedule.append({'ds': interest + principal})
        if remaining > 0.01:
            debt_schedule[-1]['ds'] += remaining
    else:
        flat_ds = calc_pmt(debt_rate, tenor, debt) if debt > 0 else 0
        for i in range(tenor):
            interest = remaining * rate
            principal = flat_ds - interest
            remaining = max(0, remaining - principal)
            debt_schedule.append({'ds': flat_ds})
    
    avg_ds = sum(d['ds'] for d in debt_schedule) / tenor if debt > 0 else 0
    
    def scenario_result(revs):
        profile = get_cfads(revs)
        cfs = [-equity]
        min_dscr = 999
        for i in range(tenor):
            cfads = profile[i]['cfads']
            ds = debt_schedule[i]['ds'] if debt_schedule else 0
            dscr = cfads / ds if ds > 0 else 999
            min_dscr = min(min_dscr, dscr)
            cfs.append(max(0, cfads - ds))
        irr = calc_irr(cfs) if equity > 0 else 0
        return {'irr': irr, 'min_dscr': min_dscr}
    
    p50_profile = get_cfads(REVENUE['P50'])
    unlev_cfs = [-capex] + [p['cfads'] for p in p50_profile]
    unlev_irr = calc_irr(unlev_cfs)
    
    p99 = scenario_result(REVENUE['P99'])
    p50 = scenario_result(REVENUE['P50'])
    p1 = scenario_result(REVENUE['P1'])
    
    variance = ((p50['irr'] - p99['irr']) / p50['irr'] * 100) if p50['irr'] > 0 else 0
    
    return {
        'debt': debt, 'equity': equity, 'avg_ds': avg_ds,
        'gearing': gearing, 'toll_pct': toll_pct, 'toll_level': toll_level,
        'unlev_irr': unlev_irr, 'p99': p99, 'p50': p50, 'p1': p1,
        'variance': variance, 'bankable': p99['min_dscr'] >= dscr_target,
        'min_dscr': p99['min_dscr']
    }

def find_max_gearing(capex, opex, tp, tl, dscr, rate, tenor, sculpt, deg_on, deg_rate):
    for g in range(85, -1, -1):
        r = calculate(capex, opex, g, tp, tl, dscr, rate, tenor, sculpt, deg_on, deg_rate)
        if r and r['bankable']: return r
    return calculate(capex, opex, 0, tp, tl, dscr, rate, tenor, sculpt, deg_on, deg_rate)

def find_min_toll_pct(capex, opex, g, tl, dscr, rate, tenor, sculpt, deg_on, deg_rate):
    for tp in range(0, 101):
        r = calculate(capex, opex, g, tp, tl, dscr, rate, tenor, sculpt, deg_on, deg_rate)
        if r and r['bankable']: return r
    return calculate(capex, opex, g, 100, tl, dscr, rate, tenor, sculpt, deg_on, deg_rate)

def find_min_toll_level(capex, opex, g, tp, dscr, rate, tenor, sculpt, deg_on, deg_rate):
    for tl in range(50, 201):
        r = calculate(capex, opex, g, tp, tl, dscr, rate, tenor, sculpt, deg_on, deg_rate)
        if r and r['bankable']: return r
    return calculate(capex, opex, g, tp, 200, dscr, rate, tenor, sculpt, deg_on, deg_rate)

# ===== HEADER =====
col_t1, col_t2 = st.columns([4, 1])
with col_t1:
    st.markdown("<div class='main-title'>Battery Toll Calculator</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>German BESS · Educational tool</div>", unsafe_allow_html=True)
with col_t2:
    st.markdown("<div class='brand-text'>Modo Energy</div>", unsafe_allow_html=True)

# ===== MODE SELECTOR =====
if 'mode' not in st.session_state:
    st.session_state.mode = 'Manual'

col_m1, col_m2, col_m3, col_m4, col_spacer = st.columns([1, 1, 1, 1, 3])
with col_m1:
    if st.button("Manual", key="btn_manual", use_container_width=True, type="primary" if st.session_state.mode == "Manual" else "secondary"):
        st.session_state.mode = "Manual"
with col_m2:
    if st.button("Max Gearing", key="btn_gearing", use_container_width=True, type="primary" if st.session_state.mode == "Max Gearing" else "secondary"):
        st.session_state.mode = "Max Gearing"
with col_m3:
    if st.button("Min Toll %", key="btn_tollpct", use_container_width=True, type="primary" if st.session_state.mode == "Min Toll %" else "secondary"):
        st.session_state.mode = "Min Toll %"
with col_m4:
    if st.button("Min Toll €", key="btn_tolllevel", use_container_width=True, type="primary" if st.session_state.mode == "Min Toll €" else "secondary"):
        st.session_state.mode = "Min Toll €"

mode = st.session_state.mode

st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

# ===== MAIN LAYOUT =====
col_left, col_right = st.columns([1, 1], gap="large")

# Default financing assumptions
dscr_target = 1.8
tenor = 10
base_rate = 3.5
spread = 175
debt_rate = base_rate + spread/100
sculpting = False
deg_on = True
deg_rate = 2.5

with col_left:
    # Project inputs
    st.markdown("<div class='section-card'><div class='section-title'>Project</div>", unsafe_allow_html=True)
    pc1, pc2 = st.columns(2)
    with pc1:
        capex = st.number_input("CapEx (€k/MW)", value=600, min_value=300, max_value=1000, step=25)
    with pc2:
        opex = st.number_input("Opex (€k/yr)", value=7, min_value=3, max_value=20)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Structure inputs
    st.markdown("<div class='section-card'><div class='section-title'>Structure</div>", unsafe_allow_html=True)
    
    # Gearing
    if mode == "Max Gearing":
        st.markdown("<div class='solving-box'><span class='solving-label'>Gearing %</span><span class='solving-badge'>→ SOLVING</span></div>", unsafe_allow_html=True)
        gearing = 55
    else:
        gearing = st.slider("Gearing %", 0, 85, 55)
    
    # Toll Coverage
    if mode == "Min Toll %":
        st.markdown("<div class='solving-box'><span class='solving-label'>Toll Coverage %</span><span class='solving-badge'>→ SOLVING</span></div>", unsafe_allow_html=True)
        toll_pct = 75
    else:
        toll_pct = st.slider("Toll Coverage %", 0, 100, 75)
    
    # Toll Level
    if mode == "Min Toll €":
        st.markdown("<div class='solving-box'><span class='solving-label'>Toll Level €k/MW/yr</span><span class='solving-badge'>→ SOLVING</span></div>", unsafe_allow_html=True)
        toll_level = 95
    else:
        toll_level = st.slider("Toll Level (€k/MW/yr)", 50, 200, 95)
        pct_of_p50 = (toll_level / REVENUE['P50'][2026]) * 100
        st.caption(f"= {pct_of_p50:.0f}% of Year 1 P50")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Options
    st.markdown("<div class='section-card'><div class='section-title'>Options</div>", unsafe_allow_html=True)
    sculpting = st.checkbox("Sculpted debt service", value=False)
    deg_on = st.checkbox("Capacity degradation (2.5%/yr)", value=True)
    deg_rate = 2.5 if deg_on else 0
    
    with st.expander("Financing assumptions"):
        fc1, fc2 = st.columns(2)
        with fc1:
            dscr_target = st.number_input("Target DSCR", value=1.8, min_value=1.0, max_value=3.0, step=0.1)
            tenor = st.number_input("Tenor (years)", value=10, min_value=5, max_value=15)
        with fc2:
            spread = st.number_input("Credit spread (bps)", value=175, min_value=100, max_value=350, step=25)
            debt_rate = base_rate + spread/100
            st.markdown(f"**All-in rate:** {debt_rate:.2f}%")
    
    st.markdown("</div>", unsafe_allow_html=True)

# ===== CALCULATE =====
if mode == "Manual":
    r = calculate(capex, opex, gearing, toll_pct, toll_level, dscr_target, debt_rate, tenor, sculpting, deg_on, deg_rate)
elif mode == "Max Gearing":
    r = find_max_gearing(capex, opex, toll_pct, toll_level, dscr_target, debt_rate, tenor, sculpting, deg_on, deg_rate)
elif mode == "Min Toll %":
    r = find_min_toll_pct(capex, opex, gearing, toll_level, dscr_target, debt_rate, tenor, sculpting, deg_on, deg_rate)
else:
    r = find_min_toll_level(capex, opex, gearing, toll_pct, dscr_target, debt_rate, tenor, sculpting, deg_on, deg_rate)

if not r:
    st.error("Invalid structure - equity cannot be zero")
    st.stop()

# ===== RIGHT COLUMN =====
with col_right:
    # Hero card
    hero_class = "hero-card" if r['bankable'] else "hero-card not-bankable"
    status = "✓ Bankable" if r['bankable'] else "✗ Not Bankable"
    
    st.markdown(f"""
    <div class="{hero_class}">
        <div>
            <div class="hero-status">{status} at {r['gearing']:.0f}% gearing</div>
            <div class="hero-sub">{r['toll_pct']:.0f}% toll @ €{r['toll_level']:.0f}k · DSCR: {r['min_dscr']:.2f}x</div>
        </div>
        <div>
            <div class="hero-irr-label">P50 Equity IRR</div>
            <div class="hero-irr">{r['p50']['irr']:.1f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics row
    st.markdown(f"""
    <div class="metrics-row">
        <div class="metric-box"><div class="metric-value">€{r['equity']:.0f}k</div><div class="metric-label">Equity</div></div>
        <div class="metric-box"><div class="metric-value">{r['unlev_irr']:.1f}%</div><div class="metric-label">Unlev IRR</div></div>
        <div class="metric-box"><div class="metric-value">{r['p99']['irr']:.1f}%</div><div class="metric-label">P99 IRR</div></div>
        <div class="metric-box"><div class="metric-value">{r['p1']['irr']:.1f}%</div><div class="metric-label">P1 IRR</div></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Financing Summary
    st.markdown("<div class='section-card'><div class='section-title'>Financing Summary</div>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="fin-grid">
        <div class="fin-box"><div class="fin-label">Debt</div><div class="fin-value">€{r['debt']:.0f}k</div></div>
        <div class="fin-box"><div class="fin-label">Equity</div><div class="fin-value">€{r['equity']:.0f}k</div></div>
        <div class="fin-box"><div class="fin-label">Debt Service</div><div class="fin-value">€{r['avg_ds']:.1f}k/yr</div></div>
        <div class="fin-box"><div class="fin-label">Variance</div><div class="fin-value">{r['variance']:.0f}%</div></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='irr-section-title'>Equity IRR by Scenario</div>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="irr-row p99"><span class="irr-label p99">P99 (Stress)</span><span class="irr-value p99">{r['p99']['irr']:.1f}%</span></div>
    <div class="irr-row p50"><span class="irr-label p50">P50 (Base)</span><span class="irr-value p50">{r['p50']['irr']:.1f}%</span></div>
    <div class="irr-row p1"><span class="irr-label p1">P1 (Upside)</span><span class="irr-value p1">{r['p1']['irr']:.1f}%</span></div>
    """, unsafe_allow_html=True)
    
    lev_effect = r['p50']['irr'] - r['unlev_irr']
    st.markdown(f"""
    <div class="leverage-box">
        <div class="leverage-title">Leverage Effect</div>
        <div class="leverage-text">Unlevered: {r['unlev_irr']:.1f}% → Levered: {r['p50']['irr']:.1f}% ({'+' if lev_effect >= 0 else ''}{lev_effect:.1f}%)</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ===== BANKABILITY MAP =====
st.markdown("<div class='section-card'><div class='section-title'>Bankability Map</div>", unsafe_allow_html=True)
st.caption(f"At €{r['toll_level']:.0f}k toll level")

pts = []
for g in range(10, 86, 5):
    for tp in range(0, 101, 10):
        c = calculate(capex, opex, g, tp, r['toll_level'], dscr_target, debt_rate, tenor, sculpting, deg_on, deg_rate)
        if c: pts.append({'g': g, 'tp': tp, 'ok': c['bankable'], 'irr': c['p50']['irr'], 'dscr': c['min_dscr']})

df = pd.DataFrame(pts)
fig = go.Figure()

# Modo-style colors for chart
nb = df[~df['ok']]
if len(nb):
    fig.add_trace(go.Scatter(x=nb['tp'], y=nb['g'], mode='markers', name='Not bankable',
        marker=dict(color='#fca5a5', size=14), hoverinfo='skip'))

bk = df[df['ok']]
if len(bk):
    fig.add_trace(go.Scatter(x=bk['tp'], y=bk['g'], mode='markers', name='Bankable',
        marker=dict(color='#6ee7b7', size=14), hoverinfo='skip'))

fig.add_trace(go.Scatter(x=[r['toll_pct']], y=[r['gearing']], mode='markers', name='You',
    marker=dict(color='#1a1a2e', size=18, symbol='star')))

fig.update_layout(
    height=320, 
    margin=dict(l=60, r=20, t=20, b=60),
    xaxis=dict(title='Toll Coverage %', range=[-5, 105], tickfont=dict(family='DM Sans', size=11), titlefont=dict(family='DM Sans', size=12)),
    yaxis=dict(title='Gearing %', range=[0, 90], tickfont=dict(family='DM Sans', size=11), titlefont=dict(family='DM Sans', size=12)),
    legend=dict(orientation='h', yanchor='bottom', y=1.02, font=dict(family='DM Sans', size=11)),
    plot_bgcolor='white',
    font=dict(family='DM Sans')
)

st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("<div class='footer'>Modo Energy · German BESS Forecasts 2026–2035 · Educational purposes only · Not financial advice</div>", unsafe_allow_html=True)
