import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL.EXT.texture_filter_anisotropic import *

import os
import time

from maze import Maze
from camera import Camera
from obj_importer import OBJ
from items import ItemManager

pygame.font.init()

def draw_text(text, x, y, size=20, color=(200,200,200)):
    pygame.font.init()
    font = pygame.font.SysFont("Consolas", size)
    surf = font.render(text, True, color, (0,0,0))
    data = pygame.image.tostring(surf, "RGBA", True)
    glWindowPos2d(x, y)
    glDrawPixels(surf.get_width(), surf.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, data)
    

def loadTexture(filename):
    textureSurface = pygame.image.load(os.path.join(os.path.dirname(__file__), "Assets", filename))
    data = pygame.image.tostring(textureSurface, "RGBA", 1)
    w, h = textureSurface.get_width(), textureSurface.get_height()
    texid = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texid)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
    glGenerateMipmap(GL_TEXTURE_2D)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    aniso = glGetFloatv(GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAX_ANISOTROPY_EXT, aniso)

    return texid

def format_time(seconds):
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    ms   = int((seconds % 1) * 100)
    return f"{mins:02d}:{secs:02d}.{ms:02d}"

def draw_victory_screen(elapsed, best_time):
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glDisable(GL_TEXTURE_2D)

    w, h = pygame.display.get_surface().get_size()

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, w, 0, h, -1, 1)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor4f(0,0,0,0.85)
    glBegin(GL_QUADS)
    glVertex2f(0,0)
    glVertex2f(w,0)
    glVertex2f(w,h)
    glVertex2f(0,h)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_TEXTURE_2D)
    
    draw_text(" MAZE COMPLETE!", x=400, y=350, size=48, color=(0,255,0))
    draw_text(f"Time: {format_time(elapsed)}", x=500, y=300, size=32)

    if best_time is not None:
        draw_text(f"Best: {format_time(best_time)}", x=400, y=260, size=26)

    draw_text("Press T for new maze", x=400, y=180, size=22)
    draw_text("Press ESC to quit", x=400, y=150, size=22)


class HintSystem:
    def __init__(self):
        self.hints_remaining = 3
        self.hint_active = False
        self.hint_end_time = 0
        self.hint_duration = 10
    
    def use_hint(self):
        if self.hints_remaining > 0:
            self.hints_remaining -= 1
            self.hint_active = True
            self.hint_end_time = time.time() + self.hint_duration
            return True
        return False
    
    def update(self):
        if self.hint_active and time.time() >= self.hint_end_time:
            self.hint_active = False
    
    def reset(self):
        self.hints_remaining = 3
        self.hint_active = False
        self.hint_end_time = 0
    
    def get_hint_text(self):
        if self.hints_remaining == 0:
            return "HINTS: 0 (Press H)", (255, 50, 50)  #Red
        else:
            return f"HINTS: {self.hints_remaining} (Press H)", (200, 200, 200)
    
    def get_hint_time_remaining(self):
        if self.hint_active:
            return max(0.0, self.hint_end_time - time.time())
        return 0.0


def main():
    pygame.init()
    display = (1000, 600)
    screen = pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("3D Maze")

    wall_tex  = loadTexture("wall_tex.png")
    floor_tex = loadTexture("floor_tex.png")
    ceil_tex  = loadTexture("ceiling_tex.png")
    bottle    = OBJ(os.path.join(os.path.dirname(__file__), "Assets", "almond_bottle.obj"))

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glShadeModel(GL_SMOOTH)
    glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.5]*4)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1]*4)

    glMatrixMode(GL_PROJECTION)
    gluPerspective(70, display[0]/display[1], 0.1, 100.0)

    displayCenter = [display[0]//2, display[1]//2]
    pygame.mouse.set_pos(displayCenter)
    mouseMove = [0, 0]

    camera = Camera()
    maze = Maze(15, 15, wall_tex, floor_tex, ceil_tex)
    items = ItemManager(maze, bottle, speed_count=10, trap_count=5)
    hints = HintSystem()

    clock = pygame.time.Clock()
    start_time = time.time()
    maze_completed = False
    best_time = None
    elapsed_time = 0.0


    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return

                if event.key == pygame.K_t:        #regenerate maze
                    maze = Maze(15, 15, wall_tex, floor_tex, ceil_tex)
                    items.reset(maze, camera)
                    camera.reset()
                    hints.reset()
                    start_time = time.time()
                    maze_completed = False
                    elapsed_time = 0.0

                if event.key == pygame.K_r:        #reset position
                    camera.reset()
                    start_time = time.time()
                    maze_completed = False

                if event.key == pygame.K_h:        #use hint
                    if hints.use_hint():
                        print(f"Hint used! {hints.hints_remaining} hints remaining.")
                    else:
                        print("No hints remaining!")

                if event.key == pygame.K_n:  # Toggle noclip
                    camera.noclip = not camera.noclip

            if event.type == pygame.MOUSEMOTION:
                mouseMove = [event.pos[0]-displayCenter[0], event.pos[1]-displayCenter[1]]

        pygame.mouse.set_pos(displayCenter)
        keypress = pygame.key.get_pressed()
        delta = clock.get_time() * 0.001

        if not maze_completed:
            camera.update(keypress, mouseMove, maze)
            items.update(camera, delta, maze)
            hints.update()
            elapsed_time = time.time() - start_time

        # Check victory
        cam_x, cam_y, cam_z = camera.get_position()
        if not maze_completed and maze.is_at_exit(cam_x, cam_z):
            maze_completed = True
            if best_time is None or elapsed_time < best_time:
                best_time = elapsed_time
            print("Completed in:", format_time(elapsed_time))

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLightfv(GL_LIGHT0, GL_POSITION, [1,1,1,0])

        maze.draw()
        items.draw()

        if hints.hint_active:
            params = maze.draw_minimap(cam_x, cam_z, display[0], display[1], minimap_size=150)
            if params:
                items.draw_on_minimap(*params)
            maze.end_minimap_drawing()
            
        items.draw_slip_overlay()

        if maze_completed:
            draw_victory_screen(elapsed_time, best_time)
            keys = pygame.key.get_pressed()
            if keys[K_t]:
                maze = Maze(15, 15, wall_tex, floor_tex, ceil_tex)
                items.reset(maze, camera)
                camera.reset()
                hints.reset()
                start_time = time.time()
                maze_completed = False
                continue

            pygame.display.flip()
            clock.tick(60)
            continue

        draw_text(f"FPS: {clock.get_fps():.1f}", x=10, y=500, size=20)
        draw_text(f"Pos: ({cam_x:.1f}, {cam_y:.1f}, {cam_z:.1f})", 10, 520, 20)
        draw_text(f"Time: {format_time(elapsed_time)}", 10, 540, 20)

        boost = items.get_boost_remaining()
        if boost > 0:
            draw_text(f"BOOST: {boost:.1f}s", 10, 480, 20)

        slip_time = items.get_slip_remaining()
        if slip_time > 0:
            draw_text(f"SLIP: {slip_time:.1f}s", 10, 460, 20, color=(100, 150, 255))

        hint_text, hint_color = hints.get_hint_text()
        draw_text(hint_text, 10, 440, 20, color=hint_color)
        hint_timer = hints.get_hint_time_remaining()
        if hint_timer > 0:
            draw_text(f"Hint: {hint_timer:.1f}s", 10, 420, 20, color=(100, 255, 100))

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()