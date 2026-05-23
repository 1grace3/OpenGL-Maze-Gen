#Maze.py

import random
import math

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
    
    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return False
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
        return True


class Maze:
    CELL_SIZE = 4.0
    WALL_THICKNESS = 0.3
    WALL_HEIGHT = 4.0

    def __init__(self, width, height, wall_tex, floor_tex, ceil_tex):
        self.width = width
        self.height = height
        self.cells = width * height
        self.walls = set()
        self.maze_walls = set()

        self.wall_tex = wall_tex 
        self.floor_tex = floor_tex
        self.ceil_tex = ceil_tex

        for y in range(height):
            for x in range(width):
                if x < width - 1:
                    self.walls.add(((x, y), (x + 1, y)))
                if y < height - 1:
                    self.walls.add(((x, y), (x, y + 1)))
        
        self.generate()
        self.exit_cell = self.find_exit_position()
    
    def generate(self):
        walls = list(self.walls)
        random.shuffle(walls)
        
        uf = UnionFind(self.cells)
        
        def cell_id(x, y): 
            return y * self.width + x
        
        for (x1, y1), (x2, y2) in walls:
            if uf.union(cell_id(x1, y1), cell_id(x2, y2)):
                continue
            else:
                self.maze_walls.add(((x1, y1), (x2, y2)))
                
    def draw(self):
        cell = self.CELL_SIZE
        h = self.WALL_HEIGHT
        thick = self.WALL_THICKNESS

        glEnable(GL_TEXTURE_2D)
        #Floor
        glBindTexture(GL_TEXTURE_2D, self.floor_tex)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0);                       glVertex3f(0, -1, 0)
        glTexCoord2f(self.width, 0);              glVertex3f(self.width*cell, -1, 0)
        glTexCoord2f(self.width, self.height);    glVertex3f(self.width*cell, -1, self.height*cell)
        glTexCoord2f(0, self.height);             glVertex3f(0, -1, self.height*cell)
        glEnd()

        #Ceiling
        glBindTexture(GL_TEXTURE_2D, self.ceil_tex)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0);                       glVertex3f(0, h-1, 0)
        glTexCoord2f(self.width, 0);              glVertex3f(self.width*cell, h-1, 0)
        glTexCoord2f(self.width, self.height);    glVertex3f(self.width*cell, h-1, self.height*cell)
        glTexCoord2f(0, self.height);             glVertex3f(0, h-1, self.height*cell)
        glEnd()

        #Internal walls
        glBindTexture(GL_TEXTURE_2D, self.wall_tex)
        for (x1, y1), (x2, y2) in self.maze_walls:
            if x1 == x2:
                wx = x1 * cell
                wz = max(y1, y2) * cell
                self.draw_box(wx, wz - thick/2, cell, thick, h)
            else:
                wx = max(x1, x2) * cell
                wz = y1 * cell
                self.draw_box(wx - thick/2, wz, thick, cell, h)

        #Border walls 
        glBindTexture(GL_TEXTURE_2D, self.wall_tex)
        
        for x in range(self.width):
            wx = x * cell
            self.draw_box(wx, -thick, cell, thick, h)
        for x in range(self.width):
            wx = x * cell
            self.draw_box(wx, self.height*cell, cell, thick, h)
        for y in range(self.height):
            wz = y * cell
            self.draw_box(-thick, wz, thick, cell, h)
        for y in range(self.height):
            wz = y * cell
            self.draw_box(self.width*cell, wz, thick, cell, h)
        
        # Draw exit marker
        self.draw_exit_marker()

    def draw_box(self, x, z, w, d, h):
        y = -1.0
        ts = 4.0
        u_w = w / ts
        u_d = d / ts
        v_h = h / ts

        #FRONT
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0);         glVertex3f(x, y, z+d)
        glTexCoord2f(u_w, 0);       glVertex3f(x+w, y, z+d)
        glTexCoord2f(u_w, v_h);     glVertex3f(x+w, y+h, z+d)
        glTexCoord2f(0, v_h);       glVertex3f(x, y+h, z+d)
        glEnd()
        #BACK
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0);         glVertex3f(x, y, z)
        glTexCoord2f(u_w, 0);       glVertex3f(x+w, y, z)
        glTexCoord2f(u_w, v_h);     glVertex3f(x+w, y+h, z)
        glTexCoord2f(0, v_h);       glVertex3f(x, y+h, z)
        glEnd()
        #LEFT
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0);         glVertex3f(x, y, z)
        glTexCoord2f(u_d, 0);       glVertex3f(x, y, z+d)
        glTexCoord2f(u_d, v_h);     glVertex3f(x, y+h, z+d)
        glTexCoord2f(0, v_h);       glVertex3f(x, y+h, z)
        glEnd()
        #RIGHT
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0);         glVertex3f(x+w, y, z)
        glTexCoord2f(u_d, 0);       glVertex3f(x+w, y, z+d)
        glTexCoord2f(u_d, v_h);     glVertex3f(x+w, y+h, z+d)
        glTexCoord2f(0, v_h);       glVertex3f(x+w, y+h, z)
        glEnd()
        #TOP
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0);        glVertex3f(x, y+h, z)
        glTexCoord2f(u_w, 0);      glVertex3f(x+w, y+h, z)
        glTexCoord2f(u_w, u_d);    glVertex3f(x+w, y+h, z+d)
        glTexCoord2f(0, u_d);      glVertex3f(x, y+h, z+d)
        glEnd()

    def draw_exit_marker(self):
        ex, ey = self.exit_cell
        cell = self.CELL_SIZE
        
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_LIGHTING)
        
        glColor3f(0.0, 1.0, 0.0)
        glBegin(GL_QUADS)
        glVertex3f(ex * cell, -0.99, ey * cell)
        glVertex3f((ex + 1) * cell, -0.99, ey * cell)
        glVertex3f((ex + 1) * cell, -0.99, (ey + 1) * cell)
        glVertex3f(ex * cell, -0.99, (ey + 1) * cell)
        glEnd()
        
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_LIGHTING)
        glColor3f(1.0, 1.0, 1.0)

    def find_exit_position(self): #Find a random cell for the exit, surrounded by 3 walls (dead end). If not, do far corner
        
        start_x, start_y = 0, 0
        min_distance = max(self.width, self.height) * 0.4
        dead_ends = []
        
        for y in range(self.height):
            for x in range(self.width):
                wall_count = 0
                if y == 0 or ((x, y-1), (x, y)) in self.maze_walls or ((x, y), (x, y-1)) in self.maze_walls:
                    wall_count += 1
                if y == self.height - 1 or ((x, y), (x, y+1)) in self.maze_walls or ((x, y+1), (x, y)) in self.maze_walls:
                    wall_count += 1
                if x == 0 or ((x-1, y), (x, y)) in self.maze_walls or ((x, y), (x-1, y)) in self.maze_walls:
                    wall_count += 1
                if x == self.width - 1 or ((x, y), (x+1, y)) in self.maze_walls or ((x+1, y), (x, y)) in self.maze_walls:
                    wall_count += 1
                
                if wall_count == 3:
                    distance = math.sqrt((x - start_x)**2 + (y - start_y)**2)
                    if distance >= min_distance:
                        dead_ends.append((x, y))
        if dead_ends:
            return random.choice(dead_ends)
        else:
            return (self.width - 1, self.height - 1)

    def get_cell_from_world(self, world_x, world_z):
        maze_x = int(world_x // self.CELL_SIZE)
        maze_y = int(world_z // self.CELL_SIZE)

        if 0 <= maze_x < self.width and 0 <= maze_y < self.height:
            return (maze_x, maze_y)
        return None

    def is_at_exit(self, world_x, world_z):
        """Check if player is at the exit cell"""
        current_cell = self.get_cell_from_world(world_x, world_z)
        return current_cell == self.exit_cell

    def can_move_to(self, world_x, world_z, radius=0.3):
        ex, ey = self.exit_cell
        at_exit_x = ex * self.CELL_SIZE <= world_x <= (ex + 1) * self.CELL_SIZE
        at_exit_z = ey * self.CELL_SIZE <= world_z <= (ey + 1) * self.CELL_SIZE
        
        if at_exit_x and at_exit_z:
            if ey == self.height - 1 and world_z + radius > self.height * self.CELL_SIZE:
                return True 
            if ex == self.width - 1 and world_x + radius > self.width * self.CELL_SIZE:
                return True

        if (world_x - radius < 0 or world_x + radius > self.width * self.CELL_SIZE or
            world_z - radius < 0 or world_z + radius > self.height * self.CELL_SIZE):
            return False

        for wall in self.maze_walls:
            (x1, y1), (x2, y2) = wall
            
            if x1 == x2:
                wall_x = x1 * self.CELL_SIZE
                wall_z = max(y1, y2) * self.CELL_SIZE
                if self._circle_vs_aabb(world_x, world_z, radius, wall_x, wall_z - self.WALL_THICKNESS/2, self.CELL_SIZE, self.WALL_THICKNESS):
                    return False
            else:
                wall_x = max(x1, x2) * self.CELL_SIZE
                wall_z = y1 * self.CELL_SIZE
                if self._circle_vs_aabb(world_x, world_z, radius, wall_x - self.WALL_THICKNESS/2, wall_z, self.WALL_THICKNESS, self.CELL_SIZE):
                    return False
        return True

    def _circle_vs_aabb(self, cx, cz, radius, box_x, box_z, box_w, box_d):
        closest_x = max(box_x, min(cx, box_x + box_w))
        closest_z = max(box_z, min(cz, box_z + box_d))
        
        dx = cx - closest_x
        dz = cz - closest_z
        distance_sq = dx*dx + dz*dz
        
        return distance_sq < (radius * radius)

    def check_circle_collision(self, cx, cz, target_x, target_z, radius):
        dx = cx - target_x
        dz = cz - target_z
        distance = math.sqrt(dx*dx + dz*dz)
        return distance < radius

    def get_random_walkable_position(self):
        cell_size = self.CELL_SIZE
        max_attempts = 100
        
        for _ in range(max_attempts):
            cell_x = random.randint(0, self.width - 1)
            cell_y = random.randint(0, self.height - 1)
            
            offset_x = random.uniform(0.5, cell_size - 0.5)
            offset_z = random.uniform(0.5, cell_size - 0.5)
            
            world_x = cell_x * cell_size + offset_x
            world_z = cell_y * cell_size + offset_z
            
            if self.can_move_to(world_x, world_z, 0.3):
                return (world_x, world_z)
        
        return (cell_size / 2, cell_size / 2)

    def draw_minimap(self, player_x, player_z, screen_width, screen_height, minimap_size=150):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, screen_width, 0, screen_height, -1, 1)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)

        map_x = screen_width - minimap_size - 10
        map_y = screen_height - minimap_size - 10
        scale_x = minimap_size / self.width
        scale_y = minimap_size / self.height

        glPushMatrix()
        
        center_x = map_x + minimap_size / 2
        center_y = map_y + minimap_size / 2
        glTranslatef(center_x, center_y, 0)
        glRotatef(-90, 0, 0, 1)
        glTranslatef(-center_x, -center_y, 0)

        glColor4f(0.1, 0.1, 0.1, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(map_x, map_y)
        glVertex2f(map_x + minimap_size, map_y)
        glVertex2f(map_x + minimap_size, map_y + minimap_size)
        glVertex2f(map_x, map_y + minimap_size)
        glEnd()
        
        #background
        glColor4f(0.1, 0.1, 0.1, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(map_x, map_y)
        glVertex2f(map_x + minimap_size, map_y)
        glVertex2f(map_x + minimap_size, map_y + minimap_size)
        glVertex2f(map_x, map_y + minimap_size)
        glEnd()
        
        #border
        glColor3f(1.0, 1.0, 1.0)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        glVertex2f(map_x, map_y)
        glVertex2f(map_x + minimap_size, map_y)
        glVertex2f(map_x + minimap_size, map_y + minimap_size)
        glVertex2f(map_x, map_y + minimap_size)
        glEnd()
        
        #Draw maze cells
        glColor3f(0.3, 0.3, 0.3)
        for y in range(self.height):
            for x in range(self.width):
                cell_x = map_x + x * scale_x
                cell_y = map_y + y * scale_y
                glBegin(GL_QUADS)
                glVertex2f(cell_x, cell_y)
                glVertex2f(cell_x + scale_x, cell_y)
                glVertex2f(cell_x + scale_x, cell_y + scale_y)
                glVertex2f(cell_x, cell_y + scale_y)
                glEnd()
        
        # Draw maze walls
        glColor3f(0.7, 0.7, 0.7)
        glLineWidth(2)
        glBegin(GL_LINES)
        
        for (x1, y1), (x2, y2) in self.maze_walls:
            if x1 == x2:  # Horizontal wall
                px = map_x + x1 * scale_x
                py = map_y + max(y1, y2) * scale_y
                glVertex2f(px, py)
                glVertex2f(px + scale_x, py)
            else:  # Vertical wall
                px = map_x + max(x1, x2) * scale_x
                py = map_y + y1 * scale_y
                glVertex2f(px, py)
                glVertex2f(px, py + scale_y)
        
        glEnd()
        
        #Draw exit (green square)
        ex, ey = self.exit_cell
        if not (0 <= ex < self.width and 0 <= ey < self.height):
            print(f"WARNING: Invalid exit position {self.exit_cell}, adjusting...")
            ex = max(0, min(self.width - 1, ex))
            ey = max(0, min(self.height - 1, ey))
        exit_x = map_x + (ex + 0.5) * scale_x
        exit_y = map_y + (ey + 0.5) * scale_y
        exit_size = min(scale_x, scale_y) * 0.4

        glColor3f(0.0, 1.0, 0.0)
        glBegin(GL_QUADS)
        glVertex2f(exit_x - exit_size, exit_y - exit_size)
        glVertex2f(exit_x + exit_size, exit_y - exit_size)
        glVertex2f(exit_x + exit_size, exit_y + exit_size)
        glVertex2f(exit_x - exit_size, exit_y + exit_size)
        glEnd()
        
        #Draw player (orange circle)
        player_cell_x = player_x / self.CELL_SIZE
        player_cell_z = player_z / self.CELL_SIZE
        player_map_x = map_x + player_cell_x * scale_x
        player_map_y = map_y + player_cell_z * scale_y
        player_size = min(scale_x, scale_y) * 0.3
        glColor3f(1.0, 0.5, 0.0)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(player_map_x, player_map_y)
        for i in range(9):
            angle = i * 3.14159 * 2 / 8
            px = player_map_x + player_size * math.cos(angle)
            py = player_map_y + player_size * math.sin(angle)
            glVertex2f(px, py)
        glEnd()
        
        glPopMatrix()
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        
        params = (map_x, map_y, scale_x, scale_y, self.CELL_SIZE)
        return params

    def end_minimap_drawing(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glColor3f(1.0, 1.0, 1.0)