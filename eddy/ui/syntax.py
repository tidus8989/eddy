# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <pantaleone@dis.uniroma1.it>    #
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
#     - Daniele Pantaleone <pantaleone@dis.uniroma1.it>                  #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QProgressBar, QMessageBox
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PyQt5.QtWidgets import QDesktopWidget, QApplication
from PyQt5.QtWidgets import QHBoxLayout, QPushButton

from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.datatypes.qt import Font
from eddy.core.functions.signals import connect


# FIXME: this is bugged as hell!
class SyntaxValidationDialog(QDialog):
    """
    This class implements the modal dialog used to perform manual syntax validation.
    """
    sgnProgress = pyqtSignal(int)
    sgnWarning = pyqtSignal(str)

    def __init__(self, project, session):
        """
        Initialize the form dialog.
        :type project: Project
        :type session: Session
        """
        super().__init__(session)

        arial12r = Font('Arial', 12)

        self.i = 0
        self.items = list(project.edges()) + list(project.nodes())
        self.popup = False
        self.project = project

        #############################################
        # TOP AREA
        #################################

        self.progressBar = QProgressBar(self)
        self.progressBar.setAlignment(Qt.AlignHCenter)
        self.progressBar.setRange(self.i, len(self.items) - 1)
        self.progressBar.setFixedSize(400, 30)
        self.progressBar.setValue(self.i)

        self.progressBox = QWidget(self)
        self.progressBoxLayout = QVBoxLayout(self.progressBox)
        self.progressBoxLayout.setContentsMargins(10, 10, 10, 10)
        self.progressBoxLayout.addWidget(self.progressBar)

        #############################################
        # CONTROLS AREA
        #################################

        self.buttonAbort = QPushButton('Abort', self)
        self.buttonAbort.setFont(arial12r)
        self.buttonIgnore = QPushButton('Ignore', self)
        self.buttonIgnore.setFont(arial12r)
        self.buttonShow = QPushButton('Show', self)
        self.buttonShow.setFont(arial12r)

        self.buttonBox = QWidget(self)
        self.buttonBox.setVisible(False)
        self.buttonBoxLayout = QHBoxLayout(self.buttonBox)
        self.buttonBoxLayout.setContentsMargins(10, 0, 10, 10)
        self.buttonBoxLayout.addWidget(self.buttonAbort, 0, Qt.AlignRight)
        self.buttonBoxLayout.addWidget(self.buttonIgnore, 0, Qt.AlignRight)
        self.buttonBoxLayout.addWidget(self.buttonShow, 0, Qt.AlignRight)

        #############################################
        # MESSAGE AREA
        #################################

        self.messageField = QTextEdit(self)
        self.messageField.setAcceptRichText(True)
        self.messageField.setAttribute(Qt.WA_MacShowFocusRect, 0)
        self.messageField.setFixedSize(400, 100)
        self.messageField.setFont(arial12r)

        self.messageBox = QWidget(self)
        self.messageBox.setVisible(False)
        self.messageBoxLayout = QVBoxLayout(self.messageBox)
        self.messageBoxLayout.setContentsMargins(10, 0, 10, 10)
        self.messageBoxLayout.addWidget(self.messageField)

        #############################################
        # CONFIGURE LAYOUT
        #################################

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.progressBox)
        self.mainLayout.addWidget(self.buttonBox, 0, Qt.AlignRight)
        self.mainLayout.addWidget(self.messageBox)

        connect(self.sgnProgress, self.doProgress)
        connect(self.sgnWarning, self.doWarning)
        connect(self.buttonAbort.clicked, self.doAbort)
        connect(self.buttonIgnore.clicked, self.doIgnore)
        connect(self.buttonShow.clicked, self.doShow)

        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowTitle('Running syntax validation...')
        self.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
        self.setFixedSize(self.sizeHint())

        desktop = QDesktopWidget()
        screen = desktop.screenGeometry()
        widget = self.geometry()
        x = (screen.width() - widget.width()) / 2
        y = (screen.height() - widget.height()) / 2
        self.move(x, y)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the active session (alias for SyntaxValidationDialog.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   EVENTS
    #################################

    def showEvent(self, showEvent):
        """
        Executed whenever the dialog is shown.
        :type showEvent: QShowEvent
        """
        self.sgnProgress.emit(0)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot(bool)
    def doAbort(self, _=False):
        """
        Executed when the abort button is pressed.
        :type _: bool
        """
        self.close()

    @pyqtSlot(bool)
    def doIgnore(self, _=False):
        """
        Executed when the ignore button is pressed.
        :type _: bool
        """
        self.buttonBox.setVisible(False)
        self.messageBox.setVisible(False)
        self.messageField.setText('')
        self.setFixedSize(self.sizeHint())
        self.sgnProgress.emit(self.i + 1)

    @pyqtSlot(int)
    def doProgress(self, i):
        """
        Perform an advance step in the validation procedure.
        :type i: int
        """
        if self.i < len(self.items):

            self.i = i
            message = None
            while self.i < len(self.items):

                item = self.items[self.i]
                self.progressBar.setValue(self.i)

                QApplication.processEvents()

                if item.isEdge():
                    source = item.source
                    target = item.target
                    pvr = self.project.profile.check(source, item, target)
                    if not pvr.isValid():
                        nA = '{0} <b>{1}</b>'.format(source.name, source.id)
                        nB = '{0} <b>{1}</b>'.format(target.name, target.id)
                        if source.type() in {Item.AttributeNode, Item.ConceptNode, Item.RoleNode}:
                            nA = '{0} <b>{1}:{2}</b>'.format(source.name, source.text(), source.id)
                        if target.type() in {Item.AttributeNode, Item.ConceptNode, Item.RoleNode}:
                            nB = '{0} <b>{1}:{2}</b>'.format(target.name, target.text(), target.id)
                        info = '{0}{1}'.format(pvr.message()[:1].lower(), pvr.message()[1:])
                        message = 'Syntax error detected on {} from {} to {}: <i>{}</i>.'.format(item.name, nA, nB, info)
                        break

                if item.isNode():
                    if item.identity is Identity.Unknown:
                        name = '{0} "{1}"'.format(item.name, item.id)
                        if item.isPredicate():
                            name = '{0} "{1}:{2}"'.format(item.name, item.text(), item.id)
                        message = 'Unkown node identity detected on {0}.'.format(name)
                        break

                self.i += 1
                print('{} - {}'.format(self.i, len(self.items)))

            if message:
                self.sgnWarning.emit(message)
            else:
                print("HERE")
                self.close(popup=True)
        else:
            self.close(popup=True)

    @pyqtSlot(bool)
    def doShow(self, _=False):
        """
        Executed when the show button is pressed.
        :type _: bool
        """
        if self.i < len(self.items):
            item = self.items[self.i]
            focus = item
            if item.isEdge():
                try:
                    focus = item.breakpoints[int(len(item.breakpoints) / 2)]
                except IndexError:
                    pass
            self.session.doFocusDiagram(item.diagram)
            self.session.mdi.activeView().centerOn(focus)
            self.session.mdi.activeDiagram().clearSelection()
            item.setSelected(True)
        self.close()

    @pyqtSlot(str)
    def doWarning(self, message):
        """
        Executed when a warning message needs to be displayed.
        :type message: int
        """
        self.buttonBox.setVisible(True)
        self.messageBox.setVisible(True)
        self.messageField.setHtml(message)
        self.setFixedSize(self.sizeHint())

    #############################################
    #   INTERFACE
    #################################

    def close(self, popup=False):
        """
        Close the modal window.
        :type popup: bool
        """
        if popup:
            msgbox = QMessageBox(self)
            msgbox.setIconPixmap(QIcon(':/icons/48/ic_done_black').pixmap(48))
            msgbox.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Done!')
            msgbox.setStandardButtons(QMessageBox.Close)
            msgbox.setText('Syntax validation completed!')
            msgbox.setTextFormat(Qt.RichText)
            msgbox.exec_()

        return super().close()
