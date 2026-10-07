import json

import pytest

from app.tools.sql_tools import ROW_LIMIT, SqlGuardError, SqlTools, clean_select, run_query


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM matches",
        "DROP TABLE matches",
        "SELECT 1; DROP TABLE matches",
        "PRAGMA writable_schema = 1",
        "ATTACH DATABASE 'x.db' AS x",
        "",
        "-- just a comment",
    ],
)
def test_guard_rejects_non_select(sql):
    with pytest.raises(SqlGuardError):
        clean_select(sql)


def test_guard_allows_select_with_comments_and_trailing_semicolon():
    assert clean_select("-- top\nSELECT 1 /* x */;") == "SELECT 1"
    assert clean_select("WITH t AS (SELECT 1 AS a) SELECT a FROM t").startswith("WITH")


def test_limit_is_applied_by_wrapping(ipl_db):
    sql = "WITH RECURSIVE n(i) AS (SELECT 1 UNION ALL SELECT i + 1 FROM n WHERE i < 500) SELECT i FROM n"
    cols, rows = run_query(ipl_db, sql)
    assert cols == ["i"]
    assert len(rows) == ROW_LIMIT


def test_connection_is_read_only(ipl_db):
    # Even a write smuggled past the keyword check fails on a read-only connection.
    import sqlite3

    from app.tools.sql_tools import _connect

    conn = _connect(ipl_db)
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("DELETE FROM matches")
    conn.close()


def test_slow_query_times_out(ipl_db, monkeypatch):
    import app.tools.sql_tools as sql_tools

    monkeypatch.setattr(sql_tools, "TIMEOUT_S", 0.2)
    endless = "WITH RECURSIVE n(i) AS (SELECT 1 UNION ALL SELECT i + 1 FROM n) SELECT COUNT(*) FROM n"
    with pytest.raises(TimeoutError):
        run_query(ipl_db, endless)


async def test_get_schema_lists_views_first(ipl_db):
    out = await SqlTools(ipl_db).get_schema({})
    lines = out.text.splitlines()
    assert lines[0].startswith("VIEW")
    assert "season_year" in out.text
    assert "2008–2023" in out.text
    assert out.summary == "3 views, 2 tables"


async def test_run_sql_returns_rows_and_summary(ipl_db):
    out = await SqlTools(ipl_db).run_sql(
        {"sql": "SELECT bowler, SUM(wickets) AS w FROM bowling_stats WHERE season_year = 2023 GROUP BY bowler"}
    )
    assert out.ok
    assert json.loads(out.text) == {"columns": ["bowler", "w"], "rows": [["Z Bowler", 1]]}
    assert out.summary == "1 row"


async def test_run_sql_reports_errors_to_the_model(ipl_db):
    out = await SqlTools(ipl_db).run_sql({"sql": "UPDATE matches SET winner = 'x'"})
    assert not out.ok
    assert out.text.startswith("ERROR")
