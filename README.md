# ⚽ Calcetto Stats & Manager - Web Application

Applicazione web professionale e mobile-first, sviluppata con **Streamlit**, **Pandas** e **Google Sheets**, per la gestione completa di statistiche, logistica convocazioni, bilanciamento squadre ELO e pagelle MVP per il calcetto tra amici.

---

## 🌟 Funzionalità Principali

### 1. 🔒 Controllo Accessi basato su PIN (RBAC)
- **👁️ PIN Sola Lettura (`5678`):**
  - Accesso completo in sola consultazione a classifiche, rating ELO, marcatori, storico partite, pagelle ed MVP.
  - I giocatori possono segnare la propria presenza per le partite convocate.
  - Funzioni di modifica, cancellazione e generazione squadre bloccate/nascoste.
- **🛡️ PIN Amministratore (`1234`):**
  - Permessi completi: registrazione e cancellazione partite con marcatori individuali, anagrafica giocatori, apertura/chiusura convocazioni, algoritmo di bilanciamento formazioni e reset dati.

---

### 2. 📊 Algoritmi Statistici Avanzati (`logic.py`)
- **⚡ Rating ELO Dinamico:**
  - Punteggio base di partenza fissato a **1500 punti** per ciascun giocatore.
  - Calcolo progressivo post-gara basato su forza media dei due team e **moltiplicatore scarto reti**:
    $$M = 1 + \ln(1 + |\Delta\text{gol}|), \quad \Delta R = K \cdot M \cdot (S_A - E_A)$$
- **⚽ Classifica Marcatori:**
  - Conteggio rigoroso dei soli gol individuali realizzati (esclusi gli assist).
  - Metriche: Gol Totali, Partite Giocate (PG), Media Gol a Partita.
- **🔥 Strisce di Vittorie Consecutive:**
  - Tracciamento della striscia vincente attualmente **aperta** e del **record storico personale**.
- **🤝 Coppie d'Oro & ⚔️ Rivali:**
  - **Coppie d'Oro:** Percentuale di vittoria per coppie di compagni di squadra (minimo 3 partite insieme).
  - **Rivali (Head-to-Head):** Statistiche negli scontri diretti quando due giocatori si affrontano da avversari.

---

### 3. 📅 Convocazioni & Bilanciamento Squadre
- **Modulo Presenze:**
  - Apertura sessione partita (data, ora, luogo).
  - Selezione rapida presenza/assenza con contatore visivo su target di **10 convocati**.
- **⚖️ Generatore Automatico Squadre Equilibrate (Admin):**
  - Algoritmo combinatorio che valuta tutte le $C(10,5)/2 = 126$ suddivisioni per minimizzare la differenza di somma ELO $|\sum ELO_A - \sum ELO_B|$.
  - Clic diretto per trasferire le formazioni nella schermata di registrazione partita.

---

### 4. ⭐ Pagelle ed Elezione MVP
- **Votazione Post-Partita:** Assegnazione voto (1-10 con step 0.5) e commento per ciascun giocatore sceso in campo.
- **Resoconto Automatico:**
  - 👑 **MVP della Partita** (giocatore con media voto più alta).
  - 🧊 **Menzione Peggiore in Campo** (giocatore con media voto più bassa).
  - Feed commenti e pagelle aggregate.

---

## 🗄️ Schemi Dati Google Sheets (`calcetto_db`)

Se colleghi l'app a Google Sheets, il foglio deve contenere **4 schede (fogli di lavoro)** con le seguenti colonne:

### 1. Scheda `giocatori`
| Colonna | Tipo | Descrizione |
|---|---|---|
| `id_giocatore` | Numero | ID progressivo univoco |
| `nome_completo` | Testo | Nome e cognome del giocatore |
| `data_creazione` | Testo (YYYY-MM-DD) | Data di inserimento |

### 2. Scheda `partite`
| Colonna | Tipo | Descrizione |
|---|---|---|
| `id_partita` | Numero | ID progressivo partita |
| `data` | Testo (YYYY-MM-DD) | Data di svolgimento |
| `squadra_a_giocatori` | Testo | 5 giocatori separati da virgola |
| `squadra_b_giocatori` | Testo | 5 giocatori separati da virgola |
| `gol_squadra_a` | Numero | Gol realizzati da Squadra A |
| `gol_squadra_b` | Numero | Gol realizzati da Squadra B |
| `esito` | Testo | Es. *Vittoria Squadra A*, *Pareggio*, *Vittoria Squadra B* |
| `marcatori` | Testo (JSON) | Es. `{"Marco Rossi": 3, "Luca Bianchi": 2}` |

### 3. Scheda `convocazioni`
| Colonna | Tipo | Descrizione |
|---|---|---|
| `id_convocazione` | Numero | ID sessione convocazione |
| `data_partita` | Testo (YYYY-MM-DD) | Data del match in programma |
| `ora_partita` | Testo (HH:MM) | Orario inizio |
| `luogo` | Testo | Campo o impianto sportivo |
| `stato` | Testo | `Aperta` oppure `Chiusa` |
| `presenti` | Testo | Elenco presenti separati da virgola |
| `assenti` | Testo | Elenco assenti separati da virgola |

### 4. Scheda `voti`
| Colonna | Tipo | Descrizione |
|---|---|---|
| `id_voto` | Numero | ID univoco del voto |
| `id_partita` | Numero | ID della partita valutata |
| `votante` | Testo | Nome di chi compila la pagella |
| `giocatore` | Testo | Nome del giocatore valutato |
| `voto` | Numero (1.0 - 10.0) | Valutazione assegnata |
| `commento` | Testo | Commento testuale (opzionale) |
| `timestamp` | Testo (YYYY-MM-DD HH:MM:SS) | Data e ora della votazione |

*(In assenza di Google Sheets, l'applicazione usa automaticamente i file CSV equivalenti in `data/`)*.

---

## 🚀 Esecuzione in Locale

```bash
# 1. Installazione dipendenze
pip install -r requirements.txt

# 2. Avvio app Streamlit
streamlit run app.py
```

- **PIN Viewer (Sola Lettura):** `5678`
- **PIN Amministratore:** `1234`
