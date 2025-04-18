from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import *
from panda3d.core import (
    NodePath,
    Vec3,
    NodePath,
    MovieTexture,
    CardMaker,
    loadPrcFileData,
    TransparencyAttrib,
    TextNode,
)
from json import loads, dump
import os
import atexit
import time

os.chdir(os.path.dirname(os.path.abspath(__file__)))
GLOBALMEM: dict = {}
DEFAULTS: dict = {
    "AUTH": {"users": {"admin": "admin"}},
    "PANDAPRC": {
        "PRCFILE": """win-size 1280 720
window-title Windows 11
text-font /Windows 11/scripts/src/SegoeUIVF-Regular-Small.ttf
undecorated true
clock-mode limited
clock-frame-rate 0
show-frame-rate-meter 0
frame-rate-meter-update-interval 0.25
sync-video 0
""",
        "STARTUP_INJECTOR": "print('No startup injector found.')",
    },
}

VRAM = {}


class UIManager:
    def __init__(self):
        self.pageStack: dict[str, UIManager.Window] = {}
        self.lastPage = None
        self.activePage = None

    def goToPage(self, pageName):
        if pageName in self.pageStack:
            if self.activePage is not None:
                self.activePage.hide()
            self.pageStack[pageName].show()
            self.lastPage = self.activePage
            self.activePage = self.pageStack[pageName]
        else:
            print(f"Page '{pageName}' Not Found")

    def fadeToPage(self, pageName, time):
        if pageName in self.pageStack:
            for root in [self.activePage.root, self.activePage.root2]:
                root.setTransparency(TransparencyAttrib.MAlpha)
            for root in [self.pageStack[pageName].root, self.pageStack[pageName].root2]:
                root.setTransparency(TransparencyAttrib.MAlpha)
            self.pageStack[pageName].fadeIn(time)

            def final(t):
                self.lastPage = self.activePage
                self.activePage = self.pageStack[pageName]
                self.lastPage.hide()

            base.doMethodLater(
                time, self.activePage.fadeOut, "fadeToPage", extraArgs=[time]
            )

            base.doMethodLater(time, final, "fadeToPage_final")
        else:
            print(f"Page '{pageName}' Not Found")

    def goBack(self):
        if self.lastPage is not None:
            self.activePage.hide()
            self.lastPage.show()
            self.activePage = self.lastPage
            self.lastPage = None
        else:
            print("No Last Page Found")

    def addPage(self, pageName, page):
        if pageName not in self.pageStack:
            self.pageStack[pageName] = page
            if self.activePage is None:
                self.activePage = page
            else:
                page.hide()
        else:
            print("Page Already Exists")

    class VideoPlayer:
        def __init__(self, name, videoPath, parent: "UIManager.Window" = None):
            self.name = name
            self.videoPath = videoPath
            self.tex = MovieTexture(self.name)
            if self.tex.read(videoPath):
                self.tex.setLoop(False)
                cm = CardMaker("fullscreenCard")
                cm.setFrameFullscreenQuad()
                cm.setUvRange(self.tex)
                card = NodePath(cm.generate())
                card.reparentTo(parent if parent is not None else render2d)
                card.setTexture(self.tex)
                self.card = card
                self.play()
            else:
                with open(videoPath, "rb") as fp:
                    print("File Found, " + str(len(fp.read())) + " bytes")
                print("Failed to load Video")

        def stop(self):
            try:
                self.tex.stop()
            except:
                pass

        def play(self):
            try:
                self.tex.play()
            except:
                pass

        def setSpeed(self, speed):
            try:
                self.tex.setPlayRate(speed)
            except:
                pass

        def getSpeed(self):
            try:
                return self.tex.getPlayRate()
            except:
                return 0

        def setLoop(self, loop):
            try:
                self.tex.setLoop(loop)
            except:
                pass

    class Window:
        def __init__(self, name, UIMgr: "UIManager", parent: "UIManager.Window" = None):
            self.name = name
            self.visible = False
            self.parent = None if parent is None else parent
            self.children = []
            self.children_dict = {}
            self.childrenNode = NodePath(name + "_children")
            self.childrenNode.reparentTo(
                aspect2d
                if parent is None
                else (
                    parent.childrenNode
                    if isinstance(parent, UIManager.Window)
                    else parent
                )
            )

            self.root = NodePath(name)
            self.root.reparentTo(
                aspect2d
                if parent is None
                else (
                    parent.childrenNode
                    if isinstance(parent, UIManager.Window)
                    else parent
                )
            )
            self.root2 = NodePath(name + "_2")
            self.root2.reparentTo(
                render2d
                if parent is None
                else (
                    parent.childrenNode
                    if isinstance(parent, UIManager.Window)
                    else parent
                )
            )
            if parent is not None:
                parent.children.append(self)
                parent.children_dict[name] = self
            self.hide()
            UIMgr.addPage(pageName=self.name, page=self)

        def show(self):
            self.visible = True
            self.root.show()
            self.root2.show()

        def hide(self):
            self.visible = False
            self.root.hide()
            self.root2.hide()

        def showParent(self):
            if not self.parent is None:
                self.parent.show()

        def hideParent(self):
            if not self.parent is None:
                self.parent.hide()

        def destroy(self):
            for child in self.children:
                child.removeNode()
            for index, child in enumerate(self.children_dict):
                child.removeNode
            self.children.clear()
            self.children_dict.clear()
            self.root.removeNode()
            self.root2.removeNode()
            self.childrenNode.removeNode()
            if self.parent is not None:
                self.parent.children.remove(self)
            self.visible = False
            self.parent = None
            del self

        def appendWindow(self, parentWindow: "UIManager.Window"):
            parentWindow.children.append(self)
            parentWindow.children_dict[self.name] = self

        def fadeIn(self, time):
            for win in [self.root, self.root2]:
                win.setTransparency(TransparencyAttrib.MAlpha)
                win.setAlphaScale(0)
                win.show()
                win.colorScaleInterval(
                    time, (1, 1, 1, 1), startColorScale=(0, 0, 0, 0)
                ).start()

        def fadeOut(self, time):
            for win in [self.root, self.root2]:
                win.setTransparency(TransparencyAttrib.MAlpha)
                win.colorScaleInterval(
                    time, (0, 0, 0, 0), startColorScale=(1, 1, 1, 1)
                ).start()


UIManager = UIManager()


class API:

    class winTypes:
        SYSTEM = "SYSTEM"
        APPLICATION = "APPLICATION"
        DIALOG = "DIALOG"
        POPUP = "POPUP"
        WIDGET = "WIDGET"

    class WindowStack:
        windows: dict[str, "API.Window"] = {}
        activeWindow: "API.Window" = None
        lastWindow: "API.Window" = None
        globalID = 0
        globalBin = 0

        def getId(self):
            self.globalID += 1
            return self.globalID

        def getBin(self):
            self.globalBin += 1
            return self.globalBin

        def addWindow(self, window: "API.Window", name: str):
            self.windows[name] = window
            self.lastWindow = self.activeWindow
            self.activeWindow = window
            if self.lastWindow:
                self.lastWindow.defocusCommand()
            self.activeWindow.root.setBin("fixed", self.getBin())

        def removeWindow(self, name: str):
            if name in self.windows:
                self.windows[name].destroy()
                del self.windows[name]
                if self.lastWindow:
                    self.focusWindow(self.lastWindow.id)

        def getWindow(self, name: str):
            return self.windows.get(name, None)

        def removeWindow(self, name: str):
            if name in self.windows:
                del self.windows[name]
                if self.lastWindow:
                    self.focusWindow(self.lastWindow.id)

        def focusWindow(self, name: str):
            if name in self.windows:
                window = self.windows[name]
                window.root.setBin("fixed", self.getBin())
                self.activeWindow = window
                if self.lastWindow:
                    self.lastWindow.defocusCommand()
                self.lastWindow = window

    class Window:
        def __init__(
            self,
            name: str,
            position: tuple = (0, 0),
            size: tuple = (500, 300),
            frameColor=(1, 1, 1, 1),
            winType: "API.winTypes" = None,
        ):
            self.name = name
            self.position = position
            self.size = size
            self.winType = winType
            self.lastPos = position
            self.lastMousePos = (0, 0)
            self.moving = False
            self.id = API.WindowStack.getId()
            frameSize = (
                -(1 / (1280 / 2)) * (self.size[0] / 2) * (1280 / 720),
                (1 / (1280 / 2)) * (self.size[0] / 2) * (1280 / 720),
                -(1 / (720 / 2)) * (self.size[1] / 2),
                (1 / (720 / 2)) * (self.size[1] / 2),
            )

            if self.winType is None:
                self.winType = API.winTypes.APPLICATION
            if self.winType == API.winTypes.APPLICATION:
                self.root = DirectFrame(
                    parent=aspect2d,  # type: ignore
                    frameColor=frameColor,
                    frameSize=frameSize,
                    pos=(position[0], 0, position[1]),
                    relief=DGG.RIDGE,
                )
                self.topBar = DirectButton(
                    parent=self.root,
                    frameColor=(0.75, 0.75, 0.75, 1),
                    frameSize=(
                        frameSize[0],
                        frameSize[1],
                        frameSize[3] - 0.075,
                        frameSize[3],
                    ),
                    relief=DGG.FLAT,
                    geom=None,
                    scale=1,
                    text="",
                )
                self.topBar.bind(DGG.B1PRESS, lambda _: self.startMove())
                self.topBar.bind(DGG.B1RELEASE, lambda _: self.stopMove())

                self.topBar.setTransparency(TransparencyAttrib.MAlpha)
                self.topBarCloseButton = DirectButton(
                    parent=self.topBar,
                    text="X",
                    scale=0.036,
                    text_scale=1.4,
                    text_pos=(0, -0.4),
                    text_fg=(1, 1, 1, 1),
                    text_font=VRAM["WIN11FONT"],
                    text_align=TextNode.ACenter,
                    pos=(frameSize[1] - 0.05, 0, frameSize[3] - 0.0365),
                    frameColor=(0.9, 0.1, 0.2, 1),
                    frameSize=(-1.2, 1.2, -1, 1),
                    relief=DGG.FLAT,
                    command=self.destroy,
                )

                self.topBarNameText = DirectLabel(
                    parent=self.topBar,
                    text=name,
                    text_scale=0.05,
                    text_pos=(0, 0),
                    text_fg=(0, 0, 0, 1),
                    text_font=VRAM["WIN11FONT"],
                    text_align=TextNode.ALeft,
                    pos=(frameSize[0] + 0.1, 0, frameSize[3] - 0.038),
                    frameColor=(0.5, 0.5, 0.5, 0),
                    relief=DGG.FLAT,
                )
                taskMgr.add(self.move_task, "move_task")  # type: ignore
            elif self.winType == API.winTypes.SYSTEM:
                self.root = DirectFrame(
                    parent=aspect2d,  # type: ignore
                    frameColor=frameColor,
                    frameSize=frameSize,
                    pos=(position[0], 0, position[1]),
                    relief=DGG.RIDGE,
                )

            API.WindowStack.addWindow(window=self, name=self.id)

        def startMove(self):
            self.moving = True
            self.lastMousePos = (
                base.mouseWatcherNode.getMouse().x,
                base.mouseWatcherNode.getMouse().y,
            )
            API.WindowStack.focusWindow(self.id)

        def stopMove(self):
            self.moving = False

        def defocusCommand(self):
            if self.winType == API.winTypes.SYSTEM:
                self.destroy()

        def move_task(self, task):
            if base.mouseWatcherNode.hasMouse() and self.moving:
                mouse_pos = base.mouseWatcherNode.getMouse()
                x = mouse_pos.x - self.lastMousePos[0]
                y = mouse_pos.y - self.lastMousePos[1]
                self.root.setPos(self.root.getPos() + Vec3(x * (1280 / 720), 0, y))
                self.lastMousePos = (
                    mouse_pos.x,
                    mouse_pos.y,
                )
            return task.cont

        def destroy(self):
            API.WindowStack.removeWindow(self.id)
            self.root.removeNode()


API = API()
API.WindowStack = API.WindowStack()


class _state:
    PASS = "PASS"
    FAIL = "FAIL"
    ERR = "ERR"
    MEM_INVALID = "MEM_INVALID"
    VAL_INVALID = "VAL_INVALID"
    ACCESS_DENIED = "ACCESS_DENIED"
    OTHER = "OTHER"


_state = _state()


class FILEMGR:
    def __init__(self):
        self.keyStore = {"readmode": "r", "writemode": "w"}

    def loadPrefs(self):
        with open("./HYBERFIL", self.keyStore["readmode"]) as f:
            global GLOBALMEM
            try:
                _f: dict = loads(f.read())
                for d, v in _f.items():
                    GLOBALMEM[d] = v
            except Exception as e:
                print("Error loading RAM disk: ", e)
                GLOBALMEM.clear()
                GLOBALMEM = DEFAULTS

        print("Loaded RAM disk")

    def savePrefs(self):
        with open("./HYBERFIL", self.keyStore["writemode"]) as f:
            dump(GLOBALMEM, f, indent=4)
        print("Saved RAM disk")

    def getKey(self, key):
        return self.keyStore.get(key, None)

    def setKey(self, key, value):
        self.keyStore[key] = value


FILEMGR = FILEMGR()


class AUTH:
    def login(self, username, password):
        return self.verify(username, password)

    def verify(self, username, password) -> _state:
        if username in GLOBALMEM["AUTH"]["users"]:
            if GLOBALMEM["AUTH"]["users"][username] == password:
                return _state.PASS
            else:
                return _state.VAL_INVALID
        elif len(username) == 0:
            return _state.ERR
        elif len(GLOBALMEM["AUTH"]["users"]) == 0:
            return _state.PASS
        else:
            return _state.MEM_INVALID


AUTH = AUTH()


class PROGRAM:
    def __init__(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        os.chdir(path)
        jsonFile = open("index.json", "r")
        self.data = loads(jsonFile.read())
        jsonFile.close()
        self.name = self.data["name"]
        self.execPath = os.path.abspath(self.data["execPath"])
        self.image = VRAM["LOADER"].loadTexture(
            "/"
            + os.path.abspath(self.data["iconPath"]).replace("\\", "/").replace(":", "")
        )
        self.hover_text = self.data["hover_text"]
        self.description = self.data["description"]
        self.programData = self.data["programData"]
        os.chdir("..")

    def run(self):
        with open(self.execPath, "r") as fp:
            programData = fp.read()

        INJECTOR = """"""
        programData = INJECTOR + programData
        exec(programData, globals())


class TASKBAR:
    def __init__(self):
        self.programs = []
        self.nodes = []

    def load(self, parent: "UIManager.Window" = None):
        self.parent = parent
        currentPath = os.path.dirname(os.path.abspath(__file__))
        os.chdir(os.path.join(currentPath, "src", "prgm"))
        for filepath in sorted(os.listdir()):
            if os.path.isdir(filepath):
                self.addProgram(PROGRAM(filepath))
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        self.border = DirectFrame(
            parent=parent.root2,
            frameColor=(1, 1, 1, 1),
            frameSize=(-1, 1, -0.075, 0.075),
            pos=(0, 0, -0.925),
        )
        self.border.setTransparency(TransparencyAttrib.MAlpha)
        self.rebuild()

    def rebuild(self):
        programsLen = len(self.getPrograms())
        if programsLen == 0:
            return
        for nodes in self.nodes:
            for n in nodes:
                n.removeNode()

        self.nodes.clear()

        program: PROGRAM
        for i, program in enumerate(self.getPrograms()):
            spacing = 0.135
            xPos = -0.925 + (i * spacing) + (spacing * (programsLen - 1) / 2)
            outline = OnscreenImage(
                image="./src/img/rounded_outline.png",
                scale=(0.07, 0.07, 0.07),
                pos=(xPos, 0, -0.925),
                parent=self.parent.root,
            )
            outline.setTransparency(TransparencyAttrib.MAlpha)

            programButton = DirectButton(
                parent=self.parent.root,
                image=program.image,
                scale=(0.06),
                pos=(xPos, 0, -0.925),
                frameColor=(0.5, 0.5, 0.5, 0.5),
                frameSize=(-1, 1, -1, 1),
                geom=None,
                relief=None,
                command=program.run,
            )
            programButton.setTransparency(TransparencyAttrib.MAlpha)

            programHoverText = DirectLabel(
                text=program.hover_text,
                text_font=VRAM["WIN11FONT"],
                text_fg=(1, 1, 1, 1),
                pos=(xPos, 0, -0.825),
                scale=0.05,
                parent=self.parent.root,
                frameColor=(0, 0, 0, 0.25),
            )
            programHoverText.setTransparency(TransparencyAttrib.MAlpha)

            programHoverText.setColorScale(1, 1, 1, 0)
            outline.setColorScale(0.5, 0.5, 0.5, 0)

            def mouseOver(hover, outline, programHoverText):
                if hover:
                    programHoverText.setColorScale(1, 1, 1, 1)
                    outline.setColorScale(0.5, 0.5, 0.5, 1)
                else:
                    programHoverText.setColorScale(1, 1, 1, 0)
                    outline.setColorScale(0.5, 0.5, 0.5, 0)

            self.nodes.append([outline, programButton, programHoverText])
            MouseOverManager.registerElement(
                element=programButton,
                hitbox_scale=(0.6, 0.6),
                callback=mouseOver,
                outline=outline,
                programHoverText=programHoverText,
            )

    def addProgram(self, program):
        self.programs.append(program)
        self.rebuild()

    def removeProgram(self, program):
        self.programs.remove(program)
        self.rebuild()

    def getPrograms(self):
        return self.programs


TASKBAR = TASKBAR()


class TaskManager:
    def __init__(self):
        self.tasks = []

    def addTask(self, task, *args, **kwargs):
        self.tasks.append([task, args, kwargs])

    def removeTask(self, task):
        for t, a, kw in self.tasks:
            if t == task:
                self.tasks.remove([t, a, kw])
                break

    def update(self, p3d_task):
        for task, args, kwargs in self.tasks:
            task(*args, **kwargs)
        return p3d_task.cont


TaskManager = TaskManager()


class GUI:
    def setTimeNodes(self, task):
        self.lockScreenTimeNode.setText(time.strftime("%I:%M:%S").lstrip("0"))
        self.lockScreenDateNode.setText(time.strftime("%A, %B %Y"))
        return task.cont

    def setEntryFocus(self, entry):
        entry["focus"] = 1
        entry.setFocus()
        self.clearTextOnFocus(entry)

    def login(self, username, password):
        result = AUTH.login(username, password)
        if result == _state.PASS:
            UIManager.fadeToPage("home", 0.35)
            TASKBAR.load(self.homeScreen)
            self.win11StartupSound.play()

    def __init__(self, base: "OS"):
        self.base = base
        self.base.setBackgroundColor(0, 0, 0, 1)
        self.windows = []
        self.lockScreenWindow = UIManager.Window("lockScreen", UIManager)
        self.loginWindow = UIManager.Window("login", UIManager)
        self.homeScreen = UIManager.Window("home", UIManager)
        self.win11StartupSound = self.base.loader.loadSfx("./src/audio/startup.m4a")

        self.win11Font = self.base.loader.loadFont(
            "./src/fonts/SegoeUIVF.ttf",
            pixelsPerUnit=200,
        )
        VRAM["WIN11FONT"] = self.win11Font
        self.lockScreenBackgroundButton = DirectButton(
            image="./src/img/lockBackground.jpg",
            image_scale=(1 * (1920 / 1080), 1, 1),
            frameSize=(-1 * (1920 / 1080), 1 * (1920 / 1080), -1, 1),
            parent=self.lockScreenWindow.root,
            relief=None,
            geom=None,
            command=lambda: [
                UIManager.fadeToPage("login", 0.15),
                self.setEntryFocus(self.loginScreenUsernameEntry),
            ],
            pressEffect=False,
        )
        self.lockScreenBackgroundButton.setTransparency(TransparencyAttrib.MAlpha)
        self.lockScreenTimeNode = OnscreenText(
            text=time.strftime("%I:%M:%S").lstrip("0"),
            font=self.win11Font,
            fg=(1, 1, 1, 1),
            pos=(0, 0.45),
            scale=0.2,
            mayChange=True,
            parent=self.lockScreenWindow.root,
        )
        self.lockScreenDateNode = OnscreenText(
            text=time.strftime("%A, %B %Y"),
            font=self.win11Font,
            fg=(1, 1, 1, 1),
            pos=(0, 0.35),
            scale=0.045,
            mayChange=True,
            parent=self.lockScreenWindow.root,
        )
        self.lockScreenWifiImage = OnscreenImage(
            image="./src/img/wifi.png",
            scale=(0.025 * (1280 / 942), 0.025, 0.025),
            pos=(1.5, 0, -0.9),
            parent=self.lockScreenWindow.root,
        )
        self.lockScreenWifiImage.setTransparency(TransparencyAttrib.MAlpha)

        self.loginScreenBackgroundImage = DirectButton(
            image="./src/img/lockBackground_blr.jpg",
            scale=(1 * (1920 / 1080), 1, 1),
            parent=self.loginWindow.root,
            relief=None,
            geom=None,
            command=lambda: [
                self.restoreDefaultTextOnFocusOut(self.loginScreenPasswordEntry),
                self.restoreDefaultTextOnFocusOut(self.loginScreenUsernameEntry),
            ],
            pressEffect=False,
        )
        self.loginScreenBackgroundImage.setTransparency(TransparencyAttrib.MAlpha)

        self.loginScreenUsernameProfileImage = OnscreenImage(
            image="./src/img/profile.png",
            scale=(0.2, 0.2, 0.2),
            pos=(0, 0, 0.35),
            parent=self.loginWindow.root,
        )
        self.loginScreenUsernameProfileImage.setTransparency(TransparencyAttrib.MAlpha)

        self.loginScreenUsernameEntry = DirectEntry(
            text="",
            scale=0.05,
            initialText="Username",
            numLines=1,
            focus=0,
            parent=self.loginWindow.root,
            pos=(0, 0, 0),
            frameColor=(0.5, 0.5, 0.5, 0.5),
            text_fg=(1, 1, 1, 1),
            text_font=self.win11Font,
            text_align=TextNode.ACenter,
            relief=DGG.FLAT,
            command=lambda t: self.setEntryFocus(self.loginScreenPasswordEntry),
        )
        self.loginScreenUsernameEntry.bind(
            DGG.B1PRESS, lambda _: self.clearTextOnFocus(self.loginScreenUsernameEntry)
        )
        self.loginScreenUsernameEntry.setTransparency(TransparencyAttrib.MAlpha)

        self.loginScreenPasswordEntry = DirectEntry(
            text="",
            scale=0.05,
            initialText="Password",
            numLines=1,
            focus=0,
            parent=self.loginWindow.root,
            pos=(0, 0, -0.15),
            frameColor=(0.5, 0.5, 0.5, 0.5),
            text_fg=(1, 1, 1, 1),
            text_font=self.win11Font,
            text_align=TextNode.ACenter,
            relief=DGG.FLAT,
            obscured=True,
            command=lambda t: [
                self.login(
                    self.loginScreenUsernameEntry.get(),
                    self.loginScreenPasswordEntry.get(),
                ),
            ],
        )
        self.loginScreenPasswordEntry.bind(
            DGG.B1PRESS, lambda _: self.clearTextOnFocus(self.loginScreenPasswordEntry)
        )
        self.loginScreenPasswordEntry.setTransparency(TransparencyAttrib.MAlpha)

        self.homeScreenBackgroundImage = DirectButton(
            image="./src/img/windows11background.png",
            scale=(1 * (1920 / 1080), 1, 1),
            parent=self.homeScreen.root,
            relief=None,
            geom=None,
            pressEffect=False,
        )
        self.homeScreenBackgroundImage.setTransparency(TransparencyAttrib.MAlpha)
        self.homeScreenBackgroundImage.setBin("background", 0)

        self.lockScreenWindow.show()
        base.taskMgr.add(self.setTimeNodes, "setTimeNodes", delay=1)

    def clearTextOnFocus(self, entry: DirectEntry):
        if entry.get() in ["Password", "Username"]:
            entry.enterText("")
        if entry == self.loginScreenPasswordEntry:
            self.restoreDefaultTextOnFocusOut(self.loginScreenUsernameEntry)
        elif entry == self.loginScreenUsernameEntry:
            self.restoreDefaultTextOnFocusOut(self.loginScreenPasswordEntry)
        entry["focus"] = 1
        entry.setFocus()

    def restoreDefaultTextOnFocusOut(self, entry: DirectEntry):
        if entry.get().strip() == "":
            if entry == self.loginScreenPasswordEntry:
                entry.enterText("Password")
            elif entry == self.loginScreenUsernameEntry:
                entry.enterText("Username")
        entry["focus"] = 0
        entry.setFocus()


class MouseOverManager:
    def __init__(self):
        self.elements = []
        self.activeElements = []

    def registerElement(self, element, hitbox_scale, callback, *args, **kwargs):
        """
        Registers an element with a callback to be triggered when the mouse is over the element.
        :param element: The NodePath or DirectGUI element to monitor.
        :param callback: The function to call when the mouse is over the element.
        """
        self.elements.append((element, hitbox_scale, callback, args, kwargs))

    def update(self):
        """
        Checks if the mouse is over any registered elements and triggers the corresponding callbacks.
        """
        if base.mouseWatcherNode.hasMouse():
            mouse_pos = base.mouseWatcherNode.getMouse()
            for element, hitbox_scale, callback, args, kwargs in self.elements:
                if not element or element.isEmpty() or element.isHidden():
                    continue
                bounds = element.getBounds()
                xmin, xmax, ymin, ymax = bounds
                transform = element.getTransform(base.render2d)
                pos: tuple[3] = transform.getPos()
                scale: tuple[3] = element.getScale()
                xmin *= scale[0] * hitbox_scale[0]
                xmax *= scale[0] * hitbox_scale[0]
                ymin *= scale[2] * hitbox_scale[1]
                ymax *= scale[2] * hitbox_scale[1]

                xmin += pos[0]
                xmax += pos[0]
                ymin += pos[2]
                ymax += pos[2]

                bounds = (xmin, xmax, ymin, ymax)
                if xmin <= mouse_pos.x <= xmax and ymin <= mouse_pos.y <= ymax:
                    if element not in self.activeElements:
                        self.activeElements.append(element)
                        callback(True, *args, **kwargs)
                else:
                    if element in self.activeElements:
                        self.activeElements.remove(element)
                        callback(False, *args, **kwargs)


MouseOverManager = MouseOverManager()


class OS(ShowBase):
    def __init__(self):
        super().__init__()
        VRAM["OS"] = self
        VRAM["LOADER"] = self.loader
        self.gui = GUI(self)
        self.taskMgr.add(TaskManager.update, "TaskManager")  # type: ignore
        TaskManager.addTask(task=MouseOverManager.update)


FILEMGR.loadPrefs()

loadPrcFileData("", GLOBALMEM["PANDAPRC"]["PRCFILE"])
exec(GLOBALMEM["PANDAPRC"]["STARTUP_INJECTOR"])


def exit_handler():
    FILEMGR.savePrefs()


atexit.register(exit_handler)

base = OS()
base.run()
