import pygame

import random

#----------------------------------------
# Pygame Setup
#----------------------------------------
pygame.init()     
pygame.display.set_mode((640, 480))
screen = pygame.display.get_surface()
clock = pygame.time.Clock()

#----------------------------------------
# Constants
#----------------------------------------
colors = dict(
    background  = (  0,   0,   0),
    ball        = (255, 255, 255),
    bat         = (255, 255,   0),
)

max_balls = 30


#----------------------------------------
# Class's
#----------------------------------------

class Mass:
    def __init__(self): #xpos, ypos, size
        self.xpos  = 0 #xpos
        self.ypos  = 0 #ypos
        self.size  = 0 #size
        self.x_vel = 0
        self.y_vel = 0
        self.size  = 0

#----------------------------------------
# Variables
#----------------------------------------

test_rect = pygame.Rect(100,100,10,50);
#blocks = [Mass() for i in range(num_blocks)];

time_elapsed = 0

#----------------------------------------
# Subroutines
#----------------------------------------

def reset():
    time_elapsed = 0


#----------------------------------------
# Main Loop
#----------------------------------------

reset()
running = True
while running:
    clock.tick(60)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
        #elif event.type == pygame.MOUSEMOTION:
        
    screen.fill(colors['background'])
    
    #for m in blocks:

    pygame.draw.rect(screen, colors['bat'], test_rect)
    
    time_elapsed += 1
    
    pygame.display.update()
pygame.quit()

print("Ticks Elapsed: %s" % time_elapsed)