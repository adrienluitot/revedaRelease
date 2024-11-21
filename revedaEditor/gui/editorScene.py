#    “Commons Clause” License Condition v1.0
#   #
#    The Software is provided to you by the Licensor under the License, as defined
#    below, subject to the following condition.
#
#    Without limiting other conditions in the License, the grant of rights under the
#    License will not include, and the License does not grant to you, the right to
#    Sell the Software.
#
#    For purposes of the foregoing, “Sell” means practicing any or all of the rights
#    granted to you under the License to provide to third parties, for a fee or other
#    consideration (including without limitation fees for hosting or consulting/
#    support services related to the Software), a product or service whose value
#    derives, entirely or substantially, from the functionality of the Software. Any
#    license notice or attribution required by the License must also include this
#    Commons Clause License Condition notice.
#
#   Add-ons and extensions developed for this software may be distributed
#   under their own separate licenses.
#
#    Software: Revolution EDA
#    License: Mozilla Public License 2.0
#    Licensor: Revolution Semiconductor (Registered in the Netherlands)
#

import os
import math
from typing import List, Sequence

# import numpy as np
from PySide6.QtCore import (QEvent, QPoint, QRectF, Qt, Signal)
from PySide6.QtGui import (QGuiApplication, QColor, QPen, QPainterPath, )
from PySide6.QtWidgets import (QGraphicsRectItem, QGraphicsScene, QMenu, QGraphicsItem,
                               QDialog,
                               QCompleter)
from dotenv import load_dotenv

import revedaEditor.backend.dataDefinitions as ddef
import revedaEditor.backend.undoStack as us
import revedaEditor.gui.propertyDialogues as pdlg


load_dotenv()
if os.environ.get("REVEDA_PDK_PATH"):
    pass
else:
    pass


class editorScene(QGraphicsScene):

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.editorWindow = self.parent.parent
        self.majorGrid = self.editorWindow.majorGrid
        self.snapTuple = self.editorWindow.snapTuple
        self._snapDistance = int(self.majorGrid * 0.5)
        self.mousePressLoc = None
        self.mouseNotReleased = False
        self.mouseMoveLoc = None
        self.mouseReleaseLoc = None
        # common edit modes
        self.editModes = ddef.editModes(selectItem=True, deleteItem=False, moveItem=False,
                                        copyItem=False, rotateItem=False,
                                        changeOrigin=False,
                                        panView=False, stretchItem=False, )
        self.readOnly = False  # if the scene is not editable
        self.undoStack = us.undoStack()
        self.undoStack.setUndoLimit(99)
        self.origin = QPoint(0, 0)
        self.cellName = self.editorWindow.file.parent.stem
        self.partialSelection = True
        self._selectionRectItem = None
        self._lastSelects = []
        self._itemsToMove = []
        self._itemsToMoveOffset = []
        self.libraryDict = self.editorWindow.libraryDict
        self.itemContextMenu = QMenu()
        self.appMainW = self.editorWindow.appMainW
        self.logger = self.appMainW.logger
        self.messageLine = self.editorWindow.messageLine
        self.statusLine = self.editorWindow.statusLine
        self.installEventFilter(self)
        self.setMinimumRenderSize(2)
        self.setSceneRect(-5e5, -5e5, 1e6, 1e6) # this is to be able to zoom out more than boundingRect
        # size might not be enough ? it may need a bigger scene rect ? or smaller devices ?

    def mousePressEvent(self, event):
        self.mousePressLoc = event.scenePos().toPoint()
        if event.button() == Qt.MouseButton.LeftButton:
            if self.editModes.panView:
                self.centerViewOnPoint(self.mousePressLoc)
                self.messageLine.setText("Pan View at mouse press position")
            else:
                itemsUnderCursor = self._getItemsAtLoc(self.mousePressLoc)
                self._itemsToMove = []
                self._itemsToMoveOffset = []
                if len(itemsUnderCursor) > 0:
                    moveSelected = False
                    for item in itemsUnderCursor:
                        if item.isSelected():
                            moveSelected = True
                            break
                    if moveSelected:
                        self._itemsToMove = [item for item in self.selectedItems() if item.parentItem() is None]
                    else:
                        self._itemsToMove = [sorted(itemsUnderCursor, key=lambda n:
                                                self._distItemCenterCursor(n, self.mousePressLoc))[0]]
                    for item in self._itemsToMove:
                        itemPos = item.scenePos().toPoint() 
                        #TODO: fix move position delta due to angle (need to use item width/height?):
                        # if item.angle == 180:
                        #     self._itemsToMoveOffset.append(self.mousePressLoc - itemPos)
                        # else:
                        self._itemsToMoveOffset.append(itemPos - self.mousePressLoc)
                    #TODO: enable move mode (move btn/key M) and 2 clicks

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.mouseReleaseLoc = event.scenePos().toPoint()
        modifiers = QGuiApplication.keyboardModifiers()
        if event.button() == Qt.MouseButton.LeftButton:
            modifiers = QGuiApplication.keyboardModifiers()
            if self.editModes.moveItem and len(self._itemsToMove) > 0:
                if self.mouseReleaseLoc != self.mousePressLoc:
                    self.moveShapesUndoStack(self._itemsToMove, self._itemsToMoveOffset,
                                             self.mousePressLoc,
                                             self.mouseReleaseLoc)
                    self._itemsToMove = []
                    self._itemsToMoveOffset = []
                    self.editModes.setMode("selectItem")
            elif self.editModes.selectItem:
                self._handleSelection(modifiers)

            self._cleanupAfterMouseRelease(modifiers)

    def _handleSelection(self, modifiers):
        addToSelection = True
        clearSelection = False
        if modifiers == Qt.KeyboardModifier.ControlModifier:
            addToSelection = False # remove from selection, only with Ctrl
        # elif modifiers == Qt.KeyboardModifier.AltModifier:
        #     self._handleAltSelection()
        if modifiers != Qt.KeyboardModifier.ControlModifier and modifiers != Qt.KeyboardModifier.ShiftModifier:
            clearSelection = True
        
        if self._selectionRectItem:
            self._processExistingSelectionRectangle(addToSelection, clearSelection)
        else:
            self._handleDefaultSelection(addToSelection, clearSelection)

    def _cleanupAfterMouseRelease(self, modifiers):
        if self._selectionRectItem:
            self.removeItem(self._selectionRectItem)
            self._selectionRectItem = None

        self._itemsToMove = self.selectedItems()
        self.messageLine.setText("Item selected" if self._itemsToMove else "Nothing selected")

    def _processExistingSelectionRectangle(self, addToSelection, clearSelection):
        selectionMode = Qt.ItemSelectionMode.IntersectsItemShape if self.partialSelection else Qt.ItemSelectionMode.ContainsItemShape
        selectionPath = QPainterPath()
        selectionPath.addRect(self._selectionRectItem.sceneBoundingRect())
        if clearSelection:
            self.clearSelection()
        if addToSelection:
            self.setSelectionArea(selectionPath, selectionOperation=Qt.AddToSelection, mode=selectionMode)
        else:
            # remove selected items from selection
            for item in self.items(self._selectionRectItem.sceneBoundingRect()):
                item.setSelected(False)
        self.messageLine.setText("Selection complete")

    def _startNewSelectionRectangle(self):
        self._selectionRectItem = QGraphicsRectItem(
            QRectF(self.mousePressLoc, self.mouseMoveLoc)
        )
        selectionRectPen = QPen(QColor("yellow"), 2, Qt.PenStyle.DashLine)
        selectionRectPen.setCosmetic(True)
        self._selectionRectItem.setPen(selectionRectPen)
        self.addItem(self._selectionRectItem)

    def _handleAltSelection(self):
        self.clearSelection()
        clicked_items = self._getItemsAtLoc(self.mouseReleaseLoc)
        if clicked_items:
            clicked_items[0].setSelected(True)

    def _handleDefaultSelection(self, addToSelection, clearSelection):
        if self._selectionRectItem == None:
            # get items
            itemsAtMousePress = self._getItemsAtLoc(self.mouseReleaseLoc)
            if len(itemsAtMousePress) == 0:
                if clearSelection:
                    self.clearSelection()
                return None
            # order by distance to cursor
            # TODO: use a more common way ? is there a builtin way to mimic hover behaviour
            itemsAtMousePress = sorted(itemsAtMousePress, key=lambda n: self._distItemCenterCursor(n, self.mouseReleaseLoc))
            # verify if items list has changed
            if itemsAtMousePress != self._lastSelects:
                self._lastSelects = itemsAtMousePress
            # choose item to manage
            itemToManage = self._lastSelects[0] # by default select first
            selectNext = False
            for item in self._lastSelects:
                if item.isSelected():
                    # found a selected item
                    if addToSelection:
                        # and we want to add an item, manage next
                        selectNext = True
                    else:
                        # we want to remove this item
                        itemToManage = item 
                        break
                elif selectNext:
                    itemToManage = item
                    break

            if clearSelection:
                self.clearSelection()
            itemToManage.setSelected(addToSelection)
    
    def _distItemCenterCursor(self, item, point):
        center = item.pos()
        return math.sqrt(pow(center.x() - point.x(), 2) + pow(center.y() - point.y(), 2))

    def _getItemsAtLoc(self, loc):
        itemsAtLoc = []
        for item in self.items(loc):
            if item.parentItem() is None:
                itemsAtLoc.append(item)
                item.scene()
                # TODO: There seems to be a bug when trying to get parent of item with "None" parent -> the item is deleted.
                # Getting its scene cancel the deletion. It seems to be the same bug as in Layout save.
        return itemsAtLoc

    def mouseMoveEvent(self, event):
        # super().mouseMoveEvent(event)
        self.mouseMoveLoc = event.scenePos().toPoint()
        if event.buttons() == Qt.MouseButton.LeftButton:
            if self._itemsToMove and self.mousePressLoc != self.mouseMoveLoc:
                self.editModes.setMode("moveItem")
            
            if self.editModes.moveItem and len(self._itemsToMove) > 0:
                for item, offset in zip(self._itemsToMove, self._itemsToMoveOffset):
                    item.setPos(self.mouseMoveLoc + offset)
            elif self.editModes.selectItem and len(self._itemsToMove) == 0:
                if self._selectionRectItem:
                    self._updateSelectionRectangle(self.mouseMoveLoc)
                else:
                    if len(self._getItemsAtLoc(self.mousePressLoc)) == 0:
                        # Start a new selection rectangle
                        self._startNewSelectionRectangle()
    
    
    def _updateSelectionRectangle(self, currentPos):
        if self._selectionRectItem:
            rect = QRectF(self.mousePressLoc, currentPos).normalized()
            self._selectionRectItem.setRect(rect)

    def snapToBase(self, number, base):
        """
        Restrict a number to the multiples of base
        """
        return int(round(number / base)) * base

    def snapToGrid(self, point: QPoint, snapTuple: tuple[int, int]):
        """
        snap point to grid. Divides and multiplies by grid size.
        """
        return QPoint(self.snapToBase(point.x(), snapTuple[0]),
                      self.snapToBase(point.y(), snapTuple[1]), )

    def rotateSelectedItems(self, point: QPoint):
        """
        Rotate selected items by 90 degree.
        """
        for item in self.selectedItems():
            self.rotateAnItem(point, item, 90)
        self.editModes.setMode("selectItem")

    def rotateAnItem(self, point: QPoint, item: QGraphicsItem, angle: int):
        undoCommand = us.undoRotateShape(self, item, point, angle)
        self.undoStack.push(undoCommand)

    def eventFilter(self, source, event):
        """
        Mouse events should snap to background grid points.
        """
        if self.readOnly:  # if read only do not propagate any mouse events
            return True
        elif event.type() in [QEvent.GraphicsSceneMouseMove, QEvent.GraphicsSceneMousePress,
                              QEvent.GraphicsSceneMouseRelease, ]:
            event.setScenePos(self.snapToGrid(event.scenePos(), self.snapTuple).toPointF())
            return False
        else:
            return super().eventFilter(source, event)

    def copySelectedItems(self):
        """
        Copies the selected items in the scene, creates a duplicate of each item,
        and adds them to the scene with a slight shift in position.
        """
        selectedItems = [
            item for item in self.selectedItems() if item.parentItem() is None
        ]
        for item in selectedItems:
            # Create a new shape based on the item dictionary and the snap tuple
            shape = self._getItemShape(item) # editorType dependant
            # Create an undo command for adding the shape
            undo_command = us.addShapeUndo(self, shape)
            # Push the undo command to the undo stack
            self.undoStack.push(undo_command)
            # Shift the position of the shape by one grid unit to the right and down
            #TODO: copy to cursor next click
            shape.setPos(
                QPoint(
                    item.pos().x() + 4 * self.snapTuple[0],
                    item.pos().y() + 4 * self.snapTuple[1],
                )
            )
        self.editModes.setMode("selectItem") # TODO: might be a better way to switch back automatically to edit mode
                                            # rather than put it everywhere ?

    def _getItemShape(self, item):
        pass

    def flipHorizontal(self):
        for item in self.selectedItems():
            item.flipTuple = (-1, 1)

    def flipVertical(self):
        for item in self.selectedItems():
            item.flipTuple = (1, -1)

    def selectAll(self):
        """
        Select all items in the scene.
        """
        [item.setSelected(True) for item in self.items()]

    def deselectAll(self):
        """
        Deselect all items in the scene.
        """
        [item.setSelected(False) for item in self.selectedItems()]

    def deleteSelectedItems(self):
        if self.selectedItems() is not None:
            for item in self.selectedItems():
                undoCommand = us.deleteShapeUndo(self, item)
                self.undoStack.push(undoCommand)
            self.update()  # update the scene

    def stretchSelectedItems(self):
        if self.selectedItems() is not None:
            try:
                for item in self.selectedItems():
                    if hasattr(item, "stretch"):
                        item.stretch = True
            except AttributeError:
                self.messageLine.setText("Nothing selected")

    def fitItemsInView(self) -> None:
        # TODO: itemsBoundingRect() processes all the items in the view, it might be very slow if the number of item is
        # consequent. We should find a better solution (like storing the items in the extreme postions to compute the 
        # bounding rect with only 4 items instead of N)
        self.views()[0].fitInView(self.itemsBoundingRect().adjusted(-40, -40, 40, 40), Qt.KeepAspectRatio)
        self.views()[0].viewport().update()

    def moveSceneVer(self, moveFactor) -> None:
        view = self.views()[0]
        currScroll = view.verticalScrollBar().value()
        shift = moveFactor/360 * view.viewport().height()/2
        view.verticalScrollBar().setValue(currScroll - shift)

    def moveSceneHor(self, moveFactor) -> None:
        view = self.views()[0]
        currScroll = view.horizontalScrollBar().value()
        shift = moveFactor/360 * view.viewport().width()/2
        view.horizontalScrollBar().setValue(currScroll - shift)

    def moveSceneLeft(self) -> None:
        view = self.views()[0]
        currScroll = view.horizontalScrollBar().value()
        newScroll = currScroll - view.viewport().width()/3
        view.horizontalScrollBar().setValue(newScroll)

    def moveSceneRight(self) -> None:
        view = self.views()[0]
        currScroll = view.horizontalScrollBar().value()
        newScroll = currScroll + view.viewport().width()/3
        view.horizontalScrollBar().setValue(newScroll)

    def moveSceneUp(self) -> None:
        view = self.views()[0]
        currScroll = view.verticalScrollBar().value()
        newScroll = currScroll - view.viewport().height()/3
        view.verticalScrollBar().setValue(newScroll)

    def moveSceneDown(self) -> None:
        view = self.views()[0]
        currScroll = view.verticalScrollBar().value()
        newScroll = currScroll + view.viewport().height()/3
        view.verticalScrollBar().setValue(newScroll)

    def centerViewOnPoint(self, point: QPoint) -> None:
        view = self.views()[0]
        view_widget = view.viewport()
        width = view_widget.width()
        height = view_widget.height()
        self.setSceneRect(point.x() - width / 2, point.y() - height / 2, width, height)

    def addUndoStack(self, item: QGraphicsItem):
        undoCommand = us.addShapeUndo(self, item)
        self.undoStack.push(undoCommand)

    def deleteUndoStack(self, item: QGraphicsItem):
        undoCommand = us.deleteShapeUndo(self, item)
        self.undoStack.push(undoCommand)

    def addListUndoStack(self, itemList: List) -> None:
        undoCommand = us.addShapesUndo(self, itemList)
        self.undoStack.push(undoCommand)

    def moveShapesUndoStack(self, items: Sequence[QGraphicsItem],
                            itemsOffsetList: Sequence[QPoint], start: QPoint,
                            end: QPoint) -> None:
        undoCommand = us.undoMoveShapesCommand(items, itemsOffsetList, start, end)
        self.undoStack.push(undoCommand)

    def addUndoMacroStack(self, undoCommands: list, macroName: str = "Macro"):
        if len(undoCommands) > 0:
            self.undoStack.beginMacro(macroName)
            for command in undoCommands:
                self.undoStack.push(command)
            self.undoStack.endMacro()

    def moveBySelectedItems(self):
        if self.selectedItems():
            dlg = pdlg.moveByDialogue(self.editorWindow)
            dlg.xEdit.setText("0.0")
            dlg.yEdit.setText("0.0")
            factor = fabproc.dbu if(self.editorType == "lay") else 1.0
            if dlg.exec() == QDialog.Accepted:
                for item in self.selectedItems():
                    dx = self.snapToBase(float(dlg.xEdit.text()) * factor, self.snapTuple[0])
                    dy = self.snapToBase(float(dlg.yEdit.text()) * factor, self.snapTuple[1])
                    moveCommand = us.undoMoveByCommand(self, self.selectedItems(), dx, dy)
                    self.undoStack.push(moveCommand)
                    self.editorWindow.messageLine.setText(
                        f"Moved items by {dlg.xEdit.text()} and {dlg.yEdit.text()}")
                    self.editModes.setMode("selectItem")

    def cellNameComplete(self, dlg: QDialog, cellNameList: List[str]):
        cellNameCompleter = QCompleter(cellNameList)
        cellNameCompleter.setCaseSensitivity(Qt.CaseInsensitive)
        dlg.instanceCellName.setCompleter(cellNameCompleter)

    def viewNameComplete(self, dlg: QDialog, viewNameList: List[str]):
        viewNameCompleter = QCompleter(viewNameList)
        viewNameCompleter.setCaseSensitivity(Qt.CaseInsensitive)
        dlg.instanceViewName.setCompleter(viewNameCompleter)
        dlg.instanceViewName.setText(viewNameList[0])
