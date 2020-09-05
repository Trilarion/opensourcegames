"""
Simple UI helpers with PyQt
"""

from PyQt5 import QtCore, QtGui, QtWidgets


def run_simple_button_app(title, actions):
    """

    :param title:
    :param actions:
    :return:
    """
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