# -*- coding: utf-8 -*-
# Tulpenmanie, a markets client.
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

import tulpenmanie.ui.commodity
import tulpenmanie.ui.market
import tulpenmanie.ui.exchange

class EditDefinitionsDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(EditDefinitionsDialog, self).__init__(parent)

        self.tab_widget = QtGui.QTabWidget()
        self.tab_widget.addTab(tulpenmanie.ui.commodity.EditWidget(),
                               "&commodities")
        self.tab_widget.addTab(tulpenmanie.ui.market.EditWidget(),
                               "&markets")
        self.tab_widget.addTab(tulpenmanie.ui.exchange.EditWidget(),
                               "&exchanges")
        button_box = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Close)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.accept)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.tab_widget)
        layout.addWidget(button_box)
        self.setLayout(layout)

        self.setWindowTitle("edit commodities, markets, exchanges")
