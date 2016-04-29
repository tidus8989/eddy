# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
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
#  #####################                          #####################  #
#                                                                        #
#  Graphol is developed by members of the DASI-lab group of the          #
#  Dipartimento di Ingegneria Informatica, Automatica e Gestionale       #
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it  #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from abc import ABCMeta, abstractmethod

from PyQt5.QtCore import pyqtSlot, Qt, QEvent, QSize
from PyQt5.QtGui import QBrush, QColor, QPainter
from PyQt5.QtWidgets import QFormLayout, QSizePolicy, QLabel, QVBoxLayout
from PyQt5.QtWidgets import QWidget, QPushButton, QMenu, QScrollArea
from PyQt5.QtWidgets import QStackedWidget, QStyle, QStyleOption

from eddy.core.commands.common import CommandRefactor
from eddy.core.commands.common import CommandSetProperty
from eddy.core.commands.nodes import CommandNodeLabelChange
from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.datatypes.owl import Facet, XsdDatatype
from eddy.core.functions.misc import first, isEmpty, clamp
from eddy.core.functions.signals import connect, disconnect
from eddy.core.qt import ColoredIcon, Font
from eddy.core.regex import RE_CAMEL_SPACE

from eddy.lang import gettext as _

from eddy.ui.fields import IntegerField, StringField, CheckBox, ComboBox


class Info(QScrollArea):
    """
    This class implements the information box.
    """
    Width = 216

    def __init__(self, parent):
        """
        Initialize the info box.
        :type parent: MainWindow
        """
        super().__init__(parent)
        self.diagram = None
        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumSize(QSize(216, 120))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.stacked = QStackedWidget(self)
        self.stacked.setContentsMargins(0, 0, 0, 0)
        self.infoEmpty = QWidget(self.stacked)
        self.infoDiagram = DiagramInfo(parent, self.stacked)
        self.infoEdge = EdgeInfo(parent, self.stacked)
        self.infoInclusionEdge = InclusionEdgeInfo(parent, self.stacked)
        self.infoNode = NodeInfo(parent, self.stacked)
        self.infoPredicateNode = PredicateNodeInfo(parent, self.stacked)
        self.infoEditableNode = EditableNodeInfo(parent, self.stacked)
        self.infoAttributeNode = AttributeNodeInfo(parent, self.stacked)
        self.infoRoleNode = RoleNodeInfo(parent, self.stacked)
        self.infoValueNode = ValueNodeInfo(parent, self.stacked)
        self.infoValueDomainNode = ValueDomainNodeInfo(parent, self.stacked)
        self.infoValueRestrictionNode = ValueRestrictionNodeInfo(parent, self.stacked)
        self.stacked.addWidget(self.infoEmpty)
        self.stacked.addWidget(self.infoDiagram)
        self.stacked.addWidget(self.infoEdge)
        self.stacked.addWidget(self.infoInclusionEdge)
        self.stacked.addWidget(self.infoNode)
        self.stacked.addWidget(self.infoPredicateNode)
        self.stacked.addWidget(self.infoEditableNode)
        self.stacked.addWidget(self.infoAttributeNode)
        self.stacked.addWidget(self.infoRoleNode)
        self.stacked.addWidget(self.infoValueNode)
        self.stacked.addWidget(self.infoValueDomainNode)
        self.stacked.addWidget(self.infoValueRestrictionNode)
        self.setWidget(self.stacked)
        self.setWidgetResizable(True)
        scrollbar = self.verticalScrollBar()
        scrollbar.installEventFilter(self)
        self.stack()

    #############################################
    #   EVENTS
    #################################

    def eventFilter(self, source, event):
        """
        Filter incoming events.
        :type source: QObject
        :type event: QEvent
        """
        if source is self.verticalScrollBar():
            if event.type() in {QEvent.Show, QEvent.Hide}:
                self.redraw()
        return super().eventFilter(source, event)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def stack(self):
        """
        Set the current stacked widget.
        """
        if self.diagram:
            selected = self.diagram.selectedItems()
            if not selected or len(selected) > 1:
                show = self.infoDiagram
                show.updateData(self.diagram)
            else:
                item = first(selected)
                if item.isNode():
                    if item.isPredicate():
                        if item.type() is Item.ValueDomainNode:
                            show = self.infoValueDomainNode
                        elif item.type() is Item.ValueRestrictionNode:
                            show = self.infoValueRestrictionNode
                        elif item.type() is Item.RoleNode:
                            show = self.infoRoleNode
                        elif item.type() is Item.AttributeNode:
                            show = self.infoAttributeNode
                        elif item.type() is Item.IndividualNode and item.identity is Identity.Value:
                            show = self.infoValueNode
                        elif item.label.editable:
                            show = self.infoEditableNode
                        else:
                            show = self.infoPredicateNode
                    else:
                        show = self.infoNode
                else:
                    if item.type() is Item.InclusionEdge:
                        show = self.infoInclusionEdge
                    else:
                        show = self.infoEdge
                show.updateData(item)
        else:
            show = self.infoEmpty

        prev = self.stacked.currentWidget()
        self.stacked.setCurrentWidget(show)
        self.redraw()
        if prev is not show:
            scrollbar = self.verticalScrollBar()
            scrollbar.setValue(0)

    #############################################
    #   INTERFACE
    #################################

    def browse(self, diagram):
        """
        Set the widget to inspect the given diagram.
        :type diagram: Diagram
        """
        self.reset()

        if diagram:
            self.diagram = diagram
            connect(self.diagram.selectionChanged, self.stack)
            connect(self.diagram.sgnItemAdded, self.stack)
            connect(self.diagram.sgnItemRemoved, self.stack)
            connect(self.diagram.sgnUpdated, self.stack)
            self.stack()

    def redraw(self):
        """
        Redraw the content of the widget.
        """

        width = self.width()
        scrollbar = self.verticalScrollBar()
        if scrollbar.isVisible():
            width -= scrollbar.width()

        widget = self.stacked.currentWidget()
        widget.setFixedWidth(width)
        self.stacked.setFixedWidth(width)

        sizeHint = widget.sizeHint()
        height = sizeHint.height()
        self.stacked.setFixedHeight(clamp(height, 0))

    def reset(self):
        """
        Clear the widget from inspecting the current diagram.
        """
        if self.diagram:

            try:
                disconnect(self.diagram.selectionChanged, self.stack)
                disconnect(self.diagram.sgnItemAdded, self.stack)
                disconnect(self.diagram.sgnItemRemoved, self.stack)
                disconnect(self.diagram.sgnUpdated, self.stack)
            except RuntimeError:
                pass
            finally:
                self.diagram = None

        self.stack()


#############################################
#   COMPONENTS
#################################


class Header(QLabel):
    """
    This class implements the header of properties section.
    """
    def __init__(self, *args):
        """
        Initialize the header.
        """
        super().__init__(*args)
        self.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.setFixedHeight(24)


class Key(QLabel):
    """
    This class implements the key of an info field.
    """
    def __init__(self, *args):
        """
        Initialize the key.
        """
        super().__init__(*args)
        self.setFixedSize(88, 20)


class Button(QPushButton):
    """
    This class implements the button to which associate a QMenu instance of an info field.
    """
    def __init__(self,  *args):
        """
        Initialize the button.
        """
        super().__init__(*args)


class Integer(IntegerField):
    """
    This class implements the integer value of an info field.
    """
    def __init__(self,  *args):
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setFixedHeight(20)


class String(StringField):
    """
    This class implements the string value of an info field.
    """
    def __init__(self,  *args):
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setFixedHeight(20)


class Select(ComboBox):
    """
    This class implements the selection box of an info field.
    """
    def __init__(self,  *args):
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setScrollEnabled(False)


class Parent(QWidget):
    """
    This class implements the parent placeholder to be used to store checkbox and radio button value fields.
    """
    def __init__(self,  *args):
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setFixedHeight(20)

    def paintEvent(self, paintEvent):
        """
        This is needed for the widget to pick the stylesheet.
        :type paintEvent: QPaintEvent
        """
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)


#############################################
#   INFO WIDGETS
#################################


class AbstractInfo(QWidget):
    """
    This class implements the base information box.
    """
    __metaclass__ = ABCMeta

    def __init__(self, mainwindow, parent=None):
        """
        Initialize the base information box.
        :type mainwindow: MainWindow
        :type parent: QWidget
        """
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.mainwindow = mainwindow

    @abstractmethod
    def updateData(self, **kwargs):
        """
        Fetch new information and fill the widget with data.
        """
        pass


class DiagramInfo(AbstractInfo):
    """
    This class implements the diagram scene information box.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the diagram scene information box.
        :type mainwindow: MainWindow
        :type parent: QWidget
        """
        super().__init__(mainwindow, parent)

        arial12r = Font('Arial', 12)

        self.conceptsKey = Key(_('INFO_KEY_CONCEPT'), self)
        self.conceptsKey.setFont(arial12r)
        self.conceptsField = Integer(self)
        self.conceptsField.setFont(arial12r)
        self.conceptsField.setReadOnly(True)

        self.rolesKey = Key(_('INFO_KEY_ROLE'), self)
        self.rolesKey.setFont(arial12r)
        self.rolesField = Integer(self)
        self.rolesField.setFont(arial12r)
        self.rolesField.setReadOnly(True)

        self.attributesKey = Key(_('INFO_KEY_ATTRIBUTE'), self)
        self.attributesKey.setFont(arial12r)
        self.attributesField = Integer(self)
        self.attributesField.setFont(arial12r)
        self.attributesField.setReadOnly(True)

        self.inclusionsKey = Key(_('INFO_KEY_INCLUSION'), self)
        self.inclusionsKey.setFont(arial12r)
        self.inclusionsField = Integer(self)
        self.inclusionsField.setFont(arial12r)
        self.inclusionsField.setReadOnly(True)

        self.membershipKey = Key(_('INFO_KEY_MEMBERSHIP'), self)
        self.membershipKey.setFont(arial12r)
        self.membershipField = Integer(self)
        self.membershipField.setFont(arial12r)
        self.membershipField.setReadOnly(True)

        self.atomicPredHeader = Header(_('INFO_HEADER_ATOMIC_PREDICATES'), self)
        self.atomicPredHeader.setFont(arial12r)

        self.atomicPredLayout = QFormLayout()
        self.atomicPredLayout.setSpacing(0)
        self.atomicPredLayout.addRow(self.conceptsKey, self.conceptsField)
        self.atomicPredLayout.addRow(self.rolesKey, self.rolesField)
        self.atomicPredLayout.addRow(self.attributesKey, self.attributesField)

        self.assertionsHeader = Header(_('INFO_HEADER_ASSERTIONS'), self)
        self.assertionsHeader.setFont(arial12r)

        self.assertionsLayout = QFormLayout()
        self.assertionsLayout.setSpacing(0)
        self.assertionsLayout.addRow(self.inclusionsKey, self.inclusionsField)
        self.assertionsLayout.addRow(self.membershipKey, self.membershipField)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setAlignment(Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.atomicPredHeader)
        self.mainLayout.addLayout(self.atomicPredLayout)
        self.mainLayout.addWidget(self.assertionsHeader)
        self.mainLayout.addLayout(self.assertionsLayout)

    def updateData(self, diagram):
        """
        Fetch new information and fill the widget with data.
        :type diagram: Diagram
        """
        count = diagram.project.count
        self.attributesField.setValue(count(predicate=Item.AttributeNode))
        self.conceptsField.setValue(count(predicate=Item.ConceptNode))
        self.rolesField.setValue(count(predicate=Item.RoleNode))
        self.inclusionsField.setValue(count(item=Item.InclusionEdge))
        self.membershipField.setValue(count(item=Item.MembershipEdge))


class EdgeInfo(AbstractInfo):
    """
    This class implements the information box for generic edges.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the generic edge information box.
        :type mainwindow: MainWindow
        :type parent: QWidget
        """
        super().__init__(mainwindow, parent)

        arial12r = Font('Arial', 12)

        self.h1 = Header(_('INFO_HEADER_GENERAL'), self)
        self.h1.setFont(arial12r)

        self.typeKey = Key(_('INFO_KEY_TYPE'), self)
        self.typeKey.setFont(arial12r)
        self.typeField = String(self)
        self.typeField.setFont(arial12r)
        self.typeField.setReadOnly(True)

        self.sourceKey = Key(_('INFO_KEY_SOURCE'), self)
        self.sourceKey.setFont(arial12r)
        self.sourceField = String(self)
        self.sourceField.setFont(arial12r)
        self.sourceField.setReadOnly(True)

        self.targetKey = Key(_('INFO_KEY_TARGET'), self)
        self.targetKey.setFont(arial12r)
        self.targetField = String(self)
        self.targetField.setFont(arial12r)
        self.targetField.setReadOnly(True)

        self.generalLayout = QFormLayout()
        self.generalLayout.setSpacing(0)
        self.generalLayout.addRow(self.typeKey, self.typeField)
        self.generalLayout.addRow(self.sourceKey, self.sourceField)
        self.generalLayout.addRow(self.targetKey, self.targetField)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setAlignment(Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.h1)
        self.mainLayout.addLayout(self.generalLayout)

    def updateData(self, edge):
        """
        Fetch new information and fill the widget with data.
        :type edge: AbstractEdge
        """
        self.sourceField.setValue(edge.source.id)
        self.targetField.setValue(edge.target.id)
        self.typeField.setValue(edge.shortname.capitalize())
        self.typeField.home(True)
        self.typeField.deselect()


class InclusionEdgeInfo(EdgeInfo):
    """
    This class implements the information box for inclusion edges.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the inclusion edge information box.
        :type mainwindow: MainWindow
        :type parent: QWidget
        """
        super().__init__(mainwindow, parent)

        arial12r = Font('Arial', 12)

        self.completeKey = Key(_('INFO_KEY_COMPLETE'), self)
        self.completeKey.setFont(arial12r)
        parent = Parent(self)
        self.completeBox = CheckBox(parent)
        self.completeBox.setFont(arial12r)
        self.completeBox.setCheckable(True)
        connect(self.completeBox.clicked, self.mainwindow.doToggleEdgeComplete)

        self.generalLayout.addRow(self.completeKey, parent)

    def updateData(self, edge):
        """
        Fetch new information and fill the widget with data.
        :type edge: InclusionEdge
        """
        super().updateData(edge)
        self.completeBox.setChecked(edge.complete)


class NodeInfo(AbstractInfo):
    """
    This class implements the information box for generic nodes.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the generic node information box.
        :type mainwindow: MainWindow
        :type parent: QWidget
        """
        super().__init__(mainwindow, parent)

        arial12r = Font('Arial', 12)

        self.node = None

        self.idKey = Key(_('INFO_KEY_ID'), self)
        self.idKey.setFont(arial12r)
        self.idField = String(self)
        self.idField.setFont(arial12r)
        self.idField.setReadOnly(True)

        self.identityKey = Key(_('INFO_KEY_IDENTITY'), self)
        self.identityKey.setFont(arial12r)
        self.identityField = String(self)
        self.identityField.setFont(arial12r)
        self.identityField.setReadOnly(True)

        self.nodePropHeader = Header(_('INFO_HEADER_NODE_PROPERTIES'), self)
        self.nodePropHeader.setFont(arial12r)
        self.nodePropLayout = QFormLayout()
        self.nodePropLayout.setSpacing(0)
        self.nodePropLayout.addRow(self.idKey, self.idField)
        self.nodePropLayout.addRow(self.identityKey, self.identityField)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setAlignment(Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.nodePropHeader)
        self.mainLayout.addLayout(self.nodePropLayout)

    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        self.idField.setValue(node.id)
        self.identityField.setValue(node.identity.value)
        self.node = node


class PredicateNodeInfo(NodeInfo):
    """
    This class implements the information box for predicate nodes.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the predicate node information box.
        """
        super().__init__(mainwindow, parent)

        arial12r = Font('Arial', 12)

        self.brushKey = Key(_('INFO_KEY_COLOR'), self)
        self.brushKey.setFont(arial12r)
        self.brushMenu = QMenu(self)
        self.brushButton = Button()
        self.brushButton.setFont(arial12r)
        self.brushButton.setMenu(self.brushMenu)
        self.brushButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.nodePropLayout.addRow(self.brushKey, self.brushButton)

    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        super().updateData(node)
        # CONFIGURE MENU
        if self.brushMenu.isEmpty():
            self.brushMenu.addActions(self.mainwindow.actionsSetBrush)
        # SELECT CURRENT BRUSH
        for action in self.mainwindow.actionsSetBrush:
            color = action.data()
            brush = QBrush(QColor(color.value))
            if node.brush == brush:
                self.brushButton.setIcon(ColoredIcon(12, 12, color.value, '#000000'))
                self.brushButton.setText(color.value)
                break


class EditableNodeInfo(PredicateNodeInfo):
    """
    This class implements the information box for the predicate nodes with editable label.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the editable node information box.
        """
        super().__init__(mainwindow, parent)

        arial12r = Font('Arial', 12)

        self.textKey = Key(_('INFO_KEY_LABEL'), self)
        self.textKey.setFont(arial12r)
        self.textField = String(self)
        self.textField.setFont(arial12r)
        self.textField.setReadOnly(False)
        connect(self.textField.editingFinished, self.editingFinished)

        self.nameKey = Key(_('INFO_KEY_NAME'), self)
        self.nameKey.setFont(arial12r)
        self.nameField = String(self)
        self.nameField.setFont(arial12r)
        self.nameField.setReadOnly(False)
        connect(self.nameField.editingFinished, self.editingFinished)

        self.predPropHeader = Header(_('INFO_HEADER_PREDICATE_PROPERTIES'), self)
        self.nodePropHeader.setFont(arial12r)
        self.predPropLayout = QFormLayout()
        self.predPropLayout.setSpacing(0)

        self.nodePropLayout.insertRow(2, self.textKey, self.textField)
        self.predPropLayout.addRow(self.nameKey, self.nameField)

        self.mainLayout.insertWidget(0, self.predPropHeader)
        self.mainLayout.insertLayout(1, self.predPropLayout)

    @pyqtSlot()
    def editingFinished(self):
        """
        Executed whenever we finish to edit the predicate/node name.
        """
        if self.node:

            try:
                sender = self.sender()
                node = self.node
                data = sender.value()
                data = data if not isEmpty(data) else node.label.template
                if data != node.text():
                    diagram = node.diagram
                    if sender is self.nameField:
                        collection = []
                        for n in diagram.project.predicates(node.type(), node.text()):
                            collection.append(CommandNodeLabelChange(n.diagram, n, n.text(), data))
                        command = CommandRefactor(_('COMMAND_NODE_REFACTOR_NAME', node.text(), data), collection)
                        diagram.undoStack.push(command)
                    else:
                        command = CommandNodeLabelChange(diagram, node, node.text(), data)
                        diagram.undoStack.push(command)
            except RuntimeError:
                pass

    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        super().updateData(node)
        self.nameField.setValue(node.text())
        self.textField.setValue(node.text())


class AttributeNodeInfo(EditableNodeInfo):
    """
    This class implements the information box for the Attribute node.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the Attribute node information box.
        """
        super().__init__(mainwindow, parent)

        arial12r = Font('Arial', 12)

        self.functKey = Key(_('INFO_KEY_FUNCTIONAL'), self)
        self.functKey.setFont(arial12r)
        functParent = Parent(self)
        self.functBox = CheckBox(functParent)
        self.functBox.setCheckable(True)
        self.functBox.setFont(arial12r)
        self.functBox.setProperty('attribute', 'functional')
        connect(self.functBox.clicked, self.flagChanged)

        self.predPropLayout.addRow(self.functKey, functParent)

    @pyqtSlot()
    def flagChanged(self):
        """
        Executed whenever one of the property fields changes.
        """
        node = self.node
        sender = self.sender()
        checked = sender.isChecked()
        diagram = node.diagram
        attribute = sender.property('attribute')
        name = _('COMMAND_ITEM_SET_PROPERTY', 'un' if checked else '', node.shortname, attribute)
        data = {'attribute': attribute, 'undo': getattr(node, attribute), 'redo': checked}
        diagram.undoStack.push(CommandSetProperty(diagram, node, data, name))

    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        super().updateData(node)
        self.functBox.setChecked(node.functional)


class RoleNodeInfo(EditableNodeInfo):
    """
    This class implements the information box for the Role node.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the Role node information box.
        """
        super().__init__(mainwindow, parent)

        arial12r = Font('Arial', 12)

        self.functKey = Key(_('INFO_KEY_FUNCTIONAL'), self)
        self.functKey.setFont(arial12r)
        functParent = Parent(self)
        self.functBox = CheckBox(functParent)
        self.functBox.setCheckable(True)
        self.functBox.setFont(arial12r)
        self.functBox.setProperty('attribute', 'functional')
        connect(self.functBox.clicked, self.flagChanged)

        self.invFunctKey = Key(_('INFO_KEY_INVERSE_FUNCTIONAL'), self)
        self.invFunctKey.setFont(arial12r)
        invFunctParent = Parent(self)
        self.invFunctBox = CheckBox(invFunctParent)
        self.invFunctBox.setCheckable(True)
        self.invFunctBox.setFont(arial12r)
        self.invFunctBox.setProperty('attribute', 'inverseFunctional')
        connect(self.invFunctBox.clicked, self.flagChanged)

        self.asymmetricKey = Key(_('INFO_KEY_ASYMMETRIC'), self)
        self.asymmetricKey.setFont(arial12r)
        asymmetricParent = Parent(self)
        self.asymmetricBox = CheckBox(asymmetricParent)
        self.asymmetricBox.setCheckable(True)
        self.asymmetricBox.setFont(arial12r)
        self.asymmetricBox.setProperty('attribute', 'asymmetric')
        connect(self.asymmetricBox.clicked, self.flagChanged)

        self.irreflexiveKey = Key(_('INFO_KEY_IRREFLEXIVE'), self)
        self.irreflexiveKey.setFont(arial12r)
        irreflexiveParent = Parent(self)
        self.irreflexiveBox = CheckBox(irreflexiveParent)
        self.irreflexiveBox.setCheckable(True)
        self.irreflexiveBox.setFont(arial12r)
        self.irreflexiveBox.setProperty('attribute', 'irreflexive')
        connect(self.irreflexiveBox.clicked, self.flagChanged)

        self.reflexiveKey = Key(_('INFO_KEY_REFLEXIVE'), self)
        self.reflexiveKey.setFont(arial12r)
        reflexiveParent = Parent(self)
        self.reflexiveBox = CheckBox(reflexiveParent)
        self.reflexiveBox.setCheckable(True)
        self.reflexiveBox.setFont(arial12r)
        self.reflexiveBox.setProperty('attribute', 'reflexive')
        connect(self.reflexiveBox.clicked, self.flagChanged)

        self.symmetricKey = Key(_('INFO_KEY_SYMMETRIC'), self)
        self.symmetricKey.setFont(arial12r)
        symmetricParent = Parent(self)
        self.symmetricBox = CheckBox(symmetricParent)
        self.symmetricBox.setCheckable(True)
        self.symmetricBox.setFont(arial12r)
        self.symmetricBox.setProperty('attribute', 'symmetric')
        connect(self.symmetricBox.clicked, self.flagChanged)

        self.transitiveKey = Key(_('INFO_KEY_TRANSITIVE'), self)
        self.transitiveKey.setFont(arial12r)
        transitiveParent = Parent(self)
        self.transitiveBox = CheckBox(transitiveParent)
        self.transitiveBox.setCheckable(True)
        self.transitiveBox.setFont(arial12r)
        self.transitiveBox.setProperty('attribute', 'transitive')
        connect(self.transitiveBox.clicked, self.flagChanged)

        self.predPropLayout.addRow(self.functKey, functParent)
        self.predPropLayout.addRow(self.invFunctKey, invFunctParent)
        self.predPropLayout.addRow(self.asymmetricKey, asymmetricParent)
        self.predPropLayout.addRow(self.irreflexiveKey, irreflexiveParent)
        self.predPropLayout.addRow(self.reflexiveKey, reflexiveParent)
        self.predPropLayout.addRow(self.symmetricKey, symmetricParent)
        self.predPropLayout.addRow(self.transitiveKey, transitiveParent)

    @pyqtSlot()
    def flagChanged(self):
        """
        Executed whenever one of the property fields changes.
        """
        node = self.node
        sender = self.sender()
        checked = sender.isChecked()
        diagram = node.diagram
        attribute = sender.property('attribute')
        prop = RE_CAMEL_SPACE.sub('\g<1> \g<2>', attribute).lower()
        name = _('COMMAND_ITEM_SET_PROPERTY', 'un' if checked else '', node.shortname, prop)
        data = {'attribute': attribute, 'undo': getattr(node, attribute), 'redo': checked}
        diagram.undoStack.push(CommandSetProperty(diagram, node, data, name))

    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        super().updateData(node)
        self.asymmetricBox.setChecked(node.asymmetric)
        self.functBox.setChecked(node.functional)
        self.invFunctBox.setChecked(node.inverseFunctional)
        self.irreflexiveBox.setChecked(node.irreflexive)
        self.reflexiveBox.setChecked(node.reflexive)
        self.symmetricBox.setChecked(node.symmetric)
        self.transitiveBox.setChecked(node.transitive)


class ValueDomainNodeInfo(PredicateNodeInfo):
    """
    This class implements the information box for the Value Domain node.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the Value Domain node information box.
        """
        super().__init__(mainwindow, parent)

        arial12r = Font('Arial', 12)

        self.datatypeKey = Key(_('INFO_KEY_DATATYPE'), self)
        self.datatypeKey.setFont(arial12r)
        self.datatypeMenu = QMenu(self)
        self.datatypeButton = Button()
        self.datatypeButton.setFont(arial12r)
        self.datatypeButton.setMenu(self.datatypeMenu)
        self.datatypeButton.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        self.nodePropLayout.addRow(self.datatypeKey, self.datatypeButton)

    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        super().updateData(node)
        # CONFIGURE MENU
        if self.datatypeMenu.isEmpty():
            self.datatypeMenu.addActions(self.mainwindow.actionsSetDatatype)
        # SELECT CURRENT DATATYPE
        datatype = node.datatype
        for action in self.mainwindow.actionsSetDatatype:
            action.setChecked(action.data() is datatype)
        self.datatypeButton.setText(datatype.value)


class ValueRestrictionNodeInfo(PredicateNodeInfo):
    """
    This class implements the information box for the Value Restriction node.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the Value Restriction node information box.
        """
        super().__init__(mainwindow, parent)

        arial12r = Font('Arial', 12)

        self.datatypeKey = Key(_('INFO_KEY_DATATYPE'), self)
        self.datatypeKey.setFont(arial12r)
        self.datatypeField = Select(self)
        self.datatypeField.setFont(arial12r)
        connect(self.datatypeField.activated, self.restrictionChanged)

        self.facetKey = Key(_('INFO_KEY_FACET'), self)
        self.facetKey.setFont(arial12r)
        self.facetField = Select(self)
        self.facetField.setFont(arial12r)
        connect(self.facetField.activated, self.restrictionChanged)

        self.restrictionKey = Key(_('INFO_KEY_RESTRICTION'), self)
        self.restrictionKey.setFont(arial12r)
        self.restrictionField = String(self)
        self.restrictionField.setFont(arial12r)
        self.restrictionField.setReadOnly(False)
        connect(self.restrictionField.editingFinished, self.restrictionChanged)

        for datatype in XsdDatatype:
            if Facet.forDatatype(datatype):
                self.datatypeField.addItem(datatype.value, datatype)

        self.nodePropLayout.addRow(self.datatypeKey, self.datatypeField)
        self.nodePropLayout.addRow(self.facetKey, self.facetField)
        self.nodePropLayout.addRow(self.restrictionKey, self.restrictionField)

    @pyqtSlot()
    def restrictionChanged(self):
        """
        Executed when we need to recompute the restriction of the node.
        """
        if self.node:

            try:
                node = self.node
                diagram = node.diagram
                datatype = self.datatypeField.currentData()
                facet = self.facetField.currentData()
                value = self.restrictionField.value()
                allowed = Facet.forDatatype(datatype)
                if facet not in allowed:
                    facet = first(allowed)
                data = node.compose(facet, value, datatype)
                if node.text() != data:
                    name = _('COMMAND_NODE_SET_VALUE_RESTRICTION', data)
                    diagram.undoStack.push(CommandNodeLabelChange(diagram, node, node.text(), data, name))
            except RuntimeError:
                pass

    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        super().updateData(node)

        datatype = node.datatype
        for i in range(self.datatypeField.count()):
            if self.datatypeField.itemData(i) is datatype:
                self.datatypeField.setCurrentIndex(i)
                break

        self.datatypeField.setEnabled(not node.constrained)

        self.facetField.clear()
        for facet in Facet.forDatatype(datatype):
            self.facetField.addItem(facet.value, facet)

        facet = node.facet
        for i in range(self.facetField.count()):
            if self.facetField.itemData(i) is facet:
                self.facetField.setCurrentIndex(i)
                break
        else:
            self.facetField.setCurrentIndex(0)

        self.restrictionField.setValue(node.value)


class ValueNodeInfo(PredicateNodeInfo):
    """
    This class implements the information box for the Individual node with identity 'Value'.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the Value node information box.
        """
        super().__init__(mainwindow, parent)

        arial12r = Font('Arial', 12)

        self.datatypeKey = Key(_('INFO_KEY_DATATYPE'), self)
        self.datatypeKey.setFont(arial12r)
        self.datatypeField = Select(self)
        self.datatypeField.setFont(arial12r)
        connect(self.datatypeField.activated, self.valueChanged)

        self.valueKey = Key(_('INFO_KEY_VALUE'), self)
        self.valueKey.setFont(arial12r)
        self.valueField = String(self)
        self.valueField.setFont(arial12r)
        self.valueField.setReadOnly(False)
        connect(self.valueField.editingFinished, self.valueChanged)

        for datatype in XsdDatatype:
            if Facet.forDatatype(datatype):
                self.datatypeField.addItem(datatype.value, datatype)

        self.nodePropLayout.addRow(self.datatypeKey, self.datatypeField)
        self.nodePropLayout.addRow(self.valueKey, self.valueField)

    @pyqtSlot()
    def valueChanged(self):
        """
        Executed when we need to recompute the Value.
        """
        if self.node:

            try:
                node = self.node
                diagram = node.diagram
                datatype = self.datatypeField.currentData()
                value = self.valueField.value()
                data = node.composeValue(value, datatype)
                if node.text() != data:
                    name = _('COMMAND_NODE_SET_VALUE', data)
                    diagram.undoStack.push(CommandNodeLabelChange(diagram, node, node.text(), data, name))
            except RuntimeError:
                pass

    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        super().updateData(node)

        datatype = node.datatype
        for i in range(self.datatypeField.count()):
            if self.datatypeField.itemData(i) is datatype:
                self.datatypeField.setCurrentIndex(i)
                break

        self.valueField.setValue(node.value)