import os
import pygame
from OpenGL.GL import *

#chatgpt helped rewrite obj loader by replacing the immediate mode, per-frame OBJ drawing to compiled OpenGL display list
#The entire mesh is now uploaded once, and rendered in a single glCallList(). Improved fps from 11 to 60.

class OBJ:
    def __init__(self, filename):
        self.vertices = []
        self.texcoords = []
        self.normals = []
        self.faces = [] 

        self.texture_id = None
        self.display_list = None

        self.base_dir = os.path.dirname(filename)
        self.load_obj(filename)
        self.build_display_list()

    def load_obj(self, filename):
        with open(filename, "r") as f:
            for line in f:
                if not line or line.startswith("#"):
                    continue

                parts = line.strip().split()
                if not parts:
                    continue

                prefix = parts[0]

                if prefix == "v":
                    self.vertices.append(tuple(map(float, parts[1:4])))

                elif prefix == "vt":
                    self.texcoords.append(tuple(map(float, parts[1:3])))

                elif prefix == "vn": 
                    self.normals.append(tuple(map(float, parts[1:4])))

                elif prefix == "f": 
                    face = []
                    for entry in parts[1:]:
                        v = vt = vn = None
                        vals = entry.split("/")

                        v  = int(vals[0]) - 1
                        if len(vals) > 1 and vals[1]:
                            vt = int(vals[1]) - 1
                        if len(vals) > 2 and vals[2]:
                            vn = int(vals[2]) - 1

                        face.append((v, vt, vn))

                    if len(face) == 3:
                        self.faces.append(face)
                    elif len(face) == 4:
                        self.faces.append([face[0], face[1], face[2]])
                        self.faces.append([face[0], face[2], face[3]])

                elif prefix == "mtllib":
                    mtl_path = os.path.join(self.base_dir, parts[1])
                    self.texture_id = self.load_mtl(mtl_path)


    def load_mtl(self, mtl_file):
        texture_path = None
        try:
            with open(mtl_file, "r") as f:
                for line in f:
                    if line.startswith("map_Kd"):
                        _, texname = line.split()
                        texture_path = os.path.join(self.base_dir, texname)
                        break
        except FileNotFoundError:
            print("MTL file missing:", mtl_file)
            return None

        if texture_path and os.path.exists(texture_path):
            return self.load_texture(texture_path)

        print("No texture referenced in MTL")
        return None

    def load_texture(self, path):
        surf = pygame.image.load(path)
        img = pygame.image.tostring(surf, "RGBA", True)
        w, h = surf.get_size()

        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, img)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glGenerateMipmap(GL_TEXTURE_2D)

        return tex

    def build_display_list(self):

        self.display_list = glGenLists(1)
        glNewList(self.display_list, GL_COMPILE)
        if self.texture_id:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
        else:
            glDisable(GL_TEXTURE_2D)
        glBegin(GL_TRIANGLES)

        for face in self.faces:
            for (v, vt, vn) in face:

                if vn is not None:
                    glNormal3fv(self.normals[vn])

                if vt is not None:
                    glTexCoord2fv(self.texcoords[vt])

                glVertex3fv(self.vertices[v])
        glEnd()
        glEndList()


    def draw(self):
        glCallList(self.display_list)
