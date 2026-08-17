# ⚽ Calcetto Stats - Web Application

Applicazione web moderna e responsive, sviluppata con **Streamlit** e **Pandas**, per gestire le statistiche delle partite di calcetto a 5 tra amici.

---

## 🌟 Funzionalità Principali

1. **🔒 PIN Gate di Sicurezza:**
   - Schermata di accesso protetta da PIN numerico (**`5678`**).
   - Gestione sessione e pulsante rapido di **Logout** nella barra laterale.

2. **🏆 Tabellone & Classifiche:**
   - **Metriche generali:** Totale partite giocate, totale giocatori iscritti, media gol a partita.
   - **Classifica di Rendimento Dinamica:** calcolata in tempo reale con Pandas (PG, V, P, S, % Vittoria, Punti calcolati 3-1-0, ordinamento automatico per Punti > % Vittoria > PG).
   - **Scheda Singolo Giocatore:** statistiche individuali, bilancio presenze in Squadra A vs Squadra B e badge della **forma recente** (ultime 5 partite con indicatori visivi 🟢 V, 🟡 P, 🔴 S).

3. **➕ Aggiungi Nuova Partita (5 vs 5):**
   - Inserimento data, punteggio e selezione dei 5 componenti di Squadra A e 5 di Squadra B.
   - **Validazioni stringenti:** esattamente 5 giocatori per squadra, nessun giocatore duplicato tra le formazioni.
   - Aggiornamento automatico e istantaneo della classifica con invalidazione della cache (`st.cache_data.clear()`).

4. **👤 Anagrafica Giocatori:**
   - Iscrizione rapida di nuovi amici al gruppo con verifica automatica per evitare omonimi.
   - Tabella riepilogativa di tutti i giocatori registrati.

5. **📜 Storico Cronologico Partite:**
   - Visualizzazione a card grafiche di tutte le partite disputate (dalla più recente alla più vecchia) con formazioni, punteggio ed esito in evidenza.

6. **🔄 Doppia Modalità di Persistenza (Zero-Config Fallback):**
   - Supporto nativo per **Google Sheets** tramite `gspread` e `google-auth`.
   - **Fallback automatico su CSV locale** (`data/giocatori.csv` e `data/partite.csv`) in assenza di credenziali Google, per consentire il test immediato in locale senza alcuna configurazione iniziale.

---

## 🚀 Guida all'Esecuzione in Locale

### 1. Prerequisiti
Assicurati di avere installato **Python 3.8** o superiore sul tuo sistema.

### 2. Installazione delle dipendenze
Apri un terminale nella cartella del progetto ed esegui:

```bash
pip install -r requirements.txt
```

### 3. Avvio dell'Applicazione
Avvia l'app con Streamlit:

```bash
streamlit run app.py
```

L'applicazione si aprirà automaticamente nel browser all'indirizzo `http://localhost:8501`.
- **PIN di sblocco:** `5678`

---

## ☁️ Guida al Deploy su Streamlit Community Cloud

Puoi pubblicare gratuitamente l'applicazione online e condividerla su WhatsApp con i tuoi amici:

### Passo 1: Pubblicazione su GitHub
1. Crea una nuova repository su [GitHub](https://github.com/).
2. Carica tutti i file di questa cartella (`app.py`, `requirements.txt`, `.streamlit/config.toml`, `.streamlit/secrets.toml.example`, `README.md`).

### Passo 2: Creazione dell'App su Streamlit Cloud
1. Accedi a [share.streamlit.io](https://share.streamlit.io/) con il tuo account GitHub.
2. Clicca su **"New app"**.
3. Seleziona la tua repository, il branch `main` e come Main file path indica `app.py`.
4. Clicca su **"Deploy!"**.

### Passo 3: Collegamento a Google Sheets (Opzionale ma Consigliato)
Se vuoi che i dati siano salvati in modo permanente su un tuo Foglio Google:

1. Crea un nuovo **Foglio Google** con due fogli di lavoro (schede in basso):
   - `giocatori` (con colonne: `id_giocatore`, `nome_completo`, `data_creazione`)
   - `partite` (con colonne: `id_partita`, `data`, `squadra_a_giocatori`, `squadra_b_giocatori`, `gol_squadra_a`, `gol_squadra_b`, `esito`)
2. Crea un **Service Account** su [Google Cloud Console](https://console.cloud.google.com/) e genera una chiave in formato JSON.
3. Condividi il Foglio Google con l'indirizzo email del Service Account dandogli permessi di **Editor**.
4. Su Streamlit Cloud, vai nelle **Settings** della tua app -> **Secrets**, e incolla il contenuto seguendo il template fornito in `.streamlit/secrets.toml.example`.

---

## 📱 Mobile-First UX
L'interfaccia è stata ottimizzata per l'utilizzo su smartphone, garantendo:
- Font ad alta leggibilità e componenti verticali fluidi.
- Selettori multiselect veloci per comporre le formazioni direttamente a bordo campo.
- Card scattanti per consultare risultati e forma prima del fischio d'inizio!
