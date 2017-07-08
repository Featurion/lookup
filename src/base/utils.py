import datetime
import os
import re

from src.base.constants import INVALID_EMPTY_NAME, INVALID_NAME_CONTENT
from src.base.constants import INVALID_NAME_LENGTH, VALID_NAME, MAX_NAME_LENGTH

def isNameInvalid(name):
    if not name:
        return INVALID_EMPTY_NAME
    elif not name.isalnum():
        return INVALID_NAME_CONTENT
    elif len(name) > MAX_NAME_LENGTH:
        return INVALID_NAME_LENGTH
    else:
        return VALID_NAME

def getTimestamp():
    return datetime.datetime.now().timestamp()

def parseTimestampFromMessage(msg):
    ts = re.search('\d+\.\d+', msg).group()
    ts = datetime.datetime.fromtimestamp(float(ts)).timestamp()
    msg = re.sub(str(ts), '({0})', msg)
    return (msg, ts)

def formatTimestamp(ts):
    return str(datetime.datetime.fromtimestamp(float(ts)).strftime('%H:%M:%S'))

def getResourcePath(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        try:
            base_path = os.path.dirname(sys.modules[''].__file__)
        except Exception:
            base_path = ''

        if not os.path.exists(os.path.join(base_path, relative_path)):
            base_path = ''

    path = os.path.join(base_path, relative_path)

    if not os.path.exists(path):
        return None
    else:
        return path

def secureStrCmp(left, right):
    equal = True

    if len(left) != len(right):
        equal = False

    for a, b in zip(left, right):
        if a != b:
            equal = False

    return equal

def centerWindow(window):
    from PyQt5.QtWidgets import QDesktopWidget
    centerPoint = QDesktopWidget().availableGeometry().center()
    geo = window.frameGeometry()
    geo.moveCenter(centerPoint)
    window.move(geo.topLeft())

def resizeWindow(window, width, height):
    window.setGeometry(0, 0, width, height)

def showDesktopNotification(tray_icon, title, message):
    tray_icon.showMessage(title, message)

def oxfordComma(list_of_strings):
    len_ = len(list_of_strings)
    if len_ == 0:
        return ''
    elif len_ == 1:
        return list_of_strings[0]
    elif len_ == 2:
        return ' and '.join(list_of_strings)
    else:
        str_ = ', '.join(list_of_strings[:-1] + [''])
        str_ += 'and ' + list_of_strings[-1]
        return str_