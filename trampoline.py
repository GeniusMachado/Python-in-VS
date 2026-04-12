import turtle
import time

# 1. Screen Setup
screen = turtle.Screen()
screen.title("Python Trampoline Animation")
screen.bgcolor("skyblue")
screen.setup(width=600, height=400)
screen.tracer(0) # Turns off auto-updates for smoother animation

# 2. Draw the Trampoline
trampoline = turtle.Turtle()
trampoline.hideturtle()
trampoline.penup()
trampoline.goto(-100, -50)
trampoline.pendown()
trampoline.pensize(5)
trampoline.color("black")
trampoline.forward(200) # The jumping surface

# 3. Ball Setup
ball = turtle.Turtle()
ball.shape("circle")
ball.color("red")
ball.penup()
ball.goto(0, 100) # Start height

# 4. Physics Variables
dy = 0          # Vertical velocity (speed and direction)
gravity = -0.1  # Constant downward force
bounce = -0.9   # Reverses direction and keeps 90% of energy

# 5. Animation Loop
while True:
    dy += gravity               # Apply gravity to velocity
    ball.sety(ball.ycor() + dy) # Move ball based on current velocity

    # Collision Detection: Hit the trampoline surface at y = -40
    if ball.ycor() <= -40:
        ball.sety(-40)          # Keep ball on top of surface
        dy *= bounce            # Reverse velocity (Bounce!)

    screen.update()             # Manually refresh the screen
    time.sleep(0.01)            # Small delay for visual speed
