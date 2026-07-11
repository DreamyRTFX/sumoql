"""
sumo_data.py — Common, reusable data logic for sumo builders.

# Contains:
# - Pure helper functions (rank parsing, form strings, H2H wins, basho math)
# - Data classes (BashoData, SanyakuData, StakesData, SummaryData)
# - Stats extraction (build_rikishi_stats)

No I/O, no formatting, no API calls.
"""

from datetime import datetime, timedelta, timezone, date


# ── Timezone setup ───────────────────────────────────────────────
JST = timezone(timedelta(hours=9))


# ── Honbasho reference data ───────────────────────────────────────

HONBASHO_DATA = {
    "01": ("January",   "⛄ Hatsu Basho",   "Tokyo",   "Ryōgoku Kokugikan", "https://upload.wikimedia.org/wikipedia/commons/d/d7/Ryogoku_Great_Sumo_Hall_%28cropped%29.jpg",    10092543),
    "03": ("March",     "🌸 Haru Basho",    "Osaka",   "Osaka Prefectural Gymnasium (Edion Arena Osaka)",   "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/EDION_Arena_Osaka.JPG/960px-EDION_Arena_Osaka.JPG",  16029119),
    "05": ("May",       "🌳 Natsu Basho",   "Tokyo",   "Ryōgoku Kokugikan", "https://upload.wikimedia.org/wikipedia/commons/d/d7/Ryogoku_Great_Sumo_Hall_%28cropped%29.jpg",    1286414),
    "07": ("July",      "🌞 Nagoya Basho",  "Nagoya",  "Aichi International Arena (IG Arena)",  "https://upload.wikimedia.org/wikipedia/commons/d/dd/NGO_Kita_Meijokoen_20250712_1446a.jpg",   16759040),
    "09": ("September", "🌻 Aki Basho",     "Tokyo",   "Ryōgoku Kokugikan", "https://upload.wikimedia.org/wikipedia/commons/d/d7/Ryogoku_Great_Sumo_Hall_%28cropped%29.jpg",  16759040),
    "11": ("November",  "🍂 Kyūshū Basho",  "Fukuoka", "Fukuoka Kokusai Center", "https://storage.googleapis.com/studio-design-asset-files/projects/YPqr7Q7ka5/s-2121x1402_v-frms_webp_b7d9b3e9-13d3-4eb4-bb2b-5cb19667d4ac_middle.webp", 13258768),
}


# ── Discord ANSI code reference ───────────────────────────────────
# Name → code maps for the sequences Discord's ```ansi code blocks support.
# This is the WHOLE supported set — no 256-color, no truecolor.
# Confirmed by eyeballing rendered output (see post_ansi_test.py).
#
# The trick lives in ESC: it MUST be the raw U+001B byte. You cannot type it;
# json.dumps encodes it as "" on the wire and Discord decodes it back.
# The block MUST be fenced ```ansi (a plain ``` renders the codes as text).

ESC = "\x1b"                 # the real ESC byte — the whole trick lives here
RESET = f"{ESC}[0m"

ANSI_STYLE = {"normal": 0, "bold": 1, "underline": 4}
ANSI_FG = {"gray": 30, "red": 31, "green": 32, "yellow": 33,
           "blue": 34, "pink": 35, "cyan": 36, "white": 37}
ANSI_BG = {"dark": 40, "orange": 41, "marble": 42, "gray": 43,
           "blue_gray": 44, "indigo": 45, "silver": 46, "white": 47}


def ansi(text, fg=None, bg=None, style=None) -> str:
    """Wrap text in a Discord-supported ANSI sequence. Codes combine as style;fg;bg."""
    codes = []
    if style is not None:
        codes.append(str(ANSI_STYLE[style]))
    if fg is not None:
        codes.append(str(ANSI_FG[fg]))
    if bg is not None:
        codes.append(str(ANSI_BG[bg]))
    if not codes:
        return text
    return f"{ESC}[{';'.join(codes)}m{text}{RESET}"


def ansi_block(body: str) -> str:
    """Wrap body in an ```ansi fenced code block for Discord."""
    return f"```ansi\n{body}\n```"


# ── Pure helper functions ─────────────────────────────────────────

def parse_short_rank(rank_str: str) -> dict:
    """Parse a full rank string like 'Yokozuna 1 East' into components.

    Returns dict with keys: initial, number, side, short
    'short' is a 4-char left-aligned string like 'Y1e ' or 'M14e'.
    """
    parts = rank_str.split()
    initial = parts[0][0].upper()
    number = int(parts[1]) if len(parts) >= 2 else 1
    side = parts[2][0].lower() if len(parts) >= 3 else ""
    short_raw = f"{initial}{number}{side}"
    short = f"{short_raw:<4}"
    return {
        "initial": initial,
        "number": number,
        "side": side,
        "short": short,
    }


def get_form_string(record: list) -> str:
    """Returns the form string (last up to 5 matches).
    Maps 'win' to '●' and everything else to '○'.
    """
    form_chars = []
    for r in record[-5:]:
        if r.get("result") in ("win", "fusen win"):
            form_chars.append("●")
        else:
            form_chars.append("○")
    return "".join(form_chars)


def get_h2h_wins(matches: list, rikishi_id: int) -> int:
    """Returns the number of H2H wins for the given rikishi."""
    return sum(1 for m in matches if m.get("winnerId") == rikishi_id)


def get_next_basho(basho_id: str) -> str:
    """Given a basho ID like '202511', return the next one ('202601').
    Handles the January -> November year wrap.
    """
    if basho_id[-2:] == "11":
        return str(int(basho_id) + 90)
    else:
        return str(int(basho_id) + 2)


def get_previous_basho(basho_id: str) -> str:
    """Given a basho ID like '202603', return the previous one ('202601').
    Handles the January -> November year wrap.
    """
    if basho_id[-2:] == "01":
        return str(int(basho_id) - 90)
    else:
        return str(int(basho_id) - 2)


def get_second_sunday(year: int, month: int) -> date:
    """Returns the date of the second Sunday of the given year and month."""
    # Start at the first day of the month
    first_day = date(year, month, 1)
    # find the first Sunday (weekday() is 6 for Sunday)
    first_sunday_offset = (6 - first_day.weekday()) % 7
    first_sunday = first_day + timedelta(days=first_sunday_offset)
    # The second Sunday is one week later
    return first_sunday + timedelta(weeks=1)


def get_current_basho_id() -> str:
    """Returns the YYYYMM string for the current or upcoming tournament.
    Sumo tournaments happen in months 1, 3, 5, 7, 9, 11.
    A tournament starts on the 2nd Sunday and lasts 15 days.
    """
    now_jst = datetime.now(JST)
    year = now_jst.year
    month = now_jst.month

    # Find the next odd month (tournament month)
    if month % 2 == 0:
        target_month = month + 1
        if target_month > 11:
            target_month = 1
            target_year = year + 1
        else:
            target_year = year
        return f"{target_year}{target_month:02d}"

    # If it's an odd month, check if the tournament is over
    start_date = get_second_sunday(year, month) 
    end_date = start_date + timedelta(days=14)  # Day 15 is 14 days after Day 1

    if now_jst.date() > end_date:
        # Tournament is over, look for the next one
        target_month = month + 2
        if target_month > 11:
            target_month = 1
            target_year = year + 1
        else:
            target_year = year
        return f"{target_year}{target_month:02d}"

    return f"{year}{month:02d}"


def get_current_day(start_date_iso: str) -> int:
    """Calculates the current tournament day (1-15) based on current JST time.
    If today is before start_date, returns 1.
    If today is after end of tournament (Day 15), returns 15.
    """
    now_jst = datetime.now(JST)
    start_dt = datetime.fromisoformat(start_date_iso.replace('Z', '+00:00')).astimezone(JST)

    # Tournament day is (current - start).days + 1
    # We strip time to compare dates only
    delta = (now_jst.date() - start_dt.date()).days
    day = delta + 1

    if day < 1:
        return 1
    if day > 15:
        return 15
    return day


def discord_ts(dt: datetime, style: str = "f") -> str:
    """Return a Discord timestamp tag: <t:UNIX:STYLE>.

    Discord renders these localized to each viewer, and the ``R`` style
    stays live ("in 2 days" -> "3 hours ago") without re-posting.

    Naive datetimes are assumed to be JST (the tournament's home timezone).

    Styles: t (short time), T (long time), d (short date), D (long date),
    f (short date/time, default), F (long date/time), R (relative).

    Note: these tags only render in normal content/titles/fields, NOT
    inside code blocks.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=JST)
    return f"<t:{int(dt.timestamp())}:{style}>"


# ── Data classes ──────────────────────────────────────────────────

class BashoData:
    """Tournament metadata extracted from torikumi API response."""

    def __init__(self, basho_id, torikumi_data=None):
        self.year = basho_id[:4]
        self.month_code = basho_id[-2:]
        (self.month_name_full, self.name, self.city,
         self.venue_name, self.venue_img, self.color) = HONBASHO_DATA[self.month_code]

        start_date = get_second_sunday(int(self.year), int(self.month_code)) 
        end_date = start_date + timedelta(days=14)
        if torikumi_data != None:
            if torikumi_data.get("date") != '':
                start_date = datetime.fromisoformat(torikumi_data.get("startDate").replace('Z', '+00:00')).astimezone(JST)
                end_date = datetime.fromisoformat(torikumi_data.get("endDate").replace('Z', '+00:00')).astimezone(JST)


        self.start_date_str = start_date.strftime('%b %d')
        self.end_date_str = end_date.strftime('%d, %Y')
        self.daily_start_time = "8PM EST • 12AM UTC • 9AM JST"

        # tz-aware datetime for the Day 1 opening bell (00:00 UTC / 09:00 JST),
        # for building live Discord <t:...> timestamps. start_date may be a
        # date (calendar fallback) or a datetime (from torikumi).
        self.start_dt = self._opening_bell(start_date)

    @staticmethod
    def _opening_bell(start_date) -> datetime:
        if isinstance(start_date, datetime):
            return start_date
        return datetime(start_date.year, start_date.month, start_date.day,
                        tzinfo=timezone.utc).astimezone(JST)


class SanyakuData:
    """San'yaku wrestlers categorized and sorted from banzuke data."""

    def __init__(self, banzuke_data):
        self.yokozuna = []
        self.ozeki = []
        self.sekiwake = []
        self.komusubi = []

        for side in ["east", "west"]:
            for rikishi in banzuke_data.get(side, []):
                rank = rikishi.get("rank", "")
                r_obj = {
                    "name": rikishi.get("shikonaEn"),
                    "rank": rank.split(" ")[0],
                    "number": int(rank.split(" ")[1]) if len(rank.split(" ")) > 1 else 1,
                    "side": side.capitalize(),
                    "id": rikishi.get("rikishiID"),
                }

                if "Yokozuna" in rank:
                    self.yokozuna.append(r_obj)
                elif "Ozeki" in rank:
                    self.ozeki.append(r_obj)
                elif "Sekiwake" in rank:
                    self.sekiwake.append(r_obj)
                elif "Komusubi" in rank:
                    self.komusubi.append(r_obj)

        self.yokozuna.sort(key=lambda x: x["number"])
        self.ozeki.sort(key=lambda x: x["number"])
        self.sekiwake.sort(key=lambda x: x["number"])
        self.komusubi.sort(key=lambda x: x["number"])


class StakesData:
    """Tournament stakes: defending champ, kadoban, kyujo."""

    def __init__(self, banzuke_data, torikumi_data, prior_torikumi, prior_banzuke):
        self.defending_champ = "(Unknown)"
        self.kadoban = []
        self.kyujo = []

        # Defending Champ
        if prior_torikumi:
            for yusho in prior_torikumi.get("yusho", []):
                if yusho.get("type", "") == "Makuuchi":
                    self.defending_champ = yusho.get("shikonaEn", "(Unknown)")
                    break

        # Kadoban: Ozeki from prior basho with < 8 wins who are still Ozeki
        prior_ozeki_losses = {}
        if prior_banzuke:
            for side in ["east", "west"]:
                for r in prior_banzuke.get(side, []):
                    if "Ozeki" in r.get("rank", ""):
                        if r.get("wins", 0) < 8:
                            prior_ozeki_losses[r.get("rikishiID")] = r.get("shikonaEn")

        for side in ["east", "west"]:
            for r in banzuke_data.get(side, []):
                if "Ozeki" in r.get("rank", "") and r.get("rikishiID") in prior_ozeki_losses:
                    self.kadoban.append(r.get("shikonaEn"))

        # Kyujo: Makuuchi rikishi absent from Day 1 torikumi
        maeg_ids = set()
        for side in ["east", "west"]:
            for r in banzuke_data.get(side, []):
                maeg_ids.add(r.get("rikishiID"))

        day1_participants = set()
        for match in torikumi_data.get("torikumi", []):
            day1_participants.add(match.get("eastId"))
            day1_participants.add(match.get("westId"))

        for side in ["east", "west"]:
            for r in banzuke_data.get(side, []):
                rid = r.get("rikishiID")
                if rid in maeg_ids and rid not in day1_participants:
                    self.kyujo.append(r.get("shikonaEn"))


class SummaryData:
    """Tournament summary data from prior torikumi (Day 15): yusho and special prizes."""

    def __init__(self, prior_torikumi_data):
        self.yusho = prior_torikumi_data.get("yusho", [])
        self.special_prizes = prior_torikumi_data.get("specialPrizes", [])


# ── Stats extraction ─────────────────────────────────────────────

def build_rikishi_stats(banzuke_data: dict, day: int) -> dict:
    """Build a dict of {rikishi_id: stats} from banzuke data up to the given day.

    Stats include: rank, shikona, wins, losses, form.
    """
    rikishi_stats = {}
    for side in ["east", "west"]:
        for rikishi in banzuke_data.get(side, []):
            rid = rikishi.get("rikishiID")
            record = rikishi.get("record", [])
            past_record = record[:day - 1]

            wins = sum(1 for r in past_record if r.get("result") in ("win", "fusen win"))
            losses = sum(1 for r in past_record if r.get("result") in ("loss", "absent", "fusen loss"))

            form = get_form_string(past_record)

            rikishi_stats[rid] = {
                "rank": rikishi.get("rank"),
                "shikona": rikishi.get("shikonaEn"),
                "wins": wins,
                "losses": losses,
                "form": form,
            }
    return rikishi_stats
