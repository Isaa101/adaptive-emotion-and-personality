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
#TO DO
EMOTION_COLOURS = {
    "Joy":      (1.0, 0.95, 0.6),   # Pastel yellow
    "Anger":    (1.0, 0.6, 0.6),    # Soft coral red
    "Fear":     (0.8, 0.8, 1.0),    # Light lavender blue
    #"Sadness":  (0.6, 0.8, 1.0),    # Gentle sky blue      !Not in lovheim_emotion
    "Shame":    (0.9, 0.7, 0.9),    # Muted pink-purple
    "Disgust":  (0.7, 0.9, 0.7),    # Pastel green
    "Interest": (1.0, 0.8, 0.5),    # Warm peach
    "Distress": (1.0, 0.75, 0.8),   # Soft rose pink
    "Neutral":  (0.85, 0.85, 0.85)  # Light grey

}


"""
Define PERSONALITY modulation
Big-five PERSONALITY traits from 0 to 1
"""
#TO DO
PERSONALITY  = {
    "openness":        0,
    "conscientious":   0,
    "extraversion":    0,
    "agreeableness":   1.0,
    "neuroticism":     0,
}

PERSONALITY2 = {
    "openness":        0,
    "conscientious":   0,
    "extraversion":    0,
    "agreeableness":   0,
    "neuroticism":     1.0,
}

def modulate_substances(dopamine, serotonin, norepinephrine):
    """
    Modulate the values of dopamine, serotonin, and noradrenaline
    based on the robot's PERSONALITY
    """

    """
    Add your code here #TO DO
    """
    # Get personality traits (0 to 1 scale)
    openness, conscientiousness, extraversion, agreeableness, neuroticism = PERSONALITY
    
    # NEUROTICISM: Amplifies negative emotional responses
    # Higher neuroticism → lower serotonin and dopamine baselines
    if neuroticism > 0.5:
        serotonin *= (1 - neuroticism * 0.3)  # Reduce serotonin by up to 30%
        dopamine *= (1 - neuroticism * 0.2)   # Reduce dopamine by up to 20%
        norepinephrine *= (1 + neuroticism * 0.4)  # Increase norepinephrine by up to 40%
    
    # EXTRAVERSION: Enhances positive emotional responses
    # Higher extraversion → amplifies dopamine for positive stimuli
    if extraversion > 0.5:
        if dopamine > 0.5:  # Positive dopamine situations
            dopamine *= (1 + extraversion * 0.3)  # Amplify by up to 30%
        if serotonin > 0.5:  # Positive serotonin situations
            serotonin *= (1 + extraversion * 0.2)  # Amplify by up to 20%
    
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
mono_text = ax.text(0.5, 0.5, "", ha="center", va="center", fontsize=10, color="black", wrap=True)
stimuli_text = ax.text(0.5, 0.1, "", ha="center", va="center", fontsize=8, color="black", wrap=True)

def update_circle(colour, dopamine, serotonin, noradrenaline, stimuli):
    circle.set_color(colour)
    mono_text.set_text(f"Dop: {dopamine:.2f}\nSer: {serotonin:.2f}\nNe: {noradrenaline:.2f}")
    stim_info = "\n".join([f"{s['name']} ({s['intensity']})" for s in stimuli]) if stimuli else "No active stimuli"
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
            dopamine, serotonin, noradrenaline = modulate_substances(dopamine, serotonin, noradrenaline)

            # Determine emotion
            emotion = lovheim_emotion(serotonin, dopamine, noradrenaline)

            # Get colour for the emotion
            colour = EMOTION_COLOURS.get(emotion, (1, 1, 1))

            # Print coloured text in terminal
            print(f"\033[38;2;{int(colour[0]*255)};{int(colour[1]*255)};{int(colour[2]*255)}m{emotion}\033[0m", f" | Dop={dopamine:.2f} Se={serotonin:.2f} Ne={noradrenaline:.2f}")

            # Update circle window
            # update_circle(colour)
            update_circle(colour, dopamine, serotonin, noradrenaline, stimuli)
            plt.pause(0.1)

        except KeyboardInterrupt:
            print("Stopped.")
            break

        time.sleep(1)


if __name__ == "__main__":
    main()
