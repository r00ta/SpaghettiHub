from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer


class Storage:
    def __init__(self) -> None:
        self.tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-large-en-v1.5")
        self.model = AutoModel.from_pretrained("BAAI/bge-large-en-v1.5")

    def print_bug(self, b, verbose=False):
        tqdm.write(f"LP#{b.bug.id}: [{b.status}] {b.bug.title}")
        if verbose:
            tqdm.write(f"URL: {b.bug.web_link}")
            tqdm.write(f"Created: {b.bug.date_created}")
            tqdm.write(f"Last Updated: {b.bug.date_last_updated}")
            tqdm.write(f"Description: {b.bug.description}")
            for i, m in enumerate(b.bug.messages):
                tqdm.write(f"Comment #{i + 1}")
                tqdm.write(f"{m.content}\n")
            tqdm.write("*" * 20)

    def store_bugs(self, bugs, context):
        if len(bugs) == 0:
            tqdm.write(f"Processing bugs [{context}]: no changes")
            return
        for b in tqdm(bugs, desc=f"Processing bugs [{context}]"):
            self._store_bug(b)

    def get_bug(self, bug_id):
        return self._get_bug_summary(bug_id) | {
            "comments": self._get_bug_comments(bug_id)
        }

    def _get_bug_summary(self, bug_id):
        cur = self.con.cursor()
        cur.execute(
            """
            SELECT text_id, content FROM texts WHERE text_id IN (
                SELECT title_id FROM issues WHERE bug_id = ?
            )
            """,
            (bug_id,),
        )
        title_id, title_content = cur.fetchone()
        cur.execute(
            """
            SELECT text_id, content FROM texts WHERE text_id IN (
                SELECT description_id FROM issues WHERE bug_id = ?
            )
            """,
            (bug_id,),
        )
        description_id, description_content = cur.fetchone()
        return {
            "bug_id": bug_id,
            "web_link": f"https://pad.lv/{bug_id}",
            "title": {"text_id": title_id, "content": title_content},
            "description": {"text_id": description_id, "content": description_content},
        }

    def _get_bug_comments(self, bug_id):
        cur = self.con.cursor()
        cur.execute(
            """
            SELECT text_id, content FROM texts WHERE text_id IN (
                SELECT text_id FROM issue_comments WHERE bug_id = ? ORDER BY rowid
            )
            """,
            (bug_id,),
        )
        comments = cur.fetchall()
        return [
            {"text_id": text_id, "content": comment} for text_id, comment in comments
        ]

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
                        (b.bug.id,),
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
                        (old_title_id, old_description_id),
                    )
                    cur.execute(
                        "DELETE FROM texts WHERE text_id IN (?, ?)",
                        (old_title_id, old_description_id),
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
            if len(texts_to_embed) == 0:
                tqdm.write("Processing embeddings: no changes")
                return

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
        cur.execute(
            """SELECT i.bug_id
            FROM issues i
            WHERE i.title_id = ?
            OR i.description_id = ?
            UNION
            SELECT i.bug_id
            FROM issues i
            INNER JOIN issue_comments ic ON i.bug_id = ic.bug_id
            WHERE ic.text_id = ?""",
            (text_id, text_id, text_id),
        )
        issue_id = cur.fetchone()
        return issue_id[0] if issue_id else None

    def close(self):
        self.con.close()

    def update_database(self):
        lp = Launchpad.login_with(
            "Bug Triage Assistant", "production", CACHEDIR, version="devel"
        )
        project = lp.projects[args.project]
        current_date = datetime.utcnow()
        last_updated = self.get_last_updated()
        if last_updated:
            tqdm.write(f"Last update: {last_updated}")
            self.store_bugs(
                project.searchTasks(status=BUG_STATES, created_since=last_updated),
                context="New",
            )
            self.store_bugs(
                project.searchTasks(status=BUG_STATES, modified_since=last_updated),
                context="Modified",
            )
        else:
            self.store_bugs(
                project.searchTasks(status=BUG_STATES), context="Full update"
            )
        self.set_last_updated(current_date)
        self.update_embeddings()
