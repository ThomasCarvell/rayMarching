from OpenGL.GL import *
import numpy as np
import pygame
import time

from glUtil import *

pygame.init()

font = pygame.font.SysFont("Ariel", 100)

class app():

    WIDTH = 2560
    HEIGHT = 1440

    FPS = 60

    def __init__(self):

        self.root = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF | pygame.NOFRAME)
        glViewport(0, 0, self.WIDTH, self.HEIGHT)
        glEnable(GL_DEPTH_TEST)

        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

        self.clock = pygame.time.Clock()

    def mainloop(self):

        dtime = 0.001

        scrnSpace = screenSpace()
        font = pygame.font.Font (None, 64)

        shaders = program("shaders.glsl")
        shaders.use()

        fov = np.array([np.pi/2, (np.pi/2) * (self.HEIGHT/self.WIDTH)], dtype = np.float32)
        playerPos = np.array([0, 4, 0], dtype = np.float32)
        playerRot = np.array([0, 0], dtype = np.float32)

        shaders.setVector2("fov", fov)
        shaders.setVector3("camPos", playerPos)
        shaders.setVector2("camRot", playerRot)

        shaders.setInt("numLights", 3)

        shaders.use()
        shaders.setVector3("lights[0].pos", np.array([2, 4, 0], dtype = np.float32))
        shaders.setVector3("lights[0].color", np.array([1, 0, 0], dtype = np.float32))
        shaders.setFloat("lights[0].intensity", 5)

        shaders.setVector3("lights[1].pos", np.array([-1, 4, -np.sqrt(2)], dtype = np.float32))
        shaders.setVector3("lights[1].color", np.array([0, 1, 0], dtype = np.float32))
        shaders.setFloat("lights[1].intensity", 5)

        shaders.setVector3("lights[2].pos", np.array([-1, 4, np.sqrt(2)], dtype = np.float32))
        shaders.setVector3("lights[2].color", np.array([0, 0, 1], dtype = np.float32))
        shaders.setFloat("lights[2].intensity", 5)

        shaders.setVector3("lights[3].pos", np.array([0, 50, 0], dtype = np.float32))
        shaders.setVector3("lights[3].color", np.array([1, 1, 1], dtype = np.float32))
        shaders.setFloat("lights[3].intensity", 10)

        refTime = time.time()

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            mVel = pygame.mouse.get_rel()
            playerRot[0] += mVel[0] * 0.25 * dtime
            playerRot[1] -= mVel[1] * 0.25 * dtime
            playerRot[1] = min(max(playerRot[1],-np.pi/2),np.pi/2)
            shaders.setVector2("camRot", playerRot)

            
            keys = pygame.key.get_pressed()
            movement = np.array([keys[pygame.K_d] - keys[pygame.K_a],
                                 keys[pygame.K_SPACE] - keys[pygame.K_LSHIFT],
                                 keys[pygame.K_w] - keys[pygame.K_s]], dtype = np.float32) * 5 * dtime
            
            playerPos[0] += np.cos(playerRot[0]) * movement[0] + np.sin(playerRot[0]) * movement[2]
            playerPos[1] += movement[1]
            playerPos[2] += np.cos(playerRot[0]) * movement[2] - np.sin(playerRot[0]) * movement[0]
            shaders.setVector3("camPos", playerPos)


            glClearColor(0, 0, 0, 1)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            shaders.use()
            scrnSpace.draw()

            pygame.display.flip()
            self.clock.tick(self.FPS)
            dtime = time.time()-refTime
            refTime = time.time()

            print(1/dtime)

    def __del__(self):
        pygame.quit()


if __name__ == "__main__":
    try:
        application = app()
        application.mainloop()
    except Exception as e:
        raise e