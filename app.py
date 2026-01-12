"""
Battery Toll Calculator - Compact Version
Modo Energy - For article embedding

Focused on: inputs → key results → bankability map
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Page config - compact
st.set_page_config(
    page_title="Toll Calculator | Modo Energy",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Clean CSS
st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding: 1rem 1rem 0rem 1rem; max-width: 700px;}
    
    h1 {font-size: 1.3rem !important; margin-bottom: 0.5rem !important;}
    
    .stRadio > div {flex-direction: row; gap: 0.5rem;}
    .stRadio > div > label {
        background: #f1f5f9; padding: 0.4rem 0.8rem; border-radius: 6px;
        font-size: 0.8rem; cursor: pointer;
    }
    .stRadio > div > label[data-checked="true"] {
        background: #1e293b; color: white;
    }
    
    .result-card {
        border-radius: 10px; padding: 1rem; margin: 0.75rem 0;
        display: flex; justify-content: space-between; align-items: center;
    }
    .result-card.bankable {background: linear-gradient(135deg, #10b981, #14b8a6); color: white;}
    .result-card.not-bankable {background: linear-gradient(135deg, #ef4444, #f97316); color: white;}
    
    .metric-row {
        display: flex; gap: 0.5rem; margin: 0.5rem 0;
    }
    .metric-box {
        flex: 1; background: #f8fafc; border-radius: 6px; padding: 0.5rem;
        text-align: center; font-size: 0.75rem;
    }
    .metric-box .value {font-size: 1.1rem; font-weight: 600; color: #1e293b;}
    .metric-box .label {color: #64748b; font-size: 0.65rem;}
    
    div[data-testid="stSlider"] {padding: 0;}
    .stSlider p {font-size: 0.75rem !important; margin-bottom: 0.2rem !important;}
</style>
""", unsafe_allow_html=True)

# Revenue data
REVENUE = {
    'P99': {2026: 159.1, 2027: 101.2, 2028: 83.3, 2029: 77.9, 2030: 72.9, 
            2031: 71.4, 2032: 70.0, 2033: 68.6, 2034: 67.2, 2035: 65.9},
    'P50': {2026: 256.0, 2027: 161.6, 2028: 129.4, 2029: 123.4, 2030: 116.4,
            2031: 114.1, 2032: 111.8, 2033: 109.6, 2034: 107.4, 2035: 105.2},
    'P1':  {2026: 333.1, 2027: 209.0, 2028: 164.6, 2029: 157.6, 2030: 149.2,
            2031: 146.2, 2032: 143.3, 2033: 140.4, 2034: 137.6, 2035: 134.9}
}

# Fixed assumptions
CAPEX, OPEX, TENOR = 600, 7, 10
DSCR_TARGET, DEBT_RATE, DEG_RATE = 1.8, 5.25, 2.5

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

def calculate(gearing, toll_pct, toll_level):
    debt = CAPEX * gearing / 100
    equity = CAPEX - debt
    if equity <= 0: return None
    
    rate = DEBT_RATE / 100
    tp = toll_pct / 100
    
    # Flat amortising
    pmt = debt * (rate * (1+rate)**TENOR) / ((1+rate)**TENOR - 1) if debt > 0 else 0
    
    def scenario_irr(revs):
        cfs = [-equity]
        min_dscr = 999
        for i in range(TENOR):
            yr = 2026 + i
            rev = revs.get(yr, revs[2035])
            deg = (1 - DEG_RATE/100)**i
            cfads = toll_level * tp + rev * (1-tp) * deg - OPEX
            dscr = cfads / pmt if pmt > 0 else 999
            min_dscr = min(min_dscr, dscr)
            cfs.append(max(0, cfads - pmt))
        return calc_irr(cfs), min_dscr
    
    p99_irr, min_dscr = scenario_irr(REVENUE['P99'])
    p50_irr, _ = scenario_irr(REVENUE['P50'])
    p1_irr, _ = scenario_irr(REVENUE['P1'])
    
    # Unlevered
    unlev_cfs = [-CAPEX]
    for i in range(TENOR):
        yr = 2026 + i
        rev = REVENUE['P50'].get(yr, REVENUE['P50'][2035])
        deg = (1 - DEG_RATE/100)**i
        unlev_cfs.append(toll_level * tp + rev * (1-tp) * deg - OPEX)
    unlev_irr = calc_irr(unlev_cfs)
    
    return {
        'debt': debt, 'equity': equity, 'gearing': gearing,
        'toll_pct': toll_pct, 'toll_level': toll_level,
        'p99_irr': p99_irr, 'p50_irr': p50_irr, 'p1_irr': p1_irr,
        'unlev_irr': unlev_irr, 'min_dscr': min_dscr,
        'bankable': min_dscr >= DSCR_TARGET
    }

def find_max_gearing(tp, tl):
    for g in range(85, -1, -1):
        r = calculate(g, tp, tl)
        if r and r['bankable']: return r
    return calculate(0, tp, tl)

def find_min_toll_pct(g, tl):
    for tp in range(0, 101):
        r = calculate(g, tp, tl)
        if r and r['bankable']: return r
    return calculate(g, 100, tl)

def find_min_toll_level(g, tp):
    for tl in range(50, 201):
        r = calculate(g, tp, tl)
        if r and r['bankable']: return r
    return calculate(g, tp, 200)

# ===== UI =====

st.markdown("#### ⚡ Battery Toll Calculator")

# Mode as pills
mode = st.radio(
    "mode", ["Manual", "Max Gearing", "Min Toll %", "Min Toll €"],
    horizontal=True, label_visibility="collapsed"
)

# Compact inputs
c1, c2, c3 = st.columns(3)
with c1:
    gearing = st.slider("Gearing %", 0, 85, 55, disabled=(mode=="Max Gearing"))
with c2:
    toll_pct = st.slider("Toll Coverage %", 0, 100, 75, disabled=(mode=="Min Toll %"))
with c3:
    toll_level = st.slider("Toll €k/MW/yr", 50, 200, 95, disabled=(mode=="Min Toll €"))

# Calculate
if mode == "Manual":
    r = calculate(gearing, toll_pct, toll_level)
elif mode == "Max Gearing":
    r = find_max_gearing(toll_pct, toll_level)
elif mode == "Min Toll %":
    r = find_min_toll_pct(gearing, toll_level)
else:
    r = find_min_toll_level(gearing, toll_pct)

if not r:
    st.error("Invalid inputs")
    st.stop()

# Result card
status = "✓ Bankable" if r['bankable'] else "✗ Not Bankable"
card_class = "bankable" if r['bankable'] else "not-bankable"

st.markdown(f"""
<div class="result-card {card_class}">
    <div>
        <div style="font-size: 1.1rem; font-weight: 600;">{status} at {r['gearing']:.0f}% gearing</div>
        <div style="font-size: 0.75rem; opacity: 0.9;">{r['toll_pct']:.0f}% toll @ €{r['toll_level']:.0f}k • DSCR: {r['min_dscr']:.2f}x</div>
    </div>
    <div style="text-align: right;">
        <div style="font-size: 0.65rem; opacity: 0.8;">P50 Equity IRR</div>
        <div style="font-size: 1.8rem; font-weight: 700;">{r['p50_irr']:.1f}%</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Metrics row
st.markdown(f"""
<div class="metric-row">
    <div class="metric-box"><div class="value">€{r['equity']:.0f}k</div><div class="label">Equity</div></div>
    <div class="metric-box"><div class="value">{r['unlev_irr']:.1f}%</div><div class="label">Unlev IRR</div></div>
    <div class="metric-box"><div class="value">{r['p99_irr']:.1f}%</div><div class="label">P99 IRR</div></div>
    <div class="metric-box"><div class="value">{r['p1_irr']:.1f}%</div><div class="label">P1 IRR</div></div>
</div>
""", unsafe_allow_html=True)

# Bankability map - compact
st.markdown("<p style='font-size: 0.75rem; color: #64748b; margin: 0.75rem 0 0.25rem 0;'>Bankability Map (at €{:.0f}k toll)</p>".format(r['toll_level']), unsafe_allow_html=True)

pts = []
for g in range(10, 86, 5):
    for tp in range(0, 101, 10):
        c = calculate(g, tp, r['toll_level'])
        if c: pts.append({'g': g, 'tp': tp, 'ok': c['bankable'], 'irr': c['p50_irr']})

df = pd.DataFrame(pts)

fig = go.Figure()

# Not bankable
nb = df[~df['ok']]
if len(nb): 
    fig.add_trace(go.Scatter(x=nb['tp'], y=nb['g'], mode='markers', name='Not bankable',
        marker=dict(color='#fca5a5', size=10), hoverinfo='skip'))

# Bankable
bk = df[df['ok']]
if len(bk):
    fig.add_trace(go.Scatter(x=bk['tp'], y=bk['g'], mode='markers', name='Bankable',
        marker=dict(color='#86efac', size=10), hoverinfo='skip'))

# Current
fig.add_trace(go.Scatter(x=[r['toll_pct']], y=[r['gearing']], mode='markers', name='You',
    marker=dict(color='#1e40af', size=14, symbol='star')))

fig.update_layout(
    height=220, margin=dict(l=40, r=10, t=10, b=40),
    xaxis=dict(title='Toll Coverage %', range=[-5, 105], title_font_size=10, tickfont_size=9),
    yaxis=dict(title='Gearing %', range=[0, 90], title_font_size=10, tickfont_size=9),
    legend=dict(orientation='h', yanchor='bottom', y=1.02, font_size=9),
    showlegend=True
)

st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# Footer
st.markdown("<p style='font-size: 0.6rem; color: #94a3b8; text-align: center; margin-top: 0;'>Modo Energy • German BESS forecasts • Educational only</p>", unsafe_allow_html=True)
