import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import serial
import serial.tools.list_ports
import threading
import time
from datetime import datetime
import math
import random
import os

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.style as mplstyle

# --- Theme Definitions ---
THEMES = {
  "dark": {
    "BG": "#1e1e1e", "PANEL": "#2d2d2d", "TEXT": "#ffffff", 
    "ACCENT": "#007acc", "GRAPH_BG": "#252526", "GRID": "#444444"
  },
  "light": {
    "BG": "#f0f0f0", "PANEL": "#ffffff", "TEXT": "#000000", 
    "ACCENT": "#005a9e", "GRAPH_BG": "#e8e8e8", "GRID": "#cccccc"
  },
  "orange": {
    "BG": "#1a1614", "PANEL": "#2b231f", "TEXT": "#f5f5f5", 
    "ACCENT": "#ff7300", "GRAPH_BG": "#241d1a", "GRID": "#4a3b34"
  },
  "green": {
    "BG": "#0f1712", "PANEL": "#18261d", "TEXT": "#e8f5ed", 
    "ACCENT": "#00b347", "GRAPH_BG": "#131f17", "GRID": "#274031"
  }
}
SUCCESS_COLOR = "#4caf50"
WARNING_COLOR = "#ff9800"
ERROR_COLOR = "#f44336"

# ==========================================
# EASTER EGG : ORCHIDEFENSE
# ==========================================
class Orchidefense(tk.Toplevel):
  def __init__(self, master):
    super().__init__(master)
    self.title("Orchidéfense - Top Secret Project")
    self.geometry("800x850")
    self.configure(bg="#111")
    self.resizable(False, False)
    
    self.ts = 40 # Tile size
    self.cols, self.rows = 15, 15
    
    self.state = "CHAR_SELECT" # CHAR_SELECT, PLAYING, GAMEOVER, VICTORY
    self.player_char = None
    self.coins = 75
    self.wave = 1
    self.max_waves = 10
    self.orchids_hp = 1000
    self.orchids_max_hp = 1000
    
    # Path generation (irregular)
    self.path = [(0,2), (1,2), (2,2), (3,2), (3,3), (3,4), (4,4), (5,4), (6,4), (7,4), (7,5), (8,5), (9,5), (10,5), (11,5), (11,6), (11,7), (11,8), (10,8), (9,8), (8,8), (7,8), (7,9), (7,10), (7,11), (7,12), (7,13), (7,14)]
    
    self.towers = []
    self.enemies = []
    self.projectiles = []
    self.max_towers = 10
    
    self.selected_tower_type = None
    self.selected_existing_tower = None
    
    self.images = {}
    self.load_assets()
    self.build_ui()
    self.game_loop_id = None
    
    self.spawn_queue = []
    self.spawn_timer = 0
    
    # Balance data
    self.tower_data = {
      "RES": {"name": "Résistance", "cost": 50, "limit": 99, "range": 100, "dmg": 20, "cooldown": 30, "color": "#ff5555", "desc": "Arc électrique. Upgrades dispo."},
      "COND": {"name": "Condensateur", "cost": 75, "limit": 99, "range": 120, "dmg": 45, "cooldown": 50, "color": "#5555ff", "desc": "Arc puissant. Upgrades dispo."},
      "TMP": {"name": "TMP102", "cost": 125, "limit": 3, "range": 80, "dmg": 5, "cooldown": 5, "color": "#ffaa00", "desc": "Lance-flammes AoE."},
      "OLED": {"name": "OLED I2C", "cost": 150, "limit": 2, "range": 150, "dmg": 0, "cooldown": 100, "color": "#aaaaaa", "desc": "Flashbang. Ralentit en zone."},
      "BUZZ": {"name": "Buzzer", "cost": 80, "limit": 2, "range": 90, "dmg": 10, "cooldown": 60, "color": "#ff00ff", "desc": "Etourdit les ennemis."},
      "PT100": {"name": "PT100", "cost": 150, "limit": 3, "range": 100, "dmg": 5, "cooldown": 80, "color": "#00ffff", "desc": "Gèle l'ennemi ciblé."},
      "ESP": {"name": "ESP32", "cost": 1250, "limit": 1, "range": 999, "dmg": 0, "cooldown": 999, "color": "#222222", "desc": "Buff: +25% Vitesse de tir."},
      "MAX": {"name": "MAX31865", "cost": 1250, "limit": 1, "range": 999, "dmg": 0, "cooldown": 999, "color": "#444444", "desc": "Buff: +25% Dégâts globaux."}
    }
    
  def load_assets(self):
    # Fallback to pure Tkinter shapes if PNGs are missing. Tries to load silently.
    files = ["char_christophe.png", "char_eleonore.png", "char_dumestre.png", "char_marine.png"]
    for f in files:
      try: self.images[f] = tk.PhotoImage(file=f)
      except: self.images[f] = None

  def build_ui(self):
    self.canvas = tk.Canvas(self, width=600, height=600, bg="#2a2a2a", highlightthickness=0)
    self.canvas.pack(pady=10)
    self.canvas.bind("<Button-1>", self.on_map_click)
    
    self.top_bar = tk.Frame(self, bg="#111")
    self.top_bar.pack(fill="x", padx=20)
    self.lbl_stats = tk.Label(self.top_bar, text="", font=("Consolas", 14, "bold"), fg="#fff", bg="#111")
    self.lbl_stats.pack(side="left")
    self.lbl_wave = tk.Label(self.top_bar, text="", font=("Consolas", 14, "bold"), fg="#ff7300", bg="#111")
    self.lbl_wave.pack(side="right")
    
    self.bot_bar = tk.Frame(self, bg="#222", height=100)
    self.bot_bar.pack(fill="both", expand=True, padx=20, pady=10)
    
    self.show_char_select()

  def show_char_select(self):
    self.canvas.delete("all")
    self.canvas.create_text(300, 100, text="SÉLECTION DU PERSONNEL", fill="#fff", font=("Consolas", 24, "bold"))
    chars = [
      ("Christophe", "10% Défense Base", "#4caf50", "char_christophe.png"),
      ("Eléonore", "10% Vitesse de tir", "#00bcd4", "char_eleonore.png"),
      ("Dumestre", "10% Dégâts supp.", "#f44336", "char_dumestre.png"),
      ("Marine", "10% Pièces supp.", "#ffeb3b", "char_marine.png")
    ]
    for i, (name, atout, col, img) in enumerate(chars):
      x = 100 + (i * 133)
      self.canvas.create_rectangle(x-50, 250, x+50, 350, fill=col, tags=f"char_{name}")
      self.canvas.create_text(x, 370, text=name, fill="#fff", font=("Consolas", 12, "bold"))
      self.canvas.create_text(x, 390, text=atout, fill="#aaa", font=("Segoe UI", 9))
      self.canvas.tag_bind(f"char_{name}", "<Button-1>", lambda e, n=name: self.start_game(n))

  def start_game(self, char_name):
    self.player_char = char_name
    self.state = "PLAYING"
    if char_name == "Christophe": self.orchids_hp = 1100; self.orchids_max_hp = 1100
    self.build_shop()
    self.load_wave()
    self.update_game()

  def build_shop(self):
    for widget in self.bot_bar.winfo_children(): widget.destroy()
    
    for key, data in self.tower_data.items():
      btn = tk.Button(self.bot_bar, text=f"{data['name']}\n{data['cost']}p", bg=data['color'], fg="#fff", font=("Consolas", 8, "bold"),
              command=lambda k=key: self.select_shop_item(k))
      btn.pack(side="left", padx=5, fill="y", expand=True)

  def select_shop_item(self, key):
    self.selected_tower_type = key
    self.canvas.config(cursor="crosshair")

  def get_buffs(self):
    # Calculate global modifiers
    speed_mod = 0.9 if self.player_char == "Eléonore" else 1.0
    dmg_mod = 1.1 if self.player_char == "Dumestre" else 1.0
    
    esp_present = any(t['type'] == "ESP" for t in self.towers)
    max_present = any(t['type'] == "MAX" for t in self.towers)
    jimmy_alive = any(e['type'] == "Jimmy" for e in self.enemies)
    
    if esp_present:
      speed_mod *= 1.1 if jimmy_alive else 0.75 # Lower is faster cooldown
    if max_present:
      dmg_mod *= 0.9 if jimmy_alive else 1.25
      
    return speed_mod, dmg_mod

  def load_wave(self):
    self.enemies.clear()
    self.projectiles.clear()
    
    # Gradual difficulty predefined
    wave_templates = {
      1: [("Flux", 5), ("Mails", 5)],
      2: [("Mails", 10), ("Etain", 3)],
      3: [("Mails", 15), ("Lampe", 2)],
      4: [("Flux", 10), ("Etain", 10)],
      5: [("Frigo", 1), ("Mails", 10)],
      6: [("Resine", 1), ("Etain", 5), ("Flux", 5)],
      7: [("Frigo", 2), ("Lampe", 5), ("Mails", 5)],
      8: [("Resine", 2), ("Frigo", 1), ("Etain", 15)],
      9: [("Frigo", 3), ("Resine", 3), ("Lampe", 10)],
      10: [("Jimmy", 1), ("Robin", 1)]
    }
    
    q = []
    for e_type, count in wave_templates.get(self.wave, []):
      for _ in range(count): q.append(e_type)
    random.shuffle(q)
    self.spawn_queue = q

  def spawn_enemy(self, e_type):
    stats = {
      "Frigo": {"hp": 200, "spd": 1.0, "reward": 100, "col": "#fff"},
      "Mails": {"hp": 25, "spd": 2.5, "reward": 10, "col": "#888"},
      "Lampe": {"hp": 35, "spd": 2.5, "reward": 25, "col": "#ff0"},
      "Resine": {"hp": 600, "spd": 0.8, "reward": 500, "col": "#a0522d"},
      "Etain": {"hp": 50, "spd": 3.5, "reward": 25, "col": "#ccc"},
      "Flux": {"hp": 15, "spd": 5.0, "reward": 10, "col": "#0ff"},
      "Jimmy": {"hp": 10000, "spd": 0.5, "reward": 0, "col": "#800080"},
      "Robin": {"hp": 10000, "spd": 0.5, "reward": 0, "col": "#008000"}
    }
    st = stats[e_type]
    self.enemies.append({
      "type": e_type, "hp": st["hp"], "max_hp": st["hp"], "spd": st["spd"], 
      "reward": st["reward"], "col": st["col"],
      "path_idx": 0, "x": self.path[0][0]*self.ts + self.ts/2, "y": self.path[0][1]*self.ts + self.ts/2,
      "frozen": 0
    })

  def on_map_click(self, event):
    if self.state != "PLAYING": return
    gx, gy = event.x // self.ts, event.y // self.ts
    
    # Check existing tower
    for i, t in enumerate(self.towers):
      if t['gx'] == gx and t['gy'] == gy:
        self.show_tower_menu(i)
        return
        
    # Placement
    if self.selected_tower_type:
      if (gx, gy) in self.path:
        messagebox.showwarning("Erreur", "Impossible de placer sur le chemin.")
        return
      if len(self.towers) >= self.max_towers:
        messagebox.showwarning("Limite", "10 tours maximum sur la carte !")
        self.selected_tower_type = None; self.canvas.config(cursor="")
        return
      
      t_data = self.tower_data[self.selected_tower_type]
      count = sum(1 for t in self.towers if t['type'] == self.selected_tower_type)
      if count >= t_data['limit']:
        messagebox.showwarning("Limite", f"Limite atteinte pour {t_data['name']}.")
        return
      if self.coins < t_data['cost']:
        messagebox.showwarning("Fonds", "Pièces insuffisantes.")
        return
        
      self.coins -= t_data['cost']
      self.towers.append({
        "type": self.selected_tower_type, "gx": gx, "gy": gy,
        "x": gx*self.ts + self.ts/2, "y": gy*self.ts + self.ts/2,
        "cd": 0, "tier": 1, "value_idx": 0
      })
      self.selected_tower_type = None
      self.canvas.config(cursor="")

  def show_tower_menu(self, t_idx):
    t = self.towers[t_idx]
    d = self.tower_data[t['type']]
    sell_price = d['cost'] // 2
    
    menu = tk.Menu(self, tearoff=0)
    menu.add_command(label=f"Stats: {d['name']} T{t['tier']}")
    menu.add_command(label=f"Dégâts de base: {d['dmg']}")
    
    # Upgrade logic for RES and COND
    if t['type'] in ["RES", "COND"]:
      vals = ["120Ω", "1kΩ", "5kΩ", "10kΩ", "20kΩ"] if t['type'] == "RES" else ["10pF", "100nF", "1µF", "47µF", "220µF"]
      if t['value_idx'] < len(vals) - 1:
        up_cost = 50 * (t['value_idx'] + 1)
        menu.add_command(label=f"Améliorer ({vals[t['value_idx']+1]}) - {up_cost}p", 
                command=lambda: self.upgrade_tower(t_idx, up_cost))
    
    menu.add_separator()
    menu.add_command(label=f"Vendre ({sell_price}p)", command=lambda: self.sell_tower(t_idx, sell_price))
    menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())

  def upgrade_tower(self, t_idx, cost):
    if self.coins >= cost:
      self.coins -= cost
      self.towers[t_idx]['value_idx'] += 1
      self.towers[t_idx]['tier'] += 1
    else:
      messagebox.showwarning("Fonds", "Pas assez de pièces.")

  def sell_tower(self, t_idx, price):
    self.coins += price
    self.towers.pop(t_idx)

  def draw(self):
    self.canvas.delete("all")
    
    # Draw path
    for px, py in self.path:
      self.canvas.create_rectangle(px*self.ts, py*self.ts, (px+1)*self.ts, (py+1)*self.ts, fill="#444", outline="#333")
      
    # Draw base (Orchids)
    bx, by = self.path[-1]
    self.canvas.create_rectangle(bx*self.ts, by*self.ts, (bx+1)*self.ts, (by+1)*self.ts, fill="#ff00ff")
    self.canvas.create_text(bx*self.ts+20, by*self.ts+20, text="BASE", font=("Consolas", 8, "bold"))
      
    # Draw Towers
    for t in self.towers:
      d = self.tower_data[t['type']]
      self.canvas.create_rectangle(t['x']-15, t['y']-15, t['x']+15, t['y']+15, fill=d['color'])
      self.canvas.create_text(t['x'], t['y'], text=t['type'][:3], font=("Consolas", 8, "bold"), fill="#fff")
      if t['tier'] > 1:
        self.canvas.create_text(t['x'], t['y']-20, text=f"T{t['tier']}", fill="#fff")

    # Draw Enemies
    for e in self.enemies:
      sz = 15 if e['type'] in ["Jimmy", "Robin", "Resine"] else 10
      self.canvas.create_oval(e['x']-sz, e['y']-sz, e['x']+sz, e['y']+sz, fill=e['col'])
      # HP Bar
      hp_pct = max(0, e['hp'] / e['max_hp'])
      self.canvas.create_rectangle(e['x']-10, e['y']-sz-5, e['x']-10+(20*hp_pct), e['y']-sz-2, fill="#0f0")

    # Draw Projectiles
    for p in self.projectiles:
      self.canvas.create_line(p['x1'], p['y1'], p['x2'], p['y2'], fill=p['col'], width=2)
      
    # UI
    self.lbl_stats.config(text=f"Pièces: {self.coins} | Orchidées HP: {self.orchids_hp}/{self.orchids_max_hp} | Tours: {len(self.towers)}/10")
    self.lbl_wave.config(text=f"Vague {self.wave}/{self.max_waves}")

  def update_game(self):
    if self.state != "PLAYING": return
    
    speed_mod, dmg_mod = self.get_buffs()
    
    # Mails & Lampe UV Synergy Check
    has_mails = any(e['type'] == "Mails" for e in self.enemies)
    has_lampe = any(e['type'] == "Lampe" for e in self.enemies)
    if has_mails and has_lampe:
      for e in self.enemies:
        if e['type'] in ["Mails", "Lampe"] and e['max_hp'] < 50:
          e['max_hp'] = 50
          e['hp'] += 15 # Heal slightly when buffed

    has_resine = any(e['type'] == "Resine" for e in self.enemies)
    
    # Spawning
    self.spawn_timer -= 1
    if self.spawn_timer <= 0 and self.spawn_queue:
      self.spawn_enemy(self.spawn_queue.pop(0))
      self.spawn_timer = 20 # frames between spawns
      
    # Towers attacking
    self.projectiles.clear()
    pt100_active_on = []
    
    for t in self.towers:
      d = self.tower_data[t['type']]
      t['cd'] -= 1
      
      # Frigo debuff
      near_frigo = any(e['type'] == "Frigo" and math.dist((e['x'], e['y']), (t['x'], t['y'])) < 100 for e in self.enemies)
      if near_frigo and t['cd'] > 0: t['cd'] += 0.5
      
      # Action
      if t['cd'] <= 0:
        in_range = [e for e in self.enemies if math.dist((e['x'], e['y']), (t['x'], t['y'])) <= d['range']]
        if in_range:
          target = in_range[0] # simple first target
          
          # Special actions
          if t['type'] in ["ESP", "MAX"]: continue # Passive
          
          base_dmg = d['dmg'] * dmg_mod
          if t['type'] in ["RES", "COND"]: base_dmg *= t['tier']
          
          # Boss Robin immunity
          if t['type'] == "RES" and target['type'] == "Robin": base_dmg = 0
          if t['type'] == "TMP" and target['type'] == "Robin": base_dmg *= 1.5
          
          # Boss Jimmy PT100 debuff logic
          if target['type'] == "Jimmy" and t['type'] == "PT100":
            pt100_active_on.append("Jimmy")

          if target['type'] == "Jimmy" and "Jimmy" in pt100_active_on:
            base_dmg *= 1.25 # takes 25% more from all while near PT100
            
          # Resine protection
          if has_resine and target['type'] != "Frigo" and target['type'] != "Resine":
            base_dmg *= 0.8
          
          if t['type'] == "OLED":
            target['spd'] *= 0.5 # Slow
          elif t['type'] == "PT100":
            target['frozen'] = 30 # frames frozen
          elif t['type'] == "BUZZ":
            target['frozen'] = 10
          
          target['hp'] -= base_dmg
          
          # Visuals
          self.projectiles.append({'x1': t['x'], 'y1': t['y'], 'x2': target['x'], 'y2': target['y'], 'col': d['color']})
          
          t['cd'] = d['cooldown'] * speed_mod

    # Enemies logic
    survivors = []
    for e in self.enemies:
      if e['hp'] <= 0:
        reward = e['reward']
        if self.player_char == "Marine": reward = int(reward * 1.1)
        self.coins += reward
        continue
        
      if e['frozen'] > 0:
        e['frozen'] -= 1
      else:
        # Move towards next path node
        if e['path_idx'] < len(self.path) - 1:
          tx, ty = self.path[e['path_idx']+1][0]*self.ts + self.ts/2, self.path[e['path_idx']+1][1]*self.ts + self.ts/2
          dist = math.dist((e['x'], e['y']), (tx, ty))
          if dist < e['spd']:
            e['path_idx'] += 1
          else:
            dx, dy = (tx - e['x'])/dist, (ty - e['y'])/dist
            e['x'] += dx * e['spd']
            e['y'] += dy * e['spd']
        else:
          # Reached base
          self.orchids_hp -= 50 if e['type'] not in ["Jimmy", "Robin"] else 500
          continue # Die at base
      
      survivors.append(e)
      
    self.enemies = survivors
    
    # Win / Loss condition
    if self.orchids_hp <= 0:
      self.state = "GAMEOVER"
    elif not self.enemies and not self.spawn_queue:
      if self.wave < self.max_waves:
        self.wave += 1
        self.load_wave()
      else:
        self.state = "VICTORY"

    self.draw()
    
    if self.state == "PLAYING":
      self.after(50, self.update_game) # 20 FPS loop
    elif self.state == "GAMEOVER":
      self.canvas.create_rectangle(0, 200, 600, 400, fill="#000")
      self.canvas.create_text(300, 300, text="LES ORCHIDÉES SONT DÉTRUITES\nECHEC DE LA MISSION", fill="#f00", font=("Consolas", 20, "bold"), justify="center")
    elif self.state == "VICTORY":
      self.canvas.create_rectangle(0, 200, 600, 400, fill="#000")
      self.canvas.create_text(300, 300, text="VICTOIRE !\nROBIN & JIMMY ONT ÉTÉ VAINCUS", fill="#0f0", font=("Consolas", 20, "bold"), justify="center")

# ==========================================
# BASE APPLICATION (ESPConfigurator)
# ==========================================
class ESPConfigurator:
  def __init__(self, root):
    self.root = root
    self.root.title("FFA TERMINAL - MONITORING SYSTEM")
    self.root.geometry("900x850")
    
    # Volatile RAM Settings (Resets on close)
    self.app_settings = {
      "theme": "dark",
      "auto_connect": False,
      "export_dir": "",
      "glossary": {
        "PHONE_1": {"name": "GRIMAUD Régis", "number": "+33613861642"},
        "PHONE_2": {"name": "LAUGA Béatrice", "number": "+33676891109"},
        "PHONE_3": {"name": "LAUREAU CRAVO Cristiana", "number": "+33687245307"},
        "PHONE_4": {"name": "GONI Marisol", "number": "+33668813860"},
        "PHONE_5": {"name": "ATTARD Éléonore", "number": "+33618956261"},
        "PHONE_6": {"name": "GRIMBERT Jimmy", "number": "+33785198897"},
        "PHONE_7": {"name": "PANIAGUA DESCLAUX Robin", "number": "+33761650411"},
        "PHONE_8": {"name": "Dispatcheur 8", "number": "+33000000008"},
        "PHONE_9": {"name": "Dispatcheur 9", "number": "+33000000009"},
        "PHONE_10": {"name": "Dispatcheur 10", "number": "+33000000010"}
      }
    }
    
    self.current_theme = THEMES[self.app_settings["theme"]]
    self.root.configure(bg=self.current_theme["BG"])

    # Connection vars
    self.serial_port = None
    self.is_connected = False
    self.is_recovering = False 
    self.last_connected_port = None
    self.last_pong = 0
    self.is_graphing = False
    
    # Logging vars
    self.log_times, self.log_pt100, self.log_tmp102 = [], [], []
    
    # Core variables matching ESP32 C++
    self.sys_variables = [
      "TARGET_FREEZER", "TIME_TO_SLEEP", "PT100_CRITICAL", "TMP102_CRITICAL", 
      "PT100_TOO_COLD", "TMP102_TOO_COLD", "PT100_TOO_HOT", "TMP102_TOO_HOT"
    ]
    self.phone_variables = [f"PHONE_{i}" for i in range(1, 11)]
    
    self.entries = {}
    self.modem_ui = {}
    self.diag_labels = {}
    self.glossary_entries = {}

    self.apply_styles()
    self.setup_ui()

  def apply_styles(self):
    style = ttk.Style()
    style.theme_use('clam')
    t = self.current_theme
    
    style.configure("TFrame", background=t["BG"])
    style.configure("TLabelframe", background=t["BG"], foreground=t["ACCENT"], bordercolor=t["PANEL"])
    style.configure("TLabelframe.Label", background=t["BG"], foreground=t["ACCENT"], font=("Segoe UI", 10, "bold"))
    style.configure("TLabel", background=t["BG"], foreground=t["TEXT"], font=("Segoe UI", 9))
    style.configure("Status.TLabel", background=t["BG"], foreground=ERROR_COLOR, font=("Segoe UI", 10, "bold"))
    style.configure("TButton", background=t["PANEL"], foreground=t["TEXT"], borderwidth=1, font=("Segoe UI", 9, "bold"))
    style.map("TButton", background=[("active", t["ACCENT"])])
    style.configure("Action.TButton", background=t["ACCENT"], foreground="#ffffff" if t["ACCENT"] != "#00b347" else "#ffffff")
    
    style.configure("TNotebook", background=t["BG"], borderwidth=0)
    style.configure("TNotebook.Tab", background=t["PANEL"], foreground=t["TEXT"], padding=[10, 5], font=("Segoe UI", 10, "bold"))
    style.map("TNotebook.Tab", background=[("selected", t["ACCENT"])], foreground=[("selected", "#ffffff")])

    self.root.configure(bg=t["BG"])
    
    for entry in self.entries.values():
      if isinstance(entry, tk.Entry):
        entry.config(bg=t["PANEL"], fg=t["TEXT"], insertbackground=t["TEXT"])
    for name_entry, num_entry in self.glossary_entries.values():
      if isinstance(name_entry, tk.Entry):
        name_entry.config(bg=t["PANEL"], fg=t["TEXT"], insertbackground=t["TEXT"])
        num_entry.config(bg=t["PANEL"], fg=t["TEXT"], insertbackground=t["TEXT"])

    if hasattr(self, 'console'):
      self.console.config(bg=t["PANEL"], fg=t["TEXT"])
    if hasattr(self, 'mini_console'):
      self.mini_console.config(bg=t["PANEL"], fg=t["TEXT"])
      
    if hasattr(self, 'ax'):
      self.fig.patch.set_facecolor(t["BG"])
      self.ax.set_facecolor(t["GRAPH_BG"])
      self.ax.set_ylabel("Temperature (°C)", color=t["TEXT"])
      self.ax.tick_params(axis='y', colors=t["TEXT"])
      self.ax.grid(color=t["GRID"], linestyle='--', linewidth=0.5)
      self.canvas.draw()

  def setup_ui(self):
    conn_frame = ttk.LabelFrame(self.root, text=" 🔌 Connection Hub ", padding=10)
    conn_frame.pack(fill="x", padx=15, pady=5)

    self.port_var = tk.StringVar()
    self.port_combo = ttk.Combobox(conn_frame, textvariable=self.port_var, width=15)
    self.port_combo.pack(side="left", padx=5)
    
    ttk.Button(conn_frame, text="Refresh", command=self.refresh_ports).pack(side="left", padx=5)
    ttk.Button(conn_frame, text="⚡ Auto-Detect", command=self.auto_detect_port).pack(side="left", padx=5)
    self.btn_connect = ttk.Button(conn_frame, text="Connect to ESP", command=self.toggle_connection, style="Action.TButton")
    self.btn_connect.pack(side="left", padx=5)

    self.status_label = ttk.Label(conn_frame, text="● OFFLINE", style="Status.TLabel")
    self.status_label.pack(side="right", padx=10)
    self.refresh_ports()

    self.notebook = ttk.Notebook(self.root)
    self.notebook.pack(fill="both", expand=True, padx=15, pady=5)

    self.tab_config = ttk.Frame(self.notebook)
    self.tab_glossary = ttk.Frame(self.notebook)
    self.tab_modem = ttk.Frame(self.notebook)
    self.tab_graph = ttk.Frame(self.notebook)
    self.tab_diag = ttk.Frame(self.notebook)
    self.tab_settings = ttk.Frame(self.notebook)
    self.tab_credits = ttk.Frame(self.notebook)
    self.tab_terminal = ttk.Frame(self.notebook)

    self.notebook.add(self.tab_config, text=" ⚙️ Core Config ")
    self.notebook.add(self.tab_glossary, text=" 📖 Glossary & Dispatch ")
    self.notebook.add(self.tab_modem, text=" 📡 Modem ")
    self.notebook.add(self.tab_graph, text=" 📈 Telemetry ")
    self.notebook.add(self.tab_diag, text=" 🛠️ Diag ")
    self.notebook.add(self.tab_settings, text=" ⚙️ App Settings ")
    self.notebook.add(self.tab_credits, text=" ℹ️ Credits ")
    self.notebook.add(self.tab_terminal, text=" 🖥️ Terminal ")

    self.build_config_tab()
    self.build_glossary_tab()
    self.build_modem_tab()
    self.build_graph_tab()
    self.build_diagnosis_tab()
    self.build_settings_tab()
    self.build_credits_tab()
    self.build_terminal_tab()
    
    mini_frame = ttk.LabelFrame(self.root, text=" Live Status ", padding=5)
    mini_frame.pack(fill="x", padx=15, pady=(0, 10), side="bottom")
    
    self.mini_console = tk.Text(mini_frame, height=5, bg=self.current_theme["PANEL"], fg=self.current_theme["TEXT"], font=("Consolas", 9, "bold"), borderwidth=0, state="disabled")
    self.mini_console.pack(fill="x")

  def build_terminal_tab(self):
    self.console = scrolledtext.ScrolledText(self.tab_terminal, bg=self.current_theme["PANEL"], fg=self.current_theme["TEXT"], font=("Consolas", 10), borderwidth=0)
    self.console.pack(fill="both", expand=True, padx=10, pady=10)

  def build_config_tab(self):
    var_frame = ttk.LabelFrame(self.tab_config, text=" Hardware Thresholds & Vars ", padding=15)
    var_frame.pack(fill="x", pady=5, padx=10)

    for i, var in enumerate(self.sys_variables):
      row, col = i // 2, (i % 2) * 2   
      ttk.Label(var_frame, text=var).grid(row=row, column=col, sticky="e", pady=10, padx=5)
      entry = tk.Entry(var_frame, width=22, bg=self.current_theme["PANEL"], fg=self.current_theme["TEXT"], insertbackground=self.current_theme["TEXT"], borderwidth=0, font=("Consolas", 10))
      entry.grid(row=row, column=col+1, sticky="w", pady=10, padx=10, ipady=3)
      self.entries[var] = entry

    btn_frame = ttk.Frame(self.tab_config)
    btn_frame.pack(fill="x", pady=10, padx=10)
    ttk.Button(btn_frame, text="📥 Pull Sys Config from ESP", command=lambda: self.send_command("GET_CONFIG")).pack(side="left", expand=True, fill="x", padx=5)
    ttk.Button(btn_frame, text="📤 Push Sys Config to ESP", command=lambda: self.write_config(self.sys_variables)).pack(side="left", expand=True, fill="x", padx=5)

  def build_glossary_tab(self):
    frame = ttk.LabelFrame(self.tab_glossary, text=" Contact Address Book (Volatile RAM) ", padding=15)
    frame.pack(fill="both", expand=True, pady=5, padx=10)

    ttk.Label(frame, text="Node ID", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", padx=5, pady=5)
    ttk.Label(frame, text="Contact Name (Display Only)", font=("Segoe UI", 9, "bold")).grid(row=0, column=1, sticky="w", padx=5, pady=5)
    ttk.Label(frame, text="Phone Number (Synced to ESP)", font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky="w", padx=5, pady=5)

    for i, var in enumerate(self.phone_variables):
      ttk.Label(frame, text=var).grid(row=i+1, column=0, sticky="w", pady=5, padx=5)
      
      name_entry = tk.Entry(frame, width=30, bg=self.current_theme["PANEL"], fg=self.current_theme["TEXT"], insertbackground=self.current_theme["TEXT"], borderwidth=0, font=("Segoe UI", 10))
      name_entry.insert(0, self.app_settings["glossary"][var]["name"])
      name_entry.grid(row=i+1, column=1, sticky="w", pady=5, padx=5, ipady=3)
      
      num_entry = tk.Entry(frame, width=22, bg=self.current_theme["PANEL"], fg=self.current_theme["TEXT"], insertbackground=self.current_theme["TEXT"], borderwidth=0, font=("Consolas", 10))
      num_entry.insert(0, self.app_settings["glossary"][var]["number"])
      num_entry.grid(row=i+1, column=2, sticky="w", pady=5, padx=5, ipady=3)
      
      self.glossary_entries[var] = (name_entry, num_entry)
      self.entries[var] = num_entry 

    btn_frame = ttk.Frame(self.tab_glossary)
    btn_frame.pack(fill="x", pady=10, padx=10)
    ttk.Button(btn_frame, text="💾 Save to RAM (Temp)", command=self.save_glossary_local).pack(side="left", expand=True, fill="x", padx=5)
    ttk.Button(btn_frame, text="📥 Pull Numbers from ESP", command=lambda: self.send_command("GET_CONFIG")).pack(side="left", expand=True, fill="x", padx=5)
    ttk.Button(btn_frame, text="📤 Push Numbers to ESP", command=lambda: self.write_config(self.phone_variables)).pack(side="left", expand=True, fill="x", padx=5)

  def save_glossary_local(self):
    for var, (name_entry, num_entry) in self.glossary_entries.items():
      self.app_settings["glossary"][var]["name"] = name_entry.get().strip()
      self.app_settings["glossary"][var]["number"] = num_entry.get().strip()
    self.log("Glossary updated in volatile memory (will reset on close).")
    messagebox.showinfo("Temp Save", "Address book updated in memory.\nDon't forget to 'Push' if you want these numbers saved to the ESP32 hardware.")

  def build_modem_tab(self):
    metrics = [("RSSI", "Overall Signal Strength"), ("RSRP", "True LTE Signal Power"), ("RSRQ", "Signal Quality"), ("SINR", "Signal-to-Interference Ratio")]
    for code, desc in metrics:
      frame = ttk.LabelFrame(self.tab_modem, text=f" [ {code} ] - {desc} ", padding=10)
      frame.pack(fill="x", pady=5, padx=10)
      
      dot = tk.Label(frame, text="●", font=("Segoe UI", 24), bg=self.current_theme["BG"], fg="#555555")
      dot.pack(side="left", padx=10)
      
      val_label = ttk.Label(frame, text="WAITING...", font=("Consolas", 16, "bold"))
      val_label.pack(side="left", padx=10)
      
      desc_label = ttk.Label(frame, text="Awaiting active cellular connection.", font=("Segoe UI", 10, "italic"), foreground="#aaaaaa")
      desc_label.pack(side="left", padx=20)
      
      self.modem_ui[code] = {"dot": dot, "val": val_label, "desc": desc_label}
      
    btn_frame = ttk.Frame(self.tab_modem)
    btn_frame.pack(fill="x", pady=15, padx=10)
    ttk.Button(btn_frame, text="📡 Request Network Diagnostics", command=lambda: self.send_command("POLL_NET")).pack(side="top", pady=5)

  def build_graph_tab(self):
    ctrl_frame = ttk.Frame(self.tab_graph)
    ctrl_frame.pack(fill="x", pady=10, padx=10)
    
    self.btn_graph = ttk.Button(ctrl_frame, text="▶ Start Logging", command=self.toggle_graph, style="Action.TButton")
    self.btn_graph.pack(side="left", padx=5)
    
    ttk.Button(ctrl_frame, text="💾 Export .TXT", command=self.export_data).pack(side="right", padx=5)
    ttk.Button(ctrl_frame, text="🗑 Clear", command=self.clear_data).pack(side="right", padx=5)

    self.fig = Figure(figsize=(5, 3), dpi=100)
    self.ax = self.fig.add_subplot(111)
    self.canvas = FigureCanvasTkAgg(self.fig, master=self.tab_graph)
    self.canvas.get_tk_widget().pack(fill="both", expand=True, pady=5, padx=10)
    
    self.stats_label = ttk.Label(self.tab_graph, text="PT100: -- °C | TMP102: -- °C | V_BAT: -- V", font=("Consolas", 12, "bold"))
    self.stats_label.pack(pady=5)
    
    self.apply_styles()

  def build_diagnosis_tab(self):
    frame = ttk.LabelFrame(self.tab_diag, text=" Remote Hardware Status ", padding=15)
    frame.pack(fill="x", pady=10, padx=10)

    for i, item in enumerate(["PT100 Probe", "Ambient Probe", "SIM800/7600 Modem", "SIM Card Status"]):
      ttk.Label(frame, text=f"{item}:").grid(row=i, column=0, sticky="w", pady=5)
      lbl = ttk.Label(frame, text="WAITING...", font=("Consolas", 10, "bold"), foreground="#aaaaaa")
      lbl.grid(row=i, column=1, sticky="w", pady=5, padx=10)
      self.diag_labels[item] = lbl

    btn_frame = ttk.Frame(self.tab_diag)
    btn_frame.pack(fill="x", pady=10, padx=10)

    ttk.Button(btn_frame, text="🔍 Run Remote Hardware Diagnostics", command=lambda: self.send_command("RUN_DIAG")).pack(fill="x", pady=5)
    ttk.Button(btn_frame, text="✉️ Force Test SMS Dispatch", command=lambda: self.send_command("TEST_SMS")).pack(fill="x", pady=5)
    ttk.Button(btn_frame, text="🔄 Soft Reboot ESP32", command=lambda: self.send_command("REBOOT")).pack(fill="x", pady=5)

  def build_settings_tab(self):
    frame = ttk.LabelFrame(self.tab_settings, text=" Temporary Session Settings ", padding=15)
    frame.pack(fill="both", expand=True, pady=10, padx=10)
    
    ttk.Label(frame, text="UI Theme:").grid(row=0, column=0, sticky="w", pady=10)
    self.theme_var = tk.StringVar(value=self.app_settings["theme"])
    theme_combo = ttk.Combobox(frame, textvariable=self.theme_var, values=["dark", "light", "orange", "green"], state="readonly", width=15)
    theme_combo.grid(row=0, column=1, sticky="w", pady=10, padx=10)
    theme_combo.bind("<<ComboboxSelected>>", self.change_theme)

    ttk.Label(frame, text="Log Export Dir:").grid(row=1, column=0, sticky="w", pady=10)
    self.export_dir_lbl = ttk.Label(frame, text=self.app_settings.get("export_dir", "Default (Current Folder)"), foreground=self.current_theme["ACCENT"])
    self.export_dir_lbl.grid(row=1, column=1, sticky="w", pady=10, padx=10)
    ttk.Button(frame, text="Change Directory", command=self.change_export_dir).grid(row=1, column=2, sticky="w", padx=10)
    
    ttk.Label(frame, text="(Note: Settings in this tab reset when the application is closed)", font=("Segoe UI", 8, "italic"), foreground="#aaaaaa").grid(row=2, column=0, columnspan=3, pady=20)

  def build_credits_tab(self):
    main_frame = ttk.Frame(self.tab_credits)
    main_frame.pack(fill="both", expand=True, pady=15, padx=20)

    # EASTER EGG TRIGGER: Bind double-click to the main title
    title_lbl = tk.Label(main_frame, text="FFA TERMINAL", font=("Consolas", 28, "bold"), bg=self.current_theme["BG"], fg=self.current_theme["ACCENT"])
    title_lbl.pack(pady=(10, 0))
    title_lbl.bind("<Double-Button-1>", lambda e: Orchidefense(self.root))
    
    sub_lbl = tk.Label(main_frame, text="Asset Environment Monitoring System", font=("Segoe UI", 12, "italic"), bg=self.current_theme["BG"], fg=self.current_theme["TEXT"])
    sub_lbl.pack(pady=(0, 20))
    
    # Invisible Button Trigger (Another way)
    btn_secret = tk.Button(main_frame, text=" ", command=lambda: Orchidefense(self.root), bg=self.current_theme["BG"], activebackground=self.current_theme["BG"], bd=0, relief="flat", highlightthickness=0)
    btn_secret.pack(pady=0)

    ack_frame = ttk.LabelFrame(main_frame, text=" Project Acknowledgements & Entities ", padding=15)
    ack_frame.pack(fill="x", pady=10)

    acks = [
      ("Developer", "GRIMBERT Jimmy"),
      ("Lycée St CRICQ", "Initiated the 6-weeks internship."),
      ("UPPA", "Université de Pau et des Pays de l'Adour: Accepted the internship."),
      ("IPREM", "Institut des Sciences Analytiques et de Physico-Chimie pour l'Environnement et les Matériaux: Provided both equipment and guidance for the project."),
      ("IBEAS", "Institut de Biologie Environnementale et Agroalimentaire de la Santé: Provided access to the freezers for both testing and deployment of the system.")
    ]

    for role, entity in acks:
      row_frame = tk.Frame(ack_frame, bg=self.current_theme["BG"])
      row_frame.pack(fill="x", pady=5)
      tk.Label(row_frame, text=f"{role}: ", font=("Consolas", 10, "bold"), bg=self.current_theme["BG"], fg=self.current_theme["ACCENT"], width=15, anchor="e").pack(side="left", padx=(0, 10))
      tk.Label(row_frame, text=entity, font=("Segoe UI", 10), bg=self.current_theme["BG"], fg=self.current_theme["TEXT"], justify="left", wraplength=600).pack(side="left")

    tech_frame = ttk.LabelFrame(main_frame, text=" Technical Stack & Profile ", padding=10)
    tech_frame.pack(fill="x", pady=10)
    stack = "Target: Frigo ARN / I2C OLED | Mode: Standalone / Zero-Footprint\nHardware: ESP32 Core + SIM7600 | Firmware: C++ | Interface: Python / Tkinter"
    tk.Label(tech_frame, text=stack, font=("Consolas", 9), justify="center", bg=self.current_theme["BG"], fg="#aaaaaa").pack()

    lic_lbl = tk.Label(main_frame, text="Free to use and distribute under CC BY-NC-SA 4.0 (Non-Commercial)", font=("Segoe UI", 8, "bold"), bg=self.current_theme["BG"], fg="#888888")
    lic_lbl.pack(side="bottom", pady=15)

  def change_theme(self, event=None):
    new_theme = self.theme_var.get()
    self.app_settings["theme"] = new_theme
    self.current_theme = THEMES[new_theme]
    self.apply_styles()

    def update_colors(parent):
      for widget in parent.winfo_children():
        if isinstance(widget, (tk.Label, tk.Frame)):
          try: widget.config(bg=self.current_theme["BG"])
          except: pass
        if isinstance(widget, tk.Label):
          if widget.cget("font") and "bold" in str(widget.cget("font")) and "Consolas" in str(widget.cget("font")):
            widget.config(fg=self.current_theme["ACCENT"])
          elif widget.cget("fg") not in ["#aaaaaa", "#888888"]:
            widget.config(fg=self.current_theme["TEXT"])
        update_colors(widget)

    update_colors(self.tab_credits)
    for metrics in self.modem_ui.values():
      metrics["dot"].config(bg=self.current_theme["BG"])

  def change_export_dir(self):
    new_dir = filedialog.askdirectory(initialdir=self.app_settings.get("export_dir"))
    if new_dir:
      self.app_settings["export_dir"] = new_dir
      self.export_dir_lbl.config(text=new_dir)

  def log(self, msg):
    if hasattr(self, 'console'):
      self.console.config(state="normal")
      self.console.insert("end", f"> {msg}\n")
      self.console.see("end")
      self.console.config(state="disabled")
      
    if hasattr(self, 'mini_console'):
      self.mini_console.config(state="normal")
      self.mini_console.delete(1.0, tk.END)
      ts = datetime.now().strftime('%H:%M:%S')
      self.mini_console.insert("end", f"[{ts}] {msg}\n")
      self.mini_console.config(state="disabled")

  def refresh_ports(self):
    ports = [port.device for port in serial.tools.list_ports.comports()]
    self.port_combo['values'] = ports
    if ports and not self.port_var.get():
      self.port_combo.current(0)

  def auto_detect_port(self):
    if self.is_connected: return
    self.log("Hunting for ESP32 on all active COM ports...")
    ports = [port.device for port in serial.tools.list_ports.comports()]
    for port in ports:
      try:
        s = serial.Serial(port, 115200, timeout=1.5)
        s.write(b"PING\n")
        response = s.readline().decode('utf-8', errors='ignore').strip()
        s.close()
        if response == "PONG":
          self.port_var.set(port)
          self.log(f"Success! ESP32 found on {port}.")
          self.toggle_connection()
          return
      except Exception: continue
    self.log("Auto-Detect: Could not find a responding ESP32.")

  def toggle_connection(self):
    if self.is_connected:
      self.disconnect(manual=True)
    else:
      port = self.port_var.get()
      if not port:
        messagebox.showerror("Error", "Type or select a COM port first.")
        return
      try:
        self.serial_port = serial.Serial(port, 115200, timeout=0.1)
        self.is_connected = True
        self.last_connected_port = port
        self.btn_connect.config(text="Disconnect")
        self.status_label.config(text="● LINKED", foreground=SUCCESS_COLOR)
        self.log(f"Connected to {port}. Awaiting ESP sync...")
        
        threading.Thread(target=self.read_serial_loop, daemon=True).start()
        threading.Thread(target=self.keepalive_loop, daemon=True).start()
      except Exception as e:
        messagebox.showerror("Connection Error", str(e))

  def trigger_auto_recovery(self):
    self.is_connected = False
    self.is_recovering = True
    self.btn_connect.config(text="Connecting...")
    self.status_label.config(text="● RE RECOVERING", foreground=WARNING_COLOR)
    self.log("⚠️ Hardware Drop Detected. Entering Auto-Recovery Mode...")
    if self.serial_port:
      try: self.serial_port.close()
      except: pass
    threading.Thread(target=self.recovery_loop, daemon=True).start()

  def recovery_loop(self):
    attempts = 0
    while self.is_recovering and attempts < 15:
      attempts += 1
      time.sleep(2) 
      try:
        self.serial_port = serial.Serial(self.last_connected_port, 115200, timeout=0.1)
        self.is_connected = True
        self.is_recovering = False
        self.root.after(0, lambda: self.btn_connect.config(text="Disconnect"))
        self.root.after(0, lambda: self.status_label.config(text="● LINKED", foreground=SUCCESS_COLOR))
        self.root.after(0, lambda: self.log(f"✅ Auto-Recovery Successful! Re-linked to {self.last_connected_port}."))
        threading.Thread(target=self.read_serial_loop, daemon=True).start()
        threading.Thread(target=self.keepalive_loop, daemon=True).start()
        return
      except serial.SerialException: pass
    if self.is_recovering:
      self.root.after(0, lambda: self.disconnect(reason="❌ Auto-Recovery Failed.", manual=False))

  def disconnect(self, reason="Disconnected from device.", manual=False):
    self.is_connected = False
    self.is_recovering = False
    self.is_graphing = False
    self.btn_graph.config(text="▶ Start Logging")
    if self.serial_port:
      try: self.serial_port.close()
      except: pass
    self.btn_connect.config(text="Connect to ESP")
    self.status_label.config(text="● OFFLINE", foreground=ERROR_COLOR)
    self.log("User disconnected." if manual else reason)

  def keepalive_loop(self):
    while self.is_connected and not self.is_recovering:
      try:
        self.send_command("POLL_DATA" if self.is_graphing else "PING", silent=True)
        time.sleep(1)
        if time.time() - self.last_pong > 30 and self.last_pong != 0:
          self.root.after(0, self.trigger_auto_recovery)
          break
      except Exception: break

  def read_serial_loop(self):
    self.last_pong = time.time()
    while self.is_connected and not self.is_recovering:
      try:
        if self.serial_port and self.serial_port.in_waiting:
          line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
          if line:
            if line == "PONG": 
              self.last_pong = time.time()
            elif line.startswith("DATA:"):
              self.last_pong = time.time()
              self.parse_telemetry(line)
            elif line.startswith("NET:"):
              self.last_pong = time.time()
              self.parse_network_data(line)
            elif line.startswith("DIAG_RES:"):
              self.last_pong = time.time()
              self.parse_diagnostic_data(line)
            elif line.startswith("SMS_RES:"):
              self.last_pong = time.time()
              res = line.replace("SMS_RES:", "").strip()
              self.root.after(0, lambda r=res: messagebox.showinfo("SMS Test", f"Dispatch Result: {r}"))
            else:
              self.log(f"ESP: {line}")
              self.parse_incoming_config(line)
      except serial.SerialException:
        self.root.after(0, self.trigger_auto_recovery)
        break
      except Exception: break
      time.sleep(0.01)

  def parse_network_data(self, line):
    try:
      parts = line.replace("NET:", "").split(',')
      rssi = int(parts[0].strip())
      rsrp = int(parts[1].strip())
      rsrq = int(parts[2].strip())
      sinr = int(parts[3].strip())
      
      self.root.after(0, lambda: self.update_modem_ui(rssi, rsrp, rsrq, sinr))
    except Exception as e: 
      self.log(f"❌ Parse Error (Network): {e} -> Received: {line}")

  def parse_diagnostic_data(self, line):
    try:
      parts = line.replace("DIAG_RES:", "").split(',')
      if len(parts) >= 4:
        p_err = parts[0].strip()
        a_err = parts[1].strip()
        m_ok = parts[2].strip()
        s_ok = parts[3].strip()
        
        def update_ui():
          self.diag_labels["PT100 Probe"].config(text="ERROR" if p_err == "1" else "OK", foreground=ERROR_COLOR if p_err == "1" else SUCCESS_COLOR)
          self.diag_labels["Ambient Probe"].config(text="ERROR" if a_err == "1" else "OK", foreground=ERROR_COLOR if a_err == "1" else SUCCESS_COLOR)
          self.diag_labels["SIM800/7600 Modem"].config(text="OK" if m_ok == "1" else "ERROR", foreground=SUCCESS_COLOR if m_ok == "1" else ERROR_COLOR)
          self.diag_labels["SIM Card Status"].config(text="READY" if s_ok == "1" else "ERROR", foreground=SUCCESS_COLOR if s_ok == "1" else ERROR_COLOR)
        self.root.after(0, update_ui)
      else:
        self.log(f"❌ Parse Error (Diag): Incomplete data -> {line}")
    except Exception as e: 
      self.log(f"❌ Parse Error (Diag): {e} -> Received: {line}")

  def update_modem_ui(self, rssi, rsrp, rsrq, sinr):
    ui = self.modem_ui
    c_rssi, t_rssi = (SUCCESS_COLOR, f"({rssi} dBm) Excellent") if rssi >= -70 else (WARNING_COLOR, f"({rssi} dBm) Acceptable") if rssi >= -85 else (ERROR_COLOR, f"({rssi} dBm) Terrible")
    ui["RSSI"]["val"].config(text=f"{rssi} dBm"); ui["RSSI"]["dot"].config(fg=c_rssi); ui["RSSI"]["desc"].config(text=t_rssi)

    c_rsrp, t_rsrp = (SUCCESS_COLOR, f"({rsrp} dBm) Good power") if rsrp >= -85 else (WARNING_COLOR, f"({rsrp} dBm) Weak") if rsrp >= -105 else (ERROR_COLOR, f"({rsrp} dBm) Dead zone")
    ui["RSRP"]["val"].config(text=f"{rsrp} dBm"); ui["RSRP"]["dot"].config(fg=c_rsrp); ui["RSRP"]["desc"].config(text=t_rsrp)

    c_rsrq, t_rsrq = (SUCCESS_COLOR, f"({rsrq} dB) Clean signal") if rsrq >= -10 else (WARNING_COLOR, f"({rsrq} dB) Fair quality") if rsrq >= -15 else (ERROR_COLOR, f"({rsrq} dB) High interference")
    ui["RSRQ"]["val"].config(text=f"{rsrq} dB"); ui["RSRQ"]["dot"].config(fg=c_rsrq); ui["RSRQ"]["desc"].config(text=t_rsrq)

    c_sinr, t_sinr = (SUCCESS_COLOR, f"({sinr} dB) Perfect") if sinr >= 13 else (WARNING_COLOR, f"({sinr} dB) Barely beating noise") if sinr >= 0 else (ERROR_COLOR, f"({sinr} dB) Noise is louder")
    ui["SINR"]["val"].config(text=f"{sinr} dB"); ui["SINR"]["dot"].config(fg=c_sinr); ui["SINR"]["desc"].config(text=t_sinr)

  def parse_telemetry(self, line):
    try:
      parts = line.replace("DATA:", "").split(',')
      pt100_val = float(parts[0].strip())
      tmp102_val = float(parts[1].strip())
      bat_val = float(parts[2].strip())
      
      self.log_times.append(datetime.now().strftime('%H:%M:%S'))
      self.log_pt100.append(pt100_val)
      self.log_tmp102.append(tmp102_val)
      self.root.after(0, lambda: self.update_graph_ui(pt100_val, tmp102_val, bat_val))
    except Exception as e: 
      self.log(f"❌ Parse Error (Telemetry): {e} -> Received: {line}")

  def update_graph_ui(self, pt100, tmp102, bat):
    self.stats_label.config(text=f"PT100: {pt100} °C | TMP102: {tmp102} °C | V_BAT: {bat} V")
    if self.is_graphing:
      self.ax.clear()
      self.ax.set_facecolor(self.current_theme["GRAPH_BG"])
      self.ax.grid(color=self.current_theme["GRID"], linestyle='--', linewidth=0.5)
      self.ax.set_ylabel("Temperature (°C)", color=self.current_theme["TEXT"])
      
      self.ax.plot(self.log_times[-60:], self.log_pt100[-60:], color='#00bcd4', label='PT100', linewidth=2)
      self.ax.plot(self.log_times[-60:], self.log_tmp102[-60:], color='#ff9800', label='TMP102', linewidth=2)
      
      legend = self.ax.legend(loc="upper left")
      for text in legend.get_texts(): text.set_color(self.current_theme["TEXT"])
      self.ax.set_xticks([]) 
      self.canvas.draw()

  def toggle_graph(self):
    if not self.is_connected:
      messagebox.showwarning("Warning", "Connect to ESP first.")
      return
    self.is_graphing = not self.is_graphing
    self.btn_graph.config(text="⏹ Stop Logging" if self.is_graphing else "▶ Start Logging", style="TButton" if self.is_graphing else "Action.TButton")
    self.log("Started data polling." if self.is_graphing else "Stopped data polling.")

  def clear_data(self):
    if messagebox.askyesno("Clear Data", "Are you sure?"):
      self.log_times.clear(); self.log_pt100.clear(); self.log_tmp102.clear()
      self.ax.clear()
      self.ax.set_facecolor(self.current_theme["GRAPH_BG"])
      self.canvas.draw()
      self.stats_label.config(text="PT100: -- °C | TMP102: -- °C | V_BAT: -- V")

  def export_data(self):
    if not self.log_times:
      messagebox.showinfo("Export", "No data to export.")
      return
      
    initial_dir = self.app_settings.get("export_dir")
    if not initial_dir or initial_dir == "Default (Current Folder)":
      initial_dir = None
      
    filepath = filedialog.asksaveasfilename(
      initialdir=initial_dir,
      defaultextension=".txt", 
      filetypes=[("Text File", "*.txt"), ("CSV File", "*.csv")],
      initialfile=f"FFA_Log_{datetime.now().strftime('%Y%m%d_%H%M')}"
    )
    if filepath:
      try:
        with open(filepath, 'w') as f:
          f.write("Time,PT100_C,TMP102_C\n")
          for t, p, a in zip(self.log_times, self.log_pt100, self.log_tmp102): f.write(f"{t},{p},{a}\n")
        messagebox.showinfo("Success", f"Data exported to:\n{filepath}")
      except Exception as e: messagebox.showerror("Export Error", str(e))

  def parse_incoming_config(self, line):
    if line.startswith("CFG:"):
      parts = line[4:].split("=")
      if len(parts) == 2:
        var_name, value = parts[0].strip(), parts[1].strip()
        if var_name in self.entries:
          self.entries[var_name].delete(0, tk.END)
          self.entries[var_name].insert(0, value)

  def send_command(self, cmd, silent=False):
    if self.is_connected and self.serial_port:
      try:
        self.serial_port.write(f"{cmd}\n".encode('utf-8'))
        if not silent: self.log(f"Sent: {cmd}")
      except Exception as e: self.log(f"Failed to send: {str(e)}")

  def write_config(self, var_list):
    for var in var_list:
      val = self.entries[var].get().strip()
      if val:
        self.send_command(f"SET {var} {val}")
        time.sleep(0.05)
    self.send_command("SAVE_CONFIG")

if __name__ == "__main__":
  root = tk.Tk()
  app = ESPConfigurator(root)
  root.mainloop()
