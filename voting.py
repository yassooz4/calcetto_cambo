"""Private, encrypted MVP ballots. Only closed election summaries are public."""

import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
from collections import Counter
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from cryptography.fernet import Fernet, InvalidToken

import storage

WORKSHEET = "votazioni_private"
LOCAL_LOG = os.path.join(storage.DATA_DIR, "votazioni_private.jsonl")
PUBLIC_COLUMNS = ["id_partita", "mvp_names", "worst_names", "mvp_votes", "worst_votes", "total_ballots"]


class VotingError(Exception):
    pass


def admin_pin():
    try:
        pin = str(st.secrets["auth"]["admin_pin"])
    except (KeyError, FileNotFoundError):
        return None
    if not re.fullmatch(r"[0-9]{4}", pin) or pin in {"5678", "8765"}:
        return None
    return pin


def admin_signature():
    pin = admin_pin()
    return hashlib.sha256(pin.encode()).hexdigest() if pin else None


def is_private_admin():
    signature = admin_signature()
    return bool(signature and st.session_state.get("authenticated")
                and st.session_state.get("user_role") == "admin"
                and hmac.compare_digest(st.session_state.get("admin_signature", ""), signature))


def require_admin():
    if not is_private_admin():
        raise VotingError("Accesso riservato all'amministratore.")


def cipher():
    try:
        key = str(st.secrets["auth"]["voting_key"])
        return Fernet(key.encode("ascii"))
    except (KeyError, FileNotFoundError, ValueError, UnicodeError):
        raise VotingError("Le votazioni riservate devono essere configurate dall'amministratore nei Secrets di Streamlit.") from None


def configured():
    if not admin_pin():
        return False
    try:
        cipher()
        return True
    except VotingError:
        return False


@st.cache_resource
def _runtime():
    return threading.RLock(), {}


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def identifier(value):
    return str(int(value))


def _backend():
    if storage.is_gsheets_configured():
        sh, error = storage.get_gsheets_spreadsheet()
        if sh is None:
            raise VotingError("Archivio cloud non raggiungibile. Riprova: nessun voto è stato salvato in un archivio alternativo.")
        return sh
    return None


def _read(sh):
    codec = cipher()
    if sh is None:
        if not os.path.exists(LOCAL_LOG):
            return []
        with open(LOCAL_LOG, encoding="utf-8") as handle:
            tokens = [line.strip() for line in handle if line.strip()]
    else:
        try:
            worksheet = sh.worksheet(WORKSHEET)
        except storage.gspread.WorksheetNotFound:
            return []
        except Exception:
            raise VotingError("Impossibile leggere l'archivio delle votazioni. Riprova.") from None
        try:
            rows = worksheet.get_all_values()
        except Exception:
            raise VotingError("Impossibile leggere l'archivio delle votazioni. Riprova.") from None
        if rows and rows[0] != ["payload"]:
            raise VotingError("Formato dell'archivio votazioni non valido.")
        tokens = [row[0] for row in rows[1:] if row and row[0]]
    try:
        events = [json.loads(codec.decrypt(token.encode()).decode()) for token in tokens]
        if any(event.get("version") != 1 for event in events):
            raise ValueError("Unknown event schema")
        return events
    except (InvalidToken, ValueError, TypeError, AttributeError):
        raise VotingError("Impossibile verificare l'archivio privato. Controlla la chiave nei Secrets senza rigenerarla.") from None


def _append(sh, events):
    codec = cipher()
    tokens = [codec.encrypt(json.dumps(dict(event, version=1, time=_now()), ensure_ascii=False).encode()).decode()
              for event in events]
    if not tokens:
        return
    try:
        if sh is None:
            os.makedirs(storage.DATA_DIR, exist_ok=True)
            with open(LOCAL_LOG, "a", encoding="utf-8") as handle:
                handle.write("\n".join(tokens) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
        else:
            try:
                worksheet = sh.worksheet(WORKSHEET)
            except storage.gspread.WorksheetNotFound:
                worksheet = sh.add_worksheet(title=WORKSHEET, rows=1000, cols=1)
                worksheet.append_row(["payload"], value_input_option="RAW")
            worksheet.append_rows([[token] for token in tokens], value_input_option="RAW")
    except Exception:
        raise VotingError("Salvataggio non confermato. Aggiorna la pagina per controllare l'esito prima di riprovare.") from None


def load_events():
    with _runtime()[0]:
        return _read(_backend())


def credentials(events):
    return {event["player_id"]: event for event in events if event["type"] == "credential"}


def players_by_id(players):
    return {identifier(row["id_giocatore"]): str(row["nome_completo"]).strip()
            for _, row in players.iterrows()}


def _unique_code(used):
    if len(used) >= 100000:
        raise VotingError("Tutte le combinazioni di password disponibili sono già assegnate.")
    while True:
        code = f"{secrets.randbelow(100000):05d}"
        if code not in used:
            return code


def ensure_codes(players):
    require_admin()
    with _runtime()[0]:
        sh = _backend()
        events = _read(sh)
        existing = credentials(events)
        used = {event["code"] for event in events if event["type"] == "credential"}
        additions = []
        for player_id, name in players_by_id(players).items():
            if player_id not in existing or existing[player_id].get("player_name") != name:
                code = _unique_code(used)
                used.add(code)
                additions.append(dict(type="credential", player_id=player_id, player_name=name, code=code, revision=secrets.token_hex(16)))
        _append(sh, additions)
        return credentials(events + additions)


def rotate_code(players, player_id):
    require_admin()
    player_id = identifier(player_id)
    if player_id not in players_by_id(players):
        raise VotingError("Giocatore non trovato.")
    with _runtime()[0]:
        sh = _backend()
        events = _read(sh)
        used = {event["code"] for event in events if event["type"] == "credential"}
        event = dict(type="credential", player_id=player_id, player_name=players_by_id(players)[player_id], code=_unique_code(used), revision=secrets.token_hex(16))
        _append(sh, [event])


def _client_key():
    try:
        address = st.context.ip_address
    except (AttributeError, RuntimeError):
        address = None
    if not address:
        address = st.session_state.setdefault("voting_client", secrets.token_hex(16))
    return hashlib.sha256(str(address).encode()).hexdigest()


def check_attempts(scope):
    with _runtime()[0]:
        attempts = _runtime()[1]
        now = time.monotonic()
        for key in list(attempts):
            attempts[key] = [moment for moment in attempts[key] if now - moment < 300]
            if not attempts[key]:
                del attempts[key]
        if len(attempts.get((scope, _client_key()), [])) >= 5 or len(attempts.get((scope, "all"), [])) >= 100:
            raise VotingError("Troppi tentativi. Attendi 5 minuti prima di riprovare.")


def failed_attempt(scope):
    with _runtime()[0]:
        for key in [(scope, _client_key()), (scope, "all")]:
            _runtime()[1].setdefault(key, []).append(time.monotonic())


def authenticate(code, players):
    check_attempts("player")
    if not re.fullmatch(r"[0-9]{5}", code):
        failed_attempt("player")
        raise VotingError("Inserisci una password valida di 5 cifre.")
    with _runtime()[0]:
        known = players_by_id(players)
        found = [event for event in credentials(_read(_backend())).values()
                 if event["player_id"] in known and event.get("player_name") == known[event["player_id"]]
                 and hmac.compare_digest(event["code"], code)]
        if len(found) != 1:
            failed_attempt("player")
            raise VotingError("Password non valida.")
        credential = found[0]
        return dict(player_id=credential["player_id"], revision=credential["revision"])


def identity_name(identity, players, events):
    if not identity:
        raise VotingError("Inserisci la tua password personale per votare.")
    current = credentials(events).get(identity.get("player_id"))
    name = players_by_id(players).get(identity.get("player_id"))
    if not current or not name or current.get("player_name") != name or not hmac.compare_digest(current["revision"], identity.get("revision", "")):
        raise VotingError("Password aggiornata: accedi nuovamente con il tuo codice personale.")
    return name


def participants(match):
    return sorted({name.strip() for column in ("squadra_a_giocatori", "squadra_b_giocatori")
                   for name in str(match.get(column, "")).split(",") if name.strip() and name.strip() != "nan"})


def ballots(events, match_id):
    result = {}
    for event in events:
        if event.get("match_id") == identifier(match_id) and event["type"] == "ballot":
            result[event["player_id"]] = event
    return list(result.values())


def election(events, match_id):
    state = {"type": "open", "match_id": identifier(match_id)}
    for event in events:
        if event.get("match_id") == identifier(match_id) and event["type"] in {"open", "close"}:
            state = event
    return state


def tally(votes):
    result = {"total_ballots": len(votes)}
    for category in ("mvp", "worst"):
        counts = Counter(vote[category] for vote in votes)
        top = max(counts.values(), default=0)
        result[category + "_names"] = sorted(name for name, count in counts.items() if count == top)
        result[category + "_votes"] = top
    return result


def own_ballot(identity, events, match_id):
    return next((vote for vote in ballots(events, match_id) if vote["player_id"] == identity["player_id"]), None)


def submit_ballot(identity, players, match, mvp, worst):
    with _runtime()[0]:
        sh = _backend()
        events = _read(sh)
        name = identity_name(identity, players, events)
        match_id = identifier(match["id_partita"])
        if election(events, match_id)["type"] == "close":
            raise VotingError("La votazione è chiusa. Il tuo voto non è stato modificato.")
        roster = participants(match)
        if name not in roster:
            raise VotingError("Puoi votare solo le partite in cui hai giocato.")
        if mvp not in roster or worst not in roster:
            raise VotingError("Seleziona due giocatori della partita.")
        if name in {mvp, worst}:
            raise VotingError("Non puoi votare per te stesso.")
        if mvp == worst:
            raise VotingError("MVP e peggiore devono essere due giocatori diversi.")
        _append(sh, [dict(type="ballot", match_id=match_id, player_id=identity["player_id"], voter_name=name, mvp=mvp, worst=worst)])


def close_election(players, match):
    require_admin()
    with _runtime()[0]:
        sh = _backend()
        events = _read(sh)
        match_id = identifier(match["id_partita"])
        if election(events, match_id)["type"] == "close":
            raise VotingError("La votazione è già chiusa.")
        votes = ballots(events, match_id)
        if not votes:
            raise VotingError("Serve almeno un voto per pubblicare il risultato.")
        roster = participants(match)
        for vote in votes:
            if any(vote[field] not in roster for field in ("voter_name", "mvp", "worst")):
                raise VotingError("La rosa della partita è cambiata dopo i voti: ripristinala prima di chiudere la votazione.")
        result = tally(votes)
        _append(sh, [dict(type="close", match_id=match_id, result=result)])
        return result


def reopen_election(match_id):
    require_admin()
    with _runtime()[0]:
        sh = _backend()
        events = _read(sh)
        if election(events, match_id)["type"] != "close":
            raise VotingError("La votazione è già aperta.")
        _append(sh, [dict(type="open", match_id=identifier(match_id))])


def public_results_frame(matches, legacy_votes):
    """Return final summaries only. Never return ballot identities or codes."""
    import logic
    # An existing encrypted archive must never be replaced by legacy results
    # merely because the admin login configuration is temporarily unavailable.
    try:
        cipher()
    except VotingError:
        events = []
    else:
        events = load_events()
    started = {event["match_id"] for event in events if "match_id" in event}
    rows = []
    for _, match in matches.iterrows():
        match_id = identifier(match["id_partita"])
        state = election(events, match_id)
        if state["type"] == "close":
            row = dict(state["result"], id_partita=int(match_id))
        elif match_id not in started:
            old = logic.calculate_match_ratings(legacy_votes, int(match_id))
            if not old["has_votes"]:
                continue
            row = dict(id_partita=int(match_id), mvp_names=[old["mvp"]["giocatore"]] if old["mvp"] else [],
                       worst_names=[old["worst"]["giocatore"]] if old["worst"] else [],
                       mvp_votes=0, worst_votes=0, total_ballots=0)
        else:
            continue
        rows.append(row)
    return pd.DataFrame(rows, columns=PUBLIC_COLUMNS)


def next_identifier(frame, column, event_field):
    """Avoid reusing an ID whose old private records are still retained."""
    ids = [int(value) for value in frame[column]] if column in frame else []
    if configured():
        ids.extend(int(event[event_field]) for event in load_events() if event_field in event)
    return max(ids, default=0) + 1
