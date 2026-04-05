import pandas as pd
import os
from datetime import date


class DataManager:
    """Handles CSV persistence for session history."""

    COLUMNS = [
        "date", "start_bal", "stop_pct", "target_pct", "stop_amt", "target_amt",
        "trades", "banker_wins", "player_wins", "losses",
        "win_amt", "loss_amt", "net", "result",
        "notes", "session_number", "final_balance",
    ]

    def __init__(self, csv_file: str = "stake_history.csv"):
        self.csv_file = csv_file

    def load_csv(self) -> pd.DataFrame:
        """Load existing CSV or return an empty DataFrame with correct columns."""
        if os.path.exists(self.csv_file):
            try:
                df = pd.read_csv(self.csv_file)
                # BUG FIX: ensure all expected columns exist (safe against old files)
                for col in self.COLUMNS:
                    if col not in df.columns:
                        df[col] = None
                return df[self.COLUMNS]
            except Exception:
                pass
        return pd.DataFrame(columns=self.COLUMNS)

    def save_row(self, data: dict):
        """Append a single completed session row to the CSV."""
        df  = self.load_csv()
        row = {"date": str(date.today()), **data}
        # BUG FIX: original code referenced 'wins' column that didn't exist
        # Now uses banker_wins + player_wins which matches COLUMNS above
        new = pd.DataFrame([{col: row.get(col) for col in self.COLUMNS}])
        df  = pd.concat([df, new], ignore_index=True)
        df.to_csv(self.csv_file, index=False)

    def get_summary(self) -> dict:
        """Return quick stats across all saved sessions."""
        df = self.load_csv()
        if df.empty:
            return {}
        return {
            "total_sessions": len(df),
            "total_net":      df["net"].sum(),
            "avg_net":        df["net"].mean(),
            "win_sessions":   int((df["net"] > 0).sum()),
            "loss_sessions":  int((df["net"] < 0).sum()),
        }