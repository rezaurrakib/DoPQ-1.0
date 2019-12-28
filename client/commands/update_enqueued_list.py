import sys
from client.commands import float_win_layout

from PyQt5 import QtCore
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QHBoxLayout, QListWidget, QLayout, QFormLayout
from PyQt5.QtWidgets import QListWidgetItem, QCheckBox, QLabel, QDialogButtonBox, QWidget, QApplication


class CustomWidget(QWidget):
    def __init__(self):
        super(CustomWidget, self).__init__()
        self.widget_layout = QHBoxLayout()
        self.text_label = QLabel()
        self.chkbox = QCheckBox()
        self.widget_layout.setSizeConstraint(QLayout.SetFixedSize)
        self.widget_layout.addWidget(self.chkbox)
        self.widget_layout.addStretch()
        self.widget_layout.setSpacing(20)
        self.widget_layout.addWidget(self.text_label)
        self.setLayout(self.widget_layout)

    def set_text(self, html_txt):
        self.text_label.setText(html_txt)
        new_font = QFont("Arial", 10, QFont.Bold)
        self.text_label.setFont(new_font)
        self.text_label.adjustSize()


class FloatingWindow(QWidget):
    def __init__(self, server_obj):
        super(FloatingWindow, self).__init__()
        self.server_obj = server_obj
        self.setWindowTitle("Update Enqueued Container List")
        icon = QIcon("../asset_files/update_cont.png")
        self.setWindowIcon(icon)
        self.setWindowFlags(QtCore.Qt.WindowTitleHint)
        self.container_list = []
        self.selected = []
        self.container_counter = 0  # Global counter for the Enqueued container
        self.list_checkbox = []  # List of checkboxes for each QLabel
        self.list_enq_labels = []  # List of the QLabels containing container info.
        self.data = []

    def create_enqueued_list(self, data):
        form_layout = QFormLayout()
        list_widget = QListWidget()
        list_widget.setMinimumHeight(700)

        for container in data:
            print("Read the enqueued data ......... ")
            custom_widget = CustomWidget()
            html_text = float_win_layout.history_containers_richtext_formatting(container, self.container_counter)
            custom_widget.set_text(html_text)
            self.list_checkbox.append(custom_widget.chkbox)
            self.list_enq_labels.append(custom_widget.text_label)

            item_wid = QListWidgetItem()
            item_wid.setSizeHint(custom_widget.sizeHint())
            list_widget.addItem(item_wid)
            list_widget.setItemWidget(item_wid, custom_widget)
            self.container_counter += 1
            self.container_list.append(container)

        self.setMinimumWidth(620)
        self.label_result = QLabel()

        # Define the QformLayout
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        form_layout.addWidget(list_widget)
        form_layout.addWidget(buttonBox)
        form_layout.addWidget(self.label_result)
        self.setLayout(form_layout)
        buttonBox.accepted.connect(self.checkboxChanged)
        buttonBox.rejected.connect(self.close)
        self.show()
    
    def closeEvent(self, event):
        print('Window is closed, closeEvent() has been called')
        self.server_obj.delete_req_enqueued_containers(self.selected)
        print('event: {0}'.format(event))
        event.accept()

    def checkboxChanged(self):
        print("Call is in checkboxChanged")
        self.label_result.setText("")
        self.selected_txt = ""

        for i, v in enumerate(self.list_checkbox):
            if v.checkState():
                self.selected_txt += "Cont_" + str(i) + " , "
                self.selected.append(self.container_list[i])
        print("Selected buttons: ", self.selected_txt)
        self.label_result.setText("{}, {}".format(self.label_result.text(), self.selected_txt))
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    clock = FloatingWindow()
    clock.show()
    sys.exit(app.exec_())
