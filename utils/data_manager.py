import pandas as pd
import os
from datetime import date

class DataManager:
    def __init__(self, csv_file="stake_history.csv"):
        self.csv_file = csv_file

    def load_csv(self):
        """Load existing CSV or create empty dataframe"""
        if os.path.exists(self.csv_file):
            return pd.read_csv(self.csv_file)
        return pd.DataFrame(columns=[
            "date", "start_bal", "stop_pct", "target_pct", "stop_amt", "target_amt",
            "trades", "wins", "losses", "win_amt", "loss_amt", "net", "result",
            "notes", "session_number", "sessions_played"
        ])

    def save_row(self, data):
        """Save a single session's data to CSV"""
        df = self.load_csv()
        today = str(date.today())

        # Add new row for this session
        new_row = pd.DataFrame([{"date": today, **data}])
        df = pd.concat([df, new_row], ignore_index=True)

        # Save to CSV
        df.to_csv(self.csv_file, index=False)