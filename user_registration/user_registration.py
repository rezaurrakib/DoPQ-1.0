import re
import sys
import hashlib
import pickledb

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLineEdit, QLabel, QDialog, QFrame, QMessageBox

__authors__ = "Md Rezaur Rahman"
__copyright__ = "Copyright 2019, The DopQ Project"
__license__ = "GPL"


class UserRegistration(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.dialog = QDialog()
        self.set_form()
        self.create_background()
        self.create_frame_layout()
        self.prepare_widgets()

    def set_form(self):
        self.dialog.setObjectName("Dialog")
        self.dialog.resize(1098, 844)
        self.dialog.setStyleSheet("background-color: rgb(0, 0, 0);")

    def create_background(self):
        self.image_label = QLabel(self.dialog)
        self.image_label.setGeometry(QtCore.QRect(20, 250, 380, 300))
        pixmap = QtGui.QPixmap("dopq_logo.png")
        pixmap = pixmap.scaled(self.image_label.width(), self.image_label.height())
        self.image_label.setPixmap(pixmap)
        self.image_label.setObjectName("image_label")

    def set_label_font(self):
        font = QtGui.QFont()
        font.setFamily("Cookie")
        font.setPointSize(18)
        return font

    def create_frame_layout(self):
        """
        Layout for the User Registration Window
        :return:
        """
        self.frame = QFrame(self.dialog)
        self.frame.setGeometry(QtCore.QRect(410, 40, 611, 751))
        #self.frame.setStyleSheet("background-color: rgb(133, 94, 66);")
        self.frame.setStyleSheet("background-color: rgb(0, 128, 240);")

        self.label_title = QLabel(self.frame)
        self.label_title.setGeometry(QtCore.QRect(150, 50, 420, 50))
        self.label_title.setFont(self.set_label_font())
        self.label_title.setStyleSheet("color: rgb(54, 38, 27);")
        self.label_title.setObjectName("label_title")

        self.username_field = QLineEdit(self.frame)
        self.username_field.setGeometry(QtCore.QRect(90, 160, 421, 51))
        self.username_field.setStyleSheet("background-color: rgb(213, 213, 213);")
        self.username_field.setObjectName("username_field")
        self.username_field.setReadOnly(False)

        self.password_field = QLineEdit(self.frame)
        self.password_field.setGeometry(QtCore.QRect(90, 250, 421, 51))
        self.password_field.setStyleSheet("background-color: rgb(213, 213, 213);")
        self.password_field.setObjectName("password_field")
        self.password_field.setReadOnly(False)

        self.retype_pass_field = QLineEdit(self.frame)
        self.retype_pass_field.setGeometry(QtCore.QRect(90, 350, 421, 51))
        self.retype_pass_field.setStyleSheet("background-color: rgb(213, 213, 213);")
        self.retype_pass_field.setObjectName("retype_pass_field")
        self.retype_pass_field.setReadOnly(False)

        self.email_field = QLineEdit(self.frame)
        self.email_field.setGeometry(QtCore.QRect(90, 440, 421, 51))
        self.email_field.setStyleSheet("background-color: rgb(213, 213, 213);")
        self.email_field.setObjectName("email_field")
        self.email_field.setReadOnly(False)

        self.signup_button = QPushButton(self.frame)
        self.signup_button.setGeometry(QtCore.QRect(90, 630, 421, 51))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.signup_button.setFont(font)
        self.signup_button.setStyleSheet("background-color: rgb(0, 98, 102);")
        self.signup_button.setObjectName("signup_button")

    def prepare_widgets(self):
        self.dialog.setWindowTitle("Docker Priority Queue-[DoPQ] User Registration")
        self.label_title.setText("<span style='font-family:Georgia, serif;'>DoPQ User Registration</span>")
        self.username_field.setText("Username")
        self.password_field.setText("Password")
        self.retype_pass_field.setText("Retype Password")
        self.email_field.setText("Email")
        self.signup_button.setText("Sign Up")

        self.signup_button.clicked.connect(self.check_user_info)

    def check_user_info(self):
        username = self.username_field.text()  # It should be unique
        password = self.password_field.text()
        re_pass = self.retype_pass_field.text()
        email = self.email_field.text()

        # Load the Database from the address
        db_location = "/home/reza/Desktop/lmu_augenKlinikRepo/dopq_user_database/dopq_database.db" # If No DB exist, it will create one
        db = pickledb.load(db_location, True)  # 'True' for dump the db object.
        self.print_db_info(db)

        if db.exists(username):
            self.show_failure_msg("duplicate_username")
            return False

        if password != re_pass:
            self.show_failure_msg("wrong_pswd_match")
            return False

        if self.is_invalid_email(email):
            self.show_failure_msg("invalid_email")
            return False

        # If all information are valid, return true
        usr_field = self.prepare_userinfo_field(password, email)
        db.set(username, usr_field)  # Save user's information into the database
        self.show_success_msg()

    def print_db_info(self, db_obj):
        getall_keys = db_obj.getall()
        for k in getall_keys:
            print("Key: ", k, " Value: ", db_obj.get(k))

    def is_invalid_email(self, email_str):
        regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
        if re.search(regex, email_str):
            return False
        else:
            return True

    def show_failure_msg(self, reason_txt):
        failure_msg = QMessageBox()
        failure_msg.setIcon(QMessageBox.Warning)
        failure_msg.setWindowTitle("Warning!")
        if reason_txt == "duplicate_username":
            failure_msg.setText('Username Already exist. Please try with different Username!')
        elif reason_txt == "wrong_pswd_match":
            failure_msg.setText('Password does not match. Please try again!')
        elif reason_txt == "invalid_email":
            failure_msg.setText('Invalid email address. Please try again!')

        failure_msg.setStandardButtons(QMessageBox.Ok)

        return_value = failure_msg.exec()
        if return_value == QMessageBox.Ok:
            print('OK clicked for failed try.')

    def show_success_msg(self):
        success_msg = QMessageBox()
        success_msg.setIcon(QMessageBox.Information)
        success_msg.setWindowTitle("Congratulations!")
        success_msg.setText('Your DoPQ account has been created successfully...')
        success_msg.setStandardButtons(QMessageBox.Ok)

        return_value = success_msg.exec()
        if return_value == QMessageBox.Ok:
            print('OK clicked')
            QtCore.QCoreApplication.quit()

    def prepare_userinfo_field(self, password, email):
        user_field = {}
        # Encrypt the password
        encd = password.encode()
        res = hashlib.md5(encd)
        encrptd_pass = res.hexdigest()

        user_field["password"] = encrptd_pass
        user_field["email"] = email
        return user_field


if __name__ == "__main__":
    app = QApplication(sys.argv)
    db_location = "/home/reza/Desktop/lmu_augenKlinikRepo/dopq_user_database/dopq_database.db"  # If No DB exist, it will create one
    db = pickledb.load(db_location, True)  # 'True' for dump the db object.
    obj = UserRegistration()
    obj.print_db_info(db)
    obj.dialog.show()
    sys.exit(app.exec_())