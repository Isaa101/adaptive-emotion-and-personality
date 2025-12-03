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
    if d < low and s > high and n > high: #No definida en colores
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
Emotion colours in RGB format
For example:
Red:   (1, 0, 0)
Green: (0, 1, 0)
Blue:  (0, 0, 1)
"""
"""
Emotion colours in RGB format - CUTE VERSION

EMOTION_COLOURS = {
    "Joy":      (1.0, 0.95, 0.6),   # Pastel yellow
    "Anger":    (1.0, 0.6, 0.6),    # Soft coral red
    "Fear":     (0.8, 0.8, 1.0),    # Light lavender blue
    #"Sadness":  (0.6, 0.8, 1.0),    # Gentle sky blue      !Not in lovheim_emotion
    "Shame":    (0.9, 0.7, 0.9),    # Muted pink-purple
    "Disgust":  (0.7, 0.9, 0.7),    # Pastel green
    "Interest": (1.0, 0.8, 0.5),    # Warm peach
    "Distress": (1.0, 0.75, 0.8),   # Soft rose pink
    "Surprise": (1.0, 1.0, 0.6),    # Light lemon yellow
    "Neutral":  (0.85, 0.85, 0.85)  # Light grey

}"""

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
    "openness":        0.0,
    "conscientious":   0.0,
    "extraversion":    0.0,
    "agreeableness":   0.0,
    "neuroticism":     1.0,
}

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
    # Higher neuroticism → lower serotonin and dopamine baselines
    if neuroticism > 0.5:
        serotonin *= (1 - neuroticism * 0.3)  # Reduce serotonin by up to 30%
        dopamine *= (1 - neuroticism * 0.2)   # Reduce dopamine by up to 20%
        norepinephrine *= (1 + neuroticism * 0.4)  # Increase norepinephrine by up to 40%
    
    # IMPROVED: Stronger effects for very high neuroticism
    if neuroticism > 0.7:
        serotonin *= (1 - neuroticism * 0.4)  # Further reduce serotonin up to 40%
        norepinephrine *= (1 + neuroticism * 0.5)  # Further increase norepinephrine up to 50%
    
    # EXTRAVERSION: Enhances positive emotional responses
    # Higher extraversion → amplifies dopamine for positive stimuli
    if extraversion > 0.5:
        if dopamine > 0.5:  # Positive dopamine situations
            dopamine *= (1 + extraversion * 0.3)  # Amplify by up to 30%
        if serotonin > 0.5:  # Positive serotonin situations
            serotonin *= (1 + extraversion * 0.2)  # Amplify by up to 20%
    
    # IMPROVED: Extraverts recover faster from negative emotions
    if extraversion > 0.5 and dopamine < 0.5:
        dopamine *= (1 + extraversion * 0.15)  # Faster recovery from negative states
    
    # AGREEABLENESS: Modulates social emotions
    # Higher agreeableness → enhances serotonin for social harmony
    if agreeableness > 0.5:
        serotonin *= (1 + agreeableness * 0.25)  # Increase serotonin by up to 25%
        # Reduce aggressive responses (anger)
        if dopamine > 0.6 and norepinephrine > 0.6:
            norepinephrine *= (1 - agreeableness * 0.3)  # Reduce norepinephrine
    
    # OPENNESS: Affects novelty responses
    # Higher openness → amplifies dopamine for novel stimuli
    if openness > 0.5:
        # When experiencing new situations (high norepinephrine from novelty)
        if norepinephrine > 0.55:
            dopamine *= (1 + openness * 0.2)  # Enhance dopamine by up to 20%
    
    # IMPROVED: Openness enhances curiosity and exploration
    if openness > 0.5 and norepinephrine > 0.5:
        dopamine *= (1 + openness * 0.25)  # Increase reward from novel experiences
    
    # CONSCIENTIOUSNESS: Stabilizes emotional responses
    # Higher conscientiousness → reduces extreme emotional swings
    if conscientiousness > 0.5:
        # Bring neurotransmitters toward neutral (0.5)
        dopamine = 0.5 + (dopamine - 0.5) * (1 - conscientiousness * 0.2)
        serotonin = 0.5 + (serotonin - 0.5) * (1 - conscientiousness * 0.2)
        norepinephrine = 0.5 + (norepinephrine - 0.5) * (1 - conscientiousness * 0.25)
    
    # Ensure values stay within bounds
    dopamine = max(0.0, min(1.0, dopamine))
    serotonin = max(0.0, min(1.0, serotonin))
    norepinephrine = max(0.0, min(1.0, norepinephrine))
    
    return dopamine, serotonin, norepinephrine


import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.patches as patches
import numpy as np

# Draw matplotlib output
plt.ion()
fig = plt.figure(figsize=(12, 6))

# Left: 3D Lovheim Cube
ax_cube = fig.add_subplot(121, projection='3d')
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

# Emotion labels at vertices (corners of cube)
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

# Current state point (will be updated)
current_point = ax_cube.scatter([0.5], [0.5], [0.5], color='red', s=200, 
                                marker='o', edgecolors='black', linewidth=2, 
                                label='Current State', zorder=10)

# Trail of previous positions (optional)
trail_points = ax_cube.plot([0.5], [0.5], [0.5], 'r--', alpha=0.3, linewidth=1)[0]
trail_history = []

ax_cube.legend(loc='upper right')

# Right: Circle display with personality bar
ax_circle = fig.add_subplot(122)
ax_circle.set_xlim(0, 1)
ax_circle.set_ylim(0, 1)
ax_circle.axis("off")

# Main emotion circle
circle = patches.Circle((0.5, 0.65), 0.3, color=(0, 0, 0), linewidth=3, edgecolor='darkgray')
ax_circle.add_patch(circle)

emotion_text = ax_circle.text(0.5, 0.65, "Neutral", ha="center", va="center", 
                              fontsize=16, weight='bold', color="white")

# Monoamines (only final/modulated values)
mono_text = ax_circle.text(0.5, 0.35, "", ha="center", va="top", fontsize=9, 
                          family='monospace',
                          bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.8))

# Personality trait bars (horizontal mini-bars)
trait_y_positions = [0.25, 0.20, 0.15, 0.10, 0.05]
trait_names = ['O', 'C', 'E', 'A', 'N']  # Openness, Conscient., Extraversion, Agreeable., Neurotic.
trait_colors = ['#9b59b6', '#3498db', '#e74c3c', '#2ecc71', '#f39c12']
trait_bars = []
trait_labels = []

for i, (name, color, y_pos) in enumerate(zip(trait_names, trait_colors, trait_y_positions)):
    # Background bar (gray)
    bg_bar = patches.Rectangle((0.1, y_pos - 0.01), 0.3, 0.02, 
                                facecolor='#cccccc', edgecolor='none')
    ax_circle.add_patch(bg_bar)
    
    # Active bar (colored, will be updated based on personality value)
    active_bar = patches.Rectangle((0.1, y_pos - 0.01), 0.0, 0.02, 
                                    facecolor=color, edgecolor='none')
    ax_circle.add_patch(active_bar)
    trait_bars.append(active_bar)
    
    # Label
    label = ax_circle.text(0.05, y_pos, name, ha='right', va='center', 
                          fontsize=8, weight='bold', color=color)
    trait_labels.append(label)

# Personality title
personality_title = ax_circle.text(0.25, 0.28, "PERSONALITY", ha="center", va="bottom",
                                   fontsize=8, weight='bold', color='#555')

# Active stimuli
stimuli_text = ax_circle.text(0.75, 0.25, "", ha="center", va="top", fontsize=7, 
                              family='monospace')

fig.tight_layout()
fig.canvas.draw()
plt.show(block=False)


def update_circle(colour, raw_d, raw_s, raw_n, mod_d, mod_s, mod_n, stimuli, emotion):
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
    
    # Update circle
    circle.set_color(colour)
    emotion_text.set_text(emotion.upper())
    emotion_text.set_color('white' if sum(colour)/3 < 0.5 else 'black')
    
    # Show only final monoamines
    mono_text.set_text(f"D:{mod_d:.2f} S:{mod_s:.2f} N:{mod_n:.2f}")
    
    # Update personality bars
    personality_values = [
        PERSONALITY["openness"],
        PERSONALITY["conscientious"],
        PERSONALITY["extraversion"],
        PERSONALITY["agreeableness"],
        PERSONALITY["neuroticism"]
    ]
    
    for bar, value in zip(trait_bars, personality_values):
        bar.set_width(0.3 * value)  # Scale to bar width
    
    # Update stimuli
    stim_info = "\n".join([f"• {s['name']}\n  ({s['intensity']:.0f})" 
                           for s in stimuli[:3]]) if stimuli else "No stimuli"  # Max 3 to save space
    stimuli_text.set_text(f"STIMULI\n{stim_info}")
    
    fig.canvas.draw()
    fig.canvas.flush_events()

'''Previous version without monoamine and stimuli text
def update_circle(colour):
    """
    Update circle colour
    """

    # Set circle colour
    circle.set_color(colour)
    fig.canvas.draw()
    fig.canvas.flush_events()
'''

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
            stimuli = socket.recv_json()  # list of stimuli dicts
            
            # Average of stimuli monoamines
            av_dopamine = 0.0
            av_serotonin = 0.0
            av_noradrenaline = 0.0   
            stimuli_counter = 0     
            for s in stimuli:
                scale = s["intensity"] / 200.0 #WHY 200? #TO DO
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
            # update_circle(colour)
            update_circle(colour, dopamine, serotonin, noradrenaline, mod_dopamine, mod_serotonin, mod_noradrenaline, stimuli, emotion)
            plt.pause(0.1)

        except KeyboardInterrupt:
            print("Stopped.")
            break

        time.sleep(1)


if __name__ == "__main__":
    main()
