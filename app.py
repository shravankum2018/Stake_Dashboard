import streamlit as st
import pandas as pd
import os
import json
from datetime import date, datetime, timedelta
from utils.data_manager import DataManager
from utils.sounds import play_sound

# ── Page configuration ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Baccarat Tracker",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Constants ────────────────────────────────────────────────────────────────
CURRENT_SESSION_FILE = "current_session.json"
DAILY_STATS_FILE     = "daily_stats.json"
HISTORY_CSV_FILE     = "stake_history.csv"
SESSION_TIMES_FILE   = "session_times.json"   # NEW: tracks session start/end timestamps

SESSION_GAP_HOURS    = 6                       # Minimum hours between sessions

CHIP_DEFS = sorted([
    {"label": "₹10",   "coin": 10},
    {"label": "₹20",   "coin": 20},
    {"label": "₹40",   "coin": 40},
    {"label": "₹60",   "coin": 60},
    {"label": "₹80",   "coin": 80},
    {"label": "₹100",  "coin": 100},
    {"label": "₹120",  "coin": 120},
    {"label": "₹140",  "coin": 140},
    {"label": "₹160",  "coin": 160},
    {"label": "₹180",  "coin": 180},
    {"label": "₹200",  "coin": 200},
    {"label": "₹400",  "coin": 400},
    {"label": "₹500",  "coin": 500},
    {"label": "₹800",  "coin": 800},
    {"label": "₹1000", "coin": 1_000},
], key=lambda x: x["coin"])

CHIP_COLORS = [
    "#6366f1","#8b5cf6","#a855f7","#ec4899","#f43f5e",
    "#ef4444","#f97316","#f59e0b","#eab308","#84cc16",
    "#22c55e","#10b981","#14b8a6","#06b6d4","#3b82f6",
]

# ── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Exo+2:wght@300;400;700&display=swap');

html, body, [class*="css"] { font-family: 'Exo 2', sans-serif; }
.block-container { padding-top: 0.8rem !important; }

.card {
    background: linear-gradient(135deg, #0f0f1a, #1a1a2e);
    border-radius: 14px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.6rem;
}

button[kind="secondary"] {
    border-radius: 50px !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px !important;
}

@keyframes pulse-border {
    0%   { box-shadow: 0 0 0 0 rgba(102,126,234,0.5); }
    70%  { box-shadow: 0 0 0 8px rgba(102,126,234,0); }
    100% { box-shadow: 0 0 0 0 rgba(102,126,234,0); }
}
.pulse { animation: pulse-border 2s infinite; }

@keyframes countdown-pulse {
    0%   { box-shadow: 0 0 0 0 rgba(245,158,11,0.4); }
    70%  { box-shadow: 0 0 0 12px rgba(245,158,11,0); }
    100% { box-shadow: 0 0 0 0 rgba(245,158,11,0); }
}
.countdown-pulse { animation: countdown-pulse 2s infinite; }

div[data-testid="stHorizontalBlock"] > div:nth-child(1) button:not(:disabled) {
    background: linear-gradient(135deg, #dc2626, #991b1b) !important;
    border: 2px solid #ef4444 !important;
    color: white !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(2) button:not(:disabled) {
    background: linear-gradient(135deg, #2563eb, #1e40af) !important;
    border: 2px solid #60a5fa !important;
    color: white !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(3) button:not(:disabled) {
    background: linear-gradient(135deg, #374151, #111827) !important;
    border: 2px solid #6b7280 !important;
    color: white !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
}

.stButton > button:hover:not(:disabled) {
    transform: translateY(-2px) !important;
    filter: brightness(1.15) !important;
    transition: all 0.15s ease !important;
}
.stButton > button:active:not(:disabled) { transform: translateY(0px) !important; }
</style>
""", unsafe_allow_html=True)

# ── Initialize DataManager ───────────────────────────────────────────────────
data_manager = DataManager(HISTORY_CSV_FILE)


# ════════════════════════════════════════════════════════════════════════════
# SESSION TIMING HELPERS  (NEW)
# ════════════════════════════════════════════════════════════════════════════

def _load_session_times() -> dict:
    """Load session start/end timestamps from disk."""
    try:
        if os.path.exists(SESSION_TIMES_FILE):
            with open(SESSION_TIMES_FILE) as f:
                data = json.load(f)
            # Reset if it's from a previous day
            if data.get("date") == str(date.today()):
                return data
    except Exception:
        pass
    return {"date": str(date.today()), "session1_end": None, "session2_end": None}


def _save_session_times(times: dict):
    """Persist session timestamps to disk."""
    times["date"] = str(date.today())
    with open(SESSION_TIMES_FILE, "w") as f:
        json.dump(times, f, indent=2)


def _mark_session_end(session_num: int):
    """Record the end time of a completed session."""
    times = _load_session_times()
    times[f"session{session_num}_end"] = datetime.now().isoformat()
    _save_session_times(times)


def _seconds_until_session2_unlocks() -> int:
    """
    Returns how many seconds remain before session 2 can start.
    Returns 0 if it's already unlocked.
    """
    times = _load_session_times()
    s1_end_str = times.get("session1_end")
    if not s1_end_str:
        return 0  # No session 1 end recorded → don't block (edge case)
    try:
        s1_end = datetime.fromisoformat(s1_end_str)
        unlock_at = s1_end + timedelta(hours=SESSION_GAP_HOURS)
        remaining = (unlock_at - datetime.now()).total_seconds()
        return max(0, int(remaining))
    except Exception:
        return 0


def _format_countdown(seconds: int) -> str:
    """Format seconds into HH:MM:SS string."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def _session2_is_locked() -> bool:
    """True if session 2 cannot start yet (gap not elapsed)."""
    return _seconds_until_session2_unlocks() > 0


# ════════════════════════════════════════════════════════════════════════════
# FILE I/O HELPERS
# ════════════════════════════════════════════════════════════════════════════

def save_to_history_csv(session_data: dict):
    row = {
        "date":            session_data.get("date", str(date.today())),
        "start_bal":       session_data.get("start_bal", 0),
        "stop_pct":        session_data.get("stop_pct", 0),
        "target_pct":      session_data.get("target_pct", 0),
        "stop_amt":        session_data.get("stop_amt", 0),
        "target_amt":      session_data.get("target_amt", 0),
        "trades":          session_data.get("trades", 0),
        "banker_wins":     session_data.get("banker_wins", 0),
        "player_wins":     session_data.get("player_wins", 0),
        "losses":          session_data.get("losses", 0),
        "win_amt":         session_data.get("win_amt", 0),
        "loss_amt":        session_data.get("loss_amt", 0),
        "net":             session_data.get("net", 0),
        "result":          session_data.get("result", "incomplete"),
        "notes":           session_data.get("notes", ""),
        "session_number":  session_data.get("session_number", 1),
        "final_balance":   session_data.get("final_balance", 0),
    }
    if os.path.exists(HISTORY_CSV_FILE):
        df = pd.read_csv(HISTORY_CSV_FILE)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])
    df.to_csv(HISTORY_CSV_FILE, index=False)


def _session_snapshot() -> dict:
    ss = st.session_state
    return {
        "day_started":        ss.day_started,
        "balance":            ss.balance,
        "start_bal":          ss.start_bal,
        "stop_pct":           ss.stop_pct,
        "target_pct":         ss.target_pct,
        "stop_amt":           ss.stop_amt,
        "target_amt":         ss.target_amt,
        "bet":                ss.bet,
        "banker_wins":        ss.banker_wins,
        "player_wins":        ss.player_wins,
        "losses":             ss.losses,
        "win_amt":            ss.win_amt,
        "loss_amt":           ss.loss_amt,
        "trades":             ss.trades,
        "notes":              ss.notes,
        "last_action":        ss.last_action,
        "bet_history":        ss.get("bet_history", []),
        "current_session":    ss.current_session,
        "session1_completed": ss.session1_completed,
        "session2_completed": ss.session2_completed,
        "sessions_played":    ss.sessions_played,
        "session1_balance":   ss.session1_balance,
        "session1_pnl":       ss.session1_pnl,
        "session1_banker_wins": ss.get("session1_banker_wins", 0),
        "session1_player_wins": ss.get("session1_player_wins", 0),
        "session1_losses":      ss.get("session1_losses", 0),
        "session2_balance":   ss.session2_balance,
        "session2_pnl":       ss.session2_pnl,
        "session2_banker_wins": ss.get("session2_banker_wins", 0),
        "session2_player_wins": ss.get("session2_player_wins", 0),
        "session2_losses":      ss.get("session2_losses", 0),
        "trade_log":          ss.get("trade_log", []),
        "result":             "active",
        "date":               str(date.today()),
        "last_update":        datetime.now().isoformat(),
    }


def save_current_session():
    with open(CURRENT_SESSION_FILE, "w") as f:
        json.dump(_session_snapshot(), f, indent=2)


def load_current_session() -> dict | None:
    if not os.path.exists(CURRENT_SESSION_FILE):
        return None
    try:
        with open(CURRENT_SESSION_FILE) as f:
            data = json.load(f)
        if data.get("date") == str(date.today()):
            return data
        if data.get("day_started") or data.get("trades", 0) > 0:
            save_to_history_csv(data)
        os.remove(CURRENT_SESSION_FILE)
    except Exception:
        pass
    return None


def save_daily_stats():
    ss = st.session_state
    stats = {
        "date":               str(date.today()),
        "sessions_played":    ss.sessions_played,
        "session1_completed": ss.session1_completed,
        "session2_completed": ss.session2_completed,
        "session1_balance":   ss.session1_balance,
        "session1_pnl":       ss.session1_pnl,
        "session1_banker_wins": ss.get("session1_banker_wins", 0),
        "session1_player_wins": ss.get("session1_player_wins", 0),
        "session1_losses":      ss.get("session1_losses", 0),
        "session2_balance":   ss.session2_balance,
        "session2_pnl":       ss.session2_pnl,
        "session2_banker_wins": ss.get("session2_banker_wins", 0),
        "session2_player_wins": ss.get("session2_player_wins", 0),
        "session2_losses":      ss.get("session2_losses", 0),
        "total_trades":       ss.trades,
        "total_pnl":          ss.balance - ss.start_bal,
        "banker_wins":        ss.banker_wins,
        "player_wins":        ss.player_wins,
        "losses":             ss.losses,
        "last_update":        datetime.now().isoformat(),
    }
    with open(DAILY_STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)


def load_daily_stats() -> dict | None:
    if not os.path.exists(DAILY_STATS_FILE):
        return None
    try:
        with open(DAILY_STATS_FILE) as f:
            stats = json.load(f)
        if stats.get("date") == str(date.today()):
            return stats
    except Exception:
        pass
    return None


def _remove_files(*paths):
    for p in paths:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass


def _save_last_balance(bal: float):
    if bal > 0:
        with open("last_balance.json", "w") as f:
            json.dump({"last_session_balance": bal}, f)


def _load_last_balance() -> float:
    try:
        if os.path.exists("last_balance.json"):
            with open("last_balance.json") as f:
                return float(json.load(f).get("last_session_balance", 0.0))
    except Exception:
        pass
    return 0.0


def reset_session_data() -> bool:
    try:
        ss = st.session_state
        last_bal = 0.0
        if ss.get("session2_completed") and ss.get("session2_balance", 0) > 0:
            last_bal = float(ss.session2_balance)
        elif ss.get("session1_completed") and ss.get("session1_balance", 0) > 0:
            last_bal = float(ss.session1_balance)
        elif ss.get("balance", 0) > 0:
            last_bal = float(ss.balance)

        _save_last_balance(last_bal)
        _init_state(force=True)
        _remove_files(CURRENT_SESSION_FILE, DAILY_STATS_FILE, SESSION_TIMES_FILE)

        if last_bal > 0:
            st.session_state.last_session_balance = last_bal
        return True
    except Exception as e:
        st.error(f"Reset error: {e}")
        return False


def reset_for_new_day() -> bool:
    try:
        _init_state(force=True)
        _remove_files(CURRENT_SESSION_FILE, DAILY_STATS_FILE, HISTORY_CSV_FILE, SESSION_TIMES_FILE)
        return True
    except Exception as e:
        st.error(f"Reset error: {e}")
        return False


# ════════════════════════════════════════════════════════════════════════════
# STATE DEFAULTS & INITIALISATION
# ════════════════════════════════════════════════════════════════════════════

DEFS = dict(
    day_started=False,
    balance=1000.0,
    start_bal=1000.0,
    stop_pct=10,
    target_pct=15,
    stop_amt=100.0,
    target_amt=150.0,
    bet=0.0,
    banker_wins=0,
    player_wins=0,
    losses=0,
    win_amt=0.0,
    loss_amt=0.0,
    trades=0,
    last_action=None,
    bet_history=[],
    summary_shown=False,
    notes="",
    max_bet=1_000_000,
    saved=False,
    current_session=1,
    session1_completed=False,
    session2_completed=False,
    sessions_played=0,
    session1_balance=0.0,
    session1_pnl=0.0,
    session1_banker_wins=0,
    session1_player_wins=0,
    session1_losses=0,
    session2_balance=0.0,
    session2_pnl=0.0,
    session2_banker_wins=0,
    session2_player_wins=0,
    session2_losses=0,
    last_session_balance=0.0,
    trade_log=[],
)


def _init_state(force: bool = False):
    for k, v in DEFS.items():
        if force or k not in st.session_state:
            st.session_state[k] = v


# ── Bootstrap ────────────────────────────────────────────────────────────────
saved_session = load_current_session()
daily_stats   = load_daily_stats()

_last_bal_from_disk = _load_last_balance()
if _last_bal_from_disk > 0:
    DEFS["last_session_balance"] = _last_bal_from_disk

_bootstrap = dict(DEFS)

if daily_stats:
    for k in ("sessions_played", "session1_completed", "session2_completed",
              "session1_balance", "session1_pnl",
              "session1_banker_wins", "session1_player_wins", "session1_losses",
              "session2_balance", "session2_pnl",
              "session2_banker_wins", "session2_player_wins", "session2_losses",
              "banker_wins", "player_wins", "losses"):
        if k in daily_stats:
            _bootstrap[k] = daily_stats[k]

if saved_session:
    for k, v in saved_session.items():
        if k in _bootstrap:
            _bootstrap[k] = v

_init_state()

for k, v in _bootstrap.items():
    if k not in st.session_state:
        st.session_state[k] = v


def auto_save():
    if st.session_state.day_started:
        save_current_session()
        save_daily_stats()


# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🎮 CONTROL PANEL")
    st.markdown("---")
    st.markdown(f"**📅 Today:** {date.today().strftime('%B %d, %Y')}")

    # ── Session gap info ──────────────────────────────────────────────────
    times_data = _load_session_times()
    s1_end_str = times_data.get("session1_end")
    if s1_end_str:
        try:
            s1_end    = datetime.fromisoformat(s1_end_str)
            unlock_at = s1_end + timedelta(hours=SESSION_GAP_HOURS)
            st.markdown(
                f'<div style="background:#f59e0b15;border:1px solid #f59e0b55;'
                f'border-radius:8px;padding:0.4rem 0.6rem;font-size:0.72rem;color:#f59e0b;">'
                f'⏱ Session 1 ended: {s1_end.strftime("%H:%M")}<br>'
                f'🔓 Session 2 unlocks: {unlock_at.strftime("%H:%M")}'
                f'</div>',
                unsafe_allow_html=True,
            )
        except Exception:
            pass

    st.markdown("---")
    st.markdown("### 🔧 Reset Options")

    if "confirm_reset_session" not in st.session_state:
        st.session_state.confirm_reset_session = False
    if "confirm_full_reset" not in st.session_state:
        st.session_state.confirm_full_reset = False

    if not st.session_state.confirm_reset_session:
        if st.button("🔄 Reset Session", use_container_width=True):
            st.session_state.confirm_reset_session = True
            st.session_state.confirm_full_reset = False
            st.rerun()
    else:
        st.markdown(
            '<div style="background:#f59e0b15;border:1px solid #f59e0b;'
            'border-radius:8px;padding:0.4rem;text-align:center;'
            'font-size:0.78rem;color:#f59e0b;margin-bottom:0.4rem;">'
            '⚠️ Reset session?</div>',
            unsafe_allow_html=True,
        )
        y1, n1 = st.columns(2)
        with y1:
            if st.button("✅ Yes", key="yes_reset_session", use_container_width=True):
                st.session_state.confirm_reset_session = False
                if reset_session_data():
                    st.success("Session reset!")
                    st.rerun()
        with n1:
            if st.button("❌ No", key="no_reset_session", use_container_width=True):
                st.session_state.confirm_reset_session = False
                st.rerun()

    if not st.session_state.confirm_full_reset:
        if st.button("🗑️ Full Reset", use_container_width=True):
            st.session_state.confirm_full_reset = True
            st.session_state.confirm_reset_session = False
            st.rerun()
    else:
        st.markdown(
            '<div style="background:#ef444415;border:1px solid #ef4444;'
            'border-radius:8px;padding:0.4rem;text-align:center;'
            'font-size:0.78rem;color:#ef4444;margin-bottom:0.4rem;">'
            '🗑️ Wipe everything?</div>',
            unsafe_allow_html=True,
        )
        y2, n2 = st.columns(2)
        with y2:
            if st.button("✅ Yes", key="yes_full_reset", use_container_width=True):
                st.session_state.confirm_full_reset = False
                if reset_for_new_day():
                    st.success("Full reset done!")
                    st.rerun()
        with n2:
            if st.button("❌ No", key="no_full_reset", use_container_width=True):
                st.session_state.confirm_full_reset = False
                st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Today's Progress")

    ss = st.session_state

    def _session_status(n: int):
        completed = ss.get(f"session{n}_completed", False)
        balance   = ss.get(f"session{n}_balance",   0.0)
        pnl       = ss.get(f"session{n}_pnl",       0.0)
        active    = (ss.current_session == n and ss.day_started)

        if completed:
            st.success(f"✅ Session {n}: COMPLETED")
            if balance > 0:
                st.metric(
                    f"Session {n} Balance",
                    f"₹{balance:,.0f}",
                    delta=f"{'+' if pnl >= 0 else ''}₹{pnl:,.0f}",
                    delta_color="normal",
                )
        elif active:
            st.info(f"🟢 Session {n}: IN PROGRESS")
        elif n == 2 and ss.session1_completed:
            remaining = _seconds_until_session2_unlocks()
            if remaining > 0:
                st.warning(f"⏳ Session {n}: LOCKED ({_format_countdown(remaining)})")
            else:
                st.warning(f"⚪ Session {n}: READY")
        else:
            st.warning(f"⚪ Session {n}: NOT STARTED")

    _session_status(1)
    _session_status(2)

    st.markdown("---")
    if ss.day_started:
        st.markdown("### 📈 Current Session Stats")
        total_wins = ss.banker_wins + ss.player_wins
        win_rate   = (total_wins / ss.trades * 100) if ss.trades > 0 else 0
        st.metric("Total Trades", ss.trades)
        st.metric("Wins",         total_wins)
        st.metric("Losses",       ss.losses)
        st.metric("Win Rate",     f"{win_rate:.0f}%")

    st.markdown("---")
    st.markdown("### 📋 Session History")

    if os.path.exists(HISTORY_CSV_FILE):
        df_h = pd.read_csv(HISTORY_CSV_FILE)
        if not df_h.empty:
            if "show_history" not in st.session_state:
                st.session_state.show_history = False
            if st.button("📖 View Full History", use_container_width=True):
                st.session_state.show_history = not st.session_state.show_history

            if st.session_state.show_history:
                df_show = df_h.tail(20).iloc[::-1].reset_index(drop=True)
                for _, row in df_show.iterrows():
                    pnl       = float(row.get("net", 0))
                    start_bal = float(row.get("start_bal", 0))
                    final_bal = float(row.get("final_balance", 0))
                    wins      = int(row.get("banker_wins", 0)) + int(row.get("player_wins", 0))
                    losses    = int(row.get("losses", 0))
                    trades    = int(row.get("trades", 0))
                    wr        = round(wins / trades * 100) if trades > 0 else 0
                    sess_num  = int(row.get("session_number", 1))
                    r_date    = str(row.get("date", ""))
                    result    = str(row.get("result", ""))
                    pnl_color = "#10b981" if pnl >= 0 else "#ef4444"
                    pnl_sign  = "+" if pnl >= 0 else ""
                    res_icon  = "🎯" if result == "target" else ("🛑" if result == "stop_loss" else "📋")
                    st.markdown(f"""
<div style="background:linear-gradient(135deg,#0f0f1a,#1a1a2e);
            border:1px solid {pnl_color}55;border-radius:12px;
            padding:0.7rem 0.8rem;margin-bottom:0.5rem;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.4rem;">
    <span style="font-size:0.8rem;font-weight:700;color:#e5e7eb;">{res_icon} Session {sess_num}</span>
    <span style="font-size:0.72rem;color:#888;">{r_date}</span>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.3rem 0.6rem;">
    <div><div style="font-size:0.6rem;color:#666;">START</div>
         <div style="font-size:0.9rem;font-weight:700;color:#f59e0b;">₹{start_bal:,.0f}</div></div>
    <div><div style="font-size:0.6rem;color:#666;">FINAL</div>
         <div style="font-size:0.9rem;font-weight:700;color:{pnl_color};">₹{final_bal:,.0f}</div></div>
    <div><div style="font-size:0.6rem;color:#666;">P&amp;L</div>
         <div style="font-size:0.95rem;font-weight:800;color:{pnl_color};">{pnl_sign}₹{abs(pnl):,.0f}</div></div>
    <div><div style="font-size:0.6rem;color:#666;">WIN RATE</div>
         <div style="font-size:0.9rem;font-weight:700;color:#a78bfa;">{wr}%</div></div>
    <div><div style="font-size:0.6rem;color:#10b981;">✅ WINS</div>
         <div style="font-size:0.9rem;font-weight:700;color:#10b981;">{wins}</div></div>
    <div><div style="font-size:0.6rem;color:#ef4444;">❌ LOSSES</div>
         <div style="font-size:0.9rem;font-weight:700;color:#ef4444;">{losses}</div></div>
  </div>
</div>""", unsafe_allow_html=True)

            st.download_button(
                "⬇️ Download CSV",
                data=df_h.to_csv(index=False).encode(),
                file_name="stake_history.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.info("No history yet")
    else:
        st.info("No history yet")


# ════════════════════════════════════════════════════════════════════════════
# MAIN HEADER
# ════════════════════════════════════════════════════════════════════════════
st.markdown(
    '<h1 style="text-align:center;font-family:\'Rajdhani\',sans-serif;'
    'font-size:2.8rem;letter-spacing:4px;margin:0 0 0.4rem 0;">🎰 BACCARAT TRACKER</h1>',
    unsafe_allow_html=True,
)

ss = st.session_state


# ════════════════════════════════════════════════════════════════════════════
# BOTH SESSIONS COMPLETE – DAY SUMMARY SCREEN
# ════════════════════════════════════════════════════════════════════════════
if ss.session2_completed:
    st.markdown("""
        <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);
                    border:2px solid #10b981;border-radius:20px;
                    padding:1.5rem;text-align:center;margin:0.5rem 0;">
            <div style="font-size:1.8rem;margin-bottom:0.3rem;">🏆 DAY COMPLETE</div>
            <div style="font-size:0.9rem;color:#888;">Both sessions completed — great job!</div>
        </div>
    """, unsafe_allow_html=True)

    def _session_result_card(n: int):
        pnl     = ss.get(f"session{n}_pnl",       0.0)
        balance = ss.get(f"session{n}_balance",    0.0)
        bw      = ss.get(f"session{n}_banker_wins", 0)
        pw      = ss.get(f"session{n}_player_wins", 0)
        lw      = ss.get(f"session{n}_losses",      0)
        wins    = bw + pw
        start   = balance - pnl
        color   = "#10b981" if pnl >= 0 else "#ef4444"
        sign    = "+" if pnl >= 0 else ""
        st.markdown(f"""
            <div style="background:linear-gradient(135deg,#0f0f1a,#1a1a2e);
                        border:1px solid {color};border-radius:15px;
                        padding:1rem;margin:0.6rem 0;">
                <div style="font-size:1.1rem;font-weight:700;margin-bottom:0.5rem;">
                    📊 SESSION {n} RESULTS
                </div>
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.6rem;">
                    <div><div style="font-size:0.65rem;color:#888;">STARTING</div>
                         <div style="font-size:1.1rem;font-weight:700;color:#f59e0b;">₹{start:,.0f}</div></div>
                    <div><div style="font-size:0.65rem;color:#888;">FINAL</div>
                         <div style="font-size:1.1rem;font-weight:700;color:{color};">₹{balance:,.0f}</div></div>
                    <div><div style="font-size:0.65rem;color:#888;">P&L</div>
                         <div style="font-size:1.1rem;font-weight:700;color:{color};">{sign}₹{abs(pnl):,.0f}</div></div>
                    <div><div style="font-size:0.65rem;color:#10b981;">✅ WINS</div>
                         <div style="font-size:1rem;font-weight:700;color:#10b981;">{wins}</div></div>
                    <div><div style="font-size:0.65rem;color:#ef4444;">❌ LOSSES</div>
                         <div style="font-size:1rem;font-weight:700;color:#ef4444;">{lw}</div></div>
                    <div><div style="font-size:0.65rem;color:#aaa;">🎯 TRADES</div>
                         <div style="font-size:1rem;font-weight:700;color:#aaa;">{wins + lw}</div></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    _session_result_card(1)
    _session_result_card(2)

    total_pnl = ss.session1_pnl + ss.session2_pnl
    tc = "#10b981" if total_pnl >= 0 else "#ef4444"
    ts = "+" if total_pnl >= 0 else ""
    st.markdown(f"""
        <div style="background:{tc}10;border:2px solid {tc};border-radius:15px;
                    padding:1rem;margin:0.6rem 0;">
            <div style="font-size:1rem;font-weight:700;margin-bottom:0.4rem;">📈 TOTAL DAY SUMMARY</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;">
                <div><div style="font-size:0.65rem;color:#888;">TOTAL P&amp;L</div>
                     <div style="font-size:1.6rem;font-weight:700;color:{tc};">{ts}₹{abs(total_pnl):,.0f}</div></div>
                <div><div style="font-size:0.65rem;color:#888;">SESSIONS</div>
                     <div style="font-size:1.6rem;font-weight:700;">2 / 2</div></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.caption("Use 'Reset Session' in the sidebar to start fresh tomorrow.")
    if st.button("🔄 Start New Day", use_container_width=True):
        if reset_session_data():
            st.rerun()
    st.stop()


# ════════════════════════════════════════════════════════════════════════════
# SESSION SETUP SCREEN
# ════════════════════════════════════════════════════════════════════════════
if not ss.day_started:
    session_num = 2 if ss.session1_completed and not ss.session2_completed else 1

    # ── 6-Hour Gap Lockout Screen (session 2 only) ─────────────────────────
    if session_num == 2 and _session2_is_locked():
        remaining_secs = _seconds_until_session2_unlocks()
        times_data     = _load_session_times()
        s1_end_str     = times_data.get("session1_end", "")
        try:
            s1_end    = datetime.fromisoformat(s1_end_str)
            unlock_at = s1_end + timedelta(hours=SESSION_GAP_HOURS)
            unlock_str = unlock_at.strftime("%I:%M %p")
            ended_str  = s1_end.strftime("%I:%M %p")
        except Exception:
            unlock_str = "—"
            ended_str  = "—"

        h = remaining_secs // 3600
        m = (remaining_secs % 3600) // 60
        s_sec = remaining_secs % 60

        # Session 1 summary while waiting
        prev_pnl   = ss.session1_pnl
        prev_color = "#10b981" if prev_pnl >= 0 else "#ef4444"
        prev_sign  = "+" if prev_pnl >= 0 else ""

        st.markdown(f"""
            <div class="countdown-pulse"
                 style="background:linear-gradient(135deg,#1a0f00,#2d1a00);
                         border:2px solid #f59e0b;border-radius:20px;
                         padding:2rem;text-align:center;margin:1rem 0;">
                <div style="font-size:2rem;margin-bottom:0.5rem;">⏳ SESSION 2 LOCKED</div>
                <div style="font-size:0.9rem;color:#f59e0b80;margin-bottom:1.2rem;">
                    Minimum {SESSION_GAP_HOURS}-hour gap between sessions required
                </div>
                <div style="font-size:0.75rem;color:#888;margin-bottom:0.4rem;">TIME REMAINING</div>
                <div style="font-size:4rem;font-weight:900;color:#f59e0b;
                            font-family:'Rajdhani',monospace;letter-spacing:4px;line-height:1;">
                    {h:02d}:{m:02d}:{s_sec:02d}
                </div>
                <div style="font-size:0.8rem;color:#888;margin-top:1rem;">
                    Session 1 ended at <strong style="color:#f59e0b;">{ended_str}</strong>
                    &nbsp;·&nbsp;
                    Session 2 unlocks at <strong style="color:#10b981;">{unlock_str}</strong>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Show session 1 result while waiting
        st.markdown(f"""
            <div style="background:{prev_color}10;border:1px solid {prev_color};
                        border-radius:12px;padding:1rem;text-align:center;margin-bottom:1rem;">
                <div style="font-size:0.7rem;color:#888;letter-spacing:1px;">SESSION 1 RESULT</div>
                <div style="font-size:1.6rem;font-weight:800;color:{prev_color};margin-top:0.2rem;">
                    {prev_sign}₹{abs(prev_pnl):,.0f}
                </div>
                <div style="font-size:0.85rem;margin-top:0.2rem;">
                    Final Balance: <strong style="color:{prev_color};">₹{ss.session1_balance:,.0f}</strong>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Tip box
        st.markdown("""
            <div style="background:#ffffff08;border:1px solid #333;border-radius:10px;
                        padding:0.8rem;text-align:center;color:#888;font-size:0.82rem;">
                💡 <strong style="color:#e5e7eb;">Why the gap?</strong>
                Taking a break between sessions helps you stay disciplined,
                reset emotionally, and make clearer decisions in Session 2.
            </div>
        """, unsafe_allow_html=True)

        # Auto-refresh every 60 seconds so countdown stays live
        st.markdown("""
            <script>
                setTimeout(function() { window.location.reload(); }, 60000);
            </script>
        """, unsafe_allow_html=True)

        # Manual refresh button
        if st.button("🔄 Refresh Countdown", use_container_width=True):
            st.rerun()

        st.stop()

    # ── Normal session setup ───────────────────────────────────────────────
    if session_num == 2:
        default_start = float(ss.session1_balance) if ss.session1_balance > 0 else 1000.0
    else:
        carried = float(ss.get("last_session_balance", 0.0))
        if carried <= 0:
            carried = _load_last_balance()
        default_start = carried if carried > 0 else 1000.0

    accent = "#10b981" if session_num == 2 else "#667eea"

    st.markdown(f"""
        <div style="background:{accent}20;border:2px solid {accent};border-radius:12px;
                    padding:0.6rem;text-align:center;margin-bottom:0.8rem;">
            <strong style="color:{accent};font-size:1rem;">
                🎯 Session {session_num} of 2
            </strong>
            &nbsp;&nbsp;
            <span style="font-size:0.78rem;color:#888;">
                (Daily limit: 2 sessions · {SESSION_GAP_HOURS}h gap enforced)
            </span>
        </div>
    """, unsafe_allow_html=True)

    if session_num == 2:
        prev_pnl   = ss.session1_pnl
        prev_color = "#10b981" if prev_pnl >= 0 else "#ef4444"
        prev_sign  = "+" if prev_pnl >= 0 else ""
        # Show when session 1 ended
        times_data = _load_session_times()
        s1_end_str = times_data.get("session1_end", "")
        ended_label = ""
        if s1_end_str:
            try:
                ended_label = f" · Ended at {datetime.fromisoformat(s1_end_str).strftime('%I:%M %p')}"
            except Exception:
                pass

        st.markdown(f"""
            <div style="background:{prev_color}10;border:1px solid {prev_color};
                        border-radius:8px;padding:0.5rem;text-align:center;margin-bottom:0.8rem;">
                <div style="font-size:0.65rem;color:#888;">SESSION 1 RESULT{ended_label}</div>
                <div style="font-size:1rem;font-weight:700;color:{prev_color};">
                    {prev_sign}₹{abs(prev_pnl):,.0f}
                </div>
                <div style="font-size:0.7rem;">Final Balance: ₹{ss.session1_balance:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    with st.container():
        c1, c2, c3 = st.columns(3)
        with c1:
            start_bal = st.number_input(
                "💰 Starting Balance",
                min_value=100.0,
                value=float(default_start),
                step=500.0,
                format="%.0f",
            )
        with c2:
            stop_pct = st.number_input(
                "🛑 Stop Loss %", min_value=1, max_value=90, value=10, step=1
            )
        with c3:
            target_pct = st.number_input(
                "🎯 Target %", min_value=1, max_value=500, value=15, step=1
            )

    sl_amt = start_bal * stop_pct / 100
    tg_amt = start_bal * target_pct / 100

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f'<div class="card" style="border:1px solid #ef4444;text-align:center;">'
            f'<span style="color:#ef4444;font-size:1rem;">🔴 Stop Loss: -₹{sl_amt:,.0f}</span></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="card" style="border:1px solid #10b981;text-align:center;">'
            f'<span style="color:#10b981;font-size:1rem;">🟢 Target: +₹{tg_amt:,.0f}</span></div>',
            unsafe_allow_html=True,
        )

    if st.button("🚀 START SESSION", use_container_width=True, type="primary"):
        ss.update(dict(
            day_started=True,
            balance=start_bal,
            start_bal=start_bal,
            stop_pct=stop_pct,
            target_pct=target_pct,
            stop_amt=sl_amt,
            target_amt=tg_amt,
            summary_shown=False,
            banker_wins=0,
            player_wins=0,
            losses=0,
            win_amt=0.0,
            loss_amt=0.0,
            trades=0,
            bet=0.0,
            notes="",
            saved=False,
            current_session=session_num,
            bet_history=[],
            trade_log=[],
        ))
        auto_save()
        st.rerun()
    st.stop()


# ════════════════════════════════════════════════════════════════════════════
# ACTIVE SESSION DASHBOARD
# ════════════════════════════════════════════════════════════════════════════

net      = ss.balance - ss.start_bal
day_loss = abs(min(net, 0))
day_gain = max(net, 0)
sl_amt   = ss.stop_amt
tg_amt   = ss.target_amt

stop_hit   = sl_amt > 0 and day_loss >= sl_amt
target_hit = tg_amt > 0 and day_gain >= tg_amt
game_over  = stop_hit or target_hit

total_wins = ss.banker_wins + ss.player_wins
win_rate   = (total_wins / ss.trades * 100) if ss.trades > 0 else 0

if net >= 0:
    remaining_amount = max(0.0, tg_amt - day_gain)
    remaining_color  = "#10b981"
    status_text      = "🎯 Amount needed to reach Target"
else:
    remaining_amount = max(0.0, sl_amt - day_loss)
    remaining_color  = "#ef4444"
    status_text      = "🛑 Amount before Stop Loss"

balance_color = "#10b981" if net > 0 else ("#ef4444" if net < 0 else "#f59e0b")

# ── Handle session completion ────────────────────────────────────────────────
if game_over and not ss.get("saved", False):
    n = ss.current_session

    # NEW: Record session end time BEFORE saving stats
    _mark_session_end(n)

    if n == 1:
        ss.session1_completed   = True
        ss.sessions_played      = 1
        ss.session1_balance     = ss.balance
        ss.session1_pnl         = net
        ss.session1_banker_wins = ss.banker_wins
        ss.session1_player_wins = ss.player_wins
        ss.session1_losses      = ss.losses
    else:
        ss.session2_completed   = True
        ss.sessions_played      = 2
        ss.session2_balance     = ss.balance
        ss.session2_pnl         = net
        ss.session2_banker_wins = ss.banker_wins
        ss.session2_player_wins = ss.player_wins
        ss.session2_losses      = ss.losses

    _save_last_balance(ss.balance)

    save_to_history_csv({
        "date":           str(date.today()),
        "start_bal":      ss.start_bal,
        "stop_pct":       ss.stop_pct,
        "target_pct":     ss.target_pct,
        "stop_amt":       sl_amt,
        "target_amt":     tg_amt,
        "trades":         ss.trades,
        "banker_wins":    ss.banker_wins,
        "player_wins":    ss.player_wins,
        "losses":         ss.losses,
        "win_amt":        ss.win_amt,
        "loss_amt":       ss.loss_amt,
        "net":            net,
        "notes":          ss.notes,
        "session_number": n,
        "result":         "stop_loss" if stop_hit else "target",
        "final_balance":  ss.balance,
    })

    ss.saved       = True
    ss.day_started = False
    _remove_files(CURRENT_SESSION_FILE)
    save_daily_stats()
    st.rerun()

if ss.day_started and not game_over:
    auto_save()

if stop_hit or target_hit:
    label = (
        f"🛑 SESSION {ss.current_session} STOP LOSS HIT"
        if stop_hit
        else f"🎯 SESSION {ss.current_session} TARGET ACHIEVED"
    )
    color = "#ef4444" if stop_hit else "#10b981"
    st.markdown(f"""
        <div style="background:{color}15;border:2px solid {color};border-radius:12px;
                    padding:0.8rem;text-align:center;margin:0.4rem 0;">
            <div style="font-size:1.1rem;font-weight:700;color:{color};">{label}</div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Active session indicator ─────────────────────────────────────────────────
st.markdown(f"""
    <div class="pulse" style="background:#667eea20;border:2px solid #667eea;
                border-radius:10px;padding:0.4rem;text-align:center;margin-bottom:0.6rem;">
        <span style="font-size:0.85rem;font-weight:700;">
            🎯 ACTIVE SESSION: {ss.current_session} of 2
            &nbsp;·&nbsp;
            <span style="font-size:0.75rem;color:#a5b4fc;">Daily limit: 2 sessions · {SESSION_GAP_HOURS}h gap enforced</span>
        </span>
    </div>
""", unsafe_allow_html=True)

# ── Row 1: Three balance cards ───────────────────────────────────────────────
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f"""
        <div style="background:linear-gradient(135deg,#f59e0b20,#f59e0b05);
                    border:2px solid #f59e0b;border-radius:12px;
                    padding:0.8rem;text-align:center;">
            <div style="font-size:0.8rem;color:#f59e0b;letter-spacing:1px;font-weight:600;">💰 STARTING BALANCE</div>
            <div style="font-size:2rem;font-weight:800;color:#f59e0b;margin-top:0.2rem;">₹{ss.start_bal:,.0f}</div>
            <div style="font-size:0.75rem;color:#f59e0b80;">Initial Capital</div>
        </div>
    """, unsafe_allow_html=True)

with c2:
    pl_color = "#10b981" if net >= 0 else "#ef4444"
    pl_sign  = "+" if net >= 0 else ""
    pl_icon  = "📈" if net >= 0 else "📉"
    st.markdown(f"""
        <div style="background:{pl_color}10;border:2px solid {pl_color};border-radius:12px;
                    padding:0.8rem;text-align:center;">
            <div style="font-size:0.8rem;color:{pl_color};letter-spacing:1px;font-weight:600;">{pl_icon} CURRENT P&amp;L</div>
            <div style="font-size:2rem;font-weight:800;color:{pl_color};margin-top:0.2rem;">{pl_sign}₹{net:,.0f}</div>
            <div style="font-size:0.75rem;color:{pl_color}80;">Profit &amp; Loss</div>
        </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
        <div style="background:{balance_color}10;border:2px solid {balance_color};border-radius:12px;
                    padding:0.8rem;text-align:center;">
            <div style="font-size:0.8rem;color:{balance_color};letter-spacing:1px;font-weight:600;">💰 CURRENT BALANCE</div>
            <div style="font-size:2rem;font-weight:800;color:{balance_color};margin-top:0.2rem;">₹{ss.balance:,.0f}</div>
            <div style="font-size:0.75rem;color:{balance_color}80;">Updated Balance</div>
        </div>
    """, unsafe_allow_html=True)

# ── Row 2: Win/Loss counters ─────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
_mini = lambda bg, color, label, value: f"""
    <div style="background:{bg};padding:0.6rem 0.4rem;border-radius:8px;text-align:center;">
        <div style="font-size:0.78rem;color:{color};font-weight:600;">{label}</div>
        <div style="font-size:1.5rem;font-weight:800;color:{color};margin-top:0.1rem;">{value}</div>
    </div>
"""
total_wins = ss.banker_wins + ss.player_wins
with c1: st.markdown(_mini("#10b98115", "#10b981", "✅ WINS",     total_wins),         unsafe_allow_html=True)
with c2: st.markdown(_mini("#ef444415", "#ef4444", "❌ LOSSES",   ss.losses),          unsafe_allow_html=True)
with c3: st.markdown(_mini("#ffffff08", "#a78bfa", "📊 WIN RATE", f"{win_rate:.0f}%"), unsafe_allow_html=True)
with c4: st.markdown(_mini("#ffffff08", "#94a3b8", "🎯 TRADES",   ss.trades),          unsafe_allow_html=True)

# ── Remaining amount card ────────────────────────────────────────────────────
st.markdown(f"""
    <div style="background:linear-gradient(135deg,{remaining_color}20,{remaining_color}05);
                border:2px solid {remaining_color};border-radius:15px;
                padding:0.8rem;text-align:center;margin:0.7rem 0;">
        <div style="font-size:0.9rem;color:{remaining_color};font-weight:600;">{status_text}</div>
        <div style="font-size:2.8rem;font-weight:800;color:{remaining_color};">₹{remaining_amount:,.0f}</div>
        <div style="font-size:0.9rem;margin-top:0.3rem;font-weight:600;">
            🛑 Stop: ₹{sl_amt:,.0f} &nbsp;|&nbsp; 🎯 Target: ₹{tg_amt:,.0f}
        </div>
        <div style="font-size:0.8rem;margin-top:0.15rem;color:#aaa;">
            Loss so far: ₹{day_loss:,.0f} &nbsp;|&nbsp; Gain so far: ₹{day_gain:,.0f}
        </div>
    </div>
""", unsafe_allow_html=True)

# ── Progress bars ────────────────────────────────────────────────────────────
stop_progress   = min(day_loss / sl_amt, 1.0) if sl_amt > 0 else 0
target_progress = min(day_gain / tg_amt, 1.0) if tg_amt > 0 else 0

c1, c2 = st.columns(2)
with c1:
    st.markdown(
        f'<div style="font-size:0.65rem;margin-bottom:0.25rem;color:#ef4444;">'
        f'🛑 STOP LOSS: ₹{day_loss:,.0f} / ₹{sl_amt:,.0f}</div>'
        f'<div style="background:#330000;border-radius:10px;height:8px;overflow:hidden;">'
        f'<div style="background:linear-gradient(90deg,#ef4444,#dc2626);'
        f'width:{stop_progress*100:.1f}%;height:100%;transition:width 0.3s;"></div></div>',
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f'<div style="font-size:0.65rem;margin-bottom:0.25rem;color:#10b981;">'
        f'🎯 TARGET: ₹{day_gain:,.0f} / ₹{tg_amt:,.0f}</div>'
        f'<div style="background:#003300;border-radius:10px;height:8px;overflow:hidden;">'
        f'<div style="background:linear-gradient(90deg,#10b981,#059669);'
        f'width:{target_progress*100:.1f}%;height:100%;transition:width 0.3s;"></div></div>',
        unsafe_allow_html=True,
    )

# ── Current bet display ──────────────────────────────────────────────────────
st.markdown(f"""
    <div style="background:linear-gradient(135deg,#f59e0b20,#f59e0b05);
                border:2px solid #f59e0b;border-radius:15px;
                padding:0.6rem;text-align:center;margin:0.7rem 0 0.3rem 0;">
        <div style="font-size:0.7rem;color:#f59e0b;">💰 CURRENT BET</div>
        <div style="font-size:2.2rem;font-weight:700;color:#f59e0b;">₹{ss.bet:,.0f}</div>
    </div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# CHIP GRID
# ════════════════════════════════════════════════════════════════════════════
st.markdown(
    '<div style="font-size:0.9rem;font-weight:700;margin:0.4rem 0 0.3rem 0;'
    'letter-spacing:1px;">🎰 PLACE CHIPS</div>',
    unsafe_allow_html=True,
)

COL_COLORS = ["#6366f1", "#f43f5e", "#f59e0b", "#10b981", "#06b6d4"]

CHIP_COLS = [
    [{"label": "₹10",   "coin": 10},   {"label": "₹20",   "coin": 20},   {"label": "₹40",   "coin": 40}],
    [{"label": "₹60",   "coin": 60},   {"label": "₹80",   "coin": 80},   {"label": "₹100",  "coin": 100}],
    [{"label": "₹120",  "coin": 120},  {"label": "₹140",  "coin": 140},  {"label": "₹160",  "coin": 160}],
    [{"label": "₹180",  "coin": 180},  {"label": "₹200",  "coin": 200},  {"label": "₹400",  "coin": 400}],
    [{"label": "₹500",  "coin": 500},  {"label": "₹800",  "coin": 800},  {"label": "₹1000", "coin": 1000}],
]

chip_css = ["<style>"]
for ci, color in enumerate(COL_COLORS):
    chip_css.append(f"""
.chip-grid2 div[data-testid="stHorizontalBlock"] > div:nth-child({ci+1}) button {{
    background: linear-gradient(160deg, {color}ee, {color}77) !important;
    border: 2px solid {color} !important;
    color: white !important;
    font-weight: 800 !important;
    font-size: 0.95rem !important;
    text-shadow: 0 1px 3px rgba(0,0,0,0.4) !important;
    border-radius: 10px !important;
    padding: 0.5rem 0 !important;
}}""")
chip_css.append("</style>")
st.markdown("".join(chip_css), unsafe_allow_html=True)

st.markdown('<div class="chip-grid2">', unsafe_allow_html=True)
for row_i in range(3):
    cols = st.columns(5)
    for col_i, col in enumerate(cols):
        chip = CHIP_COLS[col_i][row_i]
        with col:
            if st.button(chip["label"], key=f"chip_{chip['coin']}", use_container_width=True):
                new_bet = ss.bet + chip["coin"]
                if new_bet <= ss.max_bet:
                    ss.bet_history = ss.get("bet_history", []) + [ss.bet]
                    ss.bet = new_bet
                    auto_save()
                    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ── Bet controls ─────────────────────────────────────────────────────────────
st.markdown(
    '<div style="font-size:0.8rem;font-weight:700;margin:0.5rem 0 0.2rem 0;">🔧 BET CONTROLS</div>',
    unsafe_allow_html=True,
)
c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("🗑 Clear", use_container_width=True):
        if ss.bet != 0:
            ss.bet_history = ss.get("bet_history", []) + [ss.bet]
            ss.bet = 0.0
            auto_save()
            st.rerun()
with c2:
    if st.button("½ Half", use_container_width=True):
        new_bet = round(ss.bet / 2)
        ss.bet_history = ss.get("bet_history", []) + [ss.bet]
        ss.bet = new_bet
        auto_save()
        st.rerun()
with c3:
    if st.button("×2 Double", use_container_width=True):
        new_bet = ss.bet * 2
        if new_bet <= ss.max_bet:
            ss.bet_history = ss.get("bet_history", []) + [ss.bet]
            ss.bet = new_bet
            auto_save()
            st.rerun()
with c4:
    bet_hist = ss.get("bet_history", [])
    undo_disabled = (len(bet_hist) == 0) and (ss.last_action is None)
    if st.button("↩️ Undo", use_container_width=True, disabled=undo_disabled):
        bet_hist = ss.get("bet_history", [])
        if bet_hist:
            ss.bet = bet_hist[-1]
            ss.bet_history = bet_hist[:-1]
        elif ss.last_action is not None:
            for key, value in ss.last_action.items():
                setattr(ss, key, value)
            ss.last_action = None
        auto_save()
        st.rerun()

# ── Banker / Player / Loss buttons ───────────────────────────────────────────
st.markdown(
    '<div style="font-size:0.8rem;font-weight:700;margin:0.5rem 0 0.2rem 0;">🎯 OUTCOME</div>',
    unsafe_allow_html=True,
)

bet_ok = ss.bet > 0

c1, c2, c3 = st.columns([1, 1, 2])

def _snapshot_before_trade() -> dict:
    return {
        "balance":     ss.balance,
        "win_amt":     ss.win_amt,
        "loss_amt":    ss.loss_amt,
        "banker_wins": ss.banker_wins,
        "player_wins": ss.player_wins,
        "losses":      ss.losses,
        "trades":      ss.trades,
        "bet":         ss.bet,
    }

with c1:
    if st.button("🔴 BANKER\n(95% payout)", use_container_width=True, disabled=not bet_ok):
        ss.last_action = _snapshot_before_trade()
        amt      = ss.bet
        winnings = round(amt * 0.95, 2)
        ss.balance     += winnings
        ss.win_amt     += winnings
        ss.banker_wins += 1
        ss.trades      += 1
        ss.bet          = 0.0
        ss.bet_history  = []
        commission = amt - winnings
        _log = ss.get("trade_log", [])
        _log.append({"time": datetime.now().strftime("%H:%M:%S"), "type": "BANKER", "bet": amt, "result": winnings})
        ss.trade_log = _log[-10:]
        st.toast(f"🔴 Banker! +₹{winnings:,.2f} (Commission ₹{commission:,.2f})", icon="💰")
        play_sound("win")
        auto_save()
        st.rerun()

with c2:
    if st.button("🔵 PLAYER\n(1:1 payout)", use_container_width=True, disabled=not bet_ok):
        ss.last_action = _snapshot_before_trade()
        amt      = ss.bet
        ss.balance     += amt
        ss.win_amt     += amt
        ss.player_wins += 1
        ss.trades      += 1
        ss.bet          = 0.0
        ss.bet_history  = []
        _log = ss.get("trade_log", [])
        _log.append({"time": datetime.now().strftime("%H:%M:%S"), "type": "PLAYER", "bet": amt, "result": amt})
        ss.trade_log = _log[-10:]
        st.toast(f"🔵 Player! +₹{amt:,.0f}", icon="💰")
        play_sound("win")
        auto_save()
        st.rerun()

with c3:
    if st.button("⚫ LOSS  —  Full bet forfeited", use_container_width=True, disabled=not bet_ok):
        ss.last_action = _snapshot_before_trade()
        amt = ss.bet
        ss.balance  -= amt
        ss.loss_amt += amt
        ss.losses   += 1
        ss.trades   += 1
        ss.bet       = 0.0
        ss.bet_history = []
        _log = ss.get("trade_log", [])
        _log.append({"time": datetime.now().strftime("%H:%M:%S"), "type": "LOSS", "bet": amt, "result": -amt})
        ss.trade_log = _log[-10:]
        st.toast(f"⚫ Loss! -₹{amt:,.0f}", icon="💀")
        play_sound("loss")
        auto_save()
        st.rerun()

if not bet_ok:
    st.markdown(
        '<p style="text-align:center;color:#f59e0b;font-size:0.7rem;margin:0.2rem 0;">⚠️ Select chips first</p>',
        unsafe_allow_html=True,
    )

# ── Last 10 Trades History ───────────────────────────────────────────────────
trade_log = list(ss.get("trade_log", []))

st.markdown("""
    <div style="font-size:1rem;font-weight:700;margin:1rem 0 0.4rem 0;
                letter-spacing:1.5px;color:#e5e7eb;">
        🕐 LAST 10 TRADES
    </div>
""", unsafe_allow_html=True)

if not trade_log:
    st.markdown("""
        <div style="background:#ffffff08;border:1px solid #333;border-radius:10px;
                    padding:1rem;text-align:center;color:#666;font-size:0.95rem;">
            No trades yet this session
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <div style="display:grid;grid-template-columns:90px 1fr 100px 110px;
                    gap:0.4rem;padding:0.45rem 0.8rem;
                    font-size:0.78rem;color:#888;letter-spacing:1px;font-weight:700;
                    border-bottom:1px solid #2a2a3e;margin-bottom:0.2rem;">
            <div>TIME</div><div>TYPE</div>
            <div style="text-align:right;">BET</div>
            <div style="text-align:right;">RESULT</div>
        </div>
    """, unsafe_allow_html=True)

    rows_html = ""
    for trade in reversed(trade_log):
        result  = trade["result"]
        bet     = trade["bet"]
        t_type  = trade["type"]
        t_time  = trade.get("time", "--:--:--")

        is_win  = result > 0
        r_color = "#10b981" if is_win else "#ef4444"
        r_sign  = "+" if is_win else ""
        r_text  = f"{r_sign}₹{abs(result):,.0f}"

        if t_type == "BANKER":
            type_icon, type_color, type_label = "🔴", "#f87171", "Banker"
        elif t_type == "PLAYER":
            type_icon, type_color, type_label = "🔵", "#60a5fa", "Player"
        else:
            type_icon, type_color, type_label = "⚫", "#9ca3af", "Loss"

        bg     = "#10b98112" if is_win else "#ef444412"
        border = "#10b98130" if is_win else "#ef444430"

        rows_html += f"""
        <div style="display:grid;grid-template-columns:90px 1fr 100px 110px;
                    gap:0.4rem;padding:0.55rem 0.8rem;
                    background:{bg};border-left:3px solid {border};
                    border-radius:6px;margin-bottom:0.25rem;
                    font-size:0.95rem;align-items:center;">
            <div style="color:#888;font-size:0.82rem;font-family:monospace;">{t_time}</div>
            <div style="color:{type_color};font-weight:700;font-size:0.95rem;">{type_icon} {type_label}</div>
            <div style="text-align:right;color:#d1d5db;font-size:0.95rem;font-weight:600;">₹{bet:,.0f}</div>
            <div style="text-align:right;font-weight:800;font-size:1rem;color:{r_color};">{r_text}</div>
        </div>"""

    st.markdown(
        f'<div style="background:linear-gradient(135deg,#0f0f1a,#1a1a2e);'
        f'border:1px solid #2a2a3e;border-radius:14px;padding:0.5rem 0.4rem;">'
        f'{rows_html}</div>',
        unsafe_allow_html=True,
    )