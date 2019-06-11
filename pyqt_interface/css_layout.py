import os

main_window_layout = """
            QWidget{
                background-color: rgb(250,250,210);
                margin:5px;
            }
            """

userstats_title_bar = """
            QLabel{
                color: rgb(0, 0, 0);
                font: Times New Roman;
                font-family: New Century Schoolbook;
                font-size: 12pt;
                font-weight: bold;
                background: qradialgradient(cx:0, cy:0, radius: 1, fx:0.5, fy:0.5, stop:0 rgb(25, 255, 217), stop:1 rgb(0,204, 68));
                border-radius: 5px;
                border-width: 2px;
                border-style: solid;
                border-color: black;
                text-align: right;
            }
            """

status_title_bar = """
            QLabel{
                color: rgb(0, 0, 0);
                font: Times New Roman;
                font-family: New Century Schoolbook;
                font-size: 12pt;
                font-weight: bold;
                background: qradialgradient(cx:0, cy:0, radius: 1, fx:0.5, fy:0.5, stop:0 rgb(25, 255, 217), stop:1 rgb(0,204, 68));
                border-radius: 5px;
                border-width: 2px;
                border-style: solid;
                border-color: black;
                text-align: right;
            }
            """

running_cont_title_bar = """
            QLabel{
                color: rgb(0, 0, 0);
                font: Times New Roman;
                font-family: New Century Schoolbook;
                font-size: 12pt;
                font-weight: bold;
                background: qradialgradient(cx:0, cy:0, radius: 1, fx:0.5, fy:0.5, stop:0 rgb(128, 255, 128), stop:1 rgb(128, 0, 255));
                border-radius: 5px;
                border-width: 2px;
                border-style: solid;
                border-color: black;
                text-align: right;
            }
            """

enqueued_cont_title_bar = """
            QLabel{
                color: rgb(0, 0, 0);
                font: Times New Roman;
                font-family: New Century Schoolbook;
                font-size: 12pt;
                font-weight: bold;
                background: qradialgradient(cx:0, cy:0, radius: 1, fx:0.5, fy:0.5, stop:0 rgb(25, 102, 255), stop:1 rgb(25, 255, 102));
                border-radius: 5px;
                border-width: 2px;
                border-style: solid;
                border-color: black;
                text-align: right;
            }
            """

history_title_bar = """
            QLabel{
                color: rgb(0, 0, 0);
                font: Times New Roman;
                font-family: New Century Schoolbook;
                font-size: 12pt;
                font-weight: bold;
                background: qradialgradient(cx:0, cy:0, radius: 1, fx:0.5, fy:0.5, stop:0 rgb(255, 25, 255), stop:1 rgb(68, 0, 204));
                border-radius: 5px;
                border-width: 2px;
                border-style: solid;
                border-color: black;
                text-align: right;
            }
            """


dockwidget_layout = """
            QWidget{
                color: rgb(250,250,210);
                font: Times New Roman;
                font-size: 11pt;
                background-color: rgb(0, 11, 0);
                border-radius: 10px;
                border-width: 3px;
                border-color: rgb(75, 75, 75);
                border-style: solid;
            }
            """

# Layout for the Main Window Header section

dockwidget_main_header_layout = """
            QWidget{
                color: rgb(250,250,210);
                font: Times New Roman;
                font-size: 13pt;
                background: qradialgradient(cx:0, cy:0, radius: 1, fx:0.5, fy:0.5, stop:0 rgb(0, 255, 25), stop:1 rgb(25, 25, 255));
                border-radius: 10px;
                border-width: 3px;
                border-color: rgb(75, 75, 75);
                border-style: solid;
            }
            """

main_header_label_layout = """
            QLabel{
                color: rgb(0, 0,210);
                font: Times New Roman;
                font-size: 13pt;
                font-weight: bold;
                border-radius: 10px;
                border-width: 3px;
                border-color: rgb(75, 75, 75);
                border-style: solid;
            }
            """
