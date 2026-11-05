import base64
import sqlite3
import sys
from pathlib import Path
from typing import Any

import ollama
import sqlite_vec
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
MODEL = "all-minilm"
DIM = 384
# shortcut: all-minilm only sees ~256 tokens, so long mails are cut; chunk when retrieval quality needs it.
MAX_CHARS = 2000


def get_service() -> Any:  # noqa: ANN401 - googleapiclient builds its Resource methods dynamically
    """Authenticate with Gmail (OAuth, cached in secrets/token.json) and return the API service."""
    token_path = Path("./secrets/token.json")
    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES) if token_path.exists() else None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("./secrets/credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        token_path.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds)


def open_db(path: str = "./data/emails.db") -> sqlite3.Connection:
    """Open (and create if needed) the email database with the sqlite-vec extension loaded."""
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    db = sqlite3.connect(path)
    db.enable_load_extension(True)  # noqa: FBT003
    sqlite_vec.load(db)
    db.enable_load_extension(False)  # noqa: FBT003

    db.execute(
        "CREATE TABLE IF NOT EXISTS emails (rowid INTEGER PRIMARY KEY, id TEXT UNIQUE, subject TEXT, sender TEXT, date TEXT, body TEXT)"
    )
    db.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS vec_emails USING vec0(embedding float[{DIM}])")

    return db


def extract_body(payload: dict[str, Any]) -> str:
    """Return the first text/plain part of a Gmail message payload, decoded."""
    data = payload.get("body", {}).get("data")

    if data and payload.get("mimeType", "").startswith("text/plain"):
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        # Recursively check each part for a text/plain body
        body = extract_body(part)

        if body:
            return body

    return ""


def parse_message(msg: dict[str, Any]) -> dict[str, str]:
    """Reduce a full Gmail message to id, subject, sender, date and plain-text body."""
    headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}

    return {
        "id": msg["id"],
        "subject": headers.get("subject", ""),
        "sender": headers.get("from", ""),
        "date": headers.get("date", ""),
        "body": extract_body(msg["payload"]),
    }


def store(db: sqlite3.Connection, mail: dict[str, str], embedding: list[float]) -> None:
    """Insert a mail and its embedding; mails that are already stored are ignored."""
    cur = db.execute(
        "INSERT OR IGNORE INTO emails (id, subject, sender, date, body) VALUES (?, ?, ?, ?, ?)",
        (mail["id"], mail["subject"], mail["sender"], mail["date"], mail["body"]),
    )

    if cur.rowcount:
        db.execute(
            "INSERT INTO vec_emails (rowid, embedding) VALUES (?, ?)",
            (cur.lastrowid, sqlite_vec.serialize_float32(embedding)),
        )
    db.commit()


def embed(mail: dict[str, str]) -> list[float]:
    """Embed subject and body with the Ollama model."""
    text = f"{mail['subject']}\n{mail['body']}"[:MAX_CHARS]

    return ollama.embed(model=MODEL, input=text)["embeddings"][0]


def ingest(max_results: int = 20, db_path: str = "./data/emails.db") -> None:
    """Fetch the latest mails from Gmail, embed the new ones and store them."""
    service = get_service()
    db = open_db(db_path)

    refs = service.users().messages().list(userId="me", maxResults=max_results).execute().get("messages", [])
    for ref in refs:
        # Skip if the email is already stored in the database
        if db.execute("SELECT 1 FROM emails WHERE id = ?", (ref["id"],)).fetchone():
            continue

        # Gather the full message details from the Gmail API
        msg = service.users().messages().get(userId="me", id=ref["id"], format="full").execute()
        mail = parse_message(msg)
        mail_embedding = embed(mail)

        store(db, mail, mail_embedding)
        print(f"Stored: {mail['subject']}")


if __name__ == "__main__":
    ingest(int(sys.argv[1]) if len(sys.argv) > 1 else 20)
