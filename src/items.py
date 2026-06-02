import math
import time
import random
from OpenGL.GL import *
import pygame

class SplashParticle:
    def __init__(self, x, z):
        self.x = x
        self.y = -0.9
        self.z = z
        self.vx = (random.random() - 0.5) * 0.3
        self.vy = random.random() * 0.5
        self.vz = (random.random() - 0.5) * 0.3
        self.life = 1.0
        self.size = random.random() * 0.2 + 0.1
        
    def update(self, dt):
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.z += self.vz * dt * 60
        self.vy -= 0.5 * dt * 60
        self.life -= dt * 2
        return self.life > 0
        
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glColor4f(0.8, 0.9, 1.0, self.life * 0.7)
        
        size = self.size * (2.0 - self.life)
        glBegin(GL_QUADS)
        glVertex3f(-size, -size, 0)
        glVertex3f(size, -size, 0)
        glVertex3f(size, size, 0)
        glVertex3f(-size, size, 0)
        glEnd()
        glPopMatrix()


WATER_VERTEX_SHADER = """
varying vec2 texCoord;

void main() {
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    texCoord = gl_Vertex.xz * 0.5;
}
"""

WATER_FRAGMENT_SHADER = """
uniform float time;
varying vec2 texCoord;

void main()
{
    vec2 uv = texCoord * 2.0;
    
    float ripple1 = sin(uv.x * 1.2 + time * 1.5) * sin(uv.y * 1.2 + time * 1.3) * 0.3;
    float ripple2 = sin(uv.x * 2.5 + time * 2.2) * 0.25 + sin(uv.y * 2.8 + time * 1.9) * 0.25;
    float ripple3 = sin(uv.x * 5.0 + uv.y * 3.0 + time * 3.5) * 0.15;
    
    float dist = length(uv);
    float circularRipple = sin(dist * 15.0 - time * 3.0) * exp(-dist * 2.0) * 0.4;
    
    float totalRipple = ripple1 + ripple2 + ripple3 + circularRipple;
    
    vec3 waterColor = vec3(0.4, 0.6, 0.95);
    waterColor.g += totalRipple * 0.1;
    
    float foam = smoothstep(0.2, 0.4, totalRipple) * 0.3;
    waterColor += vec3(0.2, 0.25, 0.3) * foam;
    
    float depthFactor = 1.0 - smoothstep(0.0, 1.5, dist);
    waterColor *= 0.7 + depthFactor * 0.6;
    
    float alpha = 0.65 + totalRipple * 0.2;
    alpha *= 1.0 - smoothstep(1.0, 1.8, dist);
    
    gl_FragColor = vec4(waterColor, alpha);
}
"""

def compile_shader(vsrc, fsrc):
    vid = glCreateShader(GL_VERTEX_SHADER)
    glShaderSource(vid, vsrc)
    glCompileShader(vid)
    if glGetShaderiv(vid, GL_COMPILE_STATUS) != GL_TRUE:
        print("Vertex shader error:", glGetShaderInfoLog(vid).decode())

    fid = glCreateShader(GL_FRAGMENT_SHADER)
    glShaderSource(fid, fsrc)
    glCompileShader(fid)
    if glGetShaderiv(fid, GL_COMPILE_STATUS) != GL_TRUE:
        print("Fragment shader error:", glGetShaderInfoLog(fid).decode())

    pid = glCreateProgram()
    glAttachShader(pid, vid)
    glAttachShader(pid, fid)
    glLinkProgram(pid)
    if glGetProgramiv(pid, GL_LINK_STATUS) != GL_TRUE:
        print("Program link error:", glGetProgramInfoLog(pid).decode())

    return pid


WATER_SHADER = None
CELL_SIZE = 4.0

class Item:
    def __init__(self, x, z, item_type, obj_model=None):
        cx = int(x // CELL_SIZE)
        cz = int(z // CELL_SIZE)
        self.x = cx * CELL_SIZE + CELL_SIZE/2
        self.z = cz * CELL_SIZE + CELL_SIZE/2
        self.y = -0.5
        self.type = item_type
        self.obj_model = obj_model
        self.collected = False

        self.hover_timer = 0.0
        self.hover_speed = 0.05
        self.hover_amount = 0.2
        self.rotation = 0.0
        self.rotation_speed = 2.0
        self.radius = 1.0 if item_type != "trap" else 1.3
        self.water_timer = time.time()
        
        global WATER_SHADER
        if WATER_SHADER is None:
            WATER_SHADER = compile_shader(WATER_VERTEX_SHADER, WATER_FRAGMENT_SHADER)


    def update(self, dt):
        if self.collected or self.type == "trap":
            return

        scale = dt * 60
        self.hover_timer += self.hover_speed * scale
        self.rotation = (self.rotation + self.rotation_speed * scale) % 360


    def draw(self):
        if self.collected:
            return

        glPushMatrix()

        if self.type == "trap":
            self.draw_puddle()
            glPopMatrix()
            return

        hover = math.sin(self.hover_timer) * self.hover_amount
        glTranslatef(self.x, self.y + hover, self.z)
        glRotatef(self.rotation, 0, 1, 0)
        glColor3f(1.0, 0.9, 0.7)
        self.obj_model.draw()
        glColor3f(1, 1, 1)
        glPopMatrix()


    def draw_puddle(self):
        global WATER_SHADER

        glPushMatrix()
        glTranslatef(self.x, -0.95, self.z)
        
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(GL_FALSE)
        
        glUseProgram(WATER_SHADER)
        current_time = time.time() - self.water_timer
        time_loc = glGetUniformLocation(WATER_SHADER, b"time")
        if time_loc != -1:
            glUniform1f(time_loc, current_time)
        
        self._draw_disc(1.6, 64)
        
        glPushMatrix()
        glTranslatef(0.8, 0.01, -0.6)
        self._draw_disc(1.0, 48)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(-0.5, 0.02, 0.7)
        self._draw_disc(0.7, 32)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(1.2, 0.015, 0.3)
        self._draw_disc(0.4, 24)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(-0.9, 0.01, -0.8)
        self._draw_disc(0.5, 24)
        glPopMatrix()
        
        glUseProgram(0)
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
        glPopMatrix()

    def _draw_disc(self, radius, segments):
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0, 0, 0)
        for i in range(segments + 1):
            angle = 2.0 * math.pi * i / segments
            x = math.cos(angle) * radius
            z = math.sin(angle) * radius
            glVertex3f(x, 0, z)
        glEnd()

    def check_collision(self, px, pz):
        if self.collected:
            return False

        if math.hypot(px - self.x, pz - self.z) < self.radius:
            if self.type != "trap":
                self.collected = True
            return True
        return False


class ItemManager:
    def __init__(self, maze, obj_model, speed_count=3, trap_count=3):
        self.obj_model = obj_model
        self.speed_items = []
        self.trap_items = []

        self.boost_active = False
        self.boost_end_time = 0
        self.original_speed = None

        self.slip_active = False
        self.slip_end_time = 0
        self.slip_direction = [0, 0]
        self.splash_particles = []

        self.spawn_items(maze, speed_count, trap_count)

    def spawn_items(self, maze, speed_count, trap_count):
        self.speed_items.clear()
        self.trap_items.clear()
        occupied = set()

        def get_unique_position():
            for _ in range(200):
                x, z = maze.get_random_walkable_position()
                cell_x = int(x // CELL_SIZE)
                cell_z = int(z // CELL_SIZE)
                if (cell_x, cell_z) not in occupied:
                    occupied.add((cell_x, cell_z))
                    return x, z
            return maze.get_random_walkable_position()

        for _ in range(speed_count):
            x, z = get_unique_position()
            self.speed_items.append(Item(x, z, "speed", obj_model=self.obj_model))

        for _ in range(trap_count):
            x, z = get_unique_position()
            self.trap_items.append(Item(x, z, "trap"))

    def update(self, camera, dt, maze=None):
        px, _, pz = camera.get_position()

        self.splash_particles = [p for p in self.splash_particles if p.update(dt)]

        for item in self.speed_items:
            item.update(dt)
            if item.check_collision(px, pz):
                self.activate_boost(camera)

        for i, trap in enumerate(self.trap_items):
            trap.update(dt)
            if trap.check_collision(px, pz) and not self.slip_active:
                self.trigger_slip(camera, trap.x, trap.z, i)

        if self.slip_active:
            self.apply_slip_effect(camera, dt, maze)
            if time.time() >= self.slip_end_time:
                self.slip_active = False

        if self.boost_active and time.time() >= self.boost_end_time:
            self.deactivate_boost(camera)


    def trigger_slip(self, camera, trap_x, trap_z, trap_index):
        self.slip_active = True
        self.slip_end_time = time.time() + 1.5
        
        px, py, pz = camera.get_position()
        dx = px - trap_x
        dz = pz - trap_z
        
        if abs(dx) < 0.1 and abs(dz) < 0.1:
            angle = random.random() * 2 * math.pi
            self.slip_direction = [math.cos(angle), math.sin(angle)]
        else:
            mag = math.hypot(dx, dz)
            if mag > 0:
                self.slip_direction = [dx / mag, dz / mag]
            else:
                angle = random.random() * 2 * math.pi
                self.slip_direction = [math.cos(angle), math.sin(angle)]
        
        for _ in range(15):
            self.splash_particles.append(SplashParticle(trap_x, trap_z))

    def apply_slip_effect(self, camera, dt, maze=None):
        slip_speed = 0.25
        t = time.time() * 3.0
        randomness = 0.15 * (1.0 - (self.slip_end_time - time.time()) / 1.5)

        slip_x = self.slip_direction[0] + math.sin(t) * randomness
        slip_z = self.slip_direction[1] + math.cos(t * 1.3) * randomness
        
        mag = math.hypot(slip_x, slip_z)
        if mag > 0:
            slip_x = slip_x / mag * slip_speed
            slip_z = slip_z / mag * slip_speed

        new_x = camera.position[0] + slip_x * dt * 60
        new_z = camera.position[2] + slip_z * dt * 60
        
        # border collision (can noclip internal walls)
        if maze is not None and not camera.noclip:
            cell_size = maze.CELL_SIZE
            width = maze.width
            height = maze.height

            min_x, max_x = 0, width * cell_size
            min_z, max_z = 0, height * cell_size

            ex, ey = maze.exit_cell
            at_exit_x = ex * cell_size <= new_x <= (ex + 1) * cell_size
            at_exit_z = ey * cell_size <= new_z <= (ey + 1) * cell_size

            if ey == height - 1 and at_exit_x and at_exit_z and new_z + 0.3 > max_z:
                pass  
            elif ex == width - 1 and at_exit_x and at_exit_z and new_x + 0.3 > max_x:
                pass
            elif new_x - 0.3 < min_x or new_x + 0.3 > max_x or new_z - 0.3 < min_z or new_z + 0.3 > max_z:
                return
            
        camera.position[0] = new_x
        camera.position[2] = new_z


    def activate_boost(self, camera):
        if not self.boost_active:
            self.original_speed = camera.move_speed
            camera.move_speed *= 2.0
        self.boost_active = True
        self.boost_end_time = time.time() + 20.0

    def deactivate_boost(self, camera):
        if self.original_speed is not None:
            camera.move_speed = self.original_speed
            self.original_speed = None
        self.boost_active = False

    def draw(self):
        if self.splash_particles:
            glDisable(GL_LIGHTING)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glDisable(GL_TEXTURE_2D)
            glDepthMask(GL_FALSE)
            
            for particle in self.splash_particles:
                particle.draw()
            
            glDepthMask(GL_TRUE)
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_LIGHTING)
            glDisable(GL_BLEND)
        
        for item in self.speed_items:
            item.draw()
        for trap in self.trap_items:
            trap.draw()

    def draw_slip_overlay(self):
        if not self.slip_active:
            return
            
        time_left = self.slip_end_time - time.time()
        intensity = min(1.0, time_left * 2.0)
        
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        w, h = pygame.display.get_surface().get_size()
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, w, 0, h, -1, 1)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        overlay_intensity = intensity * 0.4 * (1.0 + math.sin(time.time() * 10.0) * 0.3)
        glColor4f(0.3, 0.5, 0.8, overlay_intensity)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(w, 0)
        glVertex2f(w, h)
        glVertex2f(0, h)
        glEnd()
        
        droplet_time = time.time() * 8.0
        if intensity > 0.3:
            for i in range(5):
                x = w * (0.1 + 0.8 * ((i * 123) % 100) / 100)
                y = h * (0.1 + 0.8 * ((i * 456) % 100) / 100)
                size = 15 + math.sin(droplet_time + i * 2) * 8
                alpha = 0.2 + math.sin(droplet_time * 2 + i) * 0.15
                
                glColor4f(0.8, 0.9, 1.0, alpha * intensity)
                glBegin(GL_TRIANGLE_FAN)
                for angle in range(0, 361, 30):
                    rad = math.radians(angle)
                    glVertex2f(x + math.cos(rad)*size, y + math.sin(rad)*size)
                glEnd()
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glDisable(GL_BLEND)

    def draw_on_minimap(self, map_x, map_y, sx, sy, cell_size):
        glColor3f(1, 1, 0)
        for item in self.speed_items:
            if item.collected: 
                continue
            px = map_x + (item.x / cell_size) * sx
            py = map_y + (item.z / cell_size) * sy
            glBegin(GL_QUADS)
            glVertex2f(px-4, py-4)
            glVertex2f(px+4, py-4)
            glVertex2f(px+4, py+4)
            glVertex2f(px-4, py+4)
            glEnd()

        for trap in self.trap_items:
            px = map_x + (trap.x / cell_size) * sx
            py = map_y + (trap.z / cell_size) * sy
            
            if self.slip_active:
                flash = (math.sin(time.time() * 10.0) * 0.5 + 0.5)
                glColor3f(0.3 * flash, 0.6 * flash, 1.0)
            else:
                glColor3f(0.3, 0.6, 1.0)
                
            glBegin(GL_QUADS)
            glVertex2f(px-4, py-4)
            glVertex2f(px+4, py-4)
            glVertex2f(px+4, py+4)
            glVertex2f(px-4, py+4)
            glEnd()

        glColor3f(1, 1, 1)

    def get_boost_remaining(self):
        if not self.boost_active:
            return 0.0
        return max(0.0, self.boost_end_time - time.time())

    def get_slip_remaining(self):
        if not self.slip_active:
            return 0.0
        return max(0.0, self.slip_end_time - time.time())

    def reset(self, maze, camera):
        if self.boost_active:
            self.deactivate_boost(camera)
        
        self.slip_active = False
        self.splash_particles.clear()
        self.boost_active = False
        self.boost_end_time = 0
        self.original_speed = None
        
        self.spawn_items(maze, 3, 3)