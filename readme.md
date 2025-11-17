Dashboard Vendemmia – Cantina Corradino

Project Work – Informatica per le Aziende Digitali (L-31)

Questo progetto contiene una dashboard interattiva in Python che permette di analizzare i dati della vendemmia della Cantina Corradino.
La dashboard è stata realizzata con Streamlit, Plotly, Pandas e include anche un sistema di esportazione in PDF.

Requisiti

Prima di avviare il progetto è necessario avere:

Python 3 (https://www.python.org
)

Le librerie Python elencate nel file requirements.txt

Un browser aggiornato (Chrome, Edge, Safari)

Installazione del progetto
1. Scaricare i file

Accedere alla pagina GitHub del progetto.

Cliccare su Code → Download ZIP.

Estrarre il contenuto in una cartella a scelta.

2. Aprire il terminale nella cartella del progetto

Windows: aprire la cartella → cliccare sulla barra del percorso → digitare cmd → premere Invio.

macOS: clic destro sulla cartella → selezionare Nuovo Terminale nella cartella.

Creazione dell’ambiente virtuale (consigliato)
python -m venv .venv

Attivazione

Windows:

.venv\Scripts\activate


macOS/Linux:

source .venv/bin/activate

Installazione delle librerie necessarie
pip install -r requirements.txt

Avvio della dashboard

Per eseguire la dashboard:

streamlit run dashboard_corradino.py


Il browser dovrebbe aprirsi automaticamente all’indirizzo:

http://localhost:8501


Se non si apre, copiare l’indirizzo dal terminale e incollarlo manualmente nel browser.

Caricamento dei dati

La dashboard utilizza i seguenti file CSV:

dati_vendemmia_corradino.csv

lotti_fermentazione_corradino.csv 

Se i file si trovano nella stessa cartella dello script, vengono caricati automaticamente.
In caso contrario, è possibile indicare il percorso completo tramite la sidebar dell’applicazione.

Problemi comuni

Streamlit non trovato → l’ambiente virtuale potrebbe non essere attivo.

CSV non trovato → verificare che il nome del file e il percorso siano corretti.

Pagina bianca → attendere alcuni secondi o ricaricare con Ctrl+F5.

Autore

Giovanni Tumminello – matricola 0312200110
Corso di Laurea in Informatica per le Aziende Digitali (L-31)
Università Telematica Pegaso – A.A. 2024/2025
