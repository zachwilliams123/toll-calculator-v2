"""
Battery Toll Structure Calculator
Modo Energy - Educational Tool

Deploy to Streamlit Cloud, then embed in articles via iframe:
<iframe src="https://your-app.streamlit.app/?embed=true" width="100%" height="800" frameborder="0"></iframe>
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page config
st.set_page_config(
    page_title="Battery Toll Calculator | Modo Energy",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Modo branding
st.markdown("""
<style>
    /* Hide Streamlit branding for embed */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Modo colors */
    .stApp {
        background: linear-gradient(to bottom, #f8fafc, #f1f5f9);
    }
    
    .hero-card {
        background: linear-gradient(135deg, #10b981, #14b8a6);
        border-radius: 12px;
        padding: 20px;
        color: white;
        margin-bottom: 20px;
    }
    
    .hero-card.not-bankable {
        background: linear-gradient(135deg, #ef4444, #f97316);
    }
    
    .metric-box {
        background: #f8fafc;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    
    .solving-badge {
        background: #3b82f6;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Revenue data (German BESS forecasts)
REVENUE_DATA = {
    'P99': {2026: 159.1, 2027: 101.2, 2028: 83.3, 2029: 77.9, 2030: 72.9, 
            2031: 71.4, 2032: 70.0, 2033: 68.6, 2034: 67.2, 2035: 65.9},
    'P50': {2026: 256.0, 2027: 161.6, 2028: 129.4, 2029: 123.4, 2030: 116.4,
            2031: 114.1, 2032: 111.8, 2033: 109.6, 2034: 107.4, 2035: 105.2},
    'P1':  {2026: 333.1, 2027: 209.0, 2028: 164.6, 2029: 157.6, 2030: 149.2,
            2031: 146.2, 2032: 143.3, 2033: 140.4, 2034: 137.6, 2035: 134.9}
}

def calc_pmt(rate, nper, pv):
    """Calculate flat amortising payment"""
    if rate == 0 or nper == 0:
        return pv / max(nper, 1)
    r = rate / 100
    return pv * (r * (1 + r)**nper) / ((1 + r)**nper - 1)

def calc_irr(cash_flows, guess=0.1):
    """Calculate IRR using Newton-Raphson"""
    irr = guess
    for _ in range(100):
        npv = sum(cf / (1 + irr)**i for i, cf in enumerate(cash_flows))
        dnpv = sum(-i * cf / (1 + irr)**(i+1) for i, cf in enumerate(cash_flows))
        if abs(dnpv) < 0.0001:
            break
        new_irr = irr - npv / dnpv
        if abs(new_irr - irr) < 0.0001:
            return new_irr * 100
        if new_irr < -0.99 or new_irr > 10:
            return np.nan
        irr = new_irr
    return irr * 100

def calculate_structure(capex, opex, gearing, toll_pct, toll_level, 
                        dscr_target, debt_rate, tenor, sculpting, degradation_on, degradation_rate):
    """Core financial model calculation"""
    debt = capex * (gearing / 100)
    equity = capex - debt
    if equity <= 0 and gearing > 0:
        return None
    
    toll_pct_dec = toll_pct / 100
    rate = debt_rate / 100
    
    def get_cfads(scenario_revs, for_sculpting=False):
        profile = []
        for i in range(tenor):
            year = 2026 + i
            scenario_rev = scenario_revs.get(year, scenario_revs[2035])
            deg_factor = (1 - degradation_rate/100)**i if degradation_on else 1
            
            toll_rev = toll_level * toll_pct_dec  # Fixed toll
            merch_rev = scenario_rev * (1 - toll_pct_dec) * deg_factor
            total_rev = toll_rev + merch_rev
            cfads = total_rev - opex
            profile.append({
                'year': year, 'cfads': cfads, 'toll_rev': toll_rev,
                'merch_rev': merch_rev, 'total_rev': total_rev, 'deg_factor': deg_factor
            })
        return profile
    
    # Debt schedule
    p99_profile = get_cfads(REVENUE_DATA['P99'], True)
    debt_schedule = []
    remaining = debt
    
    if sculpting and debt > 0:
        for i in range(tenor):
            target_ds = p99_profile[i]['cfads'] / dscr_target
            interest = remaining * rate
            principal = min(max(0, target_ds - interest), remaining)
            remaining = max(0, remaining - principal)
            debt_schedule.append({'ds': interest + principal, 'interest': interest, 
                                  'principal': principal, 'remaining': remaining})
        if remaining > 0.01:
            debt_schedule[-1]['ds'] += remaining
            debt_schedule[-1]['principal'] += remaining
    else:
        flat_ds = calc_pmt(debt_rate, tenor, debt) if debt > 0 else 0
        for i in range(tenor):
            interest = remaining * rate
            principal = flat_ds - interest
            remaining = max(0, remaining - principal)
            debt_schedule.append({'ds': flat_ds, 'interest': interest,
                                  'principal': principal, 'remaining': remaining})
    
    avg_ds = sum(d['ds'] for d in debt_schedule) / tenor if debt > 0 else 0
    
    def calc_scenario(scenario_revs):
        profile = get_cfads(scenario_revs)
        total_distrib = 0
        min_dscr = 999
        yearly = []
        
        for i in range(tenor):
            p = profile[i]
            ds = debt_schedule[i]['ds'] if debt_schedule else 0
            dscr = p['cfads'] / ds if ds > 0 else 999
            to_equity = max(0, p['cfads'] - ds)
            min_dscr = min(min_dscr, dscr)
            total_distrib += to_equity
            yearly.append({**p, 'ds': ds, 'dscr': dscr, 'to_equity': to_equity})
        
        equity_cfs = [-equity] + [y['to_equity'] for y in yearly]
        levered_irr = calc_irr(equity_cfs) if equity > 0 else 0
        return {'total_distrib': total_distrib, 'min_dscr': min_dscr, 
                'levered_irr': levered_irr, 'yearly': yearly}
    
    # Unlevered IRR
    p50_profile = get_cfads(REVENUE_DATA['P50'])
    unlev_cfs = [-capex] + [p['cfads'] for p in p50_profile]
    unlevered_irr = calc_irr(unlev_cfs)
    
    p99 = calc_scenario(REVENUE_DATA['P99'])
    p50 = calc_scenario(REVENUE_DATA['P50'])
    p1 = calc_scenario(REVENUE_DATA['P1'])
    
    variance = ((p50['levered_irr'] - p99['levered_irr']) / p50['levered_irr'] * 100) if p50['levered_irr'] > 0 else 0
    bankable = p99['min_dscr'] >= dscr_target
    
    # Gap analysis
    gap_data = []
    for i in range(tenor):
        year = 2026 + i
        p50_rev = REVENUE_DATA['P50'].get(year, REVENUE_DATA['P50'][2035])
        p99_rev = REVENUE_DATA['P99'].get(year, REVENUE_DATA['P99'][2035])
        deg_factor = (1 - degradation_rate/100)**i if degradation_on else 1
        
        ceiling = p50_rev * 0.80
        ds = debt_schedule[i]['ds'] if debt_schedule else avg_ds
        required_cfads = ds * dscr_target
        merch_at_p99 = p99_rev * (1 - toll_pct_dec) * deg_factor
        required_toll = required_cfads + opex - merch_at_p99
        floor = required_toll / toll_pct_dec if toll_pct_dec > 0 else 0
        
        gap_data.append({'year': year, 'ceiling': ceiling, 'floor': max(0, floor), 'actual': toll_level})
    
    return {
        'debt': debt, 'equity': equity, 'avg_ds': avg_ds, 'debt_schedule': debt_schedule,
        'unlevered_irr': unlevered_irr, 'p99': p99, 'p50': p50, 'p1': p1,
        'variance': variance, 'bankable': bankable, 'min_dscr': p99['min_dscr'],
        'gearing': gearing, 'toll_pct': toll_pct, 'toll_level': toll_level,
        'gap_data': gap_data
    }

def find_optimal_gearing(capex, opex, toll_pct, toll_level, dscr_target, debt_rate, tenor, sculpting, deg_on, deg_rate):
    for g in range(85, -1, -1):
        result = calculate_structure(capex, opex, g, toll_pct, toll_level, dscr_target, debt_rate, tenor, sculpting, deg_on, deg_rate)
        if result and result['bankable']:
            return result
    return calculate_structure(capex, opex, 0, toll_pct, toll_level, dscr_target, debt_rate, tenor, sculpting, deg_on, deg_rate)

def find_optimal_toll_pct(capex, opex, gearing, toll_level, dscr_target, debt_rate, tenor, sculpting, deg_on, deg_rate):
    for tp in range(0, 101):
        result = calculate_structure(capex, opex, gearing, tp, toll_level, dscr_target, debt_rate, tenor, sculpting, deg_on, deg_rate)
        if result and result['bankable']:
            return result
    return calculate_structure(capex, opex, gearing, 100, toll_level, dscr_target, debt_rate, tenor, sculpting, deg_on, deg_rate)

def find_optimal_toll_level(capex, opex, gearing, toll_pct, dscr_target, debt_rate, tenor, sculpting, deg_on, deg_rate):
    for tl in range(50, 201):
        result = calculate_structure(capex, opex, gearing, toll_pct, tl, dscr_target, debt_rate, tenor, sculpting, deg_on, deg_rate)
        if result and result['bankable']:
            return result
    return calculate_structure(capex, opex, gearing, toll_pct, 200, dscr_target, debt_rate, tenor, sculpting, deg_on, deg_rate)

# ============== MAIN APP ==============

# Title
st.markdown("## ⚡ Battery Toll Structure Calculator")
st.caption("German BESS forecasts • Educational tool for developers, offtakers, investors & banks")

# Mode selector
mode = st.radio(
    "Mode",
    ["Calculator", "Max Gearing", "Min Toll %", "Min Toll €"],
    horizontal=True,
    help="Calculator: set all values manually. Others: optimise for that variable."
)

# Inputs in columns
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.markdown("**Project**")
    capex = st.number_input("CapEx (€k/MW)", value=600, min_value=300, max_value=1000, step=25)
    opex = st.number_input("Opex (€k/yr)", value=7, min_value=3, max_value=20)

with col2:
    st.markdown("**Structure**")
    if mode == "Max Gearing":
        st.info("🔍 Solving for max gearing...")
        gearing = None
    else:
        gearing = st.slider("Gearing (%)", 0, 85, 55)
    
    if mode == "Min Toll %":
        st.info("🔍 Solving for min toll %...")
        toll_pct = None
    else:
        toll_pct = st.slider("Toll Coverage (%)", 0, 100, 75)

with col3:
    st.markdown("**Toll**")
    if mode == "Min Toll €":
        st.info("🔍 Solving for min toll €...")
        toll_level = None
    else:
        toll_level = st.slider("Toll Level (€k/MW/yr)", 50, 200, 95)
        toll_pct_p50 = (toll_level / REVENUE_DATA['P50'][2026]) * 100
        st.caption(f"= {toll_pct_p50:.0f}% of Year 1 P50")

# Advanced settings in expander
with st.expander("⚙️ Financing Assumptions"):
    adv1, adv2, adv3 = st.columns(3)
    with adv1:
        dscr_target = st.number_input("Target DSCR", value=1.8, min_value=1.0, max_value=3.0, step=0.1)
        sculpting = st.checkbox("Sculpted debt service", value=False)
    with adv2:
        base_rate = 3.5
        spread = st.number_input("Credit spread (bps)", value=175, min_value=100, max_value=350, step=25)
        debt_rate = base_rate + spread/100
        st.caption(f"All-in rate: {debt_rate:.2f}%")
    with adv3:
        tenor = st.number_input("Debt tenor (years)", value=10, min_value=5, max_value=15)
        degradation_on = st.checkbox("Capacity degradation", value=True)
        if degradation_on:
            degradation_rate = st.number_input("Degradation (%/yr)", value=2.5, min_value=1.0, max_value=5.0, step=0.5)
        else:
            degradation_rate = 0

# Calculate results
if mode == "Calculator":
    results = calculate_structure(capex, opex, gearing, toll_pct, toll_level, 
                                  dscr_target, debt_rate, tenor, sculpting, degradation_on, degradation_rate)
elif mode == "Max Gearing":
    results = find_optimal_gearing(capex, opex, toll_pct, toll_level, 
                                   dscr_target, debt_rate, tenor, sculpting, degradation_on, degradation_rate)
elif mode == "Min Toll %":
    results = find_optimal_toll_pct(capex, opex, gearing, toll_level,
                                    dscr_target, debt_rate, tenor, sculpting, degradation_on, degradation_rate)
else:  # Min Toll €
    results = find_optimal_toll_level(capex, opex, gearing, toll_pct,
                                      dscr_target, debt_rate, tenor, sculpting, degradation_on, degradation_rate)

if results is None:
    st.error("Invalid structure - equity cannot be zero or negative")
    st.stop()

# Hero result card
hero_class = "hero-card" if results['bankable'] else "hero-card not-bankable"
status = "✓ Bankable" if results['bankable'] else "✗ Not Bankable"

st.markdown(f"""
<div class="{hero_class}">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div>
            <div style="font-size: 24px; font-weight: bold;">{status} at {results['gearing']:.0f}% gearing</div>
            <div style="opacity: 0.9;">{results['toll_pct']:.0f}% toll @ €{results['toll_level']:.0f}k/MW/yr • Min DSCR: {results['min_dscr']:.2f}x</div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 12px; opacity: 0.8;">P50 Equity IRR</div>
            <div style="font-size: 36px; font-weight: bold;">{results['p50']['levered_irr']:.1f}%</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Metrics row
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Debt", f"€{results['debt']:.0f}k")
m2.metric("Equity", f"€{results['equity']:.0f}k")
m3.metric("Unlevered IRR", f"{results['unlevered_irr']:.1f}%")
m4.metric("P99 IRR", f"{results['p99']['levered_irr']:.1f}%")
m5.metric("P1 IRR", f"{results['p1']['levered_irr']:.1f}%")

# Charts
st.markdown("---")
chart1, chart2 = st.columns(2)

with chart1:
    st.markdown("**Toll Pricing Analysis**")
    st.caption("Ceiling (80% P50) vs Floor (DSCR requirement) vs Your Toll")
    
    gap_df = pd.DataFrame(results['gap_data'])
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=gap_df['year'], y=gap_df['ceiling'], name='Ceiling (80% P50)',
                             fill='tozeroy', fillcolor='rgba(134, 239, 172, 0.2)',
                             line=dict(color='#22c55e', width=2)))
    fig.add_trace(go.Scatter(x=gap_df['year'], y=gap_df['floor'], name='Floor (DSCR req)',
                             fill='tozeroy', fillcolor='rgba(252, 165, 165, 0.2)',
                             line=dict(color='#ef4444', width=2)))
    fig.add_trace(go.Scatter(x=gap_df['year'], y=gap_df['actual'], name='Your Toll',
                             line=dict(color='#3b82f6', width=2, dash='dash'),
                             mode='lines+markers'))
    
    fig.update_layout(
        height=300, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        yaxis_title='€k/MW/yr',
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)

with chart2:
    st.markdown("**DSCR Profile (P99 Stress)**")
    st.caption("Debt service coverage ratio over loan term")
    
    dscr_data = [{'year': y['year'], 'dscr': y['dscr']} for y in results['p99']['yearly']]
    dscr_df = pd.DataFrame(dscr_data)
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=dscr_df['year'], y=dscr_df['dscr'],
                              mode='lines+markers', name='DSCR',
                              line=dict(color='#3b82f6', width=2),
                              marker=dict(size=8)))
    fig2.add_hline(y=dscr_target, line_dash="dash", line_color="#ef4444",
                   annotation_text=f"Target: {dscr_target}x")
    
    fig2.update_layout(
        height=300, margin=dict(l=0, r=0, t=10, b=0),
        yaxis_title='DSCR (x)',
        hovermode='x unified'
    )
    st.plotly_chart(fig2, use_container_width=True)

# Bankability map
st.markdown("**Bankability Map**")
st.caption(f"At €{results['toll_level']:.0f}k toll level - green = bankable, red = not bankable")

# Generate map data
map_data = []
for g in range(10, 86, 5):
    for tp in range(0, 101, 10):
        calc = calculate_structure(capex, opex, g, tp, results['toll_level'],
                                   dscr_target, debt_rate, tenor, sculpting, degradation_on, degradation_rate)
        if calc:
            map_data.append({
                'gearing': g, 'toll_pct': tp,
                'bankable': calc['bankable'],
                'irr': calc['p50']['levered_irr'],
                'dscr': calc['min_dscr']
            })

map_df = pd.DataFrame(map_data)
bankable_df = map_df[map_df['bankable']]
not_bankable_df = map_df[~map_df['bankable']]

fig3 = go.Figure()

if len(not_bankable_df) > 0:
    fig3.add_trace(go.Scatter(
        x=not_bankable_df['toll_pct'], y=not_bankable_df['gearing'],
        mode='markers', name='Not Bankable',
        marker=dict(color='#fca5a5', size=12),
        hovertemplate='%{y}% gearing, %{x}% toll<br>DSCR: %{customdata:.2f}x<extra></extra>',
        customdata=not_bankable_df['dscr']
    ))

if len(bankable_df) > 0:
    fig3.add_trace(go.Scatter(
        x=bankable_df['toll_pct'], y=bankable_df['gearing'],
        mode='markers', name='Bankable',
        marker=dict(color='#86efac', size=12),
        hovertemplate='%{y}% gearing, %{x}% toll<br>IRR: %{customdata:.1f}%<extra></extra>',
        customdata=bankable_df['irr']
    ))

# Current position
fig3.add_trace(go.Scatter(
    x=[results['toll_pct']], y=[results['gearing']],
    mode='markers', name='Current',
    marker=dict(color='#2563eb', size=16, symbol='star')
))

fig3.update_layout(
    height=350, margin=dict(l=0, r=0, t=10, b=0),
    xaxis_title='Toll Coverage (%)',
    yaxis_title='Gearing (%)',
    legend=dict(orientation='h', yanchor='bottom', y=1.02),
    xaxis=dict(range=[0, 105]),
    yaxis=dict(range=[0, 90])
)
st.plotly_chart(fig3, use_container_width=True)

# Footer
st.markdown("---")
st.caption("**Modo Energy** • German BESS Forecasts 2026-2035 • Educational purposes only • Not financial advice")
st.caption("Questions? Contact zach.williams@modoenergy.com")
