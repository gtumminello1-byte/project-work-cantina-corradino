# dashboard_corradino.py
# Dashboard per analizzare la vendemmia della Cantina Corradino


import io
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

# --- setup pagina ---
st.set_page_config(page_title="Dashboard Cantina Corradino – Vendemmia", layout="wide")
st.title("Dashboard Cantina Corradino – Periodo di Vendemmia")
st.caption("Project Work L31 – Giovanni Tumminello")

# -------------------------
# utilità di base
# -------------------------
@st.cache_data
def carica_csv(percorso: str, col_data: str | None = None) -> pd.DataFrame:
    """Carico un CSV e, se serve, parso la colonna data."""
    df = pd.read_csv(percorso)
    if col_data and col_data in df.columns:
        df[col_data] = pd.to_datetime(df[col_data], errors="coerce")
    return df

def num_sicuro(df: pd.DataFrame, col: str) -> pd.Series:
    """Converto una colonna in numerico senza far crashare tutto."""
    return pd.to_numeric(df.get(col, pd.Series(dtype=float)), errors="coerce")

def stima_litri(df: pd.DataFrame) -> pd.Series:
    """Litri stimati = kg * resa (L/kg) * (1 - scarto)."""
    kg = num_sicuro(df, "raccolto_kg").fillna(0)
    resa = pd.to_numeric(df.get("resa_succo_L_kg", pd.Series(dtype=float)), errors="coerce").fillna(0.64)
    scarto = pd.to_numeric(df.get("scarto_%", pd.Series(dtype=float)), errors="coerce").fillna(0.30)
    return (kg * resa * (1 - scarto)).fillna(0)

def fig_to_png_bytes(fig) -> bytes:
    """Esporto una figura Plotly come PNG (serve 'kaleido' nel venv)."""
    return fig.to_image(format="png", scale=2)

def crea_grafici_report(df_filtrato: pd.DataFrame):
    """Preparo alcuni grafici base da mettere nel PDF (in base ai dati filtrati)."""
    grafici = []

    if {"data", "raccolto_kg"}.issubset(df_filtrato.columns) and not df_filtrato.empty:
        g = df_filtrato.groupby("data", as_index=False)["raccolto_kg"].sum()
        grafici.append(("Raccolto giornaliero (kg)", px.line(g, x="data", y="raccolto_kg")))

    if {"data", "temperatura_C"}.issubset(df_filtrato.columns) and not df_filtrato.empty:
        g2 = df_filtrato.groupby("data", as_index=False)["temperatura_C"].mean()
        grafici.append(("Temperatura media giornaliera (°C)", px.line(g2, x="data", y="temperatura_C")))

    if {"vigneto", "raccolto_kg"}.issubset(df_filtrato.columns) and not df_filtrato.empty:
        g3 = (df_filtrato.groupby("vigneto", as_index=False)["raccolto_kg"]
              .sum().sort_values("raccolto_kg", ascending=False))
        grafici.append(("Raccolto per vigneto (kg)", px.bar(g3, x="vigneto", y="raccolto_kg")))

    return grafici

def scrivi_paragrafo(canvas_obj, testo: str, x: float, y: float, max_larghezza: float,
                     font="Helvetica", size=10, leading=12) -> float:
    """Scrivo un paragrafo con a capo automatico; ritorno la nuova y."""
    canvas_obj.setFont(font, size)
    parole = testo.split()
    riga = ""
    for p in parole:
        prova = (riga + " " + p).strip()
        if canvas_obj.stringWidth(prova, font, size) <= max_larghezza:
            riga = prova
        else:
            canvas_obj.drawString(x, y, riga)
            y -= leading
            riga = p
    if riga:
        canvas_obj.drawString(x, y, riga)
        y -= leading
    return y

# -------------------------
# sorgenti dati (sidebar)
# -------------------------
st.sidebar.header("Sorgente dati")
percorso_v = st.sidebar.text_input("CSV vendemmia", "dati_vendemmia_corradino.csv")
percorso_l = st.sidebar.text_input("CSV lotti (opzionale)", "lotti_fermentazione_corradino.csv")

df_v = None
df_l = None

# vendemmia 
try:
    df_v = carica_csv(percorso_v, "data")
    st.sidebar.success("Vendemmia: file caricato")
except Exception as e:
    st.sidebar.warning(f"Non riesco a leggere {percorso_v}: {e}")
    up = st.sidebar.file_uploader("Carica vendemmia (CSV)", type=["csv"], key="vendemmia_up")
    if up:
        df_v = pd.read_csv(up)
        if "data" in df_v.columns:
            df_v["data"] = pd.to_datetime(df_v["data"], errors="coerce")
        st.sidebar.success("Vendemmia: upload riuscito")

# lotti 
try:
    df_l = carica_csv(percorso_l, "data_inizio")
    st.sidebar.info("Lotti: file caricato (opzionale)")
except Exception:
    up2 = st.sidebar.file_uploader("Carica lotti (CSV) – opzionale", type=["csv"], key="lotti_up")
    if up2:
        df_l = pd.read_csv(up2)
        if "data_inizio" in df_l.columns:
            df_l["data_inizio"] = pd.to_datetime(df_l["data_inizio"], errors="coerce")
        st.sidebar.success("Lotti: upload riuscito")

if df_v is None or df_v.empty:
    st.error("Nessun dato di vendemmia disponibile. Carico un CSV o rigenero i file con il simulatore.")
    st.stop()

# -------------------------
# filtri
# -------------------------
df_v = df_v.sort_values("data")
vigneti = sorted(df_v["vigneto"].dropna().unique().tolist()) if "vigneto" in df_v.columns else []
vitigni = sorted(df_v["vitigno"].dropna().unique().tolist()) if "vitigno" in df_v.columns else []

st.sidebar.header("Filtri")
sel_vigneti = st.sidebar.multiselect("Vigneto", vigneti, default=vigneti)
sel_vitigni = st.sidebar.multiselect("Vitigno", vitigni, default=vitigni)

data_min = pd.to_datetime(df_v["data"].min()).date()
data_max = pd.to_datetime(df_v["data"].max()).date()
sel_range = st.sidebar.date_input("Intervallo date", (data_min, data_max), min_value=data_min, max_value=data_max)

# filtro irrigazione
opzioni_irrig = {"Tutte": None, "Solo irrigate": 1, "Solo non irrigate": 0}
scelta_irrig = st.sidebar.selectbox("Irrigazione", list(opzioni_irrig.keys()), index=0)

# applico filtri
f = df_v.copy()
if sel_vigneti: f = f[f["vigneto"].isin(sel_vigneti)]
if sel_vitigni: f = f[f["vitigno"].isin(sel_vitigni)]
if isinstance(sel_range, tuple) and len(sel_range) == 2:
    f = f[(f["data"] >= pd.to_datetime(sel_range[0])) & (f["data"] <= pd.to_datetime(sel_range[1]))]
val_irrig = opzioni_irrig[scelta_irrig]
if val_irrig is not None and "irrigato" in f.columns:
    f = f[f["irrigato"] == val_irrig]

# -------------------------
# KPI
# -------------------------
st.subheader("KPI di sintesi")

c1, c2, c3, c4, c5, c6, c7 = st.columns(7)

raccolto = num_sicuro(f, "raccolto_kg").sum()
brix_m   = num_sicuro(f, "grado_zuccherino_Brix").mean()
acid_m   = num_sicuro(f, "acidita_g_L").mean()
resa_m   = num_sicuro(f, "resa_succo_L_kg").mean()
ricavi   = num_sicuro(f, "ricavo_€").sum()
costi    = num_sicuro(f, "costo_totale_€").sum()
margine  = num_sicuro(f, "margine_€").sum()

c1.metric("Raccolto (kg)", f"{raccolto:,.0f}".replace(",", "."))
c2.metric("°Brix medio", f"{brix_m:,.1f}".replace(",", "."))
c3.metric("Acidità media (g/L)", f"{acid_m:,.2f}".replace(",", "."))
c4.metric("Resa media (L/kg)", f"{resa_m:,.3f}".replace(",", "."))
c5.metric("Ricavi totali (€)", f"{ricavi:,.0f}".replace(",", "."))
c6.metric("Costi totali (€)", f"{costi:,.0f}".replace(",", "."))
c7.metric("Margine totale (€)", f"{margine:,.0f}".replace(",", "."))

# KPI extra (litri + efficienza)
litri = float(stima_litri(f).sum())
efficienza = litri / (costi if (costi and not np.isnan(costi)) else 1.0)

k1, k2 = st.columns(2)
k1.metric("Litri prodotti (stima)", f"{litri:,.0f}".replace(",", "."))
k2.metric("Efficienza (L/€)", f"{efficienza:,.2f}".replace(",", "."), help="Litri stimati / costo totale")

st.markdown("---")

# -------------------------
# grafici principali
# -------------------------
st.subheader("Andamento giornaliero")
colA, colB = st.columns(2)

with colA:
    if {"data", "raccolto_kg"}.issubset(f.columns):
        g = f.groupby("data", as_index=False)["raccolto_kg"].sum()
        st.plotly_chart(px.line(g, x="data", y="raccolto_kg", title="Raccolto giornaliero (kg)"), use_container_width=True)
    else:
        st.info("Mancano colonne 'data' o 'raccolto_kg'.")

with colB:
    if {"data", "temperatura_C"}.issubset(f.columns):
        g2 = f.groupby("data", as_index=False)["temperatura_C"].mean()
        st.plotly_chart(px.line(g2, x="data", y="temperatura_C", title="Temperatura media giornaliera (°C)"), use_container_width=True)
    else:
        st.info("Mancano colonne 'data' o 'temperatura_C'.")

st.subheader("Distribuzioni")
colC, colD = st.columns(2)
with colC:
    if {"vigneto", "raccolto_kg"}.issubset(f.columns):
        g3 = f.groupby("vigneto", as_index=False)["raccolto_kg"].sum().sort_values("raccolto_kg", ascending=False)
        st.plotly_chart(px.bar(g3, x="vigneto", y="raccolto_kg", title="Raccolto per vigneto (kg)"), use_container_width=True)
    else:
        st.info("Mancano colonne 'vigneto' o 'raccolto_kg'.")

with colD:
    if {"vitigno", "raccolto_kg"}.issubset(f.columns):
        g4 = f.groupby("vitigno", as_index=False)["raccolto_kg"].sum().sort_values("raccolto_kg", ascending=False)
        st.plotly_chart(px.bar(g4, x="vitigno", y="raccolto_kg", title="Raccolto per vitigno (kg)"), use_container_width=True)
    else:
        st.info("Mancano colonne 'vitigno' o 'raccolto_kg'.")

st.subheader("Qualità: °Brix vs Acidità")
if {"grado_zuccherino_Brix", "acidita_g_L"}.issubset(f.columns):
    q = f.copy()
    q["grado_zuccherino_Brix"] = pd.to_numeric(q["grado_zuccherino_Brix"], errors="coerce")
    q["acidita_g_L"] = pd.to_numeric(q["acidita_g_L"], errors="coerce")
    q = q.dropna(subset=["grado_zuccherino_Brix", "acidita_g_L"])
    if not q.empty:
        st.plotly_chart(
            px.scatter(
                q, x="grado_zuccherino_Brix", y="acidita_g_L",
                color="vitigno", facet_col="vigneto", facet_col_wrap=2,
                title="Relazione °Brix – Acidità (per vitigno, faccette per vigneto)"
            ),
            use_container_width=True
        )
    else:
        st.info("Dati insufficienti per il grafico °Brix–Acidità con i filtri attuali.")
else:
    st.info("Mancano le colonne per il grafico °Brix–Acidità.")

st.markdown("---")

# -------------------------
# lotti di fermentazione 
# -------------------------
st.header("Lotti di fermentazione")
if df_l is not None and not df_l.empty:
    lf = df_l.copy()
    if "vigneto" in lf.columns and sel_vigneti:
        lf = lf[lf["vigneto"].isin(sel_vigneti)]
    if "vitigno" in lf.columns and sel_vitigni:
        lf = lf[lf["vitigno"].isin(sel_vitigni)]

    colE, colF, colG = st.columns(3)
    uva_lotti = num_sicuro(lf, "uva_input_kg").sum()
    litri_lotti = num_sicuro(lf, "resa_L").sum()
    t_media_ferm = num_sicuro(lf, "temp_media_ferment_C").mean()

    colE.metric("Uva nei lotti (kg)", f"{uva_lotti:,.0f}".replace(",", "."))
    colF.metric("Litri prodotti (lotti)", f"{litri_lotti:,.0f}".replace(",", "."))
    colG.metric("T media ferment. (°C)", f"{t_media_ferm:,.1f}".replace(",", "."))

    st.subheader("Tabella lotti (filtrata)")
    st.dataframe(lf, use_container_width=True)

    if {"vigneto", "resa_L"}.issubset(lf.columns):
        agg_lotti = lf.groupby("vigneto", as_index=False)["resa_L"].sum().sort_values("resa_L", ascending=False)
        st.plotly_chart(px.bar(agg_lotti, x="vigneto", y="resa_L", title="Produzione (L) per vigneto – Lotti"),
                        use_container_width=True)
else:
    st.info("Se carico il file 'lotti_fermentazione_corradino.csv', qui vedo anche i lotti.")

st.markdown("---")

# -------------------------
# efficienza per irrigazione e per vigneto
# -------------------------
st.subheader("Confronto irrigazione – Efficienza (L/€)")
if "irrigato" in f.columns:
    df_eff = f.copy()
    df_eff["_litri"] = stima_litri(df_eff)
    df_eff["_costi"] = num_sicuro(df_eff, "costo_totale_€")
    grp = df_eff.groupby("irrigato", as_index=False).agg({"_litri": "sum", "_costi": "sum"})
    grp["efficienza_L_EUR"] = grp.apply(lambda r: r["_litri"] / (r["_costi"] if r["_costi"] else np.nan), axis=1)
    grp["stato_irrigazione"] = grp["irrigato"].map({1: "Irrigato", 0: "Non irrigato"}).fillna("N/D")

    st.plotly_chart(
        px.bar(grp, x="stato_irrigazione", y="efficienza_L_EUR",
               title="Efficienza per stato di irrigazione (L/€)", text_auto=".2f"),
        use_container_width=True
    )
else:
    st.info("Colonna 'irrigato' non presente nei dati.")

st.subheader("Efficienza per vigneto (L/€)")
if "vigneto" in f.columns:
    df_vig = f.copy()
    df_vig["_litri"] = stima_litri(df_vig)
    df_vig["_costi"] = num_sicuro(df_vig, "costo_totale_€")
    gv = df_vig.groupby("vigneto", as_index=False).agg({"_litri": "sum", "_costi": "sum"})
    gv = gv[gv["_costi"] > 0]
    gv["efficienza_L_EUR"] = gv["_litri"] / gv["_costi"]
    gv = gv.sort_values("efficienza_L_EUR", ascending=False)

    st.plotly_chart(
        px.bar(gv, x="vigneto", y="efficienza_L_EUR",
               title="Efficienza per vigneto (L/€)", text_auto=".2f"),
        use_container_width=True
    )
else:
    st.info("Colonna 'vigneto' non presente.")

st.subheader("Qualità per irrigazione – °Brix e Acidità")
dfq = f.copy()
dfq["grado_zuccherino_Brix"] = pd.to_numeric(dfq.get("grado_zuccherino_Brix", pd.Series(dtype=float)), errors="coerce")
dfq["acidita_g_L"] = pd.to_numeric(dfq.get("acidita_g_L", pd.Series(dtype=float)), errors="coerce")
dfq = dfq.dropna(subset=["grado_zuccherino_Brix", "acidita_g_L"], how="all")

if "irrigato" in dfq.columns and not dfq.empty:
    agg = dfq.groupby("irrigato", as_index=False).agg(
        brix_m=("grado_zuccherino_Brix", "mean"),
        acid_m=("acidita_g_L", "mean"),
        n_misure=("grado_zuccherino_Brix", "count")
    )
    agg["stato_irrigazione"] = agg["irrigato"].map({1: "Irrigato", 0: "Non irrigato"}).fillna("N/D")

    st.write("**Medie per stato di irrigazione**")
    st.dataframe(
        agg[["stato_irrigazione", "brix_m", "acid_m", "n_misure"]]
          .rename(columns={"brix_m": "°Brix medio", "acid_m": "Acidità media (g/L)", "n_misure": "N° misure"}),
        use_container_width=True
    )

    agg_melt = agg.melt(
        id_vars=["stato_irrigazione"],
        value_vars=["brix_m", "acid_m"],
        var_name="Metrica", value_name="Valore"
    )
    agg_melt["Metrica"] = agg_melt["Metrica"].map({"brix_m": "°Brix medio", "acid_m": "Acidità media (g/L)"})

    st.plotly_chart(
        px.bar(agg_melt, x="stato_irrigazione", y="Valore", color="Metrica",
               barmode="group", text_auto=".2f",
               title="Confronto medie di qualità per irrigazione"),
        use_container_width=True
    )

    col_q1, col_q2 = st.columns(2)
    with col_q1:
        if dfq["grado_zuccherino_Brix"].notna().any():
            dfq["Stato irrigazione"] = dfq["irrigato"].map({1: "Irrigato", 0: "Non irrigato"})
            st.plotly_chart(
                px.box(dfq.dropna(subset=["grado_zuccherino_Brix"]),
                       x="Stato irrigazione", y="grado_zuccherino_Brix",
                       title="Distribuzione °Brix per irrigazione"),
                use_container_width=True
            )
        else:
            st.info("Nessuna misura disponibile per °Brix con i filtri correnti.")
    with col_q2:
        if dfq["acidita_g_L"].notna().any():
            st.plotly_chart(
                px.box(dfq.dropna(subset=["acidita_g_L"]),
                       x="Stato irrigazione", y="acidita_g_L",
                       title="Distribuzione Acidità (g/L) per irrigazione"),
                use_container_width=True
            )
        else:
            st.info("Nessuna misura disponibile per Acidità con i filtri correnti.")
else:
    st.info("Dati qualità non sufficienti o colonna 'irrigato' assente.")

st.markdown("---")

# -------------------------
# export CSV + PDF
# -------------------------
st.header("Esporta (CSV)")
colX, colY = st.columns(2)
colX.download_button(
    "Scarica vendemmia filtrata (CSV)",
    data=f.to_csv(index=False).encode("utf-8"),
    file_name="vendemmia_filtrata_corradino.csv",
    mime="text/csv"
)
if df_l is not None and not df_l.empty:
    colY.download_button(
        "Scarica lotti (CSV)",
        data=df_l.to_csv(index=False).encode("utf-8"),
        file_name="lotti_fermentazione_corradino.csv",
        mime="text/csv"
    )

st.markdown("---")
st.header("Esporta Report PDF")

# riassunto filtri correnti (così il PDF è leggibile anche da chi non vede la pagina)
descr_filtro = []
if sel_vigneti: descr_filtro.append("Vigneti: " + ", ".join(sel_vigneti))
if sel_vitigni: descr_filtro.append("Vitigni: " + ", ".join(sel_vitigni))
if isinstance(sel_range, tuple) and len(sel_range) == 2:
    descr_filtro.append(f"Periodo: {sel_range[0]} → {sel_range[1]}")
if "scelta_irrig" in locals():
    descr_filtro.append(f"Irrigazione: {scelta_irrig}")
riassunto = " • ".join(descr_filtro) if descr_filtro else "Filtri: nessuno"

col_gen, col_info = st.columns([1, 2])
with col_gen:
    genera_pdf = st.button("Genera Report PDF", type="primary")
with col_info:
    st.write("Creo un PDF con KPI e 2–3 grafici principali relativi ai filtri attuali.")

def build_pdf_report(df_filtrato: pd.DataFrame, df_lotti: pd.DataFrame | None,
                     titolo: str, sottotitolo: str) -> bytes:
    """Genero il PDF del report (KPI, grafici, lotti, note metodologiche)."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    W, H = A4
    margin = 1.5 * cm
    y = H - margin

    # intestazione
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, y, titolo)
    y -= 14
    c.setFont("Helvetica", 10)
    c.drawString(margin, y, sottotitolo)
    y -= 18

    # KPI helper
    def mmedia(s):
        s = pd.to_numeric(s, errors="coerce")
        return float(s.mean()) if len(s) else float("nan")
    def somma(s):
        s = pd.to_numeric(s, errors="coerce")
        return float(s.sum()) if len(s) else 0.0

    # KPI
    raccolto = somma(df_filtrato.get("raccolto_kg", []))
    brix_m   = mmedia(df_filtrato.get("grado_zuccherino_Brix", []))
    acid_m   = mmedia(df_filtrato.get("acidita_g_L", []))
    resa_m   = mmedia(df_filtrato.get("resa_succo_L_kg", []))
    ricavi   = somma(df_filtrato.get("ricavo_€", []))
    costi    = somma(df_filtrato.get("costo_totale_€", []))
    margine  = somma(df_filtrato.get("margine_€", []))
    litri    = float(stima_litri(df_filtrato).sum())
    eff      = litri / (costi if costi else 1.0)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "KPI di sintesi (filtri correnti)")
    y -= 12
    c.setFont("Helvetica", 10)
    righe = [
        f"Raccolto: {raccolto:,.0f} kg",
        f"°Brix medio: {brix_m:,.1f}" if not np.isnan(brix_m) else "°Brix medio: n/d",
        f"Acidità media: {acid_m:,.2f} g/L" if not np.isnan(acid_m) else "Acidità media: n/d",
        f"Resa media: {resa_m:,.3f} L/kg" if not np.isnan(resa_m) else "Resa media: n/d",
        f"Ricavi totali: € {ricavi:,.0f}",
        f"Costi totali: € {costi:,.0f}",
        f"Margine totale: € {margine:,.0f}",
        f"Litri prodotti (stima): {litri:,.0f} L",
        f"Efficienza: {eff:,.2f} L/€"
    ]
    for r in righe:
        c.drawString(margin, y, r.replace(",", "."))
        y -= 12

    # Grafici principali
    grafici = crea_grafici_report(df_filtrato)
    for titolo_fig, fig in grafici:
        png = fig_to_png_bytes(fig)
        img = ImageReader(io.BytesIO(png))

        img_w = W - 2 * margin
        img_h = 7 * cm

        # se lo spazio residuo non basta, nuova pagina
        if y < img_h + 3 * cm:
            c.showPage()
            y = H - margin

        # titolo grafico
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, titolo_fig)
        y -= 8

        # immagine
        c.drawImage(img, margin, y - img_h, width=img_w, height=img_h)
        y -= (img_h + 12)

    # Lotti (se presenti)
    if df_lotti is not None and not df_lotti.empty:
        if y < 4 * cm:
            c.showPage()
            y = H - margin
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, "Sintesi lotti di fermentazione")
        y -= 12
        try:
            uva_lotti = pd.to_numeric(df_lotti.get("uva_input_kg", pd.Series(dtype=float)), errors="coerce").sum()
            litri_lotti = pd.to_numeric(df_lotti.get("resa_L", pd.Series(dtype=float)), errors="coerce").sum()
            c.setFont("Helvetica", 10)
            c.drawString(margin, y, f"Uva nei lotti: {uva_lotti:,.0f} kg".replace(",", "."))
            y -= 12
            c.drawString(margin, y, f"Litri prodotti (lotti): {litri_lotti:,.0f} L".replace(",", "."))
            y -= 16
        except Exception:
            pass

    # Pagina finale: Note metodologiche 
    c.showPage()
    W, H = A4
    margin = 1.5 * cm
    y = H - margin

    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y, "Note metodologiche")
    y -= 18

    # 1) Contesto e obiettivo
    y = scrivi_paragrafo(
        c,
        "Contesto. Ho costruito una piccola pipeline per analizzare il periodo di vendemmia della Cantina Corradino: "
        "i dati vengono simulati (privacy/tempi) e poi letti in una dashboard per il monitoraggio. "
        "L’obiettivo è visualizzare in modo chiaro i principali indicatori tecnici ed economici.",
        margin, y, W - 2*margin, size=10
    )

    # 2) Dati e struttura
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "Dati utilizzati")
    y -= 14
    y = scrivi_paragrafo(
        c,
        "- Vendemmia (CSV): data, vigneto, vitigno, raccolto, °Brix, acidità, costi e margini. "
        "- Lotti (CSV opzionale): resa in litri e temperatura media di fermentazione.",
        margin, y, W - 2*margin
    )

    # 3) Ipotesi adottate
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "Ipotesi di lavoro")
    y -= 14
    y = scrivi_paragrafo(
        c,
        "- Dati simulati, calibrati sull’intervista alla cantina (Sicilia occidentale, altitudini ~0–600 m, "
        "vendemmia fine agosto–metà ottobre, scarto medio 25–35%, irrigazione ~70%). "
        "- Le grandezze economiche sono indicative, utili per confronti relativi.",
        margin, y, W - 2*margin
    )

    # 4) KPI e formule
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "KPI e formule principali")
    y -= 14
    y = scrivi_paragrafo(
        c,
        "• Litri prodotti (stima) = kg_raccolti × resa_L/kg × (1 − scarto)  "
        "• Efficienza (L/€) = litri_prodotti / costo_totale  "
        "• Margine (€) = ricavi − costi  "
        "• °Brix e Acidità: medie aritmetiche sui dati filtrati.",
        margin, y, W - 2*margin
    )

    # 5) Limiti
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "Limiti dell’analisi")
    y -= 14
    y = scrivi_paragrafo(
        c,
        "- I risultati sono indicazioni qualitative: molte variabili (gestione in campo, pratiche di cantina) non sono modellate. "
        "Con filtri molto stretti le medie possono essere poco rappresentative.",
        margin, y, W - 2*margin
    )

    # 6) Riproducibilità
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "Riproducibilità")
    y -= 14
    y = scrivi_paragrafo(
        c,
        "Per rifare l’analisi: (1) attivo il venv; (2) eseguo il simulatore per generare i CSV; "
        "(3) avvio la dashboard; (4) imposto i filtri; (5) esporto il PDF. "
        "Dipendenze: Python 3.x, pandas, numpy, streamlit, plotly, reportlab, kaleido.",
        margin, y, W - 2*margin
    )

    # 7) Footer con timestamp e riferimenti sintetici
    c.setFont("Helvetica", 9)
    c.drawString(margin, y, "Riferimenti: Documentazione Streamlit/Plotly; Appunti L31 (Pegaso); Intervista Cantina Corradino (2025).")
    y -= 12
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(margin, y, f"Report generato il: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # chiusura
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

if genera_pdf:
    try:
        pdf_bytes = build_pdf_report(
            df_filtrato=f,
            df_lotti=df_l,
            titolo="Cantina Corradino – Report Vendemmia",
            sottotitolo=riassunto
        )
        st.success("Report generato.")
        st.download_button(
            label="Scarica Report PDF",
            data=pdf_bytes,
            file_name="report_vendemmia_corradino.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error("Errore nella generazione del PDF. Controllo che 'reportlab' e 'kaleido' siano installati nel venv.")
        st.exception(e)

st.caption("© Cantina Corradino – Analisi vendemmia (Streamlit + Plotly)")
