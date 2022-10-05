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

#  Copyright (c) 2022.

import copy
import datetime
import json
import math
# from hashlib import new
import pathlib
import shutil

import revedaeditor.backend.schBackEnd as scb  # import the backend
import revedaeditor.backend.undoStack as us
import revedaeditor.common.circuitElements as cel
import revedaeditor.common.net as net
import revedaeditor.common.shape as shp  # import the shapes
import revedaeditor.fileio.loadJSON as lj
import revedaeditor.fileio.symbolEncoder as se
import revedaeditor.gui.propertyDialogues as pdlg
import revedaeditor.resources
import revedasimgui.app as revedasim

# import numpy as np
from PySide6.QtCore import (QDir, Qt, QRect, QPoint, QMargins, QRectF, QSize, QPointF, )
from PySide6.QtGui import (QAction, QKeySequence, QColor, QIcon, QPainter, QPen,
                           QStandardItemModel, QCursor, QUndoStack, QTextDocument,
                           QGuiApplication, QCloseEvent)
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFileDialog,
                               QFormLayout, QGraphicsScene, QHBoxLayout, QLabel,
                               QLineEdit, QMainWindow, QMenu, QMessageBox, QToolBar,
                               QTreeView, QVBoxLayout, QWidget, QGraphicsItem,
                               QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsView,
                               QGridLayout, QGraphicsSceneMouseEvent, QRubberBand)


class editorWindow(QMainWindow):
    def __init__(self, filePath: pathlib.Path, libraryDict: dict,
                 libraryView, ):  # file is a pathlib.Path object
        super().__init__()
        self.file = filePath
        self.cellName = self.file.parent.stem
        self.libName = self.file.parent.parent.stem
        self.viewName = self.file.stem
        self.libraryDict = libraryDict
        self.libraryView = libraryView
        self.parentView = None
        self._createActions()
        self._createTriggers()
        self._createShortcuts()
        self.init_UI()
        self.appMainW = self.libraryView.parent.parent.parent
        self.logger = self.appMainW.logger
        self.switchViewList = ['schematic' , 'veriloga', 'symbol']
        self.stopViewList = ['symbol']

    def init_UI(self):
        """
        Placeholder for child classes init_UI function.
        """
        pass

    def _createMenuBar(self):
        self.editorMenuBar = self.menuBar()
        self.editorMenuBar.setNativeMenuBar(False)
        # Returns QMenu object.
        self.menuFile = self.editorMenuBar.addMenu("&File")
        self.menuView = self.editorMenuBar.addMenu("&View")
        self.menuEdit = self.editorMenuBar.addMenu("&Edit")
        self.menuCreate = self.editorMenuBar.addMenu("C&reate")
        self.menuCheck = self.editorMenuBar.addMenu("&Check")
        self.menuTools = self.editorMenuBar.addMenu("&Tools")
        self.menuWindow = self.editorMenuBar.addMenu("&Window")
        self.menuUtilities = self.editorMenuBar.addMenu("&Utilities")

    def _createActions(self):
        checkCellIcon = QIcon(":/icons/document-task.png")
        self.checkCellAction = QAction(checkCellIcon, "Check-Save", self)

        self.readOnlyCellIcon = QIcon(":/icons/lock.png")
        self.readOnlyCellAction = QAction(self.readOnlyCellIcon, "Make Read Only", self)

        printIcon = QIcon(":/icons/printer--arrow.png")
        self.printAction = QAction(printIcon, "Print...", self)

        exportImageIcon = QIcon(":/icons/image-export.png")
        self.exportImageAction = QAction(exportImageIcon, "Export...", self)

        exitIcon = QIcon(":/icons/external.png")
        self.exitAction = QAction(exitIcon, "Close Window", self)
        self.exitAction.setShortcut("Ctrl+Q")

        fitIcon = QIcon(":/icons/zone.png")
        self.fitAction = QAction(fitIcon, "Fit to Window", self)

        zoomInIcon = QIcon(":/icons/zone-resize.png")
        self.zoomInAction = QAction(zoomInIcon, "Zoom In", self)

        zoomOutIcon = QIcon(":/icons/zone-resize-actual.png")
        self.zoomOutAction = QAction(zoomOutIcon, "Zoom Out", self)

        panIcon = QIcon(":/icons/zone--arrow.png")
        self.panAction = QAction(panIcon, "Pan View", self)

        redrawIcon = QIcon(":/icons/arrow-circle.png")
        self.redrawAction = QAction(redrawIcon, "Redraw", self)

        # rulerIcon = QIcon(":/icons/ruler.png")
        # self.rulerAction = QAction(rulerIcon, 'Ruler', self)
        # self.menuView.addAction(self.rulerAction)
        # delRulerIcon = QIcon.fromTheme('delete')
        # self.delRulerAction = QAction(delRulerIcon, 'Delete Rulers', self)
        # self.menuView.addAction(self.delRulerAction)

        # display options
        dispConfigIcon = QIcon(":/icons/resource-monitor.png")
        self.dispConfigAction = QAction(dispConfigIcon, "Display Config...", self)

        selectConfigIcon = QIcon(":/icons/zone-select.png")
        self.selectConfigAction = QAction(selectConfigIcon, "Selection Config...", self)

        panZoomConfigIcon = QIcon(":/icons/selection-resize.png")
        self.panZoomConfigAction = QAction(panZoomConfigIcon, "Pan/Zoom Config...", self)

        undoIcon = QIcon(":/icons/arrow-circle-315-left.png")
        self.undoAction = QAction(undoIcon, "Undo", self)

        redoIcon = QIcon(":/icons/arrow-circle-225.png")
        self.redoAction = QAction(redoIcon, "Redo", self)

        yankIcon = QIcon(":/icons/node-insert.png")
        self.yankAction = QAction(yankIcon, "Yank", self)

        pasteIcon = QIcon(":/icons/clipboard-paste.png")
        self.pasteAction = QAction(pasteIcon, "Paste", self)

        deleteIcon = QIcon(":/icons/node-delete.png")
        self.deleteAction = QAction(deleteIcon, "Delete", self)

        copyIcon = QIcon(":/icons/document-copy.png")
        self.copyAction = QAction(copyIcon, "Copy", self)

        moveIcon = QIcon(":/icons/arrow-move.png")
        self.moveAction = QAction(moveIcon, "Move", self)

        moveByIcon = QIcon(":/icons/arrow-transition.png")
        self.moveByAction = QAction(moveByIcon, "Move By ...", self)

        moveOriginIcon = QIcon(":/icons/arrow-skip.png")
        self.moveOriginAction = QAction(moveOriginIcon, "Move Origin", self)

        stretchIcon = QIcon(":/icons/fill.png")
        self.stretchAction = QAction(stretchIcon, "Stretch", self)

        rotateIcon = QIcon(":/icons/arrow-circle.png")
        self.rotateAction = QAction(rotateIcon, "Rotate...", self)

        scaleIcon = QIcon(":/icons/selection-resize.png")
        self.scaleAction = QAction(scaleIcon, "Scale...", self)

        netNameIcon = QIcon(":/icons/node-design.png")
        self.netNameAction = QAction(netNameIcon, "Net Name...", self)

        # create label action but do not add to any menu.
        createLabelIcon = QIcon(":/icons/tag-label-yellow.png")
        self.createLabelAction = QAction(createLabelIcon, "Create Label...", self)

        createPinIcon = QIcon(":/icons/pin--plus.png")
        self.createPinAction = QAction(createPinIcon, "Create Pin...", self)

        goUpIcon = QIcon(":/icons/arrow-step-out.png")
        self.goUpAction = QAction(goUpIcon, "Go Up   ↑", self)

        goDownIcon = QIcon(":/icons/arrow-step.png")
        self.goDownAction = QAction(goDownIcon, "Go Down ↓", self)

        self.selectAllIcon = QIcon(":/icons/node-select-all.png")
        self.selectAllAction = QAction(self.selectAllIcon, "Select All", self)

        deselectAllIcon = QIcon(":/icons/node.png")
        self.deselectAllAction = QAction(deselectAllIcon, "Unselect All", self)

        objPropIcon = QIcon(":/icons/property-blue.png")
        self.objPropAction = QAction(objPropIcon, "Object Properties...", self)

        viewPropIcon = QIcon(":/icons/property.png")
        self.viewPropAction = QAction(viewPropIcon, "Cellview Properties...", self)

        viewCheckIcon = QIcon(":/icons/ui-check-box.png")
        self.viewCheckAction = QAction(viewCheckIcon, "Check CellView", self)

        viewErrorsIcon = QIcon(":/icons/report--exclamation.png")
        self.viewErrorsAction = QAction(viewErrorsIcon, "View Errors...", self)

        deleteErrorsIcon = QIcon(":/icons/report--minus.png")
        self.deleteErrorsAction = QAction(deleteErrorsIcon, "Delete Errors...", self)

        netlistIcon = QIcon(":/icons/script-text.png")
        self.netlistAction = QAction(netlistIcon, "Create Netlist...", self)

        simulateIcon = QIcon(":/icons/application-wave.png")
        self.simulateAction = QAction(simulateIcon, "Run RevEDA Sim GUI", self)

        createLineIcon = QIcon(":/icons/layer-shape-line.png")
        self.createLineAction = QAction(createLineIcon, "Create Line...", self)

        createRectIcon = QIcon(":/icons/layer-shape.png")
        self.createRectAction = QAction(createRectIcon, "Create Rectangle...", self)

        createPolyIcon = QIcon(":/icons/layer-shape-polygon.png")
        self.createPolyAction = QAction(createPolyIcon, "Create Polygon...", self)

        createCircleIcon = QIcon(":/icons/layer-shape-ellipse.png")
        self.createCircleAction = QAction(createCircleIcon, "Create Circle...", self)

        createArcIcon = QIcon(":/icons/layer-shape-polyline.png")
        self.createArcAction = QAction(createArcIcon, "Create Arc...", self)

        createInstIcon = QIcon(":/icons/block--plus.png")
        self.createInstAction = QAction(createInstIcon, "Create Instance...", self)

        createWireIcon = QIcon(":/icons/node-insert.png")
        self.createWireAction = QAction(createWireIcon, "Create Wire...", self)

        createBusIcon = QIcon(":/icons/node-select-all.png")
        self.createBusAction = QAction(createBusIcon, "Create Bus...", self)

        createLabelIcon = QIcon(":/icons/tag-label-yellow.png")
        self.createLabelAction = QAction(createLabelIcon, "Create Label...", self)

        createPinIcon = QIcon(":/icons/pin--plus.png")
        self.createPinAction = QAction(createPinIcon, "Create Pin...", self)

        createSymbolIcon = QIcon(":/icons/application-block.png")
        self.createSymbolAction = QAction(createSymbolIcon, "Create Symbol...", self)

    def _createToolBars(self):
        # Create tools bar called "main toolbar"
        self.toolbar = QToolBar("Main Toolbar", self)
        # place toolbar at top
        self.addToolBar(self.toolbar)
        self.toolbar.addAction(self.printAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.undoAction)
        self.toolbar.addAction(self.redoAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.deleteAction)
        self.toolbar.addAction(self.moveAction)
        self.toolbar.addAction(self.copyAction)
        self.toolbar.addAction(self.stretchAction)
        self.toolbar.addAction(self.rotateAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.fitAction)
        self.toolbar.addAction(self.zoomInAction)
        self.toolbar.addAction(self.zoomOutAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.objPropAction)

    def _addActions(self):
        # file menu
        self.menuFile.addAction(self.checkCellAction)
        self.menuFile.addAction(self.readOnlyCellAction)
        self.menuFile.addAction(self.printAction)
        self.menuFile.addAction(self.exportImageAction)
        self.menuFile.addAction(self.exitAction)
        # view menu
        self.menuView.addAction(self.fitAction)
        self.menuView.addAction(self.zoomInAction)
        self.menuView.addAction(self.zoomOutAction)
        self.menuView.addAction(self.panAction)
        self.menuView.addAction(self.redrawAction)
        self.menuView.addAction(self.dispConfigAction)
        self.menuView.addAction(self.selectConfigAction)
        self.menuView.addAction(self.panZoomConfigAction)
        # edit menu
        self.menuEdit.addAction(self.undoAction)
        self.menuEdit.addAction(self.redoAction)
        self.menuEdit.addAction(self.yankAction)
        self.menuEdit.addAction(self.pasteAction)
        self.menuEdit.addAction(self.deleteAction)
        self.menuEdit.addAction(self.copyAction)
        self.menuEdit.addAction(self.moveAction)
        self.menuEdit.addAction(self.moveByAction)
        self.menuEdit.addAction(self.moveOriginAction)
        self.menuEdit.addAction(self.stretchAction)
        self.menuEdit.addAction(self.rotateAction)

        self.menuCheck.addAction(self.viewCheckAction)

    def _createTriggers(self):
        self.exitAction.triggered.connect(self.closeWindow)
        self.fitAction.triggered.connect(self.fitToWindow)
        self.zoomInAction.triggered.connect(self.zoomIn)
        self.zoomOutAction.triggered.connect(self.zoomOut)
        self.dispConfigAction.triggered.connect(self.dispConfDialog)
        self.moveOriginAction.triggered.connect(self.moveOrigin)

    def _createShortcuts(self):
        self.redoAction.setShortcut("Shift+U")
        self.undoAction.setShortcut(Qt.Key_U)
        self.objPropAction.setShortcut(Qt.Key_Q)
        self.copyAction.setShortcut("C")
        self.rotateAction.setShortcut("Ctrl+R")
        self.deleteAction.setShortcut(QKeySequence.Delete)

    def dispConfDialog(self):
        dcd = displayConfigDialog(self)
        if dcd.exec() == QDialog.Accepted:
            gridValue = int(float(dcd.majorGridEntry.text()))
            self.centralW.scene.gridMajor = gridValue
            self.centralW.view.gridMajor = gridValue
            self.centralW.scene.gridTuple = (gridValue, gridValue)
            self.centralW.scene.update()
            self.centralW.view.update()

    # def deleteItemMethod(self, s):
    #     self.centralW.scene.itemDelete = True

    def fitToWindow(self):
        self.centralW.view.fitToView()

    def zoomIn(self):
        self.centralW.view.scale(1.25, 1.25)

    def zoomOut(self):
        self.centralW.view.scale(0.8, 0.8)

    def closeWindow(self):
        self.close()

    def _createMenu(self):
        pass

    def moveOrigin(self):
        self.centralW.scene.changeOrigin = True


class schematicEditor(editorWindow):
    def __init__(self, filePath: pathlib.Path, libraryDict: dict, libraryView) -> None:
        super().__init__(filePath, libraryDict=libraryDict, libraryView=libraryView)
        self.setWindowTitle(f"Schematic Editor - {self.cellName}")
        self.setWindowIcon(QIcon(":/icons/layer-shape.png"))
        self.symbolChooser = None
        self.cellViews = [
            "symbol"]  # only symbol can be instantiated in the schematic window.
        self._schematicActions()

    def init_UI(self):
        self.resize(1600, 800)
        self._createMenuBar()
        self._createToolBars()
        # create container to position all widgets
        self.centralW = schematicContainer(self)
        self.setCentralWidget(self.centralW)
        self.statusLine = self.statusBar()
        self.messageLine = QLabel()  # message line
        self.statusLine.addPermanentWidget(self.messageLine)

    def _createTriggers(self):
        super()._createTriggers()
        self.checkCellAction.triggered.connect(self.checkSaveCell)
        self.createWireAction.triggered.connect(self.createWireClick)
        self.createInstAction.triggered.connect(self.createInstClick)
        self.createPinAction.triggered.connect(self.createPinClick)
        self.createSymbolAction.triggered.connect(self.createSymbolClick)
        self.copyAction.triggered.connect(self.copyClick)
        self.deleteAction.triggered.connect(self.deleteClick)
        self.objPropAction.triggered.connect(self.objPropClick)
        self.undoAction.triggered.connect(self.undoClick)
        self.redoAction.triggered.connect(self.redoClick)
        self.netlistAction.triggered.connect(self.createNetlistClick)
        self.rotateAction.triggered.connect(self.rotateItemClick)
        self.simulateAction.triggered.connect(self.startSimClick)
        self.goDownAction.triggered.connect(self.goDownClick)
        self.goUpAction.triggered.connect(self.goUpClick)

    def _createMenuBar(self):
        super()._createMenuBar()
        self.menuSimulation = self.editorMenuBar.addMenu("&Simulation")
        self.menuHelp = self.editorMenuBar.addMenu("&Help")
        self._addActions()

    def _addActions(self):
        super()._addActions()
        # edit menu

        self.menuEdit.addAction(self.netNameAction)

        self.propertyMenu = self.menuEdit.addMenu("Properties")
        self.propertyMenu.addAction(self.objPropAction)

        self.selectMenu = self.menuEdit.addMenu("Select")
        self.selectMenu.addAction(self.selectAllAction)
        self.selectMenu.addAction(self.deselectAllAction)

        # hierarchy submenu
        self.hierMenu = self.menuEdit.addMenu("Hierarchy")
        self.hierMenu.addAction(self.goUpAction)
        self.hierMenu.addAction(self.goDownAction)

        # create menu
        self.menuCreate.addAction(self.createInstAction)
        self.menuCreate.addAction(self.createWireAction)
        self.menuCreate.addAction(self.createBusAction)
        self.menuCreate.addAction(self.createLabelAction)
        self.menuCreate.addAction(self.createPinAction)
        self.menuCreate.addAction(self.createSymbolAction)

        # check menu
        self.menuCheck.addAction(self.viewErrorsAction)
        self.menuCheck.addAction(self.deleteErrorsAction)

        self.menuSimulation.addAction(self.netlistAction)
        self.menuSimulation.addAction(self.simulateAction)

    def _createToolBars(self):
        super()._createToolBars()
        # toolbar.addAction(self.rulerAction)
        # toolbar.addAction(self.delRulerAction)
        self.toolbar.addAction(self.objPropAction)
        self.toolbar.addAction(self.viewPropAction)

        self.schematicToolbar = QToolBar("Schematic Toolbar", self)
        self.addToolBar(self.schematicToolbar)
        self.schematicToolbar.addAction(self.createInstAction)
        self.schematicToolbar.addAction(self.createWireAction)
        self.schematicToolbar.addAction(self.createBusAction)
        self.schematicToolbar.addAction(self.createPinAction)
        self.schematicToolbar.addAction(self.createLabelAction)
        self.schematicToolbar.addAction(self.createSymbolAction)
        self.schematicToolbar.addSeparator()
        self.schematicToolbar.addAction(self.viewCheckAction)

    def _schematicActions(self):
        self.centralW.scene.itemContextMenu.addAction(self.copyAction)
        self.centralW.scene.itemContextMenu.addAction(self.moveAction)
        self.centralW.scene.itemContextMenu.addAction(self.rotateAction)
        self.centralW.scene.itemContextMenu.addAction(self.deleteAction)
        self.centralW.scene.itemContextMenu.addAction(self.objPropAction)
        self.centralW.scene.itemContextMenu.addAction(self.goDownAction)
        if self.parentView is not None:
            self.centralW.scene.itemContextMenu.addAction(self.goUpAction)

    def _createShortcuts(self):
        super()._createShortcuts()
        self.createInstAction.setShortcut(Qt.Key_I)
        self.createWireAction.setShortcut(Qt.Key_W)
        self.createPinAction.setShortcut(Qt.Key_P)

    def createWireClick(self, s):
        self.centralW.scene.drawWire = True

    def deleteClick(self, s):
        self.centralW.scene.deleteSelectedItems()

    def createInstClick(self, s):
        revEDAPathObj = pathlib.Path(__file__)
        revEDADirObj = revEDAPathObj.parent
        if self.symbolChooser is None:
            self.symbolChooser = symbolChooser(self,
                                               self.centralW.scene)  # create the library browser
            self.symbolChooser.show()
        else:
            self.symbolChooser.raise_()

    def createPinClick(self, s):
        createPinDlg = pdlg.createSchematicPinDialog(self)
        if createPinDlg.exec() == QDialog.Accepted:
            self.centralW.scene.pinName = createPinDlg.pinName.text()
            self.centralW.scene.pinType = createPinDlg.pinType.currentText()
            self.centralW.scene.pinDir = createPinDlg.pinDir.currentText()
            self.centralW.scene.drawPin = True

    def createSymbolClick(self, s):
        self.centralW.scene.createSymbol()

    def undoClick(self, s):
        self.centralW.scene.undoStack.undo()

    def redoClick(self, s):
        self.centralW.scene.undoStack.redo()

    def objPropClick(self, s):
        self.centralW.scene.viewObjProperties()

    def copyClick(self, s):
        self.centralW.scene.copySelectedItems()

    def rotateItemClick(self, s):
        self.centralW.scene.rotateItem = True
        self.centralW.scene.itemSelect = False

    def startSimClick(self, s):
        simguiw = revedasim.simGUImainWindow(self)
        simguiw.show()

    def checkSaveCell(self):
        self.centralW.scene.saveSchematicCell(self.file)

    def loadSchematic(self):
        self.centralW.scene.loadSchematicCell(self.file)

    def closeEvent(self, event):
        self.centralW.scene.saveSchematicCell(self.file)
        self.libraryView.openViews.pop(
            f"{self.file.parent.parent.stem}_{self.file.parent.stem}_schematic")
        event.accept()

    def createNetlistClick(self, s):
        netlistExportDialogue = pdlg.netlistExportDialogue()
        if hasattr(self, "netlistDir"):
            netlistExportDialogue.netlistDirEdit.setText(self.netlistDir)
        if netlistExportDialogue.exec() == QDialog.Accepted:
            netlistDir = netlistExportDialogue.netlistDirEdit.text()
            netlistFile = pathlib.Path(netlistDir).joinpath(
                f'{self.cellName}_schematic').with_suffix(".cir")
        self.centralW.scene.createNetlist(netlistFile, True)

    def goDownClick(self, s):
        self.centralW.scene.goDownHier()

    def goUpClick(self, s):
        self.centralW.scene.goUpHier()


class symbolEditor(editorWindow):
    def __init__(self, filePath: pathlib.Path, libraryDict: dict, libraryView):
        super().__init__(filePath, libraryDict, libraryView)
        self.setWindowTitle(f"Symbol Editor - {self.cellName}")
        self._symbolActions()

    def init_UI(self):
        self.resize(1600, 800)
        self._createMenuBar()
        self._createToolBars()
        # create container to position all widgets
        self.centralW = symbolContainer(self)
        self.setCentralWidget(self.centralW)
        self.statusLine = self.statusBar()
        self.messageLine = QLabel()  # message line
        self.statusLine.addPermanentWidget(self.messageLine)

    def _createActions(self):
        super()._createActions()

    def _createShortcuts(self):
        super()._createShortcuts()
        self.stretchAction.setShortcut(Qt.Key_M)
        self.createRectAction.setShortcut(Qt.Key_R)
        self.createLineAction.setShortcut(Qt.Key_W)
        self.createLabelAction.setShortcut(Qt.Key_L)

    def _createMenuBar(self):
        super()._createMenuBar()
        self.menuHelp = self.editorMenuBar.addMenu("&Help")
        self._addActions()

    def _createToolBars(self):  # redefine the toolbar in the editorWindow class
        super()._createToolBars()
        self.symbolToolbar = QToolBar("Symbol Toolbar", self)
        self.addToolBar(self.symbolToolbar)
        self.symbolToolbar.addAction(self.createLineAction)
        self.symbolToolbar.addAction(self.createRectAction)
        self.symbolToolbar.addAction(self.createPolyAction)
        self.symbolToolbar.addAction(self.createCircleAction)
        self.symbolToolbar.addAction(self.createArcAction)
        self.symbolToolbar.addAction(self.createLabelAction)
        self.symbolToolbar.addAction(self.createPinAction)

    def _addActions(self):
        super()._addActions()
        self.menuEdit.addAction(self.stretchAction)
        self.menuEdit.addAction(self.viewPropAction)
        self.menuCreate.addAction(self.createLineAction)
        self.menuCreate.addAction(self.createRectAction)
        self.menuCreate.addAction(self.createPolyAction)
        self.menuCreate.addAction(self.createCircleAction)
        self.menuCreate.addAction(self.createArcAction)
        self.menuCreate.addAction(self.createLabelAction)
        self.menuCreate.addAction(self.createPinAction)

    def _createTriggers(self):

        self.checkCellAction.triggered.connect(self.checkSaveCell)
        self.createLineAction.triggered.connect(self.createLineClick)
        self.createRectAction.triggered.connect(self.createRectClick)
        self.createPolyAction.triggered.connect(self.createPolyClick)
        self.createArcAction.triggered.connect(self.createArcClick)
        self.createCircleAction.triggered.connect(self.createCircleClick)
        self.createLabelAction.triggered.connect(self.createSymbolLabelDialogue)
        self.createPinAction.triggered.connect(self.createPinClick)
        self.objPropAction.triggered.connect(self.objPropClick)
        self.copyAction.triggered.connect(self.copyClick)
        self.redoAction.triggered.connect(self.redoClick)
        self.undoAction.triggered.connect(self.undoClick)
        self.rotateAction.triggered.connect(self.rotateItemClick)
        self.deleteAction.triggered.connect(self.deleteClick)
        self.stretchAction.triggered.connect(self.stretchClick)
        self.viewPropAction.triggered.connect(self.viewPropClick)
        super()._createTriggers()

    def _symbolActions(self):
        self.centralW.scene.itemContextMenu.addAction(self.copyAction)
        self.centralW.scene.itemContextMenu.addAction(self.moveAction)
        self.centralW.scene.itemContextMenu.addAction(self.rotateAction)
        self.centralW.scene.itemContextMenu.addAction(self.stretchAction)
        self.centralW.scene.itemContextMenu.addAction(self.deleteAction)
        self.centralW.scene.itemContextMenu.addAction(self.objPropAction)

    def objPropClick(self):
        self.centralW.scene.itemProperties()

    def checkSaveCell(self):
        self.centralW.scene.saveSymbolCell(self.file)

    def createRectClick(self, s):
        self.setDrawMode(False, False, False, True, False, False, False)

    def createLineClick(self, s):
        self.setDrawMode(False, False, False, False, True, False, False)

    def createPolyClick(self, s):
        pass

    def createArcClick(self, s):
        self.setDrawMode(False, False, True, False, False, False, False)

    def createCircleClick(self, s):
        self.setDrawMode(False, False, False, False, False, False, True)

    def createPinClick(self, s):
        createPinDlg = pdlg.createPinDialog(self)
        if createPinDlg.exec() == QDialog.Accepted:
            self.centralW.scene.pinName = createPinDlg.pinName.text()
            self.centralW.scene.pinType = createPinDlg.pinType.currentText()
            self.centralW.scene.pinDir = createPinDlg.pinDir.currentText()
            self.setDrawMode(True, False, False, False, False, False, False)

    def rotateItemClick(self, s):
        self.centralW.scene.rotateItem = True
        self.centralW.scene.selectItem = False
        self.messageLine.setText("Click on an item to rotate CW 90 degrees.")

    def undoClick(self, s):
        self.centralW.scene.undoStack.undo()

    def redoClick(self, s):
        self.centralW.scene.undoStack.redo()

    def deleteClick(self, s):
        self.centralW.scene.deleteSelectedItems()

    def copyClick(self, s):
        self.centralW.scene.copySelectedItems()

    def stretchClick(self, s):
        self.centralW.scene.stretchSelectedItem()

    def viewPropClick(self, s):
        self.centralW.scene.viewSymbolProperties()

    def setDrawMode(self, *args):
        """
        Sets the drawing mode in the symbol editor.
        """
        self.centralW.scene.drawPin = args[0]
        self.centralW.scene.selectItem = args[1]
        self.centralW.scene.drawArc = args[2]  # draw arc
        self.centralW.scene.drawRect = args[3]  # draw rect
        self.centralW.scene.drawLine = args[4]  # draw line
        self.centralW.scene.addLabel = args[5]
        self.centralW.scene.drawCircle = args[6]
        if hasattr(self.centralW.scene, "start"):
            del self.centralW.scene.start

    def loadSymbol(self):
        """
        symbol is loaded to the scene.
        """
        self.centralW.scene.loadSymbol(self.file)

    def createSymbolLabelDialogue(self):
        createLabelDlg = pdlg.createSymbolLabelDialog(self)
        if createLabelDlg.exec() == QDialog.Accepted:
            self.setDrawMode(False, False, False, False, False, True, False)
            # directly setting scene class attributes here to pass the information.
            self.centralW.scene.labelDefinition = createLabelDlg.labelDefinition.text()
            self.centralW.scene.labelHeight = (
                createLabelDlg.labelHeightEdit.text().strip())
            self.centralW.scene.labelAlignment = (
                createLabelDlg.labelAlignCombo.currentText())
            self.centralW.scene.labelOrient = (
                createLabelDlg.labelOrientCombo.currentText())
            self.centralW.scene.labelUse = createLabelDlg.labelUseCombo.currentText()
            if createLabelDlg.labelVisiCombo.currentText() == "Yes":
                self.centralW.scene.labelOpaque = True
            else:
                self.centralW.scene.labelOpaque = False
            self.centralW.scene.labelType = "Normal"  # default button
            if createLabelDlg.normalType.isChecked():
                self.centralW.scene.labelType = "Normal"
            elif createLabelDlg.NLPType.isChecked():
                self.centralW.scene.labelType = "NLPLabel"
            elif createLabelDlg.pyLType.isChecked():
                self.centralW.scene.labelType = "PyLabel"

    def closeEvent(self, event):
        """
        Closes the application.
        """
        self.centralW.scene.saveSymbolCell(self.file)
        self.libraryView.openViews.pop(
            f"{self.file.parent.parent.stem}_{self.file.parent.stem}_symbol")
        event.accept()


class displayConfigDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Display Options")
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.vLayout = QVBoxLayout()
        fLayout = QFormLayout()
        self.majorGridEntry = QLineEdit()
        fLayout.addRow("Major Grid:", self.majorGridEntry)
        if self.parent.centralW.scene.gridMajor:
            self.majorGridEntry.setText(str(self.parent.centralW.scene.gridMajor))
        else:
            self.majorGridEntry.setText("10")
        self.vLayout.addLayout(fLayout)
        self.vLayout.addStretch(1)
        self.vLayout.addWidget(self.buttonBox)
        self.setLayout(self.vLayout)
        self.show()


class symbolContainer(QWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.parent = parent
        self.init_UI()

    def init_UI(self):
        self.scene = symbol_scene(self)
        self.view = symbol_view(self.scene, self)

        # layout statements, using a grid layout
        gLayout = QGridLayout()
        gLayout.setSpacing(10)
        gLayout.addWidget(self.view, 0, 0)
        # ratio of first column to second column is 5
        gLayout.setColumnStretch(0, 5)
        gLayout.setRowStretch(0, 6)
        self.setLayout(gLayout)


class schematicContainer(QWidget):
    def __init__(self, parent: schematicEditor):
        super().__init__(parent=parent)
        assert isinstance(parent, schematicEditor)
        self.parent = parent
        self.scene = schematic_scene(self)
        self.view = schematic_view(self.scene, self)
        self.init_UI()

    def init_UI(self):
        # layout statements, using a grid layout
        gLayout = QGridLayout()
        gLayout.setSpacing(10)
        gLayout.addWidget(self.view, 0, 0)
        # ratio of first column to second column is 5
        gLayout.setColumnStretch(0, 5)
        gLayout.setRowStretch(0, 6)
        self.setLayout(gLayout)


class editor_scene(QGraphicsScene):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.gridMajor = 10
        self.gridTuple = (self.gridMajor, self.gridMajor)
        self.selectedItems = None  # selected item
        self.defineSceneLayers()
        self.setPens()
        self.undoStack = QUndoStack()
        self.changeOrigin = False
        self.origin = QPoint(0, 0)
        self.cellName = self.parent.parent.file.parent.stem
        self.libraryDict = self.parent.parent.libraryDict
        self.rotateItem = False
        self.itemContextMenu = QMenu()
        self.appMainW = self.parent.parent.libraryView.parent.parent.parent
        self.logger = self.appMainW.logger

    def setPens(self):
        self.wirePen = QPen(self.wireLayer.color, 2)
        self.wirePen.setCosmetic(True)
        self.symbolPen = QPen(self.symbolLayer.color, 3)
        self.symbolPen.setCosmetic(True)
        self.symbolPen.setCosmetic(True)
        self.selectedWirePen = QPen(self.selectedWireLayer.color, 2)
        self.pinPen = QPen(self.pinLayer.color, 2)
        self.labelPen = QPen(self.labelLayer.color, 1)

    def defineSceneLayers(self):
        self.wireLayer = cel.layer(name="wireLayer", color=QColor("cyan"), z=1,
                                   visible=True)
        self.symbolLayer = cel.layer(name="symbolLayer", color=QColor("green"), z=1,
                                     visible=True)
        self.guideLineLayer = cel.layer(name="guideLineLayer", color=QColor("white"), z=1,
                                        visible=True)
        self.selectedWireLayer = cel.layer(name="selectedWireLayer", color=QColor("red"),
                                           z=1, visible=True)
        self.pinLayer = cel.layer(name="pinLayer", color=QColor("red"), z=2, visible=True)
        self.labelLayer = cel.layer(name="labelLayer", color=QColor("yellow"), z=3,
                                    visible=True)

    def snapGrid(self, number, base):
        return base * int(round(number / base))

    def snap2Grid(self, point: QPoint, gridTuple: tuple[int, int]):
        """
        snap point to grid. Divides and multiplies by grid size.
        """
        return QPoint(gridTuple[0] * int(round(point.x() / gridTuple[0])),
                      gridTuple[1] * int(round(point.y() / gridTuple[1])), )

    def rotateSelectedItems(self, point: QPoint):
        for item in self.selectedItems:
            rotationOriginPoint = item.mapFromScene(point)
            item.setTransformOriginPoint(rotationOriginPoint)
            item.angle += 90
            item.setRotation(item.angle)
            undoCommand = us.undoRotateShape(self, item, item.angle)
            self.undoStack.push(undoCommand)
        self.rotateItem = False
        self.itemSelect = True


class symbol_scene(editor_scene):
    """
    Scene for Symbol editor.
    """

    def __init__(self, parent):
        super().__init__(parent)
        # drawing switches
        self.resetSceneMode()  # reset to select mode
        # pen definitions
        self.setPens()
        self.draftPen = QPen(self.guideLineLayer.color, 1)
        self.drawPin = False
        self.itemSelect = True
        self.drawArc = False  # draw arc
        self.drawRect = False
        self.drawLine = False
        self.addLabel = False
        self.drawCircle = False
        self.drawMode = (
                self.drawLine or self.drawArc or self.drawRect or self.drawCircle)
        self.symbolShapes = ["line", "arc", "rect", "circle", "pin", "label"]
        self.changeOrigin = False
        # some default attributes
        self.pinName = ""
        self.pinType = shp.pin.pinTypes[0]
        self.pinDir = shp.pin.pinDirs[0]
        self.labelDefinition = ""
        self.labelType = shp.label.labelTypes[0]
        self.labelOrient = shp.label.labelOrients[0]
        self.labelAlignment = shp.label.labelAlignments[0]
        self.labelUse = shp.label.labelUses[0]
        self.labelVisible = False
        self.labelHeight = "12"
        self.labelOpaque = True

    def mousePressEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(mouse_event)
        if mouse_event.button() == Qt.LeftButton:
            self.start = self.snap2Grid(mouse_event.scenePos().toPoint(), self.gridTuple)
            if self.changeOrigin:  # change origin of the symbol
                self.origin = self.start
            if self.itemSelect:
                self.parent.parent.messageLine.setText("Select an item")
                #     # find the view rectangle every time mouse is pressed.
                self.viewRect = self.parent.view.mapToScene(
                    self.parent.view.viewport().rect()).boundingRect()
                itemsAtMousePress = self.items(mouse_event.scenePos())
                if itemsAtMousePress:
                    # normally only one item is selected
                    self.selectedItems = [item for item in itemsAtMousePress if
                                          item.isSelected()]
                    self.parent.parent.messageLine.setText("Item selected")
                else:
                    self.selectedItems = None
                    self.parent.parent.messageLine.setText("Nothing selected")
            if self.drawPin:
                if hasattr(self, "draftPin"):
                    self.removeItem(self.draftPin)
                self.draftPin = shp.pin(self.start, self.draftPen, "", "Input", "Signal",
                                        self.gridTuple, )
                self.addItem(self.draftPin)
                self.draftPin.setSelected(True)
            if self.addLabel:
                if hasattr(self, "draftLabel"):
                    self.removeItem(self.draftLabel)
                self.draftLabel = shp.label(self.start, self.draftPen, "12",
                                            self.gridTuple, )
                self.addItem(self.draftLabel)
                self.draftLabel.setSelected(True)
            if self.rotateItem:
                if self.selectedItems:
                    self.rotateSelectedItems(self.start)

    def mouseMoveEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(mouse_event)
        #
        self.current = self.snap2Grid(mouse_event.scenePos().toPoint(), self.gridTuple)
        modifiers = QGuiApplication.keyboardModifiers()
        if mouse_event.buttons() == Qt.LeftButton:
            if hasattr(self, "draftItem"):
                self.removeItem(self.draftItem)
                del self.draftItem
            if self.drawLine and hasattr(self, "start"):
                self.parent.parent.messageLine.setText("Line Mode")
                self.draftItem = shp.line(self.start, self.current, self.draftPen,
                                          self.gridTuple)
                self.addItem(self.draftItem)
            if self.drawRect and hasattr(self, "start"):
                self.draftItem = shp.rectangle(self.start, self.current, self.draftPen,
                                               self.gridTuple)
                self.addItem(self.draftItem)
            if self.drawCircle and hasattr(self, "start"):
                xlen = abs(self.current.x() - self.start.x())
                ylen = abs(self.current.y() - self.start.y())
                length = math.sqrt(xlen ** 2 + ylen ** 2)
                self.draftItem = QGraphicsEllipseItem(
                    QRectF(self.start - QPoint(int(length), int(length)),
                           self.start + QPoint(int(length), int(length)), ))
                self.draftItem.setPen(self.draftPen)
                self.addItem(self.draftItem)
            # if self.drawPin and hasattr(self, "draftPin"):  # there is a pin draft
            #     self.draftPin.setSelected(True)
            # if self.addLabel and hasattr(self, "draftLabel"):
            #     self.draftLabel.setSelected(True)
            if self.itemSelect:
                if modifiers == Qt.ShiftModifier:
                    self.draftItem = QGraphicsRectItem(
                        QRect.span(self.start, self.current))
                    self.draftItem.setPen(self.draftPen)
                    self.addItem(self.draftItem)
                    self.parent.parent.messageLine.setText("Select an Area")

        self.parent.parent.statusLine.showMessage(
            "Cursor Position: " + str(self.current.toTuple()))

    def mouseReleaseEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:

        self.current = self.snap2Grid(mouse_event.scenePos(), self.gridTuple)
        if mouse_event.button() == Qt.LeftButton:
            if (self.itemSelect and hasattr(self, "draftItem") and isinstance(
                    self.draftItem, QGraphicsRectItem)):
                self.selectedItems = [item for item in self.items(self.draftItem.rect(),
                                                                  mode=Qt.IntersectsItemBoundingRect)]
                for item in self.selectedItems:
                    item.setSelected(True)
            if self.drawLine and hasattr(self, "start"):
                self.lineDraw(self.start, self.current, self.symbolPen, self.gridTuple)
                self.drawLine = False
            if self.drawRect and hasattr(self, "start"):
                self.rectDraw(self.start, self.current, self.symbolPen, self.gridTuple)
                self.drawRect = False
            if self.drawCircle and hasattr(self, "start"):
                self.circleDraw(self.start, self.current, self.symbolPen, self.gridTuple)
                self.drawCircle = False
            if self.drawPin and hasattr(self, "draftPin"):
                self.pinDraw(self.current, self.pinPen, self.pinName, self.pinDir,
                             self.pinType, self.gridTuple, )  # draw pin
                self.drawPin = False
            if self.addLabel and hasattr(self, "draftLabel"):
                self.labelDraw(self.current, self.labelPen, self.labelDefinition,
                               self.gridTuple, self.labelType, self.labelHeight,
                               self.labelAlignment, self.labelOrient,
                               self.labelUse, )  # draw label
                self.addLabel = False
            if hasattr(self, "draftItem"):
                self.removeItem(self.draftItem)
                del self.draftItem
            elif hasattr(self, "draftPin"):
                self.removeItem(self.draftPin)
                del self.draftPin
            elif hasattr(self, "draftLabel"):
                self.removeItem(self.draftLabel)
                del self.draftLabel
            if self.changeOrigin:
                self.changeOrigin = False
            self.itemSelect = True
        super().mouseReleaseEvent(mouse_event)

    def lineDraw(self, start: QPoint, current: QPoint, pen: QPen, gridTuple: tuple):
        line = shp.line(start, current, pen, gridTuple)
        self.addItem(line)
        undoCommand = us.addShapeUndo(self, line)
        self.undoStack.push(undoCommand)
        self.drawLine = False

    def rectDraw(self, start: QPoint, end: QPoint, pen: QPen, gridTuple: tuple):
        """
        Draws a rectangle on the scene
        """
        rect = shp.rectangle(start, end - QPoint(pen.width() / 2, pen.width() / 2), pen,
                             gridTuple)
        self.addItem(rect)
        undoCommand = us.addShapeUndo(self, rect)
        self.undoStack.push(undoCommand)
        self.drawRect = False

    def circleDraw(self, start: QPoint, end: QPoint, pen: QPen, gridTuple: tuple):
        """
        Draws a circle on the scene
        """
        snappedEnd = self.snap2Grid(end, gridTuple)
        circle = shp.circle(start, snappedEnd, pen, gridTuple)
        self.addItem(circle)
        undoCommand = us.addShapeUndo(self, circle)
        self.undoStack.push(undoCommand)
        self.drawCircle = False

    def pinDraw(self, current, pen: QPen, pinName: str, pinDir, pinType,
                gridTuple: tuple):
        pin = shp.pin(current, pen, pinName, pinDir, pinType, gridTuple)
        self.addItem(pin)
        undoCommand = us.addShapeUndo(self, pin)
        self.undoStack.push(undoCommand)
        self.drawPin = False

    def labelDraw(self, current, pen: QPen, labelDefinition, gridTuple, labelType,
                  labelHeight, labelAlignment, labelOrient, labelUse, ):
        label = shp.label(current, pen, labelDefinition, gridTuple, labelType,
                          labelHeight, labelAlignment, labelOrient, labelUse, )
        label.labelVisible = self.labelOpaque
        label.setLabelName()  # set the name
        label.setOpacity(1)
        self.addItem(label)
        undoCommand = us.addShapeUndo(self, label)
        self.undoStack.push(undoCommand)
        self.addLabel = False

    def keyPressEvent(self, key_event):
        if key_event.key() == Qt.Key_Escape:
            self.resetSceneMode()
        elif key_event.key() == Qt.Key_C:
            self.copySelectedItems()
        # elif key_event.key() == Qt.Key_Up:
        #     selectedItemsCount = len(self.itemsAtMousePress)
        #     if self.selectCount == selectedItemsCount:
        #         self.selectCount = 0
        #         self.changeSelection(self.selectCount)
        #         self.selectCount += 1
        #     elif self.selectCount < selectedItemsCount:
        #         self.changeSelection(self.selectCount)
        #         self.selectCount += 1

        super().keyPressEvent(key_event)

    # def changeSelection(self, i):
    #     """
    #     Change the selected item.
    #     """
    #     self.selectedItem.setSelected(False)
    #     self.selectedItem = self.itemsAtMousePress[i]
    #     self.selectedItem.setSelected(True)

    def resetSceneMode(self):
        """
        Reset the scene mode to default. Select mode is set to True.
        """
        self.drawItem = False  # flag to indicate if an item is being drawn
        self.drawLine = False  # flag to indicate if a line is being drawn
        self.drawArc = False  # flag to indicate if an arc is being drawn
        self.drawPin = False  # flag to indicate if a pin is being drawn
        self.drawRect = False  # flag to indicate if a rectangle is being drawn
        self.addLabel = False  # flag to indicate if a label is being drawn
        self.selectCount = 0  # index of item selected
        self.selectedItems = None
        if hasattr(self, "draftItem"):
            self.removeItem(self.draftItem)
        self.itemSelect = True

    def deleteSelectedItems(self):
        for item in self.selectedItems:
            self.removeItem(item)
        del self.selectedItems
        self.update()
        self.itemSelect = True

    def copySelectedItems(self):
        if hasattr(self, "selectedItems"):
            for item in self.selectedItems:
                selectedItemJson = json.dumps(item, cls=se.symbolEncoder)
                itemCopyDict = json.loads(selectedItemJson)
                shape = lj.createSymbolItems(itemCopyDict, self.gridTuple)
                self.addItem(shape)
                undoCommand = us.addShapeUndo(self, shape)
                self.undoStack.push(undoCommand)
                # shift position by one grid unit to right and down
                shape.setPos(QPoint(item.pos().x() + 2 * self.gridTuple[0],
                                    item.pos().y() + 2 * self.gridTuple[1], ))

    def itemProperties(self):
        '''
        When item properties is queried.
        '''
        for item in self.selectedItems:
            if isinstance(item, shp.rectangle):
                self.queryDlg = pdlg.rectPropertyDialog(self.parent.parent, item)
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updateRectangleShape(item)
            if isinstance(item, shp.circle):
                self.queryDlg = pdlg.circlePropertyDialog(self.parent.parent, item)
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updateCircleShape(item)
            elif isinstance(item, shp.line):
                self.queryDlg = pdlg.linePropertyDialog(self.parent.parent, item)
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updateLineShape(item)
            elif isinstance(item, shp.pin):
                self.queryDlg = pdlg.pinPropertyDialog(self.parent.parent, item)
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updatePinShape(item)
            elif isinstance(item, shp.label):
                self.queryDlg = pdlg.labelPropertyDialog(self.parent.parent, item)
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updateLabelShape(item)

            del self.queryDlg
        else:
            print("No item selected")

    def updateRectangleShape(self, item: shp.rectangle):
        location = item.scenePos().toTuple()
        newLeft = self.snapGrid(
            float(self.queryDlg.rectLeftLine.text()) - float(location[0]),
            self.gridTuple[0], )
        newTop = self.snapGrid(
            float(self.queryDlg.rectTopLine.text()) - float(location[1]),
            self.gridTuple[1], )
        newWidth = self.snapGrid(float(self.queryDlg.rectWidthLine.text()),
                                 self.gridTuple[0])
        newHeight = self.snapGrid(float(self.queryDlg.rectHeightLine.text()),
                                  self.gridTuple[1])
        undoUpdateRectangle = us.updateShapeUndo()
        us.keepOriginalShape(self, item, self.gridTuple, parent=undoUpdateRectangle)
        item.start = QPoint(newLeft, newTop)
        item.end = QPoint(newLeft + newWidth, newTop + newHeight)
        item.setLeft(newLeft)
        item.setTop(newTop)
        item.setWidth(newWidth)
        item.setHeight(newHeight)
        us.changeOriginalShape(self, item, parent=undoUpdateRectangle)
        self.undoStack.push(undoUpdateRectangle)
        self.selectedItem.update()

    def updateCircleShape(self, item: shp.circle):

        centerX = float(self.queryDlg.centerXEdit.text())
        centerY = float(self.queryDlg.centerYEdit.text())
        radius = float(self.queryDlg.radiusEdit.text())
        centerPoint = QPoint(centerX, centerY)

        item.setCentre(self.selectedItem.mapFromScene(centerPoint))
        item.setRadius(radius)

    def updateLineShape(self, item: shp.line):
        '''
        Updates line shape from dialogue entries.
        '''
        startEntry = QPoint(int(float(self.queryDlg.startXLine.text())),
                            int(float(self.queryDlg.startYLine.text())))
        item.start = item.mapFromScene(startEntry).toPoint()
        endEntry = QPoint(int(float(self.queryDlg.endXLine.text())),
                          int(float(self.queryDlg.endYLine.text())))
        item.end = item.mapFromScene(endEntry).toPoint()

    def updatePinShape(self, item: shp.pin):
        location = item.scenePos().toTuple()
        item.start = self.snap2Grid(
            QPoint(float(self.queryDlg.pinXLine.text()) - float(location[0]),
                   float(self.queryDlg.pinYLine.text()) - float(location[1]), ),
            self.gridTuple, )
        item.rect = QRect(self.selectedItem.start.x() - 5,
                          self.selectedItem.start.y() - 5, 10, 10)
        item.pinName = self.queryDlg.pinName.text()
        item.pinType = self.queryDlg.pinType.currentText()
        item.pinDir = self.queryDlg.pinDir.currentText()
        item.update()

    def updateLabelShape(self, item: shp.label):
        """
        update pin shape with new values.
        """
        location = item.scenePos().toTuple()
        item.start = self.snap2Grid(
            QPoint(float(self.queryDlg.labelXLine.text()) - float(location[0]),
                   float(self.queryDlg.labelYLine.text()) - float(location[1]), ),
            self.gridTuple, )
        item.labelDefinition = self.queryDlg.labelDefinition.text()
        item.labelHeight = self.queryDlg.labelHeightEdit.text()
        item.labelAlign = self.queryDlg.labelAlignCombo.currentText()
        item.labelOrient = self.queryDlg.labelOrientCombo.currentText()
        item.labelUse = self.queryDlg.labelUseCombo.currentText()
        if self.queryDlg.labelVisiCombo.currentText() == "Yes":
            item.labelVisible = True
        else:
            item.labelVisible = False
        if self.queryDlg.normalType.isChecked():
            item.labelType = shp.label.labelTypes[0]
        elif self.queryDlg.NLPType.isChecked():
            item.labelType = shp.label.labelTypes[1]
        elif self.queryDlg.pyLType.isChecked():
            item.labelType = shp.label.labelTypes[2]
        # set opacity to 1 so that the label is still visible on symbol editor
        item.setOpacity(1)
        item.setLabelName()
        print(item.labelName)
        item.update()

    def loadSymbol(self, file):
        self.attributeList = []
        with open(file, "r") as temp:
            try:
                items = json.load(temp)
                for item in items:
                    if item["type"] in self.symbolShapes:
                        itemShape = lj.createSymbolItems(item, self.gridTuple)
                        # items should be always visible in symbol view
                        if isinstance(itemShape, shp.label):
                            itemShape.setOpacity(1)
                        self.addItem(itemShape)
                    elif item["type"] == "attribute":
                        attr = lj.createSymbolAttribute(item)
                        self.attributeList.append(attr)

            except json.decoder.JSONDecodeError:
                print("Invalid JSON file")

    def saveSymbolCell(self, fileName):
        items = self.items(self.sceneRect())  # get items in scene rect
        if hasattr(self, 'attributeList'):
            items.extend(self.attributeList)  # add attribute list to list
        with open(fileName, "w") as f:
            try:
                json.dump(items, f, cls=se.symbolEncoder, indent=4)
            except Exception as e:
                print(e)

    def stretchSelectedItem(self):
        if self.selectedItems is not None:
            try:
                self.selectedItem.stretch = True
            except AttributeError:
                self.parent.parent.messageLine.setText("Nothing selected")

    def viewSymbolProperties(self):
        """
        View symbol properties dialog.
        """
        # copy symbol attribute list to another list by deepcopy to be safe
        attributeListCopy = copy.deepcopy(self.attributeList)
        symbolPropDialogue = pdlg.symbolLabelsDialogue(self.parent.parent, self.items(),
                                                       attributeListCopy)
        if symbolPropDialogue.exec() == QDialog.Accepted:
            for i, item in enumerate(symbolPropDialogue.labelItemList):
                # label name is not changed.
                item.labelHeight = symbolPropDialogue.labelHeightList[i].text()
                item.labelAlign = symbolPropDialogue.labelAlignmentList[i].currentText()
                item.labelOrient = symbolPropDialogue.labelOrientationList[
                    i].currentText()
                item.labelUse = symbolPropDialogue.labelUseList[i].currentText()
                item.labelType = symbolPropDialogue.labelTypeList[i].currentText()
                item.update(item.boundingRect())
            # create an empty attribute list. If the dialog is OK, the local attribute list
            # will be copied to the symbol attribute list.
            localAttributeList = []
            for i, item in enumerate(symbolPropDialogue.attributeNameList):
                if item.text().strip() != "":
                    localAttributeList.append(se.symbolAttribute(item.text(),
                                                                 symbolPropDialogue.attributeDefList[
                                                                     i].text()))
                self.attributeList = copy.deepcopy(localAttributeList)


class schematic_scene(editor_scene):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.instCounter = 0
        self.current = QPoint(0, 0)
        self.selectedItems = None
        self.itemsAtMousePress = list()
        self.itemContextMenu = QMenu()
        self.drawWire = False  # flag to add wire
        self.drawPin = False  # flag to add pin
        self.itemSelect = True  # flag to select item
        self.drawMode = (self.drawWire or self.drawPin)
        self.draftPen = QPen(self.guideLineLayer.color, 1)
        self.draftPen.setStyle(Qt.DashLine)
        self.itemCounter = 0
        self.netCounter = 0
        # self.pinLocations = self.pinLocs()  # dictionary to store pin locations
        self.schematicNets = {}  # netName: list of nets with the same name
        self.crossDots = set()  # list of cross dots
        self.draftItem = None
        self.viewRect = QRect(0, 0, 0, 0)
        self.viewportCrossDots = (
            set())  # an empty set of crossing points in the viewport
        self.sceneCrossDots = set()  # an empty set of all crossing points in the scene
        self.crossDotsMousePress = (
            set())  # a temporary set to hold the crossdots locations
        self.start = QPoint(0, 0)
        # add instance attributes
        self.addInstance = False
        self.instanceSymbolFile = None
        # pin attribute defaults
        self.pinName = ""
        self.pinType = "Signal"
        self.pinDir = "Input"
        self.parentView = None

    def mousePressEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(mouse_event)
        if mouse_event.button() == Qt.LeftButton:
            self.start = self.snap2Grid(mouse_event.scenePos().toPoint(), self.gridTuple)
            if self.itemSelect:
                self.parent.parent.messageLine.setText("Select an item")
                #     # find the view rectangle every time mouse is pressed.
                self.viewRect = self.parent.view.mapToScene(
                    self.parent.view.viewport().rect()).boundingRect()
                itemsAtMousePress = self.items(mouse_event.scenePos())
                if itemsAtMousePress:
                    # normally only one item is selected
                    self.selectedItems = [item for item in itemsAtMousePress if
                                          item.isSelected()]
                    self.parent.parent.messageLine.setText("Item selected")
                else:
                    self.selectedItems = None
                    self.parent.parent.messageLine.setText("Nothing selected")
            if self.drawPin:
                pin = self.addPin(self.start)
                self.addItem(pin)
                pin.setSelected(True)
                self.parent.parent.messageLine.setText("Pin added")
                self.drawPin = False
            if self.rotateItem:
                if self.selectedItems:
                    self.rotateSelectedItems(self.start)

    def mouseMoveEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(mouse_event)
        #
        self.current = self.snap2Grid(mouse_event.scenePos().toPoint(), self.gridTuple)
        modifiers = QGuiApplication.keyboardModifiers()
        if mouse_event.buttons() == Qt.LeftButton:
            if hasattr(self, "draftItem"):
                self.removeItem(self.draftItem)
                del self.draftItem
            if self.drawWire and hasattr(self, "start"):
                self.parent.parent.messageLine.setText("Wire Mode")
                self.draftItem = net.schematicNet(self.start, self.current, self.draftPen)
                self.addItem(self.draftItem)
            if self.itemSelect:
                if modifiers == Qt.ShiftModifier:
                    self.draftItem = QGraphicsRectItem(
                        QRect.span(self.start, self.current))
                    self.draftItem.setPen(self.draftPen)
                    self.addItem(self.draftItem)
                    self.parent.parent.messageLine.setText("Select an Area")

        self.parent.parent.statusLine.showMessage(
            "Cursor Position: " + str(self.current.toTuple()))

    def mouseReleaseEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(mouse_event)
        self.current = self.snap2Grid(mouse_event.scenePos().toPoint(), self.gridTuple)

        if mouse_event.button() == Qt.LeftButton:
            if self.addInstance:
                instance = self.drawInstance(self.current)
                instance.setSelected(True)
                self.itemSelect = False
                self.addInstance = False
            elif hasattr(self, "draftItem") and hasattr(self, "start"):
                if self.itemSelect and isinstance(self.draftItem, QGraphicsRectItem):
                    self.selectedItems = [item for item in
                                          self.items(self.draftItem.rect(),
                                                     mode=Qt.IntersectsItemBoundingRect)
                                          if (item.childItems() or isinstance(item,
                                                                              net.schematicNet))]
                    for item in self.selectedItems:
                        item.setSelected(True)
                if self.drawWire:
                    drawnNet = self.netDraw(self.start, self.current, self.wirePen)
                    self.removeDotsInView(self.viewRect)
                    self.mergeNets(drawnNet, self.viewRect)
                    self.splitNets(self.viewRect)
                    self.findDotPoints(self.viewRect)
                    self.drawWire = False
                self.removeItem(self.draftItem)
                del self.draftItem
                del self.start

    def removeDotsInView(self, viewRect):
        dotsInView = {item for item in self.items(viewRect) if
                      isinstance(item, net.crossingDot)}
        for dot in dotsInView:
            self.removeItem(dot)
            del dot
        self.viewportCrossDots = set()

    def findDotPoints(self, viewRect):
        self.viewportCrossDots = set()  # empty the set.
        netsInView = {item for item in self.items(viewRect) if
                      isinstance(item, net.schematicNet)}
        for netItem in netsInView:
            netItemEnd = netItem.mapToScene(netItem.end)
            for netItem2 in netsInView.difference({netItem, }):
                netItem2Start = netItem.mapToScene(netItem2.start)
                if (netItem.horizontal and netItem2.horizontal) and (
                        netItemEnd == netItem2Start) or (
                        not (netItem.horizontal or netItem2.horizontal) and (
                        netItemEnd == netItem2Start)):
                    for netItem3 in netsInView.difference({netItem, }).difference(
                            {netItem2, }):
                        netItem3End = netItem3.mapToScene(netItem3.end)
                        netItem3Start = netItem3.mapToScene(netItem3.start)
                        if (netItemEnd == netItem3End) or (netItemEnd == netItem3Start):
                            cornerPoint = netItemEnd.toPoint()
                            self.viewportCrossDots.add(cornerPoint)

        for cornerPoint in self.viewportCrossDots:
            self.createCrossDot(cornerPoint, 3)

    def mergeNets(self, drawnNet, viewRect):
        # check any overlapping nets in the view
        # editing is done in the view and thus there is no need to check all nets in the scene
        horizontalNetsInView = {item for item in self.items(viewRect) if
                                (isinstance(item, net.schematicNet) and item.horizontal)}
        verticalNetsInView = {item for item in self.items(viewRect) if (
                isinstance(item, net.schematicNet) and not item.horizontal)}
        dBNetRect = drawnNet.sceneBoundingRect()
        if len(horizontalNetsInView) > 1 and drawnNet.horizontal:
            for netItem in horizontalNetsInView - {drawnNet, }:
                netItemBRect = netItem.sceneBoundingRect()
                if dBNetRect.intersects(netItemBRect):
                    mergedRect = dBNetRect.united(netItemBRect).toRect()
                    self.removeItem(netItem)  # remove the old net from the scene
                    self.removeItem(drawnNet)  # remove the drawn net from the scene
                    mergedNet = self.netDraw(
                        self.snap2Grid(mergedRect.bottomLeft(), self.gridTuple),
                        self.snap2Grid(mergedRect.bottomRight(), self.gridTuple),
                        self.wirePen, )
                    horizontalNetsInView.discard(netItem)
                    self.mergeNets(mergedNet, viewRect)
                    self.parent.parent.messageLine.setText("Merged Nets")
        elif len(verticalNetsInView) > 1 and not drawnNet.horizontal:
            for netItem in verticalNetsInView - {drawnNet, }:
                netItemBRect = netItem.sceneBoundingRect()
                if dBNetRect.intersects(netItemBRect):
                    mergedRect = dBNetRect.united(netItemBRect).toRect()
                    self.removeItem(netItem)  # remove the old net from the scene
                    self.removeItem(drawnNet)  # remove the drawn net from the scene
                    mergedNet = self.netDraw(
                        self.snap2Grid(mergedRect.bottomRight(), self.gridTuple),
                        self.snap2Grid(mergedRect.topRight(), self.gridTuple),
                        self.wirePen, )  # create a new net with the merged rectangle
                    verticalNetsInView.discard(netItem)
                    self.mergeNets(mergedNet, viewRect)
                    self.parent.parent.messageLine.setText("Net merged")

    def splitNets(self, viewRect):
        horizontalNetsInView = {item for item in self.items(viewRect) if
                                (isinstance(item, net.schematicNet) and item.horizontal)}
        verticalNetsInView = {item for item in self.items(viewRect) if (
                isinstance(item, net.schematicNet) and not item.horizontal)}
        addedNets = set()
        for hNetItem in horizontalNetsInView:
            verticalNetsInView = {item for item in self.items(viewRect) if (
                    isinstance(item, net.schematicNet) and not item.horizontal)}
            hNetBRect = hNetItem.sceneBoundingRect().toRect()
            for vNetItem in verticalNetsInView:
                vNetBRect = vNetItem.sceneBoundingRect().toRect()
                if vNetBRect.intersects(hNetBRect):
                    crossPoint = self.snap2Grid(vNetBRect.intersected(hNetBRect).center(),
                                                self.gridTuple)
                    if crossPoint != vNetItem.end and crossPoint != vNetItem.start:
                        addedNets.add(
                            (vNetItem.mapToScene(vNetItem.start).toPoint(), crossPoint))
                        addedNets.add(
                            (crossPoint, vNetItem.mapToScene(vNetItem.end).toPoint()))
                        self.removeItem(vNetItem)
                        del vNetItem
                        break
        for vNetItem in verticalNetsInView:
            horizontalNetsInView = {item for item in self.items(viewRect) if (
                    isinstance(item, net.schematicNet) and item.horizontal)}
            vNetBRect = vNetItem.sceneBoundingRect().toRect()
            for hNetItem in horizontalNetsInView:
                hNetBRect = hNetItem.sceneBoundingRect().toRect()
                if hNetBRect.intersects(vNetBRect):
                    crossPoint = self.snap2Grid(hNetBRect.intersected(vNetBRect).center(),
                                                self.gridTuple)
                    if crossPoint != hNetItem.end and crossPoint != hNetItem.start:
                        addedNets.add(
                            (hNetItem.mapToScene(hNetItem.start).toPoint(), crossPoint))
                        addedNets.add(
                            (crossPoint, hNetItem.mapToScene(hNetItem.end).toPoint()))
                        self.removeItem(hNetItem)
                        del hNetItem
                        break
        for addedNet in addedNets:
            self.netDraw(addedNet[0], addedNet[1], self.wirePen)

    def createNetlist(self, netlistFile, writeNetlist: bool):
        """
        Creates a netlist from the schematic.
        """
        with open(netlistFile, "w") as cirFile:
            cirFile.write(f'{80 * "*"}\n')
            cirFile.write('* Revolution EDA CDL Netlist\n')
            cirFile.write(f'* Library: {self.parent.parent.libName}\n')
            cirFile.write(f'* Top Cell Name: {self.parent.parent.cellName}\n')
            cirFile.write(f'* View Name: {self.parent.parent.viewName}\n')
            cirFile.write(f'* Date: {datetime.datetime.now()}\n')
            cirFile.write(f'{80 * "*"}\n')
            cirFile.write('.GLOBAL gnd!\n')
            cirFile.write('\n')
            self.recursiveNetlisting(cirFile, writeNetlist)
            cirFile.write('.END\n')

    def recursiveNetlisting(self, cirFile, writeNetlist):
        '''
        Recursively traverse all sub-circuits and netlist them.
        '''
        self.groupAllNets()
        sceneSymbolSet = self.findSceneSymbolSet()
        self.generatePinNetMap(sceneSymbolSet)
        for symbolItem in sceneSymbolSet:
            if symbolItem.attr["NLPDeviceFormat"] != "":
                line = symbolItem.createNetlistLine()
                cirFile.write(f"{line}\n")
        # create a dictionary of all symbol types in the scene.
        symbolGroupDict = self.findSceneCells(sceneSymbolSet)
        for cellName, symbolItem in symbolGroupDict.items():
            cellPath = pathlib.Path(
                self.parent.parent.libraryDict[symbolItem.libraryName].joinpath(
                    symbolItem.cellName))
            # there could be a more intelligent way finding schematic
            # cells but this should suffice for the moment.
            nlpDeviceString = symbolItem.attr["NLPDeviceFormat"]
            for circuitView in self.parent.parent.switchViewList:
                # if circuit view exists, then netlist it.
                if f"{circuitView}.json" in [p.name for p in cellPath.iterdir()]:
                    nlpDeviceLine = nlpDeviceString.split()
                    pinline = ' '  # string
                    symbolPinList = [pin.pinName for pin in symbolItem.pins.values()]
                    for item in nlpDeviceLine:
                        strippedItem = item.lstrip('[|').rstrip(':%]')
                        if strippedItem in symbolPinList:
                            pinline += f'{strippedItem} '
                    # if circuit view is not in stopView list, descend to it:
                    if not circuitView in self.parent.parent.stopViewList:
                        cirFile.write(f'.SUBCKT {cellName} {pinline} \n')
                        new_scene = schematic_scene(self.parent)
                        new_scene.loadSchematicCell(cellPath.joinpath("schematic.json"))
                        new_scene.recursiveNetlisting(cirFile, True)
                        cirFile.write(f'.ENDS {cellName} \n')

    def groupAllNets(self) -> None:
        '''
        This method starting from nets connected to pins, then named nets and unnamed
        nets, groups all the nets in the schematic.
        '''
        # all the nets in the schematic in a set to remove duplicates
        netsSceneSet = self.findSceneNetsSet()
        # create a separate set of named nets.
        # namedNetsSet = set()
        # nets connected to pins. Netlisting will start from those nets
        pinConNetsSet = set()
        # first start from schematic pins
        scenePinsSet = self.findScenePinsSet()

        for scenePin in scenePinsSet:
            for sceneNet in netsSceneSet:
                if self.checkPinNetConnect(scenePin,sceneNet):
                    if sceneNet.nameSet:
                        if sceneNet.name == scenePin.pinName:
                            pinConNetsSet.add(sceneNet)
                        else:
                            sceneNet.nameConflict = True
                            self.parent.parent.logger.error(
                                f'Net name conflict at {scenePin.pinName} of '
                                f'{scenePin.parent.instanceName}.')
                    else:
                        pinConNetsSet.add(sceneNet)
                        sceneNet.name = scenePin.pinName
                    sceneNet.update()

        # first propagate the net names to the nets connected to pins.
        # first net set is left over nets.
        notPinConnNets = self.groupNamedNets(pinConNetsSet, netsSceneSet - pinConNetsSet)

        # find all nets with nets set through net dialogue.
        namedNetsSet = set(
            [netItem for netItem in netsSceneSet - pinConNetsSet if netItem.nameSet])
        # now remove already named net set from firstNetSet
        unnamedNets = self.groupNamedNets(namedNetsSet, notPinConnNets - namedNetsSet)
        # for netItem in unnamedNets:
        #     if not netItem.nameSet:
        #         netItem.name = None  # empty all net names not set by the user
        # now start netlisting from the unnamed nets
        self.groupUnnamedNets(unnamedNets, self.netCounter)

    def generatePinNetMap(self,sceneSymbolSet):
        '''
        For symbols in sceneSymbolSet, find which pin is connected to which net
        '''
        netCounter =0
        for symbolItem in sceneSymbolSet:
            for pinName, pinItem in symbolItem.pins.items():
                pinItem.connected = False # clear connections
                # find each symbol its pin locations and save it in pinLocations
                # directory.
                # symbolItem.pinLocations[pinName] = pinItem.sceneBoundingRect()
                for netName, netItemSet in self.schematicNets.items():
                    for netItem in netItemSet:
                        if self.checkPinNetConnect(pinItem,netItem):
                            symbolItem.pinNetMap[pinName] = netName
                            pinItem.connected = True
                            print(f'{symbolItem.instanceName}, {pinItem.pinName}')
                if not pinItem.connected:
                    # # assign a default net name prefixed with d(efault).
                    # symbolItem.pinNetMap[pinName] = f'dnet{netCounter}'
                    # print(f'left unconnected:{symbolItem.pinNetMap[pinName]}')
                    # netCounter += 1
                    pass


    def findSceneCells(self, symbolSet):
        """
        This function just goes through set of symbol items in the scene and
        checks if that symbol's cell is encountered first time. If so, it adds
        it to a dictionary   cell_name:symbol
        """
        symbolGroupDict = dict()
        for symbolItem in symbolSet:
            if symbolItem.cellName not in symbolGroupDict.keys():
                symbolGroupDict[symbolItem.cellName] = symbolItem
        return symbolGroupDict

    def findSceneSymbolSet(self) -> set[shp.symbolShape]:
        '''
        Find all the symbols on the scene as a set.
        '''
        symbolSceneSet = {item for item in self.items(self.sceneRect()) if
                          isinstance(item, shp.symbolShape)}
        return symbolSceneSet

    def findSceneNetsSet(self) -> set[net.schematicNet]:
        netsSceneSet = {item for item in self.items(self.sceneRect()) if
                        isinstance(item, net.schematicNet)}
        return netsSceneSet

    def findScenePinsSet(self) -> set[shp.schematicPin]:
        pinsSceneSet = {item for item in self.items(self.sceneRect()) if
                        isinstance(item, shp.schematicPin)}
        return pinsSceneSet

    def groupNamedNets(self, namedNetsSet, unnamedNetsSet):
        """
        Groups nets with the same name.
        """
        for netItem in namedNetsSet:
            if self.schematicNets.get(netItem.name) is None:
                self.schematicNets[netItem.name] = set()
            connectedNets, unnamedNetsSet = self.traverseNets({netItem, }, unnamedNetsSet)
            self.schematicNets[netItem.name] |= connectedNets
        # These are the nets not connected to any named net
        return unnamedNetsSet

    def groupUnnamedNets(self, unnamedNetsSet:set[net.schematicNet], nameCounter:int):
        """
        Groups nets together if they are connected and assign them default names
        if they don't have a name assigned.
        """
        # select a net from the set and remove it from the set
        try:
            initialNet = unnamedNetsSet.pop()  # assign it a name, net0, net1, net2, etc.
        except KeyError:  # initialNet set is empty
            pass
        else:
            initialNet.name = "net" + str(nameCounter)
            # now go through the set and see if any of the
            # nets are connected to the initial net
            # remove them from the set and add them to the initial net's set
            self.schematicNets[initialNet.name], unnamedNetsSet = self.traverseNets(
                {initialNet, }, unnamedNetsSet)
            nameCounter += 1
            if len(unnamedNetsSet) > 1:
                self.groupUnnamedNets(unnamedNetsSet, nameCounter)
            elif len(unnamedNetsSet) == 1:
                lastNet = unnamedNetsSet.pop()
                lastNet.name = "net" + str(nameCounter)
                self.schematicNets[lastNet.name] = {lastNet}

    def traverseNets(self, connectedSet, otherNetsSet):
        """
        Start from a net and traverse the schematic to find all connected nets. If the connected net search
        is exhausted, remove those nets from the scene nets set and start again in another net until all
        the nets in the scene are exhausted.
        """
        newFoundConnectedSet = set()
        for netItem in connectedSet:
            for netItem2 in otherNetsSet:
                if self.checkConnect(netItem, netItem2):
                    if netItem2.nameSet and netItem.nameSet and netItem.name != netItem2.name:
                        self.parent.parent.messageLine.setText(
                            "Error: multiple names assigned to same net")
                        netItem2.nameConflict = True
                        netItem.nameConflict = True
                        break
                    else:
                        netItem2.name = netItem.name
                        netItem.nameConflict = False
                        netItem2.nameConflict = False
                    newFoundConnectedSet.add(netItem2)
        # keep searching if you already found a net connected to the initial net
        if len(newFoundConnectedSet) > 0:
            connectedSet.update(newFoundConnectedSet)
            otherNetsSet -= newFoundConnectedSet
            self.traverseNets(connectedSet, otherNetsSet)
        return connectedSet, otherNetsSet

    def checkPinNetConnect(self,pinItem:shp.pin,netItem:net.schematicNet):
        if pinItem.sceneBoundingRect().intersects(netItem.sceneBoundingRect()):
            return True
        else:
            return False
    def checkConnect(self, netItem, otherNetItem):
        """
        Determine if a net is connected to netItem.
        """
        netBRect = netItem.sceneBoundingRect()
        if otherNetItem is not netItem:
            otherBRect = otherNetItem.sceneBoundingRect()
            if otherBRect.contains(
                    netItem.mapToScene(netItem.start)) or otherBRect.contains(
                netItem.mapToScene(netItem.end)):
                return True
            elif netBRect.contains(
                    otherNetItem.mapToScene(otherNetItem.start)) or netBRect.contains(
                otherNetItem.mapToScene(otherNetItem.end)):
                return True
            else:
                return False

    def createCrossDot(self, center: QPoint, radius: int):
        crossDot = net.crossingDot(center, radius, self.wirePen)
        self.addItem(crossDot)
        return crossDot

    def keyPressEvent(self, key_event):
        if key_event.key() == Qt.Key_Escape:
            self.resetSceneMode()
        super().keyPressEvent(key_event)

    def resetSceneMode(self):
        self.itemSelect = True
        self.drawWire = False
        self.drawPin = False
        self.selectedItems = []
        self.parent.parent.messageLine.setText("Select Mode")

    def netDraw(self, start: QPoint, current: QPoint, pen: QPen) -> net.schematicNet:
        line = net.schematicNet(start, current, pen)
        self.addItem(line)
        undoCommand = us.addShapeUndo(self, line)
        self.undoStack.push(undoCommand)
        return line

    def addPin(self, pos: QPoint):
        pin = shp.schematicPin(pos, self.pinPen, self.pinName, self.pinDir, self.pinType,
                               self.gridTuple)
        undoCommand = us.addShapeUndo(self, pin)
        self.undoStack.push(undoCommand)
        return pin

    def drawInstance(self, pos: QPoint):
        """
        Add an instance of a symbol to the scene.
        """
        instance = self.instSymbol(self.instanceSymbolFile, pos)
        self.addItem(instance)
        undoCommand = us.addShapeUndo(self, instance)
        self.undoStack.push(undoCommand)
        return instance

    def instSymbol(self, file: pathlib.Path, pos: QPoint):
        """
        Read a symbol file and create symbolShape objects from it.
        """
        assert isinstance(file, pathlib.Path)
        self.symbolFile = file
        itemShapes = []
        itemAttributes = {}
        draftPen = QPen(self.guideLineLayer.color, 1)
        with open(self.symbolFile, "r") as temp:
            try:
                items = json.load(temp)
                for item in items:
                    if (item["type"] == "rect" or item["type"] == "line" or item[
                        "type"] == "pin" or item["type"] == "label" or item[
                        "type"] == "circle"):
                        # append recreated shapes to shapes list
                        itemShapes.append(lj.createSymbolItems(item, self.gridTuple))
                    elif item["type"] == "attribute":
                        itemAttributes[item["name"]] = item["definition"]

                # create a symbol instance passing item shapes and attributes as
                # arguments
                symbolInstance = shp.symbolShape(draftPen, self.gridTuple, itemShapes,
                                                 itemAttributes)
                symbolInstance.setPos(pos)
                # For each instance assign a counter number from the scene
                symbolInstance.counter = self.itemCounter
                symbolInstance.instanceName = f"I{symbolInstance.counter}"
                symbolInstance.libraryName = self.symbolFile.parent.parent.stem
                symbolInstance.cellName = self.symbolFile.parent.stem
                symbolInstance.viewName = "symbol"
                for item in symbolInstance.labels.values():
                    item.labelDefs()
                return symbolInstance
            except json.decoder.JSONDecodeError:
                # print("Invalid JSON file")
                self.logger.warning('Invalid JSON File')

    def deleteSelectedItems(self):
        try:
            for item in self.selectedItems:
                self.removeItem(item)
            del self.selectedItems
            self.update()
            self.itemSelect = True
        except TypeError:
            pass

    def copySelectedItems(self):
        if self.selectedItems is not None:
            for item in self.selectedItems:
                selectedItemJson = json.dumps(item, cls=se.schematicEncoder)
                itemCopyDict = json.loads(selectedItemJson)
                print(itemCopyDict)
                if isinstance(item, shp.symbolShape):
                    self.itemCounter += 1
                    itemCopyDict["name"] = f"I{self.itemCounter}"
                    itemCopyDict["labelDict"]["instName"] = ['@instName',
                                                             f"I{self.itemCounter}"]
                    shape = lj.createSchematicItems(itemCopyDict, self.libraryDict,
                                                    item.viewName, self.gridTuple)

                elif isinstance(item, net.schematicNet):
                    shape = lj.createSchematicNets(itemCopyDict)
                elif isinstance(item, shp.schematicPin):
                    shape = lj.createSchematicPins(itemCopyDict, self.gridTuple)
                self.addItem(shape)
                # shift position by one grid unit to right and down
                shape.setPos(QPoint(item.pos().x() + 4 * self.gridTuple[0],
                                    item.pos().y() + 4 * self.gridTuple[1], ))
                undoCommand = us.addShapeUndo(self, shape)
                self.undoStack.push(undoCommand)

    def saveSchematicCell(self, file: pathlib.Path):
        self.sceneR = self.sceneRect()  # get scene rect
        items = self.items(self.sceneR)  # get items in scene rect
        # only save symbol shapes
        symbolItems = self.findSceneSymbolSet()
        netItems = self.findSceneNetsSet()
        pinItems = self.findScenePinsSet()
        netlistedItems = list(symbolItems | netItems | pinItems)
        with open(file, "w") as f:
            json.dump(netlistedItems, f, cls=se.schematicEncoder, indent=4)
        if self.parent.parent.parentView is not None:
            if type(self.parentView) == schematicEditor:
                self.parent.parent.parentView.loadSchematic()
            elif type(self.parentView) == symbolEditor:
                self.parent.parent.parentView.loadSymbol()

    def loadSchematicCell(self, file: pathlib.Path):
        with open(file, "r") as temp:
            try:
                items = json.load(temp)
                for item in items:
                    if item is not None and item["type"] == "symbolShape":
                        itemShape = lj.createSchematicItems(item, self.libraryDict,
                                                            "symbol", self.gridTuple)
                        self.addItem(itemShape)
                        if itemShape.counter > self.itemCounter:
                            self.itemCounter = itemShape.counter
                    elif item is not None and item["type"] == "schematicNet":
                        netShape = lj.createSchematicNets(item)
                        self.addItem(netShape)
                    elif item is not None and item["type"] == "schematicPin":
                        pinShape = lj.createSchematicPins(item, self.gridTuple)
                        self.addItem(pinShape)

            except json.decoder.JSONDecodeError:
                print("Invalid JSON file")
        # increment item counter for next symbol
        self.itemCounter += 1
        self.findDotPoints(self.sceneRect())
        # now create a deepcopy of the scene dot locations set
        self.update()

    def viewObjProperties(self):
        """
        Display the properties of the selected object.
        """

        if self.selectedItems is not None:
            for item in self.selectedItems:
                if isinstance(item, shp.symbolShape):
                    dlg = pdlg.instanceProperties(self.parent.parent, item)
                    if dlg.exec() == QDialog.Accepted:
                        item.libraryName = dlg.libNameEdit.text().strip()
                        item.cellName = dlg.cellNameEdit.text().strip()
                        item.viewName = dlg.viewNameEdit.text().strip()
                        filePath = pathlib.Path(
                            self.libraryDict[item.libraryName].joinpath(item.cellName,
                                                                        item.viewName + ".json"))
                        item.instanceName = dlg.instNameEdit.text().strip()
                        item.angle = float(dlg.angleEdit.text().strip())
                        for label in item.labels.values():
                            if label.labelDefinition == "[@instName]":
                                label.labelValue = item.instanceName
                            elif label.labelDefinition == "[@cellName]":
                                label.labelValue = item.cellName
                        location = self.snap2Grid(
                            QPoint(float(dlg.xLocationEdit.text().strip()),
                                   float(dlg.yLocationEdit.text().strip())),
                            self.gridTuple)
                        item.setPos(location)
                        tempDoc = QTextDocument()
                        for i in range(dlg.instanceLabelsLayout.rowCount()):
                            # first create label name document with HTML annotations
                            tempDoc.setHtml(dlg.instanceLabelsLayout.itemAtPosition(i,
                                                                                    0).widget().text())
                            # now strip html annotations
                            tempLabelName = tempDoc.toPlainText().strip()
                            # check if label name is in label dictionary of item.
                            if tempLabelName in item.labels.keys():
                                item.labels[
                                    tempLabelName].labelValue = dlg.instanceLabelsLayout.itemAtPosition(
                                    i, 1).widget().text()
                                item.labels[tempLabelName].labelValueSet = True
                                visible = dlg.instanceLabelsLayout.itemAtPosition(i,
                                                                                  2).widget().currentText()
                                if visible == "True":
                                    item.labels[tempLabelName].labelVisible = True
                                else:
                                    item.labels[tempLabelName].labelVisible = False
                                item.labels[tempLabelName].labelDefs()
                        item.update()
                elif isinstance(item, net.schematicNet):
                    dlg = pdlg.netProperties(self.parent.parent, item)
                    if dlg.exec() == QDialog.Accepted:
                        item.name = dlg.netNameEdit.text().strip()
                        if item.name == "":
                            item.nameSet = False
                        else:
                            item.nameSet = True  # self.createNetlist()
                        item.update()

    def createSymbol(self):
        '''
        Create a symbol view for a schematic.
        '''
        # cellItem = self.parent.parent.viewItem.parent()
        libraryView = self.parent.parent.libraryView
        cellPath = self.parent.parent.file.parent
        cellName = self.parent.parent.cellName
        oldSymbolItem = False

        for view in cellPath.iterdir():
            if view.stem == "symbol":
                oldSymbolItem = True
                break
        if oldSymbolItem:
            dlg = pdlg.deleteCellViewDialog(cellName, "symbol", self.parent.parent)
            if dlg.exec() == QDialog.Accepted:
                self.generateSymbol()
        else:
            self.generateSymbol()

    def goDownHier(self):
        if hasattr(self, "selectedItem"):
            if isinstance(self.selectedItem, shp.symbolShape):
                dlg = pdlg.goDownHierDialogue(self.selectedItem,
                                              self.parent.parent.libraryDict, )
                if dlg.exec() == QDialog.Accepted:
                    selectedView = dlg.viewNameCB.currentText()
                    libName = self.selectedItem.libraryName
                    cellName = self.selectedItem.cellName
                    libraryView = self.parent.parent.libraryView
                    viewPath = self.parent.parent.libraryDict.get(libName).joinpath(
                        cellName).joinpath(selectedView).with_suffix('.json')

                    if selectedView == "symbol":
                        symbolWindow = symbolEditor(viewPath,
                                                    self.parent.parent.libraryDict,
                                                    self.parent.parent.libraryView)
                        symbolWindow.loadSymbol()
                        symbolWindow.parentView = self.parent.parent
                        symbolWindow.show()
                        libraryView.openViews[
                            f'{libName}_{cellName}_symbol'] = symbolWindow
                    elif selectedView == "schematic":
                        schematicWindow = schematicEditor(viewPath,
                                                          self.parent.parent.libraryDict,
                                                          self.parent.parent.libraryView)
                        schematicWindow.loadSchematic()
                        schematicWindow.parentView = self.parent.parent
                        schematicWindow.show()
                        libraryView.openViews[
                            f'{libName}_{cellName}_schematic'] = schematicWindow

    def goUpHier(self):
        print('Up baby up')

    def generateSymbol(self, *args):
        # openPath = pathlib.Path(cellItem.data(Qt.UserRole + 2))
        cellPath = self.parent.parent.file.parent
        libName = self.parent.parent.libName
        cellName = self.parent.parent.cellName
        libraryView = self.parent.parent.libraryView
        schematicPins = list(self.findScenePinsSet())

        schematicPinNames = [pinItem.pinName for pinItem in schematicPins]

        inputPins = [pinItem for pinItem in schematicPins if
                     pinItem.pinDir == shp.schematicPin.pinDirs[0]]

        outputPins = [pinItem for pinItem in schematicPins if
                      pinItem.pinDir == shp.schematicPin.pinDirs[1]]

        inoutPins = [pinItem for pinItem in schematicPins if
                     pinItem.pinDir == shp.schematicPin.pinDirs[2]]

        dlg = pdlg.symbolCreateDialog(self.parent.parent, inputPins, outputPins,
                                      inoutPins)
        if dlg.exec() == QDialog.Accepted:
            try:
                leftPinNames = list(filter(None, [pinName.strip() for pinName in
                                                  dlg.leftPinsEdit.text().split(',')]))
                rightPinNames = list(filter(None, [pinName.strip() for pinName in
                                                   dlg.rightPinsEdit.text().split(',')]))
                topPinNames = list(filter(None, [pinName.strip() for pinName in
                                                 dlg.topPinsEdit.text().split(',')]))
                bottomPinNames = list(filter(None, [pinName.strip() for pinName in
                                                    dlg.bottomPinsEdit.text().split(
                                                        ',')]))
                stubLength = int(float(dlg.stubLengthEdit.text().strip()))
                pinDistance = int(float(dlg.pinDistanceEdit.text().strip()))
            except ValueError:
                print("Enter valid value")
            else:
                rectXDim = (max(len(topPinNames), len(bottomPinNames)) + 1) * pinDistance
                rectYDim = (max(len(leftPinNames), len(rightPinNames)) + 1) * pinDistance
        symbolViewItem = scb.createCellView(libraryView, "symbol", cellPath)
        libraryDict = self.parent.parent.libraryDict
        symbolViewPath = symbolViewItem.data(Qt.UserRole + 2)
        # create symbol editor window
        symbolWindow = symbolEditor(symbolViewPath, libraryDict, libraryView)

        symbolWindow.show()
        # add window to open windows list
        libraryView.openViews[f'{libName}_{cellName}_symbol'] = symbolWindow
        symbolScene = symbolWindow.centralW.scene
        symbolScene.rectDraw(QPoint(0, 0), QPoint(rectXDim, rectYDim), self.symbolPen,
                             self.gridTuple)
        symbolScene.labelDraw(QPoint(int(0.25 * rectXDim), int(0.4 * rectYDim)),
                              self.labelPen, '[@cellName]', self.gridTuple, "NLPLabel",
                              "12", "Center", "R0", "Instance")
        symbolScene.labelDraw(QPoint(int(rectXDim), int(-0.2 * rectYDim)), self.labelPen,
                              '[@instName]', self.gridTuple, "NLPLabel", "12", "Center",
                              "R0", "Instance")
        leftPinLocs = [QPoint(-stubLength, (i + 1) * pinDistance) for i in
                       range(len(leftPinNames))]
        rightPinLocs = [QPoint(rectXDim + stubLength, (i + 1) * pinDistance) for i in
                        range(len(rightPinNames))]
        bottomPinLocs = [QPoint((i + 1) * pinDistance, rectYDim + stubLength) for i in
                         range(len(bottomPinNames))]
        topPinLocs = [QPoint((i + 1) * pinDistance, - stubLength) for i in
                      range(len(topPinNames))]
        for i in range(len(leftPinNames)):
            symbolScene.lineDraw(leftPinLocs[i], leftPinLocs[i] + QPoint(stubLength, 0),
                                 symbolScene.symbolPen, symbolScene.gridTuple)
            symbolScene.addItem(
                schematicPins[schematicPinNames.index(leftPinNames[i])].toSymbolPin(
                    leftPinLocs[i], symbolScene.pinPen, symbolScene.gridTuple))
            for i in range(len(rightPinNames)):
                symbolScene.lineDraw(rightPinLocs[i],
                                     rightPinLocs[i] + QPoint(-stubLength, 0),
                                     symbolScene.symbolPen, symbolScene.gridTuple)
                symbolScene.addItem(
                    schematicPins[schematicPinNames.index(rightPinNames[i])].toSymbolPin(
                        rightPinLocs[i], symbolScene.pinPen, symbolScene.gridTuple))
            for i in range(len(topPinNames)):
                symbolScene.lineDraw(topPinLocs[i], topPinLocs[i] + QPoint(0, stubLength),
                                     symbolScene.symbolPen, symbolScene.gridTuple)
                symbolScene.addItem(
                    schematicPins[schematicPinNames.index(topPinNames[i])].toSymbolPin(
                        topPinLocs[i], symbolScene.pinPen, symbolScene.gridTuple))
            for i in range(len(bottomPinNames)):
                symbolScene.lineDraw(bottomPinLocs[i],
                                     bottomPinLocs[i] + QPoint(0, -stubLength),
                                     symbolScene.symbolPen, symbolScene.gridTuple)
                symbolScene.addItem(
                    schematicPins[schematicPinNames.index(bottomPinNames[i])].toSymbolPin(
                        bottomPinLocs[i], symbolScene.pinPen, symbolScene.gridTuple))
            # symbol attribute generation for netlisting.
            symbolScene.attributeList = list()  # empty attribute list
            nlpPinNames = ""
            for pinName in schematicPinNames:
                nlpPinNames += f" [|{pinName}:%]"
            symbolScene.attributeList.append(se.symbolAttribute("NLPDeviceFormat",
                                                                f'X[@instName] {nlpPinNames} [@cellName]'))
            libraryView.reworkDesignLibrariesView()
            return symbolViewItem


class editor_view(QGraphicsView):
    """
    The qgraphicsview for qgraphicsscene. It is used for both schematic and layout editors.
    """

    def __init__(self, scene, parent):
        super().__init__(scene, parent)
        self.parent = parent
        self.scene = scene
        self.gridMajor = self.scene.gridMajor
        self.init_UI()

    def init_UI(self):
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        # self.setCacheMode(QGraphicsView.CacheBackground)
        self.standardCursor = QCursor(Qt.CrossCursor)
        self.setCursor(self.standardCursor)  # set cursor to standard arrow
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setMouseTracking(
            True)

    def wheelEvent(self, mouse_event):
        factor = 1.1
        if mouse_event.angleDelta().y() < 0:
            factor = 0.9
        view_pos = QPoint(int(mouse_event.globalPosition().x()),
                          int(mouse_event.globalPosition().y()))
        scene_pos = self.mapToScene(view_pos)
        self.centerOn(scene_pos)
        self.scale(factor, factor)
        delta = self.mapToScene(view_pos) - self.mapToScene(
            self.viewport().rect().center())
        self.centerOn(scene_pos - delta)
        super().wheelEvent(mouse_event)

    def snapGrid(self, number, base):
        return base * int(math.floor(number / base))

    def drawBackground(self, painter, rect):
        rectCoord = rect.getRect()
        painter.fillRect(rect, QColor("black"))
        painter.setPen(QColor("white"))
        grid_x_start = math.ceil(rectCoord[0] / self.gridMajor) * self.gridMajor
        grid_y_start = math.ceil(rectCoord[1] / self.gridMajor) * self.gridMajor
        num_x_points = math.floor(rectCoord[2] / self.gridMajor)
        num_y_points = math.floor(rectCoord[3] / self.gridMajor)
        for i in range(int(num_x_points)):  # rect width
            for j in range(int(num_y_points)):  # rect length
                painter.drawPoint(grid_x_start + i * self.gridMajor,
                                  grid_y_start + j * self.gridMajor)
        super().drawBackground(painter, rect)

    def keyPressEvent(self, key_event):
        if key_event.key() == Qt.Key_F:
            self.fitToView()
        super().keyPressEvent(key_event)

    def fitToView(self):
        viewRect = self.scene.itemsBoundingRect().marginsAdded(QMargins(40, 40, 40, 40))
        self.fitInView(viewRect, Qt.AspectRatioMode.KeepAspectRatio)
        self.show()


class symbol_view(editor_view):
    def __init__(self, scene, parent):
        self.scene = scene
        self.parent = parent
        super().__init__(self.scene, self.parent)
        self.visibleRect = QRect(0, 0, 0, 0)  # initialize to an empty rectangle


class schematic_view(editor_view):
    def __init__(self, scene, parent):
        self.scene = scene
        self.parent = parent
        super().__init__(self.scene, self.parent)
        self.visibleRect = QRect(0, 0, 0, 0)  # initialize to an empty rectangle
        self.viewItems = []
        self.netItems = []

    def mouseReleaseEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        if mouse_event.button() == Qt.LeftButton:
            if self.scene.drawWire:
                self.visibleRect = self.viewport().geometry()
                self.viewItems = [item for item in self.items(self.visibleRect,
                                                              mode=Qt.IntersectsItemShape)
                                  if isinstance(item, shp.symbolShape)]
                self.netItems = [item for item in
                                 self.items(self.visibleRect, mode=Qt.IntersectsItemShape)
                                 if isinstance(item, net.schematicNet)]
        super().mouseReleaseEvent(mouse_event)


class libraryBrowser(QMainWindow):
    def __init__(self, parent: QMainWindow) -> None:
        super().__init__()
        self.parent = parent
        self.libraryDict = self.parent.libraryDict
        self.cellViews = self.parent.cellViews
        self.setWindowTitle("Library Browser")
        self._createMenuBar()
        self._createActions()
        self._createToolBars()
        self.logger = self.parent.logger
        self.initUI()

    def initUI(self):
        self.libBrowserCont = libraryBrowserContainer(self)
        self.setCentralWidget(self.libBrowserCont)

    def _createMenuBar(self):
        self.browserMenubar = self.menuBar()
        self.browserMenubar.setNativeMenuBar(False)
        self.libraryMenu = self.browserMenubar.addMenu("&Library")

    def _createActions(self):
        openLibIcon = QIcon(":/icons/database--plus.png")
        self.openLibAction = QAction(openLibIcon, "Create/Open Lib...", self)
        self.libraryMenu.addAction(self.openLibAction)
        self.openLibAction.triggered.connect(self.openLibDialog)

        self.libraryEditorAction = QAction(openLibIcon, "Library Editor", self)
        self.libraryMenu.addAction(self.libraryEditorAction)
        self.libraryEditorAction.triggered.connect(self.libraryEditorClick)

        newLibIcon = QIcon(":/icons/database--plus.png")
        self.newLibAction = QAction(newLibIcon, "New Lib...", self)
        self.libraryMenu.addAction(self.newLibAction)
        self.newLibAction.triggered.connect(self.newLibClick)

        saveLibIcon = QIcon(":/icons/database-import.png")
        self.saveLibAction = QAction(saveLibIcon, "Save Lib...", self)
        self.libraryMenu.addAction(self.saveLibAction)

        closeLibIcon = QIcon(":/icons/database-delete.png")
        self.closeLibAction = QAction(closeLibIcon, "Close Lib...", self)
        self.libraryMenu.addAction(self.closeLibAction)

        self.libraryMenu.addSeparator()
        newCellIcon = QIcon(":/icons/document--plus.png")
        self.newCellAction = QAction(newCellIcon, "New Cell...", self)
        self.libraryMenu.addAction(self.newCellAction)

        openCellIcon = QIcon(":/icons/document--pencil.png")
        self.openCellAction = QAction(openCellIcon, "Open Cell...", self)
        self.libraryMenu.addAction(self.openCellAction)

        saveCellIcon = QIcon(":/icons/document-import.png")
        self.saveCellAction = QAction(saveCellIcon, "Save Cell", self)
        self.libraryMenu.addAction(self.saveCellAction)

        closeCellIcon = QIcon(":/icons/document--minus.png")
        closeCellAction = QAction(closeCellIcon, "Close Cell", self)
        self.libraryMenu.addAction(closeCellAction)

        deleteIcon = QIcon(":/icons/node-delete.png")
        self.deleteCellAction = QAction(deleteIcon, "Delete", self)
        self.libraryMenu.addAction(self.deleteCellAction)

    def _createToolBars(self):
        # Create tools bar called "main toolbar"
        toolbar = QToolBar("Main Toolbar", self)
        # place toolbar at top
        self.addToolBar(toolbar)
        toolbar.addAction(self.newLibAction)
        toolbar.addAction(self.openLibAction)
        toolbar.addAction(self.saveLibAction)
        toolbar.addSeparator()
        toolbar.addAction(self.newCellAction)
        toolbar.addAction(self.openCellAction)
        toolbar.addAction(self.saveCellAction)

    def openLibDialog(self):
        home_dir = str(pathlib.Path.cwd())
        libDialog = QFileDialog(self, "Create/Open Library", home_dir)
        libDialog.setFileMode(QFileDialog.Directory)
        # libDialog.Option(QFileDialog.ShowDirsOnly)
        if libDialog.exec() == QDialog.Accepted:
            self.libraryDict[libDialog.selectedFiles()[0]] = pathlib.Path(
                libDialog.selectedFiles()[0])
            self.libBrowserCont.designView.reworkDesignLibrariesView()

    def libraryEditorClick(self, s):
        pathEditDlg = libraryPathEditorDialog(self)
        # dlg.buttonBox.clicked(dlg.buttonBox.)

        if pathEditDlg.exec() == QDialog.Accepted:
            self.reworkLibraryModel(pathEditDlg)
            #  now update root libraryDict
            self.parent.libraryDict = self.libraryDict

    def newLibClick(self, s):
        # print('not implemented yet.')
        self.logger.error('Not implemented yet.')

    def reworkLibraryModel(self, dialog: QDialog):
        libFilePath = pathlib.Path.cwd().parent.joinpath("library.yaml")
        tempLibDict = {}
        for item in dialog.libraryEditRowList:
            if item.libraryNameEdit.text().strip() != "":  # check if the key is empty
                tempLibDict[item.libraryNameEdit.text()] = item.libraryPathEdit.text()
        try:
            with libFilePath.open(mode="w") as f:
                scb.writeLibDefFile(tempLibDict, libFilePath)
        except IOError:
            # print(f"Cannot save library definitions in {libFilePath}")
            self.logger.error(f"Cannot save library definitions in {libFilePath}")
        # self.parent.centralWidget.treeView.addLibrary()
        self.libraryDict = {}  # now empty the library dict
        for key, value in tempLibDict.items():
            self.libraryDict[key] = pathlib.Path(
                value)  # redefine  libraryDict with pathlib paths.
        self.libBrowserCont.designView.libraryModel.clear()
        self.libBrowserCont.designView.initModel()
        self.libBrowserCont.designView.setModel(
            self.libBrowserCont.designView.libraryModel)
        for designPath in self.libraryDict.values():  # type: Path
            self.libBrowserCont.designView.populateLibrary(designPath,
                                                           self.libBrowserCont.designView.rootItem)
        self.libBrowserCont.designView.libraryDict = self.libraryDict

    def closeEvent(self, event: QCloseEvent) -> None:
        self.parent.libraryBrowser = None
        event.accept()


class libraryBrowserContainer(QWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.parent = parent
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.designView = designLibrariesView(self)
        self.layout.addWidget(self.designView)
        self.setLayout(self.layout)


class designLibrariesView(QTreeView):
    def __init__(self, parent):
        super().__init__(parent=parent)  # QTreeView
        self.parent = parent  # type: QMainWindow
        self.libraryDict = self.parent.parent.libraryDict  # type: dict
        self.cellViews = self.parent.parent.cellViews  # type: list
        self.openViews = {}  # type: dict
        self.viewCounter = 0
        self.mainW = self.parent.parent.parent
        self.logger = self.mainW.logger
        self.init_UI()

    def init_UI(self):
        self.setSortingEnabled(True)
        self.setUniformRowHeights(True)
        self.expandAll()
        self.initModel()
        # iterate design library directories. Designpath is the path of library
        # obtained from libraryDict
        for designPath in self.libraryDict.values():  # type: Path
            self.populateLibrary(designPath, self.rootItem)
        self.setModel(self.libraryModel)

    def initModel(self):
        # library model is based on qstandarditemmodel
        self.libraryModel = QStandardItemModel()
        self.libraryModel.setHorizontalHeaderLabels(["Libraries"])
        self.rootItem = self.libraryModel.invisibleRootItem()

    # populate the library model
    def populateLibrary(self, designPath, parentItem):  # designPath: Path
        if designPath.is_dir():
            libraryItem = self.addLibraryToModel(designPath, parentItem)
            cellList = [str(cell.name) for cell in designPath.iterdir() if cell.is_dir()]
            for cell in cellList:  # type: str
                cellItem = self.addCellToModel(designPath.joinpath(cell), libraryItem)
                viewList = [str(view) for view in designPath.joinpath(cell).iterdir() if
                            view.suffix == ".json" and str(view.stem) in self.cellViews]
                if len(viewList) >= 0:
                    for view in viewList:
                        self.addViewToModel(designPath.joinpath(cell, view), cellItem)

    # library related methods

    def addLibraryToModel(self, designPath, parentItem):
        libraryEntry = scb.libraryItem(designPath)
        parentItem.appendRow(libraryEntry)
        return libraryEntry

    def removeLibrary(self):
        shutil.rmtree(self.selectedItem.data(Qt.UserRole + 2))
        self.libraryModel.removeRow(self.selectedItem.row())

    def saveLibAs(self):
        pass

    def renameLib(self):
        pass

    # cell related methods
    def addCellToModel(self, cellPath, parentItem):
        cellEntry = scb.cellItem(cellPath)
        parentItem.appendRow(cellEntry)
        return cellEntry

    def createCell(self):
        dlg = createCellDialog(self, self.libraryModel, self.selectedItem)
        if dlg.exec() == QDialog.Accepted:
            scb.createCell(self, self.libraryModel, self.selectedItem,
                           dlg.nameEdit.text())
            self.reworkDesignLibrariesView()

    def copyCell(self):
        dlg = copyCellDialog(self, self.libraryModel, self.selectedItem)

        if dlg.exec() == QDialog.Accepted:
            scb.copyCell(self, dlg.model, dlg.cellItem, dlg.copyName.text(),
                         dlg.selectedLibPath)

    def renameCell(self):
        dlg = renameCellDialog(self, self.selectedItem)
        if dlg.exec() == QDialog.Accepted:
            scb.renameCell(self, dlg.cellItem, dlg.nameEdit.text())

    def deleteCell(self):
        try:
            shutil.rmtree(self.selectedItem.data(Qt.UserRole + 2))
            self.selectedItem.parent().removeRow(self.selectedItem.row())
        except OSError as e:
            # print(f"Error:{e.strerror}")
            self.logger.warning(f"Error:{e.strerror}")

    # cellview related methods

    def addViewToModel(self, viewPath, parentItem):
        viewEntry = scb.viewItem(viewPath)
        parentItem.appendRow(viewEntry)
        return viewEntry

    def createCellView(self):
        assert isinstance(self.selectedItem, scb.cellItem)
        dlg = createCellViewDialog(self, self.libraryModel,
                                   self.selectedItem)  # type: createCellViewDialog
        if dlg.exec() == QDialog.Accepted:
            cellPath = self.selectedItem.data(Qt.UserRole + 2)
            newViewEntry = scb.createCellView(self, dlg.nameEdit.text(), cellPath)
            dlg.cellItem.appendRow(newViewEntry)
            self.reworkDesignLibrariesView()

    def openView(self):
        openPath = pathlib.Path(self.selectedItem.data(Qt.UserRole + 2))
        libName = openPath.parent.parent.stem
        cellName = openPath.parent.stem
        if (
                self.selectedItem.text() == "schematic" and not f'{libName}_{cellName}_schematic' in self.openViews):
            schematicWindow = schematicEditor(openPath, self.libraryDict, self, )
            schematicWindow.loadSchematic()
            schematicWindow.show()
            self.openViews[f'{libName}_{cellName}_schematic'] = schematicWindow
        elif (
                self.selectedItem.text() == "symbol" and not f'{libName}_{cellName}_symbol' in self.openViews):
            # create a symbol editor window and load the symbol JSON file.
            symbolWindow = symbolEditor(openPath, self.libraryDict, self)
            symbolWindow.loadSymbol()
            symbolWindow.show()
            self.openViews[f'{libName}_{cellName}_symbol'] = symbolWindow
        elif f'{libName}_{cellName}_symbol' in self.openViews:
            self.openViews[f'{libName}_{cellName}_symbol'].raise_()
        elif f'{libName}_{cellName}_schematic' in self.openViews:
            self.openViews[f'{libName}_{cellName}_schematic'].raise_()

    def copyView(self):
        dlg = copyViewDialog(self, self.libraryModel, self.selectedItem)
        if dlg.exec() == QDialog.Accepted:
            if self.selectedItem.data(Qt.UserRole + 1) == "view":
                viewPath = self.selectedItem.data(Qt.UserRole + 2)
                newViewPath = dlg.selectedLibPath.joinpath(dlg.selectedCell,
                                                           dlg.selectedView + ".json")
                if not newViewPath.exists():
                    try:
                        newViewPath.parent.mkdir(parents=True)
                    except FileExistsError:
                        pass
                    shutil.copy(viewPath, newViewPath)
                else:
                    QMessageBox.warning(self, "Error", "View already exits.")
                    self.logger.warning("View already exists.")
                    self.copyView()  # try again

    def renameView(self):
        pass

    def deleteView(self):
        try:
            self.selectedItem.data(Qt.UserRole + 2).unlink()
            self.selectedItem.parent().removeRow(self.selectedItem.row())
        except OSError as e:
            # print(f"Error:{e.strerror}")
            self.logger.warning(f"Error:{e.strerror}")

    def reworkDesignLibrariesView(self):
        self.libraryModel.clear()
        self.initModel()
        self.setModel(self.libraryModel)
        for designPath in self.libraryDict.values():  # type: Path
            self.populateLibrary(designPath, self.rootItem)

    # context menu
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        try:
            index = self.selectedIndexes()[0]
        except IndexError:
            pass
        try:
            self.selectedItem = self.libraryModel.itemFromIndex(index)
            if self.selectedItem.data(Qt.UserRole + 1) == "library":
                menu.addAction("Save Library As...", self.saveLibAs)
                menu.addAction("Rename Library", self.renameLib)
                menu.addAction("Remove Library", self.removeLibrary)
                menu.addAction("Create Cell", self.createCell)
            elif self.selectedItem.data(Qt.UserRole + 1) == "cell":
                menu.addAction(
                    QAction("Create CellView...", self, triggered=self.createCellView))
                menu.addAction(QAction("Copy Cell...", self, triggered=self.copyCell))
                menu.addAction(QAction("Rename Cell...", self, triggered=self.renameCell))
                menu.addAction(QAction("Delete Cell...", self, triggered=self.deleteCell))
            elif self.selectedItem.data(Qt.UserRole + 1) == "view":
                menu.addAction(QAction("Open View", self, triggered=self.openView))
                menu.addAction(QAction("Copy View...", self, triggered=self.copyView))
                menu.addAction(QAction("Rename View...", self, triggered=self.renameView))
                menu.addAction(QAction("Delete View...", self, triggered=self.deleteView))
            menu.exec(event.globalPos())
        except UnboundLocalError:
            pass


class createCellDialog(QDialog):
    def __init__(self, parent, libraryModel, selectedItem):
        super().__init__(parent)
        self.parent = parent
        self.libraryModel = libraryModel
        self.selectedItem = selectedItem
        self.init_UI()

    def init_UI(self):
        self.setWindowTitle("Create Cell")
        layout = QFormLayout()
        self.nameEdit = QLineEdit()
        self.nameEdit.setPlaceholderText("Enter Cell Name")
        layout.addRow("Cell Name:", self.nameEdit)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addRow(self.buttonBox)
        self.setLayout(layout)


class createCellViewDialog(QDialog):
    def __init__(self, parent, model, cellItem):
        super().__init__(parent=parent)
        self.parent = parent
        self.model = model
        self.cellItem = cellItem
        self.cellPath = self.cellItem.data(Qt.UserRole + 2)
        self.init_UI()

    def init_UI(self):
        self.setWindowTitle("Create CellView")
        layout = QFormLayout()
        layout.setSpacing(10)
        self.viewComboBox = QComboBox()
        self.viewComboBox.addItems(self.parent.cellViews)
        layout.addRow("Select View:", self.viewComboBox)
        self.nameEdit = QLineEdit()
        self.nameEdit.setPlaceholderText("CellView Name")
        self.nameEdit.setFixedWidth(200)
        layout.addRow(QLabel("View Name:"), self.nameEdit)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addRow(self.buttonBox)
        self.setLayout(layout)


class renameCellDialog(QDialog):
    def __init__(self, parent, cellItem):
        super().__init__(parent=parent)
        self.parent = parent
        self.cellItem = cellItem

        self.init_UI()

    def init_UI(self):
        self.setWindowTitle("Rename Cell")
        layout = QFormLayout()
        layout.setSpacing(10)
        self.nameEdit = QLineEdit()
        self.nameEdit.setPlaceholderText("Cell Name")
        self.nameEdit.setFixedWidth(200)
        layout.addRow(QLabel("Cell Name:"), self.nameEdit)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addRow(self.buttonBox)
        self.setLayout(layout)


class copyCellDialog(QDialog):
    def __init__(self, parent, model, cellItem):
        super().__init__(parent=parent)
        self.parent = parent
        self.model = model
        self.cellItem = cellItem

        # self.index = 0
        self.init_UI()

    def init_UI(self):
        self.setWindowTitle("Copy Cell")
        layout = QFormLayout()
        layout.setSpacing(10)
        self.libraryComboBox = QComboBox()
        self.libraryComboBox.setModel(self.model)
        self.libraryComboBox.setModelColumn(0)
        self.libraryComboBox.setCurrentIndex(0)
        self.selectedLibPath = self.libraryComboBox.itemData(0, Qt.UserRole + 2)
        self.libraryComboBox.currentTextChanged.connect(self.selectLibrary)
        layout.addRow(QLabel("Library:"), self.libraryComboBox)
        self.copyName = QLineEdit()
        self.copyName.setPlaceholderText("Enter Cell Name")
        self.copyName.setFixedWidth(130)
        layout.addRow(QLabel("Cell Name:"), self.copyName)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addRow(self.buttonBox)
        self.setLayout(layout)

    def selectLibrary(self):
        self.selectedLibPath = self.libraryComboBox.itemData(
            self.libraryComboBox.currentIndex(), Qt.UserRole + 2)


class copyViewDialog(QDialog):
    def __init__(self, parent, model, cellItem):
        super().__init__(parent=parent)
        self.parent = parent
        self.model = model
        self.cellItem = cellItem
        self.init_UI()

    def init_UI(self):
        self.setWindowTitle("Copy CellView")
        layout = QFormLayout()
        layout.setSpacing(10)
        self.libraryComboBox = QComboBox()
        self.libraryComboBox.setModel(self.model)
        self.libraryComboBox.setModelColumn(0)
        self.libraryComboBox.setCurrentIndex(0)
        self.selectedLibPath = self.libraryComboBox.itemData(0, Qt.UserRole + 2)
        self.libraryComboBox.currentTextChanged.connect(self.selectLibrary)
        layout.addRow(QLabel("Library:"), self.libraryComboBox)
        self.cellComboBox = QComboBox()
        cellList = [str(cell.cellName) for cell in self.selectedLibPath.iterdir() if
                    cell.is_dir()]
        self.cellComboBox.addItems(cellList)
        self.cellComboBox.setEditable(True)
        self.cellComboBox.InsertPolicy = QComboBox.InsertAfterCurrent
        layout.addRow(QLabel("Cell Name:"), self.cellComboBox)
        self.selectedCell = self.cellComboBox.currentText()
        self.cellComboBox.currentTextChanged.connect(self.selectCell)
        self.viewComboBox = QComboBox()
        self.viewComboBox.setEditable(True)
        self.viewComboBox.InsertPolicy = QComboBox.InsertAfterCurrent
        self.viewComboBox.addItems(self.viewList())
        self.selectedView = self.viewComboBox.currentText()
        self.viewComboBox.currentTextChanged.connect(self.selectView)
        layout.addRow(QLabel("View Name:"), self.viewComboBox)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addRow(self.buttonBox)
        self.setLayout(layout)

    def viewList(self):
        viewList = [str(view.stem) for view in
                    self.selectedLibPath.joinpath(self.selectedCell).iterdir() if
                    view.suffix == ".json"]
        return viewList

    def selectLibrary(self):
        self.selectedLibPath = self.libraryComboBox.itemData(
            self.libraryComboBox.currentIndex(), Qt.UserRole + 2)
        cellList = [str(cell.cellName) for cell in self.selectedLibPath.iterdir() if
                    cell.is_dir()]
        self.cellComboBox.clear()
        self.cellComboBox.addItems(cellList)

    def selectCell(self):
        self.selectedCell = self.cellComboBox.currentText()
        self.viewComboBox.clear()
        self.viewComboBox.addItems(self.viewList())

    def selectView(self):
        self.selectedView = self.viewComboBox.currentText()


# library path editor dialogue
class libraryPathEditorDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.libraryEditRowList = []
        self.libraryDict = self.parent.libraryDict
        self.logger = self.parent.parent.logger
        self.init_UI()

    def init_UI(self):
        self.setWindowTitle("Library Path Editor")
        mainLayout = QVBoxLayout()
        mainLayout.setSpacing(10)
        self.entriesLayout = QVBoxLayout()  # layout for all the entries
        labelLayout = QHBoxLayout()
        labelLayout.addWidget(QLabel("Library Name"))
        labelLayout.addWidget(QLabel("Library Path"))
        mainLayout.addLayout(labelLayout)  # add label layout to main layout
        mainLayout.addLayout(labelLayout)  # add label layout to main layout
        for key in self.libraryDict.keys():
            self.libraryEditRowList.append(libraryEditRow(self))
            self.entriesLayout.addWidget(self.libraryEditRowList[-1])
            self.libraryEditRowList[-1].libraryNameEdit.setText(key)
            self.libraryEditRowList[-1].libraryPathEdit.setText(
                str(self.libraryDict[key]))
            self.libraryEditRowList[-1].libraryPathEdit.textChanged.connect(self.addRow)
        mainLayout.addLayout(self.entriesLayout)
        self.libraryEditRowList.append(libraryEditRow(self))
        self.entriesLayout.addWidget(self.libraryEditRowList[-1])
        self.libraryEditRowList[-1].libraryPathEdit.textChanged.connect(self.addRow)
        mainLayout.addLayout(self.entriesLayout)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        mainLayout.addWidget(self.buttonBox)
        self.setLayout(mainLayout)
        self.show()

    #
    # def cancel(self):
    #     self.close()

    def addRow(self):
        if self.libraryEditRowList[-1].libraryPathEdit.text() != "":
            self.libraryEditRowList.append(libraryEditRow(self))
            self.entriesLayout.addWidget(self.libraryEditRowList[-1])
            self.libraryEditRowList[-1].libraryPathEdit.textChanged.connect(self.addRow)


class libraryEditRow(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.init_UI()

    def init_UI(self):
        self.layout = QHBoxLayout()
        self.layout.setSpacing(10)
        self.libraryNameEdit = libraryNameEditC(self)
        self.libraryPathEdit = libraryPathEditC(self)
        self.layout.addWidget(self.libraryNameEdit)
        self.layout.addWidget(self.libraryPathEdit)
        self.setLayout(self.layout)


class libraryNameEditC(QLineEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.fileDialog = QFileDialog()
        self.fileDialog.setFileMode(QFileDialog.Directory)
        self.logger=self.parent.parent.parent.logger
        self.init_UI()

    def init_UI(self):
        self.setPlaceholderText("Library Name")
        self.setMaximumWidth(250)
        self.setFixedWidth(200)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction("Remove", self.removeRow)
        menu.addAction("Add Library...", self.addLibrary)
        menu.addAction("Library Info...", self.libInfo)
        menu.exec(event.globalPos())

    def addLibrary(self):
        self.fileDialog.exec()
        if self.fileDialog.selectedFiles():
            self.selectedDirectory = QDir(self.fileDialog.selectedFiles()[0])
            self.setText(self.selectedDirectory.dirName())
            self.parent.libraryPathEdit.setText(self.selectedDirectory.absolutePath())

    def removeRow(self):
        self.parent.deleteLater()
        self.parent.parent.libraryEditRowList.remove(self.parent)

    def libInfo(self):
        self.logger.warning('Not yet implemented.')


class libraryPathEditC(QLineEdit):
    def __init__(self, parent):
        self.parent = parent
        super().__init__(parent)
        self.init_UI()

    def init_UI(self):
        self.setPlaceholderText("Library Path                ")
        self.setMaximumWidth(600)
        self.setFixedWidth(500)


class symbolChooser(libraryBrowser):
    def __init__(self, parent, scene):
        self.parent = parent
        self.libraryDict = self.parent.libraryDict
        self.scene = scene
        super().__init__(parent)
        self.setWindowTitle("Symbol Chooser")
        self.logger = self.scene.logger

    def initUI(self):
        self.symBrowserCont = symbolBrowserContainer(parent=self)
        self.setCentralWidget(self.symBrowserCont)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.parent.symbolChooser = None
        event.accept()


class symbolBrowserContainer(libraryBrowserContainer):
    def __init__(self, parent) -> None:
        self.parent = parent
        super().__init__(parent)

    def initUI(self):
        self.layout = QVBoxLayout()
        self.designView = symLibrariesView(self)
        self.layout.addWidget(self.designView)
        self.setLayout(self.layout)


class symLibrariesView(designLibrariesView):
    def __init__(self, parent):
        self.parent = parent
        self.scene = self.parent.parent.scene
        super().__init__(parent)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        try:
            index = self.selectedIndexes()[0]
        except IndexError:
            pass
        self.selectedItem = self.libraryModel.itemFromIndex(index)
        if self.selectedItem.data(Qt.UserRole + 1) == "view":
            menu.addAction(QAction("Add Symbol", self, triggered=self.addSymbol))
            menu.addAction(QAction("Open View", self, triggered=self.openView))
            menu.addAction(QAction("Copy View...", self, triggered=self.copyView))
            menu.addAction(QAction("Rename View...", self, triggered=self.renameView))
            menu.addAction(QAction("Delete View...", self, triggered=self.deleteView))
        menu.exec(event.globalPos())

    # library related methods

    def removeLibrary(self):
        pass

    def saveLibAs(self):
        pass

    def renameLib(self):
        pass

    # cell related methods

    def createCell(self):
        pass

    def copyCell(self):
        pass

    def renameCell(self):
        pass

    def deleteCell(self):
        pass

    def addSymbol(self):
        assert type(self.scene) is schematic_scene, 'not a schematic scene'
        symbolFile = self.selectedItem.data(Qt.UserRole + 2)
        self.scene.instanceSymbolFile = symbolFile
        self.scene.addInstance = True
        self.scene.itemCounter += 1
