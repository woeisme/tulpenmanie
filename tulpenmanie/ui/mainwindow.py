# Tulpenmanie, a commodities market client.
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

import tulpenmanie.commodity
import tulpenmanie.market
import tulpenmanie.providers
import tulpenmanie.exchange
#This next import registers providers with the former module
from tulpenmanie.provider_modules import *
import tulpenmanie.ui.exchange
import tulpenmanie.ui.edit


class MainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super (MainWindow, self).__init__(parent)

        tulpenmanie.commodity.create_model(self)
        tulpenmanie.market.create_model(self)
        tulpenmanie.exchange.create_exchanges_model(self)

        edit_definitions_action = QtGui.QAction("&definitions", self,
                                            shortcut="Ctrl+E",
                                            triggered=self._edit_definitions)

        self.markets_menu = QtGui.QMenu(tulpenmanie.translation.markets,
                                        self)
        self.menuBar().addMenu(self.markets_menu)
        options_menu = QtGui.QMenu(QtCore.QCoreApplication.translate(
            "options menu title", "options"), self)
        options_menu.addAction(edit_definitions_action)
        self.menuBar().addMenu(options_menu)

        self.markets = dict()
        self.accounts = dict()
        self.parse_models()

    def parse_models(self):
        self.parse_markets()
        self.parse_exchanges()

    def parse_markets(self):
        "if a dock doesn't exist for market create it"
        # Delete a  dock if it isn't in the model
        for uuid in self.markets.keys():
            if not tulpenmanie.market.model.findItems(uuid):
                for thing in self.markets[uuid].values():
                    thing.deleteLater()
                    self.markets.pop(uuid)

        for market_row in range(tulpenmanie.market.model.rowCount()):
            market_uuid = str(tulpenmanie.market.model.item(
                market_row, tulpenmanie.market.model.UUID).text())

            if market_uuid in self.markets:
                dock = self.markets[market_uuid]['dock']

            else:
                market_dict = dict()
                market_name = tulpenmanie.market.model.item(
                    market_row, tulpenmanie.market.model.NAME).text()
                menu = QtGui.QMenu(market_name, self)
                self.markets_menu.addMenu(menu)

                dock = tulpenmanie.ui.market.DockWidget(market_row, self)
                dock.setAllowedAreas(QtCore.Qt.TopDockWidgetArea)
                self.addDockWidget(QtCore.Qt.TopDockWidgetArea, dock)

                menu.addAction(dock.enable_market_action)
                menu.addSeparator()

                market_dict['menu'] = menu
                market_dict['dock'] = dock
                self.markets[market_uuid] = market_dict

            enable = tulpenmanie.market.model.item(
                market_row, tulpenmanie.market.model.ENABLE).text()
            # TODO we should just get a bool instead of a string
            if enable == "true":
                enable = True
            else:
                enable = False
            dock.enable_market_action.setChecked(enable)
            dock.enable_market(enable)

    def parse_exchanges(self):
        for exchange_row in range(tulpenmanie.exchange.model.rowCount()):
            exchange_item = tulpenmanie.exchange.model.item(exchange_row)
            exchange_name = str(exchange_item.text())

            # parse accounts
            credentials = []
            account_valid = True
            for setting in exchange_item.required_account_settings:
                credential = exchange_item.child(0, setting).text()
                if credential:
                    credentials.append(credential)
                else:
                    account_valid = False

            if account_valid:
                if exchange_name in self.accounts:
                    account_object = self.accounts[exchange_name]
                    if account_object:
                        account_object.set_credentials(credentials)
                    else:
                        AccountClass = tulpenmanie.providers.accounts[exchange_name]
                        account_object = AccountClass(credentials)
                        self.accounts[exchange_name] = account_object
                else:
                    AccountClass = tulpenmanie.providers.accounts[exchange_name]
                    account_object = AccountClass(credentials)
                    self.accounts[exchange_name] = account_object
            else:
                account_object = None
                self.accounts[exchange_name] = account_object

            ## parse remote markets
            markets_item = exchange_item.child(0, exchange_item.MARKETS)
            for market_row in range(markets_item.rowCount()):
                local_market = str(markets_item.child(
                    market_row, exchange_item.MARKET_LOCAL).text())

                if local_market:
                    remote_market = markets_item.child(
                        market_row, exchange_item.MARKET_REMOTE).text()
                    dock = self.markets[local_market]['dock']

                    if exchange_name in dock.exchanges:
                        exchange_widget = dock.exchanges[exchange_name]
                    else:
                        # make exchange widget
                        exchange_widget = tulpenmanie.ui.exchange.ExchangeWidget(
                            exchange_item, market_row, remote_market, dock)

                    enable = markets_item.child(
                        market_row, exchange_item.MARKET_ENABLE).text()
                    if enable == "true":
                        enable = True
                    else:
                        enable = False
                    exchange_widget.enable_exchange_action.setChecked(enable)
                    self.markets[local_market]['menu'].addAction(
                        exchange_widget.enable_exchange_action)

                    if dock.isEnabled():
                        exchange_widget.enable_exchange(enable)
                    else:
                        exchange_widget.setEnabled(False)
                    account_widget = exchange_widget.account_widget
                    if not account_widget and account_object:
                        account_widget = tulpenmanie.ui.exchange.AccountWidget(
                            account_object, remote_market, exchange_widget)
                        account_widget.enable_account(exchange_widget.isEnabled())
                    if account_widget and not account_object:
                        exchange_widget.account_widget = None
                        account_widget.deleteLater()

    def _edit_definitions(self):
        dialog = tulpenmanie.ui.edit.EditDefinitionsDialog(self)
        dialog.exec_()
        self.parse_models()

    def closeEvent(self, event):
        #TODO maybe a market model could store
        #commodities items in a second place
        tulpenmanie.commodity.model.save()
        tulpenmanie.market.model.save()
        tulpenmanie.exchange.model.save()

        event.accept()

