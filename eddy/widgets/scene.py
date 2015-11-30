# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: an editor for the Graphol ontology language.                    #
#  Copyright (C) 2015 Daniele Pantaleone <danielepantaleone@me.com>      #
#                                                                        #
#  This program is free software: you can redistribute it and/or modify  #
#  it under the terms of the GNU General Public License as published by  #
#  the Free Software Foundation, either version 3 of the License, or     #
#  (at your option) any later version.                                   #
#                                                                        #
#  This program is distributed in the hope that it will be useful,       #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the          #
#  GNU General Public License for more details.                          #
#                                                                        #
#  You should have received a copy of the GNU General Public License     #
#  along with this program. If not, see <http://www.gnu.org/licenses/>.  #
#                                                                        #
##########################################################################
#                                                                        #
#  Graphol is developed by members of the DASI-lab group of the          #
#  Dipartimento di Ingegneria Informatica, Automatica e Gestionale       #
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


import itertools
import os
import sys

from PyQt5.QtCore import Qt, QPointF, QSettings, QRectF, pyqtSignal
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QGraphicsScene, QUndoStack, QMenu
from PyQt5.QtXml import QDomDocument

from eddy import __appname__ as appname, __organization__ as organization, getPath
from eddy.commands import CommandEdgeAdd, CommandNodeAdd, CommandNodeMove
from eddy.datatypes import DiagramMode, DistinctList, ItemType, RestrictionType, SpecialType
from eddy.functions import rangeF, snapF
from eddy.items import ConceptNode, ComplementNode, DomainRestrictionNode, InputEdge, InclusionEdge
from eddy.items import RangeRestrictionNode, RoleChainNode, RoleInverseNode, ValueDomainNode
from eddy.utils import Clipboard, UniqueID


class Document(object):
    """
    This class is used to hold scene saved file data (filepath, filename etc).
    """
    def __init__(self):
        """
        Initialize the scene document.
        """
        self._edited = None
        self._filepath = ''

    @property
    def edited(self):
        """
        Returns the timestamp when the file has been last modified.
        :return: float
        """
        return self._edited

    @edited.setter
    def edited(self, value):
        """
        Set the timestamp when the file has been last modified
        :param value: the timestamp value
        """
        self._edited = float(value)

    @property
    def filepath(self):
        """
        Returns the filepath of the document.
        :return: str
        """
        return self._filepath

    @filepath.setter
    def filepath(self, value):
        """
        Set the filepath of the document.
        :param value: the filepath of the document.
        """
        self._filepath = getPath(value)

    @property
    def name(self):
        """
        Returns the name of the saved file.
        :rtype: str
        """
        if not self.filepath:
            return 'Untitled'
        return os.path.basename(os.path.normpath(self.filepath))


class DiagramScene(QGraphicsScene):
    """
    This class implements the main Diagram Scene.
    """
    GridPen = QPen(QColor(80, 80, 80), 0, Qt.SolidLine)
    GridSize = 20
    MinSize = 2000
    MaxSize = 1000000

    edgeInserted = pyqtSignal('QGraphicsItem', int)  # emitted when a edge is inserted in the scene
    nodeInserted = pyqtSignal('QGraphicsItem', int)  # emitted when a node is inserted in the scene
    modeChanged = pyqtSignal(DiagramMode)  # emitted when the operational mode changes
    updated = pyqtSignal()  # emitted when the scene is updated

    ####################################################################################################################
    #                                                                                                                  #
    #   SCENE IMPLEMENTATION                                                                                           #
    #                                                                                                                  #
    ####################################################################################################################

    def __init__(self, mainwindow, parent=None):
        """
        Initialize the graphic scene.
        :param mainwindow: the reference to the main window.
        :param parent: the parent widget.
        """
        super().__init__(parent)
        self.mainwindow = mainwindow  ## main window reference
        self.command = None  ## undo/redo command to be added in the stack
        self.clipboardPasteOffsetX = Clipboard.PasteOffsetX  ## X offset to be added to item position upon paste
        self.clipboardPasteOffsetY = Clipboard.PasteOffsetY  ## Y offset to be added to item position upon paste
        self.document = Document()  ## document associated with the current scene
        self.edgesById = {}  ## used to index edges using their id
        self.nodesById = {}  ## used to index nodes using their id
        self.nodesByLabel = {}  ## used to index nodes using their label text
        self.settings = QSettings(QSettings.IniFormat, QSettings.UserScope, organization, appname)  ## settings
        self.uniqueID = UniqueID()  ## used to generate unique incremental ids
        self.undostack = QUndoStack(self)  ## use to push actions and keep history for undo/redo
        self.undostack.setUndoLimit(50)  ## TODO: make the stack configurable
        self.mode = DiagramMode.Idle  ## operation mode
        self.modeParam = None  ## extra parameter for the operation mode (see setMode())
        self.mouseOverNode = None  ## node below the mouse cursor during edge insertion
        self.mousePressPos = None  ## scene position where the mouse has been pressed
        self.mousePressNode = None  ## node acting as mouse grabber during mouse move events
        self.mousePressNodePos = None  ## position of the shape acting as mouse grabber during mouse move events
        self.mousePressData = {}  ## extra data needed to process item interactive movements

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def contextMenuEvent(self, menuEvent):
        """
        Bring up the context menu if necessary.
        :param menuEvent: the context menu event instance.
        """
        if not self.items(menuEvent.scenePos()):
            menu = QMenu()
            if not self.mainwindow.clipboard.empty():
                menu.addAction(self.mainwindow.actionPaste)
            menu.addAction(self.mainwindow.actionSelectAll)
            menu.addSeparator()
            menu.addAction(self.mainwindow.actionOpenSceneProperties)
            menu.exec_(menuEvent.screenPos())
        else:
            super().contextMenuEvent(menuEvent)

    def mousePressEvent(self, mouseEvent):
        """
        Executed when a mouse button is clicked on the scene.
        :param mouseEvent: the mouse event instance.
        """
        if mouseEvent.buttons() & Qt.LeftButton:

            if self.mode is DiagramMode.NodeInsert:

                ########################################################################################################
                #                                                                                                      #
                #                                         NODE INSERTION                                               #
                #                                                                                                      #
                ########################################################################################################

                # create a new node and place it under the mouse position
                func = self.modeParam
                node = func(scene=self)
                node.setPos(self.snapToGrid(mouseEvent.scenePos()))

                # no need to switch back the operation mode here: the signal handlers already does that and takes
                # care of the keyboard modifiers being held (if CTRL is being held the operation mode doesn't change)
                self.undostack.push(CommandNodeAdd(scene=self, node=node))
                self.nodeInserted.emit(node, mouseEvent.modifiers())

                super().mousePressEvent(mouseEvent)

            elif self.mode is DiagramMode.EdgeInsert:

                ########################################################################################################
                #                                                                                                      #
                #                                         EDGE INSERTION                                               #
                #                                                                                                      #
                ########################################################################################################

                # see if we are pressing the mouse on a node and if so set the edge add command
                node = self.itemOnTopOf(mouseEvent.scenePos(), edges=False)
                if node:

                    func = self.modeParam
                    edge = func(scene=self, source=node)
                    edge.updateEdge(target=mouseEvent.scenePos())

                    # put the command on hold since we don't know if the edge will be truly inserted
                    self.command = CommandEdgeAdd(scene=self, edge=edge)

                    # add the edge to the scene
                    self.addItem(self.command.edge)

                super().mousePressEvent(mouseEvent)

            else:

                # see if this event needs to be handled in graphics items before we prepare data for a different
                # operational mode: a graphics item may bypass the actions being performed here below by
                # switching the operational mode to something different than DiagramMode.Idle.
                super().mousePressEvent(mouseEvent)

                if self.mode is DiagramMode.Idle:

                    ####################################################################################################
                    #                                                                                                  #
                    #                                       ITEM MOVEMENT                                              #
                    #                                                                                                  #
                    ####################################################################################################

                    # see if we have some nodes selected in the scene: this is needed because itemOnTopOf
                    # will discard labels, so if we have a node whose label is overlapping the node shape,
                    # clicking on the label will make itemOnTopOf return the node item instead of the label.
                    selected = self.selectedNodes()

                    if selected:

                        # we have some nodes selected in the scene so we probably are going to do a
                        # move operation, prepare data for mouse move event => select a node that will act
                        # as mouse grabber to compute delta movements for each componenet in the selection
                        self.mousePressNode = self.itemOnTopOf(mouseEvent.scenePos(), edges=False)

                        if self.mousePressNode:

                            self.mousePressNodePos = self.mousePressNode.pos()
                            self.mousePressPos = mouseEvent.scenePos()

                            # initialize data
                            self.mousePressData = {
                                'nodes': {
                                    node: {
                                        'anchors': {k: v for k, v in node.anchors.items()},
                                        'pos': node.pos(),
                                    } for node in selected},
                                'edges': {}
                            }

                            # figure out if the nodes we are moving are sharing edges: if so, move the edge
                            # together with the nodes (which actually means moving the edge breakpoints)
                            for node in self.mousePressData['nodes']:
                                for edge in node.edges:
                                    if edge not in self.mousePressData['edges']:
                                        if edge.other(node).isSelected():
                                            self.mousePressData['edges'][edge] = edge.breakpoints[:]

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when then mouse is moved on the scene.
        :param mouseEvent: the mouse event instance.
        """
        if mouseEvent.buttons() & Qt.LeftButton:

            if self.mode is DiagramMode.EdgeInsert:

                ########################################################################################################
                #                                                                                                      #
                #                                         EDGE INSERTION                                               #
                #                                                                                                      #
                ########################################################################################################

                if self.command and self.command.edge:
                    mousePos = mouseEvent.scenePos()
                    self.command.edge.updateEdge(target=mousePos)
                    self.mouseOverNode = self.itemOnTopOf(mousePos, edges=False, skip={self.command.edge.source})

            else:

                # if we are still idle we are probably going to start a node(s) move: if that's
                # the case change the operational mode before actually computing delta movements
                if self.mode is DiagramMode.Idle:
                    if self.mousePressNode:
                        self.setMode(DiagramMode.NodeMove)

                if self.mode is DiagramMode.NodeMove:

                    ####################################################################################################
                    #                                                                                                  #
                    #                                       ITEM MOVEMENT                                              #
                    #                                                                                                  #
                    ####################################################################################################

                    # calculate the delta and adjust the value if the snap to grid feature is enabled: we'll use the
                    # position of the node acting as mouse grabber to determine the new delta to and move other items
                    snapped = self.snapToGrid(self.mousePressNodePos + mouseEvent.scenePos() - self.mousePressPos)
                    delta = snapped - self.mousePressNodePos

                    # update all the breakpoints positions
                    for edge, breakpoints in self.mousePressData['edges'].items():
                        for i in range(len(breakpoints)):
                            edge.breakpoints[i] = breakpoints[i] + delta

                    # move all the selected nodes
                    for node, data in self.mousePressData['nodes'].items():
                        node.setPos(data['pos'] + delta)
                        for edge, pos in data['anchors'].items():
                            node.setAnchor(edge, pos + delta)
                        node.updateEdges()

        super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the scene.
        :param mouseEvent: the mouse event instance.
        """
        if mouseEvent.button() == Qt.LeftButton:

            if self.mode is DiagramMode.EdgeInsert:

                ########################################################################################################
                #                                                                                                      #
                #                                         EDGE INSERTION                                               #
                #                                                                                                      #
                ########################################################################################################

                if self.command and self.command.edge:

                    # keep the edge only if it's overlapping a node in the scene
                    node = self.itemOnTopOf(mouseEvent.scenePos(), edges=False, skip={self.command.edge.source})

                    if node:

                        self.command.edge.target = node
                        self.command.edge.source.addEdge(self.command.edge)
                        self.command.edge.target.addEdge(self.command.edge)
                        self.command.edge.updateEdge()

                        self.undostack.push(self.command)
                        self.updated.emit()

                    else:

                        # remove the edge from the scene
                        self.removeItem(self.command.edge)

                    # always emit this signal even if the edge has not been inserted since this will clear
                    # also the toolbox switching back the operation mode to DiagramMode.Idle in case the CTRL
                    # keyboard modifier is not being held (in which case the toolbox button will stay selected)
                    self.edgeInserted.emit(self.command.edge, mouseEvent.modifiers())

                    self.clearSelection()
                    self.command = None
                    self.mouseOverNode = None

            elif self.mode is DiagramMode.NodeMove:

                ########################################################################################################
                #                                                                                                      #
                #                                         ITEM MOVEMENT                                                #
                #                                                                                                      #
                ########################################################################################################

                data = {
                    'nodes': {
                        node: {
                            'anchors': {k: v for k, v in node.anchors.items()},
                            'pos': node.pos(),
                        } for node in self.mousePressData['nodes']},
                    'edges': {x: x.breakpoints[:] for x in self.mousePressData['edges']}
                }

                self.undostack.push(CommandNodeMove(scene=self, pos1=self.mousePressData, pos2=data))
                self.setMode(DiagramMode.Idle)

        super().mouseReleaseEvent(mouseEvent)

        self.mousePressPos = None
        self.mousePressNode = None
        self.mousePressNodePos = None
        self.mousePressData = None

    ####################################################################################################################
    #                                                                                                                  #
    #   DRAWING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def drawBackground(self, painter, rect):
        """
        Draw the scene background.
        :param painter: the current active painter.
        :param rect: the exposed rectangle.
        """
        # do not draw the background grid if we are printing the scene
        # TODO: replace isinstance with something smarter since this may be resource consuming
        if self.settings.value('scene/snap_to_grid', False, bool) and not isinstance(painter.device(), QPrinter):
            startX = int(rect.left()) - (int(rect.left()) % DiagramScene.GridSize)
            startY = int(rect.top()) - (int(rect.top()) % DiagramScene.GridSize)
            painter.setPen(DiagramScene.GridPen)
            painter.drawPoints(*(QPointF(x, y) for x in rangeF(startX, rect.right(), DiagramScene.GridSize) \
                                                 for y in rangeF(startY, rect.bottom(), DiagramScene.GridSize)))

    ####################################################################################################################
    #                                                                                                                  #
    #   EXPORT                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def toGraphol(self):
        """
        Export the current node in Graphol format.
        :rtype: QDomDocument
        """
        doc = QDomDocument()
        doc.appendChild(doc.createProcessingInstruction('xml', 'version="1.0" encoding="UTF-8" standalone="no"'))

        root = doc.createElement('graphol')
        root.setAttribute('xmlns', 'http://www.dis.uniroma1.it/~graphol/schema')
        root.setAttribute('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        root.setAttribute('xmlns:data', 'http://www.dis.uniroma1.it/~graphol/schema/data')
        root.setAttribute('xmlns:line', 'http://www.dis.uniroma1.it/~graphol/schema/line')
        root.setAttribute('xmlns:shape', 'http://www.dis.uniroma1.it/~graphol/schema/shape')
        root.setAttribute('xsi:schemaLocation', 'http://www.dis.uniroma1.it/~graphol/schema '
                                                'http://www.dis.uniroma1.it/~graphol/schema/graphol.xsd')

        doc.appendChild(root)

        graph = doc.createElement('graph')
        graph.setAttribute('width', self.sceneRect().width())
        graph.setAttribute('height', self.sceneRect().height())

        for node in self.nodes():
            # append all the nodes to the graph element
            graph.appendChild(node.toGraphol(doc))

        for edge in self.edges():
            # append all the edges to the graph element
            graph.appendChild(edge.toGraphol(doc))

        # append the whole graph to the root
        root.appendChild(graph)

        return doc

    ####################################################################################################################
    #                                                                                                                  #
    #   AXIOMS COMPOSITION                                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def asymmetricRoleAxiomComposition(self, source):
        """
        Returns a collection of items to be added to the given source node to compose an asymmetric role.
        :param source: the role node source of the composition.
        :rtype: set
        """
        x1 = snapF(source.pos().x() + source.width() / 2 + 100, DiagramScene.GridSize, snap=True)
        y1 = snapF(source.pos().y() - source.height() / 2 - 40, DiagramScene.GridSize, snap=True)
        y2 = snapF(source.pos().y() - source.height() / 2 - 80, DiagramScene.GridSize, snap=True)

        node1 = RoleInverseNode(scene=self)
        node1.setPos(QPointF(x1, source.pos().y()))
        node2 = ComplementNode(scene=self)
        node2.setPos(QPointF(x1, y1))
        edge1 = InputEdge(scene=self, source=source, target=node1)
        edge2 = InputEdge(scene=self, source=node1, target=node2)
        edge3 = InclusionEdge(scene=self, source=source, target=node2, breakpoints=[
            QPointF(source.pos().x(), y2),
            QPointF(x1, y2)
        ])

        return {node1, node2, edge1, edge2, edge3}
    
    def functionalAxiomComposition(self, source):
        """
        Returns a collection of items to be added to the given source node to compose a functional axiom.
        :param source: the node source of the composition.
        :rtype: set
        """
        node1 = DomainRestrictionNode(scene=self, restriction=RestrictionType.exists)
        edge1 = InputEdge(scene=self, source=source, target=node1, functional=True)

        size = DiagramScene.GridSize

        offsets = (
            QPointF(snapF(+source.width() / 2 + 90, size), 0),
            QPointF(snapF(-source.width() / 2 - 90, size), 0),
            QPointF(0, snapF(-source.height() / 2 - 70, size)),
            QPointF(0, snapF(+source.height() / 2 + 70, size)),
            QPointF(snapF(+source.width() / 2 + 90, size), snapF(-source.height() / 2 - 70, size)),
            QPointF(snapF(-source.width() / 2 - 90, size), snapF(-source.height() / 2 - 70, size)),
            QPointF(snapF(+source.width() / 2 + 90, size), snapF(+source.height() / 2 + 70, size)),
            QPointF(snapF(-source.width() / 2 - 90, size), snapF(+source.height() / 2 + 70, size)),
        )

        pos = None
        num = sys.maxsize
        rad = QPointF(node1.width() / 2, node1.height() / 2)

        for o in offsets:
            count = len(self.items(QRectF(source.pos() + o - rad, source.pos() + o + rad)))
            if count < num:
                num = count
                pos = source.pos() + o

        node1.setPos(pos)

        return {node1, edge1}
    
    def inverseFunctionalAxiomComposition(self, source):
        """
        Returns a collection of items to be added to the given source node to compose an inverse functional axiom.
        :param source: the node source of the composition.
        :rtype: set
        """
        node1 = RangeRestrictionNode(scene=self, restriction=RestrictionType.exists)
        edge1 = InputEdge(scene=self, source=source, target=node1, functional=True)
        
        size = DiagramScene.GridSize
        
        offsets = (
            QPointF(snapF(+source.width() / 2 + 90, size), 0),
            QPointF(snapF(-source.width() / 2 - 90, size), 0),
            QPointF(0, snapF(-source.height() / 2 - 70, size)),
            QPointF(0, snapF(+source.height() / 2 + 70, size)),
            QPointF(snapF(+source.width() / 2 + 90, size), snapF(-source.height() / 2 - 70, size)),
            QPointF(snapF(-source.width() / 2 - 90, size), snapF(-source.height() / 2 - 70, size)),
            QPointF(snapF(+source.width() / 2 + 90, size), snapF(+source.height() / 2 + 70, size)),
            QPointF(snapF(-source.width() / 2 - 90, size), snapF(+source.height() / 2 + 70, size)),
        )
    
        pos = None
        num = sys.maxsize
        rad = QPointF(node1.width() / 2, node1.height() / 2)
    
        for o in offsets:
            count = len(self.items(QRectF(source.pos() + o - rad, source.pos() + o + rad)))
            if count < num:
                num = count
                pos = source.pos() + o
    
        node1.setPos(pos)

        return {node1, edge1}
        
    def irreflexiveRoleAxiomComposition(self, source):
        """
        Returns a collection of items to be added to the given source node to compose an irreflexive role.
        :param source: the role node source of the composition.
        :rtype: set
        """
        x1 = snapF(source.pos().x() + source.width() / 2 + 40, DiagramScene.GridSize, snap=True)
        x2 = snapF(source.pos().x() + source.width() / 2 + 120, DiagramScene.GridSize, snap=True)
        x3 = snapF(source.pos().x() + source.width() / 2 + 250, DiagramScene.GridSize, snap=True)

        node1 = DomainRestrictionNode(scene=self, restriction=RestrictionType.self)
        node1.setPos(QPointF(x1, source.pos().y()))
        node2 = ComplementNode(scene=self)
        node2.setPos(QPointF(x2, source.pos().y()))
        node3 = ConceptNode(scene=self, special=SpecialType.TOP)
        node3.setPos(QPointF(x3, source.pos().y()))
        edge1 = InputEdge(scene=self, source=source, target=node1)
        edge2 = InputEdge(scene=self, source=node1, target=node2)
        edge3 = InclusionEdge(scene=self, source=node3, target=node2)

        return {node1, node2, node3, edge1, edge2, edge3}

    def propertyDomainAxiomComposition(self, source):
        """
        Returns a collection of items to be added to the given source node to compose a property domain.
        :param source: the node source of the composition.
        :rtype: set
        """
        node1 = DomainRestrictionNode(scene=self, restriction=RestrictionType.exists)
        edge1 = InputEdge(scene=self, source=source, target=node1)
        
        size = DiagramScene.GridSize
        
        offsets = (
            QPointF(snapF(+source.width() / 2 + 90, size), 0),
            QPointF(snapF(-source.width() / 2 - 90, size), 0),
            QPointF(0, snapF(-source.height() / 2 - 70, size)),
            QPointF(0, snapF(+source.height() / 2 + 70, size)),
            QPointF(snapF(+source.width() / 2 + 90, size), snapF(-source.height() / 2 - 70, size)),
            QPointF(snapF(-source.width() / 2 - 90, size), snapF(-source.height() / 2 - 70, size)),
            QPointF(snapF(+source.width() / 2 + 90, size), snapF(+source.height() / 2 + 70, size)),
            QPointF(snapF(-source.width() / 2 - 90, size), snapF(+source.height() / 2 + 70, size)),
        )

        pos = None
        num = sys.maxsize
        rad = QPointF(node1.width() / 2, node1.height() / 2)

        for o in offsets:
            count = len(self.items(QRectF(source.pos() + o - rad, source.pos() + o + rad)))
            if count < num:
                num = count
                pos = source.pos() + o

        node1.setPos(pos)

        return {node1, edge1}

    def propertyRangeAxiomComposition(self, source):
        """
        Returns a collection of items to be added to the given source node to compose a property range.
        :param source: the node source of the composition.
        :rtype: set
        """
        node1 = RangeRestrictionNode(scene=self, restriction=RestrictionType.exists)
        edge1 = InputEdge(scene=self, source=source, target=node1)

        if source.isType(ItemType.AttributeNode):
            node2 = ValueDomainNode(scene=self)
            edge2 = InclusionEdge(scene=self, source=node1, target=node2)
        else:
            node2 = None
            edge2 = None

        size = DiagramScene.GridSize

        offsets = (
            (
                QPointF(snapF(+source.width() / 2 + 90, size), 0),
                QPointF(snapF(-source.width() / 2 - 90, size), 0),
                QPointF(0, snapF(-source.height() / 2 - 70, size)),
                QPointF(0, snapF(+source.height() / 2 + 70, size)),
                QPointF(snapF(+source.width() / 2 + 90, size), snapF(-source.height() / 2 - 70, size)),
                QPointF(snapF(-source.width() / 2 - 90, size), snapF(-source.height() / 2 - 70, size)),
                QPointF(snapF(+source.width() / 2 + 90, size), snapF(+source.height() / 2 + 70, size)),
                QPointF(snapF(-source.width() / 2 - 90, size), snapF(+source.height() / 2 + 70, size)),
            ),
            (
                QPointF(snapF(+node1.width() / 2 + 120, size), 0),
                QPointF(snapF(-node1.width() / 2 - 120, size), 0),
                QPointF(0, snapF(-node1.height() / 2 - 80, size)),
                QPointF(0, snapF(+node1.height() / 2 + 80, size)),
            )
        )

        pos1 = None
        pos2 = None
        num1 = sys.maxsize
        num2 = sys.maxsize
        rad1 = QPointF(node1.width() / 2, node1.height() / 2)
        rad2 = None if source.isType(ItemType.RoleNode) else QPointF(node2.width() / 2, node2.height() / 2)

        if source.isType(ItemType.RoleNode):

            for o1, o2 in itertools.product(*offsets):
                count1 = len(self.items(QRectF(source.pos() + o1 - rad1, source.pos() + o1 + rad1)))
                if count1 < num1:
                    num1 = count1
                    pos1 = source.pos() + o1

        elif source.isType(ItemType.AttributeNode):

            for o1, o2 in itertools.product(*offsets):
                count1 = len(self.items(QRectF(source.pos() + o1 - rad1, source.pos() + o1 + rad1)))
                count2 = len(self.items(QRectF(source.pos() + o1 + o2 - rad2, source.pos() + o1 + o2 + rad2)))
                if count1 + count2 < num1 + num2:
                    num1 = count1
                    num2 = count2
                    pos1 = source.pos() + o1
                    pos2 = source.pos() + o1 + o2

        node1.setPos(pos1)
        nodes = {node1}
        edges = {edge1}

        if source.isType(ItemType.AttributeNode):
            node2.setPos(pos2)
            nodes.add(node2)
            edges.add(edge2)

        return nodes | edges
            
    def reflexiveRoleAxiomComposition(self, source):
        """
        Returns a collection of items to be added to the given source node to compose a reflexive role.
        :param source: the role node source of the composition.
        :rtype: set
        """
        x1 = snapF(source.pos().x() + source.width() / 2 + 40, DiagramScene.GridSize, snap=True)
        x2 = snapF(source.pos().x() + source.width() / 2 + 250, DiagramScene.GridSize, snap=True)

        node1 = DomainRestrictionNode(scene=self, restriction=RestrictionType.self)
        node1.setPos(QPointF(x1, source.pos().y()))
        node2 = ConceptNode(scene=self, special=SpecialType.TOP)
        node2.setPos(QPointF(x2, source.pos().y()))
        edge1 = InputEdge(scene=self, source=source, target=node1)
        edge2 = InclusionEdge(scene=self, source=node2, target=node1)

        return {node1, node2, edge1, edge2}

    def symmetricRoleAxiomComposition(self, source):
        """
        Returns a collection of items to be added to the given source node to compose a symmetric role.
        :param source: the role node source of the composition.
        :rtype: set
        """
        x1 = snapF(source.pos().x() + source.width() / 2 + 100, DiagramScene.GridSize, snap=True)
        y1 = snapF(source.pos().y() - source.height() / 2 - 80, DiagramScene.GridSize, snap=True)

        node1 = RoleInverseNode(scene=self)
        node1.setPos(QPointF(x1, source.pos().y()))
        edge1 = InputEdge(scene=self, source=source, target=node1)
        edge2 = InclusionEdge(scene=self, source=source, target=node1, breakpoints=[
            QPointF(source.pos().x(), y1),
            QPointF(x1, y1)
        ])

        return {node1, edge1, edge2}
    
    def transitiveRoleAxiomComposition(self, source):
        """
        Returns a collection of items to be added to the given source node to compose a transitive role.
        :param source: the role node source of the composition.
        :rtype: set
        """
        x1 = snapF(source.pos().x() + source.width() / 2 + 90, DiagramScene.GridSize, snap=True)
        x2 = snapF(source.pos().x() + source.width() / 2 + 50, DiagramScene.GridSize, snap=True)
        x3 = snapF(source.pos().x() - source.width() / 2 - 20, DiagramScene.GridSize, snap=True)
        y1 = snapF(source.pos().y() - source.height() / 2 - 20, DiagramScene.GridSize, snap=True)
        y2 = snapF(source.pos().y() + source.height() / 2 + 20, DiagramScene.GridSize, snap=True)
        y3 = snapF(source.pos().y() - source.height() / 2 + 80, DiagramScene.GridSize, snap=True)

        node1 = RoleChainNode(scene=self)
        node1.setPos(QPointF(x1, source.pos().y()))

        edge1 = InputEdge(scene=self, source=source, target=node1, breakpoints=[
            QPointF(source.pos().x(), y1),
            QPointF(x2, y1),
        ])

        edge2 = InputEdge(scene=self, source=source, target=node1, breakpoints=[
            QPointF(source.pos().x(), y2),
            QPointF(x2, y2),
        ])

        edge3 = InclusionEdge(scene=self, source=node1, target=source, breakpoints=[
            QPointF(x1, y3),
            QPointF(x3, y3),
            QPointF(x3, source.pos().y()),
        ])

        return {node1, edge1, edge2, edge3}

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def addItem(self, item):
        """
        Add an item to the diagram scene.
        :param item: the item to add.
        """
        super().addItem(item)

        # map the item over the index matching its type
        collection = self.nodesById if item.isNode() else self.edgesById
        collection[item.id] = item

        try:
            # map the item in the nodesByLabel index if needed
            if item.isNode() and item.label.editable:
                index = item.labelText()
                if not index in self.nodesByLabel:
                    self.nodesByLabel[index] = DistinctList()
                self.nodesByLabel[index].append(item)
        except AttributeError:
            # some nodes have no label hence we don't have to index them
            pass

    def clear(self):
        """
        Clear the Diagram Scene by removing all the elements.
        """
        self.edgesById.clear()
        self.nodesById.clear()
        self.nodesByLabel.clear()
        self.undostack.clear()
        super().clear()

    def edge(self, eid):
        """
        Returns the edge matching the given node id.
        :param eid: the edge id.
        :raise KeyError: if there is no such edge in the diagram.
        """
        return self.edgesById[eid]

    def edges(self):
        """
        Returns a view on all the edges of the diagram.
        :rtype: view
        """
        return self.edgesById.values()

    def itemOnTopOf(self, point, nodes=True, edges=True, skip=None):
        """
        Returns the shape which is on top of the given point.
        :type point: QPointF
        :type nodes: bool
        :type edges: bool
        :type skip: iterable
        :param point: the graphic point of the scene from where to pick items.
        :param nodes: whether to include nodes in our search.
        :param edges: whether to include edges in our search.
        :param skip: a collection of items to be excluded from the search.
        :rtype: Item
        """
        skip = skip or {}
        data = [x for x in self.items(point) if (nodes and x.isNode() or edges and x.isEdge()) and x not in skip]
        if data:
            return max(data, key=lambda x: x.zValue())
        return None

    def node(self, nid):
        """
        Returns the node matching the given node id.
        :param nid: the node id.
        :raise KeyError: if there is no such node in the diagram.
        """
        return self.nodesById[nid]

    def nodes(self):
        """
        Returns a view on all the nodes in the diagram
        :rtype: view
        """
        return self.nodesById.values()

    def removeItem(self, item):
        """
        Remove an item from the Diagram scene.
        :param item: the item to remove.
        """
        super().removeItem(item)

        # remove the item from the index matching its type
        collection = self.nodesById if item.isNode() else self.edgesById
        collection.pop(item.id, None)

        try:
            # remove the item from the nodesByLabel index if needed
            if item.isNode() and item.label.editable:
                index = item.labelText()
                if index in self.nodesByLabel:
                    self.nodesByLabel[index].remove(item)
                    if not self.nodesByLabel[index]:
                        del self.nodesByLabel[index]
        except AttributeError:
            # some nodes have no label hence we don't have to index them
            pass

    def selectedEdges(self):
        """
        Returns the edges selected in the scene.
        :rtype: list
        """
        return [x for x in self.selectedItems() if x.isEdge()]

    def selectedItems(self):
        """
        Returns the items selected in the scene (will filter out labels since we don't need them).
        :rtype: list
        """
        return [x for x in super().selectedItems() if x.isNode() or x.isEdge()]

    def selectedNodes(self):
        """
        Returns the nodes selected in the scene.
        :rtype: list
        """
        return [x for x in self.selectedItems() if x.isNode()]

    def setMode(self, mode, param=None):
        """
        Set the operation mode.
        :param mode: the operation mode.
        :param param: the mode parameter (if any).
        """
        if self.mode != mode or self.modeParam != param:
            self.mode = mode
            self.modeParam = param
            self.modeChanged.emit(mode)

    def snapToGrid(self, point):
        """
        Snap the shape position to the grid.
        :type point: QPointF
        :param point: the position of the shape.
        :return: the position of the shape snapped to the grid if the feature is enabled.
        :rtype: QPointF
        """
        if self.settings.value('scene/snap_to_grid', False, bool):
            newX = snapF(point.x(), DiagramScene.GridSize)
            newY = snapF(point.y(), DiagramScene.GridSize)
            return QPointF(newX, newY)
        else:
            return point

    def visibleRect(self, margin=0):
        """
        Returns a rectangle matching the area of visible items.
        Will return None if there is no item in the diagram.
        :param margin: extra margin to be added to the sides of the rectangle.
        :rtype: QRectF
        """
        items = self.items()
        if items:

            X = set()
            Y = set()
            for item in items:
                B = item.mapRectToScene(item.boundingRect())
                X |= {B.left(), B.right()}
                Y |= {B.top(), B.bottom()}

            return QRectF(QPointF(min(X) - margin, min(Y) - margin), QPointF(max(X) + margin, max(Y) + margin))

        return None