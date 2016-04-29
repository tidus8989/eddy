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


import os

from traceback import format_exception

from PyQt5.QtCore import Qt, pyqtSlot, QRectF, QSettings
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QFrame, QLabel, QMessageBox
from PyQt5.QtWidgets import QWidget, QDialogButtonBox

from eddy import ORGANIZATION, APPNAME
from eddy.core.datatypes.system import File
from eddy.core.diagram import Diagram
from eddy.core.exporters.graphol import GrapholExporter
from eddy.core.functions.fsystem import isdir
from eddy.core.functions.misc import cutR, isEmpty
from eddy.core.functions.path import isPathValid, shortPath, expandPath
from eddy.core.functions.signals import connect
from eddy.core.project import Project
from eddy.core.qt import Font
from eddy.lang import gettext as _
from eddy.ui.fields import StringField


class NewDiagramDialog(QDialog):
    """
    This class is used to display a modal window used to create a new diagram.
    """
    def __init__(self, project, parent=None):
        """
        Initialize the new diagram dialog.
        :type project: Project
        :type parent: QWidget
        """
        super().__init__(parent)

        arial12r = Font('Arial', 12)

        #############################################
        # FORM AREA
        #################################

        self.project = project
        self.projectPath = shortPath(project.path)
        self.projectPath = '{0}{1}'.format(cutR(self.projectPath, os.path.sep), os.path.sep)

        self.nameLabel = QLabel(self)
        self.nameLabel.setFont(arial12r)
        self.nameLabel.setText(_('DIAGRAM_NAME_LABEL'))
        self.nameField = StringField(self)
        self.nameField.setFont(arial12r)
        self.nameField.setMinimumWidth(400)
        self.nameField.setMaxLength(64)
        connect(self.nameField.textChanged, self.onNameFieldChanged)
        connect(self.nameField.textChanged, self.doDiagramPathValidate)

        self.pathLabel = QLabel(self)
        self.pathLabel.setFont(arial12r)
        self.pathLabel.setText(_('DIAGRAM_LOCATION_LABEL'))
        self.pathField = StringField(self)
        self.pathField.setFont(arial12r)
        self.pathField.setMinimumWidth(400)
        self.pathField.setReadOnly(True)
        self.pathField.setFocusPolicy(Qt.NoFocus)
        self.pathField.setValue(self.projectPath)

        spacer = QFrame()
        spacer.setFrameShape(QFrame.HLine)
        spacer.setFrameShadow(QFrame.Sunken)

        self.formWidget = QWidget(self)
        self.formLayout = QFormLayout(self.formWidget)
        self.formLayout.addRow(self.nameLabel, self.nameField)
        self.formLayout.addWidget(spacer)
        self.formLayout.addRow(self.pathLabel, self.pathField)

        #############################################
        # CONFIRMATION AREA
        #################################

        self.confirmationBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.confirmationBox.setContentsMargins(10, 0, 10, 10)
        self.confirmationBox.setFont(arial12r)
        self.confirmationBox.button(QDialogButtonBox.Ok).setEnabled(False)

        #############################################
        # SETUP DIALOG LAYOUT
        #################################

        self.caption = QLabel(self)
        self.caption.setContentsMargins(8, 0, 8, 0)
        self.caption.setProperty('class', 'invalid')
        self.caption.setVisible(False)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.formWidget)
        self.mainLayout.addWidget(self.caption)
        self.mainLayout.addWidget(self.confirmationBox, 0, Qt.AlignRight)

        self.setFixedSize(self.sizeHint())
        self.setWindowTitle(_('DIAGRAM_WINDOW_TITLE_NEW'))

        connect(self.confirmationBox.accepted, self.accept)
        connect(self.confirmationBox.rejected, self.reject)

    #############################################
    # SLOTS
    #################################

    @pyqtSlot()
    def accept(self):
        """
        Accept the diagram form and creates a new empty diagram.
        """
        settings = QSettings(ORGANIZATION, APPNAME)
        size = settings.value('diagram/size', 5000, int)
        path = expandPath(self.pathField.value())

        try:
            diagram = Diagram(self.pathField.value(), self.project)
            diagram.setSceneRect(QRectF(-size / 2, -size / 2, size, size))
            diagram.setItemIndexMethod(Diagram.NoIndex)
            exporter = GrapholExporter(diagram, self)
            exporter.run()
        except Exception as e:
            msgbox = QMessageBox(self)
            msgbox.setIconPixmap(QPixmap(':/icons/error'))
            msgbox.setWindowIcon(QIcon(':/images/eddy'))
            msgbox.setWindowTitle(_('DIAGRAM_CREATION_FAILED_WINDOW_TITLE'))
            msgbox.setStandardButtons(QMessageBox.Close)
            msgbox.setText(_('DIAGRAM_CREATION_FAILED_MESSAGE', path))
            msgbox.setDetailedText(''.join(format_exception(type(e), e, e.__traceback__)))
            msgbox.exec_()
            super().reject()
        else:
            super().accept()

    @pyqtSlot()
    def doDiagramPathValidate(self):
        """
        Validate diagram path settings.
        """
        caption = ''
        enabled = True

        #############################################
        # CHECK NAME
        #################################

        name = self.nameField.value()
        path = self.pathField.value()

        if not name:
            caption = ''
            enabled = False
        else:
            if isdir(path):
                caption = _('DIAGRAM_CAPTION_ALREADY_EXISTS', name)
                enabled = False
            elif not isPathValid(path):
                caption = _('DIAGRAM_CAPTION_NAME_NOT_VALID', name)
                enabled = False

        self.caption.setText(caption)
        self.caption.setVisible(not isEmpty(caption))
        self.confirmationBox.button(QDialogButtonBox.Ok).setEnabled(enabled)
        self.setFixedSize(self.sizeHint())

    @pyqtSlot(str)
    def onNameFieldChanged(self, name):
        """
        Update the diagram location field to reflect the new diagram name.
        :type name: str
        """
        if not isEmpty(name):
            name = name.strip()
            name = '{0}{1}'.format(cutR(name, File.Graphol.extension), File.Graphol.extension)
        self.pathField.setValue('{0}{1}'.format(self.projectPath, name))