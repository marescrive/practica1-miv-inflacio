import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Inflació per mandat presidencial", layout="wide")

@st.cache_data
def carrega():
    return pd.read_csv("inflacio_per_mandat.csv")

dm = carrega()
ordre = list(dm["mandat"].drop_duplicates())  # ordre cronològic fixat al preprocessament
partit_de = dm.drop_duplicates("mandat").set_index("mandat")["partit"].to_dict()
color_partit = {"Demòcrata": "#1f77b4", "Republicà": "#d62728"}

# --- Controls (barra lateral)
st.sidebar.header("Controls")
# FILTRAR: per partit i per mandat
partits = st.sidebar.multiselect("Partit", ["Demòcrata", "Republicà"],
                                 default=["Demòcrata", "Republicà"])
disponibles = [m for m in ordre if partit_de[m] in partits]
seleccio = st.sidebar.multiselect("Mandats", disponibles, default=disponibles)
# Prevenció d'errors: no deixem dibuixar un gràfic buit.
if not seleccio:
    st.warning("Selecciona almenys un mandat a la barra lateral.")
    st.stop()
# SELECCIONAR: ressaltar un mandat
opcions = ["Cap"] + seleccio
ressaltat = st.sidebar.selectbox(
    "Ressalta un mandat", opcions,
    index=opcions.index("Trump II") if "Trump II" in seleccio else 0)
# RECONFIGURAR: mes de comparació i retall de totes les sèries.
# Per defecte retallem: la vista inicial és la comparació honesta (mateix nombre de mesos).
mes = st.sidebar.slider("Mes de comparació", 1, 48, 18)
retalla = st.sidebar.checkbox("Retalla totes les sèries a aquest mes", value=True)

fig = go.Figure()
for nom in seleccio:
    d = dm[dm["mandat"] == nom]
    if retalla:
        d = d[d["mes_de_mandat"] <= mes]
    partit = partit_de[nom]
    actiu = nom == ressaltat
    fig.add_trace(go.Scatter(
        x=d["mes_de_mandat"], y=d["inflacio_acum"], mode="lines+text",
        name=f"{nom} ({partit})",
        line=dict(color=color_partit[partit], width=4 if actiu else 1.5),
        opacity=1 if actiu else (0.8 if ressaltat == "Cap" else 0.45),
        # Etiqueta directa només al mandat ressaltat (evita que se solapin).
        text=[""] * (len(d) - 1) + [nom if actiu else ""], textposition="middle right",
        # ABSTRAURE: detall a petició amb el tooltip
        hovertemplate="%{x} mesos<br>%{y:.2f} %<extra>" + nom + "</extra>",
    ))

# Marca explícita que Trump II és una sèrie incompleta (el que el gràfic original amagava).
if "Trump II" in seleccio:
    t = dm[dm["mandat"] == "Trump II"]
    fi = t["mes_de_mandat"].max()
    ultim = t[t["mes_de_mandat"] <= (mes if retalla else fi)].iloc[-1]
    if ultim["mes_de_mandat"] == fi:
        data = pd.to_datetime(ultim["date"]).strftime("%m/%Y")
        fig.add_annotation(x=fi, y=ultim["inflacio_acum"], ax=60, ay=-50,
                           text=f"Dades disponibles fins al mes {fi} ({data})",
                           showarrow=True, arrowcolor="#555")

fig.add_vline(x=mes, line_dash="dot", line_color="#555",
              annotation_text=f"Mes {mes}", annotation_position="top left")
fig.update_layout(
    title="Inflació acumulada per mandat presidencial dels EUA (IPC-U desestacionalitzat)",
    xaxis=dict(title="Mesos des de la investidura (gener)",
               range=[0, (mes if retalla else 48) + 10]),
    yaxis=dict(title="Inflació acumulada (%)", rangemode="tozero"),
    legend_title="Mandat", template="simple_white", height=600,
    paper_bgcolor="white", plot_bgcolor="white", font=dict(color="#222"),
)

# theme=None: respectem el template de Plotly en lloc del tema fosc de Streamlit.
st.plotly_chart(fig, use_container_width=True, theme=None)
st.caption("Font: BLS via FRED (sèrie CPIAUCSL). Elaboració pròpia.")