import pygame
import sys
import random
import serial
import serial.tools.list_ports
import math

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1600, 900
PADDLE_WIDTH, PADDLE_HEIGHT = 15, 100
BALL_SIZE = 12
FPS = 60
NEON_COLORS = [
    (0, 100, 255),    # Player blue
    (255, 20, 147),   # AI pink
    (0, 255, 255),    # Cyan
    (255, 105, 180)   # Hot pink
]

# Game variables
player_score = 0
ai_score = 0
game_active = False

# Initialize serial connection
ser = None
try:
    ports = serial.tools.list_ports.comports()
    for port in ports:
        try:
            ser = serial.Serial(port.device, 115200, timeout=0)  # Set timeout to 0 for non-blocking
            print(f"Connected to {port.device}")
            break
        except:
            continue
except:
    print("Serial initialization failed - using keyboard controls")
    ser = None

class Paddle:
    def __init__(self, x, y, is_player=False):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.color = NEON_COLORS[0] if is_player else NEON_COLORS[1]
        self.speed = 8
        self.glow_size = 30
        self.glow_alpha = 100
        self.inner_glow_alpha = 60
        self.tube_width = 4
        self.is_player = is_player
        
    def draw(self, surface):
        # Outer glow
        glow_surf = pygame.Surface((self.rect.width + self.glow_size*2, 
                                  self.rect.height + self.glow_size*2), pygame.SRCALPHA)
        
        # Draw the glowing tube effect
        for i in range(3, 0, -1):
            alpha = self.glow_alpha // (i + 1)
            pygame.draw.rect(glow_surf, (*self.color, alpha), 
                            (self.glow_size - i*2, self.glow_size - i*2,
                             self.rect.width + i*4, self.rect.height + i*4),
                            border_radius=3 + i)
        
        surface.blit(glow_surf, (self.rect.x - self.glow_size, self.rect.y - self.glow_size))
        
        # Inner glow (brighter core)
        inner_glow = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(inner_glow, (*self.color, self.inner_glow_alpha), 
                        (0, 0, self.rect.width, self.rect.height),
                        border_radius=2)
        surface.blit(inner_glow, (self.rect.x, self.rect.y))
        
        # Neon tube (main bright line)
        pygame.draw.rect(surface, self.color, self.rect, self.tube_width, border_radius=2)
        
        # Bright center line
        bright_color = (min(self.color[0] + 100, 255), 
                       min(self.color[1] + 100, 255), 
                       min(self.color[2] + 100, 255))
        center_rect = pygame.Rect(
            self.rect.x + self.tube_width//2,
            self.rect.y + self.tube_width//2,
            self.rect.width - self.tube_width,
            self.rect.height - self.tube_width
        )
        pygame.draw.rect(surface, bright_color, center_rect, 1, border_radius=1)

    def move(self, y):
        self.rect.y = y
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT

class Ball:
    def __init__(self):
        self.reset()
        self.color = random.choice(NEON_COLORS[2:])
        self.glow_size = 15
        self.glow_alpha = 120
        self.inner_glow_alpha = 80
        self.tube_width = 3
        self.hits = 0  # Track consecutive hits
        
    def reset(self):
        self.rect = pygame.Rect(WIDTH // 2 - BALL_SIZE // 2, 
                               HEIGHT // 2 - BALL_SIZE // 2, 
                               BALL_SIZE, BALL_SIZE)
        self.dx = 5 * random.choice((1, -1))
        self.dy = 5 * random.choice((1, -1))
        self.hits = 0
        
    def draw(self, surface):
        # Outer glow
        glow_surf = pygame.Surface((self.rect.width + self.glow_size*2, 
                                   self.rect.height + self.glow_size*2), pygame.SRCALPHA)
        
        # Create concentric glowing circles
        for i in range(3, 0, -1):
            alpha = self.glow_alpha // (i + 1)
            radius = self.rect.width//2 + i*2
            pygame.draw.circle(glow_surf, (*self.color, alpha), 
                             (glow_surf.get_width()//2, glow_surf.get_height()//2), 
                             radius)
        
        surface.blit(glow_surf, (self.rect.x - self.glow_size, self.rect.y - self.glow_size))
        
        # Inner glow
        inner_glow = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.circle(inner_glow, (*self.color, self.inner_glow_alpha), 
                         (self.rect.width//2, self.rect.height//2), 
                         self.rect.width//2)
        surface.blit(inner_glow, (self.rect.x, self.rect.y))
        
        # Bright neon ring
        pygame.draw.circle(surface, self.color, self.rect.center, self.rect.width//2, self.tube_width)
        
        # Bright center dot
        bright_color = (min(self.color[0] + 100, 255), 
                       min(self.color[1] + 100, 255), 
                       min(self.color[2] + 100, 255))
        pygame.draw.circle(surface, bright_color, self.rect.center, self.rect.width//4)

    def move(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        
        if self.rect.top <= 0 or self.rect.bottom >= HEIGHT:
            self.dy *= -1
            
        if self.rect.left <= 0:
            self.reset()
            return "ai"
        if self.rect.right >= WIDTH:
            self.reset()
            return "player"
        return None

def main():
    global player_score, ai_score, game_active
    
    # Set up the display
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Neon Pong - Block Scoring")
    clock = pygame.time.Clock()

    # Create game objects
    player_paddle = Paddle(50, HEIGHT // 2 - PADDLE_HEIGHT // 2, is_player=True)
    ai_paddle = Paddle(WIDTH - 50 - PADDLE_WIDTH, HEIGHT // 2 - PADDLE_HEIGHT // 2)
    ball = Ball()
    
    # Font
    font = pygame.font.Font(None, 74)
    small_font = pygame.font.Font(None, 36)
    hit_font = pygame.font.Font(None, 24)
    
    # Moving average filter for serial smoothing
    READING_BUFFER_SIZE = 12
    distance_readings = []  # Buffer to store recent distance readings
    last_serial_y = None  # Store last valid serial position
    
    # Game loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_active:
                    game_active = True
                elif event.key == pygame.K_ESCAPE:
                    running = False
        
        # Fill the screen with black
        screen.fill((0, 0, 0))
        
        # Draw dashed center line
        pygame.draw.line(screen, (50, 50, 50), (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), 1)
        
        # Draw scores
        player_text = font.render(str(player_score), True, NEON_COLORS[0])
        ai_text = font.render(str(ai_score), True, NEON_COLORS[1])
        screen.blit(player_text, (WIDTH // 4 - player_text.get_width() // 2, 20))
        screen.blit(ai_text, (3 * WIDTH // 4 - ai_text.get_width() // 2, 20))
        
        # Get player input
        keys = pygame.key.get_pressed()
        
        # Read from serial if connected (non-blocking)
        serial_y = last_serial_y
        if ser:
            try:
                if ser.in_waiting > 0:  # Check if data is available
                    ser.write(b' ')  # Send trigger
                    distance = ser.read(ser.in_waiting).decode('utf-8', errors='ignore').strip()
                    if distance:
                        try:
                            distance = int(distance.split('\n')[-1])  # Get latest value
                            # Clamp distance to 2 cm - 12 cm
                            distance = max(2, min(12, distance))
                            # Add to buffer
                            distance_readings.append(distance)
                            if len(distance_readings) > READING_BUFFER_SIZE:
                                distance_readings.pop(0)  # Remove oldest
                            # Compute moving average
                            avg_distance = sum(distance_readings) / len(distance_readings)
                            serial_y = max(0, min(HEIGHT - PADDLE_HEIGHT, 
                                                int((avg_distance - 2) * (HEIGHT - PADDLE_HEIGHT) / (12 - 2))))
                            last_serial_y = serial_y  # Update last valid position
                        except ValueError:
                            pass
            except:
                pass
        
        # Move player paddle
        if serial_y is not None:
            player_paddle.move(serial_y)
        else:
            if keys[pygame.K_UP]:
                player_paddle.move(player_paddle.rect.y - player_paddle.speed)
            if keys[pygame.K_DOWN]:
                player_paddle.move(player_paddle.rect.y + player_paddle.speed)
        
        # Simplified AI - just follows ball without perfection
        if game_active:
            if ai_paddle.rect.centery < ball.rect.centery:
                ai_paddle.move(ai_paddle.rect.y + ai_paddle.speed * 0.5)
            elif ai_paddle.rect.centery > ball.rect.centery:
                ai_paddle.move(ai_paddle.rect.y - ai_paddle.speed * 0.5)
        
        # Move ball and check for scoring
        if game_active:
            result = ball.move()
            if result == "player":
                player_score += 1 # Score equals number of hits
                game_active = False
            elif result == "ai":
                ai_score += 1
                game_active = False
            
            # Check collisions
            if ball.rect.colliderect(player_paddle.rect):
                ball.hits += 1
                ball.color = random.choice(NEON_COLORS[2:])
                ball.dx *= -1.05
                if abs(ball.dx) < 5:
                    ball.dx = 5 if ball.dx > 0 else -5
            elif ball.rect.colliderect(ai_paddle.rect):
                ball.color = random.choice(NEON_COLORS[2:])
                ball.dx *= -1
        
        # Draw paddles and ball
        player_paddle.draw(screen)
        ai_paddle.draw(screen)
        ball.draw(screen)
        
        # Show hit counter
        if game_active:
            hit_text = hit_font.render(f"Hits: {ball.hits}", True, NEON_COLORS[0])
            screen.blit(hit_text, (20, 20))
        
        # Show start message if game isn't active
        if not game_active:
            start_text = small_font.render("Press SPACE to start", True, (200, 200, 200))
            screen.blit(start_text, (WIDTH // 2 - start_text.get_width() // 2, 
                                   HEIGHT // 2 - start_text.get_height() // 2))
        
        # Update the display
        pygame.display.flip()
        clock.tick(FPS)
    
    # Clean up
    if ser and ser.is_open:
        ser.close()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()