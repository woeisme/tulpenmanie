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

import logging

from PyQt4 import QtCore, QtGui


logger = logging.getLogger(__name__)


class FlatSettingsModel(QtGui.QStandardItemModel):

    def __init__(self, parent=None):
        super(FlatSettingsModel, self).__init__(parent)
        self.settings = QtCore.QSettings()
        self.settings.beginGroup(self.name)
        self.setColumnCount(self.COLUMNS)
        self._populate()

    def _populate(self):
        logger.debug("loading %s", self.name)
        for row, uuid in enumerate(self.settings.childGroups()):
            self.settings.beginGroup(uuid)
            item = QtGui.QStandardItem(uuid)
            self.setItem(row, self.UUID, item)
            for setting, column in self.SETTINGS_MAP:
                item = QtGui.QStandardItem(self.settings.value(setting))
                self.setItem(int(row), column, item)
            self.settings.endGroup()

    def save(self):
        logger.debug("saving %s", self.name)
        rows = range(self.rowCount())
        self.settings.remove('')
        for row in rows:
            uuid = self.item(row, self.UUID).text()
            self.settings.beginGroup(uuid)
            for setting, column in self.SETTINGS_MAP:
                value =  self.item(row, column).text()
                self.settings.setValue(setting, value)
            self.settings.endGroup()

    def delete_row(self, row):
        uuid = self.item(self.UUID, row).text()
        self.settings.remove(uuid)
        self.removeRow(row)


class OrdersModel(QtGui.QStandardItemModel):

    # TODO set prefixes and suffixes
    # TODO data should be read-only

    COLUMNS = 3
    ORDER_ID, PRICE, AMOUNT = range(COLUMNS)

    def __init__(self, parent=None):
        super(OrdersModel, self).__init__(parent)

    def append_order(self, order_id, price, amount):
        self.appendRow( (QtGui.QStandardItem(str(order_id)),
                         QtGui.QStandardItem(str(price)),
                         QtGui.QStandardItem(str(amount)) ) )

    def remove_order(self, order_id):
        orders = self.findItems(str(order_id),
                                QtCore.Qt.MatchExactly,
                                self.ORDER_ID)
        for order in orders:
            self.removeRow(order.row())

    def clear_orders(self):
        self.removeRows(0, self.rowCount())
