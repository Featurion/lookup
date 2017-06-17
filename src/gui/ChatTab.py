from threading import Thread

from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget, QStackedWidget, QHBoxLayout, QMessageBox

from src.base import utils
from src.base.constants import INVALID_EMPTY_NAME, INVALID_NAME_CONTENT
from src.base.constants import INVALID_NAME_LENGTH, VALID_NAME, MAX_NAME_LENGTH
from src.base.constants import TITLE_INVALID_NAME, TITLE_EMPTY_NAME, EMPTY_NAME
from src.base.constants import TITLE_SELF_CONNECT, SELF_CONNECT, NAME_CONTENT
from src.base.constants import NAME_LENGTH
from src.gui.MultipleInputWidget import MultipleInputWidget
from src.gui.ConnectingWidget import ConnectingWidget
from src.gui.ChatWidget import ChatWidget


class ChatTab(QWidget):

    new_message_signal = pyqtSignal(str, float)
    zone_redy_signal = pyqtSignal()

    def __init__(self, interface):
        QWidget.__init__(self)

        self.interface = interface
        self.__zone = None
        self.__unread = 0

        self.widget_stack = QStackedWidget(self)
        self.input_widget = MultipleInputWidget(self,
                                                'images/new_chat.png', 150,
                                                'Usernames:', 'LookUp',
                                                self.connect, self.addInput)
        self.chat_widget = ChatWidget(self)
        self.widget_stack.addWidget(self.input_widget)
        self.widget_stack.addWidget(ConnectingWidget(self))
        self.widget_stack.addWidget(self.chat_widget)
        self.widget_stack.setCurrentIndex(0)

        self.new_message_signal.connect(self.newMessage)
        self.zone_redy_signal.connect(self.redy)

        _layout = QHBoxLayout()
        _layout.addWidget(self.widget_stack)
        self.setLayout(_layout)

    def exit(self):
        return NotImplemented

    def getClient(self):
        return self.interface.getClient()

    def getZone(self):
        return self.__zone

    def setZone(self, zone):
        if self.getZone() is None:
            self.__zone = zone
        else:
            self.notify.critical('suspicious attempt to change zone')

    def addInput(self):
        _iw = MultipleInputWidget(*self.input_widget._data,
                                  self.input_widget.getInputsText(),
                                  len(self.input_widget.inputs) + 1)
        self.widget_stack.removeWidget(self.input_widget)
        self.input_widget = _iw
        self.widget_stack.insertWidget(0, self.input_widget)
        self.widget_stack.setCurrentIndex(0)

    def connect(self, names):
        for name in set(names):
            status = utils.isNameInvalid(name)
            msg = None

            if name == self.interface.getClient().getName():
                msg = (TITLE_SELF_CONNECT, SELF_CONNECT)
            elif status == INVALID_NAME_CONTENT:
                msg = (TITLE_INVALID_NAME, NAME_CONTENT)
            elif status == INVALID_NAME_LENGTH:
                msg = (TITLE_INVALID_NAME, NAME_LENGTH)
            elif status == INVALID_EMPTY_NAME:
                msg = (TITLE_EMPTY_NAME, EMPTY_NAME)
            else:
                pass

            if msg:
                QMessageBox.warning(self, *msg)
                names.remove(name)

        titled_names = utils.oxfordComma(names)
        self.widget_stack.widget(1).setConnectingToName(titled_names)
        self.widget_stack.setCurrentIndex(1)
        self.interface.getWindow().setTabTitle(self, titled_names)

        Thread(target=self.interface.getClient().requestNewZone,
               args=(self, sorted(names)),
               daemon=True).start()

    @pyqtSlot(str, float)
    def newMessage(self, msg, ts):
        self.chat_widget.log.addMessage(msg, ts)

        scrollbar = self.chat_widget.chat_log.verticalScrollBar()
        if scrollbar.value() == scrollbar.maximum():
            scrollbar.setValue(scrollbar.maximum())

    @pyqtSlot()
    def redy(self):
        self.widget_stack.setCurrentIndex(2)
