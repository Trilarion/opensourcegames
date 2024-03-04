"""
Simple UI helpers with PyQt
"""

import sys
from PySide6 import QtCore, QtGui, QtWidgets


def exception_hook(type, value, traceback):
    """
    Use sys.__excepthook__, the standard hook.
    """
    sys.__excepthook__(type, value, traceback)


def run_simple_button_app(title, actions):
    """

    :param title:
    :param actions:
    :return:
    """
    # fix PySide6 eating exceptions (see http://stackoverflow.com/q/14493081/1536976)
    sys.excepthook = exception_hook

    # create app
    app = QtWidgets.QApplication([])

    # create single widget
    widget = QtWidgets.QWidget()
    widget.setWindowTitle(title)
    widget.setMinimumSize(200, 200)

    # add actions
    layout = QtWidgets.QVBoxLayout(widget)
    for name, action in actions.items():
        button = QtWidgets.QPushButton(name)
        button.clicked.connect(action)
        layout.addWidget(button)
    layout.addStretch()

    # execute app
    widget.show()
    return app.exec_()