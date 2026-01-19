"""
Battery Toll Calculator v2.1
Modo Energy - German BESS Educational Tool

Fixes:
- Plotly titlefont deprecation (now uses title_font)
- Performance optimization with caching
- Improved bankability map visualization
- Polished UI/UX
"""

import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import plotly.graph_objects as go

# ============================================================================
# PAGE CONFIG - Must be first Streamlit command
# ============================================================================
st.set_page_config(
    page_title="Battery Toll Calculator | Modo Energy",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# CUSTOM CSS - Modo Energy Brand Styling
# ============================================================================
st.markdown("""
<style>
    /* Import DM Sans */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    
    /* Global font */
    html, body, [class*="css"], .stMarkdown, p, div, span, label {
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Hide Streamlit chrome */
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding: 1.25rem 2rem 2rem 2rem; max-width: 1150px;}
    
    /* Title area */
    .main-title {
        font-size: 1.6rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.15rem;
        letter-spacing: -0.025em;
    }
    .subtitle {
        font-size: 0.85rem;
        color: #64748b;
        margin-bottom: 0.75rem;
    }
    .brand-text {
        font-size: 0.85rem;
        color: #0d9488;
        font-weight: 600;
    }
    
    /* Mode selector - pill style */
    .mode-container {
        display: inline-flex;
        background: #f1f5f9;
        border-radius: 10px;
        padding: 4px;
        gap: 4px;
        margin-bottom: 1rem;
    }
    
    /* Section cards */
    .section-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.1rem 1.25rem;
        border: 1px solid #e2e8f0;
        margin-bottom: 0.85rem;
    }
    .section-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: #334155;
        margin-bottom: 0.85rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #f1f5f9;
    }
    
    /* Hero card - bankable */
    .hero-card {
        background: linear-gradient(135deg, #10b981 0%, #0d9488 100%);
        border-radius: 12px;
        padding: 1.1rem 1.25rem;
        color: white;
        margin-bottom: 0.85rem;
    }
    .hero-card.not-bankable {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    }
    .hero-status {
        font-size: 1.15rem;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    .hero-detail {
        font-size: 0.8rem;
        opacity: 0.9;
    }
    .hero-irr-label {
        font-size: 0.7rem;
        opacity: 0.85;
        text-align: right;
    }
    .hero-irr-value {
        font-size: 2rem;
        font-weight: 700;
        text-align: right;
        line-height: 1.1;
    }
    
    /* Metric boxes */
    .metrics-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.6rem;
        margin-bottom: 0.85rem;
    }
    .metric-box {
        background: #f8fafc;
        border-radius: 8px;
        padding: 0.7rem 0.85rem;
        text-align: center;
        border: 1px solid #e2e8f0;
    }
    .metric-value {
        font-size: 1.15rem;
        font-weight: 700;
        color: #1e293b;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 0.65rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        margin-top: 0.15rem;
    }
    
    /* Financing summary */
    .fin-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.6rem;
    }
    .fin-box {
        background: #f8fafc;
        border-radius: 8px;
        padding: 0.65rem 0.85rem;
        border: 1px solid #e2e8f0;
    }
    .fin-label {
        font-size: 0.7rem;
        color: #64748b;
    }
    .fin-value {
        font-size: 1.05rem;
        font-weight: 600;
        color: #1e293b;
    }
    
    /* IRR scenario rows */
    .irr-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: #334155;
        margin-bottom: 0.5rem;
        margin-top: 0.85rem;
    }
    .irr-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.6rem 0.85rem;
        border-radius: 8px;
        margin-bottom: 0.35rem;
    }
    .irr-row.p99 { background: #fef2f2; }
    .irr-row.p50 { background: #ecfdf5; }
    .irr-row.p1 { background: #f0fdf4; }
    .irr-label {
        font-size: 0.8rem;
        font-weight: 500;
    }
    .irr-label.p99 { color: #dc2626; }
    .irr-label.p50 { color: #059669; }
    .irr-label.p1 { color: #16a34a; }
    .irr-value {
        font-size: 1rem;
        font-weight: 700;
    }
    .irr-value.p99 { color: #dc2626; }
    .irr-value.p50 { color: #059669; }
    .irr-value.p1 { color: #16a34a; }
    
    /* Leverage box */
    .leverage-box {
        background: #fefce8;
        border-radius: 8px;
        padding: 0.75rem 0.85rem;
        margin-top: 0.6rem;
        border: 1px solid #fef08a;
    }
    .leverage-title {
        font-size: 0.7rem;
        font-weight: 600;
        color: #a16207;
    }
    .leverage-text {
        font-size: 0.8rem;
        color: #854d0e;
    }
    
    /* Solving badge */
    .solving-box {
        background: #eff6ff;
        border: 2px solid #3b82f6;
        border-radius: 8px;
        padding: 0.55rem 0.85rem;
        margin-bottom: 0.6rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .solving-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #1e40af;
    }
    .solving-badge {
        background: #3b82f6;
        color: white;
        font-size: 0.6rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 5px;
        letter-spacing: 0.04em;
    }
    
    /* Slider styling */
    div[data-testid="stSlider"] {
        padding-top: 0 !important;
        padding-bottom: 0.5rem !important;
    }
    div[data-testid="stSlider"] label p {
        font-size: 0.8rem !important;
        color: #475569 !important;
        margin-bottom: 0.15rem !important;
    }
    
    /* Number input */
    div[data-testid="stNumberInput"] label p {
        font-size: 0.8rem !important;
        color: #475569 !important;
    }
    div[data-testid="stNumberInput"] input {
        font-size: 0.9rem !important;
    }
    
    /* Checkbox */
    div[data-testid="stCheckbox"] label p {
        font-size: 0.8rem !important;
        color: #475569 !important;
    }
    
    /* Expander */
    div[data-testid="stExpander"] summary p {
        font-size: 0.85rem !important;
        font-weight: 500 !important;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        font-size: 0.7rem;
        color: #94a3b8;
        margin-top: 1rem;
        padding-top: 0.75rem;
        border-top: 1px solid #f1f5f9;
    }
    
    /* Reduce spacing globally */
    .stVerticalBlock > div {
        gap: 0.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA - German BESS Revenue Forecasts (€k/MW/yr)
# ============================================================================
REVENUE_DATA = {
    'year': list(range(2026, 2036)),
    'p10': [85, 78, 72, 68, 65, 63, 61, 59, 58, 57],
    'p50': [115, 108, 102, 97, 93, 90, 87, 85, 83, 81],
    'p90': [155, 145, 138, 132, 127, 123, 119, 116, 113, 110]
}

# ============================================================================
# FINANCIAL MODEL - Cached for performance
# ============================================================================
@st.cache_data
def calculate_project(capex, opex, gearing, toll_pct, toll_level, dscr_target, debt_rate, tenor, sculpted, deg_on, deg_rate):
    """Calculate project financials with caching for performance."""
    years = REVENUE_DATA['year']
    n_years = len(years)
    
    # Degradation factor
    deg_factors = [(1 - deg_rate) ** i if deg_on else 1.0 for i in range(n_years)]
    
    # Apply degradation to revenues
    p10_rev = [REVENUE_DATA['p10'][i] * deg_factors[i] for i in range(n_years)]
    p50_rev = [REVENUE_DATA['p50'][i] * deg_factors[i] for i in range(n_years)]
    p90_rev = [REVENUE_DATA['p90'][i] * deg_factors[i] for i in range(n_years)]
    
    # Toll vs merchant split
    toll_frac = toll_pct / 100
    
    # Total revenues (toll portion is fixed, merchant portion varies)
    def calc_total_rev(merchant_rev):
        return [toll_level * toll_frac + merchant_rev[i] * (1 - toll_frac) for i in range(n_years)]
    
    total_p10 = calc_total_rev(p10_rev)
    total_p50 = calc_total_rev(p50_rev)
    total_p90 = calc_total_rev(p90_rev)
    
    # Financing
    total_capex = capex * 1000  # €k/MW to €/MW
    debt = total_capex * (gearing / 100)
    equity = total_capex - debt
    
    # Debt service calculation
    if sculpted:
        # Sculpted: debt service profiled to maintain constant DSCR against declining P50
        net_cf_p50 = [total_p50[i] * 1000 - opex * 1000 for i in range(n_years)]
        total_debt_capacity = sum([cf / dscr_target for cf in net_cf_p50[:tenor]])
        
        if total_debt_capacity <= 0:
            return None
        
        scale = min(1.0, debt / total_debt_capacity)
        debt_service = [(net_cf_p50[i] / dscr_target) * scale if i < tenor else 0 for i in range(n_years)]
    else:
        # Flat amortization
        if tenor <= 0:
            return None
        annual_rate = debt_rate / 100
        if annual_rate > 0:
            pmt = debt * (annual_rate * (1 + annual_rate) ** tenor) / ((1 + annual_rate) ** tenor - 1)
        else:
            pmt = debt / tenor
        debt_service = [pmt if i < tenor else 0 for i in range(n_years)]
    
    # Calculate cashflows and metrics for each scenario
    def calc_scenario(total_rev):
        net_cf = [(total_rev[i] * 1000 - opex * 1000) for i in range(n_years)]
        equity_cf = [net_cf[i] - debt_service[i] for i in range(n_years)]
        
        # DSCR by year
        dscr = [net_cf[i] / debt_service[i] if debt_service[i] > 0 else 99 for i in range(n_years)]
        min_dscr = min([d for d in dscr if d < 99]) if any(d < 99 for d in dscr) else 99
        
        # IRR calculation
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
    
    # Unlevered IRR (P50, no debt)
    unlev_cf = [-total_capex] + [(total_p50[i] * 1000 - opex * 1000) for i in range(n_years)]
    unlev_irr = npf.irr(unlev_cf) * 100
    
    # Bankability check
    bankable = p10_result['min_dscr'] >= dscr_target
    
    return {
        'bankable': bankable,
        'gearing': gearing,
        'toll_pct': toll_pct,
        'toll_level': toll_level,
        'debt': debt / 1000,
        'equity': equity / 1000,
        'debt_service': sum(debt_service[:tenor]) / tenor / 1000 if tenor > 0 else 0,
        'unlev_irr': unlev_irr if not np.isnan(unlev_irr) else 0,
        'min_dscr': p10_result['min_dscr'],
        'p99': {'irr': p10_result['irr'], 'min_dscr': p10_result['min_dscr']},
        'p50': {'irr': p50_result['irr'], 'min_dscr': p50_result['min_dscr']},
        'p1': {'irr': p90_result['irr'], 'min_dscr': p90_result['min_dscr']},
        'variance': (p90_result['irr'] - p10_result['irr']) if p90_result['irr'] > -50 and p10_result['irr'] > -50 else 0
    }

@st.cache_data
def find_max_gearing(capex, opex, toll_pct, toll_level, dscr_target, debt_rate, tenor, sculpted, deg_on, deg_rate):
    """Binary search for maximum bankable gearing."""
    lo, hi = 0, 85
    best = 0
    for _ in range(20):
        mid = (lo + hi) / 2
        result = calculate_project(capex, opex, mid, toll_pct, toll_level, dscr_target, debt_rate, tenor, sculpted, deg_on, deg_rate)
        if result and result['bankable']:
            best = mid
            lo = mid
        else:
            hi = mid
    return round(best, 1)

@st.cache_data
def find_min_toll_pct(capex, opex, gearing, toll_level, dscr_target, debt_rate, tenor, sculpted, deg_on, deg_rate):
    """Binary search for minimum toll percentage."""
    lo, hi = 0, 100
    best = 100
    for _ in range(20):
        mid = (lo + hi) / 2
        result = calculate_project(capex, opex, gearing, mid, toll_level, dscr_target, debt_rate, tenor, sculpted, deg_on, deg_rate)
        if result and result['bankable']:
            best = mid
            hi = mid
        else:
            lo = mid
    return round(best, 1)

@st.cache_data
def find_min_toll_level(capex, opex, gearing, toll_pct, dscr_target, debt_rate, tenor, sculpted, deg_on, deg_rate):
    """Binary search for minimum toll level (€k/MW/yr)."""
    lo, hi = 50, 200
    best = 200
    for _ in range(20):
        mid = (lo + hi) / 2
        result = calculate_project(capex, opex, gearing, toll_pct, mid, dscr_target, debt_rate, tenor, sculpted, deg_on, deg_rate)
        if result and result['bankable']:
            best = mid
            hi = mid
        else:
            lo = mid
    return round(best, 1)

@st.cache_data
def generate_bankability_map(capex, opex, toll_level, dscr_target, debt_rate, tenor, sculpted, deg_on, deg_rate):
    """Generate bankability map data points."""
    points = []
    for g in range(10, 86, 5):
        for tp in range(0, 101, 10):
            result = calculate_project(capex, opex, g, tp, toll_level, dscr_target, debt_rate, tenor, sculpted, deg_on, deg_rate)
            if result:
                points.append({
                    'gearing': g,
                    'toll_pct': tp,
                    'bankable': result['bankable'],
                    'irr': result['p50']['irr'],
                    'dscr': result['min_dscr']
                })
    return pd.DataFrame(points)

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
# MODE SELECTOR - Using native Streamlit for better performance
# ============================================================================
mode = st.radio(
    "Select mode",
    options=["Manual", "Max Gearing", "Min Toll %", "Min Toll €"],
    horizontal=True,
    label_visibility="collapsed"
)

# ============================================================================
# MAIN LAYOUT - Two columns
# ============================================================================
left_col, right_col = st.columns([1, 1.15], gap="medium")

# ============================================================================
# LEFT COLUMN - INPUTS
# ============================================================================
with left_col:
    # Project section
    st.markdown("<div class='section-card'><div class='section-title'>Project</div>", unsafe_allow_html=True)
    proj_cols = st.columns(2)
    with proj_cols[0]:
        capex = st.number_input("CapEx (€k/MW)", min_value=300, max_value=1000, value=600, step=25)
    with proj_cols[1]:
        opex = st.number_input("Opex (€k/yr)", min_value=0, max_value=30, value=7, step=1)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Structure section
    st.markdown("<div class='section-card'><div class='section-title'>Structure</div>", unsafe_allow_html=True)
    
    # Default financing assumptions
    dscr_target = 1.80
    debt_rate = 6.5
    tenor = 10
    
    # Mode-specific logic
    if mode == "Max Gearing":
        st.markdown("""
            <div class='solving-box'>
                <span class='solving-label'>Gearing %</span>
                <span class='solving-badge'>→ SOLVING</span>
            </div>
        """, unsafe_allow_html=True)
        toll_pct = st.slider("Toll Coverage %", 0, 100, 65)
        toll_level = st.slider("Toll Level (€k/MW/yr)", 50, 150, 95)
    elif mode == "Min Toll %":
        gearing = st.slider("Gearing %", 10, 85, 45)
        st.markdown("""
            <div class='solving-box'>
                <span class='solving-label'>Toll Coverage %</span>
                <span class='solving-badge'>→ SOLVING</span>
            </div>
        """, unsafe_allow_html=True)
        toll_level = st.slider("Toll Level (€k/MW/yr)", 50, 150, 95)
    elif mode == "Min Toll €":
        gearing = st.slider("Gearing %", 10, 85, 45)
        toll_pct = st.slider("Toll Coverage %", 0, 100, 65)
        st.markdown("""
            <div class='solving-box'>
                <span class='solving-label'>Toll Level (€k/MW/yr)</span>
                <span class='solving-badge'>→ SOLVING</span>
            </div>
        """, unsafe_allow_html=True)
    else:  # Manual
        gearing = st.slider("Gearing %", 10, 85, 45)
        toll_pct = st.slider("Toll Coverage %", 0, 100, 65)
        toll_level = st.slider("Toll Level (€k/MW/yr)", 50, 150, 95)
    
    # Show toll as % of Year 1 P50
    if mode != "Min Toll €":
        year1_p50 = REVENUE_DATA['p50'][0]
        toll_pct_of_p50 = (toll_level / year1_p50) * 100
        st.caption(f"= {toll_pct_of_p50:.0f}% of Year 1 P50")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Options section
    st.markdown("<div class='section-card'><div class='section-title'>Options</div>", unsafe_allow_html=True)
    sculpted = st.checkbox("Sculpted debt service", value=True)
    deg_on = st.checkbox("Capacity degradation (2.5%/yr)", value=True)
    deg_rate = 0.025
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Financing assumptions (collapsible)
    with st.expander("Financing assumptions"):
        fin_cols = st.columns(3)
        with fin_cols[0]:
            dscr_target = st.number_input("DSCR Target", min_value=1.0, max_value=3.0, value=1.80, step=0.05, format="%.2f")
        with fin_cols[1]:
            debt_rate = st.number_input("Debt Rate %", min_value=3.0, max_value=12.0, value=6.5, step=0.25, format="%.2f")
        with fin_cols[2]:
            tenor = st.number_input("Tenor (yrs)", min_value=5, max_value=15, value=10, step=1)

# ============================================================================
# SOLVE FOR OPTIMIZED VALUES
# ============================================================================
if mode == "Max Gearing":
    gearing = find_max_gearing(capex, opex, toll_pct, toll_level, dscr_target, debt_rate, tenor, sculpted, deg_on, deg_rate)
elif mode == "Min Toll %":
    toll_pct = find_min_toll_pct(capex, opex, gearing, toll_level, dscr_target, debt_rate, tenor, sculpted, deg_on, deg_rate)
elif mode == "Min Toll €":
    toll_level = find_min_toll_level(capex, opex, gearing, toll_pct, dscr_target, debt_rate, tenor, sculpted, deg_on, deg_rate)

# Calculate final result
result = calculate_project(capex, opex, gearing, toll_pct, toll_level, dscr_target, debt_rate, tenor, sculpted, deg_on, deg_rate)

# ============================================================================
# RIGHT COLUMN - RESULTS
# ============================================================================
with right_col:
    if result:
        # Hero card
        bankable_class = "" if result['bankable'] else "not-bankable"
        status_text = f"✓ Bankable at {gearing:.0f}% gearing" if result['bankable'] else f"✗ Not bankable at {gearing:.0f}% gearing"
        detail_text = f"{toll_pct:.0f}% toll @ €{toll_level:.0f}k · DSCR: {result['min_dscr']:.2f}x"
        
        st.markdown(f"""
        <div class='hero-card {bankable_class}'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <div class='hero-status'>{status_text}</div>
                    <div class='hero-detail'>{detail_text}</div>
                </div>
                <div>
                    <div class='hero-irr-label'>P50 Equity IRR</div>
                    <div class='hero-irr-value'>{result['p50']['irr']:.1f}%</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Metrics row
        st.markdown(f"""
        <div class='metrics-row'>
            <div class='metric-box'>
                <div class='metric-value'>€{result['equity']:.0f}k</div>
                <div class='metric-label'>Equity</div>
            </div>
            <div class='metric-box'>
                <div class='metric-value'>{result['unlev_irr']:.1f}%</div>
                <div class='metric-label'>Unlev IRR</div>
            </div>
            <div class='metric-box'>
                <div class='metric-value'>{result['p99']['irr']:.1f}%</div>
                <div class='metric-label'>P99 IRR</div>
            </div>
            <div class='metric-box'>
                <div class='metric-value'>{result['p1']['irr']:.1f}%</div>
                <div class='metric-label'>P1 IRR</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Financing Summary
        st.markdown(f"""
        <div class='section-card'>
            <div class='section-title'>Financing Summary</div>
            <div class='fin-grid'>
                <div class='fin-box'>
                    <div class='fin-label'>Debt</div>
                    <div class='fin-value'>€{result['debt']:.0f}k</div>
                </div>
                <div class='fin-box'>
                    <div class='fin-label'>Equity</div>
                    <div class='fin-value'>€{result['equity']:.0f}k</div>
                </div>
                <div class='fin-box'>
                    <div class='fin-label'>Debt Service</div>
                    <div class='fin-value'>€{result['debt_service']:.1f}k/yr</div>
                </div>
                <div class='fin-box'>
                    <div class='fin-label'>Variance</div>
                    <div class='fin-value'>{result['variance']:.0f}%</div>
                </div>
            </div>
            
            <div class='irr-title'>Equity IRR by Scenario</div>
            <div class='irr-row p99'>
                <span class='irr-label p99'>P99 (Stress)</span>
                <span class='irr-value p99'>{result['p99']['irr']:.1f}%</span>
            </div>
            <div class='irr-row p50'>
                <span class='irr-label p50'>P50 (Base)</span>
                <span class='irr-value p50'>{result['p50']['irr']:.1f}%</span>
            </div>
            <div class='irr-row p1'>
                <span class='irr-label p1'>P1 (Upside)</span>
                <span class='irr-value p1'>{result['p1']['irr']:.1f}%</span>
            </div>
            
            <div class='leverage-box'>
                <div class='leverage-title'>Leverage Effect</div>
                <div class='leverage-text'>Unlevered: {result['unlev_irr']:.1f}% → Levered: {result['p50']['irr']:.1f}% ({'+' if result['p50']['irr'] - result['unlev_irr'] >= 0 else ''}{result['p50']['irr'] - result['unlev_irr']:.1f}%)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Bankability Map
        st.markdown("<div class='section-card'><div class='section-title'>Bankability Map</div>", unsafe_allow_html=True)
        st.caption(f"At €{toll_level:.0f}k toll level")
        
        # Generate map data
        df = generate_bankability_map(capex, opex, toll_level, dscr_target, debt_rate, tenor, sculpted, deg_on, deg_rate)
        
        # Create figure
        fig = go.Figure()
        
        # Not bankable points
        not_bankable = df[~df['bankable']]
        if len(not_bankable) > 0:
            fig.add_trace(go.Scatter(
                x=not_bankable['toll_pct'],
                y=not_bankable['gearing'],
                mode='markers',
                name='Not bankable',
                marker=dict(color='#fca5a5', size=16, line=dict(width=1, color='#fecaca')),
                hovertemplate='Gearing: %{y}%<br>Toll: %{x}%<extra></extra>'
            ))
        
        # Bankable points
        bankable = df[df['bankable']]
        if len(bankable) > 0:
            fig.add_trace(go.Scatter(
                x=bankable['toll_pct'],
                y=bankable['gearing'],
                mode='markers',
                name='Bankable',
                marker=dict(color='#86efac', size=16, line=dict(width=1, color='#bbf7d0')),
                hovertemplate='Gearing: %{y}%<br>Toll: %{x}%<br>IRR: %{customdata:.1f}%<extra></extra>',
                customdata=bankable['irr']
            ))
        
        # Current position
        fig.add_trace(go.Scatter(
            x=[toll_pct],
            y=[gearing],
            mode='markers',
            name='Current',
            marker=dict(color='#1e40af', size=20, symbol='star', line=dict(width=2, color='white')),
            hovertemplate=f'<b>Your position</b><br>Gearing: {gearing:.0f}%<br>Toll: {toll_pct:.0f}%<extra></extra>'
        ))
        
        # Layout - FIXED: Using title_font instead of deprecated titlefont
        fig.update_layout(
            height=280,
            margin=dict(l=50, r=20, t=10, b=50),
            xaxis=dict(
                title=dict(text='Toll Coverage %', font=dict(family='DM Sans', size=12)),
                range=[-5, 105],
                tickfont=dict(family='DM Sans', size=11),
                gridcolor='#f1f5f9',
                zeroline=False
            ),
            yaxis=dict(
                title=dict(text='Gearing %', font=dict(family='DM Sans', size=12)),
                range=[5, 90],
                tickfont=dict(family='DM Sans', size=11),
                gridcolor='#f1f5f9',
                zeroline=False
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='left',
                x=0,
                font=dict(family='DM Sans', size=10)
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family='DM Sans'),
            hoverlabel=dict(font=dict(family='DM Sans'))
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.error("Unable to calculate. Check inputs.")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("<div class='footer'>Modo Energy · German BESS Forecasts 2026–2035 · Educational purposes only · Not financial advice</div>", unsafe_allow_html=True)
