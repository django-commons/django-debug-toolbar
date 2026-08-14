import logging
import uuid

from django.db import DatabaseError

logger = logging.getLogger(__name__)


class OracleExplainPlanHelper:
    """
    A helper class to run, format, and audit Oracle SQL EXPLAIN PLANs.

    Architecture & Lifecycle:
        Unlike unified single-command engines (like PostgreSQL's "EXPLAIN ANALYZE"),
        Oracle requires an orchestrated multi-step workflow:
        1. Generation: Executes "EXPLAIN PLAN" to estimate cost and record execution
           path nodes under a unique STATEMENT_ID in the session's PLAN_TABLE.
        2. Formatting: Queries "DBMS_XPLAN.DISPLAY" to extract and format those nodes
           from the PLAN_TABLE into structured, human-readable ASCII text.
        3. Auditing: Parses the plan nodes to identify all accessed tables and indexes,
           fetching their performance, status, and size metadata from the Oracle
           dictionary catalog views (ALL_TABLES & ALL_INDEXES).
        4. ASCII Rendering: Appends the catalog metrics formatted as aligned ASCII tables.
        5. Cleanup: Deletes the temporary nodes created in PLAN_TABLE to prevent session
           pollution and table growth.
        6. QBR Suppression: Conditionally filters out the Query Block Registry section.

    Security Mandate:
        Because the Oracle "EXPLAIN PLAN" syntax requires the literal query text,
        this class performs direct string interpolation on the `sql` argument.
        IT IS MANDATORY that any caller ensures the `sql` argument is safe and
        pre-validated against SQL injection before executing. Within the toolbar's
        context, this is secure as SQL strings are fetched solely from the
        cryptographically signed server-side cache.

    Database Version Adaptation:
        - Oracle < 21: The database outputs the Query Block Registry (QBR) as raw
          nested XML. This XML can cause infinite recursion and memory exhaustion on
          unprepared markdown parsers (such as certain LLM CLIs). The helper
          automatically identifies and suppresses this section if `suppress_qbr_block`
          is active and the connection version is legacy to 21.
        - Oracle 21c/23c+: The database natively formats the QBR as clean, structured,
          hierarchical plain text. The helper preserves and displays this text safely.

    Class Attributes:
        display_format (str): The formatting arguments passed to DBMS_XPLAN.DISPLAY.
                              Defaults to "ADVANCED +ADAPTIVE".
        chunk_size (int): The maximum number of table/index names processed in a single
                          IN clause when fetching catalog statistics. Defaults to 50.
        suppress_qbr_block (bool): Whether to suppress the Query Block Registry for
                                   Oracle < 21 connections. Defaults to True.
        include_catalog_audit (bool): Whether to query and append the metadata tables
                                      for tables and indexes. Defaults to True.
    """

    display_format = "ADVANCED +ADAPTIVE"
    chunk_size = 50
    suppress_qbr_block = True
    include_catalog_audit = True

    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, sql, params):
        """
        Orchestrates the Oracle explain workflow:
        1. Run EXPLAIN PLAN using a unique statement ID.
        2. Query DBMS_XPLAN.DISPLAY for the detailed execution plan.
        3. Attempt to fetch database catalog statistics for involved schemas.
        4. Render schema health audit reports as aligned ASCII tables.
        5. Clean up temporary rows from the PLAN_TABLE.
        6. Suppress the dangerous "Query Block Registry" block.
        """
        stmt_id = f"dt_{uuid.uuid4().hex[:25]}"

        try:
            # 1. Fetch raw execution plan lines from DBMS_XPLAN
            result = self._fetch_raw_plan(sql, params, stmt_id)

            # 2. Extract involved tables/indexes for schema health audit
            if self.include_catalog_audit:
                try:
                    # Graceful fallback: skip optional audit if catalog
                    # views are inaccessible.
                    table_keys = self._get_involved_tables(stmt_id)
                    if table_keys:
                        table_stats, index_stats = self._fetch_catalog_statistics(
                            table_keys
                        )
                        audit_lines = self._render_stats_as_ascii(
                            table_stats, index_stats
                        )
                        for line in audit_lines:
                            result.append((line,))
                except DatabaseError as e:
                    # Sanitize the error to prevent leaking sensitive schema
                    # names or data. Extract the generic exception class name
                    # to assist in debugging without PII.
                    error_type = type(e).__name__
                    logger.warning(
                        "Oracle catalog audit skipped due to a database "
                        "exception [%s]. This usually indicates restricted "
                        "user permissions on dictionary views.",
                        error_type,
                    )

            # 3. Suppress "Query Block Registry" to
            # prevent client OOM on some LLMs
            # on Oracle < 21
            if self.suppress_qbr_block and self._oracle_version < (21,):
                result = self._suppress_qbr(result)
            return result, ["PLAN_TABLE_OUTPUT"]

        finally:
            self._cleanup_plan_table(stmt_id)

    def _fetch_raw_plan(self, sql, params, stmt_id):
        """
        Executes the statement explain and retrieves plan lines.

        Note on Two-Query Flow: Unlike PostgreSQL's unified single-command
        "EXPLAIN ANALYZE", Oracle separates execution plan generation from
        plan formatting. The first query executes "EXPLAIN PLAN" to generate
        and write the raw plan metadata into the session's PLAN_TABLE.
        The second query then calls "dbms_xplan.display" as a table function
        to fetch, format, and return those rows as structured ASCII text.

        Note on SQL Safety: Refer to the Security Mandate in the class docstring.
        Values inside `sql` remain safely bound via `params`.
        """
        self.cursor.execute(
            f"EXPLAIN PLAN SET STATEMENT_ID = '{stmt_id}' FOR {sql}", params
        )
        self.cursor.execute(
            "SELECT plan_table_output FROM table(dbms_xplan.display("
            f"'PLAN_TABLE', %s, '{self.display_format}'))",
            [stmt_id],
        )
        return self.cursor.fetchall()

    def _get_involved_tables(self, stmt_id):
        """
        Interrogates PLAN_TABLE and reverse maps indexes
        to identify all involved tables.
        """
        # Get active connection username to resolve any NULL owners
        current_user = None
        raw_cursor = getattr(self.cursor, "cursor", None)
        if raw_cursor and hasattr(raw_cursor, "connection"):
            current_user = getattr(raw_cursor.connection, "username", None)
        if current_user:
            current_user = current_user.upper()

        # Fetch tables from PLAN_TABLE
        self.cursor.execute(
            (
                "SELECT DISTINCT object_owner, object_name "
                "FROM PLAN_TABLE "
                "WHERE statement_id = %s "
                "AND object_type = 'TABLE' "
                "AND object_name IS NOT NULL"
            ),
            [stmt_id],
        )
        tbl_rows = self.cursor.fetchall()
        table_keys = {
            (r[0].upper() if r[0] else current_user, r[1]) for r in tbl_rows if r[1]
        }

        # Fetch indexes from PLAN_TABLE
        self.cursor.execute(
            (
                "SELECT DISTINCT object_owner, object_name "
                "FROM PLAN_TABLE "
                "WHERE statement_id = %s "
                "AND object_type = 'INDEX' "
                "AND object_name IS NOT NULL"
            ),
            [stmt_id],
        )
        idx_rows = self.cursor.fetchall()
        idx_keys = [
            (r[0].upper() if r[0] else current_user, r[1]) for r in idx_rows if r[1]
        ]

        # Reverse map index ownership to locate parent tables in all_indexes
        if idx_keys:
            for i in range(0, len(idx_keys), self.chunk_size):
                chunk = idx_keys[i : i + self.chunk_size]
                conditions = " OR ".join(
                    ["(owner = %s AND index_name = %s)"] * len(chunk)
                )
                params = []
                for owner, name in chunk:
                    params.extend([owner, name])

                self.cursor.execute(
                    (
                        "SELECT DISTINCT table_owner, table_name "
                        "FROM all_indexes "
                        f"WHERE {conditions}"
                    ),
                    params,
                )
                mapped_tbl_rows = self.cursor.fetchall()
                for r in mapped_tbl_rows:
                    if r[1]:
                        table_keys.add((r[0], r[1]))

        return table_keys

    def _fetch_catalog_statistics(self, table_keys):
        """
        Fetches bulk performance statistics and health flags
        from standard dictionary views.
        """
        table_stats = []
        index_stats = []
        table_keys_list = list(table_keys)

        for i in range(0, len(table_keys_list), self.chunk_size):
            chunk = table_keys_list[i : i + self.chunk_size]

            table_conditions = []
            table_params = []
            for owner, name in chunk:
                table_conditions.append("(owner = %s AND table_name = %s)")
                table_params.extend([owner, name])

            table_where_clause = " OR ".join(table_conditions)

            # Retrieve table storage metrics
            self.cursor.execute(
                (
                    "SELECT owner, table_name, num_rows, blocks, avg_row_len, "
                    "TO_CHAR(last_analyzed, 'YYYY-MM-DD HH24:MI:SS') as "
                    "last_analyzed "
                    "FROM all_tables "
                    f"WHERE {table_where_clause}"
                ),
                table_params,
            )
            table_stats.extend(self.cursor.fetchall())

            # Retrieve index performance and integrity statuses
            self.cursor.execute(
                (
                    "SELECT owner, index_name, table_name, uniqueness, status, "
                    "TO_CHAR(last_analyzed, 'YYYY-MM-DD HH24:MI:SS') as "
                    "last_analyzed "
                    "FROM all_indexes "
                    f"WHERE {table_where_clause} "
                    "ORDER BY table_name, index_name"
                ),
                table_params,
            )
            index_stats.extend(self.cursor.fetchall())

        return table_stats, index_stats

    def _render_stats_as_ascii(self, table_stats, index_stats):
        """
        Formats the database metadata and catalog rows
        into visual, aligned ASCII tables.
        """
        if not table_stats and not index_stats:
            return []

        # Determine dynamic column widths to fit all content cleanly
        t_col_owner = max([len(str(r[0])) for r in table_stats] + [15])
        t_col_name = max([len(str(r[1])) for r in table_stats] + [30])
        table_border = (
            f"+{'-' * (t_col_owner + 2)}+{'-' * (t_col_name + 2)}+"
            f"{'-' * 12}+{'-' * 12}+{'-' * 13}+{'-' * 21}+"
        )

        idx_col_owner = max([len(str(r[0])) for r in index_stats] + [15])
        idx_col_name = max([len(str(r[1])) for r in index_stats] + [30])
        t_col_idx = max([len(str(r[2])) for r in index_stats] + [25])
        index_border = (
            f"+{'-' * (idx_col_owner + 2)}+{'-' * (idx_col_name + 2)}+"
            f"{'-' * (t_col_idx + 2)}+{'-' * 12}+{'-' * 10}+{'-' * 21}+"
        )

        audit_lines = [
            "",
            "",
            "Schema Health & Statistics Audit (ALL_TABLES & ALL_INDEXES)",
            "================================================================",
            "Table Statistics:",
            table_border,
            (
                f"| {'Owner':<{t_col_owner}} | {'Table Name':<{t_col_name}} | "
                f"{'Num Rows':<10} | {'Blocks':<10} | {'Avg Row Len':<11} | "
                f"{'Last Analyzed':<19} |"
            ),
            table_border,
        ]

        for r in table_stats:
            owner = str(r[0])
            t_name = str(r[1])
            num_rows = str(r[2]) if r[2] is not None else "—"
            blocks = str(r[3]) if r[3] is not None else "—"
            avg_len = str(r[4]) if r[4] is not None else "—"
            analyzed = str(r[5]) if r[5] is not None else "—"
            audit_lines.append(
                f"| {owner:<{t_col_owner}} | {t_name:<{t_col_name}} | "
                f"{num_rows:<10} | {blocks:<10} | {avg_len:<11} | "
                f"{analyzed:<19} |"
            )
        audit_lines.append(table_border)

        audit_lines.extend(
            [
                "",
                "Index Statistics & Status:",
                index_border,
                (
                    f"| {'Owner':<{idx_col_owner}} | {'Index Name':<{idx_col_name}} | "
                    f"{'Table Name':<{t_col_idx}} | {'Uniqueness':<10} | "
                    f"{'Status':<8} | {'Last Analyzed':<19} |"
                ),
                index_border,
            ]
        )

        for r in index_stats:
            owner = str(r[0])
            idx_name = str(r[1])
            t_name = str(r[2])
            uniq = str(r[3])
            status = str(r[4])
            analyzed = str(r[5]) if r[5] is not None else "—"
            audit_lines.append(
                f"| {owner:<{idx_col_owner}} | {idx_name:<{idx_col_name}} | "
                f"{t_name:<{t_col_idx}} | {uniq:<10} | {status:<8} | "
                f"{analyzed:<19} |"
            )
        audit_lines.append(index_border)

        return audit_lines

    @property
    def _oracle_version(self):
        """Resolves the Oracle database version tuple dynamically."""
        db = getattr(self.cursor, "db", None)
        version = getattr(db, "oracle_version", None)
        if isinstance(version, (tuple, list)):
            return version
        return (19,)  # Safe fallback for Oracle < 21 and mock/test environments

    def _suppress_qbr(self, result):
        """Locates and slices out Query Block Registry lines."""
        qbr_start = None
        qbr_end = None

        for i, row in enumerate(result):
            line = row[0] if row and row[0] is not None else ""
            if "Query Block Registry:" in line:
                qbr_start = i
                break

        if qbr_start is None:
            return result

        # Find where the QBR block ends.
        # Any line starting with a non-space character (excluding dashed/equals lines or
        # empty lines) indicates the end of the QBR block and start of another section.
        for i in range(qbr_start + 2, len(result)):
            line = result[i][0] if result[i] and result[i][0] is not None else ""
            stripped = line.strip()
            if not stripped:
                continue
            if not line.startswith(" ") and not all(c in "-=" for c in stripped):
                qbr_end = i
                break

        if qbr_end is not None:
            return result[:qbr_start] + result[qbr_end:]
        return result[:qbr_start]

    def _cleanup_plan_table(self, stmt_id):
        """Deletes any temporary rows created in PLAN_TABLE."""
        try:
            self.cursor.execute(
                "DELETE FROM PLAN_TABLE WHERE statement_id = %s", [stmt_id]
            )
        except DatabaseError as e:
            error_type = type(e).__name__
            logger.warning(
                "Failed to clean up PLAN_TABLE [%s]. Session pollution may occur.",
                error_type,
            )
