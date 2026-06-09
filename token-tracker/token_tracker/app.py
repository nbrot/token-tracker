import json
import rumps
from datetime import date, timedelta
from pathlib import Path

from token_tracker.log_parser import parse_usage, total_tokens
from token_tracker.pricing import cost_usd, format_cost, format_tokens

REFRESH_INTERVAL = 120
BAR_WIDTH = 22
CONFIG_FILE = Path.home() / ".claude" / "token_tracker_config.json"
DEFAULT_BUDGET = 75.0

_MONTHS_FR = [
    "", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]


# ── config ─────────────────────────────────────────────────────────────────────

def _load_budget() -> float:
    try:
        if CONFIG_FILE.exists():
            return float(json.loads(CONFIG_FILE.read_text()).get("monthly_budget", DEFAULT_BUDGET))
    except (json.JSONDecodeError, ValueError, IOError):
        pass
    return DEFAULT_BUDGET


def _save_budget(amount: float) -> None:
    try:
        CONFIG_FILE.write_text(json.dumps({"monthly_budget": amount}))
    except IOError:
        pass


# ── visuals ────────────────────────────────────────────────────────────────────

def _bar(pct: float) -> str:
    """
    Bounded progress bar with urgency edge marker.

    The right edge of the filled region uses a thin-to-thick block character
    that grows visually as spending approaches the limit — so urgency is
    readable without colour.

      calm   ( <60%) : ▏  thin line     [████████▏░░░░░░░░░░░░░░]
      moderate(60–80%): ▎  slight edge  [████████████████▎░░░░░░]
      warning (≥80%) : ▍  thick edge   [████████████████████▍░░]
      over   (100%)  : no edge marker  [██████████████████████]
    """
    pct = max(0.0, min(1.0, pct))
    filled = round(pct * BAR_WIDTH)
    empty  = BAR_WIDTH - filled

    if filled == 0:
        return "░" * BAR_WIDTH
    if empty == 0:
        return "█" * BAR_WIDTH

    edge = "▍" if pct >= 0.8 else ("▎" if pct >= 0.6 else "▏")
    return "█" * (filled - 1) + edge + "░" * empty


def _bar_line(pct: float) -> str:
    return f"  [{_bar(pct)}]"


def _header_line(month: str, pct: float) -> str:
    """
    Single header with the percentage tab-aligned to the right
    (NSMenuItem renders \\t as a right-alignment tab stop).
    """
    alert = "  ⛔" if pct >= 1.0 else ("  ⚠" if pct >= 0.8 else "")
    return f"  Budget · {month}\t{pct*100:.0f}%{alert}"


def _fmt_month(d: date) -> str:
    return f"{_MONTHS_FR[d.month]} {d.year}"


# ── app ────────────────────────────────────────────────────────────────────────

class TokenTrackerApp(rumps.App):
    def __init__(self):
        super().__init__("$…", quit_button="Quitter")
        self._budget = _load_budget()

        # Budget section — all disabled (visual only)
        self._budget_header = _disabled("Budget — …")
        self._budget_bar    = _disabled("…")
        self._budget_detail = _disabled("…")

        # Stats
        self._today = rumps.MenuItem("Aujourd'hui      —")
        self._week  = rumps.MenuItem("Cette semaine    —")
        self._month = rumps.MenuItem("Ce mois          —")

        # Models submenu
        self._models_menu = rumps.MenuItem("Par modèle")
        self._models_menu["…"] = rumps.MenuItem("Chargement…")

        # Actions
        self._set_budget_btn = rumps.MenuItem("Définir budget…", callback=self._set_budget)
        self._refresh_btn    = rumps.MenuItem("Rafraîchir",       callback=self._refresh)

        self.menu = [
            self._budget_header,
            self._budget_bar,
            self._budget_detail,
            None,
            self._today,
            self._week,
            self._month,
            None,
            self._models_menu,
            None,
            self._set_budget_btn,
            self._refresh_btn,
        ]

        self._refresh(None)

    # ── refresh ────────────────────────────────────────────────────────────────

    @rumps.timer(REFRESH_INTERVAL)
    def _auto_refresh(self, _):
        self._refresh(None)

    def _refresh(self, _):
        today       = date.today()
        week_start  = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        today_usage = parse_usage(start_date=today,       end_date=today)
        week_usage  = parse_usage(start_date=week_start,  end_date=today)
        month_usage = parse_usage(start_date=month_start, end_date=today)

        today_cost = cost_usd(today_usage)
        week_cost  = cost_usd(week_usage)
        month_cost = cost_usd(month_usage)
        remaining  = max(0.0, self._budget - month_cost)
        pct        = month_cost / self._budget if self._budget > 0 else 0.0

        # ── Menu bar title ─────────────────────────────────────────────────────
        self.title = f"${today_cost:.2f}"

        # ── Budget section ─────────────────────────────────────────────────────
        self._budget_header.title = _header_line(_fmt_month(today), pct)
        self._budget_bar.title    = _bar_line(pct)
        self._budget_detail.title = (
            f"  ${month_cost:.2f} dépensé  ·  ${remaining:.2f} restants de ${self._budget:.0f}"
        )

        # ── Stats ──────────────────────────────────────────────────────────────
        self._today.title = f"Aujourd'hui      {format_cost(today_cost)}"
        self._week.title  = f"Cette semaine    {format_cost(week_cost)}"
        self._month.title = f"Ce mois          {format_cost(month_cost)}"

        # ── Models submenu ─────────────────────────────────────────────────────
        self._models_menu.clear()
        if today_usage:
            for model, u in sorted(today_usage.items()):
                short = _short_model(model)
                self._models_menu[short] = rumps.MenuItem(
                    f"{short}   {format_tokens(u.total)}"
                    f"  (in {format_tokens(u.input_tokens)}"
                    f" · out {format_tokens(u.output_tokens)})"
                )
        else:
            self._models_menu["—"] = rumps.MenuItem("Aucune donnée aujourd'hui")

    # ── set budget dialog ──────────────────────────────────────────────────────

    def _set_budget(self, _):
        w = rumps.Window(
            message="Budget mensuel Claude Code (USD)",
            title="Token Tracker",
            default_text=str(int(self._budget)),
            ok="Enregistrer",
            cancel="Annuler",
            dimensions=(200, 24),
        )
        response = w.run()
        if response.clicked:
            try:
                self._budget = max(1.0, float(response.text.strip()))
                _save_budget(self._budget)
                self._refresh(None)
            except ValueError:
                pass


# ── helpers ────────────────────────────────────────────────────────────────────

def _disabled(title: str) -> rumps.MenuItem:
    item = rumps.MenuItem(title)
    item.set_callback(None)
    return item


def _short_model(model: str) -> str:
    # "claude-sonnet-4-6" → "Sonnet 4.6"
    # "claude-haiku-4-5-20251001" → "Haiku 4.5"
    parts = model.replace("claude-", "").split("-")
    if len(parts) >= 3:
        return f"{parts[0].capitalize()} {parts[1]}.{parts[2]}"
    if len(parts) == 2:
        return f"{parts[0].capitalize()} {parts[1]}"
    return model
