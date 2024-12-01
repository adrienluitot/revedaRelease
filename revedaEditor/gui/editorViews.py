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

from collections import Counter

# import numpy as np
from PySide6.QtCore import (
    QPoint,
    QRect,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QGuiApplication,
    QColor,
    QMouseEvent,
    QKeyEvent,
    QPainter,
    QWheelEvent,
    QInputDevice
)
from PySide6.QtWidgets import (
    QGraphicsView,
)

import os
from dotenv import load_dotenv

load_dotenv()

if os.environ.get("REVEDA_PDK_PATH"):
    import pdk.schLayers as schlyr
else:
    import defaultPDK.schLayers as schlyr

import revedaEditor.common.net as net
import revedaEditor.backend.undoStack as us


# import os
# if os.environ.get('REVEDASIM_PATH'):
#     import revedasim.simMainWindow as smw


class editorView(QGraphicsView):
    """
    The qgraphicsview for qgraphicsscene. It is used for both schematic and layout editors.
    """
    keyPressedSignal = Signal(int)

    # zoomFactorChanged = Signal(float)
    def __init__(self, scene, parent):
        super().__init__(scene, parent)
        self.parent = parent
        self.editor = self.parent.parent
        self.scene = scene
        self.logger = self.scene.logger
        self.majorGrid = self.editor.majorGrid
        self.snapGrid = self.editor.snapGrid
        self.snapTuple = self.editor.snapTuple
        self.gridbackg = True
        self.linebackg = False
        self._left: QPoint = QPoint(0, 0)
        self._right: QPoint = QPoint(0, 0)
        self._top: QPoint = QPoint(0, 0)
        self._bottom: QPoint = QPoint(0, 0)
        self.viewRect = QRect(0, 0, 0, 0)
        self.zoomFactor = 1.0
        self._middleClickScroll = False
        self._middleClickScrollDelta = QPoint(0,0)
        self.init_UI()

    def init_UI(self):
        """
        Initializes the user interface.

        This function sets up various properties of the QGraphicsView object, such as rendering hints,
        mouse tracking, transformation anchors, and cursor shape.

        Returns:
            None
        """
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # TODO: this might be an option
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        # self.setCacheMode(QGraphicsView.CacheBackground)
        self.setMouseTracking(True)
        self.setInteractive(True)
        self.setCursor(Qt.CrossCursor)
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.TextAntialiasing, True)
        self.viewRect = self.mapToScene(self.rect()).boundingRect().toRect()


    def mousePressEvent(self, mouse_event) -> None:
        super().mousePressEvent(mouse_event)
        if mouse_event.button() == Qt.MiddleButton:
            # Start middle click scroll
            self._middleClickScroll = True
            self._middleClickScrollDelta = mouse_event.position().toPoint()
    
    def mouseReleaseEvent(self, mouse_event) -> None:
        super().mouseReleaseEvent(mouse_event)
        if self._middleClickScroll and mouse_event.button() == Qt.MiddleButton:
            # Release middle click scroll
            self._middleClickScroll = False

    def mouseMoveEvent(self, mouse_event) -> None:
        super().mouseMoveEvent(mouse_event)
        if self._middleClickScroll:
            # Apply middle click scroll
            newPos = mouse_event.position().toPoint()
            oldX = self.horizontalScrollBar().value()
            oldY = self.verticalScrollBar().value()
            self.horizontalScrollBar().setValue(oldX + self._middleClickScrollDelta.x() - newPos.x())
            self.verticalScrollBar().setValue(oldY + self._middleClickScrollDelta.y() - newPos.y())
            self._middleClickScrollDelta = mouse_event.position().toPoint()

    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        Handle the wheel event for zooming in and out of the view.

        Args:
            event (QWheelEvent): The wheel event to handle.
        """
        modifiers = QGuiApplication.keyboardModifiers()

        if event.pointingDevice().type() == QInputDevice.DeviceType.Mouse and modifiers == Qt.ShiftModifier:
            angle = event.angleDelta().x() # if shift is pressed, wheel angle is on the x attrivute
        else:
            angle = event.angleDelta().y()

        if angle == 0: return None

        if modifiers == Qt.ShiftModifier:
            #shift: up -> left / down -> right
            self.scene.moveSceneHor(angle)
        elif modifiers == Qt.ControlModifier:
            #ctrl: up -> top / down -> down
            self.scene.moveSceneVer(angle)
        else:
            # Get the current center point of the view
            center = self.viewport().rect().center()
            oldPos = event.position().toPoint()
            oldScroll = QPoint(self.horizontalScrollBar().value(), self.verticalScrollBar().value())
            delta = oldPos - center
            self.horizontalScrollBar().setValue(oldScroll.x() + delta.x())
            self.verticalScrollBar().setValue(oldScroll.y() + delta.y())

            # Perform the zoom
            self.zoomFactor = 1 + (angle / 360 * 0.6)
            self.scale(self.zoomFactor, self.zoomFactor)

            # Get the new scroll position
            oldScroll = QPoint(self.horizontalScrollBar().value(), self.verticalScrollBar().value())

            self.horizontalScrollBar().setValue(oldScroll.x() - delta.x())
            self.verticalScrollBar().setValue(oldScroll.y() - delta.y())
            # self.zoomFactorChanged.emit(self.zoomFactor)

    def drawBackground(self, painter, rect):
        """
        Draws the background of the painter within the given rectangle.

        Args:
            painter (QPainter): The painter object to draw on.
            rect (QRect): The rectangle to draw the background within.
        """

        # Fill the rectangle with black color
        painter.fillRect(rect, QColor("black"))

        # Calculate the coordinates of the left, top, bottom, and right edges of the rectangle
        self._left = int(rect.left()) - (int(rect.left()) % self.majorGrid)
        self._top = int(rect.top()) - (int(rect.top()) % self.majorGrid)
        self._bottom = int(rect.bottom())
        self._right = int(rect.right())

        if self.gridbackg:
            # Set the pen color to gray
            painter.setPen(QColor("white"))

            # Create a range of x and y coordinates for drawing the grids
            x_coords, y_coords = self.findCoords()

            for x_coord in x_coords:
                for y_coord in y_coords:
                    painter.drawPoint(x_coord, y_coord)

        elif self.linebackg:
            # Set the pen color to gray
            painter.setPen(QColor("gray"))

            # Create a range of x and y coordinates for drawing the lines
            x_coords, y_coords = self.findCoords()

            # Draw vertical lines
            for x in x_coords:
                painter.drawLine(x, self._top, x, self._bottom)

            # Draw horizontal lines
            for y in y_coords:
                painter.drawLine(self._left, y, self._right, y)

        else:
            # Call the base class method to draw the background
            super().drawBackground(painter, rect)

    def findCoords(self):
        """
        Calculate the coordinates for drawing lines or points on a grid.

        Returns:
            tuple: A tuple containing the x and y coordinates for drawing the lines or points.
        """
        x_coords = range(self._left, self._right, self.majorGrid)
        y_coords = range(self._top, self._bottom, self.majorGrid)

        if 160 <= len(x_coords) < 320:
            # Create a range of x and y coordinates for drawing the lines
            x_coords = range(self._left, self._right, self.majorGrid * 2)
            y_coords = range(self._top, self._bottom, self.majorGrid * 2)
        elif 320 <= len(x_coords) < 640:
            x_coords = range(self._left, self._right, self.majorGrid * 4)
            y_coords = range(self._top, self._bottom, self.majorGrid * 4)
        elif 640 <= len(x_coords) < 1280:
            x_coords = range(self._left, self._right, self.majorGrid * 8)
            y_coords = range(self._top, self._bottom, self.majorGrid * 8)
        elif 1280 <= len(x_coords) < 2560:
            x_coords = range(self._left, self._right, self.majorGrid * 16)
            y_coords = range(self._top, self._bottom, self.majorGrid * 16)
        elif len(x_coords) >= 2560:  # grid dots are too small to see
            x_coords = range(self._left, self._right, self.majorGrid * 1000)
            y_coords = range(self._top, self._bottom, self.majorGrid * 1000)

        return x_coords, y_coords

    def keyPressEvent(self, event: QKeyEvent):
        self.keyPressedSignal.emit(event.key())
        match event.key():
            case Qt.Key_M:
                self.scene.editModes.setMode('moveItem')
                self.editor.messageLine.setText('Move Item')
            case Qt.Key_F:
                self.scene.fitItemsInView()
            case Qt.Key_Left:
                self.scene.moveSceneLeft()
            case Qt.Key_Right:
                self.scene.moveSceneRight()
            case Qt.Key_Up:
                self.scene.moveSceneUp()
            case Qt.Key_Down:
                self.scene.moveSceneDown()
            case Qt.Key_Escape:
                self.scene.editModes.setMode("selectItem")
                self.editor.messageLine.setText("Select Item")
                self.scene.deselectAll()
                self.scene._items = None
                if self.scene._selectionRectItem:
                    self.scene.removeItem(self.scene._selectionRectItem)
                    self.scene._selectionRectItem = None
            case _:
                super().keyPressEvent(event)

    def printView(self, printer):
        """
        Print view using selected Printer.

        Args:
            printer (QPrinter): The printer object to use for printing.

        This method prints the current view using the provided printer. It first creates a QPainter object
        using the printer. Then, it toggles the gridbackg and linebackg attributes. After that, it calls
        the revedaPrint method to render the view onto the painter. Finally, it toggles the gridbackg
        and linebackg attributes back to their original state.
        """
        painter = QPainter(printer)

        # Toggle gridbackg attribute
        if self.gridbackg:
            self.gridbackg = False
        else:
            self.linebackg = False

        # Render the view onto the painter
        self.revedaPrint(painter)

        # Toggle gridbackg and linebackg attributes back to their original state
        self.gridbackg = not self.gridbackg
        self.linebackg = not self.linebackg

    def revedaPrint(self, painter):
        viewport_geom = self.viewport().geometry()
        self.drawBackground(painter, viewport_geom)
        painter.drawText(viewport_geom, "Revolution EDA")
        self.render(painter)
        painter.end()


class symbolView(editorView):
    def __init__(self, scene, parent):
        self.scene = scene
        self.parent = parent
        super().__init__(self.scene, self.parent)

    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)
        match event.key():
            case Qt.Key_Escape:
                if self.scene.polygonGuideLine is not None:
                    self.scene.removeItem(self.scene.polygonGuideLine)
                    self.scene.polygonGuideLine = None
                    self.scene.newPolygon = None


class schematicView(editorView):
    def __init__(self, scene, parent):
        self.scene = scene
        self.parent = parent
        super().__init__(self.scene, self.parent)
        self._dotRadius = 2

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.viewRect = self.mapToScene(self.rect()).boundingRect().toRect()
        viewSnapLinesSet = {
            guideLineItem
            for guideLineItem in self.scene.items(self.viewRect)
            if isinstance(guideLineItem, net.guideLine)
        }
        self.removeSnapLines(viewSnapLinesSet)
        # self.mergeSplitViewNets()

    def mergeSplitViewNets(self):
        netsInView = [
            netItem
            for netItem in self.scene.items(self.viewRect)
            if isinstance(netItem, net.schematicNet)
        ]
        for netItem in netsInView:
            if netItem.scene():
                self.scene.mergeSplitNets(netItem)

    def removeSnapLines(self, viewSnapLinesSet):
        undoCommandList = []
        for snapLine in viewSnapLinesSet:
            lines = self.scene.addStretchWires(
                snapLine.sceneEndPoints[0], snapLine.sceneEndPoints[1]
            )

            if lines != []:
                for line in lines:
                    line.inheritGuideLine(snapLine)
                    undoCommandList.append(us.addShapeUndo(self.scene, line))
                self.scene.addUndoMacroStack(undoCommandList, "Stretch Wires")
        if len(viewSnapLinesSet) > 0:
            # undoCommandList.append(us.addShapesUndo(self.scene, lines))
            self.scene.removeItem(snapLine)

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        xextend = self._right - self._left
        yextend = self._bottom - self._top
        netsInView = [
            netItem
            for netItem in self.scene.items(rect)
            if isinstance(netItem, net.schematicNet)
        ]
        if xextend <= 1000 or yextend <= 1000:
            netEndPoints = []
            for netItem in netsInView:
                netEndPoints.extend(netItem.sceneEndPoints)
            pointCountsDict = Counter(netEndPoints)
            dotPoints = [
                point for point, count in pointCountsDict.items() if count >= 3
            ]
            painter.setPen(schlyr.wirePen)
            painter.setBrush(schlyr.wireBrush)
            for dotPoint in dotPoints:
                painter.drawEllipse(dotPoint, self._dotRadius, self._dotRadius)

    def keyPressEvent(self, event: QKeyEvent):
        """
        Handles the key press event for the editor view.

        Args:
            event (QKeyEvent): The key press event to handle.

        """
        if event.key() == Qt.Key_Escape:
            # Esc key pressed, remove snap rect and reset states
            self.scene.removeSnapRect()
            if self.scene._newNet is not None:
                # New net creation mode, cancel creation
                #self.scene.removeItem(self.scene._newNet) # TODO: check behaviour
                self.scene.wireFinished.emit(self.scene._newNet)
                self.scene._newNet = None
            elif self.scene._stretchNet is not None:
                # Stretch net mode, cancel stretch
                self.scene._stretchNet.setSelected(False)
                self.scene._stretchNet.stretch = False
                self.scene.checkNewNet(self.scene._stretchNet)
            # Set the edit mode to select item
            self.scene.editModes.setMode("selectItem")
        super().keyPressEvent(event)


class layoutView(editorView):
    def __init__(self, scene, parent):
        self.scene = scene
        self.parent = parent
        super().__init__(self.scene, self.parent)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            if self.scene._newPath is not None:
                self.scene.removeItem(self.scene._newPath)
                self.scene._newPath = None
            elif self.scene._newRect:
                if self.scene._newRect.rect.isNull() is not None:
                    self.scene.removeItem(self.scene._newRect)
                    self.scene.undoStack.removeLastCommand() #TODO: would be cleaner to not push to undo if not validated (like for the path)
                self.scene._newRect = None
            elif self.scene._stretchPath is not None:
                self.scene._stretchPath.setSelected(False)
                self.scene._stretchPath.stretch = False
                self.scene._stretchPath = None
            elif self.scene.editModes.drawPolygon:
                self.scene.removeItem(self.scene._polygonGuideLine)
                self.scene._newPolygon.points.pop(0)  # remove first duplicate point
                self.scene._newPolygon = None
            elif self.scene.editModes.addInstance:
                self.scene.newInstance = None
                self.scene.layoutInstanceTuple = None

            self.scene.editModes.setMode("selectItem")
        super().keyPressEvent(event)
