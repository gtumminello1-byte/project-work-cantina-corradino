Dashboard Vendemmia – Cantina Corradino

Repository tecnica del Project Work



Questa repository contiene:

il codice della dashboard Streamlit per l’analisi dei dati di vendemmia

lo script di simulazione dei dataset (vendemmia e lotti di fermentazione)

i file CSV generati

i requisiti software necessari per eseguire il progetto

Il focus del repository è esclusivamente tecnico: uso del codice, funzioni, dipendenze e istruzioni operative.

Struttura del progetto

├── dashboard_corradino.py             # Dashboard Streamlit (file principale)
├── simulatore_cantina_corradino.py    # Script per generare dataset simulati
├── dati_vendemmia_corradino.csv       # Dataset vendemmia simulato
├── lotti_fermentazione_corradino.csv  # Dataset lotti di fermentazione
├── requirements.txt                   # Librerie Python richieste
└── README.md                          # Documentazione tecnica

Tecnologie utilizzate:

Python 
Streamlit — interfaccia web della dashboard
Pandas / NumPy — gestione e analisi dei dati
Plotly Express — grafici interattivi
ReportLab — generazione del PDF
Kaleido — esportazione dei grafici in PNG
io.BytesIO — buffer in memoria per l’esportazione del PDF

Installazione

Clona la repository:
git clone https://github.com/tuo-username/project-work-corradino.git
cd project-work-corradino

Installa i requisiti:
pip install -r requirements.txt

Avvio della dashboard:

streamlit run dashboard_corradino.py

Dashboard disponibile su:
http://localhost:8501


Generazione dei dataset 
Se si desidera rigenerare i CSV:

python simulatore_cantina_corradino.py

Lo script crea automaticamente:
dati_vendemmia_corradino.csv
lotti_fermentazione_corradino.csv


Autore

Giovanni Tumminello matr. 0312200110
Corso di Laurea L31 – Informatica per le aziende digitali
Università Pegaso – A.A. 2024/2025
