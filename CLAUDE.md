# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

SumoQL queries [sumo-api.com](https://www.sumo-api.com) and posts formatted Discord webhook embeds about Grand Sumo Tournaments (honbasho): a pre-tournament **briefing**, a **daily match card**, and a post-tournament **summary**.

## Commands

Activate the venv before running anything (PowerShell): `.venv\Scripts\activate`

- Run all tests: `pytest`
- Run one test file: `pytest test_sumo_data.py`
- Run one test: `pytest test_sumo_data.py::TestParseShortRank::test_yokozuna`
- Build & post the pre-tournament briefing: `python build_briefing.py` (posts to `testpoint` from `.env`; target basho is hard-coded in `__main__`)
- Build & post the daily match card: `python build_new_matches.py` (auto-discovers current basho and day via `get_current_basho_id` / `get_current_day`)
- Build the tournament summary (dry-run by default): `python build_summary.py` — add `--post` to actually send

`.env` provides two comma-separated webhook URL lists: `endpoints` (live) and `testpoint` (testing). Please don't post to endpoints by default.

## Architecture

The code is intentionally split between **pure logic** and **I/O**:

- [sumo_data.py](sumo_data.py) — Pure data layer. No network, no formatting, no side effects. Owns `HONBASHO_DATA` (the per-month tournament reference table: name, city, venue, image URL, embed color), helper functions (`parse_short_rank`, `get_form_string`, `get_h2h_wins`, `get_previous_basho`, `get_current_basho_id`, `get_current_day`), and the data classes that summarize an API response into a builder-friendly shape: `BashoData`, `SanyakuData`, `StakesData`, `SummaryData`, plus `build_rikishi_stats`.
- [sumo_hooks.py](sumo_hooks.py) — I/O layer. `SumoAPIClient` wraps the three sumo-api endpoints used (`torikumi`, `banzuke`, `h2h`), and `post_webhook` POSTs payloads to Discord.
- `build_*.py` — Three builders, one per Discord post. Each one fetches via `SumoAPIClient`, hands data to the `*Data` classes from `sumo_data`, formats a Discord embed payload, and posts via `post_webhook`. Keep builder-specific formatting (e.g. `_pair_up`, `_format_row`, `format_match_line`) inside the builder; promote anything reusable into `sumo_data.py`.

When adding a new post type, follow the same split: extend `sumo_data.py` with any new pure data class/helper, and create a new `build_*.py` that owns only the embed structure and orchestration.

### Domain conventions worth knowing

- **Basho IDs** are `YYYYMM` strings with `MM` in `{01, 03, 05, 07, 09, 11}` (the six honbasho months). `get_previous_basho("202601") == "202511"` — the January→prior-November wrap is real and tested; preserve it in any new date math.
- **Tournament timing**: a basho starts on the **2nd Sunday** of its month and runs 15 days. `get_current_basho_id` uses JST (`Asia/Tokyo`, UTC+9) to decide whether the current odd month's tournament is still live or whether we should target the next one.
- **Ranks** parse from strings like `"Maegashira 14 East"` into a 4-char short form like `"M14e"` used by the table layouts. New rank-aware code should go through `parse_short_rank` rather than re-splitting the string.
- **Form / win-loss counts**: `"win"` and `"fusen win"` (forfeit win) count as wins; `"loss"`, `"absent"`, and `"fusen loss"` count as losses. The form string is the last 5 entries rendered as `●`/`○`.
- **Kadoban / kyujo** detection in `StakesData` requires *both* the current and prior basho's banzuke + day-1 torikumi — don't drop the prior fetches when refactoring.

### Gotchas

- **Raw JSON files** -- do not injest large json files directly. Probe for structure first.

### Open work

- **add retirees section to new tournament announcement**
- **standardize and rebuild message format**: bring summary, new matches and briefing up to new format
- **Stats and projections post basho**: use sql-injest project to generate a statistical oddities summary for the last basho and future Makuuchi projections. Can also include `https://www3.nhk.or.jp/nhkworld/en/tv/sumo/highlights/#id` when it becomes available.
- **Next basho teaser**: similar to briefing but during the off season -- provides a reminder of time until next basho with some fun content
    - Photos, highlight videos, trivia, stats...
- **Daily results and summaries**: Recap can link to eg. `https://www3.nhk.or.jp/nhkworld/en/tv/sumo/tournament/202605/day15.html`. Results under spoiler.
- <t:epoch:R> timestamps — your hardcoded 8PM EST is wrong for anyone outside EST. Discord renders <t:1752278400:R> as a live "in 3 hours" localized per viewer. Perfect for the briefing ("begins in 24 hours") and daily card. -- daily/summary
- **```ansi code blocks** — Discord supports ANSI color codes in code blocks. -- works, adds ~15 characters per block
- kachi koshi indicator. kinboshi indicator -- summary
- Banzuke movement: diff current vs prior banzuke (you fetch both already!) — biggest climbers/fallers, shin-nyūmaku debutants, returnees from Juryo. -- briefing
- Ozeki promotion watch: sekiwake carrying 20+ wins over the last two basho — "needs 13 for promotion" is the pre-tournament storyline when it's live. -- briefing