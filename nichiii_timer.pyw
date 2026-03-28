import tkinter as tk
from tkinter import ttk, messagebox
import time
import json
import os
import platform
from pathlib import Path
import re
import sys

import pygame
from pynput import mouse

if platform.system() == "Windows":
    import winsound
else:
    import subprocess

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_path()
STATE_FILE = os.path.join(BASE_DIR, "timer_state.json")
CLICK_SOUND = resource_path("click.wav")
PENCIL_SOUND_FILE = resource_path("pencil_drag.wav")

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
pencil_sound = None
mouse_listener = None
pencil_sound_enabled = True

def load_pencil_sound():
    global pencil_sound
    if Path(PENCIL_SOUND_FILE).exists():
        try:
            pencil_sound = pygame.mixer.Sound(PENCIL_SOUND_FILE)
            return True
        except:
            return False
    return False

def on_mouse_click(x, y, button, pressed):
    if pencil_sound is None or not pencil_sound_enabled:
        return
    if button == mouse.Button.left:
        if pressed and not pygame.mixer.get_busy():
            pencil_sound.play(loops=-1)
        elif not pressed:
            pencil_sound.stop()

def toggle_pencil_sound():
    global mouse_listener
    if pencil_sound_enabled:
        if pencil_sound is None:
            status_label.config(text="No pencil sound file!", foreground="red")
            return
        status_label.config(text="Pencil Sound: ON  (hold pen while drawing)", foreground="#00bcd4")
        if mouse_listener is None or not mouse_listener.running:
            mouse_listener = mouse.Listener(on_click=on_mouse_click)
            mouse_listener.start()
    else:
        status_label.config(text="Pencil Sound: OFF", foreground="#e53935")
        if pencil_sound:
            pencil_sound.stop()
        if mouse_listener and mouse_listener.running:
            mouse_listener.stop()

class CostTimer:
    def __init__(self, root, hourly_rate, currency="₱", elapsed_time=0.0, break_time=0.0, 
                 running=None, saved_simple_mode=True, saved_pencil_enabled=True, saved_pencil_volume=0.35):
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

        self.pencil_enabled = bool(saved_pencil_enabled)
        global pencil_sound_enabled
        pencil_sound_enabled = self.pencil_enabled

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

        self.simple_frame = ttk.Frame(root)
        self.simple_frame.pack(fill="both", expand=True)

        work_row = ttk.Frame(self.simple_frame)
        work_row.pack(pady=(12, 4))
        self.work_play_btn = ttk.Button(work_row, text="▶", width=2, command=self.toggle_work)
        self.work_play_btn.pack(side="left", padx=(0, 8))
        self.work_label = ttk.Label(work_row, text="00:00:00", font=("Consolas", 18, "bold"), foreground="#00bcd4")
        self.work_label.pack(side="left")
        self.top_btn = ttk.Button(work_row, text="📌", width=2, command=self.toggle_topmost)
        self.top_btn.pack(side="left", padx=(8, 0))

        break_row = ttk.Frame(self.simple_frame)
        break_row.pack(pady=(6, 6))
        self.break_play_btn = ttk.Button(break_row, text="▶", width=2, command=self.toggle_break)
        self.break_play_btn.pack(side="left", padx=(0, 8))
        self.break_label = ttk.Label(break_row, text="00:00:00", font=("Consolas", 18, "bold"), foreground="#e53935")
        self.break_label.pack(side="left")
        self.mode_btn = ttk.Button(break_row, text="🌗", width=2, command=self.toggle_mode)
        self.mode_btn.pack(side="left", padx=(8, 0))

        self.cost_label = ttk.Label(self.simple_frame, text=f"Cost: 0.00 {self.currency}",
                                    font=("Segoe UI", 13, "bold"), foreground="#e0e0e0")
        self.cost_label.pack(pady=(4, 10))

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

        rate_row = ttk.Frame(center_frame)
        ttk.Label(rate_row, text="Hourly Rate:").pack(side="left", padx=5)
        self.rate_var = tk.StringVar(value=f"{self.hourly_rate:.2f} {self.currency}")
        self.rate_entry = ttk.Entry(rate_row, textvariable=self.rate_var, width=15, justify="center")
        self.rate_entry.pack(side="left")
        self.save_btn = ttk.Button(rate_row, text="💾", command=self.update_rate)
        self.save_btn.pack(side="left", padx=5)
        rate_row.pack(pady=4)

        self.total_time_label = ttk.Label(center_frame, text="Total Time: 00:00:00")
        self.total_time_label.pack(pady=4)

        btn_row = ttk.Frame(center_frame)
        btn_row.pack(pady=8)
        self.reset_btn = ttk.Button(btn_row, text="🔄", width=3, command=self.reset_all)
        self.reset_btn.pack(side="left", padx=5)
        self.tick_btn = ttk.Button(btn_row, text="🔈", width=3, command=self.toggle_tick_sound)
        self.tick_btn.pack(side="left", padx=5)

        pencil_frame = ttk.LabelFrame(center_frame, text="Pencil Sketch Sound (for Clip Studio)", padding=10)
        pencil_frame.pack(pady=10, fill="x")

        self.pencil_toggle_btn = ttk.Button(pencil_frame, text="Toggle Pencil Sound", command=self.toggle_pencil)
        self.pencil_toggle_btn.pack(pady=5)

        global status_label
        status_label = ttk.Label(pencil_frame, text="", foreground="#00bcd4")
        status_label.pack(pady=5)

        ttk.Label(pencil_frame, text="Volume:").pack(anchor="w")
        self.volume_var = tk.DoubleVar(value=saved_pencil_volume)
        self.volume_slider = ttk.Scale(pencil_frame, from_=0.0, to=1.0, orient="horizontal",
                                       variable=self.volume_var, command=self.change_pencil_volume)
        self.volume_slider.pack(fill="x", pady=5)

        if pencil_sound:
            toggle_pencil_sound()
        else:
            status_label.config(text="Sound file missing", foreground="red")

        self.work_start = time.time() - self.work_elapsed if self.running.get("work") else None
        self.break_start = time.time() - self.break_elapsed if self.running.get("break") else None

        self.update_timer()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.show_mode(self.simple_mode)

    def toggle_pencil(self):
        self.pencil_enabled = not self.pencil_enabled
        global pencil_sound_enabled
        pencil_sound_enabled = self.pencil_enabled
        toggle_pencil_sound()

    def change_pencil_volume(self, val):
        global pencil_sound
        if pencil_sound:
            pencil_sound.set_volume(float(val))

    def update_rate(self):
        text = self.rate_var.get().strip()
        match = re.match(r"([\d,.]+)\s*([A-Za-z₱$€¥]*)", text)
        if not match:
            messagebox.showerror("Invalid", "Enter a number followed by optional currency")
            return
        num, cur = match.groups()
        try:
            self.hourly_rate = float(num.replace(",", ""))
            self.currency = cur if cur else self.currency
        except ValueError:
            messagebox.showerror("Invalid", "Could not parse hourly rate.")
            return

        self.save_state()
        messagebox.showinfo("Saved", "Settings saved")

    def toggle_work(self):
        if self.running.get("break"): self.toggle_break()
        if self.running.get("work"):
            self.running["work"] = False
            self.work_elapsed = time.time() - self.work_start
        else:
            self.running["work"] = True
            self.work_start = time.time() - self.work_elapsed
        self.update_buttons()

    def toggle_break(self):
        if self.running.get("work"): self.toggle_work()
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
        for b in [self.work_play_btn, self.fm_work_play_btn]: b.config(text=wp)
        for b in [self.break_play_btn, self.fm_break_play_btn]: b.config(text=bp)

    def toggle_tick_sound(self):
        self.sound_enabled = not self.sound_enabled
        self.tick_btn.config(text="🔈" if self.sound_enabled else "🔇")

    def play_tick(self):
        if not self.sound_enabled or not Path(CLICK_SOUND).exists():
            return
        try:
            if platform.system() == "Windows":
                winsound.PlaySound(CLICK_SOUND, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except:
            pass

    def update_timer(self):
        now = time.time()
        if self.running.get("work"):
            self.work_elapsed = now - self.work_start
        if self.running.get("break"):
            self.break_elapsed = now - self.break_start

        def fmt(sec): return f"{int(sec//3600):02}:{int(sec%3600//60):02}:{int(sec%60):02}"

        for lbl in [self.work_label, self.fm_work_label]:
            lbl.config(text=fmt(self.work_elapsed))
        for lbl in [self.break_label, self.fm_break_label]:
            lbl.config(text=fmt(self.break_elapsed))

        total_seconds = int(self.work_elapsed + self.break_elapsed)
        if total_seconds != getattr(self, "last_second", 0):
            self.last_second = total_seconds
            if self.running.get("work") or self.running.get("break"):
                self.play_tick()

        self.total_time_label.config(text=f"Total Time: {fmt(total_seconds)}")

        cost = (self.hourly_rate / 3600) * self.work_elapsed
        cost_str = f"Cost: {cost:,.2f} {self.currency}"
        self.cost_label.config(text=cost_str)
        self.fm_cost_label.config(text=cost_str)

        self.root.after(200, self.update_timer)

    def reset_all(self):
        self.running = {"work": False, "break": False}
        self.work_elapsed = self.break_elapsed = 0.0
        self.update_buttons()

    def toggle_mode(self):
        self.simple_mode = not self.simple_mode
        self.show_mode(self.simple_mode)

    def show_mode(self, simple):
        if simple:
            self.full_frame.pack_forget()
            self.simple_frame.pack(fill="both", expand=True)
        else:
            self.simple_frame.pack_forget()
            self.full_frame.pack(fill="both", expand=True)

    def toggle_topmost(self):
        state = not self.stay_on_top.get()
        self.stay_on_top.set(state)
        self.root.attributes("-topmost", state)

    def save_state(self):
        data = {
            "hourly_rate": self.hourly_rate,
            "currency": self.currency,
            "work_elapsed": self.work_elapsed,
            "break_elapsed": self.break_elapsed,
            "running": self.running,
            "pencil_enabled": self.pencil_enabled,
            "pencil_volume": self.volume_var.get()
        }
        try:
            with open(STATE_FILE, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print("Save failed:", e)

    def on_close(self):
        self.save_state()
        if pencil_sound:
            pencil_sound.stop()
        if mouse_listener and mouse_listener.running:
            mouse_listener.stop()
        self.root.destroy()

def main():
    load_pencil_sound()
    state = load_state()

    root = tk.Tk()
    app = CostTimer(
        root,
        hourly_rate=state.get("hourly_rate", 100),
        currency=state.get("currency", "₱"),
        elapsed_time=state.get("work_elapsed", 0.0),
        break_time=state.get("break_elapsed", 0.0),
        running=state.get("running", {"work": False, "break": False}),
        saved_simple_mode=True,
        saved_pencil_enabled=state.get("pencil_enabled", True),
        saved_pencil_volume=state.get("pencil_volume", 0.35)
    )

    root.mainloop()

if __name__ == "__main__":
    main()