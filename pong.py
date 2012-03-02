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


#----------------------------------------
# Class's
#----------------------------------------

class Mass:

    all_mass = [] # A list of all generated mass's
    
    def __init__(self, pos=(0,0), vel=(0,0)):
        self.pos = pos
        self.vel = vel
        Mass.all_mass.append(self)
    
    def move(self):
        """
        Increment the 
        """
        self.pos = (self.pos[0]+self.vel[0], self.pos[1]+self.vel[1])

class Ball(Mass):

    all_balls = [] # A sub set of mass's that is only the ball objects

    def __init__(self, **kwargs):
        Mass.__init__(self,**kwargs)
        self.radius = kwargs.get('radius',3)
        Ball.all_balls.append(self)
        
    def move(self):
        Mass.move(self)
        if self.pos[1] < 0 or self.pos[1] > screen.get_height():
            self.vel = (self.vel[0], -self.vel[1])
        if self.pos[0] < 0 or self.pos[0] > screen.get_width():
            self.vel = (-self.vel[0], self.vel[1])
            

#----------------------------------------
# Variables
#----------------------------------------

test_rect = pygame.Rect(100,100,10,50);



time_elapsed = 0

#----------------------------------------
# Subroutines
#----------------------------------------

def reset():
    for i in range(30):
        b = Ball(
                pos = (random.random()*screen.get_width(), random.random()*screen.get_height()),
                vel = (random.random()*3                 , random.random()*3                  ),
            )
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
    
    for b in Ball.all_balls:
        b.move()
        pygame.draw.circle(screen, colors['ball'], (int(b.pos[0]),int(b.pos[1])), b.radius) #, width=0


    pygame.draw.rect(screen, colors['bat'], test_rect)
    
    time_elapsed += 1
    
    pygame.display.update()
pygame.quit()

print("Ticks Elapsed: %s" % time_elapsed)