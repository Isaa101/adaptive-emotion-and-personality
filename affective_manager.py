"""
PROGRAM 2 — affective_processor.py
This program receives stimuli, computes monoamines, prints colour-coded emotions,
and shows a coloured circle window.
"""

import zmq
import time
import matplotlib.pyplot as plt
import matplotlib.patches as patches

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
        
    return "Neutral"  # fallback

"""
Emotion colours in RGB format
For example:
Red:   (1, 0, 0)
Green: (0, 1, 0)
Blue:  (0, 0, 1)
"""
EMOTION_COLOURS = {
    "Joy":     (0.8, 0.8, 0.8),
    "Anger":   (0.8, 0.8, 0.8),
    "Fear":    (0.8, 0.8, 0.8),
    "Sadness": (0.8, 0.8, 0.8),
    "Shame":   (0.8, 0.8, 0.8),
    "Disgust": (0.8, 0.8, 0.8),
    "Interest":(0.8, 0.8, 0.8),
    "Distress":(0.8, 0.8, 0.8),
    "Neutral": (0.8, 0.8, 0.8)
}


"""
Define PERSONALITY modulation
Big-five PERSONALITY traits from 0 to 1
"""
PERSONALITY  = {
    "openness":        0.5,
    "conscientious":   0.5,
    "extraversion":    0.5,
    "agreeableness":   0.5,
    "neuroticism":     0.5,
}

def modulate_substances(d, s, n):
    """
    Modulate the values of dopamine, serotonin, and noradrenaline
    based on the robot's PERSONALITY
    """

    """
    Add your code here
    """

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


def update_circle(colour):
    """
    Update circle colour
    """

    # Set circle colour
    circle.set_color(colour)
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
            stimuli = socket.recv_json()  # list of stimuli dicts

            # Apply effects from all active stimuli
            for s in stimuli:
                # Scale intensity to a value between 0 and 0.5
                scale = s["intensity"] / 200.0
                dopamine = 0.5 + s["d"] * scale
                serotonin = 0.5 +  s["s"] * scale
                noradrenaline = 0.5 + s["n"] * scale

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
            update_circle(colour)

        except KeyboardInterrupt:
            print("Stopped.")
            break

        time.sleep(1)


if __name__ == "__main__":
    main()
