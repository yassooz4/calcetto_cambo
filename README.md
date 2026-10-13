# ⚽ Calcetto Stats & Manager - Web Application

Applicazione web professionale e mobile-first, sviluppata con **Streamlit**, **Pandas** e **Google Sheets**, per la gestione completa di statistiche, bilanciamento squadre ELO e votazioni riservate MVP e peggiore per il calcetto tra amici.

---

## 🌟 Funzionalità Principali

### 1. 🔒 Accesso e riservatezza
- **Viewer (`5678`):** consultazione delle statistiche e dei risultati pubblicati. Per votare serve inoltre la password personale del giocatore.
- **Amministratore:** PIN di 4 cifre configurato nei Secrets di Streamlit (`auth.admin_pin`), verificato esclusivamente sul server. Non usare i precedenti PIN pubblici.
- **Password giocatori:** 5 cifre, anche con zeri iniziali, 100.000 combinazioni. Codici unici generati nell'app e visibili accanto ai nomi soltanto nella sezione amministrativa Password Giocatori.
- Il tastierino di ingresso non riceve i PIN validi dal server. Le sessioni amministrative precedenti vengono invalidate quando cambia il PIN.

---

### 2. 📊 Algoritmi Statistici Avanzati (`logic.py`)
- **⚡ Rating ELO Dinamico:**
  - Punteggio base di partenza fissato a **1500 punti** per ciascun giocatore.
  - Calcolo progressivo post-gara basato su forza media dei due team e **moltiplicatore scarto reti**:
    $$M = 1 + \ln(1 + |\Delta\text{gol}|), \quad \Delta R = K \cdot M \cdot (S_A - E_A)$$
- **⚽ Classifica Marcatori:**
  - Conteggio rigoroso dei soli gol individuali realizzati (esclusi gli assist).
  - Metriche: Gol Totali, Partite Giocate (PG), Media Gol a Partita.
- **🎴 OVR delle carte — Rating Cambo (`ratings.py`, `rating_ui.py`):**
  - `OVR = round(0.80 × rendimento complessivo + 0.20 × rendimento ultime 5 partite giocate)`. Entrambi usano `45% GOL + 45% RIS + 10% MVP`, con precisione completa fino all'arrotondamento finale.
  - La scala è 50–99. La calibrazione pubblica della stagione 2026/27 è congelata in `rating_calibration.json`: 7 partite, 70 presenze, 21 giocatori, 11 con almeno tre presenze. Il 95° percentile delle loro medie gol, arrotondato per eccesso a 0,25, dà **3,25 gol/partita** come riferimento. Le medie iniziali sono 139/70 gol/partita e il 50% dei punti possibili. Sono regole di progetto, non standard scientifici.
  - **Pochi dati:** ogni periodo usa 5 partite equivalenti alla media iniziale per attenuare gol e risultati: `gol_stimati = (gol + 5 × media_iniziale_gol) / (PG + 5)`; `risultati_stimati = (punti_corretti / 3 + 5 × media_iniziale_risultati) / (PG + 5)`. Le presenze non sono un attributo e non danno bonus.
  - **Difficoltà:** il contesto rigioca l'archivio completo e registra la probabilità ELO prima di ciascuna gara. `punti_corretti = punti × (1.5 − probabilità_prepartita)`; vittoria 3, pareggio 1, sconfitta 0. Vittorie da sfavoriti pesano di più. Gli aggiornamenti ELO mantengono algoritmo, scarto reti e arrotondamento esistenti; il generatore continua a bilanciare tramite ELO.
  - Indici: `GOL = 50 + 49 × clamp(gol_stimati / riferimento, 0, 1)`; `RIS = 50 + 49 × clamp(risultati_stimati, 0, 1)`; `MVP = 50 + 49 × titoli / (partite con MVP pubblicato + 5)`. Un MVP su una votazione dà un indice di circa 58, non 99. Votazioni aperte escluse, nessun risultato significa nessun bonus. Titoli ex aequo e titoli storici pubblicati inclusi.
  - **Scheda:** tre componenti con medie gol, percentuale vittorie e MVP su partite votate; tre barre di confronto con la media dei giocatori attivi. La forma recente è un indicatore separato, già compreso nell'OVR, e non un quarto asse.
  - **Andamento:** OVR ricostruito dopo ogni partita, variazione dall'ultima gara e spiegazione dei componenti che la determinano. Si applicano il modello corrente e i risultati MVP oggi pubblicati: correggere partite o riaprire votazioni può cambiare anche il passato. Non sono istantanee salvate all'epoca delle gare.
  - Senza partite: “Non ancora valutato”, nessun numero inventato. Sotto 5 presenze: OVR provvisorio; superare la soglia non certifica affidabilità statistica. Il confronto esclude chi non ha giocato.
  - Il filtro della cerchia si applica a statistiche, titoli, periodo recente e andamento. La scala stagionale e la forza ELO prepartita restano quelle dell'archivio completo. Non entrano assist, assenze o titoli di peggiore. Difesa e contributo dei portieri non sono direttamente misurati.
  - **Nuova calibrazione:** `ratings.calibrate_season(df_partite, stagione, data)` produce un nuovo snapshot pubblico con soli aggregati e ID partita. Salvare intenzionalmente il risultato in `rating_calibration.json` per una nuova stagione; non ricalibrare a ogni nuova gara, filtro o apertura della pagina. Nessun dato privato o credenziale entra nello snapshot.
- **🔥 Strisce di Vittorie Consecutive:**
  - Tracciamento della striscia vincente attualmente **aperta** e del **record storico personale**.
- **🤝 Coppie d'Oro & ⚔️ Rivali:**
  - **Coppie d'Oro:** Percentuale di vittoria per coppie di compagni di squadra (minimo 3 partite insieme).
  - **Rivali (Head-to-Head):** Statistiche negli scontri diretti quando due giocatori si affrontano da avversari.

---

### 3. ⚖️ Generatore Automatico Squadre Equilibrate (Admin)
- Sezione autonoma con selezione diretta di 10 giocatori dall'anagrafica, senza sessioni di convocazione o registrazione presenze.
- Algoritmo combinatorio che valuta tutte le $C(10,5)/2 = 126$ suddivisioni per minimizzare la differenza di somma ELO tra le squadre.
- Visualizzazione delle formazioni sul campo e confronto dei valori ELO.
- Clic diretto per trasferire le formazioni nella schermata di registrazione partita.

---

### 4. 👑 MVP & Peggiore
- Ogni partecipante accede con la propria password personale. Il server riconosce automaticamente il votante.
- Due sole scelte: MVP e peggiore, fra i giocatori della partita, escludendo sé stessi. Le due scelte devono essere diverse.
- Un voto per persona e partita: nuovi invii aggiornano le scelte precedenti, senza duplicare il conteggio.
- Solo l'amministratore può consultare il registro dei votanti e le loro scelte, il conteggio provvisorio e chi deve ancora votare.
- L'amministratore chiude manualmente la votazione e pubblica il risultato. Dopo la chiusura i giocatori non possono modificare i voti.
- In caso di parità, tutti i primi classificati ricevono il titolo ex aequo. Una riapertura ritira il risultato pubblico finché non viene chiusa nuovamente.
- Le classifiche e lo storico usano esclusivamente i risultati finali. I titoli delle precedenti pagelle numeriche restano nell'archivio finché non viene avviata una nuova votazione per quella partita.
- Password e schede personali sono cifrate con Fernet nell'archivio Google Sheets. Le scritture sono append-only e serializzate nel singolo processo Streamlit, senza riscrivere l'intero foglio. Se il cloud non risponde, il voto non passa silenziosamente al CSV locale.

### Configurazione prima della pubblicazione
Aggiungere ai **Secrets di Streamlit Cloud**, senza rimuovere le impostazioni Google esistenti:

```toml
[auth]
admin_pin = "NUOVO_PIN_DI_4_CIFRE"
voting_key = "CHIAVE_FERNET_GENERATA_PRIVATAMENTE"
```

La chiave può essere generata localmente con `Fernet.generate_key()` dalla libreria cryptography. Conservare una copia privata: cambiarla senza migrare l'archivio rende illeggibili password e voti esistenti. Non inserire credenziali reali in GitHub.

Il foglio `votazioni_private` viene creato automaticamente al primo accesso amministrativo a Password Giocatori; contiene una sola colonna `payload` con eventi cifrati. I dati CSV storici restano invariati. In sviluppo senza Google Sheets, l'archivio cifrato è `data/votazioni_private.jsonl`, escluso da Git.

Prima di unire la modifica a main, impostare entrambi i segreti; altrimenti l'accesso amministratore e le nuove votazioni rimangono disabilitati.

---

## 🗄️ Schemi Dati Google Sheets (`calcetto_db`)

Se colleghi l'app a Google Sheets, l'archivio storico contiene **4 schede (fogli di lavoro)**; la nuova scheda privata viene creata automaticamente con le seguenti colonne:

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

### 3. Scheda `convocazioni` (compatibilità archivio)

La scheda è conservata per compatibilità con gli archivi esistenti; non è utilizzata dal generatore e non è più gestita dall'interfaccia.

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
- **PIN Amministratore:** il valore privato configurato in `auth.admin_pin`


## Verifiche

```bash
python -m unittest -q test_voting.py test_voting_ui.py test_ovr.py test_ovr_ui.py
```

I test usano giocatori fittizi e archivi isolati; non accedono ai dati di produzione.
