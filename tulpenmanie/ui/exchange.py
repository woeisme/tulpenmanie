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

import decimal
import logging
from PyQt4 import QtCore, QtGui

import tulpenmanie.exchange
import tulpenmanie.model.order

logger =  logging.getLogger(__name__)


class EditWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(EditWidget, self).__init__(parent)

        list_view = QtGui.QListView()
        list_view.setModel(tulpenmanie.exchange.model)

        self.stacked_widget = QtGui.QStackedWidget()
        self.mappers = []
        for row in range(tulpenmanie.exchange.model.rowCount()):
            exchange_item = tulpenmanie.exchange.model.item(row)
            exchange_layout = QtGui.QGridLayout()
            grid_row = 0
            mapper = QtGui.QDataWidgetMapper()
            mapper.setModel(tulpenmanie.exchange.model)
            mapper.setRootIndex(exchange_item.index())
            mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.AutoSubmit)
            self.mappers.append(mapper)

            for setting, column in exchange_item.mappings:
                # TODO get required length if any and set that to
                # the edit length, or make a validator
                label = QtGui.QLabel(setting)
                if column in exchange_item.numeric_settings:
                    edit = QtGui.QDoubleSpinBox()
                elif column in exchange_item.boolean_settings:
                    edit = QtGui.QCheckBox()
                else:
                    edit = QtGui.QLineEdit()
                    if column in exchange_item.hidden_settings:
                        edit.setEchoMode(QtGui.QLineEdit.Password)
                exchange_layout.addWidget(label, grid_row,0)
                exchange_layout.addWidget(edit, grid_row,1)
                grid_row += 1
                mapper.addMapping(edit, column)
            mapper.toFirst()
            mapper.setCurrentIndex(row)

            markets_item = exchange_item.child(0, exchange_item.MARKETS)
            market_layout = QtGui.QGridLayout()
            for row in range(markets_item.rowCount()):

                mapper = QtGui.QDataWidgetMapper()
                mapper.setModel(tulpenmanie.exchange.model)
                mapper.setRootIndex(markets_item.index())
                mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.AutoSubmit)
                self.mappers.append(mapper)

                check_state = markets_item.child(
                    row, exchange_item.MARKET_ENABLE).text() == 'true'
                remote_label = QtGui.QLabel(
                    markets_item.child(
                        row, exchange_item.MARKET_REMOTE).text())
                check_box = QtGui.QCheckBox()
                market_combo = tulpenmanie.widget.UuidComboBox()
                market_combo.setModel(tulpenmanie.market.model)
                market_combo.setModelColumn(1)
                market_combo.setEnabled(check_state)
                check_box.toggled.connect(market_combo.setEnabled)

                mapper.addMapping(check_box, exchange_item.MARKET_ENABLE)
                mapper.addMapping(market_combo,
                                  exchange_item.MARKET_LOCAL, 'currentUuid')
                mapper.toFirst()
                mapper.setCurrentIndex(row)
                market_layout.addWidget(remote_label, row,0)
                market_layout.addWidget(check_box, row,1)
                market_layout.addWidget(market_combo, row,2)

            markets_widget = QtGui.QWidget()
            markets_widget.setLayout(market_layout)
            scroll = QtGui.QScrollArea()
            scroll.setWidget(markets_widget)

            exchange_layout.addWidget(scroll, grid_row,0, 1,2)
            exchange_widget = QtGui.QWidget()
            exchange_widget.setLayout(exchange_layout)

            self.stacked_widget.addWidget(exchange_widget)

        layout = QtGui.QHBoxLayout()
        layout.addWidget(list_view)
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

        # Connections
        list_view.clicked.connect(self._exchange_changed)

    def _exchange_changed(self, exchange_index):
        row = exchange_index.row()
        self.stacked_widget.setCurrentIndex(row)

class ErrorHandling(object):

    def exchange_error_handler(self, message):
        message_box = QtGui.QMessageBox(self)
        message_box.setIcon(QtGui.QMessageBox.Warning)
        message_box.setText(message)
        message_box.exec_()


class ExchangeDockWidget(QtGui.QDockWidget, ErrorHandling):

    def __init__(self, exchange_item, exchange_market_row, parent=None):
        exchange_name = exchange_item.text()
        market_uuid = exchange_item.markets_item.child(
            exchange_market_row, exchange_item.MARKET_LOCAL).text()
        self.remote_market = str(exchange_item.markets_item.child(
            exchange_market_row, exchange_item.MARKET_REMOTE).text())
        title = exchange_name + ' ' + self.remote_market
        super(ExchangeDockWidget, self).__init__(title, parent)

        self.account_widget = None
        self.exchange_item = exchange_item
        self.market_row = exchange_market_row

        self.exchange = tulpenmanie.exchange.get_exchange_object(exchange_name)

        try:
            market_uuid = exchange_item.markets_item.child(
                exchange_market_row, exchange_item.MARKET_LOCAL).text()
            market_item = tulpenmanie.market.model.findItems(market_uuid)[0]
            local_market_row = market_item.row()

            base_uuid = tulpenmanie.market.model.item(
                local_market_row, tulpenmanie.market.model.BASE).text()
            base_search = tulpenmanie.commodity.model.findItems(
                base_uuid, QtCore.Qt.MatchExactly, 0)
            base_item = base_search[0]

            counter_uuid = tulpenmanie.market.model.item(
                local_market_row, tulpenmanie.market.model.COUNTER).text()
            counter_search = tulpenmanie.commodity.model.findItems(
                counter_uuid, QtCore.Qt.MatchExactly, 0)
            counter_item = counter_search[0]
        except IndexError:
            logger.critical("settings error, invalid model mapping in market "
                            "%s or exchange %s", market_uuid, exchange_name)
            logger.critical(msg)
            return None

        self.base_row = base_item.row()
        self.counter_row = counter_item.row()

        #Widgets
        self.widget = QtGui.QWidget(self)
        side_layout = QtGui.QGridLayout()
        side_layout.setColumnStretch(1,1)
        label_font = QtGui.QFont()
        label_font.setPointSize(7)

        row = 0
        for translation, stat in (
            (QtCore.QCoreApplication.translate(
                'ExchangeDockWidget', "ask", "best ask price"), 'ask'),
            (QtCore.QCoreApplication.translate(
                'ExchangeDockWidget', "last", "price of last trade"), 'last'),
            (QtCore.QCoreApplication.translate(
                'ExchangeDockWidget', "bid", "best bid price"), 'bid')):

            label = QtGui.QLabel(translation)
            label.setAlignment(QtCore.Qt.AlignRight)
            label.setFont(label_font)
            widget = tulpenmanie.widget.CommodityLcdWidget(self.counter_row)
            setattr(self, '{}_widget'.format(stat), widget)
            side_layout.addWidget(label, row,0)
            side_layout.addWidget(widget, row,1)
            row += 1

        self.account_layout = QtGui.QVBoxLayout()
        layout = QtGui.QHBoxLayout()
        layout.addLayout(side_layout)
        layout.addLayout(self.account_layout)
        self.widget.setLayout(layout)
        self.setWidget(self.widget)

        self.enable_exchange_action = QtGui.QAction(title, parent)
        self.enable_exchange_action.setCheckable(True)
        self.enable_exchange_action.triggered.connect(self.enable_exchange)

    def set_signal_connection_state(self, state):
        ticker_proxy = self.exchange.get_ticker_proxy(self.remote_market)
        if state:
            self.exchange.exchange_error_signal.connect(
                self.exchange_error_handler)
            ticker_proxy.ask_signal.connect(self.ask_widget.setValue)
            ticker_proxy.last_signal.connect(self.last_widget.setValue)
            ticker_proxy.bid_signal.connect(self.bid_widget.setValue)

    def closeEvent(self, event):
        self.enable_exchange(False)
        self.enable_exchange_action.setChecked(False)
        event.accept()

    def enable_exchange(self, enable):
        self.setEnabled(enable)
        self.setVisible(enable)
        self.set_signal_connection_state(enable)
        self.exchange.set_ticker_stream_state(enable, self.remote_market)

        market_item = self.exchange_item.child(0, self.exchange_item.MARKETS)
        enable_item = market_item.child(self.market_row,
                                        self.exchange_item.MARKET_ENABLE)
        if enable:
            enable_item.setText("true")
        else:
            enable_item.setText("false")

    def add_account_widget(self, widget):
        self.account_widget = widget
        self.account_layout.addWidget(widget)


class AccountWidget(QtGui.QWidget, ErrorHandling):

    #TODO funds signals should connect to multiple account widgets,
    # where accounts and commodities are the same

    def __init__(self, account_object, remote_market, parent):
        super(AccountWidget, self).__init__(parent)

        self.remote_market = str(remote_market)
        #TODO this will break if pair does not have 3 character codes
        base = self.remote_market[:3]
        counter = self.remote_market[-3:]

        # Data
        self.account = account_object

        self.asks_model = tulpenmanie.model.order.OrdersModel(
            parent.base_row, parent.counter_row, self)
        self.bids_model = tulpenmanie.model.order.OrdersModel(
            parent.base_row, parent.counter_row, self)
        self.asks_model.setHorizontalHeaderLabels(
            ("id",
             QtCore.QCoreApplication.translate('AccountWidget',
                                               "ask", "ask price"),
             QtCore.QCoreApplication.translate('AccountWidget',
                                               "amount", "ask amount")))
        self.bids_model.setHorizontalHeaderLabels(
            ("id",
             QtCore.QCoreApplication.translate('AccountWidget',
                                               "bid", "bid price"),
             QtCore.QCoreApplication.translate('AccountWidget',
                                               "amount", "bid amount")))
        # Create UI
        layout = QtGui.QGridLayout()

        base_funds_label = tulpenmanie.widget.FundsLabel(
            parent.base_row)
        counter_funds_label = tulpenmanie.widget.FundsLabel(
            parent.counter_row)

        refresh_funds_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('AccountWidget',
                                              "&refresh funds"),
            self, triggered=self.account.refresh_funds)

        funds_font = QtGui.QFont()
        funds_font.setPointSize(13)
        for label in (base_funds_label,
                      counter_funds_label):
            label.setAlignment(QtCore.Qt.AlignHCenter)
            label.setFont(funds_font)
            label.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
            label.addAction(refresh_funds_action)

        layout.addWidget(base_funds_label, 0,0, 1,3)
        layout.addWidget(counter_funds_label, 0,3, 1,3)

        self.ask_base_amount_spin = tulpenmanie.widget.CommoditySpinBox(
            parent.base_row)
        self.ask_base_amount_spin.valueChanged[float].connect(
            self.ask_base_amount_changed)

        self.bid_base_amount_spin = tulpenmanie.widget.CommoditySpinBox(
            parent.base_row)
        self.bid_base_amount_spin.valueChanged[float].connect(
            self.bid_base_amount_changed)

        self.ask_price_spin = tulpenmanie.widget.CommoditySpinBox(
            parent.counter_row)
        self.ask_price_spin.valueChanged[float].connect(self.ask_price_changed)

        self.bid_price_spin = tulpenmanie.widget.CommoditySpinBox(
            parent.counter_row)
        self.bid_price_spin.valueChanged[float].connect(self.bid_price_changed)

        self.ask_counter_amount_label = tulpenmanie.widget.CounterAmountLabel(
            parent.counter_row)
        self.ask_counter_estimate_label = tulpenmanie.widget.CounterEstimateLabel(
            parent.counter_row)
        self.bid_counter_amount_label = tulpenmanie.widget.CounterAmountLabel(
            parent.counter_row)
        self.bid_counter_estimate_label = tulpenmanie.widget.CounterEstimateLabel(
            parent.counter_row)

        ask_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('AccountWidget', "&ask",
                                              "as in ask order"))
        bid_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('AccountWidget', "&bid",
                                              "as in bid order"))
        ask_order_menu = QtGui.QMenu()
        ask_limit_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('AccountWidget', "limit order"),
            ask_button)
        ask_limit_action.setEnabled(False)
        ask_market_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('AccountWidget', "market order"),
            ask_button)
        ask_market_action.setEnabled(False)
        ask_order_menu.addAction(ask_limit_action)
        ask_order_menu.addAction(ask_market_action)
        ask_order_menu.setDefaultAction(ask_limit_action)
        ask_button.setMenu(ask_order_menu)

        bid_order_menu = QtGui.QMenu()
        bid_limit_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('AccountWidget', "limit order"),
            bid_button)
        bid_limit_action.setEnabled(False)
        bid_market_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('AccountWidget', "market order"),
            bid_button)
        bid_market_action.setEnabled(False)
        bid_order_menu.addAction(bid_limit_action)
        bid_order_menu.addAction(bid_market_action)
        bid_order_menu.setDefaultAction(bid_limit_action)
        bid_button.setMenu(bid_order_menu)

        at_seperator = QtCore.QCoreApplication.translate('AccountWidget',
                                                         "@", "amount @ price")

        layout.addWidget(self.ask_base_amount_spin, 1,0)
        layout.addWidget(QtGui.QLabel(at_seperator), 1,1)
        layout.addWidget(self.ask_price_spin, 1,2)
        layout.addWidget(ask_button, 2,0, 2,1)
        layout.addWidget(self.ask_counter_amount_label, 2,2,)
        layout.addWidget(self.ask_counter_estimate_label, 3,2,)

        layout.addWidget(self.bid_base_amount_spin, 1,3)
        layout.addWidget(QtGui.QLabel(at_seperator), 1,4)
        layout.addWidget(self.bid_price_spin, 1,5)
        layout.addWidget(bid_button, 2,3, 2,1)
        layout.addWidget(self.bid_counter_amount_label, 2,5)
        layout.addWidget(self.bid_counter_estimate_label, 3,5)

        for spin in (self.ask_base_amount_spin, self.bid_base_amount_spin,
                     self.ask_price_spin,self.bid_price_spin):
            spin.setMaximum(999999)

        # TODO these views should prefix/suffix price and amounts
        self.ask_orders_view = QtGui.QTableView()
        self.ask_orders_view.setModel(self.asks_model)
        layout.addWidget(self.ask_orders_view, 4,0, 1,3)

        self.bid_orders_view = QtGui.QTableView()
        self.bid_orders_view.setModel(self.bids_model)
        layout.addWidget(self.bid_orders_view, 4,3, 1,3)

        for view in self.ask_orders_view, self.bid_orders_view:
            view.setSelectionMode(QtGui.QListView.SingleSelection)
            view.setSelectionBehavior(QtGui.QListView.SelectRows)
            view.setColumnHidden(0, True)
            view.setShowGrid(False)
            view.verticalHeader().hide()
            view.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        self.setLayout(layout)

        #Refresh orders action
        refresh_orders_action = QtGui.QAction(
            "&refresh orders", self, triggered=self.account.refresh_orders)
        #Cancel order action
        cancel_ask_action = QtGui.QAction("&cancel ask order", self,
                                   triggered=self._cancel_ask)
        self.ask_orders_view.addAction(cancel_ask_action)
        self.ask_orders_view.addAction(refresh_orders_action)
        cancel_bid_action = QtGui.QAction("&cancel bid order", self,
                                   triggered=self._cancel_bid)
        self.bid_orders_view.addAction(cancel_bid_action)
        self.bid_orders_view.addAction(refresh_orders_action)

        # Connect to account
        base_funds_proxy = self.account.get_funds_proxy(base)
        base_funds_proxy.balance.connect(base_funds_label.setValue)
        base_funds_proxy.balance_changed.connect(
            base_funds_label.change_value)

        counter_funds_proxy = self.account.get_funds_proxy(counter)
        counter_funds_proxy.balance.connect(counter_funds_label.setValue)
        counter_funds_proxy.balance_changed.connect(
            counter_funds_label.change_value)

        self.account.exchange_error_signal.connect(self.exchange_error_handler)

        orders_proxy = self.account.get_orders_proxy(self.remote_market)
        orders_proxy.asks.connect(self.new_asks)
        orders_proxy.bids.connect(self.new_bids)
        orders_proxy.ask.connect(self.new_ask)
        orders_proxy.bid.connect(self.new_bid)
        orders_proxy.ask_cancelled.connect(self.ask_cancelled)
        orders_proxy.bid_cancelled.connect(self.bid_cancelled)

        # Check if ready to order
        # TODO this sucks, it must go
        signal_name = self.remote_market.replace('/', '_') + '_ready_signal'
        signal = getattr(self.account, signal_name)
        if hasattr(self.account, 'place_ask_limit_order'):
            signal.connect(ask_limit_action.setEnabled)
            signal.connect(bid_limit_action.setEnabled)
            ask_limit_action.triggered.connect(self._ask_limit)
            bid_limit_action.triggered.connect(self._bid_limit)
        if hasattr(self.account, 'place_ask_market_order'):
            signal.connect(ask_market_action.setEnabled)
            signal.connect(bid_market_action.setEnabled)
            ask_market_action.triggered.connect(self._ask_market)
            bid_market_action.triggered.connect(self._bid_market)

        parent.add_account_widget(self)
        parent.enable_exchange_action.toggled.connect(self.enable_account)

    def enable_account(self, enable):
        if enable:
            # TODO sometimes redundant to refresh() and refresh_orders()
            remote_market = self.remote_market.replace('/', '_')
            self.account.check_order_status(remote_market)
            self.account.refresh()

    def new_asks(self, orders):
        self.asks_model.clear_orders()
        self.asks_model.append_orders(orders)

    def new_ask(self, order):
        self.asks_model.append_orders( (order,) )

    def new_bids(self, orders):
        self.bids_model.clear_orders()
        self.bids_model.append_orders(orders)

    def new_bid(self, order):
        self.bids_model.append_orders( (order,) )

    def _ask_limit(self):
        amount = self.ask_base_amount_spin.decimal_value()
        price = self.ask_price_spin.decimal_value()
        self.account.place_ask_limit_order(self.remote_market, amount, price)

    def _bid_limit(self):
        amount = self.bid_base_amount_spin.decimal_value()
        price = self.bid_price_spin.decimal_value()
        self.account.place_bid_limit_order(self.remote_market, amount, price)

    def _ask_market(self):
        amount = self.ask_base_amount_spin.decimal_value()
        self.account.place_ask_market_order(self.remote_market, amount)

    def _bid_market(self):
        amount = self.bid_base_amount_spin.decimal_value()
        self.account.place_bid_market_order(self.remote_market, amount)

    def _cancel_ask(self):
        row = self.ask_orders_view.currentIndex().row()
        item = self.asks_model.item(row, self.asks_model.ORDER_ID)
        if item:
            order_id = item.text()
            self.account.cancel_ask_order(self.remote_market, order_id)

    def ask_cancelled(self, order_id):
        items = self.asks_model.findItems(order_id, QtCore.Qt.MatchExactly, 0)
        for item in items:
            self.asks_model.removeRow(item.row())

    def _cancel_bid(self):
        row = self.bid_orders_view.currentIndex().row()
        item = self.bids_model.item(row, self.bids_model.ORDER_ID)
        if item:
            order_id = item.text()
            self.account.cancel_bid_order(self.remote_market, order_id)

    def bid_cancelled(self, order_id):
        items = self.bids_model.findItems(order_id, QtCore.Qt.MatchExactly, 0)
        for item in items:
            self.bids_model.removeRow(item.row())

    def ask_base_amount_changed(self, base_amount):
        base_amount = decimal.Decimal(str(base_amount))
        if not base_amount:
            self.ask_counter_amount_label.clear()
            return
        price = self.ask_price_spin.decimal_value()
        if not price:
            self.ask_counter_amount_label.clear()
            return
        self.change_ask_counter(base_amount, price)

    def ask_price_changed(self, price):
        price = decimal.Decimal(str(price))
        if not price:
            self.ask_counter_amount_label.clear()
            return
        base_amount = self.ask_base_amount_spin.decimal_value()
        if not base_amount:
            self.ask_counter_amount_label.clear()
            return
        self.change_ask_counter(base_amount, price)

    def change_ask_counter(self, base_amount, price):
        counter_amount = base_amount * price
        self.ask_counter_amount_label.setValue(counter_amount)
        commission = self.account.get_commission(counter_amount,
                                                 self.remote_market)
        if commission:
            self.ask_counter_estimate_label.setValue(counter_amount - commission)
            return
        self.ask_counter_estimate_label.clear()

    def bid_base_amount_changed(self, base_amount):
        base_amount = decimal.Decimal(str(base_amount))
        if not base_amount:
            self.bid_counter_amount_label.clear()
            return
        price = self.bid_price_spin.decimal_value()
        if not price:
            self.bid_counter_amount_label.clear()
            return
        self.change_bid_counter(base_amount, price)

    def bid_price_changed(self, price):
        price = decimal.Decimal(str(price))
        if not price:
            self.bid_counter_amount_label.clear()
            return
        base_amount = self.bid_base_amount_spin.decimal_value()
        if not base_amount:
            self.bid_counter_amount_label.clear()
        else:
            self.change_bid_counter(base_amount, price)

    def change_bid_counter(self, base_amount, price):
        counter_amount = base_amount * price
        self.bid_counter_amount_label.setValue(counter_amount)
        commission = self.account.get_commission(counter_amount,
                                                 self.remote_market)
        if commission:
            self.bid_counter_estimate_label.setValue(counter_amount - commission)
        else:
            self.bid_counter_estimate_label.clear()
