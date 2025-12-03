# Aina Crespi Hromcova
# Isabel Gregorio Díez
"""
PROGRAM 1 — stimulus_sender.py
This program defines a set of STIMULI with their values and sends them to the affective processor.
The user can insert the STIMULI desired to active different emotions.
"""

import zmq
import time
import threading
from queue import Queue

"""
Define the STIMULI with their names and effects on monoamines
"""
STIMULI = {
    "touch":  {"d": 1,  "s": 1,  "n": -1}, # Joy
    "push": {"d": 1,  "s": -1,  "n": -1}, # Anger
    "criticism": {"d": -1,  "s": -1,  "n": -1}, # Shame
    "reward": {"d": 1,  "s": 1,  "n": 1}, # Interest

    "threat": {"d": 1,  "s": -1, "n": -1}, # Fear
    "broccoli": {"d": -1,  "s": 1,  "n": -1}, # Disgust
    "exam": {"d": -1,  "s": -1,  "n": 1}, # Distress
    "gift": {"d": 1,  "s": 1,  "n": -1} # Surprise

}


class Stimulus:
    """
    Stimulus object
    """

    def __init__(self, name, dop, ser, ne, intensity=100, decay=5):
        """
        Initialize a stimulus
        """

        # Class variables
        self.name = name
        self.dop = dop
        self.ser = ser
        self.ne = ne
        self.intensity = intensity
        self.decay_rate = decay

    def decay(self):
        """
        Reduce intensity by decay rate each time step
        """

        # Reduce intensity by decay rate each time step
        if self.intensity > 0: self.intensity -= self.decay_rate

    def is_active(self):
        """
        Stimulus is active if its intensity is greater than 0
        """

        # Stimulus is active if its intensity is greater than 0
        return self.intensity > 0

    def to_dict(self):
        """
        Convert stimulus to a dictionary
        """

        # Convert stimulus to a dictionary to be sent to the affective processor
        return {"name": self.name, "d": self.dop, "s": self.ser, "n": self.ne, "intensity": self.intensity}

class StimulusManager:
    """
    Manages all STIMULI and updates intensities
    """

    def __init__(self):
        """
        Initialize the stimulus manager
        """

        # Class variables
        self.active_STIMULI = {}
        self.lock = threading.Lock()

    def add_stimulus(self, name):
        """
        Add a stimulus to the list of active STIMULI
        """

        # Check if the stimulus is defined
        if name not in STIMULI:
            print(f"Unknown stimulus '{name}'... Wrong name or not in the db...")
            return

        # Get stimulus parameters
        params = STIMULI[name]

        # Create a new stimulus
        stim = Stimulus(name, params["d"], params["s"], params["n"])

        # Add stimulus to the list of active STIMULI
        with self.lock:
            self.active_STIMULI[name] = stim

        # Print a message
        print(f"→ Stimulus activated: {name} with maximum intensity")

    def update(self):
        """
        Decay all active STIMULI and remove those at 0 intensity
        """

        # Decay all active STIMULI and remove those at 0 intensity
        with self.lock:
            # Loop through all active STIMULI
            for s in list(self.active_STIMULI.values()):
                # Apply decay rate
                s.decay()

                # Remove stimulus if it is not active
                if not s.is_active(): del self.active_STIMULI[s.name]

    def get_active(self):
        """
        Get all active STIMULI as a list of dictionaries
        """

        # Get all active STIMULI as a list of dictionaries
        with self.lock:
            # Return a list of dictionaries
            return [s.to_dict() for s in self.active_STIMULI.values()]

def keyboard_listener(queue):
    """
    Non-blocking keyboard listener thread
    """

    # Loop until the user quits
    while True:
        # Request a stimulus
        print("Enter a stimulus: ")

        # Get the user input
        user_input = input().strip().lower()
        # Put the user input in the queue
        queue.put(user_input)

        # Check if the user wants to quit
        if user_input == "q":
            break

def main():
    """
    Main function
    """

    # ZMQ setup
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:5555")

    # Create a stimulus manager
    stim_manager = StimulusManager()
    command_queue = Queue()

    # Print a message
    print("Stimulus manager running...\n")

    # Start keyboard thread
    thread = threading.Thread(target=keyboard_listener, args=(command_queue,), daemon=True)
    thread.start()

    # Loop until the user quits
    try:
        while True:
            # Check if a new command has arrived
            while not command_queue.empty():
                # Get the command from the queue
                cmd = command_queue.get()

                # Check if the user wants to quit
                if cmd == "q": return

                # Add necessary STIMULI to the list of active STIMULI
                stim_manager.add_stimulus(cmd)

            # Update intensities
            stim_manager.update()

            # Send all active STIMULI
            active = stim_manager.get_active()
            socket.send_json(active)

            # Sleep for 1 second
            time.sleep(1)

    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
