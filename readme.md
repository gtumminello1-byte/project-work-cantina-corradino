Dashboard Vendemmia – Cantina Corradino

Project Work – Informatica per le Aziende Digitali (L-31)

Questo progetto contiene una dashboard interattiva in Python che permette di analizzare i dati della vendemmia della Cantina Corradino.
La dashboard è stata realizzata con Streamlit, Plotly, Pandas e include anche un sistema di export in PDF.



1. Requisiti

Prima di avviare il progetto serve:

Python 3 (https://www.python.org
)

Librerie Python elencate in requirements.txt

Un browser (Chrome, Edge, Safari…)



2. Installazione del progetto
2.1. Scaricare i file

Vai sulla pagina GitHub del progetto.

Clicca su Code → Download ZIP.

Estrai il contenuto in una cartella a scelta.

2.2. Aprire un terminale nella cartella

Windows: apri la cartella → clic sulla barra del percorso → scrivi cmd → Invio.

macOS: tasto destro sulla cartella → “Nuovo Terminale nella cartella”.



3. Creazione ambiente virtuale (consigliato):

   python -m venv .venv

Attivazione:

Windows:
.venv\Scripts\activate

macOS/Linux:
source .venv/bin/activate



4. Installazione delle librerie:

   pip install -r requirements.txt



5. Avvio della dashboard

Lanciare:
streamlit run dashboard_corradino.py

Il browser si aprirà automaticamente su:
http://localhost:8501

Se non si apre da solo, copiare l’indirizzo dal terminale e incollarlo nel browser.



6. Caricamento dei dati

La dashboard usa due file CSV:

dati_vendemmia_corradino.csv

lotti_fermentazione_corradino.csv 

Se sono nella stessa cartella della dashboard, vengono caricati automaticamente.
Altrimenti è possibile scrivere il percorso completo nella sidebar.



8. Problemi comuni

Streamlit non trovato → l’ambiente non è attivo.

CSV non trovato → controllare che il nome o il percorso siano corretti.

Pagina bianca → aspettare qualche secondo o premere Ctrl+F5.



Autore

Giovanni Tumminello matr. 0312200110
Informatica per le aziende digitali (L-31) 
Università Telematica Pegaso - A.A. 2024/25



