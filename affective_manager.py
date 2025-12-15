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
Emotion colours in RGB format
For example:
Red:   (1, 0, 0)
Green: (0, 1, 0)
Blue:  (0, 0, 1)
"""
#TO DO
EMOTION_COLOURS = {
    "Joy":      (1.0, 0.95, 0.6),   # Pastel yellow
    "Anger":    (1.0, 0.6, 0.6),    # Soft coral red
    "Fear":     (0.8, 0.8, 1.0),    # Light lavender blue
    "Shame":    (0.9, 0.7, 0.9),    # Muted pink-purple
    "Disgust":  (0.7, 0.9, 0.7),    # Pastel green
    "Interest": (1.0, 0.8, 0.5),    # Warm peach
    "Distress": (1.0, 0.75, 0.8),   # Soft rose pink
    "Surprise":  (1.0, 0.9, 0.6),  # Light orange
    "Neutral":  (0.85, 0.85, 0.85),  # Light grey
}


"""
Define PERSONALITY modulation
Big-five PERSONALITY traits from 0 to 1
"""
#TO DO
PERSONALITY  = {
    "openness":        1.0,
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

def modulate_substances(d, s, n, personality=PERSONALITY):
    """
    Modulate the values of dopamine, serotonin, and noradrenaline
    based on the robot's PERSONALITY
    """

    # Get personality traits (0 to 1 scale)
    openness = personality["openness"]
    conscientiousness = personality["conscientious"]
    extraversion = personality ["extraversion"]
    agreeableness = personality["agreeableness"]
    neuroticism = personality["neuroticism"]

     # NEUROTICISM: amplifies negative emotional reactivity
    if neuroticism > 0.5:
        if s < 0.5:  # Already low serotonin -> lower further
            s = 0.5 + (s - 0.5) * (1 + neuroticism * 0.5)
        if d < 0.5:  # Low dopamine -> lower further
            d = 0.5 + (d - 0.5) * (1 + neuroticism * 0.4)
        if n > 0.5:  # High norepinephrine -> higher further
            n = 0.5 + (n - 0.5) * (1 + neuroticism * 0.6)

    # EXTRAVERSION: enhances reward sensitivity (mainly dopamine)
    if extraversion > 0.5:
        if d > 0.5:  # Amplify positive dopamine responses
            d = 0.5 + (d - 0.5) * (1 + extraversion * 0.4)
        if s > 0.5:  # Slight serotonin boost for social positivity
            s = 0.5 + (s - 0.5) * (1 + extraversion * 0.1)

    # AGREEABLENESS: promotes social harmony, reduces conflict
    if agreeableness > 0.5:
        if s > 0.5:  # Enhance serotonin for calm/positive social states
            s = 0.5 + (s - 0.5) * (1 + agreeableness * 0.3)
        if n > 0.5:  # Reduce norepinephrine to lower anger/aggression
            n = 0.5 + (n - 0.5) * (1 - agreeableness * 0.4)

    # OPENNESS: enhances novelty and curiosity responses
    if openness > 0.5:
        if d > 0.5:  # Amplify dopamine for novel stimuli
            d = 0.5 + (d - 0.5) * (1 + openness * 0.3)

    # CONSCIENTIOUSNESS: stabilizes emotional responses
    if conscientiousness > 0.5:
        # Pull toward neutral, stronger for extremes
        d = 0.5 + (d - 0.5) * (1 - conscientiousness * 0.25)
        s = 0.5 + (s - 0.5) * (1 - conscientiousness * 0.25)
        n = 0.5 + (n - 0.5) * (1 - conscientiousness * 0.3)

    # Clamp to [0, 1]
    d = max(0.0, min(1.0, d))
    s = max(0.0, min(1.0, s))
    n = max(0.0, min(1.0, n))

    return d, s, n


# Draw matplotlib output
plt.ion()
fig, ax = plt.subplots(figsize=(4, 4))

# Initial circle with black colour
circle = patches.Circle((0.5, 0.5), 0.4, color=(0, 0, 0))
ax.add_patch(circle)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
fig.canvas.draw()
plt.show(block=False)

# Text in window for monoamine levels and active stimuli
# Text in window for monoamine levels and active stimuli
raw_text = ax.text(0.5, 0.75, "", ha="center", va="center", fontsize=8, color="black", wrap=True)
mod_text = ax.text(0.5, 0.5, "", ha="center", va="center", fontsize=8, color="black", wrap=True)
stimuli_text = ax.text(0.5, 0.1, "", ha="center", va="center", fontsize=7, color="black", wrap=True)


def update_circle(colour, raw_d, raw_s, raw_n, mod_d, mod_s, mod_n, stimuli):
    circle.set_color(colour)
    raw_text.set_text(f"Before Personality:\nDop: {raw_d:.2f} | Ser: {raw_s:.2f} | Ne: {raw_n:.2f}")
    mod_text.set_text(f"After Personality:\nDop: {mod_d:.2f} | Ser: {mod_s:.2f} | Ne: {mod_n:.2f}")
    stim_info =    stim_info = "\n".join([f"{s['name']} ({s['intensity']})" for s in stimuli]) if stimuli else "No active stimuli"
    stimuli_text.set_text(stim_info)
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
            # monoamines reset to baseline each iteration
            serotonin = 0.5
            dopamine = 0.5
            noradrenaline = 0.5 

            # Receive stimuli from the stimulus manager
            stimuli = socket.recv_json()  # list of stimuli dicts
            
            # Update monoamine levels based on stimuli 
            stimuli_counter = 0     
            for s in stimuli:
                scale = s["intensity"] / 200.0 # un estímulo a máxima intensidad desplaza como mucho 0.5 la monoamina correspondiente
                stimuli_counter += 1
                dopamine += s["d"] * scale
                noradrenaline += s["n"] * scale
                serotonin += s["s"] * scale
            

            # Clamp values between 0 and 1
            dopamine = max(0, min(1, dopamine))
            serotonin = max(0, min(1, serotonin))
            noradrenaline = max(0, min(1, noradrenaline))

            # Show levels
            print(f"Monoamines without modulation: Dop={dopamine:.2f} Se={serotonin:.2f} Ne={noradrenaline:.2f}")

            # Modulate values based on PERSONALITY
            mod_dopamine, mod_serotonin, mod_noradrenaline = modulate_substances(dopamine, serotonin, noradrenaline, PERSONALITY2)

            # Determine emotion
            emotion = lovheim_emotion(mod_serotonin, mod_dopamine, mod_noradrenaline)

            # Get colour for the emotion
            colour = EMOTION_COLOURS.get(emotion, (1, 1, 1))

            # Print coloured text in terminal
            print(f"\033[38;2;{int(colour[0]*255)};{int(colour[1]*255)};{int(colour[2]*255)}m{emotion}\033[0m", f" | Dop={dopamine:.2f} Se={serotonin:.2f} Ne={noradrenaline:.2f}")

            # Update circle window
            # update_circle(colour)
            update_circle(colour, dopamine, serotonin, noradrenaline, mod_dopamine, mod_serotonin, mod_noradrenaline, stimuli)
            plt.pause(0.1)

        except KeyboardInterrupt:
            print("Stopped.")
            break

        time.sleep(1)


if __name__ == "__main__":
    main()
