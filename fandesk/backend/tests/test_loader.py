import sqlite3


def test_season_year_is_the_ipl_edition(ipl_db):
    conn = sqlite3.connect(ipl_db)
    rows = dict(conn.execute("SELECT season, season_year FROM matches").fetchall())
    assert rows == {"2007/08": 2008, "2020/21": 2020, "2023": 2023}


def test_views_carry_season_year(ipl_db):
    conn = sqlite3.connect(ipl_db)
    for view in ("batting_stats", "bowling_stats", "team_results"):
        cols = [c[1] for c in conn.execute(f"PRAGMA table_info({view})")]
        assert "season_year" in cols, view


def test_batting_counts_runs_and_legal_balls(ipl_db):
    conn = sqlite3.connect(ipl_db)
    runs, balls, fours, sixes, dismissed = conn.execute(
        "SELECT runs, balls, fours, sixes, dismissed FROM batting_stats WHERE match_id = 1001 AND batter = 'A Batter'"
    ).fetchone()
    # 4 + 6 + wide + 0 (out): the wide is not a ball faced.
    assert (runs, balls, fours, sixes, dismissed) == (10, 3, 1, 1, 1)


def test_bowler_wickets_exclude_run_outs(ipl_db):
    conn = sqlite3.connect(ipl_db)
    wickets, balls, conceded = conn.execute(
        "SELECT wickets, balls, runs_conceded FROM bowling_stats WHERE match_id = 1001"
    ).fetchone()
    assert wickets == 1  # the catch counts, the run out does not
    assert balls == 4  # the wide is not a legal ball
    assert conceded == 12  # 4 + 6 + 1 wide + 1


def test_team_results_has_two_rows_per_match(ipl_db):
    conn = sqlite3.connect(ipl_db)
    assert conn.execute("SELECT COUNT(*) FROM team_results").fetchone()[0] == 6
    assert conn.execute("SELECT SUM(won) FROM team_results").fetchone()[0] == 3
