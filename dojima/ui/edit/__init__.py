# -*- coding: utf-8 -*-
# Dojima, a markets client.
# Copyright (C) 2012  Emery Hemingway
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from PyQt4 import QtCore, QtGui

import dojima.ui.edit.commodity
#import dojima.ui.edit.market
#import dojima.ui.edit.exchange
import dojima.ui.edit.ot_markets

class EditDefinitionsDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(EditDefinitionsDialog, self).__init__(parent)

        self.tab_widget = QtGui.QTabWidget()
        self.tab_widget.addTab(
            dojima.ui.edit.commodity.EditWidget(self),
            QtCore.QCoreApplication.translate('EditDefinitionsDialog',
                                              "&commodities"))
        """
        self.tab_widget.addTab(
            dojima.ui.edit.market.EditWidget(),
            QtCore.QCoreApplication.translate('EditDefinitionsDialog',
                                              "&markets"))
        self.tab_widget.addTab(
            dojima.ui.edit.exchange.EditWidget(),
            QtCore.QCoreApplication.translate('EditDefinitionsDialog',
                                              "&exchanges"))
        """
        self.tab_widget.addTab(
            dojima.ui.edit.ot_markets.EditWidget(),
            QtCore.QCoreApplication.translate('EditDefinitionsDialog',
                                              "&OT markets"))

        # TODO just connect once
        button_box = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Close)
        button_box.rejected.connect(self.accept)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.tab_widget)
        layout.addWidget(button_box)
        self.setLayout(layout)

        self.setWindowTitle("edit commodities definitions")

    """
    def close(self):
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            widget.save()
        self.accept()
    """