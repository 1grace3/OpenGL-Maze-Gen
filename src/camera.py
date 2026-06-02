#camera.py

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

class Camera:
    def __init__(self):
        self.position = [2.0, 0.0, 2.0]
        self.yaw = 0.0
        self.noclip = False
        
        glMatrixMode(GL_MODELVIEW)
        gluLookAt(self.position[0], self.position[1], self.position[2], 2, 0, 3, 0, 1, 0)
        self.viewMatrix = glGetFloatv(GL_MODELVIEW_MATRIX)
        glLoadIdentity()

        #Camera settings
        self.up_down_angle = 0.0
        self.mouse_sensitivity = 0.1
        self.move_speed = 0.15

        #Head bob settings
        self.bob_timer = 0.0
        self.bob_speed = 0.2
        self.bob_vert_amount = 0.1
        self.bob_horiz_amount = 0.08
        self.bob_x = 0.0
        self.bob_y = 0.0
        self.smooth_factor = 0.2

    def get_position(self):
        return tuple(self.position)

    def update(self, keypress, mouseMove, maze):
        dx, dy = mouseMove
        self.yaw += dx * self.mouse_sensitivity
        self.up_down_angle += dy * self.mouse_sensitivity
        self.up_down_angle = max(-80, min(80, self.up_down_angle))
        
        #head bobbing
        moving = ( keypress[pygame.K_w] or keypress[pygame.K_s] or  keypress[pygame.K_a] or keypress[pygame.K_d] )
        if moving:
            self.bob_timer += self.bob_speed
            target_bob_y = math.sin(self.bob_timer) * self.bob_vert_amount
            target_bob_x = math.sin(self.bob_timer * 0.5) * self.bob_horiz_amount
        else:
            target_bob_y = 0.0
            target_bob_x = 0.0
        self.bob_y += (target_bob_y - self.bob_y) * self.smooth_factor
        self.bob_x += (target_bob_x - self.bob_x) * self.smooth_factor
        
        #collisions and movement
        move_forward = 0.0
        move_right = 0.0
        if keypress[pygame.K_w]:   # forward
            move_forward += self.move_speed
        if keypress[pygame.K_s]:   # backward
            move_forward -= self.move_speed
        if keypress[pygame.K_d]:   # right
            move_right += self.move_speed
        if keypress[pygame.K_a]:   # left
            move_right -= self.move_speed
        
        if move_forward != 0 or move_right != 0:
            rad = math.radians(self.yaw)
            forward_x = math.sin(rad)
            forward_z = -math.cos(rad)
            right_x = math.cos(rad)
            right_z = math.sin(rad)
            
            new_x = self.position[0] + forward_x * move_forward + right_x * move_right
            new_z = self.position[2] + forward_z * move_forward + right_z * move_right

            if self.noclip:
                self.position[0] = new_x
                self.position[2] = new_z
            else:
                if maze.can_move_to(new_x, new_z, radius=0.3):
                    self.position[0] = new_x
                    self.position[2] = new_z
                else:
                    if maze.can_move_to(new_x, self.position[2], radius=0.3):
                        self.position[0] = new_x
                    elif maze.can_move_to(self.position[0], new_z, radius=0.3):
                        self.position[2] = new_z
        
        glLoadIdentity()
        glRotatef(self.up_down_angle, 1, 0, 0)
        glRotatef(self.yaw, 0, 1, 0)
        glTranslatef(self.bob_x, self.bob_y, 0)
        glTranslatef(-self.position[0], -self.position[1], -self.position[2])
        self.viewMatrix = glGetFloatv(GL_MODELVIEW_MATRIX)


    def reset(self):
        self.position = [2.0, 0.0, 2.0]
        self.yaw = 0.0
        self.up_down_angle = 0.0
        self.bob_timer = 0.0
        self.bob_x = 0.0
        self.bob_y = 0.0

        glLoadIdentity()
        gluLookAt(2, 0, 2, 2, 0, 3, 0, 1, 0)
        self.viewMatrix = glGetFloatv(GL_MODELVIEW_MATRIX)
        glLoadIdentity()