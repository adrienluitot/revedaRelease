import json
import shape as shp
from PySide6.QtCore import (QDir, QLine, QRect, QRectF, QPoint, QPointF, QSize, )
from PySide6.QtGui import (QAction, QKeySequence, QColor, QFont, QIcon, QPainter, QPen, QBrush, QFontMetrics,
                           QStandardItemModel, QTransform, QCursor, QUndoCommand, QUndoStack)


class symbolEncoder(json.JSONEncoder):
    def default(self, item):
        if isinstance(item, shp.rectangle):
            itemDict = {
                "type": "rect",
                "rect": item.__dict__["rect"].getCoords(),
                "color": item.__dict__["pen"].color().toTuple(),
                "width": item.__dict__["pen"].width(),
                "lineStyle": str(item.__dict__["pen"].style()),
                "cosmetic": item.__dict__["pen"].isCosmetic(),
                "location": item.scenePos().toTuple(),
            }
            return itemDict
        elif isinstance(item, shp.line):
            itemDict = {
                "type": "line",
                "start": item.__dict__["start"].toTuple(),
                "end": item.__dict__["end"].toTuple(),
                "color": item.__dict__["pen"].color().toTuple(),
                "width": item.__dict__["pen"].width(),
                "lineStyle": str(item.__dict__["pen"].style()),
                "cosmetic": item.__dict__["pen"].isCosmetic(),
                "location": item.scenePos().toTuple(),
            }
            return itemDict
        elif isinstance(item, shp.pin):
            itemDict = {
                "type": "pin",
                "start": item.__dict__["start"].toTuple(),
                "color": item.__dict__["pen"].color().toTuple(),
                "width": item.__dict__["pen"].width(),
                "lineStyle": str(item.__dict__["pen"].style()),
                "cosmetic": item.__dict__["pen"].isCosmetic(),
                "pinName": item.__dict__["pinName"],
                "pinDir": item.__dict__["pinDir"],
                "pinType": item.__dict__["pinType"],
                "location": item.scenePos().toTuple(),
            }
            return itemDict
        elif isinstance(item, shp.label):
            itemDict = {
                "type": "label",
                "start": item.__dict__["start"].toTuple(),
                "color": item.__dict__["pen"].color().toTuple(),
                "width": item.__dict__["pen"].width(),
                "lineStyle": str(item.__dict__["pen"].style()),
                "cosmetic": item.__dict__["pen"].isCosmetic(),
                "labelName": item.__dict__["labelName"],
                "labelType": item.__dict__["labelType"],
                "labelHeight": item.__dict__["labelHeight"],
                "labelAlign": item.__dict__["labelAlign"],
                "labelOrient": item.__dict__["labelOrient"],
                "labelUse": item.__dict__["labelUse"],
                "location": item.scenePos().toTuple(),
            }
            return itemDict

        else:
            return super().default(item)

