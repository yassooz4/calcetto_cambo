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
- **🎴 OVR delle carte — Rating Cambo:**
  - `OVR = round(0.80 × rendimento complessivo + 0.20 × rendimento ultime 5 partite giocate)`.
  - Entrambi i rendimenti usano gli stessi pesi: `45% GOL + 45% RIS + 10% MVP`, con precisione completa fino all'arrotondamento dell'OVR finale.
  - Indici sulla scala 50–99: `GOL = 50 + 49 × min(media gol / 3.5, 1)`; `RIS = 50 + 49 × punti / (3 × partite giocate)`; `MVP = 50 + 49 × titoli / partite con risultato MVP pubblicato`. Vittoria 3 punti, pareggio 1, sconfitta 0. Il riferimento di 3,5 gol è una regola scelta per questa scala, non uno standard statistico.
  - Le votazioni aperte non entrano nel denominatore MVP; in assenza di risultati pubblicati l'indice resta al valore base 50, senza bonus. I titoli ex aequo e quelli storici conservati sono inclusi.
  - Senza partite la carta mostra “Non ancora valutato” e nessun numero inventato. Con meno di 5 presenze l'OVR è provvisorio; questa è una soglia di presentazione e non una certificazione di affidabilità statistica.
  - Il filtro della cerchia si applica a tutti i dati, inclusi i titoli MVP. La media del radar esclude chi non ha giocato nel periodo selezionato.
  - ELO, presenze, titoli di peggiore e assist non fanno parte dell'OVR. Le formazioni mostrano lo stesso OVR delle carte; il bilanciamento continua a usare l'ELO.
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
