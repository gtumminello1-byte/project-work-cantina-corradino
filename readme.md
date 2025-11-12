# Dashboard Analisi Vendemmia – Cantina Corradino

##  Project Work – Corso di Laurea L31 (Università Telematica Pegaso)

Questo progetto è stato realizzato come project work finale per il corso di laurea triennale L31 in informatica per le aziende digitali.  
L’obiettivo è stato quello di simulare e analizzare il processo di vendemmia di una cantina vitivinicola reale (Cantina Corradino), attraverso una dashboard interattiva sviluppata in Python con Streamlit e Plotly.

---

## Obiettivi del progetto

- Rappresentare in modo visuale e interattivo i dati di raccolta e fermentazione.  
- Calcolare e monitorare i principali KPI aziendali, come:
  - resa in litri per kg d’uva
  - grado zuccherino (°Brix)
  - acidità media (g/L)
  - costi e margini di produzione
  - efficienza produttiva (L/€)
- Confrontare le performance tra vigneti irrigati e non irrigati.
- Esportare i risultati in formato PDF e CSV.

---

## Contesto e ispirazione

La Cantina Corradino è un’azienda agricola artigianale che opera in Sicilia a Castelbuono (PA),con vari vigneti sparsi in territori climaticamente strategici della Sicilia.  
I dati utilizzati nella dashboard sono simulati, ma derivano da una vera intervista con il titolare ed enologo Davide Corradino, in modo da mantenere un legame realistico con il territorio e i processi produttivi reali.

---

## Tecnologie utilizzate

| Linguaggio / Libreria | Descrizione |
|------------------------|-------------|
| Python 3 | Linguaggio principale del progetto |
| Streamlit | Framework per lo sviluppo della dashboard web |
| Plotly Express | Creazione dei grafici interattivi |
| Pandas | Gestione e analisi dei dataset CSV |
| NumPy | Supporto matematico e calcoli numerici |
| ReportLab | Generazione del report PDF |
| Kaleido | Conversione dei grafici Plotly in immagini per il PDF |

---

##  Struttura del progetto

├── dashboard_corradino.py # File principale della dashboard
├── dati_vendemmia_corradino.csv # Dataset principale (simulato)
├── lotti_fermentazione_corradino.csv # Dataset lotti 
├── README.md # Descrizione del progetto
├── img/ # Screenshot della dashboard


---

##  Avvio della dashboard

Per eseguire la dashboard in locale:

1. Clona o scarica la repository:
   ```bash
   git clone https://github.com/tuo-username/project-work-corradino.git
   cd project-work-corradino

Installa le librerie necessarie:
pip install -r requirements.txt

Avvia Streamlit:
streamlit run dashboard_corradino.py

Apri nel browser:
http://localhost:8501

---

Giovanni Tumminello, matricola 0312200110
Corso di Laurea L31 informatica per le aziende digitali – Università Pegaso
Anno accademico 2024/2025

