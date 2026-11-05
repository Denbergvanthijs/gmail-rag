import struct
import sys

from gmail_rag.ingest import open_db


def sample(db, n):
    """Return n random emails with their stored embedding, to eyeball ingest results."""
    rows = db.execute(
        "SELECT e.rowid, e.id, e.subject, e.sender, e.date, e.body, v.embedding "
        "FROM emails e LEFT JOIN vec_emails v ON v.rowid = e.rowid ORDER BY random() LIMIT ?",
        (n,),
    ).fetchall()

    return [dict(zip(("rowid", "id", "subject", "sender", "date", "body", "embedding"), r)) for r in rows]


def main(n=5, db_path="./data/emails.db"):
    db = open_db(db_path)
    total = db.execute("SELECT count(*) FROM emails").fetchone()[0]
    vectors = db.execute("SELECT count(*) FROM vec_emails").fetchone()[0]
    print(f"{total} emails, {vectors} embeddings")

    for r in sample(db, n):
        vec = struct.unpack(f"{len(r['embedding']) // 4}f", r["embedding"]) if r["embedding"] else ()
        print("=" * 80)
        print(f"rowid:   {r['rowid']}\nid:      {r['id']}\nfrom:    {r['sender']}")
        print(f"date:    {r['date']}\nsubject: {r['subject']}")
        print(f"embedding: dim={len(vec)} first5={[round(x, 4) for x in vec[:5]]}")
        print(f"body ({len(r['body'])} chars):\n{r['body']}")


if __name__ == "__main__":
    # Script to sample and display random emails with their embeddings from the database
    # Used to quickly inspect the contents of the email database and verify embeddings
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 5)
