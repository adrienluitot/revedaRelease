"""
======================= START OF LICENSE NOTICE =======================
  Copyright (C) 2022 Murat Eskiyerli. All Rights Reserved

  NO WARRANTY. THE PRODUCT IS PROVIDED BY DEVELOPER "AS IS" AND ANY
  EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL DEVELOPER BE LIABLE FOR
  ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
  GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
  IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
  OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THE PRODUCT, EVEN
  IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
======================== END OF LICENSE NOTICE ========================
  Primary Author: Murat Eskiyerli

"""
import logging
import logging.config
import pathlib
import sys
from contextlib import redirect_stderr, redirect_stdout

import backend.schBackEnd as scb  # import the backend
import gui.editorWindows as edw
import gui.pythonConsole as pcon
import api.ui as ui
import resources.resources
import yaml
from PySide6.QtGui import (QAction, QFont, QIcon, )
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                               QMenuBar, )


class mainwContainer(QWidget):
    """
    Definition for the main app window layout.
    """

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.parent = parent
        self.console = pcon.pythonConsole(globals())
        self.init_UI()

    def init_UI(self):
        # treeView = designLibrariesView(self)

        self.console.writeoutput("Welcome to RevEDA")
        self.console.writeoutput("Revolution Semiconductor (C) 2022.")
        self.console.setfont(QFont("Fira Mono Regular", 12))
        # layout statements, using a grid layout
        gLayout = QVBoxLayout()
        gLayout.setSpacing(10)
        gLayout.addWidget(self.console)
        self.setLayout(gLayout)


# main application window definition
class mainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        # revEDAPathObj = Path(__file__)
        revEDADirObj = pathlib.Path.cwd().parent
        # library definition file path
        libraryPathObj = revEDADirObj.joinpath("library.yaml")
        try:
            with libraryPathObj.open(mode="r") as f:
                # create a dictionary of library (directory) names and paths
                self.libraryDict = scb.readLibDefFile(f)
        except IOError:
            print(f"Cannot find {str(libraryPathObj)} file.")
            self.libraryDict = {}
        # this list is the list of usable cellviews.i
        self.cellViews = ["schematic", "symbol", "layout", "veriloga"]
        self.init_UI()
        # Create a custom logger
        self.logger = logging.getLogger(__name__)
        c_handler = logging.StreamHandler(stream=self.centralW.console)
        c_handler.setLevel(logging.WARNING)
        c_format = logging.Formatter('%(levelname)s - %(message)s')
        c_handler.setFormatter(c_format)
        f_handler = logging.FileHandler('reveda.log')
        f_handler.setLevel(logging.DEBUG)
        f_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        f_handler.setFormatter(f_format)
        self.logger.addHandler(c_handler)
        self.logger.addHandler(f_handler)

    def init_UI(self):
        self.resize(900, 300)
        self._createMenuBar()
        self._createActions()
        # create container to position all widgets
        self.centralW = mainwContainer(self)
        self.setCentralWidget(self.centralW)
        self.libraryBrowser = None

    def _createMenuBar(self):
        self.mainW_menubar = self.menuBar()
        self.mainW_menubar.setNativeMenuBar(False)
        # Returns QMenu object.
        self.menuFile = self.mainW_menubar.addMenu("&File")
        self.menuTools = self.mainW_menubar.addMenu("&Tools")
        self.importTools = self.menuTools.addMenu("&Import")
        self.menuOptions = self.mainW_menubar.addMenu("&Options")
        self.menuHelp = self.mainW_menubar.addMenu("&Help")

        self.mainW_statusbar = self.statusBar()
        self.mainW_statusbar.showMessage("Ready")

        # create actions

    def _createActions(self):
        exitIcon = QIcon(":/icons/external.png")
        self.exitAction = QAction(exitIcon, "Exit", self)
        self.exitAction.setShortcut("Ctrl+Q")
        self.exitAction.triggered.connect(self.exitApp)  # type: ignore
        self.menuFile.addAction(self.exitAction)

        openLibIcon = QIcon(":/icons/database--pencil.png")
        self.libraryBrowserAction = QAction(openLibIcon, "Library Browser", self)
        self.menuTools.addAction(self.libraryBrowserAction)
        self.libraryBrowserAction.triggered.connect(self.libraryBrowserClick)

        importVerilogaIcon = QIcon(":/icons/document--plus.png")
        self.importVerilogaAction = QAction(importVerilogaIcon, 'Import Verilog-a '
                                                                'file...')
        self.importTools.addAction(self.importVerilogaAction)

        newCellIcon = QIcon(":/icons/document--plus.png")
        self.importVerilogaAction = QAction(newCellIcon, "Import Verilog-A", self)

    # open library browser window
    def libraryBrowserClick(self):
        if self.libraryBrowser is None:
            self.libraryBrowser = edw.libraryBrowser(self)  # create the library browser
            self.libraryBrowser.show()  # update the main library dictionary if library path dialogue  # is OK'd.
        else:
            self.libraryBrowser.show()
            self.libraryBrowser.raise_()

    def libDictUpdate(self):
        self.libraryDict = self.libraryBrowser.libraryDict

    def exitApp(self):
        self.app.closeAllWindows()

    def closeEvent(self, event):
        self.app.closeAllWindows()
        event.accept()


# Start Main application window
app = QApplication(sys.argv)
app.setStyle("Fusion")
# empty argument as there is no parent window.
mainW = mainWindow(app)
mainW.setWindowTitle("Revolution EDA Main Window")
redirect = pcon.Redirect(mainW.centralW.console.errorwrite)
with redirect_stdout(mainW.centralW.console), redirect_stderr(redirect):
    mainW.show()
    sys.exit(app.exec())
