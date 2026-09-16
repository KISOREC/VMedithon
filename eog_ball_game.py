import pygame
import threading
import time
import socket
import json

# ================= SOCKET SETUP =================
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("127.0.0.1", 9000))   # Node TCP server
sock.setblocking(False)

# ================= CONTROL FLAGS =================
move_left = False
move_right = False
blink = False

# 🔒 Blink debounce
blink_locked = False

# ================= WIFI RECEIVE THREAD =================
def eye_control():
    global move_left, move_right, blink

    buffer = ""
    while True:
        try:
            data = sock.recv(1024).decode()
            buffer += data

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                packet = json.loads(line)

                blink = packet.get("blink", 0) == 1
                direction = packet.get("dir", "NEUTRAL")

                move_left = direction == "LEFT"
                move_right = direction == "RIGHT"

        except:
            pass


# Start Wi-Fi listener
threading.Thread(target=eye_control, daemon=True).start()

# ================= PYGAME SETUP =================
pygame.init()
WIDTH, HEIGHT = 800, 500
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("EOG Ball Slider Game – Wireless BCI")

clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 32)

# ================= GAME OBJECTS =================
paddle = pygame.Rect(WIDTH // 2 - 60, HEIGHT - 30, 120, 15)
paddle_speed = 14

ball = pygame.Rect(WIDTH // 2, HEIGHT // 2, 15, 15)
ball_dx = 6
ball_dy = -6

game_over = False

# ================= RESET FUNCTION =================
def reset_game():
    global ball_dx, ball_dy, game_over, blink_locked
    ball.x = WIDTH // 2
    ball.y = HEIGHT // 2
    ball_dx = 6
    ball_dy = -6
    game_over = False
    blink_locked = False

# ================= MAIN LOOP =================
running = True
while running:
    clock.tick(75)
    win.fill((20, 20, 30))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not game_over:
        # Paddle movement
        if move_left:
            paddle.x -= paddle_speed
        if move_right:
            paddle.x += paddle_speed

        paddle.x = max(0, min(WIDTH - paddle.width, paddle.x))

        # Ball movement
        ball.x += ball_dx
        ball.y += ball_dy

        # Wall collision
        if ball.left <= 0 or ball.right >= WIDTH:
            ball_dx *= -1
        if ball.top <= 0:
            ball_dy *= -1

        # Paddle collision
        if ball.colliderect(paddle):
            ball_dy *= -1

        # Game over condition
        if ball.bottom >= HEIGHT:
            game_over = True

    else:
        text = font.render("GAME OVER – Blink to Restart", True, (255, 80, 80))
        win.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))

        # 🔒 Debounced blink restart
        if blink and not blink_locked:
            blink_locked = True
            reset_game()

    # Unlock blink when eye opens
    if not blink:
        blink_locked = False

    # Draw objects
    pygame.draw.rect(win, (0, 200, 255), paddle)
    pygame.draw.ellipse(win, (255, 50, 50), ball)

    pygame.display.update()

pygame.quit()
sock.close()
