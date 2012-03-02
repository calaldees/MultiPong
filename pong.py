#!/usr/bin/python

import pygame

import random
import argparse
import sys
import socket
from select import select
import json

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
    zone        = (  0,   0, 100),
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
    
    def remove(self):
        Mass.all_mass.remove(self)
    
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
    
    def remove(self):
        Ball.all_balls.remove(self)
        Mass.remove(self)
    
    def move(self):
        Mass.move(self)
        # Bounce ball off top and bottom of screen by inverting velocity
        if self.pos[1] < 0 or self.pos[1] > screen.get_height():
            self.vel = (self.vel[0], -self.vel[1])
            

class EventZone():
    
    all_zones = []
    
    def __init__(self, rectangle):
        self.rectangle = rectangle
        self.masss_in_zone = []
        EventZone.all_zones.append(self)
    
    def trigger_mass_events(self):
        # Leave area event
        for m in self.masss_in_zone:
            if not self.rectangle.collidepoint(m.pos): # If mass has moved out of the zone then perform an event
                self.event_leave(m)
        
        # Enter area event
        for m in Mass.all_mass:
            if m not in self.masss_in_zone and self.rectangle.collidepoint(m.pos):
                self.masss_in_zone.append(m)
                self.event_enter(m)

    # Null event methods for overriding
    def event_enter(self, m):
        pass
    def event_leave(self, m):
        pass
        
        
    
class NetZone(EventZone):
    
    def __init__(self, rectangle=None):
        # Shortcuts to define dead zone areas from strings. Automatically creates rectangle areas
        default_zone_width = 20
        if   rectangle == 'left':
            rectangle = pygame.Rect( 0                                   ,  0                 , default_zone_width, screen.get_height() )
        elif rectangle == 'right':
            rectangle = pygame.Rect( screen.get_width()-default_zone_width, default_zone_width, default_zone_width, screen.get_height() )
        # Call super contructor
        EventZone.__init__(self, rectangle)
    
    def event_leave(self, m):
        self.masss_in_zone.remove(m)
        m.remove()
        print("mass removed: %s" % m)
    
    def event_enter(self, m):
        print("net send: %s" % m)


class ScoreZone(EventZone):
    
    def __init__(self, rectangle=None, score_func=None):
        # Shortcuts to define score zones - bit cumbersom .. but all events are delt with in the same way
        default_zone_width = 20 * 2
        if   rectangle == 'left':
            rectangle = pygame.Rect( 0-default_zone_width,  0-default_zone_width, default_zone_width, screen.get_height()+default_zone_width*2 )
        elif rectangle == 'right':
            rectangle = pygame.Rect( screen.get_width()  ,  0-default_zone_width, default_zone_width, screen.get_height()+default_zone_width*2 )
        self.score_func = score_func
        # Call super contructor
        EventZone.__init__(self, rectangle)
        
    def event_enter(self, m):
        if callable(self.score_func):
            self.score_func(m)
        print("score!: %s" % m)
        m.remove()
    

#----------------------------------------
# Variables
#----------------------------------------

test_rect = pygame.Rect(100,100,10,50);



time_elapsed = 0

#----------------------------------------
# Subroutines
#----------------------------------------

def reset():
    global time_elapsed
    EventZone.all_zones = []
    NetZone('left')
    ScoreZone('right')
    time_elapsed = 0


#----------------------------------------
# Main Loop
#----------------------------------------

def mainloop(ssock, left, right, inputs):
    global time_elapsed

    reset()
    running = True
    while running:
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            #elif event.type == pygame.MOUSEMOTION:
            
        screen.fill(colors['background'])
        
        masss_to_create = 30 - len(Mass.all_mass)
        for i in range(masss_to_create):
            max_vel = 3
            b = Ball(
                    pos = (screen.get_width()/2, screen.get_height()/2), #(random.random()*screen.get_width(), random.random()*screen.get_height()),
                    vel = (random.random()*max_vel-max_vel/2 , random.random()*max_vel-max_vel/2 ),
                )
            
        
        for z in EventZone.all_zones:
            pygame.draw.rect(screen, colors['zone'], z.rectangle)
            z.trigger_mass_events()
        
        for b in Ball.all_balls:
            b.move()
            pygame.draw.circle(screen, colors['ball'], (int(b.pos[0]),int(b.pos[1])), b.radius) #, width=0


        pygame.draw.rect(screen, colors['bat'], test_rect)
        
        time_elapsed += 1
        
        pygame.display.update()

        l = []
        if ssock: l.append(ssock)
        if left: l.append(left)
        if right: l.append(right)
        if inputs: l.append(inputs)
        [readable, writable, errors] = select(l, [], [], 0)
        for r in readable:
            if r == ssock:
                continue
                tmp_sock = ssock.accept()
                d = tmp_sock.recv(1024)
                if d.startswith("left"):
                    left = tmp_sock
                if d.startswith("right"):
                    right = tmp_sock
            if r == left:
                pass
            if r == right:
                pass
            if r == inputs:
                pass
        
    pygame.quit()

    print("Ticks Elapsed: %s" % time_elapsed)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--left')
    parser.add_argument('--right')
    parser.add_argument('--inputs')
    parser.add_argument('--port', type=int, default=47474)
    args = parser.parse_args(argv[1:])

    ssock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ssock.bind(("0.0.0.0", args.port))

    left = None
    if args.left:
        n, p = args.left.split(":")
        left = socket.create_connection((n, int(p)))
        left.send("left")

    right = None
    if args.right:
        n, p = args.right.split(":")
        right = socket.create_connection((n, int(p)))
        right.send("right")

    inputs = None
    if args.inputs:
        n, p = args.inputs.split(":")
        inputs = socket.create_connection((n, int(p)))

    mainloop(ssock, left, right, inputs)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
