import tkinter as tk
from tkinter import ttk, messagebox
import math


# ==========================================
# BACKEND: LOGIC "LEGO BLOCKS"
# ==========================================

def solve_prices_and_rrr(entry, sl, tp, pos_type, target_rrr):
    """
    Block 1: Solves for missing prices. If you want RRR locked, leave TP blank.
    """
    if sl is None:
        raise ValueError("Stop Loss is required to calculate share size.")

    # If TP is missing, calculate it based on the locked Target RRR
    if tp is None:
        risk_per_share = (entry - sl) if pos_type == "Long" else (sl - entry)
        if risk_per_share <= 0:
            raise ValueError("Invalid Stop Loss for this position type.")

        tp = entry + (risk_per_share * target_rrr) if pos_type == "Long" else entry - (risk_per_share * target_rrr)
        rrr = target_rrr  # RRR is locked to your target

    # If user manually enters all three prices, RRR MUST recalculate
    else:
        risk_per_share = (entry - sl) if pos_type == "Long" else (sl - entry)
        reward_per_share = (tp - entry) if pos_type == "Long" else (entry - tp)
        if risk_per_share <= 0:
            raise ValueError("Invalid Stop Loss for this position type.")

        rrr = reward_per_share / risk_per_share

    return sl, tp, rrr


def calculate_max_shares(balance, risk_pct, entry, sl, pos_type):
    """
    Block 2: STRICTLY solves for maximum shares based on fixed risk %.
    Take Profit/RRR is ignored here because it doesn't affect purchasing power.
    """
    if risk_pct is None or risk_pct <= 0:
        raise ValueError("A valid Risk % is required.")

    risk_amount = balance * (risk_pct / 100)
    risk_per_share = (entry - sl) if pos_type == "Long" else (sl - entry)

    # Maximize shares within risk parameter
    shares = math.floor(risk_amount / risk_per_share)

    return shares, risk_amount, risk_per_share


# ==========================================
# BACKEND: THE ORCHESTRATOR
# ==========================================

def solve_trade_parameters(balance, pos_type, risk_pct, entry, sl, tp, target_rrr=2.0):
    """
    The Orchestrator: Notice 'shares' is no longer passed as an input.
    It is strictly a calculated output now.
    """
    if entry is None:
        raise ValueError("Entry Price is always required.")
    if sl is None:
        raise ValueError("Stop Loss Price is always required to size a position.")

    # 1. Lock RRR and find Exit (if Exit is blank)
    sl, tp, actual_rrr = solve_prices_and_rrr(entry, sl, tp, pos_type, target_rrr)

    # 2. Maximize Share Size based on Risk %
    shares, risk_amount, risk_per_share = calculate_max_shares(balance, risk_pct, entry, sl, pos_type)

    # 3. Calculate final reward metrics
    reward_per_share = (tp - entry) if pos_type == "Long" else (entry - tp)

    return {
        "risk_pct": round(risk_pct, 2),
        "entry": round(entry, 2),
        "sl": round(sl, 2),
        "tp": round(tp, 2),
        "shares": int(shares),
        "risk_amount": risk_amount,
        "risk_per_share": risk_per_share,
        "reward_per_share": reward_per_share,
        "rrr": round(actual_rrr, 2)
    }
# ==========================================
# FRONTEND: GUI APPLICATION
# ==========================================

class TradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto-Populating Position Sizer")
        self.root.geometry("400x550")
        self.root.configure(padx=20, pady=20)

        # --- Variables (StringVars allow for empty/blank inputs) ---
        self.balance_var = tk.StringVar(value="10000")
        self.pos_type_var = tk.StringVar(value="Long")

        # Inputs that can be left blank
        self.risk_pct_var = tk.StringVar(value="1.0")
        self.shares_var = tk.StringVar(value="")
        self.entry_var = tk.StringVar()
        self.stop_loss_var = tk.StringVar()
        self.take_profit_var = tk.StringVar(value="")

        # New default RRR setting
        self.rrr_target_var = tk.StringVar(value="2.0")

        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self.root, text="Account Setup", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.create_input_row("Account Balance ($):", self.balance_var)
        self.create_input_row("Target RRR (Default):", self.rrr_target_var)

        ttk.Separator(self.root, orient='horizontal').pack(fill='x', pady=10)

        ttk.Label(self.root, text="Trade Setup (Leave missing fields blank)", font=("Arial", 10, "bold")).pack(
            anchor="w", pady=(0, 5))

        # Position Type Dropdown
        frame = ttk.Frame(self.root)
        frame.pack(fill='x', pady=2)
        ttk.Label(frame, text="Position Type:", width=18).pack(side='left')
        ttk.Combobox(frame, textvariable=self.pos_type_var, values=["Long", "Short"], state="readonly").pack(
            side='left', fill='x', expand=True)

        self.create_input_row("Entry Price ($):", self.entry_var)
        self.create_input_row("Stop Loss ($):", self.stop_loss_var)
        self.create_input_row("Take Profit ($):", self.take_profit_var)

        ttk.Separator(self.root, orient='horizontal').pack(fill='x', pady=5)

        self.create_input_row("Risk %:", self.risk_pct_var)
        ttk.Label(self.root, text="-- OR --", foreground="gray").pack(pady=2)
        self.create_input_row("Shares to Buy:", self.shares_var)

        # Action Button
        ttk.Button(self.root, text="Calculate & Auto-Fill", command=self.process_trade).pack(pady=15, fill='x')

        # Output Section
        self.result_text = tk.Text(self.root, height=7, state='disabled', bg="#f0f0f0", font=("Courier", 10))
        self.result_text.pack(fill='both', expand=True)

    def create_input_row(self, label_text, variable):
        frame = ttk.Frame(self.root)
        frame.pack(fill='x', pady=2)
        ttk.Label(frame, text=label_text, width=18).pack(side='left')
        ttk.Entry(frame, textvariable=variable).pack(side='left', fill='x', expand=True)

    def parse_float(self, string_var):
        """Helper to convert string input to float, or return None if empty."""
        val = string_var.get().strip()
        if not val:
            return None
        try:
            return float(val)
        except ValueError:
            raise ValueError(f"Invalid number format: '{val}'")

    def process_trade(self):
        try:
            # 1. Safely gather inputs (Converts empty strings to None)
            balance = self.parse_float(self.balance_var)
            pos_type = self.pos_type_var.get()
            target_rrr = self.parse_float(self.rrr_target_var) or 2.0

            risk_pct = self.parse_float(self.risk_pct_var)
            shares = self.parse_float(self.shares_var)
            entry = self.parse_float(self.entry_var)
            sl = self.parse_float(self.stop_loss_var)
            tp = self.parse_float(self.take_profit_var)

            # 2. Execute Backend Solver
            solved = solve_trade_parameters(balance, pos_type, risk_pct, entry, sl, tp, target_rrr)

            # 3. Auto-populate the GUI fields with the solved data
            self.risk_pct_var.set(str(solved['risk_pct']))
            self.entry_var.set(str(solved['entry']))
            self.stop_loss_var.set(str(solved['sl']))
            self.take_profit_var.set(str(solved['tp']))
            self.shares_var.set(str(solved['shares']))

            # 4. Format Output Text
            total_cost = solved['shares'] * solved['entry']

            output = f"Total Risked:   ${solved['risk_amount']:,.2f}\n"
            output += f"Capital Needed: ${total_cost:,.2f}\n"
            output += "-" * 25 + "\n"
            output += f"Risk/Share:     ${solved['risk_per_share']:.2f}\n"
            output += f"Reward/Share:   ${solved['reward_per_share']:.2f}\n"
            output += f"R/R Ratio:      1 : {solved['rrr']:.2f}\n"

            if solved['rrr'] < target_rrr:
                output += f"\nWARNING: RRR is below target ({target_rrr})"

            self.result_text.config(state='normal')
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, output)
            self.result_text.config(state='disabled')

        except ValueError as e:
            messagebox.showerror("Math Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")


# ==========================================
# APP LAUNCHER
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = TradingApp(root)
    root.mainloop()