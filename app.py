
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="KI-Engpassanalyse", layout="wide")

st.markdown("""
<style>
    .main { background-color: #fafafa; }
    .metric-box {
        border-radius: 0.5rem;
        padding: 1rem;
        background-color: white;
        box-shadow: 0 0 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .metric-green { color: green; font-weight: bold; }
    .metric-red { color: red; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.sidebar.image("logo.png", use_container_width=True)
st.title("KI-gestützte Engpassanalyse und Kapazitätsvorschau")

@st.cache_data
def load_data():
    df = pd.read_csv("arbeitsgaenge_demo.csv")
    df["AG-Starttermin"] = pd.to_datetime(df["AG-Starttermin"])
    df["AG-Ende"] = pd.to_datetime(df["AG-Ende"])
    return df

df = load_data()

kw = st.sidebar.selectbox("Kalenderwoche", sorted(df["KW"].dropna().unique()))
maschine = st.sidebar.selectbox("Maschinenressource", sorted(df["Maschinenressource"].dropna().unique()))

df_filtered = df[(df["KW"] == kw) & (df["Maschinenressource"] == maschine)]

st.subheader("Kennzahlenübersicht")
tage = df_filtered["Tag"].nunique()
max_kapazitaet = tage * 16

sum_plan = df_filtered["Planzeit [h]"].sum()
sum_ki = df_filtered["KI-Zeit [h]"].sum()
sum_ist = df_filtered["Ist-Zeit [h]"].sum(min_count=1)

auslastung_plan = round((sum_plan / max_kapazitaet) * 100, 1)
auslastung_ki = round((sum_ki / max_kapazitaet) * 100, 1)

engpaesse = df_filtered.groupby("Tag")[["Planzeit [h]", "KI-Zeit [h]"]].sum()
anz_engpaesse = ((engpaesse > 16).any(axis=1)).sum()

def color_class(value, threshold=100):
    return "metric-red" if value > threshold else "metric-green"

col1, col2, col3 = st.columns(3)
col1.markdown(f"<div class='metric-box'>Anzahl Engpässe<br><span class='{color_class(anz_engpaesse, 0)}'>{anz_engpaesse}</span></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='metric-box'>Auslastung (Plan)<br><span class='{color_class(auslastung_plan)}'>{auslastung_plan}%</span></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='metric-box'>Auslastung (KI)<br><span class='{color_class(auslastung_ki)}'>{auslastung_ki}%</span></div>", unsafe_allow_html=True)

st.subheader("Engpass-Aufträge (>100% Tagesauslastung laut Plan oder KI)")
kritische_tage = engpaesse[(engpaesse["Planzeit [h]"] > 16) | (engpaesse["KI-Zeit [h]"] > 16)].index
df_engpaesse = df_filtered[df_filtered["Tag"].isin(kritische_tage)]

st.dataframe(df_engpaesse[[
    "FA-Nr.", "Artikelnr.", "Bez./Artikel", "Maschinenressource", "Tag", "Planzeit [h]", "KI-Zeit [h]"
]])

st.subheader("Zeitvergleich Plan / KI / IST je Wochentag")
vergleich = df_filtered.groupby("Wochentag")[["Planzeit [h]", "KI-Zeit [h]", "Ist-Zeit [h]"]].sum().reset_index()

fig = go.Figure()
fig.add_trace(go.Bar(x=vergleich["Wochentag"], y=vergleich["Planzeit [h]"], name="Plan"))
fig.add_trace(go.Bar(x=vergleich["Wochentag"], y=vergleich["KI-Zeit [h]"], name="KI"))
fig.add_trace(go.Bar(x=vergleich["Wochentag"], y=vergleich["Ist-Zeit [h]"], name="IST"))
fig.update_layout(barmode='group', xaxis_title="Wochentag", yaxis_title="Stunden")
st.plotly_chart(fig)

st.subheader("Detailtabelle: Plan / KI / IST je Auftrag")
st.dataframe(df_filtered[[
    "FA-Nr.", "Tag", "Wochentag", "Maschinenressource", "Planzeit [h]", "KI-Zeit [h]", "Ist-Zeit [h]"
]])
