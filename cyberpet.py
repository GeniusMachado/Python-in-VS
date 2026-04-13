import threading
import time
import random

class CyberPet:
    def __init__(self, name):
        self.name = name
        self.energy = 100
        self.happiness = 100
        self.state = "IDLE"  # Current state of the State Machine
        self.is_alive = True

    def brain(self):
        """The 'Complex' logic: A background thread that dictates behavior."""
        while self.is_alive:
            # Automatic status decay
            self.energy -= 2
            self.happiness -= 1
            
            # State Machine transitions
            if self.energy < 20:
                self.state = "SLEEPING"
            elif self.happiness < 30:
                self.state = "SAD"
            elif self.energy > 80 and self.happiness > 80:
                self.state = "ZOOMIES"
            else:
                self.state = "IDLE"

            # Perform actions based on state
            self._render_state()
            time.sleep(3)

    def _render_state(self):
        emojis = {"IDLE": "😐", "SLEEPING": "💤", "SAD": "😢", "ZOOMIES": "🏎️💨"}
        print(f"\n[{self.name} is {self.state} {emojis.get(self.state, '')}]")
        print(f"Energy: {self.energy}% | Happiness: {self.happiness}%")
        if self.energy <= 0:
            print(f"💀 {self.name} has fainted! Game Over.")
            self.is_alive = False

    def feed(self):
        print(f"🍱 You fed {self.name} some digital sushi!")
        self.energy = min(100, self.energy + 30)

    def play(self):
        print(f"🎾 You played fetch with {self.name}!")
        self.happiness = min(100, self.happiness + 40)
        self.energy -= 10

# Initialize the pet
my_pet = CyberPet("Byte")

# Start the 'Brain' thread (Autonomous behavior)
pet_thread = threading.Thread(target=my_pet.brain, daemon=True)
pet_thread.start()

# Interaction Loop
print(f"Welcome to CyberPet! Meet {my_pet.name}.")
while my_pet.is_alive:
    cmd = input("\nCommands: (1) Feed  (2) Play  (3) Quit\n> ")
    if cmd == "1":
        my_pet.feed()
    elif cmd == "2":
        my_pet.play()
    elif cmd == "3":
        my_pet.is_alive = False
        print("Goodbye!")
        break
      
