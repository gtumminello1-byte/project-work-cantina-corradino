# simulatore_cantina_corradino.py
# Simulazione del periodo di vendemmia per la Cantina Corradino (Sicilia)
# Autore: Giovanni Tumminello – Project Work Università Pegaso (L31)
# Output: dati_vendemmia_corradino.csv e lotti_fermentazione_corradino.csv

from datetime import date, timedelta
import numpy as np
import pandas as pd

# ==============================
# PARAMETRI DELLA SIMULAZIONE
# ==============================

VIGNETI = [
    {"nome": "SanGiuseppeJato", "altitudine_m": 0, "vitigni": ["Nero d'Avola", "Malvasia", "Syrah"]},
    {"nome": "Favara", "altitudine_m": 0, "vitigni": ["Nero d'Avola", "Syrah"]},
    {"nome": "Castellana_Alcamo", "altitudine_m": 600, "vitigni": ["Catarratto", "Petit Verdot", "Grillo"]},
]

PERCENTUALE_IRRIGAZIONE = 0.70
SCARTO_MIN, SCARTO_MAX = 0.25, 0.35

INIZIO_VENDEMMIA = date(2025, 8, 25)
FINE_VENDEMMIA   = date(2025, 10, 15)

rng = np.random.default_rng(42)

# ==================================
# FUNZIONI DI SUPPORTO
# ==================================

def intervallo_date(inizio, fine):
    giorno = inizio
    while giorno <= fine:
        yield giorno
        giorno += timedelta(days=1)

def temperatura_giornaliera(data, altitudine):
    base = 30 - max(0, (data.timetuple().tm_yday - 240)) * 0.08
    rumore = rng.normal(0, 1.2)
    return round(base - (altitudine/600)*3.0 + rumore, 1)

def pioggia_giornaliera():
    if rng.random() < 0.20:
        return round(max(0, rng.normal(6, 5)), 1)
    return 0.0

def umidita_suolo(precedente, pioggia, irrigato):
    nuova = precedente + pioggia*0.5 + (5 if irrigato else 0) - 2.5
    return float(np.clip(nuova, 10, 40))

def raccolto_kg(vitigno, temperatura, pioggia, irrigato):
    prob_base = 0.10
    fattore_temp = np.clip(1 - abs((temperatura - 28))/10, 0.6, 1.2)
    penalita_pioggia = 0.5 if pioggia > 5 else 1.0
    bonus_vitigno = 1.1 if vitigno in ["Nero d'Avola","Syrah","Grillo"] else 1.0
    probabilita = prob_base * fattore_temp * penalita_pioggia * bonus_vitigno
    if rng.random() > probabilita:
        return 0.0
    base_media = 600
    scala_vitigno = {
        "Nero d'Avola": 1.2, "Syrah": 1.1, "Malvasia": 0.9,
        "Catarratto": 1.0, "Petit Verdot": 0.8, "Grillo": 1.1
    }.get(vitigno, 1.0)
    fattore_irrigazione = 2.0 if irrigato else 1.0
    media = base_media * scala_vitigno * fattore_irrigazione
    return float(max(0, rng.normal(media, media*0.35)))

def grado_zuccherino(vitigno, temperatura, pioggia, altitudine):
    base = 22.5 + (temperatura - 26)*0.25 - (altitudine/600)*0.8 - (0.4 if pioggia > 5 else 0)
    aggiustamento = {"Nero d'Avola":1.0, "Syrah":0.8, "Malvasia":0.2,
                     "Catarratto":-0.3, "Petit Verdot":0.6, "Grillo":-0.1}.get(vitigno, 0)
    valore = base + aggiustamento + rng.normal(0, 0.6)
    return float(np.clip(valore, 18, 26))

def acidita_mosto(vitigno, temperatura, altitudine):
    base = 6.8 - (temperatura - 26)*0.1 + (altitudine/600)*0.4
    aggiustamento = {"Malvasia": -0.1, "Catarratto": 0.2, "Petit Verdot": -0.2}.get(vitigno, 0)
    valore = base + aggiustamento + rng.normal(0, 0.25)
    return float(np.clip(valore, 5.5, 8.2))

def resa_succo_litri_per_kg(vitigno):
    medie = {"Nero d'Avola":0.66, "Syrah":0.65, "Malvasia":0.64,
             "Catarratto":0.63, "Petit Verdot":0.62, "Grillo":0.64}
    return float(np.clip(rng.normal(medie.get(vitigno, 0.64), 0.015), 0.60, 0.70))

def costo_manodopera(kg_raccolti):
    return float(220 + 0.07 * kg_raccolti)

def altri_costi(irrigato, pioggia):
    costo_irrigazione = 45 if irrigato and pioggia < 3 else (15 if irrigato else 0)
    macchine = 60
    return float(costo_irrigazione + macchine)

# =====================================
# SIMULAZIONE VENDEMMIA CORRADINO
# =====================================

def simula_vendemmia(inizio=INIZIO_VENDEMMIA, fine=FINE_VENDEMMIA):
    record = []
    umidita = {v["nome"]: rng.uniform(14, 24) for v in VIGNETI}
    
    for giorno in intervallo_date(inizio, fine):
        for v in VIGNETI:
            nome, alt = v["nome"], v["altitudine_m"]
            for vitigno in v["vitigni"]:
                irrigato = 1 if rng.random() < PERCENTUALE_IRRIGAZIONE else 0
                temp = temperatura_giornaliera(giorno, alt)
                pioggia = pioggia_giornaliera()
                umidita[nome] = umidita_suolo(umidita[nome], pioggia, irrigato)
                siccita = 1 if (pioggia == 0.0 and umidita[nome] < 15) else 0

                kg = raccolto_kg(vitigno, temp, pioggia, irrigato)
                if kg > 0:
                    brix = grado_zuccherino(vitigno, temp, pioggia, alt)
                    acid = acidita_mosto(vitigno, temp, alt)
                    resa = resa_succo_litri_per_kg(vitigno)
                    scarto = rng.uniform(SCARTO_MIN, SCARTO_MAX)
                else:
                    brix = acid = resa = scarto = np.nan

                costo_lavoro = costo_manodopera(kg)
                costo_totale = costo_lavoro + altri_costi(irrigato, pioggia)
                ricavo = (kg * (resa if not np.isnan(resa) else 0.64)) * 1.1 if kg > 0 else 0.0
                margine = ricavo - costo_totale

                record.append({
                    "data": giorno.isoformat(),
                    "vigneto": nome,
                    "altitudine_m": alt,
                    "vitigno": vitigno,
                    "irrigato": irrigato,
                    "temperatura_C": temp,
                    "pioggia_mm": pioggia,
                    "umidita_suolo_%": round(umidita[nome], 1),
                    "siccita_flag": siccita,
                    "raccolto_kg": round(kg, 1),
                    "grado_zuccherino_Brix": round(brix, 1) if not np.isnan(brix) else "",
                    "acidita_g_L": round(acid, 2) if not np.isnan(acid) else "",
                    "resa_succo_L_kg": round(resa, 3) if not np.isnan(resa) else "",
                    "scarto_%": round(scarto, 3) if not np.isnan(scarto) else "",
                    "costo_manodopera_€": round(costo_lavoro, 2),
                    "costo_totale_€": round(costo_totale, 2),
                    "ricavo_€": round(ricavo, 2),
                    "margine_€": round(margine, 2)
                })
    return pd.DataFrame(record)

# =========================================
# CREAZIONE LOTTI DI FERMENTAZIONE
# =========================================

def crea_lotti_fermentazione(df_vendemmia):
    df = df_vendemmia[df_vendemmia["raccolto_kg"] > 0].copy()
    if df.empty:
        return pd.DataFrame()
    
    df["data"] = pd.to_datetime(df["data"])
    lotti = []
    for (vigneto, vitigno), gruppo in df.groupby(["vigneto", "vitigno"]):
        gruppo = gruppo.sort_values("data").reset_index(drop=True)
        i = 0
        while i < len(gruppo):
            dimensione = int(rng.integers(3, 7))
            finestra = gruppo.iloc[i:i+dimensione]
            data_inizio = finestra["data"].min().date().isoformat()
            data_fine = finestra["data"].max().date().isoformat()
            input_kg = float(finestra["raccolto_kg"].sum())
            if input_kg < 300:
                i += dimensione
                continue
            
            temp_media = float(np.nanmean(finestra["temperatura_C"]))
            brix_iniziale = float(np.nanmean(pd.to_numeric(finestra["grado_zuccherino_Brix"], errors="coerce")))
            brix_finale = max(0.2, round(brix_iniziale - float(rng.uniform(20, 22)), 1))
            resa = float(np.nanmean(pd.to_numeric(finestra["resa_succo_L_kg"], errors="coerce")))
            scarto = float(np.nanmean(pd.to_numeric(finestra["scarto_%"], errors="coerce")))
            resa = 0.64 if np.isnan(resa) else resa
            scarto = 0.30 if np.isnan(scarto) else scarto
            produzione_L = input_kg * resa * (1 - scarto)

            lotti.append({
                "lotto_id": f"LOTTO-{vigneto[:3].upper()}-{vitigno.split()[0].upper()}-{data_inizio}",
                "data_inizio": data_inizio,
                "data_fine": data_fine,
                "vitigno": vitigno,
                "vigneto": vigneto,
                "uva_input_kg": round(input_kg, 1),
                "temp_media_ferment_C": round(temp_media - 4 + float(rng.normal(0, 0.5)), 1),
                "brix_iniziale": round(brix_iniziale, 1),
                "brix_finale": brix_finale,
                "resa_L": round(produzione_L, 1),
                "scarto_%": round(scarto, 3),
                "note": "Lotto generato automaticamente"
            })
            i += dimensione
    return pd.DataFrame(lotti)

# =====================
# ESECUZIONE SCRIPT
# =====================

if __name__ == "__main__":
    df_vendemmia = simula_vendemmia()
    df_lotti = crea_lotti_fermentazione(df_vendemmia)
    df_vendemmia.to_csv("dati_vendemmia_corradino.csv", index=False)
    df_lotti.to_csv("lotti_fermentazione_corradino.csv", index=False)
    print(f"✅ Simulazione completata: {len(df_vendemmia)} righe vendemmia, {len(df_lotti)} lotti generati.")
