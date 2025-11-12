import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import time
import json
import os
import platform
from pathlib import Path
import re

if platform.system() == "Windows":
    import winsound
else:
    import subprocess

STATE_FILE = "timer_state.json"
CLICK_SOUND = "click.wav"


class CostTimer:
    def __init__(self, root, hourly_rate, currency="₱", elapsed_time=0.0, break_time=0.0, running=None, saved_simple_mode=True):
        self.root = root
        self.root.title("Nichiii Timer")
        self.root.configure(bg="#1e1e1e")
        self.root.attributes("-topmost", True)

        self.hourly_rate = hourly_rate
        self.currency = currency
        self.work_elapsed = elapsed_time
        self.break_elapsed = break_time
        self.running = running if running else {"work": False, "break": False}
        self.simple_mode = bool(saved_simple_mode)
        self.stay_on_top = tk.BooleanVar(value=True)
        self.sound_enabled = True
        self.last_second = 0

        # ---- Style ----
        style = ttk.Style()
        style.theme_use("clam")
        accent_bg = "#2d2d30"
        hover_bg = "#3a3a3d"
        fg_light = "#e0e0e0"
        style.configure("TFrame", background="#1e1e1e")
        style.configure("TButton", font=("Segoe UI", 10), padding=6,
                        background=accent_bg, foreground=fg_light, relief="flat")
        style.map("TButton", background=[("active", hover_bg)])
        style.configure("TLabel", background="#1e1e1e", foreground=fg_light, font=("Segoe UI", 11))

        # ---- SIMPLE MODE ----
        self.simple_frame = ttk.Frame(root)
        self.simple_frame.pack(fill="both", expand=True)

        # Work timer row
        work_row = ttk.Frame(self.simple_frame)
        work_row.pack(pady=(12, 4))
        self.work_play_btn = ttk.Button(work_row, text="▶", width=2, command=self.toggle_work)
        self.work_play_btn.pack(side="left", padx=(0, 8))
        self.work_label = ttk.Label(work_row, text="00:00:00", font=("Consolas", 18, "bold"), foreground="#00bcd4")
        self.work_label.pack(side="left")
        self.top_btn = ttk.Button(work_row, text="📌", width=2, command=self.toggle_topmost)
        self.top_btn.pack(side="left", padx=(8, 0))

        # Break timer row
        break_row = ttk.Frame(self.simple_frame)
        break_row.pack(pady=(6, 6))
        self.break_play_btn = ttk.Button(break_row, text="▶", width=2, command=self.toggle_break)
        self.break_play_btn.pack(side="left", padx=(0, 8))
        self.break_label = ttk.Label(break_row, text="00:00:00", font=("Consolas", 18, "bold"), foreground="#e53935")
        self.break_label.pack(side="left")
        self.mode_btn = ttk.Button(break_row, text="🌗", width=2, command=self.toggle_mode)
        self.mode_btn.pack(side="left", padx=(8, 0))

        # Cost
        self.cost_label = ttk.Label(self.simple_frame, text=f"Cost: 0.00 {self.currency}",
                                    font=("Segoe UI", 13, "bold"), foreground="#e0e0e0")
        self.cost_label.pack(pady=(4, 10))

        # ---- FULL MODE ----
        self.full_frame = ttk.Frame(root)

        fm_work_row = ttk.Frame(self.full_frame)
        fm_work_row.pack(pady=(12, 4))
        self.fm_work_play_btn = ttk.Button(fm_work_row, text="▶", width=2, command=self.toggle_work)
        self.fm_work_play_btn.pack(side="left", padx=(0, 8))
        self.fm_work_label = ttk.Label(fm_work_row, text="00:00:00", font=("Consolas", 18, "bold"), foreground="#00bcd4")
        self.fm_work_label.pack(side="left")
        self.fm_top_btn = ttk.Button(fm_work_row, text="📌", width=2, command=self.toggle_topmost)
        self.fm_top_btn.pack(side="left", padx=(8, 0))

        fm_break_row = ttk.Frame(self.full_frame)
        fm_break_row.pack(pady=(6, 10))
        self.fm_break_play_btn = ttk.Button(fm_break_row, text="▶", width=2, command=self.toggle_break)
        self.fm_break_play_btn.pack(side="left", padx=(0, 8))
        self.fm_break_label = ttk.Label(fm_break_row, text="00:00:00", font=("Consolas", 18, "bold"), foreground="#e53935")
        self.fm_break_label.pack(side="left")
        self.fm_mode_btn = ttk.Button(fm_break_row, text="🌗", width=2, command=self.toggle_mode)
        self.fm_mode_btn.pack(side="left", padx=(8, 0))

        self.fm_cost_label = ttk.Label(self.full_frame, text=f"Cost: 0.00 {self.currency}",
                                       font=("Segoe UI", 13, "bold"), foreground="#e0e0e0")
        self.fm_cost_label.pack(pady=(4, 10))

        center_frame = ttk.Frame(self.full_frame)
        center_frame.pack(pady=8)

        # Hourly Rate (with currency)
        rate_row = ttk.Frame(center_frame)
        ttk.Label(rate_row, text="Hourly Rate:").pack(side="left", padx=5)
        self.rate_var = tk.StringVar(value=f"{self.hourly_rate:.2f} {self.currency}")
        self.rate_entry = ttk.Entry(rate_row, textvariable=self.rate_var, width=15, justify="center")
        self.rate_entry.pack(side="left")
        ttk.Button(rate_row, text="💾", command=self.update_rate).pack(side="left", padx=5)
        rate_row.pack(pady=4)

        # Total time
        self.total_time_label = ttk.Label(center_frame, text="Total Time: 00:00:00")
        self.total_time_label.pack(pady=4)

        # Reset & Tick buttons
        btn_row = ttk.Frame(center_frame)
        btn_row.pack(pady=8)
        self.reset_btn = ttk.Button(btn_row, text="🔄", width=3, command=self.reset_all)
        self.reset_btn.pack(side="left", padx=5)
        self.tick_btn = ttk.Button(btn_row, text="🔈", width=3, command=self.toggle_tick_sound)
        self.tick_btn.pack(side="left", padx=5)

        # ---- INIT ----
        self.work_start = time.time() - self.work_elapsed if self.running.get("work") else None
        self.break_start = time.time() - self.break_elapsed if self.running.get("break") else None

        self.update_timer()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.show_mode(self.simple_mode)

    # ---- TIMER LOGIC ----
    def toggle_work(self):
        if self.running.get("break"):
            self.toggle_break()
        if self.running.get("work"):
            self.running["work"] = False
            self.work_elapsed = time.time() - self.work_start
        else:
            self.running["work"] = True
            self.work_start = time.time() - self.work_elapsed
        self.update_buttons()

    def toggle_break(self):
        if self.running.get("work"):
            self.toggle_work()
        if self.running.get("break"):
            self.running["break"] = False
            self.break_elapsed = time.time() - self.break_start
        else:
            self.running["break"] = True
            self.break_start = time.time() - self.break_elapsed
        self.update_buttons()

    def update_buttons(self):
        wp = "⏸" if self.running.get("work") else "▶"
        bp = "⏸" if self.running.get("break") else "▶"
        for b in [self.work_play_btn, self.fm_work_play_btn]:
            b.config(text=wp)
        for b in [self.break_play_btn, self.fm_break_play_btn]:
            b.config(text=bp)

    def toggle_tick_sound(self):
        self.sound_enabled = not self.sound_enabled
        icon = "🔈" if self.sound_enabled else "🔇"
        self.tick_btn.config(text=icon)

    def play_tick(self):
        if not self.sound_enabled or not Path(CLICK_SOUND).exists():
            return
        try:
            if platform.system() == "Windows":
                winsound.PlaySound(CLICK_SOUND, winsound.SND_FILENAME | winsound.SND_ASYNC)
            elif platform.system() == "Darwin":
                subprocess.run(["afplay", CLICK_SOUND], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["aplay", CLICK_SOUND], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def update_timer(self):
        now = time.time()
        if self.running.get("work"):
            self.work_elapsed = now - self.work_start
        if self.running.get("break"):
            self.break_elapsed = now - self.break_start

        def fmt(sec): return f"{int(sec//3600):02}:{int(sec%3600//60):02}:{int(sec%60):02}"
        work_t, break_t = fmt(self.work_elapsed), fmt(self.break_elapsed)

        for lbl in [self.work_label, self.fm_work_label]:
            lbl.config(text=work_t)
        for lbl in [self.break_label, self.fm_break_label]:
            lbl.config(text=break_t)

        total_seconds = int(self.work_elapsed + self.break_elapsed)
        if total_seconds != self.last_second:
            self.last_second = total_seconds
            if self.running.get("work") or self.running.get("break"):
                self.play_tick()

        total_time = fmt(total_seconds)
        self.total_time_label.config(text=f"Total Time: {total_time}")

        cost = (self.hourly_rate / 3600) * self.work_elapsed
        cost_str = f"Cost: {cost:,.2f} {self.currency}"
        self.cost_label.config(text=cost_str)
        self.fm_cost_label.config(text=cost_str)

        self.save_state()
        self.root.after(200, self.update_timer)

    def reset_all(self):
        self.running = {"work": False, "break": False}
        self.work_elapsed = self.break_elapsed = 0.0
        self.update_buttons()
        for lbl in [self.work_label, self.break_label, self.fm_work_label, self.fm_break_label]:
            lbl.config(text="00:00:00")
        for lbl in [self.cost_label, self.fm_cost_label]:
            lbl.config(text=f"Cost: 0.00 {self.currency}")
        self.total_time_label.config(text="Total Time: 00:00:00")
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)

    # ---- UI ----
    def toggle_mode(self):
        self.simple_mode = not self.simple_mode
        self.show_mode(self.simple_mode)

    def show_mode(self, simple):
        if simple:
            self.full_frame.pack_forget()
            self.simple_frame.pack(fill="both", expand=True)
            self.root.update_idletasks()
            w, h = self.simple_frame.winfo_reqwidth(), self.simple_frame.winfo_reqheight()
            self.root.geometry(f"{w+30}x{h+30}")
        else:
            self.simple_frame.pack_forget()
            self.full_frame.pack(fill="both", expand=True)
            self.root.update_idletasks()
            w, h = self.full_frame.winfo_reqwidth(), self.full_frame.winfo_reqheight()
            self.root.geometry(f"{w+60}x{h+60}")

    def toggle_topmost(self):
        state = not self.stay_on_top.get()
        self.stay_on_top.set(state)
        self.root.attributes("-topmost", state)
        icon = "📌" if state else "📍"
        for b in [self.top_btn, self.fm_top_btn]:
            b.config(text=icon)

    def update_rate(self):
        text = self.rate_var.get().strip()
        match = re.match(r"([\d,.]+)\s*([A-Za-z₱$€¥]*)", text)
        if not match:
            messagebox.showerror("Invalid", "Enter a number followed by optional currency (e.g. 100 USD)")
            return
        num, cur = match.groups()
        try:
            self.hourly_rate = float(num.replace(",", ""))
            self.currency = cur if cur else self.currency
            self.fm_cost_label.config(text=f"Cost: 0.00 {self.currency}")
            self.cost_label.config(text=f"Cost: 0.00 {self.currency}")
        except ValueError:
            messagebox.showerror("Invalid", "Could not parse hourly rate.")

    # ---- STATE ----
    def save_state(self):
        data = {
            "hourly_rate": self.hourly_rate,
            "currency": self.currency,
            "work_elapsed": self.work_elapsed,
            "break_elapsed": self.break_elapsed,
            "running": self.running,
            "simple_mode": self.simple_mode
        }
        with open(STATE_FILE, "w") as f:
            json.dump(data, f)

    def on_close(self):
        self.save_state()
        self.root.destroy()


def load_state():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def main():
    saved = load_state()
    temp_root = tk.Tk()
    temp_root.withdraw()
    if saved:
        hourly_rate = saved.get("hourly_rate", 0.0)
        currency = saved.get("currency", "₱")
        work_elapsed = saved.get("work_elapsed", 0.0)
        break_elapsed = saved.get("break_elapsed", 0.0)
        running = saved.get("running", {"work": False, "break": False})
        simple_mode = saved.get("simple_mode", True)
    else:
        while True:
            try:
                rate = simpledialog.askstring("Hourly Rate", "Enter your hourly rate (e.g., 100 ₱ or 50 USD):")
                if rate is None:
                    temp_root.destroy()
                    return
                m = re.match(r"([\d,.]+)\s*([A-Za-z₱$€¥]*)", rate.strip())
                if not m:
                    raise ValueError
                hourly_rate = float(m.group(1).replace(",", ""))
                currency = m.group(2) if m.group(2) else "₱"
                break
            except ValueError:
                messagebox.showerror("Invalid", "Please enter a valid number and optional currency.")
        work_elapsed = break_elapsed = 0.0
        running = {"work": False, "break": False}
        simple_mode = True

    temp_root.destroy()
    root = tk.Tk()
    app = CostTimer(root, hourly_rate, currency, work_elapsed, break_elapsed, running, simple_mode)
    root.mainloop()


if __name__ == "__main__":
    main()
