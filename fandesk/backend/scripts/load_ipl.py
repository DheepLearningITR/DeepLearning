"""Build ipl.db from Cricsheet's IPL CSV archive (ball-by-ball, 2008 onward).

    python scripts/load_ipl.py --out data/ipl.db [--zip path/to/ipl_csv2.zip]

The archive has, per match, `<id>.csv` (one row per ball) and `<id>_info.csv`
(key/value lines such as `info,season,2007/08`). Info files are pivoted into the
`matches` table. Cricsheet labels some seasons like "2007/08" or "2020/21", so
every table and view carries `season_year`: the calendar year the match was
played, which is the IPL edition (2008, 2010, 2020...).
"""

import argparse
import csv
import io
import sqlite3
import sys
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

URL = "https://cricsheet.org/downloads/ipl_csv2.zip"

# Dismissals credited to the bowler; run outs, retirements etc. are not.
BOWLER_WICKETS = ("bowled", "caught", "caught and bowled", "lbw", "stumped", "hit wicket")

SCHEMA = f"""
CREATE TABLE matches (
    match_id        INTEGER PRIMARY KEY,
    season          TEXT,
    season_year     INTEGER NOT NULL,
    date            TEXT,
    venue           TEXT,
    city            TEXT,
    team1           TEXT,
    team2           TEXT,
    toss_winner     TEXT,
    toss_decision   TEXT,
    winner          TEXT,
    win_by_runs     INTEGER,
    win_by_wickets  INTEGER,
    result          TEXT,
    player_of_match TEXT
);
CREATE TABLE deliveries (
    match_id        INTEGER NOT NULL REFERENCES matches(match_id),
    season_year     INTEGER NOT NULL,
    innings         INTEGER,
    over            INTEGER,
    ball            INTEGER,
    batting_team    TEXT,
    bowling_team    TEXT,
    batter          TEXT,
    non_striker     TEXT,
    bowler          TEXT,
    runs_off_bat    INTEGER,
    extras          INTEGER,
    wides           INTEGER,
    noballs         INTEGER,
    byes            INTEGER,
    legbyes         INTEGER,
    wicket_type     TEXT,
    player_dismissed TEXT
);
CREATE INDEX deliveries_match ON deliveries(match_id);
CREATE INDEX deliveries_batter ON deliveries(batter);
CREATE INDEX deliveries_bowler ON deliveries(bowler);

-- One row per batter per match.
CREATE VIEW batting_stats AS
SELECT d.match_id, d.season_year, d.batting_team AS team, d.batter,
       SUM(d.runs_off_bat) AS runs,
       SUM(CASE WHEN d.wides = 0 THEN 1 ELSE 0 END) AS balls,
       SUM(CASE WHEN d.runs_off_bat = 4 THEN 1 ELSE 0 END) AS fours,
       SUM(CASE WHEN d.runs_off_bat = 6 THEN 1 ELSE 0 END) AS sixes,
       MAX(CASE WHEN d.player_dismissed = d.batter THEN 1 ELSE 0 END) AS dismissed
FROM deliveries d
GROUP BY d.match_id, d.batting_team, d.batter;

-- One row per bowler per match. Only bowler-credited dismissals count as wickets.
CREATE VIEW bowling_stats AS
SELECT d.match_id, d.season_year, d.bowling_team AS team, d.bowler,
       SUM(CASE WHEN d.wides = 0 AND d.noballs = 0 THEN 1 ELSE 0 END) AS balls,
       SUM(d.runs_off_bat + d.wides + d.noballs) AS runs_conceded,
       SUM(CASE WHEN d.wicket_type IN ({", ".join(f"'{w}'" for w in BOWLER_WICKETS)}) THEN 1 ELSE 0 END) AS wickets
FROM deliveries d
GROUP BY d.match_id, d.bowling_team, d.bowler;

-- One row per team per match.
CREATE VIEW team_results AS
SELECT match_id, season_year, date, venue, team1 AS team, team2 AS opponent,
       CASE WHEN winner = team1 THEN 1 ELSE 0 END AS won, result
FROM matches
UNION ALL
SELECT match_id, season_year, date, venue, team2 AS team, team1 AS opponent,
       CASE WHEN winner = team2 THEN 1 ELSE 0 END AS won, result
FROM matches;
"""


def _int(value: str | None) -> int:
    try:
        return int(value) if value not in (None, "") else 0
    except ValueError:
        return 0


def parse_info(text: str) -> dict:
    """Pivot an `_info.csv` file into one matches row."""
    info: dict = {}
    teams: list[str] = []
    for row in csv.reader(io.StringIO(text)):
        if len(row) < 3 or row[0] != "info":
            continue
        key, value = row[1], row[2]
        if key == "team":
            teams.append(value)
        elif key == "date":
            info.setdefault("date", value)  # first day of the match
        elif key not in ("player", "registry", "umpire", "players"):
            info.setdefault(key, value)
    date = info.get("date", "")
    winner = info.get("winner")
    if winner:
        result = "win"
    elif info.get("outcome") == "tie" or info.get("eliminator"):
        result = "tie"
        winner = info.get("eliminator")
    else:
        result = info.get("outcome", "no result")
    return {
        "season": info.get("season"),
        "season_year": int(date[:4]) if date[:4].isdigit() else _int(str(info.get("season", ""))[:4]),
        "date": date,
        "venue": info.get("venue"),
        "city": info.get("city"),
        "team1": teams[0] if teams else None,
        "team2": teams[1] if len(teams) > 1 else None,
        "toss_winner": info.get("toss_winner"),
        "toss_decision": info.get("toss_decision"),
        "winner": winner,
        "win_by_runs": _int(info.get("winner_runs")),
        "win_by_wickets": _int(info.get("winner_wickets")),
        "result": result,
        "player_of_match": info.get("player_of_match"),
    }


def parse_balls(text: str, match_id: int, season_year: int) -> list[tuple]:
    rows = []
    for r in csv.DictReader(io.StringIO(text)):
        over_str, _, ball_str = r["ball"].partition(".")
        rows.append((
            match_id, season_year, _int(r["innings"]), _int(over_str), _int(ball_str),
            r["batting_team"], r["bowling_team"], r["striker"], r["non_striker"], r["bowler"],
            _int(r["runs_off_bat"]), _int(r["extras"]), _int(r.get("wides")), _int(r.get("noballs")),
            _int(r.get("byes")), _int(r.get("legbyes")),
            r.get("wicket_type") or None, r.get("player_dismissed") or None,
        ))
    return rows


def load(zip_bytes: bytes, out: Path) -> tuple[int, int]:
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    conn = sqlite3.connect(tmp)
    conn.executescript(SCHEMA)

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        info_files = {Path(n).name[: -len("_info.csv")]: n for n in names if n.endswith("_info.csv")}
        ball_files = {Path(n).stem: n for n in names if n.endswith(".csv") and not n.endswith("_info.csv")}
        matches = 0
        balls = 0
        for mid in sorted(set(info_files) & set(ball_files), key=lambda s: int(s) if s.isdigit() else 0):
            if not mid.isdigit():
                continue
            m = parse_info(zf.read(info_files[mid]).decode("utf-8"))
            conn.execute(
                "INSERT INTO matches VALUES (:match_id, :season, :season_year, :date, :venue, :city, :team1, :team2,"
                " :toss_winner, :toss_decision, :winner, :win_by_runs, :win_by_wickets, :result, :player_of_match)",
                {"match_id": int(mid), **m},
            )
            rows = parse_balls(zf.read(ball_files[mid]).decode("utf-8"), int(mid), m["season_year"])
            conn.executemany(f"INSERT INTO deliveries VALUES ({', '.join('?' * 18)})", rows)
            matches += 1
            balls += len(rows)

    conn.commit()
    conn.execute("ANALYZE")
    conn.close()
    tmp.replace(out)
    return matches, balls


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=Path("data/ipl.db"))
    parser.add_argument("--zip", type=Path, help="Use a local copy of ipl_csv2.zip instead of downloading.")
    args = parser.parse_args()

    if args.zip:
        data = args.zip.read_bytes()
    else:
        print(f"Downloading {URL} ...", flush=True)
        req = urllib.request.Request(URL, headers={"User-Agent": "FanDesk-Demo/1.0 (IPL loader)"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
    matches, balls = load(data, args.out)

    conn = sqlite3.connect(args.out)
    lo, hi = conn.execute("SELECT MIN(season_year), MAX(season_year) FROM matches").fetchone()
    conn.close()
    print(f"Wrote {args.out}: {matches:,} matches, {balls:,} deliveries, seasons {lo}–{hi}.")
    return 0 if matches else 1


if __name__ == "__main__":
    sys.exit(main())
