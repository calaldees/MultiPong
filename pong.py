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
    
    def __init__(self, pos=(0,0), vel=(0,0), mass=10, **kwargs):
        self.pos     = pos
        self.pos_old = pos
        self.vel   = vel
        self.force = (0,0)
        self.mass  = float(mass)
        Mass.all_mass.append(self)

    @property
    def rectangle(self):
        """
        Should be overridden by extending class's
        """
        return pygame.Rect(self.pos[0], self.pos[1], 1, 1)

    @property
    def movement_bounding_rect(self):
        max_x = max(self.pos[0], self.pos_old[0])
        min_x = min(self.pos[0], self.pos_old[0])
        max_y = max(self.pos[1], self.pos_old[1])
        min_y = min(self.pos[1], self.pos_old[1])
        return pygame.Rect(min_x, min_y, max_x-min_x, max_y-min_y)

    def flip_vel_x(self):
        self.vel = (-self.vel[0],  self.vel[1])
    def flip_vel_y(self):
        self.vel = ( self.vel[0], -self.vel[1])

    def set_pos(self, pos):
        self.pos_old = self.pos
        self.pos = pos

    def add_force(self, force):
        self.force = (self.force[0]+float(force[0]), self.force[1]+float(force[1]))
    
    def remove(self):
        Mass.all_mass.remove(self)

    def apply_force(self):
        if self.force and self.force != (0,0):
            self.vel = (self.vel[0] + self.force[0]/self.mass, self.vel[1] + self.force[1]/self.mass)
            self.force = (0,0) # Once the force is applied, reset it to zero
    
    def move(self):
        """
        Increment the mass's position based on velocity
        """
        self.set_pos( (self.pos[0]+self.vel[0], self.pos[1]+self.vel[1]) )



class Ball(Mass):

    all_balls = [] # A sub set of mass's that is only the ball objects

    def __init__(self, *args, **kwargs):
        Mass.__init__(self, *args, **kwargs)
        self.radius    = kwargs.get('radius',3) # AllanC - BUG! NAME!! it's not really the radius! it's the diameter!
        self.rectangle = pygame.Rect(self.pos[0], self.pos[1], self.radius, self.radius)
        Ball.all_balls.append(self)

    @property
    def rectangle_old(self):
        #if self.pos_old:
            return pygame.Rect(self.pos_old[0], self.pos_old[1], self.rectangle.width, self.rectangle.height)
        #else:
        #    return self.rectangle
    
    @property
    def movement_bounding_rect(self):
        return self.rectangle.union(self.rectangle_old)

    def set_pos(self, pos):
        Mass.set_pos(self, pos)
        self.rectangle.x = pos[0]
        self.rectangle.y = pos[1]
    
    def remove(self):
        Ball.all_balls.remove(self)
        Mass.remove(self)
    
    def move(self):
        Mass.move(self)
        # Bounce ball off top and bottom of screen by inverting velocity
        # AllanC - to be replaced by applying vertical force to mass rather than crudely fliping vel
        if self.pos[1] < 0 or self.pos[1] > screen.get_height():
            self.flip_vel_y()


class Bat(Mass):

    all_bats = []
    air_viscosity = 0.96

    def __init__(self, *args, **kwargs):
        Mass.__init__(self, *args, **kwargs)
        Bat.all_bats.append(self)
        pos  = kwargs.get('pos' , ( 0, 0))
        size = kwargs.get('size', (10,50))
        self.rectangle = pygame.Rect(pos[0], pos[1], size[0], size[1])
        self.pevious_collition_with_balls_tracker = []

    def set_pos(self, pos):
        Mass.set_pos(self, pos)
        self.rectangle.x = pos[0]
        self.rectangle.y = pos[1]
    
    def move(self):
        Mass.move(self)
        # Bounce ball off top and bottom of screen by inverting velocity
        if self.rectangle.y < 0 or self.rectangle.bottom > screen.get_height():
            self.vel = (self.vel[0], -self.vel[1])
    
    @staticmethod
    def apply_air_viscocity_to_all_bats():
        for bat in Bat.all_bats:
            bat.vel = (bat.vel[0]*Bat.air_viscosity, bat.vel[1]*Bat.air_viscosity)
            
    @staticmethod
    def apply_ball_collisions_for_all_bats():
        for bat in Bat.all_bats:
            pevious_collition_with_balls_tracker     = bat.pevious_collition_with_balls_tracker
            bat.pevious_collition_with_balls_tracker = []
            for ball in Ball.all_balls:
                # Don't allow collitions with the same bat for sequential iterations
                if ball in pevious_collition_with_balls_tracker:
                    continue
                if bat.rectangle.colliderect(ball.movement_bounding_rect):
                    bat.pevious_collition_with_balls_tracker.append(ball) # Track collition with this ball to prevent duplicate interations
                    # At this point it becomes relevent what direction the two objects were traveling in order to resolve impulse
                    # Every action has an equal and opposite reaction.
                    # We need a force to entirely reverse the ball's direction, that force must in turn be applyed to the bat. The bat has a much higher mass so the kickback is minimal
                    # The impuse of the bat must be taken into account
                    #  we have posibilitys
                    #    bat and ball are moving in opposite directions
                    #    bat and ball are moving in the same direction
                    # we need to know the 'Relative' velocity between the two colliding objects
                    
                    relative_velocity = bat.vel[0] - ball.vel[0]
                    
                    impulse_ball = 2 * ball.mass * relative_velocity # Force to reflect relative velocity
                    
                    ball.add_force(( impulse_ball,0))
                    bat .add_force((-impulse_ball,0))
                    
                    # To prevent spazzing - if the objects collide, move ball outside each other to prevent repeated collitions
                    if ball.pos_old > bat.pos_old:
                        ball.set_pos((bat.rectangle.right             +1, ball.pos[1]))
                    else:
                        ball.set_pos((bat.rectangle.left -ball.radius -1, ball.pos[1]))
                    


class EventZone():
    
    all_zones = []
    
    def __init__(self, rectangle):
        self.rectangle = rectangle
        self.masss_in_zone = []
        EventZone.all_zones.append(self)
    
    def trigger_mass_events(self):
        # Enter area event
        for m in Mass.all_mass:
            if m not in self.masss_in_zone and self.rectangle.colliderect(m.movement_bounding_rect):
                self.masss_in_zone.append(m)
                self.event_enter(m)

        # Leave area event
        for m in self.masss_in_zone:
            if not self.rectangle.colliderect(m.rectangle): # If mass has moved out of the zone then perform an event
                self.event_leave(m)

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
        #print("mass removed: %s" % m)
    
    def event_enter(self, m):
        #print("net send: %s" % m)
        pass


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
        #print("score!: %s" % m)
        m.remove()


#----------------------------------------
# Variables
#----------------------------------------

Bat(pos=(100,100), size=(10,50), mass=100)

last_mouse_pos = None

time_elapsed = 0

#----------------------------------------
# Subroutines
#----------------------------------------

def reset():
    global time_elapsed
    global last_mouse_pos
    EventZone.all_zones = []
    NetZone('left')
    ScoreZone('right')
    time_elapsed = 0


#----------------------------------------
# Main Loop
#----------------------------------------

def mainloop(args, ssock, inputs):
    global time_elapsed
    global last_mouse_pos

    reset()
    running = True
    keys    = {}
    left    = None
    right   = None
    while running:
        clock.tick(60)
        
        # Inputs
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            #if event.type == pygame.MOUSEMOTION:
            #    if last_mouse_pos:
            #        mouse_diff = (event.pos[0]-last_mouse_pos[0], event.pos[1]-last_mouse_pos[1])
            #        Bat.all_bats[0].add_force(mouse_diff)
            #    last_mouse_pos = (event.pos[0], event.pos[1])


        bat  = Bat.all_bats[0]
        f    = 20
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]: running=False
        if keys[pygame.K_UP    ]: bat.add_force(( 0,-f))
        if keys[pygame.K_DOWN  ]: bat.add_force(( 0, f))
        if keys[pygame.K_LEFT  ]: bat.add_force((-f, 0))
        if keys[pygame.K_RIGHT ]: bat.add_force(( f, 0))


        # Black screen
        screen.fill(colors['background'])
        
        # Create new Balls for testing
        masss_to_create = 30 - len(Mass.all_mass)
        for i in range(masss_to_create):
            max_vel = 3
            b = Ball(
                    pos = (screen.get_width()/2, screen.get_height()/2), #(random.random()*screen.get_width(), random.random()*screen.get_height()),
                    vel = (random.random()*max_vel-max_vel/2 , random.random()*max_vel-max_vel/2 ),
                )
        
        # Zone events
        for z in EventZone.all_zones:
            pygame.draw.rect(screen, colors['zone'], z.rectangle)
            z.trigger_mass_events()
        
        # Apply forces and move all mass's
        Bat.apply_ball_collisions_for_all_bats()
        for m in Mass.all_mass:
            m.apply_force()
            m.move()
        Bat.apply_air_viscocity_to_all_bats()
        
        
        # Draw balls
        for b in Ball.all_balls:
            pygame.draw.circle(screen, colors['ball'], (int(b.pos[0]+b.radius/2),int(b.pos[1]+b.radius/2)), b.radius) #, width=0
        # Draw bats
        for bat in Bat.all_bats:
            pygame.draw.rect(screen, colors['bat'], bat.rectangle)
        
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
                d = r.recv(1024)
                print "from left:", d
            if r == right:
                d = r.recv(1024)
                print "from right:", d
            if r == inputs:
                d = r.recv(1024)
                if d:
                    d = json.loads(d)
                    print "from inputs:", d
                    if d['action'] == "hello":
                        print "responding to hello"
                        inputs.send(json.dumps({'action':'hello', 'value':'screen', 'port': args.port})+"\n")
                    if d['action'] == "left":
                        print "adding left"
                        left = socket.create_connection((d['value'], int(d['port'])))
                    if d['action'] == "right":
                        print "adding right"
                        right = socket.create_connection((d['value'], int(d['port'])))
        
    pygame.quit()

    print("Ticks Elapsed: %s" % time_elapsed)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--inputs')
    parser.add_argument('--bind', default="0.0.0.0")
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args(argv[1:])

    ssock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ssock.bind((args.bind, args.port))

    inputs = None
    if args.inputs:
        n, p = args.inputs.split(":")
        inputs = socket.create_connection((n, int(p)))

    mainloop(args, ssock, inputs) #left, right,


if __name__ == "__main__":
    sys.exit(main(sys.argv))

