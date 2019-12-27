import sys
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtWidgets import QDialogButtonBox, QLineEdit, QFormLayout, QLabel


class ClearHistory(QWidget):
    def __init__(self, server_obj):
        super(ClearHistory, self).__init__()
        self.setWindowTitle("Caution!")
        icon = QtGui.QIcon("caution.png")
        self.setWindowIcon(icon)
        self.resize(450, 100)
        self.server_obj = server_obj
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.label = QLabel()
        self.label.setText("<b><font color=red>Careful! You are about to clear the DoPQ History."
                           "</font><br>Provide <font color=green>Username</font> and <font color=green>Password</font> to proceed ...</b>")
        form_layout = QFormLayout()
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        form_layout.addWidget(self.label)
        form_layout.addRow("<font color=#00008b><b>Username: </b></font>", self.username)
        form_layout.addRow("<font color=#00008b><b>Password: </b></font>", self.password)
        form_layout.addWidget(buttonBox)
        self.setLayout(form_layout)

        buttonBox.accepted.connect(self.get_input)
        buttonBox.rejected.connect(self.close_diaglog)
        self.show()

    def get_input(self):
        print('OK clicked')
        info = [self.username.text(), self.password.text()]
        print(info)
        self.server_obj.clear_dopq_history(info)
        self.close()

    def close_diaglog(self):
        print("Cancel Clicked!")
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    clr_hist = ClearHistory("sdkslkd")
    sys.exit(app.exec_())