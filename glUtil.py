from OpenGL.GL import *
import numpy as np
from ctypes import c_void_p, sizeof


class screenSpace():
    def __init__(self):
        self.verticies = np.array([1,1, 1,-1, -1,-1, -1,1], dtype=np.float32)
        self.faces = np.array([0,1,3, 2,3,1], dtype = np.uint)

        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        self.vertexBuffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertexBuffer)
        glBufferData(GL_ARRAY_BUFFER, sizeof(GLfloat) * self.verticies.size, self.verticies, GL_DYNAMIC_DRAW)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, False, 2 * sizeof(GLfloat), c_void_p(0))

        self.indexBuffer = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.indexBuffer)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, sizeof(GLuint) * self.faces.size, self.faces, GL_DYNAMIC_DRAW)

        glBindVertexArray(0)

    def draw(self):
        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, c_void_p(0))
        glBindVertexArray(0)

class program():

    REFERENCE = [GL_FRAGMENT_SHADER, GL_VERTEX_SHADER, GL_GEOMETRY_SHADER, GL_TESS_CONTROL_SHADER, GL_TESS_EVALUATION_SHADER]
    
    FRAGMENT = 0
    VERTEX = 1
    GEOMETRY = 2
    TESSCONTROL = 3
    TESSEVAL = 4

    def _compileShader(self, type, source):
        shader = glCreateShader(type)
        glShaderSource(shader, source)
        glCompileShader(shader)

        compiled = glGetShaderiv(shader, GL_COMPILE_STATUS)
        
        if not compiled:
            info = glGetShaderInfoLog(shader).decode()
            glDeleteShader(shader)

            raise Exception("Shader compile error: " + info)

        return shader

    def __init__(self, filename):
        shaderSources = ['' for i in range(5)]

        mode = -1

        with open(filename,"r") as f:
            while line := f.readline():
                if line.find("#shader") != -1:
                    if line.find("fragment") != -1: mode = self.FRAGMENT
                    elif line.find("vert") != -1: mode = self.VERTEX
                    elif line.find("geo") != -1: mode = self.GEOMETRY
                    elif line.find("tesseval") != -1: mode = self.TESSEVAL
                    elif line.find("tesscontrol") != -1: mode = self.TESSCONTROL
                    continue

                if mode == -1:
                    continue

                shaderSources[mode] += line

        self.program = glCreateProgram()
        self.uniforms = {}

        shaders = [0, 0, 0, 0, 0]

        for type,shader in enumerate(shaderSources):
            if not shader:
                continue

            shaders[type] = self._compileShader(self.REFERENCE[type],shaderSources[type])

        for shader in shaders:
            if not shader:
                continue

            glAttachShader(self.program,shader)

        glLinkProgram(self.program)
        glValidateProgram(self.program)

        for i in range(glGetProgramiv(self.program, GL_ACTIVE_UNIFORMS)):
            uniform = glGetActiveUniform(self.program, i);
            self.uniforms[uniform[0].decode()] = glGetUniformLocation(self.program, uniform[0].decode())

    def use(self):
        glUseProgram(self.program)

    def setMatrix4(self, name, value):
        glProgramUniformMatrix4fv(self.program, self.uniforms[name], 1, value)

    def setVector3(self, name, value):
        glProgramUniform3fv(self.program, self.uniforms[name], 1, value)

    def setVector2(self, name, value):
        glProgramUniform2fv(self.program, self.uniforms[name], 1, value)

    def setFloat(self, name, value):
        glProgramUniform1f(self.program, self.uniforms[name], value)

    def setInt(self, name, value):
        glProgramUniform1i(self.program, self.uniforms[name], value)

    def loc(self,name):
        return self.uniforms[name]
    
    def setFloatPtr(self, loc, value):
        glProgramUniform1f(self.program, loc, value)

    def setVector3Ptr(self, loc, value):
        glProgramUniform3fv(self.program, loc, 1, value)