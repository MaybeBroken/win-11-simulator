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
from direct.showbase.Audio3DManager import Audio3DManager

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
        state = self.verify(username, password)
        if state is _state.PASS:
            print("Logged in")
        elif state is _state.VAL_INVALID:
            print("Invalid Password")
        elif state is _state.MEM_INVALID:
            print("Invalid Username")
        else:
            print("Unknown Error")
        return state

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
        self.execPath = self.data["execPath"]
        self.image = VRAM["LOADER"].loadTexture(
            "/"
            + os.path.abspath(self.data["iconPath"]).replace("\\", "/").replace(":", "")
        )
        self.hover_text = self.data["hover_text"]
        self.description = self.data["description"]
        self.programData = self.data["programData"]


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
            xPos = 0 - (2 / programsLen) * (i + 1) + 1
            outline = OnscreenImage(
                image="./src/img/rounded_outline.png",
                scale=(0.07, 0.07, 0.07),
                pos=(xPos, 0, -0.925),
                parent=self.parent.root,
            )
            outline.setTransparency(TransparencyAttrib.MAlpha)
            outline.setColorScale(0.5, 0.5, 0.5, 0.5)

            programButton = DirectButton(
                parent=self.parent.root,
                image=program.image,
                scale=(0.055),
                pos=(xPos, 0, -0.925),
                frameColor=(0.5, 0.5, 0.5, 0.5),
                frameSize=(-1, 1, -1, 1),
                geom=None,
                relief=None,
            )
            programButton.setTransparency(TransparencyAttrib.MAlpha)

            programHoverText = DirectLabel(
                text=program.hover_text,
                text_font=VRAM["WIN11FONT"],
                text_fg=(1, 1, 1, 1),
                pos=(xPos, 0, -0.85),
                scale=0.05,
                parent=self.parent.root,
                frameColor=(0, 0, 0, 0),
            )
            programHoverText.setTransparency(TransparencyAttrib.MAlpha)
            programHoverText.setColorScale(1, 1, 1, 0)

            self.nodes.append([outline, programButton, programHoverText])
        print("Rebuilt Taskbar")

    def addProgram(self, program):
        self.programs.append(program)
        print(f"Added program: {program.name}")
        self.rebuild()

    def removeProgram(self, program):
        self.programs.remove(program)
        print(f"Removed program: {program.name}")
        self.rebuild()

    def getPrograms(self):
        print("Getting programs")
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

    def update(self):
        for task, args, kwargs in self.tasks:
            task(*args, **kwargs)


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


class OS(ShowBase):
    def __init__(self):
        super().__init__()
        VRAM["OS"] = self
        VRAM["LOADER"] = self.loader
        self.gui = GUI(self)


FILEMGR.loadPrefs()

loadPrcFileData("", GLOBALMEM["PANDAPRC"]["PRCFILE"])
exec(GLOBALMEM["PANDAPRC"]["STARTUP_INJECTOR"])


def exit_handler():
    FILEMGR.savePrefs()


atexit.register(exit_handler)

base = OS()
base.run()
