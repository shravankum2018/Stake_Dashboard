import streamlit as st
import pandas as pd
import os
import json
from datetime import date, datetime
from utils.data_manager import DataManager
from utils.styles import get_css, CHIP_DEFS
from utils.sounds import play_sound

# Page configuration
st.set_page_config(
    page_title="Stake Tracker",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize data manager
data_manager = DataManager()

# Load CSS
st.markdown(get_css(), unsafe_allow_html=True)

# File paths
CURRENT_SESSION_FILE = "current_session.json"
DAILY_STATS_FILE = "daily_stats.json"
HISTORY_CSV_FILE = "stake_history.csv"

def save_to_history_csv(session_data):
    """Save completed session to history CSV"""
    history_file = HISTORY_CSV_FILE

    row_data = {
        'date': session_data.get('date', str(date.today())),
        'start_bal': session_data.get('start_bal', 0),
        'stop_pct': session_data.get('stop_pct', 0),
        'target_pct': session_data.get('target_pct', 0),
        'stop_amt': session_data.get('stop_amt', 0),
        'target_amt': session_data.get('target_amt', 0),
        'trades': session_data.get('trades', 0),
        'wins': session_data.get('wins', 0),
        'losses': session_data.get('losses', 0),
        'win_amt': session_data.get('win_amt', 0),
        'loss_amt': session_data.get('loss_amt', 0),
        'net': session_data.get('net', 0),
        'result': session_data.get('result', 'incomplete'),
        'notes': session_data.get('notes', ''),
        'session_number': session_data.get('session_number', 1),
        'final_balance': session_data.get('final_balance', 0)
    }

    if os.path.exists(history_file):
        df = pd.read_csv(history_file)
        df = pd.concat([df, pd.DataFrame([row_data])], ignore_index=True)
    else:
        df = pd.DataFrame([row_data])

    df.to_csv(history_file, index=False)

def save_current_session():
    """Save current session data to file"""
    session_data = {
        'day_started': st.session_state.day_started,
        'balance': st.session_state.balance,
        'start_bal': st.session_state.start_bal,
        'stop_pct': st.session_state.stop_pct,
        'target_pct': st.session_state.target_pct,
        'stop_amt': st.session_state.stop_amt,
        'target_amt': st.session_state.target_amt,
        'bet': st.session_state.bet,
        'wins': st.session_state.wins,
        'losses': st.session_state.losses,
        'win_amt': st.session_state.win_amt,
        'loss_amt': st.session_state.loss_amt,
        'trades': st.session_state.trades,
        'notes': st.session_state.notes,
        'last_action': st.session_state.last_action,
        'current_session': st.session_state.current_session,
        'session1_completed': st.session_state.session1_completed,
        'session2_completed': st.session_state.session2_completed,
        'sessions_played': st.session_state.sessions_played,
        'session1_balance': st.session_state.session1_balance,
        'session1_pnl': st.session_state.session1_pnl,
        'session2_balance': st.session_state.session2_balance,
        'session2_pnl': st.session_state.session2_pnl,
        'result': "active",
        'date': str(date.today()),
        'last_update': datetime.now().isoformat()
    }

    with open(CURRENT_SESSION_FILE, 'w') as f:
        json.dump(session_data, f, indent=2)

def load_current_session():
    """Load current session data from file"""
    if os.path.exists(CURRENT_SESSION_FILE):
        try:
            with open(CURRENT_SESSION_FILE, 'r') as f:
                session_data = json.load(f)

            # Check if session is from today
            session_date = session_data.get('date', '')
            if session_date == str(date.today()):
                return session_data
            else:
                # Session from previous day, save to history
                if session_data.get('day_started', False) or session_data.get('trades', 0) > 0:
                    save_to_history_csv(session_data)
                os.remove(CURRENT_SESSION_FILE)
                return None
        except:
            pass
    return None

def save_daily_stats():
    """Save daily session stats"""
    daily_stats = {
        'date': str(date.today()),
        'sessions_played': st.session_state.sessions_played,
        'session1_completed': st.session_state.session1_completed,
        'session2_completed': st.session_state.session2_completed,
        'session1_balance': st.session_state.session1_balance,
        'session1_pnl': st.session_state.session1_pnl,
        'session2_balance': st.session_state.session2_balance,
        'session2_pnl': st.session_state.session2_pnl,
        'total_trades': st.session_state.trades,
        'total_pnl': st.session_state.balance - st.session_state.start_bal,
        'last_update': datetime.now().isoformat()
    }

    with open(DAILY_STATS_FILE, 'w') as f:
        json.dump(daily_stats, f, indent=2)

def load_daily_stats():
    """Load daily stats"""
    if os.path.exists(DAILY_STATS_FILE):
        try:
            with open(DAILY_STATS_FILE, 'r') as f:
                stats = json.load(f)
                if stats.get('date') == str(date.today()):
                    return stats
        except:
            pass
    return None

def reset_for_new_day():
    """Reset everything for a new day"""
    try:
        # Clear current session files
        if os.path.exists(CURRENT_SESSION_FILE):
            os.remove(CURRENT_SESSION_FILE)
        if os.path.exists(DAILY_STATS_FILE):
            os.remove(DAILY_STATS_FILE)

        # Reset session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]

        return True
    except Exception as e:
        print(f"Error during reset: {e}")
        return False

def reset_session_data():
    """Reset all session data to default values"""
    try:
        # Reset all session state values
        st.session_state.day_started = False
        st.session_state.balance = 1000.0
        st.session_state.start_bal = 1000.0
        st.session_state.stop_pct = 10
        st.session_state.target_pct = 15
        st.session_state.stop_amt = 100.0
        st.session_state.target_amt = 150.0
        st.session_state.bet = 0.0
        st.session_state.wins = 0
        st.session_state.losses = 0
        st.session_state.win_amt = 0.0
        st.session_state.loss_amt = 0.0
        st.session_state.trades = 0
        st.session_state.last_action = None
        st.session_state.summary_shown = False
        st.session_state.notes = ""
        st.session_state.saved = False
        st.session_state.current_session = 1
        st.session_state.session1_completed = False
        st.session_state.session2_completed = False
        st.session_state.sessions_played = 0
        st.session_state.session1_balance = 0.0
        st.session_state.session1_pnl = 0.0
        st.session_state.session2_balance = 0.0
        st.session_state.session2_pnl = 0.0

        # Clear current session file
        if os.path.exists(CURRENT_SESSION_FILE):
            os.remove(CURRENT_SESSION_FILE)
        if os.path.exists(DAILY_STATS_FILE):
            os.remove(DAILY_STATS_FILE)

        return True
    except Exception as e:
        print(f"Error resetting session: {e}")
        return False

# Session state defaults
DEFS = dict(
    day_started=False,
    balance=1000.0,
    start_bal=1000.0,
    stop_pct=10,
    target_pct=15,
    stop_amt=100.0,
    target_amt=150.0,
    bet=0.0,
    wins=0,
    losses=0,
    win_amt=0.0,
    loss_amt=0.0,
    trades=0,
    last_action=None,
    summary_shown=False,
    notes="",
    max_bet=100000,
    saved=False,
    current_session=1,
    session1_completed=False,
    session2_completed=False,
    sessions_played=0,
    session1_balance=0.0,
    session1_pnl=0.0,
    session2_balance=0.0,
    session2_pnl=0.0
)

# Load saved session if exists
saved_session = load_current_session()
daily_stats = load_daily_stats()

if daily_stats:
    DEFS['sessions_played'] = daily_stats.get('sessions_played', 0)
    DEFS['session1_completed'] = daily_stats.get('session1_completed', False)
    DEFS['session2_completed'] = daily_stats.get('session2_completed', False)
    DEFS['session1_balance'] = daily_stats.get('session1_balance', 0.0)
    DEFS['session1_pnl'] = daily_stats.get('session1_pnl', 0.0)
    DEFS['session2_balance'] = daily_stats.get('session2_balance', 0.0)
    DEFS['session2_pnl'] = daily_stats.get('session2_pnl', 0.0)

if saved_session:
    for k, v in saved_session.items():
        if k in DEFS:
            DEFS[k] = v

# Initialize session state
for k, v in DEFS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Auto-save after every change
def auto_save():
    if st.session_state.day_started:
        save_current_session()
        save_daily_stats()

# Sidebar
with st.sidebar:
    st.markdown("## 🎮 CONTROL PANEL")
    st.markdown("---")

    st.markdown(f"**📅 Today:** {date.today().strftime('%B %d, %Y')}")
    st.markdown("---")

    st.markdown("### 🔧 Reset Options")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Reset Current Session", use_container_width=True):
            if reset_session_data():
                st.success("Session reset! Starting fresh...")
                st.rerun()

    with col2:
        if st.button("🗑️ Complete Reset", use_container_width=True):
            files = [CURRENT_SESSION_FILE, DAILY_STATS_FILE, HISTORY_CSV_FILE]
            for file in files:
                if os.path.exists(file):
                    os.remove(file)
            if reset_session_data():
                st.success("Complete reset! Starting fresh...")
                st.rerun()

    st.markdown("---")

    st.markdown("### 📊 Today's Progress")

    if st.session_state.session1_completed:
        st.success("✅ Session 1: COMPLETED")
        if st.session_state.session1_balance > 0:
            st.metric("Session 1 Balance", f"₹{st.session_state.session1_balance:,.0f}",
                     delta=f"{'+' if st.session_state.session1_pnl >= 0 else ''}₹{st.session_state.session1_pnl:,.0f}",
                     delta_color="normal")
    elif st.session_state.current_session == 1 and st.session_state.day_started:
        st.info("🟢 Session 1: IN PROGRESS")
    else:
        st.warning("⚪ Session 1: NOT STARTED")

    if st.session_state.session2_completed:
        st.success("✅ Session 2: COMPLETED")
        if st.session_state.session2_balance > 0:
            st.metric("Session 2 Balance", f"₹{st.session_state.session2_balance:,.0f}",
                     delta=f"{'+' if st.session_state.session2_pnl >= 0 else ''}₹{st.session_state.session2_pnl:,.0f}",
                     delta_color="normal")
    elif st.session_state.current_session == 2 and st.session_state.day_started:
        st.info("🟢 Session 2: IN PROGRESS")
    elif st.session_state.session1_completed:
        st.warning("⚪ Session 2: READY")
    else:
        st.warning("⚪ Session 2: NOT STARTED")

    st.markdown("---")

    if st.session_state.day_started:
        st.markdown("### 📈 Current Session Stats")
        st.metric("Trades", st.session_state.trades)
        st.metric("Wins", st.session_state.wins)
        st.metric("Losses", st.session_state.losses)
        win_rate = (st.session_state.wins / st.session_state.trades * 100) if st.session_state.trades > 0 else 0
        st.metric("Win Rate", f"{win_rate:.0f}%")

    st.markdown("---")

    if st.button("💾 Save Progress", use_container_width=True):
        auto_save()
        st.success("Progress saved!")

    st.markdown("---")

    st.markdown("### 📋 Session History")

    if os.path.exists(HISTORY_CSV_FILE):
        df_history = pd.read_csv(HISTORY_CSV_FILE)
        if not df_history.empty:
            st.dataframe(df_history.tail(5), use_container_width=True, height=200)

            csv_data = df_history.to_csv(index=False).encode()
            st.download_button(
                label="⬇️ Download History",
                data=csv_data,
                file_name="stake_history.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("No history yet")
    else:
        st.info("No history yet")

# Header
st.markdown('<h1 style="text-align:center; font-size:1.8rem; margin:0 0 0.3rem 0;">🎰 STAKE TRACKER</h1>', unsafe_allow_html=True)

# Check if both sessions are completed
if st.session_state.session2_completed:
    st.markdown("""
        <div style="background:linear-gradient(135deg, #1a1a2e, #16213e); border:2px solid #10b981; border-radius:20px; padding:2rem; text-align:center; margin:1rem 0;">
            <div style="font-size:1.8rem; margin-bottom:0.5rem;">🏆 DAY COMPLETE</div>
            <div style="font-size:1rem; margin-bottom:1.5rem; color:#888;">Both sessions completed for today!</div>
    """, unsafe_allow_html=True)

    # Display Session 1 Results
    if st.session_state.session1_completed:
        s1_color = "#10b981" if st.session_state.session1_pnl >= 0 else "#ef4444"
        s1_sign = "+" if st.session_state.session1_pnl >= 0 else ""
        st.markdown(f'''
            <div style="background:linear-gradient(135deg, #0f0f1a, #1a1a2e); border:1px solid {s1_color}; border-radius:15px; padding:1rem; margin:1rem 0;">
                <div style="font-size:1.2rem; font-weight:bold; margin-bottom:0.5rem;">📊 SESSION 1 RESULTS</div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem;">
                    <div>
                        <div style="font-size:0.7rem; color:#888;">STARTING BALANCE</div>
                        <div style="font-size:1.3rem; font-weight:bold; color:#f59e0b;">₹{st.session_state.session1_balance - st.session_state.session1_pnl:,.0f}</div>
                    </div>
                    <div>
                        <div style="font-size:0.7rem; color:#888;">FINAL BALANCE</div>
                        <div style="font-size:1.3rem; font-weight:bold; color:{s1_color};">₹{st.session_state.session1_balance:,.0f}</div>
                    </div>
                    <div>
                        <div style="font-size:0.7rem; color:#888;">PROFIT / LOSS</div>
                        <div style="font-size:1.3rem; font-weight:bold; color:{s1_color};">{s1_sign}₹{abs(st.session_state.session1_pnl):,.0f}</div>
                    </div>
                    <div>
                        <div style="font-size:0.7rem; color:#888;">RESULT</div>
                        <div style="font-size:1rem; font-weight:bold; color:{s1_color};">{'PROFIT 🎉' if st.session_state.session1_pnl >= 0 else 'LOSS 💀'}</div>
                    </div>
                </div>
            </div>
        ''', unsafe_allow_html=True)

    # Display Session 2 Results
    if st.session_state.session2_completed:
        s2_color = "#10b981" if st.session_state.session2_pnl >= 0 else "#ef4444"
        s2_sign = "+" if st.session_state.session2_pnl >= 0 else ""
        st.markdown(f'''
            <div style="background:linear-gradient(135deg, #0f0f1a, #1a1a2e); border:1px solid {s2_color}; border-radius:15px; padding:1rem; margin:1rem 0;">
                <div style="font-size:1.2rem; font-weight:bold; margin-bottom:0.5rem;">📊 SESSION 2 RESULTS</div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem;">
                    <div>
                        <div style="font-size:0.7rem; color:#888;">STARTING BALANCE</div>
                        <div style="font-size:1.3rem; font-weight:bold; color:#f59e0b;">₹{st.session_state.session2_balance - st.session_state.session2_pnl:,.0f}</div>
                    </div>
                    <div>
                        <div style="font-size:0.7rem; color:#888;">FINAL BALANCE</div>
                        <div style="font-size:1.3rem; font-weight:bold; color:{s2_color};">₹{st.session_state.session2_balance:,.0f}</div>
                    </div>
                    <div>
                        <div style="font-size:0.7rem; color:#888;">PROFIT / LOSS</div>
                        <div style="font-size:1.3rem; font-weight:bold; color:{s2_color};">{s2_sign}₹{abs(st.session_state.session2_pnl):,.0f}</div>
                    </div>
                    <div>
                        <div style="font-size:0.7rem; color:#888;">RESULT</div>
                        <div style="font-size:1rem; font-weight:bold; color:{s2_color};">{'PROFIT 🎉' if st.session_state.session2_pnl >= 0 else 'LOSS 💀'}</div>
                    </div>
                </div>
            </div>
        ''', unsafe_allow_html=True)

    # Total Day Summary
    total_pnl = st.session_state.session1_pnl + st.session_state.session2_pnl
    total_color = "#10b981" if total_pnl >= 0 else "#ef4444"
    total_sign = "+" if total_pnl >= 0 else ""

    st.markdown(f'''
        <div style="background:linear-gradient(135deg, #10b98110, #10b98105); border:2px solid {total_color}; border-radius:15px; padding:1rem; margin:1rem 0;">
            <div style="font-size:1.1rem; font-weight:bold; margin-bottom:0.5rem;">📈 TOTAL DAY SUMMARY</div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem;">
                <div>
                    <div style="font-size:0.7rem; color:#888;">TOTAL P&L</div>
                    <div style="font-size:1.5rem; font-weight:bold; color:{total_color};">{total_sign}₹{abs(total_pnl):,.0f}</div>
                </div>
                <div>
                    <div style="font-size:0.7rem; color:#888;">SESSIONS PLAYED</div>
                    <div style="font-size:1.5rem; font-weight:bold;">2 / 2</div>
                </div>
            </div>
        </div>
    ''', unsafe_allow_html=True)

    st.markdown("""
        <div style="text-align:center; margin-top:1rem;">
            <div style="font-size:0.9rem; color:#888;">Use 'Reset Current Session' to start fresh tomorrow</div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Start New Session", use_container_width=True):
        if reset_session_data():
            st.rerun()
    st.stop()

# Check if can play today
if st.session_state.sessions_played >= 2 and not st.session_state.session2_completed:
    st.session_state.session2_completed = True
    save_daily_stats()

if st.session_state.session2_completed:
    st.stop()

# Setup Screen
if not st.session_state.day_started:
    with st.container():
        st.markdown('<div style="background:rgba(255,255,255,0.05); padding:1rem; border-radius:12px; margin:0.5rem 0;">', unsafe_allow_html=True)

        session_num = 1
        default_start_bal = 1000.0

        if st.session_state.session1_completed and not st.session_state.session2_completed:
            session_num = 2
            # Use Session 1's final balance as starting balance for Session 2
            default_start_bal = st.session_state.session1_balance if st.session_state.session1_balance > 0 else 1000.0
            st.markdown(f'''
                <div style="background:#10b98120; border:2px solid #10b981; border-radius:10px; padding:0.6rem; text-align:center; margin-bottom:1rem;">
                    <strong style="color:#10b981; font-size:1rem;">🎯 Starting Session {session_num} of 2</strong>
                </div>
            ''', unsafe_allow_html=True)

            # Show previous session result
            prev_pnl = st.session_state.session1_pnl
            prev_color = "#10b981" if prev_pnl >= 0 else "#ef4444"
            prev_sign = "+" if prev_pnl >= 0 else ""
            st.markdown(f'''
                <div style="background:{prev_color}10; border:1px solid {prev_color}; border-radius:8px; padding:0.5rem; text-align:center; margin-bottom:1rem;">
                    <div style="font-size:0.7rem; color:#888;">Previous Session Result</div>
                    <div style="font-size:1rem; font-weight:bold; color:{prev_color};">{prev_sign}₹{abs(prev_pnl):,.0f}</div>
                    <div style="font-size:0.7rem;">Final Balance: ₹{st.session_state.session1_balance:,.0f}</div>
                </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
                <div style="background:#667eea20; border:2px solid #667eea; border-radius:10px; padding:0.6rem; text-align:center; margin-bottom:1rem;">
                    <strong style="color:#667eea; font-size:1rem;">🎯 Starting Session {session_num} of 2</strong>
                </div>
            ''', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            start_bal = st.number_input(
                "💰 Starting Balance",
                min_value=100.0,
                value=float(default_start_bal),
                step=500.0,
                format="%.0f",
                help=f"Previous session balance: ₹{default_start_bal:,.0f}"
            )
        with col2:
            stop_pct = st.number_input("🛑 Stop Loss %", min_value=1, max_value=90, value=10, step=1)
        with col3:
            target_pct = st.number_input("🎯 Target %", min_value=1, max_value=500, value=15, step=1)

        sl_amt = start_bal * stop_pct / 100
        tg_amt = start_bal * target_pct / 100

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div style="background:#00000030; padding:0.6rem; border-radius:8px; text-align:center;"><span style="color:#ef4444; font-size:1rem;">🔴 Stop Loss: -₹{sl_amt:,.0f}</span></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div style="background:#00000030; padding:0.6rem; border-radius:8px; text-align:center;"><span style="color:#10b981; font-size:1rem;">🟢 Target: +₹{tg_amt:,.0f}</span></div>', unsafe_allow_html=True)

        if st.button("🚀 START SESSION", use_container_width=True):
            st.session_state.update(dict(
                day_started=True,
                balance=start_bal,
                start_bal=start_bal,
                stop_pct=stop_pct,
                target_pct=target_pct,
                stop_amt=sl_amt,
                target_amt=tg_amt,
                summary_shown=False,
                wins=0, losses=0, win_amt=0, loss_amt=0, trades=0, bet=0,
                notes="", saved=False,
                current_session=session_num
            ))
            auto_save()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Main Dashboard
net = st.session_state.balance - st.session_state.start_bal
day_loss = abs(min(net, 0))
day_gain = max(net, 0)
sl_amt = st.session_state.stop_amt
tg_amt = st.session_state.target_amt

# Calculate remaining amounts based on current P&L
if net >= 0:
    remaining_target = max(0, tg_amt - day_gain)
    remaining_stop = sl_amt + day_gain
    remaining_amount = remaining_target
    remaining_color = "#10b981"
    status_text = "🎯 Amount needed to reach Target"
else:
    remaining_stop = max(0, sl_amt - day_loss)
    remaining_target = tg_amt + day_loss
    remaining_amount = remaining_stop
    remaining_color = "#ef4444"
    status_text = "🛑 Amount before Stop Loss"

stop_hit = sl_amt > 0 and day_loss >= sl_amt
target_hit = tg_amt > 0 and day_gain >= tg_amt
game_over = stop_hit or target_hit
wr = (st.session_state.wins / st.session_state.trades * 100) if st.session_state.trades > 0 else 0
avg_bet = (st.session_state.win_amt + st.session_state.loss_amt) / st.session_state.trades if st.session_state.trades > 0 else 0

# Determine colors for current balance
if net > 0:
    balance_color = "#10b981"
    balance_icon = "📈"
elif net < 0:
    balance_color = "#ef4444"
    balance_icon = "📉"
else:
    balance_color = "#f59e0b"
    balance_icon = "⚖️"

# Handle session completion
if game_over and not st.session_state.get('saved', False):
    # Save session results
    if st.session_state.current_session == 1:
        st.session_state.session1_completed = True
        st.session_state.sessions_played = 1
        st.session_state.session1_balance = st.session_state.balance
        st.session_state.session1_pnl = net
    elif st.session_state.current_session == 2:
        st.session_state.session2_completed = True
        st.session_state.sessions_played = 2
        st.session_state.session2_balance = st.session_state.balance
        st.session_state.session2_pnl = net

    # Save to history
    session_data = {
        'date': str(date.today()),
        'start_bal': st.session_state.start_bal,
        'stop_pct': st.session_state.stop_pct,
        'target_pct': st.session_state.target_pct,
        'stop_amt': sl_amt,
        'target_amt': tg_amt,
        'trades': st.session_state.trades,
        'wins': st.session_state.wins,
        'losses': st.session_state.losses,
        'win_amt': st.session_state.win_amt,
        'loss_amt': st.session_state.loss_amt,
        'net': net,
        'notes': st.session_state.notes,
        'session_number': st.session_state.current_session,
        'result': "stop_loss" if stop_hit else "target",
        'final_balance': st.session_state.balance
    }
    save_to_history_csv(session_data)

    st.session_state.saved = True
    st.session_state.day_started = False

    # Clear current session file
    if os.path.exists(CURRENT_SESSION_FILE):
        os.remove(CURRENT_SESSION_FILE)

    save_daily_stats()
    st.rerun()

# Auto-save after every action
if st.session_state.day_started and not game_over:
    auto_save()

# Alert Banner
if stop_hit or target_hit:
    alert_text = f"🛑 SESSION {st.session_state.current_session} STOP LOSS HIT" if stop_hit else f"🎯 SESSION {st.session_state.current_session} TARGET ACHIEVED"
    alert_color = "#ef4444" if stop_hit else "#10b981"

    next_session_msg = ""
    if st.session_state.current_session == 1 and not st.session_state.session2_completed:
        next_session_msg = "✅ Click START to begin Session 2"
    elif st.session_state.current_session == 2:
        next_session_msg = "🏆 Both sessions completed! View results above"

    st.markdown(f'''
        <div style="background:{alert_color}15; border:2px solid {alert_color}; border-radius:12px; padding:0.8rem; text-align:center; margin:0.5rem 0;">
            <div style="font-size:1.1rem; font-weight:bold; color:{alert_color};">{alert_text}</div>
            <div style="font-size:0.85rem; margin-top:0.3rem;">{next_session_msg}</div>
        </div>
    ''', unsafe_allow_html=True)

    if st.session_state.current_session == 1 and not st.session_state.session2_completed:
        if st.button("🎮 Start Session 2", use_container_width=True):
            st.session_state.day_started = False
            st.session_state.saved = False
            st.rerun()

    st.stop()

# Show current session indicator
st.markdown(f'''
    <div style="background:#667eea20; border:2px solid #667eea; border-radius:10px; padding:0.4rem; text-align:center; margin-bottom:0.8rem;">
        <span style="font-size:0.85rem; font-weight:bold;">🎯 ACTIVE SESSION: {st.session_state.current_session} of 2</span>
    </div>
''', unsafe_allow_html=True)

# Stats Row 1 - Three main metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f'''
        <div style="background:linear-gradient(135deg, #f59e0b20, #f59e0b05); border:2px solid #f59e0b; border-radius:12px; padding:0.6rem; text-align:center;">
            <div style="font-size:0.7rem; color:#f59e0b; letter-spacing:1px;">💰 STARTING BALANCE</div>
            <div style="font-size:1.4rem; font-weight:bold; color:#f59e0b; margin-top:0.3rem;">₹{st.session_state.start_bal:,.0f}</div>
            <div style="font-size:0.65rem; color:#f59e0b80; margin-top:0.2rem;">Initial Capital</div>
        </div>
    ''', unsafe_allow_html=True)

with col2:
    pl_color = "#10b981" if net >= 0 else "#ef4444"
    pl_sign = "+" if net >= 0 else ""
    pl_icon = "📈" if net >= 0 else "📉"
    st.markdown(f'''
        <div style="background:{pl_color}10; border:2px solid {pl_color}; border-radius:12px; padding:0.6rem; text-align:center;">
            <div style="font-size:0.7rem; color:{pl_color}; letter-spacing:1px;">{pl_icon} CURRENT P&L</div>
            <div style="font-size:1.4rem; font-weight:bold; color:{pl_color}; margin-top:0.3rem;">{pl_sign}₹{net:,.0f}</div>
            <div style="font-size:0.65rem; color:{pl_color}80; margin-top:0.2rem;">Profit & Loss</div>
        </div>
    ''', unsafe_allow_html=True)

with col3:
    balance_icon = "💰"
    st.markdown(f'''
        <div style="background:{balance_color}10; border:2px solid {balance_color}; border-radius:12px; padding:0.6rem; text-align:center;">
            <div style="font-size:0.7rem; color:{balance_color}; letter-spacing:1px;">{balance_icon} CURRENT BALANCE</div>
            <div style="font-size:1.4rem; font-weight:bold; color:{balance_color}; margin-top:0.3rem;">₹{st.session_state.balance:,.0f}</div>
            <div style="font-size:0.65rem; color:{balance_color}80; margin-top:0.2rem;">Updated Balance</div>
        </div>
    ''', unsafe_allow_html=True)

# Stats Row 2
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'''
        <div style="background:#00000030; padding:0.4rem; border-radius:8px; text-align:center;">
            <div style="font-size:0.6rem; color:#888;">✅ WINS</div>
            <div style="font-size:1rem; font-weight:bold; color:#10b981;">{st.session_state.wins}</div>
        </div>
    ''', unsafe_allow_html=True)
with col2:
    st.markdown(f'''
        <div style="background:#00000030; padding:0.4rem; border-radius:8px; text-align:center;">
            <div style="font-size:0.6rem; color:#888;">❌ LOSSES</div>
            <div style="font-size:1rem; font-weight:bold; color:#ef4444;">{st.session_state.losses}</div>
        </div>
    ''', unsafe_allow_html=True)
with col3:
    st.markdown(f'''
        <div style="background:#00000030; padding:0.4rem; border-radius:8px; text-align:center;">
            <div style="font-size:0.6rem; color:#888;">📊 WIN RATE</div>
            <div style="font-size:1rem; font-weight:bold;">{wr:.0f}%</div>
        </div>
    ''', unsafe_allow_html=True)
with col4:
    st.markdown(f'''
        <div style="background:#00000030; padding:0.4rem; border-radius:8px; text-align:center;">
            <div style="font-size:0.6rem; color:#888;">🎯 TOTAL TRADES</div>
            <div style="font-size:1rem; font-weight:bold;">{st.session_state.trades}</div>
        </div>
    ''', unsafe_allow_html=True)

# Remaining Amount Card
st.markdown(f'''
    <div style="background:linear-gradient(135deg, {remaining_color}20, {remaining_color}05); border:2px solid {remaining_color}; border-radius:15px; padding:0.8rem; text-align:center; margin:0.8rem 0;">
        <div style="font-size:0.75rem; color:{remaining_color};">{status_text}</div>
        <div style="font-size:2rem; font-weight:bold; color:{remaining_color};">₹{remaining_amount:,.0f}</div>
        <div style="font-size:0.7rem; margin-top:0.3rem;">
            🛑 Stop Limit: ₹{sl_amt:,.0f} &nbsp;|&nbsp; 🎯 Target Limit: ₹{tg_amt:,.0f}
        </div>
        <div style="font-size:0.65rem; margin-top:0.2rem; color:#888;">
            Current Loss: ₹{day_loss:,.0f} | Current Gain: ₹{day_gain:,.0f}
        </div>
    </div>
''', unsafe_allow_html=True)

# Progress Section
stop_progress = min(day_loss / sl_amt, 1.0) if sl_amt > 0 else 0
target_progress = min(day_gain / tg_amt, 1.0) if tg_amt > 0 else 0

col1, col2 = st.columns(2)

with col1:
    st.markdown(f'<div style="font-size:0.7rem; margin-bottom:0.3rem; color:#ef4444;">🛑 STOP LOSS PROGRESS: ₹{day_loss:,.0f} / ₹{sl_amt:,.0f}</div>', unsafe_allow_html=True)
    st.markdown(f'''
        <div style="background:#330000; border-radius:10px; height:8px; overflow:hidden;">
            <div style="background:linear-gradient(90deg, #ef4444, #dc2626); width:{stop_progress * 100}%; height:100%; transition:width 0.3s ease;"></div>
        </div>
    ''', unsafe_allow_html=True)

with col2:
    st.markdown(f'<div style="font-size:0.7rem; margin-bottom:0.3rem; color:#10b981;">🎯 TARGET PROGRESS: ₹{day_gain:,.0f} / ₹{tg_amt:,.0f}</div>', unsafe_allow_html=True)
    st.markdown(f'''
        <div style="background:#003300; border-radius:10px; height:8px; overflow:hidden;">
            <div style="background:linear-gradient(90deg, #10b981, #059669); width:{target_progress * 100}%; height:100%; transition:width 0.3s ease;"></div>
        </div>
    ''', unsafe_allow_html=True)

# Current Bet Display
st.markdown(f'''
    <div style="background:linear-gradient(135deg, #f59e0b20, #f59e0b05); border:2px solid #f59e0b; border-radius:15px; padding:0.6rem; text-align:center; margin:0.8rem 0;">
        <div style="font-size:0.7rem; color:#f59e0b;">💰 CURRENT BET</div>
        <div style="font-size:2rem; font-weight:bold; color:#f59e0b;">₹{st.session_state.bet:,.0f}</div>
    </div>
''', unsafe_allow_html=True)

# Chip Selection
st.markdown('<div style="font-size:0.8rem; font-weight:bold; margin:0.5rem 0;">🎰 PLACE CHIPS</div>', unsafe_allow_html=True)
chip_cols = st.columns(5)
for idx, (col, chip) in enumerate(zip(chip_cols, CHIP_DEFS)):
    with col:
        if st.button(chip['label'], key=f"chip_{chip['coin']}", use_container_width=True):
            new_bet = st.session_state.bet + chip['coin']
            if new_bet <= st.session_state.max_bet:
                st.session_state.bet = new_bet
                auto_save()
                st.rerun()

# Bet Controls
st.markdown('<div style="font-size:0.8rem; font-weight:bold; margin:0.5rem 0 0.3rem 0;">🔧 BET CONTROLS</div>', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🗑 Clear", use_container_width=True):
        st.session_state.bet = 0.0
        auto_save()
        st.rerun()
with col2:
    if st.button("½ Half", use_container_width=True):
        st.session_state.bet = round(st.session_state.bet / 2)
        auto_save()
        st.rerun()
with col3:
    if st.button("×2 Double", use_container_width=True):
        new_bet = st.session_state.bet * 2
        if new_bet <= st.session_state.max_bet:
            st.session_state.bet = new_bet
        auto_save()
        st.rerun()
with col4:
    if st.button("↩️ Undo", use_container_width=True, disabled=st.session_state.last_action is None):
        if st.session_state.last_action:
            for key, value in st.session_state.last_action.items():
                st.session_state[key] = value
            st.session_state.last_action = None
            auto_save()
            st.rerun()

# Win/Loss Buttons
st.markdown('<div style="font-size:0.8rem; font-weight:bold; margin:0.5rem 0 0.3rem 0;">🎯 RECORD RESULT</div>', unsafe_allow_html=True)
bet_ok = st.session_state.bet > 0

col1, col2 = st.columns(2)
with col1:
    if st.button("✅ WIN", use_container_width=True, disabled=not bet_ok):
        st.session_state.last_action = {
            'balance': st.session_state.balance,
            'win_amt': st.session_state.win_amt,
            'wins': st.session_state.wins,
            'trades': st.session_state.trades,
            'bet': st.session_state.bet
        }
        amt = st.session_state.bet
        st.session_state.balance += amt
        st.session_state.win_amt += amt
        st.session_state.wins += 1
        st.session_state.trades += 1
        st.session_state.bet = 0.0
        play_sound('win')
        auto_save()
        st.rerun()
with col2:
    if st.button("❌ LOSS", use_container_width=True, disabled=not bet_ok):
        st.session_state.last_action = {
            'balance': st.session_state.balance,
            'loss_amt': st.session_state.loss_amt,
            'losses': st.session_state.losses,
            'trades': st.session_state.trades,
            'bet': st.session_state.bet
        }
        amt = st.session_state.bet
        st.session_state.balance -= amt
        st.session_state.loss_amt += amt
        st.session_state.losses += 1
        st.session_state.trades += 1
        st.session_state.bet = 0.0
        play_sound('loss')
        auto_save()
        st.rerun()

if not bet_ok:
    st.markdown('<p style="text-align:center; color:#f59e0b; font-size:0.7rem; margin:0.3rem 0;">⚠️ Select chips first</p>', unsafe_allow_html=True)

# Session Notes
with st.expander("📝 Session Notes", expanded=False):
    notes = st.text_area("", value=st.session_state.notes, height=60, key="notes_input", label_visibility="collapsed")
    if notes != st.session_state.notes:
        st.session_state.notes = notes
        auto_save()