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


from mockito import when

from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtTest import QTest

from eddy.commands import CommandNodeLabelEdit
from eddy.datatypes import ItemType, DiagramMode, DistinctList
from eddy.items import InclusionEdge

from tests import EddyTestCase


class Test_DiagramScene(EddyTestCase):

    def setUp(self):
        """
        Setup DiagramScene specific test environment.
        """
        super().setUp()

        self.scene = self.mainwindow.createScene(5000, 5000)
        self.mainview = self.mainwindow.createView(self.scene)
        self.subwindow = self.mainwindow.createSubWindow(self.mainview)
        self.subwindow.showMaximized()
        self.mainwindow.mdi.setActiveSubWindow(self.subwindow)
        self.mainwindow.mdi.update()

        when(self.scene.settings).value('scene/snap_to_grid', False, bool).thenReturn(False)

    ####################################################################################################################
    #                                                                                                                  #
    #   NODE INSERTION                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def test_insert_single_node(self):
        # GIVEN
        button = self.mainwindow.palette_.button(ItemType.ConceptNode)
        # WHEN
        QTest.mouseClick(button, Qt.LeftButton)
        self.assertTrue(button.isChecked())
        self.assertIs(self.scene.mode, DiagramMode.NodeInsert)
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(100, 100))
        # THEN
        self.assertFalse(button.isChecked())
        self.assertIs(self.scene.mode, DiagramMode.Idle)
        self.assertLen(2, self.scene.items())
        self.assertEmpty(self.scene.edgesById)
        self.assertNotEmpty(self.scene.nodesById)
        self.assertDictHasKey('n0', self.scene.nodesById)
        self.assertEqual(1, self.scene.undostack.count())
        self.assertTrue(self.scene.node('n0').isSelected())
        self.assertEquals(self.scene.node('n0').pos(), self.mainview.mapToScene(QPoint(100, 100)))

    def test_insert_multiple_nodes(self):
        # GIVEN
        button = self.mainwindow.palette_.button(ItemType.ConceptNode)
        # WHEN
        QTest.mouseClick(button, Qt.LeftButton)
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, QPoint(0, 100))
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, QPoint(400, 100))
        # THEN
        self.assertTrue(button.isChecked())
        self.assertIs(self.scene.mode, DiagramMode.NodeInsert)
        self.assertLen(4, self.scene.items())
        self.assertEmpty(self.scene.edgesById)
        self.assertNotEmpty(self.scene.nodesById)
        self.assertDictHasKey('n0', self.scene.nodesById)
        self.assertDictHasKey('n1', self.scene.nodesById)
        self.assertEqual(2, self.scene.undostack.count())
        self.assertEquals(self.scene.node('n0').pos(), self.mainview.mapToScene(QPoint(0, 100)))
        self.assertEquals(self.scene.node('n1').pos(), self.mainview.mapToScene(QPoint(400, 100)))
        QTest.keyRelease(self.mainview.viewport(), Qt.Key_Control)
        self.assertIs(self.scene.mode, DiagramMode.Idle)
        self.assertFalse(button.isChecked())

    ####################################################################################################################
    #                                                                                                                  #
    #   EDGE INSERTION                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def test_insert_single_edge_with_endpoint(self):
        # GIVEN
        button = self.mainwindow.palette_.button(ItemType.InclusionEdge)
        self.createStubDiagram1()
        # WHEN
        QTest.mouseClick(button, Qt.LeftButton)
        self.assertIs(self.scene.mode, DiagramMode.EdgeInsert)
        self.assertTrue(button.isChecked())
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, self.mainview.mapFromScene(QPoint(-200, -200)))
        self.assertIsNotNone(self.scene.command)
        self.assertIsInstance(self.scene.command.edge, InclusionEdge)
        self.assertIs(self.scene.command.edge.source, self.scene.node('n0'))
        self.assertIsNone(self.scene.command.edge.target)
        self.assertLen(9, self.scene.items())
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, self.mainview.mapFromScene(QPoint(+200, -200)))
        # THEN
        self.assertLen(9, self.scene.items())
        self.assertIsNone(self.scene.command)
        self.assertNotEmpty(self.scene.edgesById)
        self.assertDictHasKey('e0', self.scene.edgesById)
        self.assertIs(self.scene.edge('e0').source, self.scene.node('n0'))
        self.assertIs(self.scene.edge('e0').target, self.scene.node('n1'))
        self.assertEqual(1, self.scene.undostack.count())
        self.assertIs(self.scene.mode, DiagramMode.Idle)

    def test_insert_single_edge_with_no_endpoint(self):
        # GIVEN
        button = self.mainwindow.palette_.button(ItemType.InclusionEdge)
        self.createStubDiagram1()
        # WHEN
        QTest.mouseClick(button, Qt.LeftButton)
        self.assertIs(self.scene.mode, DiagramMode.EdgeInsert)
        self.assertTrue(button.isChecked())
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, self.mainview.mapFromScene(QPoint(-200, -200)))
        self.assertIsNotNone(self.scene.command)
        self.assertIsInstance(self.scene.command.edge, InclusionEdge)
        self.assertIs(self.scene.command.edge.source, self.scene.node('n0'))
        self.assertIsNone(self.scene.command.edge.target)
        self.assertLen(9, self.scene.items())
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, self.mainview.mapFromScene(QPoint(2000, -200)))
        # THEN
        self.assertLen(8, self.scene.items())
        self.assertIsNone(self.scene.command)
        self.assertEmpty(self.scene.edgesById)
        self.assertEqual(0, self.scene.undostack.count())
        self.assertIs(self.scene.mode, DiagramMode.Idle)

    def test_insert_multiple_edges_with_endpoint(self):
        # GIVEN
        button = self.mainwindow.palette_.button(ItemType.InclusionEdge)
        self.createStubDiagram1()
        # WHEN
        QTest.mouseClick(button, Qt.LeftButton)
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, -200)))
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, -200)))
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, -200)))
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, +200)))
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, +200)))
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, +200)))
        # THEN
        self.assertLen(11, self.scene.items())
        self.assertIsNone(self.scene.command)
        self.assertNotEmpty(self.scene.edgesById)
        self.assertDictHasKey('e0', self.scene.edgesById)
        self.assertDictHasKey('e1', self.scene.edgesById)
        self.assertDictHasKey('e2', self.scene.edgesById)
        self.assertIs(self.scene.edge('e0').source, self.scene.node('n0'))
        self.assertIs(self.scene.edge('e0').target, self.scene.node('n1'))
        self.assertIs(self.scene.edge('e1').source, self.scene.node('n0'))
        self.assertIs(self.scene.edge('e1').target, self.scene.node('n2'))
        self.assertIs(self.scene.edge('e2').source, self.scene.node('n2'))
        self.assertIs(self.scene.edge('e2').target, self.scene.node('n3'))
        self.assertEqual(3, self.scene.undostack.count())
        self.assertIs(self.scene.mode, DiagramMode.EdgeInsert)
        QTest.keyRelease(self.mainview.viewport(), Qt.Key_Control)
        self.assertIs(self.scene.mode, DiagramMode.Idle)
        self.assertFalse(button.isChecked())

    ####################################################################################################################
    #                                                                                                                  #
    #   ITEM SELECTION                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def test_select_single_item(self):
        # GIVEN
        self.createStubDiagram2()
        # WHEN
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, self.mainview.mapFromScene(QPoint(-200, -220)))
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, self.mainview.mapFromScene(QPoint(+200, -220)))
        # THEN
        self.assertIs(self.scene.mode, DiagramMode.Idle)
        self.assertLen(1, self.scene.selectedNodes())
        self.assertLen(1, self.scene.selectedItems())
        self.assertTrue(self.scene.node('n1').isSelected())

    def test_select_multiple_items(self):
        # GIVEN
        self.createStubDiagram2()
        # WHEN
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, -220)))
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, -220)))
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, +220)))
        # THEN
        self.assertIs(self.scene.mode, DiagramMode.Idle)
        self.assertLen(0, self.scene.selectedEdges())
        self.assertLen(3, self.scene.selectedNodes())
        self.assertLen(3, self.scene.selectedItems())
        self.assertTrue(self.scene.node('n0').isSelected())
        self.assertTrue(self.scene.node('n1').isSelected())
        self.assertTrue(self.scene.node('n3').isSelected())
        self.assertFalse(self.scene.node('n2').isSelected())

    def test_select_all_using_shortcut(self):
        # GIVEN
        self.createStubDiagram2()
        # WHEN
        QTest.keyClick(self.mainview.viewport(), 'a', Qt.ControlModifier)
        # THEN
        self.assertCountEqual(self.scene.nodes(), self.scene.selectedNodes())
        self.assertCountEqual(self.scene.edges(), self.scene.selectedEdges())

    ####################################################################################################################
    #                                                                                                                  #
    #   EDGE SWAPPING                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def test_swap_all_edges(self):
        # GIVEN
        self.createStubDiagram2()
        data1 = {edge: {'source': edge.source.id, 'target': edge.target.id} for edge in self.scene.edges()}
        # WHEN
        self.mainwindow.actionSelectAll.trigger()
        self.mainwindow.actionSwapEdge.trigger()
        # THEN
        data2 = {edge: {'source': edge.source.id, 'target': edge.target.id} for edge in self.scene.edges()}
        for edge in data1:
            self.assertEqual(data1[edge]['source'], data2[edge]['target'])
            self.assertEqual(data1[edge]['target'], data2[edge]['source'])
        self.assertEqual(1, self.scene.undostack.count())

    ####################################################################################################################
    #                                                                                                                  #
    #   EDGE TOGGLES                                                                                                   #
    #                                                                                                                  #
    ####################################################################################################################

    def test_toggle_edge_complete(self):
        # GIVEN
        self.createStubDiagram2()
        edge = self.scene.edge('e0')
        edge.setSelected(True)
        # WHEN
        self.mainwindow.actionToggleEdgeComplete.trigger()
        # THEN
        self.assertTrue(edge.complete)
        self.assertEqual(1, self.scene.undostack.count())

    def test_toggle_multi_edge_complete_off(self):
        # GIVEN
        self.createStubDiagram2()
        self.scene.edge('e0').complete = True
        self.scene.edge('e1').complete = True
        self.scene.edge('e2').complete = True
        for edge in (self.scene.edge('e0'), self.scene.edge('e1'), self.scene.edge('e2'), self.scene.edge('e3')):
            edge.setSelected(True)
        # WHEN
        self.mainwindow.actionToggleEdgeComplete.trigger()
        # THEN
        for edge in (self.scene.edge('e0'), self.scene.edge('e1'), self.scene.edge('e2'), self.scene.edge('e3')):
            self.assertFalse(edge.complete)
        self.assertEqual(1, self.scene.undostack.count())

    def test_toggle_multi_edge_complete_on(self):
        # GIVEN
        self.createStubDiagram2()
        self.scene.edge('e0').complete = True
        for edge in (self.scene.edge('e0'), self.scene.edge('e1'), self.scene.edge('e2'), self.scene.edge('e3')):
            edge.setSelected(True)
        # WHEN
        self.mainwindow.actionToggleEdgeComplete.trigger()
        # THEN
        for edge in (self.scene.edge('e0'), self.scene.edge('e1'), self.scene.edge('e2'), self.scene.edge('e3')):
            self.assertTrue(edge.complete)
        self.assertEqual(1, self.scene.undostack.count())

    def test_toggle_edge_functional(self):
        # GIVEN
        self.createStubDiagram4()
        edge = self.scene.edge('e0')
        edge.setSelected(True)
        # WHEN
        self.mainwindow.actionToggleEdgeFunctional.trigger()
        # THEN
        self.assertTrue(edge.functional)
        self.assertEqual(1, self.scene.undostack.count())

    ####################################################################################################################
    #                                                                                                                  #
    #   TEST AXIOM COMPOSITION                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def test_compose_asymmetric_role(self):
        # GIVEN
        self.createStubDiagram3()
        self.scene.node('n0').setSelected(True)
        # WHEN
        self.mainwindow.actionComposeAsymmetricRole.trigger()
        # THEN
        self.assertEqual(4, len(self.scene.nodes()))
        self.assertEqual(3, len(self.scene.edges()))
        self.assertEqual(1, self.scene.undostack.count())
        self.assertTrue(self.scene.node('n0').asymmetric)

    def test_decompose_asymmetric_role(self):
        # GIVEN
        self.createStubDiagram3()
        self.scene.node('n0').setSelected(True)
        self.mainwindow.actionComposeAsymmetricRole.trigger()
        self.assertTrue(self.scene.node('n0').asymmetric)
        # WHEN
        self.mainwindow.actionComposeAsymmetricRole.setChecked(True)
        self.mainwindow.actionComposeAsymmetricRole.trigger()
        # THEN
        self.assertFalse(self.scene.node('n0').asymmetric)

    def test_compose_irreflexive_role(self):
        # GIVEN
        self.createStubDiagram3()
        self.scene.node('n0').setSelected(True)
        # WHEN
        self.mainwindow.actionComposeIrreflexiveRole.trigger()
        # THEN
        self.assertEqual(5, len(self.scene.nodes()))
        self.assertEqual(3, len(self.scene.edges()))
        self.assertEqual(1, self.scene.undostack.count())
        self.assertTrue(self.scene.node('n0').irreflexive)

    def test_decompose_irreflexive_role(self):
        # GIVEN
        self.createStubDiagram3()
        self.scene.node('n0').setSelected(True)
        self.mainwindow.actionComposeIrreflexiveRole.trigger()
        self.assertTrue(self.scene.node('n0').irreflexive)
        # WHEN
        self.mainwindow.actionComposeIrreflexiveRole.setChecked(True)
        self.mainwindow.actionComposeIrreflexiveRole.trigger()
        # THEN
        self.assertFalse(self.scene.node('n0').irreflexive)

    def test_compose_reflexive_role(self):
        # GIVEN
        self.createStubDiagram3()
        self.scene.node('n0').setSelected(True)
        # WHEN
        self.mainwindow.actionComposeReflexiveRole.trigger()
        # THEN
        self.assertEqual(4, len(self.scene.nodes()))
        self.assertEqual(2, len(self.scene.edges()))
        self.assertEqual(1, self.scene.undostack.count())
        self.assertTrue(self.scene.node('n0').reflexive)

    def test_decompose_reflexive_role(self):
        # GIVEN
        self.createStubDiagram3()
        self.scene.node('n0').setSelected(True)
        self.mainwindow.actionComposeReflexiveRole.trigger()
        self.assertTrue(self.scene.node('n0').reflexive)
        # WHEN
        self.mainwindow.actionComposeReflexiveRole.setChecked(True)
        self.mainwindow.actionComposeReflexiveRole.trigger()
        # THEN
        self.assertFalse(self.scene.node('n0').reflexive)

    def test_compose_symmetric_role(self):
        # GIVEN
        self.createStubDiagram3()
        self.scene.node('n0').setSelected(True)
        # WHEN
        self.mainwindow.actionComposeSymmetricRole.trigger()
        # THEN
        self.assertEqual(3, len(self.scene.nodes()))
        self.assertEqual(2, len(self.scene.edges()))
        self.assertEqual(1, self.scene.undostack.count())
        self.assertTrue(self.scene.node('n0').symmetric)

    def test_decompose_symmetric_role(self):
        # GIVEN
        self.createStubDiagram3()
        self.scene.node('n0').setSelected(True)
        self.mainwindow.actionComposeSymmetricRole.trigger()
        self.assertTrue(self.scene.node('n0').symmetric)
        # WHEN
        self.mainwindow.actionComposeSymmetricRole.setChecked(True)
        self.mainwindow.actionComposeSymmetricRole.trigger()
        # THEN
        self.assertFalse(self.scene.node('n0').symmetric)

    def test_compose_transitive_role(self):
        # GIVEN
        self.createStubDiagram3()
        self.scene.node('n0').setSelected(True)
        # WHEN
        self.mainwindow.actionComposeTransitiveRole.trigger()
        # THEN
        self.assertEqual(3, len(self.scene.nodes()))
        self.assertEqual(3, len(self.scene.edges()))
        self.assertEqual(1, self.scene.undostack.count())
        self.assertTrue(self.scene.node('n0').transitive)

    def test_decompose_transitive_role(self):
        # GIVEN
        self.createStubDiagram3()
        self.scene.node('n0').setSelected(True)
        self.mainwindow.actionComposeTransitiveRole.trigger()
        self.assertTrue(self.scene.node('n0').transitive)
        # WHEN
        self.mainwindow.actionComposeTransitiveRole.setChecked(True)
        self.mainwindow.actionComposeTransitiveRole.trigger()
        # THEN
        self.assertFalse(self.scene.node('n0').transitive)

    ####################################################################################################################
    #                                                                                                                  #
    #   NODE LABEL INDEX                                                                                               #
    #                                                                                                                  #
    ####################################################################################################################

    def test_node_label_index_update_upon_label_edit(self):
        # GIVEN
        self.createStubDiagram1()
        self.assertIn('concept', self.scene.nodesByLabel)
        self.assertIsInstance(self.scene.nodesByLabel['concept'], DistinctList)
        self.assertLen(4, self.scene.nodesByLabel['concept'])
        # WHEN
        command = CommandNodeLabelEdit(self.scene, self.scene.node('n0'))
        command.end('label1')
        self.scene.undostack.push(command)
        # THEN
        self.assertEqual(1, self.scene.undostack.count())
        self.assertIn('concept', self.scene.nodesByLabel)
        self.assertLen(3, self.scene.nodesByLabel['concept'])
        self.assertNotIn(self.scene.node('n0'), self.scene.nodesByLabel['concept'])
        self.assertIn('label1', self.scene.nodesByLabel)
        self.assertLen(1, self.scene.nodesByLabel['label1'])
        self.assertIn(self.scene.node('n0'), self.scene.nodesByLabel['label1'])
        # WHEN
        self.scene.undostack.undo()
        # THEN
        self.assertIn('concept', self.scene.nodesByLabel)
        self.assertLen(4, self.scene.nodesByLabel['concept'])
        self.assertIn(self.scene.node('n0'), self.scene.nodesByLabel['concept'])
        self.assertNotIn('label1', self.scene.nodesByLabel)

    def test_node_label_index_update_upon_node_removal(self):
        # GIVEN
        self.createStubDiagram1()
        self.assertIn('concept', self.scene.nodesByLabel)
        self.assertIsInstance(self.scene.nodesByLabel['concept'], DistinctList)
        self.assertLen(4, self.scene.nodesByLabel['concept'])
        # WHEN
        self.scene.removeItem(self.scene.node('n2'))
        # THEN
        self.assertIn('concept', self.scene.nodesByLabel)
        self.assertLen(3, self.scene.nodesByLabel['concept'])

    ####################################################################################################################
    #                                                                                                                  #
    #   STUB DIAGRAM GENERATION                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def createStubDiagram1(self):
        """
        Create a stub diagram to be used in test cases.
        The diagram is composed of 4 Concept nodes.
        """
        QTest.mouseClick(self.mainwindow.palette_.button(ItemType.ConceptNode), Qt.LeftButton)
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, -200))) # n0
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, -200))) # n1
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, +200))) # n2
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, +200))) # n3
        QTest.keyRelease(self.mainview.viewport(), Qt.Key_Control)

        self.scene.clearSelection()
        self.scene.undostack.clear()

    def createStubDiagram2(self):
        """
        Create a stub diagram to be used in test cases.
        The diagram is composed of 4 Concept nodes connected using 4 Inclusion edges.
        """
        QTest.mouseClick(self.mainwindow.palette_.button(ItemType.ConceptNode), Qt.LeftButton)
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, -200))) # n0
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, -200))) # n1
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, +200))) # n2
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, +200))) # n3
        QTest.keyRelease(self.mainview.viewport(), Qt.Key_Control)

        QTest.mouseClick(self.mainwindow.palette_.button(ItemType.InclusionEdge), Qt.LeftButton)
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, -200)))
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, -200))) # n0 -> n1
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, -200)))
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, +200))) # n0 -> n2
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, +200)))
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, +200))) # n2 -> n3
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, +200)))
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, -200))) # n3 -> n1
        QTest.keyRelease(self.mainview.viewport(), Qt.Key_Control)

        self.scene.clearSelection()
        self.scene.undostack.clear()

    def createStubDiagram3(self):
        """
        Create a stub diagram to be used in test cases.
        The diagram is composed of a Role Node and an attribute Node.
        """
        QTest.mouseClick(self.mainwindow.palette_.button(ItemType.RoleNode), Qt.LeftButton)
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, self.mainview.mapFromScene(QPoint(-200, -200))) # n0
        QTest.mouseClick(self.mainwindow.palette_.button(ItemType.AttributeNode), Qt.LeftButton)
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, self.mainview.mapFromScene(QPoint(+200, -200))) # n1

        self.scene.clearSelection()
        self.scene.undostack.clear()

    def createStubDiagram4(self):
        """
        Create a stub diagram to be used in test cases.
        The diagram is composed of 4 Concept nodes connected to an Intersection node using 4 Input edges.
        """
        QTest.mouseClick(self.mainwindow.palette_.button(ItemType.ConceptNode), Qt.LeftButton)
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, -200))) # n0
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, -200))) # n1
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, +200))) # n2
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, +200))) # n3
        QTest.keyRelease(self.mainview.viewport(), Qt.Key_Control)

        QTest.mouseClick(self.mainwindow.palette_.button(ItemType.IntersectionNode), Qt.LeftButton)
        QTest.mouseClick(self.mainview.viewport(), Qt.LeftButton, Qt.NoModifier, self.mainview.mapFromScene(QPoint(0, 0))) # n4

        QTest.mouseClick(self.mainwindow.palette_.button(ItemType.InputEdge), Qt.LeftButton)
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, -200)))
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(0, 0))) # n0 -> n4
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, -200)))
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(0, 0))) # n1 -> n4
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(-200, +200)))
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(0, 0))) # n2 -> n4
        QTest.mousePress(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(+200, +200)))
        QTest.mouseRelease(self.mainview.viewport(), Qt.LeftButton, Qt.ControlModifier, self.mainview.mapFromScene(QPoint(0, 0))) # n3 -> n4
        QTest.keyRelease(self.mainview.viewport(), Qt.Key_Control)

        self.scene.clearSelection()
        self.scene.undostack.clear()