
# -*- coding: utf-8 -*-
# Aina Crespi Hromcova
# Isabel Gregorio Díez
"""
Programa unificado: entrada de estímulos por terminal + visualización en una sola app.
- Sin sockets ni ZMQ.
- Hilo para entrada de teclado.
- Decaimiento de estímulos dependiente del tiempo (puntos/segundo).

Basado en:
 - stimuli_manager.py (definición de STIMULI y gestor de estímulos)
 - affective_manager.py (lógica de monoaminas, UI Matplotlib, personalidad, colores)
"""

import time
import threading
from queue import Queue

# --- Matplotlib / Numpy / 3D / Parcheado UI ---
import matplotlib
matplotlib.use('TkAgg')  # o 'Qt5Agg' si lo prefieres
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (necesario para proyección 3D)
import numpy as np
from itertools import combinations, product

# =========================
#        ESTÍMULOS
# =========================

STIMULI = {
    "touch":      {"d":  1, "s":  1, "n": -1},  # Joy
    "push":       {"d":  1, "s": -1, "n":  1},  # Anger
    "criticism":  {"d": -1, "s": -1, "n": -1},  # Shame
    "reward":     {"d":  1, "s":  1, "n":  1},  # Interest
    "threat":     {"d":  1, "s": -1, "n": -1},  # Fear
    "broccoli":   {"d": -1, "s":  1, "n": -1},  # Disgust
    "exam":       {"d": -1, "s": -1, "n":  1},  # Distress
    "gift":       {"d":  1, "s":  1, "n": -1},  # Surprise
}

class Stimulus:
    """Representa un estímulo con intensidad y decaimiento temporal."""

    def __init__(self, name, dop, ser, ne, intensity=100.0, decay=5.0):
        self.name = name
        self.dop = float(dop)
        self.ser = float(ser)
        self.ne = float(ne)
        self.intensity = float(intensity)   # 0..100
        self.decay_rate = float(decay)      # puntos/segundo
        self._last_t = time.perf_counter()

    def decay(self):
        """Reduce intensidad en función del tiempo transcurrido."""
        now = time.perf_counter()
        dt = now - self._last_t
        self._last_t = now
        if self.intensity > 0:
            self.intensity -= self.decay_rate * dt
            if self.intensity < 0:
                self.intensity = 0.0

    def is_active(self):
        return self.intensity > 0

    def to_dict(self):
        return {"name": self.name, "d": self.dop, "s": self.ser, "n": self.ne, "intensity": self.intensity}


class StimulusManager:
    """Gestiona estímulos activos y su decaimiento."""
    def __init__(self):
        self.active_STIMULI = {}
        self.lock = threading.Lock()

    def add_stimulus(self, name):
        if name not in STIMULI:
            print(f"⚠️  Estímulo desconocido '{name}'. Usa 'list' para ver opciones.")
            return
        params = STIMULI[name]
        stim = Stimulus(name, params["d"], params["s"], params["n"])
        with self.lock:
            self.active_STIMULI[name] = stim
        print(f"→ Estímulo activado: {name} (intensidad 100)")

    def update(self):
        with self.lock:
            for s in list(self.active_STIMULI.values()):
                s.decay()
                if not s.is_active():
                    del self.active_STIMULI[s.name]

    def get_active(self):
        with self.lock:
            return [s.to_dict() for s in self.active_STIMULI.values()]

# =========================
#      PERSONALIDAD / EMOCIÓN
# =========================

def lovheim_emotion(s, d, n):
    """Región emocional en el cubo de Lövheim (umbral simple)."""
    high = 0.6
    low = 0.4
    if d > high and s > high and n < low:  return "Joy"
    if d > high and s < low  and n > high: return "Anger"
    if d < low  and s < low  and n > high: return "Distress"
    if d < low  and s > high and n > high: return "Surprise"
    if d < low  and s < low  and n < low:  return "Shame"
    if d > high and s < low  and n < low:  return "Fear"
    if d < low  and s > high and n < low:  return "Disgust"
    if d > high and s > high and n > high: return "Interest"
    return "Neutral"

EMOTION_COLOURS = {
    "Joy":      (1.0, 0.84, 0.0),
    "Anger":    (1.0, 0.0, 0.0),
    "Fear":     (0.58, 0.0, 0.83),
    "Shame":    (0.5, 0.0, 0.5),
    "Disgust":  (0.0, 1.0, 0.0),
    "Interest": (1.0, 0.5, 0.0),
    "Distress": (1.0, 0.08, 0.58),
    "Surprise": (0.0, 1.0, 1.0),
    "Neutral":  (0.5, 0.5, 0.5),
}

# Rasgos Big Five 0..1 (puedes ajustar)
PERSONALITY = {
    "openness":        0.0,
    "conscientious":   0.0,
    "extraversion":    0.0,
    "agreeableness":   1.0,
    "neuroticism":     0.0,
}


# --- English personality narratives (card content) ---
PERSONALITY_PROFILES = {
    "Balanced": {
        "name": "Balanced",
        "summary": (
            "A well-rounded personality with no dominant trait. Emotional responses remain near baseline, "
            "with modest shifts depending on current stimuli."
        ),
        "monoamines": (
            "Monoamine modulation is minimal: dopamine, serotonin, and norepinephrine stay close to 0.5 baseline."
        ),
        "emotions": (
            "Emotional states transition smoothly across the Lövheim cube; no single emotion is disproportionately amplified."
        ),
    },
    "openness": {
        "name": "Creative Explorer",
        "summary": (
            "Curiosity-driven and novelty-seeking; engages easily with new, complex stimuli and ideas."
        ),
        "monoamines": (
            "Openness elevates dopamine in the presence of novelty/arousal (higher NE), boosting exploratory drive and interest."
        ),
        "emotions": (
            "Facilitates movement toward Interest and Surprise when stimuli are novel; reduces stagnation in Neutral zones."
        ),
    },
    "conscientious": {
        "name": "Organized Planner",
        "summary": (
            "Goal-oriented, self-regulated, and methodical; resists impulsive swings."
        ),
        "monoamines": (
            "Conscientiousness dampens extremes around baseline (0.5), compressing dopamine, serotonin, and norepinephrine variance."
        ),
        "emotions": (
            "Stabilizes affect: fewer abrupt transitions into Anger/Fear/Distress; sustains Neutral or mild Joy/Interest."
        ),
    },
    "extraversion": {
        "name": "Social Enthusiast",
        "summary": (
            "Energetic and socially engaged; responds strongly to rewarding or affiliative stimuli."
        ),
        "monoamines": (
            "Extraversion amplifies dopamine and serotonin above 0.5, especially under positive/rewarding input."
        ),
        "emotions": (
            "Biases toward Joy and Interest; accelerates recovery from negative states like Fear or Shame."
        ),
    },
    "agreeableness": {
        "name": "Compassionate Helper",
        "summary": (
            "Cooperative and empathy-oriented; seeks social harmony and prosocial outcomes."
        ),
        "monoamines": (
            "Agreeableness boosts serotonin and can attenuate norepinephrine during high DA+NE states, reducing reactive aggression."
        ),
        "emotions": (
            "Suppresses transitions to Anger; supports calm/affiliative emotions, maintaining Neutral or Joy in social contexts."
        ),
    },
    "neuroticism": {
        "name": "Sensitive Reactor",
        "summary": (
            "Emotionally sensitive and vigilant to threat; negative cues have stronger impact."
        ),
        "monoamines": (
            "Neuroticism lowers dopamine/serotonin and elevates norepinephrine, heightening stress reactivity."
        ),
        "emotions": (
            "Shifts the state toward Fear, Distress, or Shame under adverse stimuli; prolongs negative affective episodes."
        ),
    },
}



def get_personality_name():
    """Return (display_name, internal_key, summary_text) based on dominant trait."""
    traits = {
        "openness":      PERSONALITY["openness"],
               "conscientious": PERSONALITY["conscientious"],
        "extraversion":  PERSONALITY["extraversion"],
        "agreeableness": PERSONALITY["agreeableness"],
        "neuroticism":   PERSONALITY["neuroticism"],
    }
    dominant = max(traits.items(), key=lambda x: x[1])
    if dominant[1] < 0.3:
        profile = PERSONALITY_PROFILES["Balanced"]
        return profile["name"], "Balanced", profile["summary"]

    key = dominant[0]  # internal key (matches PERSONALITY_PROFILES keys)
    profile = PERSONALITY_PROFILES[key]
    return profile["name"], key, profile["summary"]

def get_personality_effects():
    d_eff = s_eff = n_eff = 0.0
    if PERSONALITY["neuroticism"] > 0.5:
        d_eff -= PERSONALITY["neuroticism"] * 0.2
        s_eff -= PERSONALITY["neuroticism"] * 0.3
        n_eff += PERSONALITY["neuroticism"] * 0.4
    if PERSONALITY["extraversion"] > 0.5:
        d_eff += PERSONALITY["extraversion"] * 0.3
        s_eff += PERSONALITY["extraversion"] * 0.2
    if PERSONALITY["agreeableness"] > 0.5:
        s_eff += PERSONALITY["agreeableness"] * 0.25
        n_eff -= PERSONALITY["agreeableness"] * 0.15
    if PERSONALITY["openness"] > 0.5:
        d_eff += PERSONALITY["openness"] * 0.2
    if PERSONALITY["conscientious"] > 0.5:
        d_eff -= PERSONALITY["conscientious"] * 0.1
        s_eff -= PERSONALITY["conscientious"] * 0.1
        n_eff -= PERSONALITY["conscientious"] * 0.1
    return d_eff, s_eff, n_eff

def modulate_substances(dopamine, serotonin, norepinephrine):
    opn = PERSONALITY["openness"]
    con = PERSONALITY["conscientious"]
    ext = PERSONALITY["extraversion"]
    agr = PERSONALITY["agreeableness"]
    neu = PERSONALITY["neuroticism"]

    if neu > 0.5:
        serotonin     *= (1 - neu * 0.3)
        dopamine      *= (1 - neu * 0.2)
        norepinephrine*= (1 + neu * 0.4)
        if neu > 0.7:
            serotonin *= (1 - neu * 0.4)
            norepinephrine *= (1 + neu * 0.5)

    if ext > 0.5:
        if dopamine > 0.5:
            dopamine *= (1 + ext * 0.3)
        if serotonin > 0.5:
            serotonin *= (1 + ext * 0.2)
        if dopamine < 0.5:
            dopamine *= (1 + ext * 0.15)

    if agr > 0.5:
        serotonin *= (1 + agr * 0.25)
        if dopamine > 0.6 and norepinephrine > 0.6:
            norepinephrine *= (1 - agr * 0.3)

    if opn > 0.5:
        if norepinephrine > 0.55:
            dopamine *= (1 + opn * 0.2)
        if norepinephrine > 0.5:
            dopamine *= (1 + opn * 0.25)

    if con > 0.5:
        dopamine       = 0.5 + (dopamine - 0.5) * (1 - con * 0.2)
        serotonin      = 0.5 + (serotonin - 0.5) * (1 - con * 0.2)
        norepinephrine = 0.5 + (norepinephrine - 0.5) * (1 - con * 0.25)

    dopamine       = max(0.0, min(1.0, dopamine))
    serotonin      = max(0.0, min(1.0, serotonin))
    norepinephrine = max(0.0, min(1.0, norepinephrine))
    return dopamine, serotonin, norepinephrine

# =========================
#         UI MATPLOTLIB
# =========================

plt.ion()
fig = plt.figure(figsize=(16, 8))

gs = fig.add_gridspec(
    2, 2, width_ratios=[1, 1], height_ratios=[1, 1.2],
    left=0.05, right=0.98, top=0.96, bottom=0.04,
    hspace=0.15, wspace=0.15
)

# --- Izquierda: Cubo 3D ---
ax_cube = fig.add_subplot(gs[:, 0], projection='3d')
ax_cube.set_xlabel('Serotonin', fontsize=10, weight='bold')
ax_cube.set_ylabel('Dopamine', fontsize=10, weight='bold')
ax_cube.set_zlabel('Norepinephrine', fontsize=10, weight='bold')
ax_cube.set_xlim(0, 1); ax_cube.set_ylim(0, 1); ax_cube.set_zlim(0, 1)
ax_cube.set_title("Lövheim Cube", fontsize=12, weight='bold')

r = [0, 1]
for s, e in combinations(np.array(list(product(r, r, r))), 2):
    if np.sum(np.abs(s - e)) == r[1] - r[0]:
        ax_cube.plot3D(*zip(s, e), color="gray", alpha=0.3, linewidth=0.5)

emotions_pos = {
    "Joy":      (1, 1, 0, EMOTION_COLOURS["Joy"]),
    "Interest": (1, 1, 1, EMOTION_COLOURS["Interest"]),
    "Surprise": (1, 0, 1, EMOTION_COLOURS["Surprise"]),
    "Fear":     (0, 1, 0, EMOTION_COLOURS["Fear"]),
    "Anger":    (0, 1, 1, EMOTION_COLOURS["Anger"]),
    "Distress": (0, 0, 1, EMOTION_COLOURS["Distress"]),
    "Disgust":  (1, 0, 0, EMOTION_COLOURS["Disgust"]),
    "Shame":    (0, 0, 0, EMOTION_COLOURS["Shame"]),
}
for emotion, (s, d, n, color) in emotions_pos.items():
    ax_cube.scatter(s, d, n, color=color, s=100, alpha=0.6, edgecolors='black', linewidth=1.5)
    ax_cube.text(s, d, n, f" {emotion}", fontsize=8, weight='bold')

current_point = ax_cube.scatter([0.5], [0.5], [0.5], color='red', s=200,
                                marker='o', edgecolors='black', linewidth=2,
                                label='Current State', zorder=10)
trail_points = ax_cube.plot([0.5], [0.5], [0.5], 'r--', alpha=0.3, linewidth=1)[0]
trail_history = []
ax_cube.legend(loc='upper right')

# --- Arriba derecha: Círculo + Lista de estímulos ---
ax_top_right = fig.add_subplot(gs[0, 1])
ax_top_right.set_xlim(0, 1); ax_top_right.set_ylim(0, 1); ax_top_right.axis("off")
title_text = ax_top_right.text(0.5, 0.98, "CURRENT STATE", ha="center", va="top",
                               fontsize=11, weight='bold', color='#333')
circle = patches.Circle((0.25, 0.5), 0.18, facecolor=(0, 0, 0), linewidth=3, edgecolor='darkgray')
ax_top_right.add_patch(circle)
circle_glow = patches.Circle((0.25, 0.5), 0.20, facecolor=(0.5, 0.5, 0.5), alpha=0.3, linewidth=0)
ax_top_right.add_patch(circle_glow)
emotion_text = ax_top_right.text(0.25, 0.5, "Neutral", ha="center", va="center",
                                 fontsize=13, weight='bold', color="white")
mono_text = ax_top_right.text(0.25, 0.28, "", ha="center", va="top", fontsize=7,
                              family='monospace', color='#555')
stimuli_title = ax_top_right.text(0.55, 0.75, "ACTIVE STIMULI", ha="left", va="top",
                                  fontsize=9, weight='bold', color='#333')
stimuli_text = ax_top_right.text(0.55, 0.70, "No active stimuli", ha="left", va="top",
                                 fontsize=8, family='monospace', color='#666')

# --- Abajo derecha: Tarjeta de personalidad ---
ax_bottom_right = fig.add_subplot(gs[1, 1])
ax_bottom_right.set_xlim(0, 1); ax_bottom_right.set_ylim(0, 1); ax_bottom_right.axis("off")
card_bg = patches.FancyBboxPatch((0.02, 0.02), 0.96, 0.96, boxstyle="round,pad=0.02",
                                 facecolor='#f8f9fa', edgecolor='#dee2e6', linewidth=2)
ax_bottom_right.add_patch(card_bg)
header_bg = patches.FancyBboxPatch((0.04, 0.80), 0.92, 0.16, boxstyle="round,pad=0.01",
                                   facecolor='#3498db', edgecolor='none')
ax_bottom_right.add_patch(header_bg)
card_title = ax_bottom_right.text(0.5, 0.90, "PERSONALITY PROFILE", ha="center", va="center",
                                  fontsize=11, weight='bold', color='white')
personality_name = ax_bottom_right.text(0.5, 0.84, "Balanced", ha="center", va="center",
                                        fontsize=9, style='italic', color='white')

# Mini radar
ax_radar = fig.add_axes([0.54, 0.08, 0.15, 0.22], projection='polar')
ax_radar.set_title("Traits", fontsize=8, weight='bold', pad=8)
categories = ['O', 'C', 'E', 'A', 'N']
N = len(categories)
angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
angles += angles[:1]
ax_radar.set_xticks(angles[:-1])
ax_radar.set_xticklabels(categories, fontsize=8, weight='bold')
ax_radar.set_ylim(0, 1)
ax_radar.set_yticks([0.5, 1.0]); ax_radar.set_yticklabels(['0.5', '1.0'], fontsize=6)
ax_radar.grid(True, alpha=0.3)
personality_values = [0.5] * N + [0.5]
personality_plot, = ax_radar.plot(angles, personality_values, 'o-', linewidth=2, color='#3498db')

effects_title = ax_bottom_right.text(0.72, 0.74, "Effects on Monoamines:", ha="left", va="top",
                                     fontsize=8, weight='bold', color='#333')
effects_text = ax_bottom_right.text(0.72, 0.70, "", ha="left", va="top",
                                    fontsize=7, family='monospace', color='#555')
desc_title = ax_bottom_right.text(0.06, 0.35, "Description:", ha="left", va="top",
                                  fontsize=8, weight='bold', color='#333')
description_text = ax_bottom_right.text(0.06, 0.31, "", ha="left", va="top",
                                        fontsize=7, color='#555', wrap=True)

fig.canvas.draw()
plt.show(block=False)

pulse_scale = 1.0
pulse_direction = 1

def update_circle(colour, raw_d, raw_s, raw_n, mod_d, mod_s, mod_n, stimuli, emotion):
    global pulse_scale, pulse_direction

    # Punto en el cubo
    current_point._offsets3d = ([mod_s], [mod_d], [mod_n])
    current_point.set_color(colour)

    # Estela
    trail_history.append((mod_s, mod_d, mod_n))
    if len(trail_history) > 10:
        trail_history.pop(0)
    if len(trail_history) > 1:
        ts, td, tn = zip(*trail_history)
        trail_points.set_data_3d(ts, td, tn)

    # Círculo + pulso
    circle.set_facecolor(colour)
    circle_glow.set_facecolor(colour)

    pulse_scale += 0.02 * pulse_direction
    if pulse_scale >= 1.15:
        pulse_direction = -1
    elif pulse_scale <= 0.95:
        pulse_direction = 1
    circle_glow.set_radius(0.20 * pulse_scale)

    emotion_text.set_text(emotion.upper())
    emotion_text.set_color('white' if sum(colour)/3 < 0.5 else 'black')
    mono_text.set_text(f"D:{mod_d:.2f}\nS:{mod_s:.2f}\nN:{mod_n:.2f}")

    # Lista de estímulos
    if stimuli:
        lines = []
        for s in stimuli[:5]:
            lines.append(f"• {s['name']:<12} [{s['intensity']:>3.0f}]")
        stim_info = "\n".join(lines)
    else:
        stim_info = "None"
    stimuli_text.set_text(stim_info)


   
    # ===== Update personality card (English narrative) =====
    display_name, profile_key, summary_text = get_personality_name()
    personality_name.set_text(display_name)

    # Radar values (unchanged)
    values = [
        PERSONALITY["openness"],
        PERSONALITY["conscientious"],
        PERSONALITY["extraversion"],
        PERSONALITY["agreeableness"],
        PERSONALITY["neuroticism"],
    ]
    values += values[:1]
    personality_plot.set_ydata(values)
    while ax_radar.collections:
        ax_radar.collections[0].remove()
    ax_radar.fill(angles, values, alpha=0.25, color="#3498db")

    # Numeric effects (keep) + English explanation
    d_eff, s_eff, n_eff = get_personality_effects()

    # Compose English text from profile dictionary
    profile = PERSONALITY_PROFILES[profile_key]
    header_color_map = {
        "Balanced": "#3498db",
        "openness": "#8e44ad",
        "conscientious": "#2c3e50",
        "extraversion": "#e67e22",
        "agreeableness": "#27ae60",
        "neuroticism": "#c0392b",
    }
    # Apply header color (optional but nice)
    header_bg.set_facecolor(header_color_map.get(profile_key, "#3498db"))

    narrative = (
        f"{profile['summary']}\n\n"
        f"Monoamines:\n- {profile['monoamines']}\n\n"
        f"Emotions:\n- {profile['emotions']}"
    )

    # Brief numeric line in 'effects_text' (right column) for quick reference
    effects_text.set_text(
        f"Dopamine: {d_eff:+.2f}\nSerotonin: {s_eff:+.2f}\nNorepinephrine: {n_eff:+.2f}"
    )

       # Full English narrative in the 'description_text' (bottom of the card)
    import textwrap
    wrapped_desc = "\n".join(textwrap.wrap(narrative, width=55))
    description_text.set_text(wrapped_desc)

    fig.canvas.draw()
    fig.canvas.flush_events()

# =========================
#     ENTRADA TECLADO
# =========================

def keyboard_listener(queue, stop_event):
    hint = ", ".join(sorted(STIMULI.keys()))
    print("Comandos: escribe un estímulo, 'list' para listar, 'q' para salir.")
    print(f"Estímulos disponibles: {hint}")
    while not stop_event.is_set():
        try:
            user_input = input(">> ").strip().lower()
        except EOFError:
            user_input = "q"
        if user_input in ("q", "quit", "exit"):
            stop_event.set()
            break
        if user_input == "list":
            print("Disponibles:", ", ".join(sorted(STIMULI.keys())))
            continue
        if user_input:
            queue.put(user_input)

# =========================
#          MAIN
# =========================

def main():
    stop_event = threading.Event()
    cmd_queue = Queue()
    stim_manager = StimulusManager()

    # Hilo para teclado
    t = threading.Thread(target=keyboard_listener, args=(cmd_queue, stop_event), daemon=True)
    t.start()

    print("Affective app en ejecución...\n(Usa la ventana de terminal para introducir estímulos)")

    # Basales
    serotonin = 0.5
    dopamine = 0.5
    noradrenaline = 0.5

    try:
        last_update_t = time.perf_counter()
        while not stop_event.is_set():
            # Procesa comandos
            while not cmd_queue.empty():
                cmd = cmd_queue.get()
                stim_manager.add_stimulus(cmd)

            # Decaimiento y recopilación
            stim_manager.update()
            stimuli = stim_manager.get_active()

            # Media de monoaminas según intensidad (idéntico esquema de escalado)
            av_d = av_s = av_n = 0.0
            cnt = 0
            for s in stimuli:
                scale = s["intensity"] / 200.0  # mantiene el rango como en tu versión
                cnt += 1
                av_d += s["d"] * scale
                av_n += s["n"] * scale
                av_s += s["s"] * scale
            if cnt != 0:
                av_s /= cnt
                av_d /= cnt
                av_n /= cnt

            # Monoaminas: 0.5 + promedio escalado y acotado
            dopamine      = max(0.0, min(1.0, 0.5 + av_d))
            serotonin     = max(0.0, min(1.0, 0.5 + av_s))
            noradrenaline = max(0.0, min(1.0, 0.5 + av_n))

            # Modulación por personalidad
            mod_d, mod_s, mod_n = modulate_substances(dopamine, serotonin, noradrenaline)

            # Emoción + color
            emotion = lovheim_emotion(mod_s, mod_d, mod_n)
            colour = EMOTION_COLOURS.get(emotion, (1, 1, 1))

            # Log en terminal (opcional)
            print(f"\033[38;2;{int(colour[0]*255)};{int(colour[1]*255)};{int(colour[2]*255)}m{emotion}\033[0m",
                  f"Dop={dopamine:.2f} Ser={serotonin:.2f} Nor={noradrenaline:.2f}")

            # Actualiza UI
            update_circle(colour, dopamine, serotonin, noradrenaline,
                          mod_d, mod_s, mod_n, stimuli, emotion)

            # Ritmo ~10 Hz
            plt.pause(0.05)
            time.sleep(0.05)

    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        try:
            t.join(timeout=0.5)
        except RuntimeError:
            pass
        plt.close(fig)

if __name__ == "__main__":
    main()
# -*- coding: utf-8 -*-
