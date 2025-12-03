# Aina Crespi Hromcova
# Isabel Gregorio Díez
"""
PROGRAM 2 — affective_processor.py
This program receives stimuli, computes monoamines, prints colour-coded emotions,
and shows a coloured circle window.
"""

import zmq
import time
import matplotlib.pyplot as plt
import matplotlib.patches as patches

import matplotlib
matplotlib.use('TkAgg')  # o 'Qt5Agg

#Imports for new window
from itertools import combinations, product
import numpy as np
from mpl_toolkits.mplot3d import Axes3D



def lovheim_emotion(s, d, n):
    """
    Basic implementation of Lovheim cube:
    High/Low thresholds define emotional region.
    """

    # Thresholds to compute emotions
    high = 0.6
    low = 0.4

    # Compute emotion based on values and thresholds
    if d > high and s > high and n < low:
        return "Joy"
    if d > high and s < low and n > high:
        return "Anger"
    if d < low and s < low and n > high:
        return "Distress"
    if d < low and s > high and n > high:
        return "Surprise"
    if d < low and s < low and n < low:
        return "Shame"
    if d > high and s < low and n < low:
        return "Fear"
    if d < low and s > high and n < low:
        return "Disgust"
    if d > high and s > high and n > high:
        return "Interest"
        
    return "Neutral"  # fallback

"""
Emotion colours in RGB format - VIVID VERSION
"""
EMOTION_COLOURS = {
    "Joy":      (1.0, 0.84, 0.0),    # Gold/Bright Yellow
    "Anger":    (1.0, 0.0, 0.0),     # Pure Red
    "Fear":     (0.58, 0.0, 0.83),   # Purple
    "Shame":    (0.5, 0.0, 0.5),     # Dark Magenta
    "Disgust":  (0.0, 1.0, 0.0),     # Lime Green
    "Interest": (1.0, 0.5, 0.0),     # Bright Orange
    "Distress": (1.0, 0.08, 0.58),   # Hot Pink
    "Surprise": (0.0, 1.0, 1.0),     # Cyan/Aqua
    "Neutral":  (0.5, 0.5, 0.5)      # Gray
}

"""
Define PERSONALITY modulation
Big-five PERSONALITY traits from 0 to 1
"""
PERSONALITY  = {
    "openness":        0.0,
    "conscientious":   0.0,
    "extraversion":    0.0,
    "agreeableness":   1.0,
    "neuroticism":     0.0,
}

PERSONALITY2 = {
    "openness":        0.8,
    "conscientious":   0.0,
    "extraversion":    0.0,
    "agreeableness":   0.0,
    "neuroticism":     0.0,
}

PERSONALITY3 = {
    "openness":        0.0,
    "conscientious":   0.0,
    "extraversion":    0.9,
    "agreeableness":   0.0,
    "neuroticism":     0.0,
}

def get_personality_name():
    """Returns personality name based on dominant trait"""
    traits = {
        "openness": PERSONALITY["openness"],
        "conscientious": PERSONALITY["conscientious"],
        "extraversion": PERSONALITY["extraversion"],
        "agreeableness": PERSONALITY["agreeableness"],
        "neuroticism": PERSONALITY["neuroticism"]
    }
    
    # Find dominant trait
    dominant = max(traits.items(), key=lambda x: x[1])
    
    if dominant[1] < 0.3:
        return "Balanced", "A well-rounded personality with no extreme traits."
    
    names = {
        "openness": "Creative Explorer",
        "conscientious": "Organized Planner",
        "extraversion": "Social Enthusiast",
        "agreeableness": "Compassionate Helper",
        "neuroticism": "Sensitive Reactor"
    }
    
    descriptions = {
        "openness": "Amplifies dopamine response to novel stimuli, enhancing curiosity and interest.",
        "conscientious": "Stabilizes monoamine fluctuations, reducing emotional extremes.",
        "extraversion": "Boosts dopamine and serotonin for positive emotions, speeds recovery from negative states.",
        "agreeableness": "Increases serotonin for social harmony, reduces aggressive responses (anger).",
        "neuroticism": "Lowers serotonin and dopamine baselines, heightens norepinephrine, amplifying negative emotions."
    }
    
    return names[dominant[0]], descriptions[dominant[0]]

def get_personality_effects():
    """Calculate average effect on each monoamine"""
    # Simplified calculation of personality effects
    d_effect = 0.0
    s_effect = 0.0
    n_effect = 0.0
    
    if PERSONALITY["neuroticism"] > 0.5:
        d_effect -= PERSONALITY["neuroticism"] * 0.2
        s_effect -= PERSONALITY["neuroticism"] * 0.3
        n_effect += PERSONALITY["neuroticism"] * 0.4
    
    if PERSONALITY["extraversion"] > 0.5:
        d_effect += PERSONALITY["extraversion"] * 0.3
        s_effect += PERSONALITY["extraversion"] * 0.2
    
    if PERSONALITY["agreeableness"] > 0.5:
        s_effect += PERSONALITY["agreeableness"] * 0.25
        n_effect -= PERSONALITY["agreeableness"] * 0.15
    
    if PERSONALITY["openness"] > 0.5:
        d_effect += PERSONALITY["openness"] * 0.2
    
    if PERSONALITY["conscientious"] > 0.5:
        # Stabilizes, so reduces extremes (represented as slight negative)
        d_effect -= PERSONALITY["conscientious"] * 0.1
        s_effect -= PERSONALITY["conscientious"] * 0.1
        n_effect -= PERSONALITY["conscientious"] * 0.1
    
    return d_effect, s_effect, n_effect

def modulate_substances(dopamine, serotonin, norepinephrine):
    """
    Modulate the values of dopamine, serotonin, and noradrenaline
    based on the robot's PERSONALITY
    """

    # Get personality traits (0 to 1 scale)
    openness = PERSONALITY["openness"]
    conscientiousness = PERSONALITY["conscientious"]
    extraversion = PERSONALITY["extraversion"]
    agreeableness = PERSONALITY["agreeableness"]
    neuroticism = PERSONALITY["neuroticism"]
    
    # NEUROTICISM: Amplifies negative emotional responses
    if neuroticism > 0.5:
        serotonin *= (1 - neuroticism * 0.3)
        dopamine *= (1 - neuroticism * 0.2)
        norepinephrine *= (1 + neuroticism * 0.4)
    
    if neuroticism > 0.7:
        serotonin *= (1 - neuroticism * 0.4)
        norepinephrine *= (1 + neuroticism * 0.5)
    
    # EXTRAVERSION: Enhances positive emotional responses
    if extraversion > 0.5:
        if dopamine > 0.5:
            dopamine *= (1 + extraversion * 0.3)
        if serotonin > 0.5:
            serotonin *= (1 + extraversion * 0.2)
    
    if extraversion > 0.5 and dopamine < 0.5:
        dopamine *= (1 + extraversion * 0.15)
    
    # AGREEABLENESS: Modulates social emotions
    if agreeableness > 0.5:
        serotonin *= (1 + agreeableness * 0.25)
        if dopamine > 0.6 and norepinephrine > 0.6:
            norepinephrine *= (1 - agreeableness * 0.3)
    
    # OPENNESS: Affects novelty responses
    if openness > 0.5:
        if norepinephrine > 0.55:
            dopamine *= (1 + openness * 0.2)
    
    if openness > 0.5 and norepinephrine > 0.5:
        dopamine *= (1 + openness * 0.25)
    
    # CONSCIENTIOUSNESS: Stabilizes emotional responses
    if conscientiousness > 0.5:
        dopamine = 0.5 + (dopamine - 0.5) * (1 - conscientiousness * 0.2)
        serotonin = 0.5 + (serotonin - 0.5) * (1 - conscientiousness * 0.2)
        norepinephrine = 0.5 + (norepinephrine - 0.5) * (1 - conscientiousness * 0.25)
    
    # Ensure values stay within bounds
    dopamine = max(0.0, min(1.0, dopamine))
    serotonin = max(0.0, min(1.0, serotonin))
    norepinephrine = max(0.0, min(1.0, norepinephrine))
    
    return dopamine, serotonin, norepinephrine


# Draw matplotlib output
plt.ion()
fig = plt.figure(figsize=(16, 8))

# Create custom grid: Left for cube, Right split into top and bottom
gs = fig.add_gridspec(2, 2, width_ratios=[1, 1], height_ratios=[1, 1.2], 
                      left=0.05, right=0.98, top=0.96, bottom=0.04, 
                      hspace=0.15, wspace=0.15)

# ===== LEFT: 3D Lovheim Cube =====
ax_cube = fig.add_subplot(gs[:, 0], projection='3d')
ax_cube.set_xlabel('Serotonin', fontsize=10, weight='bold')
ax_cube.set_ylabel('Dopamine', fontsize=10, weight='bold')
ax_cube.set_zlabel('Norepinephrine', fontsize=10, weight='bold')
ax_cube.set_xlim(0, 1)
ax_cube.set_ylim(0, 1)
ax_cube.set_zlim(0, 1)
ax_cube.set_title("Lövheim Cube", fontsize=12, weight='bold')

# Draw cube wireframe
r = [0, 1]
for s, e in combinations(np.array(list(product(r, r, r))), 2):
    if np.sum(np.abs(s-e)) == r[1]-r[0]:
        ax_cube.plot3D(*zip(s, e), color="gray", alpha=0.3, linewidth=0.5)

# Emotion labels at vertices
emotions_pos = {
    "Joy":      (1, 1, 0, EMOTION_COLOURS["Joy"]),
    "Interest": (1, 1, 1, EMOTION_COLOURS["Interest"]),
    "Surprise": (1, 0, 1, EMOTION_COLOURS["Surprise"]),
    "Fear":     (0, 1, 0, EMOTION_COLOURS["Fear"]),
    "Anger":    (0, 1, 1, EMOTION_COLOURS["Anger"]),
    "Distress": (0, 0, 1, EMOTION_COLOURS["Distress"]),
    "Disgust":  (1, 0, 0, EMOTION_COLOURS["Disgust"]),
    "Shame":    (0, 0, 0, EMOTION_COLOURS["Shame"])
}

for emotion, (s, d, n, color) in emotions_pos.items():
    ax_cube.scatter(s, d, n, color=color, s=100, alpha=0.6, edgecolors='black', linewidth=1.5)
    ax_cube.text(s, d, n, f"  {emotion}", fontsize=8, weight='bold')

# Current state point
current_point = ax_cube.scatter([0.5], [0.5], [0.5], color='red', s=200, 
                                marker='o', edgecolors='black', linewidth=2, 
                                label='Current State', zorder=10)

# Trail
trail_points = ax_cube.plot([0.5], [0.5], [0.5], 'r--', alpha=0.3, linewidth=1)[0]
trail_history = []

ax_cube.legend(loc='upper right')

# ===== TOP RIGHT: Emotion Circle + Active Stimuli =====
ax_top_right = fig.add_subplot(gs[0, 1])
ax_top_right.set_xlim(0, 1)
ax_top_right.set_ylim(0, 1)
ax_top_right.axis("off")

# Title
title_text = ax_top_right.text(0.5, 0.98, "CURRENT STATE", ha="center", va="top",
                                fontsize=11, weight='bold', color='#333')

# Emotion circle (LEFT SIDE - perfectly circular)
circle = patches.Circle((0.25, 0.5), 0.18, facecolor=(0, 0, 0), 
                        linewidth=3, edgecolor='darkgray')
ax_top_right.add_patch(circle)

# Outer glow for pulse effect
circle_glow = patches.Circle((0.25, 0.5), 0.20, facecolor=(0.5, 0.5, 0.5), 
                             alpha=0.3, linewidth=0)
ax_top_right.add_patch(circle_glow)

emotion_text = ax_top_right.text(0.25, 0.5, "Neutral", ha="center", va="center",
                                 fontsize=13, weight='bold', color="white")

mono_text = ax_top_right.text(0.25, 0.28, "", ha="center", va="top", fontsize=7,
                              family='monospace', color='#555')

# Active stimuli list (RIGHT SIDE)
stimuli_title = ax_top_right.text(0.55, 0.75, "ACTIVE STIMULI", ha="left", va="top",
                                  fontsize=9, weight='bold', color='#333')

stimuli_text = ax_top_right.text(0.55, 0.70, "No active stimuli", ha="left", va="top",
                                 fontsize=8, family='monospace', color='#666')

# ===== BOTTOM RIGHT: Personality ID Card =====
ax_bottom_right = fig.add_subplot(gs[1, 1])
ax_bottom_right.set_xlim(0, 1)
ax_bottom_right.set_ylim(0, 1)
ax_bottom_right.axis("off")

# Card background
card_bg = patches.FancyBboxPatch((0.02, 0.02), 0.96, 0.96,
                                 boxstyle="round,pad=0.02",
                                 facecolor='#f8f9fa',
                                 edgecolor='#dee2e6',
                                 linewidth=2)
ax_bottom_right.add_patch(card_bg)

# Card header
header_bg = patches.FancyBboxPatch((0.04, 0.80), 0.92, 0.16,
                                   boxstyle="round,pad=0.01",
                                   facecolor='#3498db',
                                   edgecolor='none')
ax_bottom_right.add_patch(header_bg)

card_title = ax_bottom_right.text(0.5, 0.90, "PERSONALITY PROFILE", ha="center", va="center",
                                  fontsize=11, weight='bold', color='white')

personality_name = ax_bottom_right.text(0.5, 0.84, "Balanced", ha="center", va="center",
                                        fontsize=9, style='italic', color='white')

# Mini radar chart (LEFT SIDE of card)
ax_radar = fig.add_axes([0.54, 0.08, 0.15, 0.22], projection='polar')
ax_radar.set_title("Traits", fontsize=8, weight='bold', pad=8)

categories = ['O', 'C', 'E', 'A', 'N']  # Abbreviated
N = len(categories)
angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
angles += angles[:1]

ax_radar.set_xticks(angles[:-1])
ax_radar.set_xticklabels(categories, fontsize=8, weight='bold')
ax_radar.set_ylim(0, 1)
ax_radar.set_yticks([0.5, 1.0])
ax_radar.set_yticklabels(['0.5', '1.0'], fontsize=6)
ax_radar.grid(True, alpha=0.3)

personality_values = [0.5] * N
personality_values += personality_values[:1]
personality_plot, = ax_radar.plot(angles, personality_values, 'o-', linewidth=2, color='#3498db')

# Monoamine effects (RIGHT SIDE of card)
effects_title = ax_bottom_right.text(0.72, 0.74, "Effects on Monoamines:", ha="left", va="top",
                                     fontsize=8, weight='bold', color='#333')

effects_text = ax_bottom_right.text(0.72, 0.70, "", ha="left", va="top",
                                    fontsize=7, family='monospace', color='#555')

# Description (BOTTOM of card)
desc_title = ax_bottom_right.text(0.06, 0.35, "Description:", ha="left", va="top",
                                  fontsize=8, weight='bold', color='#333')

description_text = ax_bottom_right.text(0.06, 0.31, "", ha="left", va="top",
                                        fontsize=7, color='#555', wrap=True)

fig.canvas.draw()
plt.show(block=False)

# Pulse animation variables
pulse_scale = 1.0
pulse_direction = 1

def update_circle(colour, raw_d, raw_s, raw_n, mod_d, mod_s, mod_n, stimuli, emotion):
    global pulse_scale, pulse_direction
    
    # Update 3D cube position
    current_point._offsets3d = ([mod_s], [mod_d], [mod_n])
    current_point.set_color(colour)
    
    # Add trail
    trail_history.append((mod_s, mod_d, mod_n))
    if len(trail_history) > 10:
        trail_history.pop(0)
    if len(trail_history) > 1:
        trail_s, trail_d, trail_n = zip(*trail_history)
        trail_points.set_data_3d(trail_s, trail_d, trail_n)
    
    # ===== Update emotion circle with pulse =====
    circle.set_facecolor(colour)
    circle_glow.set_facecolor(colour)
    
    # Pulse animation
    pulse_scale += 0.02 * pulse_direction
    if pulse_scale >= 1.15:
        pulse_direction = -1
    elif pulse_scale <= 0.95:
        pulse_direction = 1
    
    circle_glow.set_radius(0.20 * pulse_scale)
    
    emotion_text.set_text(emotion.upper())
    emotion_text.set_color('white' if sum(colour)/3 < 0.5 else 'black')
    
    mono_text.set_text(f"D:{mod_d:.2f}\nS:{mod_s:.2f}\nN:{mod_n:.2f}")
    
    # ===== Update active stimuli =====
    if stimuli:
        stim_lines = []
        for s in stimuli[:5]:  # Show max 5
            stim_lines.append(f"• {s['name']:<12} [{s['intensity']:>3.0f}]")
        stim_info = "\n".join(stim_lines)
    else:
        stim_info = "None"
    
    stimuli_text.set_text(stim_info)
    
    # ===== Update personality card =====
    pers_name, pers_desc = get_personality_name()
    personality_name.set_text(pers_name)
    
    # Update radar chart
    values = [
        PERSONALITY["openness"],
        PERSONALITY["conscientious"],
        PERSONALITY["extraversion"],
        PERSONALITY["agreeableness"],
        PERSONALITY["neuroticism"]
    ]
    values += values[:1]
    personality_plot.set_ydata(values)
    
    # Recreate fill
    while ax_radar.collections:
        ax_radar.collections[0].remove()
    ax_radar.fill(angles, values, alpha=0.25, color='#3498db')
    
    # Update effects
    d_eff, s_eff, n_eff = get_personality_effects()
    effects_str = f"Dopamine:      {d_eff:+.2f}\nSerotonin:     {s_eff:+.2f}\nNorepinephrine: {n_eff:+.2f}"
    effects_text.set_text(effects_str)
    
    # Update description (wrap text manually)
    import textwrap
    wrapped_desc = "\n".join(textwrap.wrap(pers_desc, width=55))
    description_text.set_text(wrapped_desc)
    
    fig.canvas.draw()
    fig.canvas.flush_events()

def main():
    """
    Main function
    """

    # ZMQ setup
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5555")
    socket.setsockopt_string(zmq.SUBSCRIBE, "")

    # Print a message
    print("Affective processor running...\n")

    # Monoamines start at 0.5, their baseline value
    serotonin = 0.5
    dopamine = 0.5
    noradrenaline = 0.5

    # Loop forever
    while True:
        try:
            # Receive stimuli from the stimulus manager
            stimuli = socket.recv_json()
            
            # Average of stimuli monoamines
            av_dopamine = 0.0
            av_serotonin = 0.0
            av_noradrenaline = 0.0   
            stimuli_counter = 0     
            for s in stimuli:
                scale = s["intensity"] / 200.0
                stimuli_counter += 1
                av_dopamine += s["d"] * scale
                av_noradrenaline += s["n"] * scale
                av_serotonin += s["s"] * scale
            if stimuli_counter != 0:
                av_serotonin = av_serotonin/stimuli_counter
                av_dopamine = av_dopamine/stimuli_counter
                av_noradrenaline = av_noradrenaline/stimuli_counter

            # Scale intensity to a value between 0 and 0.5
            dopamine = 0.5 + av_dopamine
            serotonin = 0.5 +  av_serotonin
            noradrenaline = 0.5 + av_noradrenaline

            # Clamp values between 0 and 1
            dopamine = max(0, min(1, dopamine))
            serotonin = max(0, min(1, serotonin))
            noradrenaline = max(0, min(1, noradrenaline))

            # Show levels
            print(f"Monoamines without modulation: Dop={dopamine:.2f} Se={serotonin:.2f} Ne={noradrenaline:.2f}")

            # Modulate values based on PERSONALITY
            mod_dopamine, mod_serotonin, mod_noradrenaline = modulate_substances(dopamine, serotonin, noradrenaline)

            # Determine emotion
            emotion = lovheim_emotion(mod_serotonin, mod_dopamine, mod_noradrenaline)

            # Get colour for the emotion
            colour = EMOTION_COLOURS.get(emotion, (1, 1, 1))

            # Print coloured text in terminal
            print(f"\033[38;2;{int(colour[0]*255)};{int(colour[1]*255)};{int(colour[2]*255)}m{emotion}\033[0m", f" | Dop={dopamine:.2f} Se={serotonin:.2f} Ne={noradrenaline:.2f}")

            # Update circle window
            update_circle(colour, dopamine, serotonin, noradrenaline, mod_dopamine, mod_serotonin, mod_noradrenaline, stimuli, emotion)
            plt.pause(0.1)

        except KeyboardInterrupt:
            print("Stopped.")
            break

        time.sleep(1)


if __name__ == "__main__":
    main()