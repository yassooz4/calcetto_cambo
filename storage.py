"""
================================================================================
STORAGE.PY - Layer di Persistenza Dati (Google Sheets & Fallback CSV Locale)
Gestione I/O per giocatori, partite, convocazioni e votazioni
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
    GSPREAD_IMPORT_ERROR = None
except Exception as e:
    GSPREAD_AVAILABLE = False
    GSPREAD_IMPORT_ERROR = str(e)


# ==============================================================================
# COSTANTI & PATH LOCALI
# ==============================================================================
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CSV_GIOCATORI = os.path.join(DATA_DIR, "giocatori.csv")
CSV_PARTITE = os.path.join(DATA_DIR, "partite.csv")
CSV_CONVOCAZIONI = os.path.join(DATA_DIR, "convocazioni.csv")
CSV_VOTI = os.path.join(DATA_DIR, "voti.csv")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Dati di Default per Inizializzazione Demo
GIOCATORI_DEFAULT = [
    {"id_giocatore": 1, "nome_completo": "Marco Rossi", "data_creazione": "2024-01-10", "in_gruppo_ristretto": True},
    {"id_giocatore": 2, "nome_completo": "Luca Bianchi", "data_creazione": "2024-01-10", "in_gruppo_ristretto": True},
    {"id_giocatore": 3, "nome_completo": "Matteo Ferrari", "data_creazione": "2024-01-10", "in_gruppo_ristretto": True},
    {"id_giocatore": 4, "nome_completo": "Alessandro Russo", "data_creazione": "2024-01-10", "in_gruppo_ristretto": True},
    {"id_giocatore": 5, "nome_completo": "Davide Colombo", "data_creazione": "2024-01-10", "in_gruppo_ristretto": True},
    {"id_giocatore": 6, "nome_completo": "Federico Ricci", "data_creazione": "2024-01-10", "in_gruppo_ristretto": True},
    {"id_giocatore": 7, "nome_completo": "Andrea Marino", "data_creazione": "2024-01-10", "in_gruppo_ristretto": True},
    {"id_giocatore": 8, "nome_completo": "Lorenzo Greco", "data_creazione": "2024-01-10", "in_gruppo_ristretto": True},
    {"id_giocatore": 9, "nome_completo": "Simone Bruno", "data_creazione": "2024-01-10", "in_gruppo_ristretto": True},
    {"id_giocatore": 10, "nome_completo": "Gabriele Gallo", "data_creazione": "2024-01-10", "in_gruppo_ristretto": True},
    {"id_giocatore": 11, "nome_completo": "Francesco Conti", "data_creazione": "2024-01-15", "in_gruppo_ristretto": False},
    {"id_giocatore": 12, "nome_completo": "Giovanni De Luca", "data_creazione": "2024-01-15", "in_gruppo_ristretto": False},
]

PARTITE_DEFAULT = [
    {
        "id_partita": 1,
        "data": "2024-02-01",
        "squadra_a_giocatori": "Marco Rossi, Luca Bianchi, Matteo Ferrari, Alessandro Russo, Davide Colombo",
        "squadra_b_giocatori": "Federico Ricci, Andrea Marino, Lorenzo Greco, Simone Bruno, Gabriele Gallo",
        "gol_squadra_a": 7,
        "gol_squadra_b": 5,
        "esito": "Vittoria Squadra A",
        "marcatori": '{"Marco Rossi": 3, "Luca Bianchi": 2, "Matteo Ferrari": 2, "Federico Ricci": 3, "Andrea Marino": 2}'
    },
    {
        "id_partita": 2,
        "data": "2024-02-08",
        "squadra_a_giocatori": "Marco Rossi, Luca Bianchi, Francesco Conti, Giovanni De Luca, Davide Colombo",
        "squadra_b_giocatori": "Matteo Ferrari, Alessandro Russo, Andrea Marino, Lorenzo Greco, Gabriele Gallo",
        "gol_squadra_a": 4,
        "gol_squadra_b": 4,
        "esito": "Pareggio",
        "marcatori": '{"Marco Rossi": 2, "Francesco Conti": 2, "Alessandro Russo": 3, "Matteo Ferrari": 1}'
    }
]

CONVOCAZIONI_DEFAULT = [
    {
        "id_convocazione": 1,
        "data_partita": "2024-02-15",
        "ora_partita": "20:30",
        "luogo": "Campo Comunale 1 (Sintetico)",
        "stato": "Aperta",
        "presenti": "Marco Rossi, Luca Bianchi, Matteo Ferrari, Alessandro Russo, Davide Colombo, Federico Ricci, Andrea Marino",
        "assenti": "Giovanni De Luca"
    }
]

VOTI_DEFAULT = [
    {
        "id_voto": 1,
        "id_partita": 1,
        "votante": "Federico Ricci",
        "giocatore": "Marco Rossi",
        "voto": 8.5,
        "commento": "Tripletta decisiva e grande visione di gioco!",
        "timestamp": "2024-02-01 23:15:00"
    },
    {
        "id_voto": 2,
        "id_partita": 1,
        "votante": "Marco Rossi",
        "giocatore": "Federico Ricci",
        "voto": 8.0,
        "commento": "Migliore della sua squadra, sempre pericoloso.",
        "timestamp": "2024-02-01 23:20:00"
    },
    {
        "id_voto": 3,
        "id_partita": 1,
        "votante": "Luca Bianchi",
        "giocatore": "Gabriele Gallo",
        "voto": 5.5,
        "commento": "Un po' distratto sui ripiegamenti difensivi.",
        "timestamp": "2024-02-01 23:25:00"
    }
]


# ==============================================================================
# GOOGLE SHEETS HELPER & DIAGNOSTICA
# ==============================================================================
def sanitize_private_key(raw_pk: str) -> str:
    """
    Sanitizza e normalizza una chiave privata RSA/Service Account Google:
    1. Rimuove apici esterni extra (singoli, doppi, tripli apici da configurazioni multiline TOML).
    2. Risolve le sequenze di escape (\\n -> \n, \\r -> \r).
    3. Estrae il payload Base64 pulito (rimuovendo spazi, newlines e caratteri spuri non Base64 come punti).
    4. Ricostruisce il blocco PEM standard con header -----BEGIN PRIVATE KEY-----, righe a 64 char e footer -----END PRIVATE KEY-----.
    """
    if not raw_pk:
        return ""

    pk = str(raw_pk).strip()

    # Rimuove apici esterni (singoli, doppi o tripli)
    for _ in range(3):
        pk = pk.strip()
        if (pk.startswith('"""') and pk.endswith('"""')) or (pk.startswith("'''") and pk.endswith("'''")):
            pk = pk[3:-3].strip()
        elif (pk.startswith('"') and pk.endswith('"')) or (pk.startswith("'") and pk.endswith("'")):
            pk = pk[1:-1].strip()

    # Risolve sequenze di escape
    pk = pk.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\r\n", "\n").replace("\r", "\n")

    # Gestione delimitatori PEM
    import re
    begin_match = re.search(r"-----BEGIN[^-]+-----", pk)
    end_match = re.search(r"-----END[^-]+-----", pk)

    if begin_match and end_match:
        body = pk[begin_match.end():end_match.start()]
    elif begin_match:
        body = pk[begin_match.end():]
    elif end_match:
        body = pk[:end_match.start()]
    else:
        body = pk

    # Rimuove qualsiasi carattere non Base64 standard (A-Z, a-z, 0-9, +, /, =)
    clean_body = re.sub(r"[^A-Za-z0-9+/=]", "", body)

    if clean_body:
        chunk_size = 64
        lines = [clean_body[i:i + chunk_size] for i in range(0, len(clean_body), chunk_size)]
        return "-----BEGIN PRIVATE KEY-----\n" + "\n".join(lines) + "\n-----END PRIVATE KEY-----\n"

    # Fallback se non è stato possibile estrarre un body
    pk = pk.strip()
    if not pk.startswith("-----BEGIN"):
        pk = "-----BEGIN PRIVATE KEY-----\n" + pk
    if not pk.endswith("-----"):
        pk = pk + "\n-----END PRIVATE KEY-----\n"
    return pk


def get_gsheets_config():
    """
    Recupera le credenziali del Service Account e l'identificativo/URL dello Spreadsheet
    dai segreti di Streamlit (st.secrets), supportando molteplici strutture:
      - [connections.gsheets] (standard Streamlit GSheets connection)
      - [gcp_service_account]
      - [service_account]
      - [gspread]
      - radice di st.secrets
    
    Restituisce: (sa_info_dict, spreadsheet_target_str, err_msg)
    """
    if not GSPREAD_AVAILABLE:
        return None, None, f"Librerie Google mancanti nell'ambiente ({GSPREAD_IMPORT_ERROR or 'gspread/google-auth non importabili'})."

    try:
        if not hasattr(st, "secrets") or not st.secrets:
            return None, None, "st.secrets non trovato o vuoto. Inserisci le credenziali nei Secrets di Streamlit Cloud."
            
        sa_info = {}
        spreadsheet_target = None
        
        # 1. Controlla possibili dizionari / sezioni di segreti
        sections_to_check = []
        
        # [connections.gsheets]
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            try:
                sections_to_check.append(dict(st.secrets["connections"]["gsheets"]))
            except Exception:
                pass
            
        # [gcp_service_account]
        if "gcp_service_account" in st.secrets:
            try:
                sections_to_check.append(dict(st.secrets["gcp_service_account"]))
            except Exception:
                pass
            
        # [service_account]
        if "service_account" in st.secrets:
            try:
                sections_to_check.append(dict(st.secrets["service_account"]))
            except Exception:
                pass
            
        # [gspread]
        if "gspread" in st.secrets:
            try:
                sections_to_check.append(dict(st.secrets["gspread"]))
            except Exception:
                pass
            
        # Radice st.secrets (solo valori scalari/stringhe o chiavi dirette)
        try:
            root_dict = {k: st.secrets[k] for k in st.secrets.keys() if not hasattr(st.secrets[k], "keys")}
            sections_to_check.append(root_dict)
        except Exception:
            pass

        # Chiavi tipiche del Service Account Google
        sa_keys = [
            "type", "project_id", "private_key_id", "private_key",
            "client_email", "client_id", "auth_uri", "token_uri",
            "auth_provider_x509_cert_url", "client_x509_cert_url", "universe_domain"
        ]

        # Chiavi possibili per lo Spreadsheet URL/ID
        sheet_target_keys = [
            "spreadsheet", "spreadsheet_url", "url", "sheet_id",
            "spreadsheet_id", "spreadsheet_name", "title"
        ]

        # Popola sa_info e spreadsheet_target combinando le sezioni
        for sec in sections_to_check:
            if not isinstance(sec, dict):
                continue
            for k in sa_keys:
                if k in sec and k not in sa_info:
                    sa_info[k] = sec[k]
            if not spreadsheet_target:
                for sk in sheet_target_keys:
                    if sk in sec and sec[sk]:
                        spreadsheet_target = str(sec[sk]).strip()
                        break

        # Controlla anche a livello radice di st.secrets per spreadsheet_target se non ancora trovato
        if not spreadsheet_target:
            for sk in sheet_target_keys:
                if sk in st.secrets:
                    val = st.secrets[sk]
                    if isinstance(val, str) and val.strip():
                        spreadsheet_target = val.strip()
                        break

        if not sa_info:
            return None, None, f"Nessuna credenziale Google Service Account trovata in st.secrets. Chiavi disponibili: {list(st.secrets.keys())}"

        # Verifica campi minimi obbligatori per autenticazione Service Account
        missing_fields = []
        if "private_key" not in sa_info:
            missing_fields.append("private_key")
        if "client_email" not in sa_info:
            missing_fields.append("client_email")

        if missing_fields:
            return None, None, f"Campi obbligatori mancanti nei secrets per il Service Account: {', '.join(missing_fields)}. Campi rilevati: {list(sa_info.keys())}"

        if not spreadsheet_target:
            return None, None, "Identificativo o URL dello Spreadsheet non trovato nei segreti. Aggiungi la chiave 'spreadsheet' o 'spreadsheet_url' con il link del foglio Google."

        # Imposta valori di default per campi opzionali standard
        if "type" not in sa_info:
            sa_info["type"] = "service_account"
        if "token_uri" not in sa_info:
            sa_info["token_uri"] = "https://oauth2.googleapis.com/token"
        if "auth_uri" not in sa_info:
            sa_info["auth_uri"] = "https://accounts.google.com/o/oauth2/auth"
            
        # Sanitizzazione e normalizzazione avanzata della chiave privata RSA
        sa_info["private_key"] = sanitize_private_key(sa_info["private_key"])

        return sa_info, spreadsheet_target, None

    except Exception as e:
        return None, None, f"Eccezione durante la lettura dei secrets: {type(e).__name__} - {str(e)}"


def is_gsheets_configured() -> bool:
    """Verifica se le credenziali di Google Sheets sono disponibili nei segreti."""
    if not GSPREAD_AVAILABLE:
        return False
    sa_info, spreadsheet_target, _ = get_gsheets_config()
    return (sa_info is not None) and bool(spreadsheet_target)


def get_gsheets_spreadsheet():
    """
    Inizializza la connessione a Google Sheets tramite gspread e apre lo spreadsheet.
    Restituisce: (spreadsheet_obj, error_message_or_None)
    """
    if not GSPREAD_AVAILABLE:
        return None, f"Librerie Google non disponibili: {GSPREAD_IMPORT_ERROR}"
        
    sa_info, spreadsheet_target, config_err = get_gsheets_config()
    if config_err:
        return None, config_err
    if not sa_info or not spreadsheet_target:
        return None, "Configurazione Google Sheets non disponibile nei segreti."
        
    try:
        creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    except Exception as e:
        return None, f"Errore inizializzazione Google Credentials: {type(e).__name__} - {str(e)}"

    try:
        client = gspread.authorize(creds)
    except Exception as e:
        return None, f"Errore autorizzazione client gspread: {type(e).__name__} - {str(e)}"
        
    target = str(spreadsheet_target).strip()
    
    try:
        # Caso 1: URL completo (inclusi parametri /edit?gid=... o simili)
        if target.startswith("http://") or target.startswith("https://"):
            try:
                sh = client.open_by_url(target)
                return sh, None
            except Exception as url_err:
                # Estrazione ID da pattern URL standard /spreadsheets/d/<ID>/
                import re
                match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", target)
                if match:
                    try:
                        sh = client.open_by_key(match.group(1))
                        return sh, None
                    except Exception as key_err:
                        raise Exception(f"Apertura per URL fallita ({url_err}) ed estrazione per ID ({match.group(1)}) fallita: {key_err}")
                raise url_err

        # Caso 2: Chiave/ID univoco dello Sheet (stringa alfanumerica lunga senza slash o spazi)
        elif len(target) > 25 and "/" not in target and " " not in target:
            try:
                sh = client.open_by_key(target)
                return sh, None
            except Exception as key_err:
                try:
                    sh = client.open(target)
                    return sh, None
                except Exception:
                    raise key_err

        # Caso 3: Nome/Titolo del foglio
        else:
            sh = client.open(target)
            return sh, None

    except Exception as e:
        client_email = sa_info.get("client_email", "non definita")
        return None, f"Impossibile aprire il foglio Google '{target}' ({type(e).__name__}): {str(e)}. Assicurati che il foglio esista e sia stato CONDIVISO con accesso Editor all'email del Service Account: {client_email}"


def read_worksheet_as_df(sh, worksheet_name: str, default_cols: list) -> pd.DataFrame:
    """Legge un foglio di lavoro da gspread e restituisce un DataFrame pandas."""
    try:
        worksheet = sh.worksheet(worksheet_name)
    except Exception:
        # Se il worksheet non esiste, lo crea con le intestazioni di default
        try:
            worksheet = sh.add_worksheet(title=worksheet_name, rows=100, cols=max(15, len(default_cols) + 2))
            try:
                worksheet.update([default_cols], "A1")
            except Exception:
                worksheet.update([default_cols])
            return pd.DataFrame(columns=default_cols)
        except Exception:
            return pd.DataFrame(columns=default_cols)
    
    values = worksheet.get_all_values()
    if not values or len(values) == 0:
        return pd.DataFrame(columns=default_cols)
    
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
    try:
        worksheet.update(all_values, "A1")
    except Exception:
        worksheet.update(all_values)


# ==============================================================================
# INIZIALIZZAZIONE STORAGE LOCALE (CSV)
# ==============================================================================
def init_local_storage():
    """Inizializza la cartella locale e i file CSV di fallback con le strutture corrette."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    
    if not os.path.exists(CSV_GIOCATORI) or os.path.getsize(CSV_GIOCATORI) < 5:
        df_gio = pd.DataFrame(GIOCATORI_DEFAULT)
        df_gio.to_csv(CSV_GIOCATORI, index=False)
        
    if not os.path.exists(CSV_PARTITE) or os.path.getsize(CSV_PARTITE) < 5:
        df_par = pd.DataFrame(PARTITE_DEFAULT)
        df_par.to_csv(CSV_PARTITE, index=False)

    if not os.path.exists(CSV_CONVOCAZIONI) or os.path.getsize(CSV_CONVOCAZIONI) < 5:
        df_conv = pd.DataFrame(CONVOCAZIONI_DEFAULT)
        df_conv.to_csv(CSV_CONVOCAZIONI, index=False)

    if not os.path.exists(CSV_VOTI) or os.path.getsize(CSV_VOTI) < 5:
        df_voti = pd.DataFrame(VOTI_DEFAULT)
        df_voti.to_csv(CSV_VOTI, index=False)


def _sanitize_boolean_series(series: pd.Series) -> pd.Series:
    """Normalizza una serie di valori in booleani affidabili (True/False)."""
    return series.astype(str).str.strip().str.lower().isin(["true", "1", "t", "yes", "si", "sì", "vero"])


# ==============================================================================
# CARICAMENTO DATI (CON CACHE E SANITIZZAZIONE)
# ==============================================================================
@st.cache_data(ttl=300)
def load_data():
    """
    Carica i dataframe di tutte le tabelle: giocatori, partite, convocazioni, voti.
    Usa Google Sheets tramite gspread se configurato, altrimenti usa il fallback locale CSV.
    Restituisce: (df_giocatori, df_partite, df_convocazioni, df_voti, storage_source, storage_error)
    """
    sh, gsheets_err = get_gsheets_spreadsheet()
    
    if sh is not None:
        try:
            # 1. Giocatori
            cols_gio = ["id_giocatore", "nome_completo", "data_creazione", "in_gruppo_ristretto"]
            df_giocatori = read_worksheet_as_df(sh, "giocatori", cols_gio)
            if "nome_completo" in df_giocatori.columns:
                df_giocatori = df_giocatori.dropna(subset=["nome_completo"])
                df_giocatori = df_giocatori[df_giocatori["nome_completo"].astype(str).str.strip() != ""]
            if not df_giocatori.empty:
                if "id_giocatore" in df_giocatori.columns:
                    df_giocatori["id_giocatore"] = pd.to_numeric(df_giocatori["id_giocatore"], errors="coerce").fillna(0).astype(int)
                if "in_gruppo_ristretto" in df_giocatori.columns:
                    df_giocatori["in_gruppo_ristretto"] = _sanitize_boolean_series(df_giocatori["in_gruppo_ristretto"])
                else:
                    df_giocatori["in_gruppo_ristretto"] = False

            # 2. Partite
            cols_par = ["id_partita", "data", "squadra_a_giocatori", "squadra_b_giocatori", "gol_squadra_a", "gol_squadra_b", "esito", "marcatori"]
            df_partite = read_worksheet_as_df(sh, "partite", cols_par)
            if "id_partita" in df_partite.columns:
                df_partite = df_partite.dropna(subset=["id_partita"])
                df_partite = df_partite[df_partite["id_partita"].astype(str).str.strip() != ""]
            if not df_partite.empty:
                if "id_partita" in df_partite.columns:
                    df_partite["id_partita"] = pd.to_numeric(df_partite["id_partita"], errors="coerce").fillna(0).astype(int)
                if "gol_squadra_a" in df_partite.columns:
                    df_partite["gol_squadra_a"] = pd.to_numeric(df_partite["gol_squadra_a"], errors="coerce").fillna(0).astype(int)
                if "gol_squadra_b" in df_partite.columns:
                    df_partite["gol_squadra_b"] = pd.to_numeric(df_partite["gol_squadra_b"], errors="coerce").fillna(0).astype(int)
                if "marcatori" not in df_partite.columns:
                    df_partite["marcatori"] = "{}"

            # 3. Convocazioni
            cols_conv = ["id_convocazione", "data_partita", "ora_partita", "luogo", "stato", "presenti", "assenti"]
            df_convocazioni = read_worksheet_as_df(sh, "convocazioni", cols_conv)
            if not df_convocazioni.empty and "id_convocazione" in df_convocazioni.columns:
                df_convocazioni["id_convocazione"] = pd.to_numeric(df_convocazioni["id_convocazione"], errors="coerce").fillna(0).astype(int)

            # 4. Voti
            cols_voti = ["id_voto", "id_partita", "votante", "giocatore", "voto", "commento", "timestamp"]
            df_voti = read_worksheet_as_df(sh, "voti", cols_voti)
            if not df_voti.empty:
                if "id_voto" in df_voti.columns:
                    df_voti["id_voto"] = pd.to_numeric(df_voti["id_voto"], errors="coerce").fillna(0).astype(int)
                if "id_partita" in df_voti.columns:
                    df_voti["id_partita"] = pd.to_numeric(df_voti["id_partita"], errors="coerce").fillna(0).astype(int)
                if "voto" in df_voti.columns:
                    df_voti["voto"] = pd.to_numeric(df_voti["voto"], errors="coerce").fillna(0.0)

            return df_giocatori, df_partite, df_convocazioni, df_voti, "Google Sheets (Cloud)", None
        except Exception as e:
            gsheets_err = f"Errore lettura tabelle dallo Spreadsheet: {type(e).__name__} - {str(e)}"

    # Fallback locale CSV
    init_local_storage()
    df_giocatori = pd.read_csv(CSV_GIOCATORI)
    df_partite = pd.read_csv(CSV_PARTITE)
    df_convocazioni = pd.read_csv(CSV_CONVOCAZIONI) if os.path.exists(CSV_CONVOCAZIONI) else pd.DataFrame(CONVOCAZIONI_DEFAULT)
    df_voti = pd.read_csv(CSV_VOTI) if os.path.exists(CSV_VOTI) else pd.DataFrame(VOTI_DEFAULT)

    # Conversioni tipi
    if not df_giocatori.empty:
        if "id_giocatore" in df_giocatori.columns:
            df_giocatori["id_giocatore"] = pd.to_numeric(df_giocatori["id_giocatore"], errors="coerce").fillna(0).astype(int)
        if "in_gruppo_ristretto" in df_giocatori.columns:
            df_giocatori["in_gruppo_ristretto"] = _sanitize_boolean_series(df_giocatori["in_gruppo_ristretto"])
        else:
            df_giocatori["in_gruppo_ristretto"] = False

    if not df_partite.empty:
        if "id_partita" in df_partite.columns:
            df_partite["id_partita"] = pd.to_numeric(df_partite["id_partita"], errors="coerce").fillna(0).astype(int)
        if "gol_squadra_a" in df_partite.columns:
            df_partite["gol_squadra_a"] = pd.to_numeric(df_partite["gol_squadra_a"], errors="coerce").fillna(0).astype(int)
        if "gol_squadra_b" in df_partite.columns:
            df_partite["gol_squadra_b"] = pd.to_numeric(df_partite["gol_squadra_b"], errors="coerce").fillna(0).astype(int)
        if "marcatori" not in df_partite.columns:
            df_partite["marcatori"] = "{}"

    if not df_convocazioni.empty and "id_convocazione" in df_convocazioni.columns:
        df_convocazioni["id_convocazione"] = pd.to_numeric(df_convocazioni["id_convocazione"], errors="coerce").fillna(0).astype(int)

    if not df_voti.empty:
        if "id_voto" in df_voti.columns:
            df_voti["id_voto"] = pd.to_numeric(df_voti["id_voto"], errors="coerce").fillna(0).astype(int)
        if "id_partita" in df_voti.columns:
            df_voti["id_partita"] = pd.to_numeric(df_voti["id_partita"], errors="coerce").fillna(0).astype(int)
        if "voto" in df_voti.columns:
            df_voti["voto"] = pd.to_numeric(df_voti["voto"], errors="coerce").fillna(0.0)

    return df_giocatori, df_partite, df_convocazioni, df_voti, "Locale (CSV)", gsheets_err


# ==============================================================================
# SALVATAGGIO DATI (CON CLEAR CACHE AUTOMATICO)
# ==============================================================================
def save_giocatori(df_giocatori: pd.DataFrame) -> bool:
    """Salva giocatori su Google Sheets o CSV locale con invalidazione cache."""
    # Garantisci la presenza del campo booleano
    if "in_gruppo_ristretto" not in df_giocatori.columns:
        df_giocatori["in_gruppo_ristretto"] = False
    else:
        df_giocatori["in_gruppo_ristretto"] = df_giocatori["in_gruppo_ristretto"].astype(bool)

    sh, _ = get_gsheets_spreadsheet()
    if sh is not None:
        try:
            write_df_to_worksheet(sh, "giocatori", df_giocatori)
            st.cache_data.clear()
            return True
        except Exception:
            pass
    init_local_storage()
    df_giocatori.to_csv(CSV_GIOCATORI, index=False)
    st.cache_data.clear()
    return True


def toggle_giocatore_gruppo_ristretto(id_giocatore: int, stato: bool) -> bool:
    """Aggiorna lo stato di appartenenza alla cerchia ristretta per un singolo giocatore."""
    df_giocatori, *_ = load_data()
    if df_giocatori.empty or "id_giocatore" not in df_giocatori.columns:
        return False
    
    df_up = df_giocatori.copy()
    if "in_gruppo_ristretto" not in df_up.columns:
        df_up["in_gruppo_ristretto"] = False
        
    idx = df_up[df_up["id_giocatore"] == id_giocatore].index
    if not idx.empty:
        df_up.loc[idx, "in_gruppo_ristretto"] = bool(stato)
        return save_giocatori(df_up)
    return False


def update_gruppo_ristretto_members(member_ids: list) -> bool:
    """Aggiorna in blocco l'appartenenza al gruppo ristretto in base alla lista di ID fornita."""
    df_giocatori, *_ = load_data()
    if df_giocatori.empty or "id_giocatore" not in df_giocatori.columns:
        return False
    
    df_up = df_giocatori.copy()
    int_ids = [int(i) for i in member_ids]
    df_up["in_gruppo_ristretto"] = df_up["id_giocatore"].astype(int).isin(int_ids)
    return save_giocatori(df_up)


def save_partite(df_partite: pd.DataFrame) -> bool:
    """Salva partite su Google Sheets o CSV locale con invalidazione cache."""
    sh, _ = get_gsheets_spreadsheet()
    if sh is not None:
        try:
            write_df_to_worksheet(sh, "partite", df_partite)
            st.cache_data.clear()
            return True
        except Exception:
            pass
    init_local_storage()
    df_partite.to_csv(CSV_PARTITE, index=False)
    st.cache_data.clear()
    return True


def save_convocazioni(df_convocazioni: pd.DataFrame) -> bool:
    """Salva convocazioni su Google Sheets o CSV locale con invalidazione cache."""
    sh, _ = get_gsheets_spreadsheet()
    if sh is not None:
        try:
            write_df_to_worksheet(sh, "convocazioni", df_convocazioni)
            st.cache_data.clear()
            return True
        except Exception:
            pass
    init_local_storage()
    df_convocazioni.to_csv(CSV_CONVOCAZIONI, index=False)
    st.cache_data.clear()
    return True


def save_voti(df_voti: pd.DataFrame) -> bool:
    """Salva votazioni/pagelle su Google Sheets o CSV locale con invalidazione cache."""
    sh, _ = get_gsheets_spreadsheet()
    if sh is not None:
        try:
            write_df_to_worksheet(sh, "voti", df_voti)
            st.cache_data.clear()
            return True
        except Exception:
            pass
    init_local_storage()
    df_voti.to_csv(CSV_VOTI, index=False)
    st.cache_data.clear()
    return True


def get_all_voti() -> pd.DataFrame:
    """Restituisce l'intero DataFrame dei voti registrati."""
    *_, df_voti, _, _ = load_data()
    return df_voti


def delete_voto(id_voto: int) -> bool:
    """
    Elimina un singolo voto identificato da id_voto e aggiorna lo storage (GSheets o CSV).
    Svuota la cache per garantire il ricalcolo immediato delle medie e dell'MVP.
    """
    *_, df_voti, _, _ = load_data()
    if df_voti.empty or "id_voto" not in df_voti.columns:
        return False
    
    df_updated = df_voti[df_voti["id_voto"].astype(str) != str(id_voto)].copy()
    return save_voti(df_updated)


def delete_voti_partita(id_partita: int) -> bool:
    """
    Elimina tutti i voti associati a una determinata partita.
    """
    *_, df_voti, _, _ = load_data()
    if df_voti.empty or "id_partita" not in df_voti.columns:
        return False
        
    df_updated = df_voti[df_voti["id_partita"].astype(str) != str(id_partita)].copy()
    return save_voti(df_updated)


def update_partita(id_partita: int, updated_data: dict) -> bool:
    """
    Aggiorna i campi di una partita esistente identificata da id_partita
    (data, squadre, gol, esito, marcatori) e persiste le modifiche.
    """
    _, df_partite, *_ = load_data()
    if df_partite.empty or "id_partita" not in df_partite.columns:
        return False
        
    idx = df_partite[df_partite["id_partita"].astype(str) == str(id_partita)].index
    if idx.empty:
        return False
        
    df_up = df_partite.copy()
    for col, val in updated_data.items():
        if col in df_up.columns:
            df_up.loc[idx, col] = val
            
    return save_partite(df_up)


def reset_all_to_demo():
    """Ripristina tutti i dati ai valori di default/demo."""
    save_giocatori(pd.DataFrame(GIOCATORI_DEFAULT))
    save_partite(pd.DataFrame(PARTITE_DEFAULT))
    save_convocazioni(pd.DataFrame(CONVOCAZIONI_DEFAULT))
    save_voti(pd.DataFrame(VOTI_DEFAULT))
    st.cache_data.clear()
