import pytest
from sumo_data import (
    parse_short_rank,
    get_form_string,
    get_h2h_wins,
    get_previous_basho,
    build_rikishi_stats,
    BashoData,
    SanyakuData,
    StakesData,
)

# ── parse_short_rank ──────────────────────────────────────────────

class TestParseShortRank:
    def test_yokozuna(self):
        result = parse_short_rank("Yokozuna 1 East")
        assert result["initial"] == "Y"
        assert result["number"] == 1
        assert result["side"] == "e"
        assert result["short"] == "Y1e "

    def test_ozeki(self):
        result = parse_short_rank("Ozeki 2 West")
        assert result["initial"] == "O"
        assert result["number"] == 2
        assert result["side"] == "w"
        assert result["short"] == "O2w "

    def test_sekiwake(self):
        result = parse_short_rank("Sekiwake 1 East")
        assert result["short"] == "S1e "

    def test_komusubi(self):
        result = parse_short_rank("Komusubi 1 West")
        assert result["short"] == "K1w "

    def test_maegashira(self):
        result = parse_short_rank("Maegashira 14 East")
        assert result["initial"] == "M"
        assert result["number"] == 14
        assert result["short"] == "M14e"

    def test_maegashira_single_digit(self):
        result = parse_short_rank("Maegashira 3 West")
        assert result["short"] == "M3w "

    def test_short_rank_is_left_padded_to_4(self):
        """All short ranks should be exactly 4 characters, left-aligned."""
        for rank_str in ["Yokozuna 1 East", "Maegashira 3 West", "Maegashira 14 East"]:
            result = parse_short_rank(rank_str)
            assert len(result["short"]) == 4


# ── get_form_string ───────────────────────────────────────────────

class TestGetFormString:
    def test_basic(self):
        record = [
            {"result": "loss"},
            {"result": "loss"},
            {"result": "win"},
            {"result": "loss"},
            {"result": "loss"},
        ]
        assert get_form_string(record) == "○○●○○"

    def test_short_record(self):
        record = [{"result": "win"}, {"result": "loss"}]
        assert get_form_string(record) == "●○"

    def test_takes_last_5_only(self):
        record = [
            {"result": "loss"}, {"result": "loss"}, {"result": "loss"},
            {"result": "win"}, {"result": "loss"}, {"result": "win"},
            {"result": "loss"}, {"result": "win"}, {"result": "win"},
        ]
        assert get_form_string(record) == "○●○●●"

    def test_empty_record(self):
        assert get_form_string([]) == ""

    def test_all_wins(self):
        record = [{"result": "win"}] * 7
        assert get_form_string(record) == "●●●●●"

    def test_absent_counts_as_loss(self):
        record = [{"result": "absent"}]
        assert get_form_string(record) == "○"


# ── get_h2h_wins ─────────────────────────────────────────────────

class TestGetH2hWins:
    def test_basic(self):
        matches = [
            {"winnerId": 1},
            {"winnerId": 7},
            {"winnerId": 7},
            {"winnerId": 1},
            {"winnerId": 1},
        ]
        assert get_h2h_wins(matches, 1) == 3
        assert get_h2h_wins(matches, 7) == 2

    def test_empty_matches(self):
        assert get_h2h_wins([], 1) == 0

    def test_no_wins(self):
        matches = [{"winnerId": 99}, {"winnerId": 99}]
        assert get_h2h_wins(matches, 1) == 0


# ── get_previous_basho ───────────────────────────────────────────

class TestGetPreviousBasho:
    def test_normal(self):
        assert get_previous_basho("202603") == "202601"

    def test_january_wraps_to_prior_november(self):
        assert get_previous_basho("202601") == "202511"

    def test_may(self):
        assert get_previous_basho("202605") == "202603"

    def test_november(self):
        assert get_previous_basho("202611") == "202609"


# ── build_rikishi_stats ──────────────────────────────────────────

class TestBuildRikishiStats:
    def _make_banzuke(self, east=None, west=None):
        return {"east": east or [], "west": west or []}

    def test_basic_stats(self):
        banzuke = self._make_banzuke(east=[
            {
                "rikishiID": 42,
                "rank": "Ozeki 1 East",
                "shikonaEn": "Kotozakura",
                "record": [
                    {"result": "win"},
                    {"result": "win"},
                    {"result": "loss"},
                    {"result": "win"},
                ],
            }
        ])
        stats = build_rikishi_stats(banzuke, day=3)
        assert 42 in stats
        # Day 3 means we look at record[:2] (days 1 and 2)
        assert stats[42]["wins"] == 2
        assert stats[42]["losses"] == 0
        assert stats[42]["shikona"] == "Kotozakura"
        assert stats[42]["rank"] == "Ozeki 1 East"

    def test_day_1_has_no_record(self):
        banzuke = self._make_banzuke(east=[
            {
                "rikishiID": 1,
                "rank": "Yokozuna 1 East",
                "shikonaEn": "Terunofuji",
                "record": [{"result": "win"}],
            }
        ])
        stats = build_rikishi_stats(banzuke, day=1)
        assert stats[1]["wins"] == 0
        assert stats[1]["losses"] == 0
        assert stats[1]["form"] == ""

    def test_absent_counts_as_loss(self):
        banzuke = self._make_banzuke(west=[
            {
                "rikishiID": 5,
                "rank": "Maegashira 10 West",
                "shikonaEn": "SomeRikishi",
                "record": [
                    {"result": "absent"},
                    {"result": "fusen-loss"},
                ],
            }
        ])
        stats = build_rikishi_stats(banzuke, day=3)
        assert stats[5]["losses"] == 2
        assert stats[5]["wins"] == 0


# ── BashoData ─────────────────────────────────────────────────────

class TestBashoData:
    def test_march_basho(self):
        torikumi = {
            "date": "202603",
            "startDate": "2026-03-08T00:00:00Z",
            "endDate": "2026-03-22T00:00:00Z",
        }
        basho = BashoData(torikumi)
        assert basho.year == "2026"
        assert basho.month_code == "03"
        assert basho.name == "Haru Basho"
        assert basho.city == "Osaka"
        assert basho.start_date_str == "Mar 08"
        assert basho.end_date_str == "Mar 22, 2026"

    def test_january_prior_wraps_to_november(self):
        torikumi = {
            "date": "202601",
            "startDate": "2026-01-12T00:00:00Z",
            "endDate": "2026-01-26T00:00:00Z",
        }
        basho = BashoData(torikumi)
        assert basho.prior_year == "2025"
        assert "Nov" in basho.prior_basho_label


# ── SanyakuData ───────────────────────────────────────────────────

class TestSanyakuData:
    def test_categorizes_and_sorts(self):
        banzuke = {
            "east": [
                {"rank": "Yokozuna 1 East", "shikonaEn": "Terunofuji", "rikishiID": 1},
                {"rank": "Ozeki 1 East", "shikonaEn": "Kotozakura", "rikishiID": 2},
                {"rank": "Sekiwake 1 East", "shikonaEn": "Hoshoryu", "rikishiID": 3},
                {"rank": "Komusubi 1 East", "shikonaEn": "Wakatakakage", "rikishiID": 4},
            ],
            "west": [
                {"rank": "Ozeki 2 West", "shikonaEn": "Onosato", "rikishiID": 5},
                {"rank": "Komusubi 1 West", "shikonaEn": "Abi", "rikishiID": 6},
            ],
        }
        san = SanyakuData(banzuke)
        assert len(san.yokozuna) == 1
        assert san.yokozuna[0]["name"] == "Terunofuji"
        assert len(san.ozeki) == 2
        assert san.ozeki[0]["number"] == 1  # sorted
        assert san.ozeki[1]["number"] == 2
        assert len(san.sekiwake) == 1
        assert len(san.komusubi) == 2

    def test_empty_banzuke(self):
        san = SanyakuData({"east": [], "west": []})
        assert san.yokozuna == []
        assert san.ozeki == []


# ── StakesData ────────────────────────────────────────────────────

class TestStakesData:
    def test_defending_champ_from_prior(self):
        prior_torikumi = {
            "yusho": [
                {"type": "Makuuchi", "shikonaEn": "Onosato"},
                {"type": "Juryo", "shikonaEn": "SomeoneElse"},
            ]
        }
        stakes = StakesData(
            banzuke_data={"east": [], "west": []},
            torikumi_data={"torikumi": []},
            prior_torikumi=prior_torikumi,
            prior_banzuke=None,
        )
        assert stakes.defending_champ == "Onosato"

    def test_no_prior_data(self):
        stakes = StakesData(
            banzuke_data={"east": [], "west": []},
            torikumi_data={"torikumi": []},
            prior_torikumi=None,
            prior_banzuke=None,
        )
        assert stakes.defending_champ == "(Unknown)"

    def test_kadoban_detection(self):
        prior_banzuke = {
            "east": [
                {"rank": "Ozeki 1 East", "rikishiID": 10, "shikonaEn": "KadobanGuy", "wins": 6},
            ],
            "west": [],
        }
        current_banzuke = {
            "east": [
                {"rank": "Ozeki 1 East", "rikishiID": 10, "shikonaEn": "KadobanGuy"},
            ],
            "west": [],
        }
        stakes = StakesData(
            banzuke_data=current_banzuke,
            torikumi_data={"torikumi": []},
            prior_torikumi=None,
            prior_banzuke=prior_banzuke,
        )
        assert "KadobanGuy" in stakes.kadoban

    def test_kyujo_detection(self):
        banzuke = {
            "east": [
                {"rank": "Yokozuna 1 East", "rikishiID": 1, "shikonaEn": "AbsentGuy"},
            ],
            "west": [],
        }
        torikumi = {
            "torikumi": [
                {"eastId": 99, "westId": 88},  # rikishi 1 is NOT in day 1 matches
            ]
        }
        stakes = StakesData(
            banzuke_data=banzuke,
            torikumi_data=torikumi,
            prior_torikumi=None,
            prior_banzuke=None,
        )
        assert "AbsentGuy" in stakes.kyujo
