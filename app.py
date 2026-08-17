"""
================================================================================
CALCETTO STATS - Web Application per Statistiche di Calcetto tra Amici
Stack: Streamlit, Pandas, gspread, google-auth
================================================================================
"""

import os
from datetime import date, datetime
import pandas as pd
import streamlit as st

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

# ==============================================================================
# CONFIGURAZIONE PAGINA & TEMA
# ==============================================================================
st.set_page_config(
    page_title="Calcetto Stats",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="auto"
)

# Custom CSS Mobile-First e Stile Moderno
st.markdown("""
<style>
    /* Stili Globali */
    .main-title {
        font-size: 1.8rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
        color: #10b981;
    }
    .sub-title {
        font-size: 0.95rem;
        color: #94a3b8;
        margin-bottom: 1.2rem;
    }
    
    /* Card per storico partite */
    .match-card {
        background-color: #1e293b;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 5px solid #10b981;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .match-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
        font-weight: 600;
        font-size: 0.9rem;
        color: #94a3b8;
    }
    .match-score {
        font-size: 1.4rem;
        font-weight: 800;
        text-align: center;
        margin: 0.5rem 0;
        color: #f8fafc;
    }
    .team-box {
        font-size: 0.88rem;
        line-height: 1.4;
        color: #cbd5e1;
    }
    .team-title {
        font-weight: 700;
        color: #38bdf8;
    }
    .team-title-b {
        font-weight: 700;
        color: #f43f5e;
    }
    
    /* Badge Forma */
    .badge-v {
        display: inline-block;
        background-color: #10b981;
        color: white;
        font-weight: bold;
        border-radius: 6px;
        padding: 2px 8px;
        margin: 2px;
        font-size: 0.85rem;
    }
    .badge-p {
        display: inline-block;
        background-color: #eab308;
        color: #0f172a;
        font-weight: bold;
        border-radius: 6px;
        padding: 2px 8px;
        margin: 2px;
        font-size: 0.85rem;
    }
    .badge-s {
        display: inline-block;
        background-color: #ef4444;
        color: white;
        font-weight: bold;
        border-radius: 6px;
        padding: 2px 8px;
        margin: 2px;
        font-size: 0.85rem;
    }
    
    /* Mobile tweaks */
    @media (max-width: 768px) {
        .main-title {
            font-size: 1.5rem;
        }
        .match-score {
            font-size: 1.2rem;
        }
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# COSTANTI & CONFIGURAZIONE AMBIENTE
# ==============================================================================
PIN_CORRETTO = "5678"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CSV_GIOCATORI = os.path.join(DATA_DIR, "giocatori.csv")
CSV_PARTITE = os.path.join(DATA_DIR, "partite.csv")

# Dati di default per inizializzazione locale
GIOCATORI_DEFAULT = [
    {"id_giocatore": 1, "nome_completo": "Marco Rossi", "data_creazione": "2024-01-10"},
    {"id_giocatore": 2, "nome_completo": "Luca Bianchi", "data_creazione": "2024-01-10"},
    {"id_giocatore": 3, "nome_completo": "Matteo Ferrari", "data_creazione": "2024-01-10"},
    {"id_giocatore": 4, "nome_completo": "Alessandro Russo", "data_creazione": "2024-01-10"},
    {"id_giocatore": 5, "nome_completo": "Davide Colombo", "data_creazione": "2024-01-10"},
    {"id_giocatore": 6, "nome_completo": "Federico Ricci", "data_creazione": "2024-01-10"},
    {"id_giocatore": 7, "nome_completo": "Andrea Marino", "data_creazione": "2024-01-10"},
    {"id_giocatore": 8, "nome_completo": "Lorenzo Greco", "data_creazione": "2024-01-10"},
    {"id_giocatore": 9, "nome_completo": "Simone Bruno", "data_creazione": "2024-01-10"},
    {"id_giocatore": 10, "nome_completo": "Gabriele Gallo", "data_creazione": "2024-01-10"},
    {"id_giocatore": 11, "nome_completo": "Francesco Conti", "data_creazione": "2024-01-15"},
    {"id_giocatore": 12, "nome_completo": "Giovanni De Luca", "data_creazione": "2024-01-15"},
]

PARTITE_DEFAULT = [
    {
        "id_partita": 1,
        "data": "2024-02-01",
        "squadra_a_giocatori": "Marco Rossi, Luca Bianchi, Matteo Ferrari, Alessandro Russo, Davide Colombo",
        "squadra_b_giocatori": "Federico Ricci, Andrea Marino, Lorenzo Greco, Simone Bruno, Gabriele Gallo",
        "gol_squadra_a": 7,
        "gol_squadra_b": 5,
        "esito": "Vittoria Squadra A"
    },
    {
        "id_partita": 2,
        "data": "2024-02-08",
        "squadra_a_giocatori": "Marco Rossi, Luca Bianchi, Francesco Conti, Giovanni De Luca, Davide Colombo",
        "squadra_b_giocatori": "Matteo Ferrari, Alessandro Russo, Andrea Marino, Lorenzo Greco, Gabriele Gallo",
        "gol_squadra_a": 4,
        "gol_squadra_b": 4,
        "esito": "Pareggio"
    }
]


# ==============================================================================
# GESTIONE PERSISTENZA (GOOGLE SHEETS CON GSPREAD & FALLBACK LOCALE CSV)
# ==============================================================================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def get_gsheets_config():
    """Recupera la configurazione e le credenziali di Google Sheets dai segreti di Streamlit."""
    try:
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            return dict(st.secrets["connections"]["gsheets"])
        elif "gspread" in st.secrets:
            return dict(st.secrets["gspread"])
        elif "service_account" in st.secrets:
            return dict(st.secrets["service_account"])
    except Exception:
        pass
    return None


def is_gsheets_configured() -> bool:
    """Verifica se le credenziali di Google Sheets sono definite nei segreti di Streamlit."""
    if not GSPREAD_AVAILABLE:
        return False
    cfg = get_gsheets_config()
    return cfg is not None and len(cfg) > 0


def get_gsheets_spreadsheet():
    """Inizializza la connessione a Google Sheets tramite gspread e apre lo spreadsheet."""
    if not is_gsheets_configured():
        return None
    try:
        cfg = get_gsheets_config()
        if not cfg:
            return None
        
        spreadsheet_target = (
            cfg.get("spreadsheet")
            or cfg.get("spreadsheet_url")
            or cfg.get("url")
            or cfg.get("sheet_id")
            or cfg.get("spreadsheet_name")
        )
        
        sa_keys = [
            "type", "project_id", "private_key_id", "private_key",
            "client_email", "client_id", "auth_uri", "token_uri",
            "auth_provider_x509_cert_url", "client_x509_cert_url", "universe_domain"
        ]
        sa_info = {k: cfg[k] for k in sa_keys if k in cfg}
        
        if "private_key" in sa_info and isinstance(sa_info["private_key"], str):
            sa_info["private_key"] = sa_info["private_key"].replace("\\n", "\n")
            
        creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)
        client = gspread.authorize(creds)
        
        if not spreadsheet_target:
            return None
            
        spreadsheet_target = str(spreadsheet_target).strip()
        if spreadsheet_target.startswith("http://") or spreadsheet_target.startswith("https://"):
            return client.open_by_url(spreadsheet_target)
        elif len(spreadsheet_target) > 30 and " " not in spreadsheet_target:
            try:
                return client.open_by_key(spreadsheet_target)
            except Exception:
                return client.open(spreadsheet_target)
        else:
            return client.open(spreadsheet_target)
    except Exception:
        return None


def read_worksheet_as_df(sh, worksheet_name: str) -> pd.DataFrame:
    """Legge un foglio di lavoro da gspread e restituisce un DataFrame pandas."""
    try:
        worksheet = sh.worksheet(worksheet_name)
    except Exception:
        return pd.DataFrame()
    
    values = worksheet.get_all_values()
    if not values or len(values) == 0:
        return pd.DataFrame()
    
    headers = [str(h).strip() for h in values[0]]
    rows = values[1:]
    if not rows:
        return pd.DataFrame(columns=headers)
        
    df = pd.DataFrame(rows, columns=headers)
    return df


def write_df_to_worksheet(sh, worksheet_name: str, df: pd.DataFrame):
    """Scrive un DataFrame pandas su un foglio di lavoro gspread."""
    try:
        worksheet = sh.worksheet(worksheet_name)
    except Exception:
        rows_needed = max(100, len(df) + 10)
        cols_needed = max(20, len(df.columns) + 2)
        worksheet = sh.add_worksheet(title=worksheet_name, rows=rows_needed, cols=cols_needed)
    
    headers = list(df.columns)
    data_rows = df.fillna("").astype(str).values.tolist()
    all_values = [headers] + data_rows
    
    worksheet.clear()
    worksheet.update(range_name="A1", values=all_values)


def init_local_storage():
    """Inizializza la cartella locale e i file CSV di fallback se non esistono."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    
    if not os.path.exists(CSV_GIOCATORI):
        df_gio = pd.DataFrame(GIOCATORI_DEFAULT)
        df_gio.to_csv(CSV_GIOCATORI, index=False)
        
    if not os.path.exists(CSV_PARTITE):
        df_par = pd.DataFrame(PARTITE_DEFAULT)
        df_par.to_csv(CSV_PARTITE, index=False)


@st.cache_data(ttl=300)
def load_data():
    """
    Carica i dataframe 'giocatori' e 'partite'.
    Usa Google Sheets tramite gspread se configurato, altrimenti usa il fallback locale CSV.
    """
    sh = get_gsheets_spreadsheet()
    
    if sh is not None:
        try:
            # Lettura da Google Sheets
            df_giocatori = read_worksheet_as_df(sh, "giocatori")
            df_partite = read_worksheet_as_df(sh, "partite")
            
            # Sanitizzazione colonne giocatori
            if df_giocatori is None or (df_giocatori.empty and "nome_completo" not in df_giocatori.columns):
                df_giocatori = pd.DataFrame(columns=["id_giocatore", "nome_completo", "data_creazione"])
                try:
                    write_df_to_worksheet(sh, "giocatori", df_giocatori)
                except Exception:
                    pass
            else:
                if "nome_completo" in df_giocatori.columns:
                    df_giocatori = df_giocatori.dropna(subset=["nome_completo"])
                    df_giocatori = df_giocatori[df_giocatori["nome_completo"].astype(str).str.strip() != ""]
                
            # Sanitizzazione colonne partite
            if df_partite is None or (df_partite.empty and "id_partita" not in df_partite.columns):
                df_partite = pd.DataFrame(columns=[
                    "id_partita", "data", "squadra_a_giocatori", 
                    "squadra_b_giocatori", "gol_squadra_a", "gol_squadra_b", "esito"
                ])
                try:
                    write_df_to_worksheet(sh, "partite", df_partite)
                except Exception:
                    pass
            else:
                if "id_partita" in df_partite.columns:
                    df_partite = df_partite.dropna(subset=["id_partita"])
                    df_partite = df_partite[df_partite["id_partita"].astype(str).str.strip() != ""]
                
            # Conversione tipi
            if not df_giocatori.empty and "id_giocatore" in df_giocatori.columns:
                df_giocatori["id_giocatore"] = pd.to_numeric(df_giocatori["id_giocatore"], errors="coerce").fillna(0).astype(int)
            if not df_partite.empty:
                if "id_partita" in df_partite.columns:
                    df_partite["id_partita"] = pd.to_numeric(df_partite["id_partita"], errors="coerce").fillna(0).astype(int)
                if "gol_squadra_a" in df_partite.columns:
                    df_partite["gol_squadra_a"] = pd.to_numeric(df_partite["gol_squadra_a"], errors="coerce").fillna(0).astype(int)
                if "gol_squadra_b" in df_partite.columns:
                    df_partite["gol_squadra_b"] = pd.to_numeric(df_partite["gol_squadra_b"], errors="coerce").fillna(0).astype(int)
                    
            return df_giocatori, df_partite, "Google Sheets"
        except Exception:
            # Fallback su locale in caso di errore
            pass
            
    # Fallback locale CSV
    init_local_storage()
    df_giocatori = pd.read_csv(CSV_GIOCATORI)
    df_partite = pd.read_csv(CSV_PARTITE)
    
    # Conversione corretta dei tipi
    if not df_giocatori.empty and "id_giocatore" in df_giocatori.columns:
        df_giocatori["id_giocatore"] = pd.to_numeric(df_giocatori["id_giocatore"], errors="coerce").fillna(0).astype(int)
    if not df_partite.empty:
        if "id_partita" in df_partite.columns:
            df_partite["id_partita"] = pd.to_numeric(df_partite["id_partita"], errors="coerce").fillna(0).astype(int)
        if "gol_squadra_a" in df_partite.columns:
            df_partite["gol_squadra_a"] = pd.to_numeric(df_partite["gol_squadra_a"], errors="coerce").fillna(0).astype(int)
        if "gol_squadra_b" in df_partite.columns:
            df_partite["gol_squadra_b"] = pd.to_numeric(df_partite["gol_squadra_b"], errors="coerce").fillna(0).astype(int)
        
    return df_giocatori, df_partite, "Locale (CSV)"


def save_giocatori(df_giocatori: pd.DataFrame):
    """Salva il dataframe giocatori su GSheets o su CSV locale."""
    sh = get_gsheets_spreadsheet()
    if sh is not None:
        try:
            write_df_to_worksheet(sh, "giocatori", df_giocatori)
            st.cache_data.clear()
            return True
        except Exception:
            pass
    # Fallback locale
    init_local_storage()
    df_giocatori.to_csv(CSV_GIOCATORI, index=False)
    st.cache_data.clear()
    return True


def save_partite(df_partite: pd.DataFrame):
    """Salva il dataframe partite su GSheets o su CSV locale."""
    sh = get_gsheets_spreadsheet()
    if sh is not None:
        try:
            write_df_to_worksheet(sh, "partite", df_partite)
            st.cache_data.clear()
            return True
        except Exception:
            pass
    # Fallback locale
    init_local_storage()
    df_partite.to_csv(CSV_PARTITE, index=False)
    st.cache_data.clear()
    return True



# ==============================================================================
# LOGICA DI CALCOLO CLASSIFICHE & STATISTICHE (PANDAS)
# ==============================================================================
def calculate_leaderboard(df_giocatori: pd.DataFrame, df_partite: pd.DataFrame) -> pd.DataFrame:
    """
    Calcola la classifica generale dei giocatori basandosi sulle partite registrate.
    Restituisce un dataframe con: Giocatore, PG, V, P, S, % Vittoria, Punti.
    Ordinamento: Punti DESC -> % Vittoria DESC -> PG DESC.
    """
    if df_giocatori.empty:
        return pd.DataFrame(columns=["Giocatore", "PG", "V", "P", "S", "% Vittoria", "Punti"])

    # Inizializza statistiche base per ogni giocatore iscritto
    stats = {}
    for _, row in df_giocatori.iterrows():
        nome = str(row["nome_completo"]).strip()
        stats[nome] = {"PG": 0, "V": 0, "P": 0, "S": 0}

    # Elaborazione di ciascuna partita
    if not df_partite.empty:
        for _, match in df_partite.iterrows():
            # Estrarre giocatori squadra A e B
            raw_a = str(match.get("squadra_a_giocatori", ""))
            raw_b = str(match.get("squadra_b_giocatori", ""))
            
            sq_a = [p.strip() for p in raw_a.split(",") if p.strip()]
            sq_b = [p.strip() for p in raw_b.split(",") if p.strip()]
            
            gol_a = int(match.get("gol_squadra_a", 0))
            gol_b = int(match.get("gol_squadra_b", 0))
            
            # Assegnazione esito
            if gol_a > gol_b:
                esito_a, esito_b = "V", "S"
            elif gol_b > gol_a:
                esito_a, esito_b = "S", "V"
            else:
                esito_a, esito_b = "P", "P"

            for player in sq_a:
                if player in stats:
                    stats[player]["PG"] += 1
                    stats[player][esito_a] += 1

            for player in sq_b:
                if player in stats:
                    stats[player]["PG"] += 1
                    stats[player][esito_b] += 1

    # Creazione della tabella riassuntiva
    rows = []
    for player, s in stats.items():
        pg = s["PG"]
        v = s["V"]
        p = s["P"]
        sc = s["S"]
        punti = (v * 3) + (p * 1)
        win_rate = round((v / pg * 100), 1) if pg > 0 else 0.0

        rows.append({
            "Giocatore": player,
            "Punti": punti,
            "PG": pg,
            "V": v,
            "P": p,
            "S": sc,
            "% Vittoria": win_rate
        })

    df_result = pd.DataFrame(rows)
    if not df_result.empty:
        # Ordinamento: Punti DESC -> % Vittoria DESC -> PG DESC
        df_result = df_result.sort_values(
            by=["Punti", "% Vittoria", "PG", "Giocatore"],
            ascending=[False, False, False, True]
        ).reset_index(drop=True)

    return df_result


def get_player_details(player_name: str, df_partite: pd.DataFrame) -> dict:
    """Calcola lo storico dettagliato e la forma recente di un singolo giocatore."""
    if df_partite.empty:
        return {"presenze_a": 0, "presenze_b": 0, "totale": 0, "forma": [], "gol_fatti_squadre": 0}

    # Ordina cronologicamente le partite (dalla più recente alla più vecchia)
    df_sorted = df_partite.sort_values(by=["data", "id_partita"], ascending=[False, False])

    presenze_a = 0
    presenze_b = 0
    forma = []
    
    for _, match in df_sorted.iterrows():
        raw_a = [p.strip() for p in str(match.get("squadra_a_giocatori", "")).split(",") if p.strip()]
        raw_b = [p.strip() for p in str(match.get("squadra_b_giocatori", "")).split(",") if p.strip()]
        gol_a = int(match.get("gol_squadra_a", 0))
        gol_b = int(match.get("gol_squadra_b", 0))

        if player_name in raw_a:
            presenze_a += 1
            if gol_a > gol_b:
                forma.append("V")
            elif gol_a < gol_b:
                forma.append("S")
            else:
                forma.append("P")
        elif player_name in raw_b:
            presenze_b += 1
            if gol_b > gol_a:
                forma.append("V")
            elif gol_b < gol_a:
                forma.append("S")
            else:
                forma.append("P")

    return {
        "presenze_a": presenze_a,
        "presenze_b": presenze_b,
        "totale": presenze_a + presenze_b,
        "forma": forma[:5],  # ultime 5 partite
    }


# ==============================================================================
# SISTEMA DI AUTENTICAZIONE (PIN GATE)
# ==============================================================================
def render_pin_gate():
    """Mostra la schermata di blocco per inserire il PIN di sicurezza."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; font-size: 3.5rem;'>⚽🔒</div>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #10b981;'>Calcetto Stats</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8;'>Inserisci il PIN per accedere alla gestione statistiche</p>", unsafe_allow_html=True)
        
        with st.form("pin_form", clear_on_submit=False):
            pin_input = st.text_input("PIN di Accesso", type="password", placeholder="••••", max_chars=10)
            submit_btn = st.form_submit_button("Sblocca Applicazione 🔓", use_container_width=True)
            
            if submit_btn:
                if pin_input.strip() == PIN_CORRETTO:
                    st.session_state["authenticated"] = True
                    st.success("Accesso eseguito con successo!")
                    st.rerun()
                else:
                    st.error("PIN non corretto. Riprova.")


# ==============================================================================
# VISTA A: TABELLONE & CLASSIFICHE (DASHBOARD)
# ==============================================================================
def view_dashboard(df_giocatori: pd.DataFrame, df_partite: pd.DataFrame, storage_source: str):
    st.markdown("<div class='main-title'>🏆 Tabellone & Classifiche</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-title'>Panoramica rendimento generale • Sorgente dati: <b>{storage_source}</b></div>", unsafe_allow_html=True)

    # 1. Metriche Generali in Alto
    tot_partite = len(df_partite)
    tot_giocatori = len(df_giocatori)
    
    if tot_partite > 0:
        tot_gol = df_partite["gol_squadra_a"].sum() + df_partite["gol_squadra_b"].sum()
        media_gol = round(tot_gol / tot_partite, 1)
    else:
        media_gol = 0.0

    m1, m2, m3 = st.columns(3)
    m1.metric("⚽ Partite Giocate", f"{tot_partite}")
    m2.metric("👥 Giocatori Iscritti", f"{tot_giocatori}")
    m3.metric("🎯 Media Gol / Gara", f"{media_gol}")

    st.markdown("---")

    # 2. Classifica Generale Rendimento
    st.markdown("### 🥇 Classifica Generale")
    df_rank = calculate_leaderboard(df_giocatori, df_partite)
    
    if df_rank.empty:
        st.info("Nessun dato disponibile. Inizia aggiungendo giocatori e registrando la prima partita!")
    else:
        # Formattazione per la visualizzazione
        df_display = df_rank.copy()
        df_display["Pos."] = range(1, len(df_display) + 1)
        df_display["% Vittoria"] = df_display["% Vittoria"].apply(lambda x: f"{x:.1f}%")
        
        # Riordino colonne
        cols = ["Pos.", "Giocatore", "Punti", "PG", "V", "P", "S", "% Vittoria"]
        df_display = df_display[cols]
        
        # Mostra tabella responsive
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Pos.": st.column_config.NumberColumn("Pos.", width="small"),
                "Giocatore": st.column_config.TextColumn("Giocatore", width="medium"),
                "Punti": st.column_config.NumberColumn("Punti 🏆", help="3 per V, 1 per P, 0 per S"),
                "PG": st.column_config.NumberColumn("PG", help="Partite Giocate"),
                "V": st.column_config.NumberColumn("V", help="Vittorie"),
                "P": st.column_config.NumberColumn("P", help="Pareggi"),
                "S": st.column_config.NumberColumn("S", help="Sconfitte"),
                "% Vittoria": st.column_config.TextColumn("% Vittoria", help="(Vittorie / PG) * 100"),
            }
        )

    st.markdown("---")

    # 3. Scheda Statistiche Individuali (Player Spotlight)
    st.markdown("### 🔍 Scheda Singolo Giocatore")
    
    lista_giocatori = sorted(df_giocatori["nome_completo"].dropna().unique().tolist()) if not df_giocatori.empty else []
    
    if not lista_giocatori:
        st.info("Nessun giocatore registrato.")
    else:
        selected_player = st.selectbox("Seleziona un giocatore per visualizzare lo storico:", options=lista_giocatori)
        
        if selected_player:
            details = get_player_details(selected_player, df_partite)
            
            p_col1, p_col2 = st.columns([1, 1])
            with p_col1:
                st.markdown(f"#### Statistiche di **{selected_player}**")
                st.write(f"- **Presenze Totali:** {details['totale']}")
                st.write(f"- 🟦 **In Squadra A:** {details['presenze_a']} volte")
                st.write(f"- 🟥 **In Squadra B:** {details['presenze_b']} volte")
                
            with p_col2:
                st.markdown("#### Forma Recente (Ultime 5 partite)")
                if details["forma"]:
                    badges_html = ""
                    for res in details["forma"]:
                        if res == "V":
                            badges_html += "<span class='badge-v'>V</span>"
                        elif res == "P":
                            badges_html += "<span class='badge-p'>P</span>"
                        else:
                            badges_html += "<span class='badge-s'>S</span>"
                    st.markdown(badges_html, unsafe_allow_html=True)
                    st.caption("Ordine da sinistra a destra: dalla più recente alla meno recente.")
                else:
                    st.write("Nessuna partita disputata finora.")


# ==============================================================================
# VISTA B: AGGIUNGI NUOVA PARTITA
# ==============================================================================
def view_add_match(df_giocatori: pd.DataFrame, df_partite: pd.DataFrame):
    st.markdown("<div class='main-title'>➕ Registra Nuova Partita</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Inserisci data, risultato e formazioni 5 vs 5</div>", unsafe_allow_html=True)

    lista_giocatori = sorted(df_giocatori["nome_completo"].dropna().unique().tolist()) if not df_giocatori.empty else []
    
    if len(lista_giocatori) < 10:
        st.warning(f"⚠️ Servono almeno 10 giocatori registrati nell'anagrafica per creare una partita 5 vs 5. Attualmente disponibili: **{len(lista_giocatori)}**.")
        st.info("👉 Vai nella sezione **'👥 Aggiungi Giocatore'** per iscrivere nuovi amici.")
        return

    with st.form("form_nuova_partita", clear_on_submit=False):
        # Data della partita
        data_partita = st.date_input("📅 Data Partita", value=date.today())
        
        st.markdown("#### ⚽ Risultato Finale")
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            gol_a = st.number_input("Gol Squadra A 🟦", min_value=0, max_value=50, value=0, step=1)
        with r_col2:
            gol_b = st.number_input("Gol Squadra B 🟥", min_value=0, max_value=50, value=0, step=1)

        st.markdown("---")
        st.markdown("#### 👥 Formazioni (Esattamente 5 giocatori per squadra)")
        
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            st.markdown("##### 🟦 Squadra A")
            sq_a = st.multiselect(
                "Seleziona i 5 giocatori di Squadra A:",
                options=lista_giocatori,
                max_selections=5,
                key="multiselect_sq_a",
                help="Seleziona esattamente 5 giocatori"
            )
            st.caption(f"Selezionati: {len(sq_a)}/5")
            
        with f_col2:
            st.markdown("##### 🟥 Squadra B")
            sq_b = st.multiselect(
                "Seleziona i 5 giocatori di Squadra B:",
                options=lista_giocatori,
                max_selections=5,
                key="multiselect_sq_b",
                help="Seleziona esattamente 5 giocatori"
            )
            st.caption(f"Selezionati: {len(sq_b)}/5")

        st.markdown("---")
        submit_partita = st.form_submit_button("💾 Salva Partita", use_container_width=True)

        if submit_partita:
            # Validazioni Stringenti
            errori = []
            
            if len(sq_a) != 5:
                errori.append(f"La Squadra A deve contenere esattamente 5 giocatori (attualmente ne ha {len(sq_a)}).")
                
            if len(sq_b) != 5:
                errori.append(f"La Squadra B deve contenere esattamente 5 giocatori (attualmente ne ha {len(sq_b)}).")
                
            duplicati = set(sq_a).intersection(set(sq_b))
            if duplicati:
                errori.append(f"I seguenti giocatori sono stati inseriti in entrambe le squadre: {', '.join(duplicati)}.")

            if errori:
                for err in errori:
                    st.error(f"❌ {err}")
            else:
                # Determinazione esito
                if gol_a > gol_b:
                    esito = "Vittoria Squadra A"
                elif gol_b > gol_a:
                    esito = "Vittoria Squadra B"
                else:
                    esito = "Pareggio"

                # Nuovo ID progressivo
                nuovo_id = 1
                if not df_partite.empty and "id_partita" in df_partite.columns:
                    nuovo_id = int(df_partite["id_partita"].max()) + 1

                nuova_riga = {
                    "id_partita": nuovo_id,
                    "data": data_partita.strftime("%Y-%m-%d"),
                    "squadra_a_giocatori": ", ".join(sq_a),
                    "squadra_b_giocatori": ", ".join(sq_b),
                    "gol_squadra_a": int(gol_a),
                    "gol_squadra_b": int(gol_b),
                    "esito": esito
                }

                df_updated = pd.concat([df_partite, pd.DataFrame([nuova_riga])], ignore_index=True)
                save_partite(df_updated)
                
                st.success("✅ Partita registrata con successo! Le classifiche sono state aggiornate.")
                st.balloons()
                st.rerun()


# ==============================================================================
# VISTA C: AGGIUNGI & GESTISCI GIOCATORE (ANAGRAFICA)
# ==============================================================================
def view_add_player(df_giocatori: pd.DataFrame, df_partite: pd.DataFrame):
    st.markdown("<div class='main-title'>👤 Anagrafica Giocatori</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Aggiungi nuovi amici al gruppo o gestisci i giocatori registrati</div>", unsafe_allow_html=True)

    # Inserimento nuovo giocatore
    with st.form("form_nuovo_giocatore", clear_on_submit=True):
        nome_input = st.text_input("Nome e Cognome del Giocatore", placeholder="es. Mario Rossi")
        submit_giocatore = st.form_submit_button("➕ Aggiungi Giocatore", use_container_width=True)

        if submit_giocatore:
            nome_clean = nome_input.strip()
            
            if not nome_clean:
                st.error("❌ Il nome del giocatore non può essere vuoto.")
            else:
                # Controllo duplicati case-insensitive
                nomi_esistenti = [str(n).strip().lower() for n in df_giocatori["nome_completo"].dropna().tolist()] if not df_giocatori.empty else []
                if nome_clean.lower() in nomi_esistenti:
                    st.error(f"❌ Esiste già un giocatore registrato con il nome '{nome_clean}'.")
                else:
                    nuovo_id = 1
                    if not df_giocatori.empty and "id_giocatore" in df_giocatori.columns:
                        nuovo_id = int(df_giocatori["id_giocatore"].max()) + 1

                    nuova_riga = {
                        "id_giocatore": nuovo_id,
                        "nome_completo": nome_clean,
                        "data_creazione": date.today().strftime("%Y-%m-%d")
                    }

                    df_updated = pd.concat([df_giocatori, pd.DataFrame([nuova_riga])], ignore_index=True)
                    save_giocatori(df_updated)
                    st.success(f"✅ Giocatore **{nome_clean}** aggiunto con successo (ID #{nuovo_id})!")
                    st.rerun()

    # Sezione Eliminazione Singolo Giocatore
    with st.expander("🗑️ Elimina un Giocatore", expanded=False):
        if df_giocatori.empty:
            st.info("Nessun giocatore registrato da eliminare.")
        else:
            lista_nomi_del = sorted(df_giocatori["nome_completo"].dropna().unique().tolist())
            del_player = st.selectbox(
                "Seleziona il giocatore da eliminare:",
                options=lista_nomi_del,
                key="select_del_player"
            )
            
            # Verifica presenza nello storico partite
            partite_con_giocatore = 0
            if not df_partite.empty:
                for _, m in df_partite.iterrows():
                    raw = str(m.get("squadra_a_giocatori", "")) + ", " + str(m.get("squadra_b_giocatori", ""))
                    if del_player in [p.strip() for p in raw.split(",")]:
                        partite_con_giocatore += 1
            
            if partite_con_giocatore > 0:
                st.warning(f"⚠️ **{del_player}** è presente in **{partite_con_giocatore}** partita/e registrata/e. Rimuovendolo non sarà più selezionabile per nuove partite.")

            btn_del_gio = st.button(f"🗑️ Elimina '{del_player}'", type="primary", use_container_width=True, key="btn_del_single_player")
            if btn_del_gio:
                df_updated = df_giocatori[df_giocatori["nome_completo"] != del_player].copy()
                save_giocatori(df_updated)
                st.success(f"✅ Giocatore **{del_player}** eliminato con successo!")
                st.rerun()

    st.markdown("---")
    st.markdown(f"### 📋 Elenco Giocatori Iscritti ({len(df_giocatori)})")
    
    if df_giocatori.empty:
        st.info("Nessun giocatore registrato.")
    else:
        df_view = df_giocatori.sort_values(by="id_giocatore", ascending=True).copy()
        st.dataframe(
            df_view,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id_giocatore": st.column_config.NumberColumn("ID", width="small"),
                "nome_completo": st.column_config.TextColumn("Nome Completo", width="medium"),
                "data_creazione": st.column_config.TextColumn("Data Iscrizione", width="small"),
            }
        )


# ==============================================================================
# VISTA D: STORICO PARTITE
# ==============================================================================
def view_match_history(df_partite: pd.DataFrame):
    st.markdown("<div class='main-title'>📜 Storico Partite</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Tutte le sfide registrate in ordine cronologico inverso</div>", unsafe_allow_html=True)

    if df_partite.empty:
        st.info("Nessuna partita presente nello storico. Registra una nuova partita per iniziare!")
        return

    # Sezione Eliminazione Singola Partita
    with st.expander("🗑️ Elimina una Partita", expanded=False):
        opzioni_partite = {}
        for _, m in df_partite.sort_values(by=["data", "id_partita"], ascending=[False, False]).iterrows():
            id_p = m.get("id_partita", "")
            d = m.get("data", "")
            g_a = m.get("gol_squadra_a", 0)
            g_b = m.get("gol_squadra_b", 0)
            esito = m.get("esito", "")
            label = f"Partita #{id_p} del {d} — Squadra A ({g_a}) vs Squadra B ({g_b}) [{esito}]"
            opzioni_partite[label] = id_p

        scelta_partita_str = st.selectbox(
            "Seleziona la partita da eliminare:",
            options=list(opzioni_partite.keys()),
            key="select_del_match"
        )
        id_da_eliminare = opzioni_partite[scelta_partita_str]

        btn_del_match = st.button("🗑️ Elimina Partita Selezionata", type="primary", use_container_width=True, key="btn_del_single_match")
        if btn_del_match:
            df_updated = df_partite[df_partite["id_partita"] != id_da_eliminare].copy()
            save_partite(df_updated)
            st.success("✅ Partita eliminata con successo!")
            st.rerun()

    st.markdown("---")

    # Ordinamento cronologico inverso (dalla più recente alla più vecchia)
    df_sorted = df_partite.sort_values(by=["data", "id_partita"], ascending=[False, False]).reset_index(drop=True)

    for idx, match in df_sorted.iterrows():
        id_p = match.get("id_partita", idx + 1)
        data_str = match.get("data", "N/D")
        gol_a = match.get("gol_squadra_a", 0)
        gol_b = match.get("gol_squadra_b", 0)
        esito = match.get("esito", "")
        sq_a = match.get("squadra_a_giocatori", "")
        sq_b = match.get("squadra_b_giocatori", "")

        # Colore esito
        if "Squadra A" in esito:
            badge_color = "#38bdf8"
        elif "Squadra B" in esito:
            badge_color = "#f43f5e"
        else:
            badge_color = "#eab308"

        card_html = f"""
        <div class="match-card">
            <div class="match-header">
                <span>🗓️ Partita #{id_p} del <b>{data_str}</b></span>
                <span style="background-color: {badge_color}; color: #0f172a; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem;">
                    {esito}
                </span>
            </div>
            <div class="match-score">
                <span style="color: #38bdf8;">Squadra A</span> &nbsp;
                <span style="background: #0f172a; padding: 4px 14px; border-radius: 8px; border: 1px solid #334155;">{gol_a} - {gol_b}</span>
                &nbsp; <span style="color: #f43f5e;">Squadra B</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px;">
                <div class="team-box">
                    <span class="team-title">🟦 Formazione A:</span><br>
                    {sq_a}
                </div>
                <div class="team-box">
                    <span class="team-title-b">🟥 Formazione B:</span><br>
                    {sq_b}
                </div>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)


# ==============================================================================
# MAIN ROUTING & APPLICAZIONE
# ==============================================================================
def main():
    # Inizializzazione session state per l'autenticazione
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    # Controllo Autenticazione (PIN Gate)
    if not st.session_state["authenticated"]:
        render_pin_gate()
        return

    # Caricamento Dati
    df_giocatori, df_partite, storage_source = load_data()

    # Sidebar con navigazione e Strumenti di Amministrazione
    with st.sidebar:
        st.markdown("### ⚽ Calcetto Manager")
        st.caption(f"Persistenza: **{storage_source}**")
        st.markdown("---")
        
        scelta_menu = st.radio(
            "Navigazione Sezioni:",
            options=[
                "🏆 Tabellone & Classifiche",
                "➕ Aggiungi Nuova Partita",
                "👥 Aggiungi Giocatore",
                "📜 Storico Partite"
            ],
            index=0
        )
        
        st.markdown("---")
        
        # Strumenti Amministrativi / Reset Rapido
        with st.expander("⚙️ Gestione & Reset Dati", expanded=False):
            st.caption("Strumenti rapidi per svuotare i dati di test o resettare l'archivio.")
            
            # Svuota Partite
            if st.button("🧹 Svuota Tutte le Partite", use_container_width=True, help="Elimina tutte le partite registrate"):
                st.session_state["confirm_reset_matches"] = True
            
            if st.session_state.get("confirm_reset_matches", False):
                st.warning("⚠️ Sei sicuro di voler cancellare TUTTE le partite?")
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    if st.button("Sì, Svuota", key="btn_yes_clear_matches", type="primary", use_container_width=True):
                        empty_p = pd.DataFrame(columns=[
                            "id_partita", "data", "squadra_a_giocatori", 
                            "squadra_b_giocatori", "gol_squadra_a", "gol_squadra_b", "esito"
                        ])
                        save_partite(empty_p)
                        st.session_state["confirm_reset_matches"] = False
                        st.success("Tutte le partite sono state rimosse!")
                        st.rerun()
                with col_m2:
                    if st.button("Annulla", key="btn_no_clear_matches", use_container_width=True):
                        st.session_state["confirm_reset_matches"] = False
                        st.rerun()

            # Svuota Giocatori
            if st.button("👥 Svuota Tutti i Giocatori", use_container_width=True, help="Elimina tutti i giocatori iscritti"):
                st.session_state["confirm_reset_players"] = True
                
            if st.session_state.get("confirm_reset_players", False):
                st.warning("⚠️ Sei sicuro di voler cancellare TUTTI i giocatori?")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    if st.button("Sì, Svuota", key="btn_yes_clear_players", type="primary", use_container_width=True):
                        empty_g = pd.DataFrame(columns=["id_giocatore", "nome_completo", "data_creazione"])
                        save_giocatori(empty_g)
                        st.session_state["confirm_reset_players"] = False
                        st.success("Tutti i giocatori sono stati rimossi!")
                        st.rerun()
                with col_p2:
                    if st.button("Annulla", key="btn_no_clear_players", use_container_width=True):
                        st.session_state["confirm_reset_players"] = False
                        st.rerun()

            # Ripristino Demo
            if st.button("🔄 Ripristina Dati Esempio", use_container_width=True, help="Reimposta i giocatori e le partite demo iniziali"):
                save_giocatori(pd.DataFrame(GIOCATORI_DEFAULT))
                save_partite(pd.DataFrame(PARTITE_DEFAULT))
                st.success("Dati di esempio ripristinati con successo!")
                st.rerun()

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["authenticated"] = False
            st.rerun()

    # Routing delle viste
    if scelta_menu == "🏆 Tabellone & Classifiche":
        view_dashboard(df_giocatori, df_partite, storage_source)
    elif scelta_menu == "➕ Aggiungi Nuova Partita":
        view_add_match(df_giocatori, df_partite)
    elif scelta_menu == "👥 Aggiungi Giocatore":
        view_add_player(df_giocatori, df_partite)
    elif scelta_menu == "📜 Storico Partite":
        view_match_history(df_partite)


if __name__ == "__main__":
    main()
