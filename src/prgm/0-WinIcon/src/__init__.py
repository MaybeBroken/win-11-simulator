from direct.gui.DirectGui import *

if "a" == "b":
    from main import API

window = API.Window(
    name="Window",
    position=(-0.3, -0.25),
    size=(350, 400),
    frameColor=(0, 0, 0, 1),
    winType=API.winTypes.SYSTEM,
)
