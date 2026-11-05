import base64

from ingest import DIM, open_db, parse_message, store


def b64(s):
    return base64.urlsafe_b64encode(s.encode()).decode()


def test_parse_message_nested_multipart():
    msg = {
        "id": "1",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Hi"},
                {"name": "From", "value": "a@b.c"},
            ],
            "mimeType": "multipart/alternative",
            "parts": [{"mimeType": "text/plain", "body": {"data": b64("hello")}}],
        },
    }

    mail = parse_message(msg)

    assert (mail["subject"], mail["sender"], mail["body"]) == ("Hi", "a@b.c", "hello")


def test_store_is_idempotent_and_searchable():
    db = open_db(":memory:")
    mail = {"id": "1", "subject": "s", "sender": "x", "date": "d", "body": "b"}

    store(db, mail, [0.1] * DIM)
    store(db, mail, [0.1] * DIM)

    assert db.execute("SELECT count(*) FROM emails").fetchone()[0] == 1
    assert db.execute("SELECT count(*) FROM vec_emails").fetchone()[0] == 1
