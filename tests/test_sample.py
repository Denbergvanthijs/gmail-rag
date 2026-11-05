from gmail_rag.ingest import DIM, open_db, store
from gmail_rag.sample import sample


def test_sample_returns_n_rows_with_embedding():
    db = open_db(":memory:")

    for i in range(3):
        store(
            db,
            {"id": str(i), "subject": "s", "sender": "x", "date": "d", "body": "b"},
            [0.1] * DIM,
        )
    rows = sample(db, 2)

    assert len(rows) == 2
    assert all(len(r["embedding"]) == DIM * 4 for r in rows)
