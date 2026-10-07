import io
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import load_ipl  # noqa: E402

BALL_HEADER = (
    "match_id,season,start_date,venue,innings,ball,batting_team,bowling_team,striker,non_striker,bowler,"
    "runs_off_bat,extras,wides,noballs,byes,legbyes,penalty,wicket_type,player_dismissed,other_wicket_type,"
    "other_player_dismissed"
)


def _info(season: str, date: str, team1: str, team2: str, winner: str) -> str:
    return "\n".join([
        "version,2.2.0",
        "info,team," + team1,
        "info,team," + team2,
        "info,gender,male",
        "info,season," + season,
        "info,date," + date,
        "info,venue,Test Ground",
        "info,city,Chennai",
        "info,toss_winner," + team1,
        "info,toss_decision,bat",
        "info,player_of_match,A Batter",
        "info,winner," + winner,
        "info,winner_runs,5",
        "info,player," + team1 + ",A Batter",
        "info,registry,people,A Batter,abc123",
    ])


def _balls(mid: int, season: str, date: str, bat: str, bowl: str) -> str:
    rows = [
        # ball, striker, bowler, runs_off_bat, extras, wides, noballs, wicket_type, player_dismissed
        ("0.1", "A Batter", "Z Bowler", 4, 0, "", "", "", ""),
        ("0.2", "A Batter", "Z Bowler", 6, 0, "", "", "", ""),
        ("0.3", "A Batter", "Z Bowler", 0, 1, "1", "", "", ""),
        ("0.4", "A Batter", "Z Bowler", 0, 0, "", "", "caught", "A Batter"),
        ("0.5", "B Batter", "Z Bowler", 1, 0, "", "", "run out", "C Batter"),
    ]
    lines = [BALL_HEADER]
    for ball, striker, bowler, runs, extras, wides, noballs, wtype, dismissed in rows:
        lines.append(
            f"{mid},{season},{date},Test Ground,1,{ball},{bat},{bowl},{striker},X Partner,{bowler},"
            f"{runs},{extras},{wides},{noballs},,,,{wtype},{dismissed},,"
        )
    return "\n".join(lines)


def make_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        matches = [
            (1001, "2007/08", "2008-04-18", "Chennai Super Kings", "Mumbai Indians"),
            (1002, "2020/21", "2020-09-19", "Chennai Super Kings", "Mumbai Indians"),
            (1003, "2023", "2023-04-01", "Gujarat Titans", "Chennai Super Kings"),
        ]
        for mid, season, date, t1, t2 in matches:
            zf.writestr(f"{mid}_info.csv", _info(season, date, t1, t2, t1))
            zf.writestr(f"{mid}.csv", _balls(mid, season, date, t1, t2))
        zf.writestr("README.txt", "not a match")
    return buf.getvalue()


@pytest.fixture(scope="session")
def ipl_db(tmp_path_factory) -> Path:
    path = tmp_path_factory.mktemp("data") / "ipl.db"
    load_ipl.load(make_zip(), path)
    return path


from test_orchestrator import FakeWiki, setup  # noqa: E402,F401  (shared fixture)
