# app.py
import taichi as ti

ti.init(arch=ti.gpu)

window = ti.ui.Window("Hackathon Simulator", (1280, 720))

while window.running:
    window.show()