import argparse
import sqlite3
import numpy as np
import pprint
from numpy.linalg import norm
from datetime import datetime
from tqdm import tqdm
from launchpadlib.launchpad import Launchpad
from transformers import AutoTokenizer, AutoModel

CACHEDIR = "./cache"
BUG_STATES = [
    "New",
    "Triaged",
    "Confirmed",
    "In Progress",
    "Fix Committed",
    "Fix Released",
    "Incomplete",
    "Invalid",
    "Won't Fix",
]

def cosine_similarity(a, b):
    return np.dot(a, b)/(norm(a) * norm(b))

class Search:
    def __init__(self, storage):
        self.storage = storage
        self.embeddings = []
        self.load_embeddings()

    def load_embeddings(self):
        self.embeddings = self.storage.get_embeddings()
    
    def find_similar_texts(self, prompt):
        q = self.storage.generate_embedding(prompt)
        return sorted(((cosine_similarity(q, e), i) for i, e in self.embeddings), reverse=True)

    def _add_scores(self, nested_dict, score_mapping):
        if "text_id" in nested_dict:
            nested_dict["score"] = str(score_mapping[nested_dict["text_id"]])
        else:
            for v in nested_dict.values():
                if isinstance(v, dict):
                    self._add_scores(v, score_mapping)
                elif isinstance(v, list):
                    for item in v:
                        self._add_scores(item, score_mapping)
    
    def find_similar_issues(self, prompt, limit=10):
        top_scores = []
        unique_issues = set()
        matching_issues = []
        scores = self.find_similar_texts(prompt)
        for similarity, text_id in scores:
            bug_id = self.storage.get_issue_related_with_text_id(text_id)
            top_scores.append((text_id, str(similarity)))
            unique_issues.add(bug_id)
            if len(unique_issues) == limit:
                break
        text_id_to_score = {text_id: score for score, text_id in scores}
        for bug_id in unique_issues:
            issue = self.storage.get_bug(bug_id)
            self._add_scores(issue, text_id_to_score)
            matching_issues.append(issue)
        return {"scores": top_scores, "issues":matching_issues}

class Storage:
    def __init__(self, name) -> None:
        self.con = self._create_database(name)
        self._create_tables()
        self.tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-large-en-v1.5")
        self.model = AutoModel.from_pretrained("BAAI/bge-large-en-v1.5")

    def _create_database(self, name="issues"):
        db_name = f"{name}.db"
        con = sqlite3.connect(db_name)
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
        return con

    def _create_tables(self):
        cur = self.con.cursor()
        cur.executescript(
            """
            -- Table to store text content and a table for text embeddings
            CREATE TABLE IF NOT EXISTS texts (
                text_id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS embeddings (
                text_id INTEGER NOT NULL,
                embedding BLOB,
                FOREIGN KEY (text_id) REFERENCES texts(text_id)
            );

            -- Table to store issues
            CREATE TABLE IF NOT EXISTS issues (
                bug_id INTEGER PRIMARY KEY,
                date_created DATETIME NOT NULL,
                date_last_updated DATETIME NOT NULL,
                web_link TEXT NOT NULL,
                title_id INTEGER NOT NULL,
                description_id INTEGER NOT NULL,
                FOREIGN KEY (title_id) REFERENCES texts(text_id),
                FOREIGN KEY (description_id) REFERENCES texts(text_id)
            );

            -- Table to store issue comments
            CREATE TABLE IF NOT EXISTS issue_comments (
                bug_id INTEGER NOT NULL,
                text_id INTEGER NOT NULL,
                FOREIGN KEY (bug_id) REFERENCES issues(bug_id),
                FOREIGN KEY (text_id) REFERENCES texts(text_id)
            );
                            
            -- Table to store the date of the last update
            CREATE TABLE IF NOT EXISTS update_history (
                last_updated DATETIME
            );
            """
        )
        cur.close()

    def print_bug(self, b, verbose=False):
        tqdm.write(f"LP#{b.bug.id}: [{b.status}] {b.bug.title}")
        if verbose:
            tqdm.write(f"URL: {b.bug.web_link}")
            tqdm.write(f"Created: {b.bug.date_created}")
            tqdm.write(f"Last Updated: {b.bug.date_last_updated}")
            tqdm.write(f"Description: {b.bug.description}")
            for i, m in enumerate(b.bug.messages):
                tqdm.write(f"Comment #{i+1}")
                tqdm.write(f"{m.content}\n")
            tqdm.write("*" * 20)

    def store_bugs(self, bugs, context):
        for b in tqdm(bugs, desc=f"Processing bugs [{context}]"):
            self._store_bug(b)

    def get_bug(self, bug_id):
        return self._get_bug_summary(bug_id) | {"comments": self._get_bug_comments(bug_id)}
    
    def _get_bug_summary(self, bug_id):
        cur = self.con.cursor()
        cur.execute("""
                SELECT text_id, content FROM texts WHERE text_id IN (
                    SELECT title_id FROM issues WHERE bug_id = ?
                )
                    """, (bug_id,))
        title_id, title_content = cur.fetchone()
        cur.execute("""
                SELECT text_id, content FROM texts WHERE text_id IN (
                    SELECT description_id FROM issues WHERE bug_id = ?
                )
                    """, (bug_id,))
        description_id, description_content = cur.fetchone()
        return { "bug_id": bug_id,
            "title": {"text_id" : title_id, "content": title_content},
            "description": {"text_id" : description_id, "content": description_content},
            }

    def _get_bug_comments(self, bug_id):
        cur = self.con.cursor()
        cur.execute("""
                SELECT text_id, content FROM texts WHERE text_id IN (
                    SELECT text_id FROM issue_comments WHERE bug_id = ? ORDER BY rowid
                )
                    """, (bug_id,))
        comments = cur.fetchall()
        return [{"text_id": text_id, "content": comment} for text_id, comment in comments]
    
    def _store_bug(self, b):
        cur = self.con.cursor()
        try:
            # Check if bug already exists and get its last updated date
            cur.execute(
                "SELECT date_last_updated FROM issues WHERE bug_id = ?", (b.bug.id,)
            )
            existing_bug = cur.fetchone()

            if (
                existing_bug is None
                or datetime.strptime(existing_bug[0], "%Y-%m-%d %H:%M:%S.%f%z")
                < b.bug.date_last_updated
            ):
                self.con.execute("BEGIN TRANSACTION")
                # Bug is not in database or is outdated, so insert or update it
                title_id = cur.execute(
                    "INSERT INTO texts (content) VALUES (?)", (b.bug.title,)
                ).lastrowid
                description_id = cur.execute(
                    "INSERT INTO texts (content) VALUES (?)", (b.bug.description,)
                ).lastrowid
                if existing_bug is None:
                    # Insert new bug
                    cur.execute(
                        """
                        INSERT INTO issues (bug_id, date_created, date_last_updated, web_link, title_id, description_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            b.bug.id,
                            b.bug.date_created,
                            b.bug.date_last_updated,
                            b.bug.web_link,
                            title_id,
                            description_id,
                        ),
                    )
                else:
                    # Update existing bug
                    cur.execute(
                        "SELECT title_id, description_id FROM issues WHERE bug_id = ?",
                        (b.bug.id,)
                    )
                    old_title_id, old_description_id = cur.fetchone()
                    cur.execute(
                        """
                        UPDATE issues SET date_last_updated = ?, title_id = ?, description_id = ?
                        WHERE bug_id = ?
                        """,
                        (b.bug.date_last_updated, title_id, description_id, b.bug.id),
                    )
                    cur.execute(
                        "DELETE FROM embeddings WHERE text_id IN (?, ?)",
                        (old_title_id, old_description_id)
                    )
                    cur.execute(
                        "DELETE FROM texts WHERE text_id IN (?, ?)",
                        (old_title_id, old_description_id)
                    )

                # Delete existing comments before adding updated comments
                cur.execute(
                    "DELETE FROM embeddings WHERE text_id IN (SELECT text_id FROM issue_comments WHERE bug_id = ?)",
                    (b.bug.id,),
                )
                cur.execute(
                    "DELETE FROM texts WHERE text_id IN (SELECT text_id FROM issue_comments WHERE bug_id = ?)",
                    (b.bug.id,),
                )
                cur.execute("DELETE FROM issue_comments WHERE bug_id = ?", (b.bug.id,))

                # Insert comments data
                first = True
                for m in b.bug.messages: 
                    # skip comment #0 which is identical to the description
                    if first:
                        first = False
                        continue
                    comment_id = cur.execute(
                        "INSERT INTO texts (content) VALUES (?)", (m.content,)
                    ).lastrowid
                    cur.execute(
                        "INSERT INTO issue_comments (bug_id, text_id) VALUES (?, ?)",
                        (b.bug.id, comment_id),
                    )

                self.con.commit()
                self.print_bug(
                    b, verbose=True
                )  # TODO: retrieve verbosity from command line parameters
            else:
                tqdm.write(f"Bug LP#{b.bug.id} [{b.status}] is up to date, skipping...")
        except Exception as e:
            self.con.rollback()
            print(f"When processing bug {b.bug.id}, an error occurred: {e}")
        finally:
            cur.close()

    def generate_embedding(self, content):
        inputs = self.tokenizer(
            content, return_tensors="pt", truncation=True, padding=True
        )
        outputs = self.model(**inputs)
        embeddings = outputs.last_hidden_state.mean(dim=1)
        return embeddings.cpu().detach().numpy()[0]

    def update_embeddings(self):
        cur = self.con.cursor()
        try:
            cur.execute(
                """
                SELECT t.text_id, t.content FROM texts t
                LEFT JOIN embeddings e ON t.text_id = e.text_id
                WHERE e.text_id IS NULL
                """
            )
            texts_to_embed = cur.fetchall()

            for text_id, content in tqdm(texts_to_embed, desc="Generating embeddings"):
                # Start a transaction for each embedding creation
                self.con.execute("BEGIN TRANSACTION")
                # Generate and insert embedding
                embedding = self.generate_embedding(content).tobytes()
                cur.execute(
                    "INSERT INTO embeddings (text_id, embedding) VALUES (?, ?)",
                    (text_id, embedding),
                )
                self.con.commit()  # Commit the transaction after each embedding creation

        except Exception as e:
            self.con.rollback()  # Rollback the transaction in case of error
            print(f"An error occurred: {e}")
        finally:
            cur.close()

    def get_embeddings(self):
        cur = self.con.cursor()
        cur.execute("SELECT text_id, embedding FROM embeddings")
        embeddings = cur.fetchall()
        return (
            (text_id, np.frombuffer(b, dtype=np.float32)) for text_id, b in embeddings
        )

    def set_last_updated(self, date):
        cur = self.con.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO update_history (rowid, last_updated) VALUES (1, ?)",
            (date,),
        )
        self.con.commit()

    def get_last_updated(self):
        cur = self.con.cursor()
        cur.execute("SELECT last_updated FROM update_history WHERE rowid = 1")
        result = cur.fetchone()
        return datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S.%f") if result else None

    def get_issue_related_with_text_id(self, text_id):
        cur = self.con.cursor()
        cur.execute("""SELECT i.bug_id
            FROM issues i
            WHERE i.title_id = ?
            OR i.description_id = ?
            UNION
            SELECT i.bug_id
            FROM issues i
            INNER JOIN issue_comments ic ON i.bug_id = ic.bug_id
            WHERE ic.text_id = ?""", (text_id, text_id, text_id))
        issue_id = cur.fetchone()
        return issue_id[0] if issue_id else None

    def close(self):
        self.con.close()


def update_database(st):
    lp = Launchpad.login_with(
        "Bug Triage Assistant", "production", CACHEDIR, version="devel"
    )
    project = lp.projects[args.project]
    current_date = datetime.utcnow()
    last_updated = st.get_last_updated()
    tqdm.write(f"Last update: {last_updated}")
    if last_updated:
        st.store_bugs(
            project.searchTasks(status=BUG_STATES, created_since=last_updated),
            context="New",
        )
        st.store_bugs(
            project.searchTasks(status=BUG_STATES, modified_since=last_updated),
            context="Modified",
        )
    else:
        st.store_bugs(project.searchTasks(status=BUG_STATES), context="Full update")
    st.set_last_updated(current_date)
    st.update_embeddings()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="launchpad-bug-triage",
        description="Launchpad Bug Triage Assistant",
    )
    parser.add_argument(
        "-p", "--project", default="maas", help="Launchpad project name"
    )
    args = parser.parse_args()

    st = Storage(args.project)
    update_database(st)
    s = Search(st)

    pprint.pprint(s.find_similar_issues("multipath issue", limit=5))
    st.close()
