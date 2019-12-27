import os

MAIN_HEADER_HTML = """<font color="#ff0000">Do</font><font color='darkturquoise'>cker</font> 
                    <font color="#ff0000">P</font><font color='darkturquoise'>riority</font>  
                    <font color="#ff0000">Q</font><font color='darkturquoise'>ueue</font>
                    <font color="#2300fe">!</font>"""
USER_STAT_TITLE_HTML = """<span style='color:#000000; font-family:Georgia, serif; font-size=16'><b> User Statistics </b></span>"""
STATUS_TITLE_HTML = """<span style='color:#000000; font-family:Georgia, serif; font-size=16'><b> DoPQ Status </b></span>"""
RUNNING_CONT_TITLE_HTML = """<span style='color:#000000; font-family:Georgia, serif; font-size=16'><b> Running Containers </b></span>"""
ENQUEUED_CONT_TITLE_HTML = """<span style='color:#000000; font-family:Georgia, serif; font-size=16'><b> Enqueued Containers </b></span>"""
HISTORY_TITLE_HTML = """<span style='color:#000000; font-family:Georgia, serif; font-size=16'><b> History </b></span>"""


def history_containers_richtext_formatting(container, cnt):
    html_text = ""
    html_text += "<span style='color:#8b4513;'><b> <u>Container No.:</u> " + str(cnt) + "</b></span>"
    html_text += "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
    html_text += "<u>Container Name: </u><span style='color:salmon;'><b>" + container["name"] + "</span></b>"
    html_text += "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
    html_text += "<u>Container Status: </u><span style='color:red;'><b>" + container["status"] + "</span></b>"
    html_text += "<table>"
    html_text += "<tr>"
    html_text += "<th width='18%'></th>"
    html_text += "<th width='15%'></th>"
    html_text += "<th width='18%'></th>"
    html_text += "<th width='15%'></th>"
    html_text += "</tr>"

    html_text += "<tr>"
    html_text += "<td> <p align='right'> Docker Name: </td>"

    if container['docker name'] == "":
        html_text += "<td> <p align='left'> <font color='darkcyan' size='2'><b>Not Assigned</b></font></td>"
    else:
        html_text += "<td> <p align='left'> <font color='green'><b>" + container['docker name'] + "</b></font></td>"

    html_text += "<td> <p align='right'> Executor: </td>"
    html_text += "<td> <p align='left'> <font color='Yellow'><b>" + container['executor'] + "</b></font></td>"
    html_text += "</tr>"

    html_text += "<tr>"
    html_text += "<td> <p align='right'> Uptime: </td>"
    if container['run_time']== "":
        html_text += "<td> <p align='left'> <font color='darkcyan' size='2'> <b>Not Yet Started</b></font></td>"
    else:
        html_text += "<td> <p align='left'> <font color='Yellow'><b>" + container['run_time'] + "</b></font></td>"

    html_text += "<td> <p align='right'> Created: </td>"
    if container['created']== "":
        html_text += "<td> <p align='left'> <font color='darkcyan' size='2'><b>Not Yet Created</b></font></td>"
    else:
        html_text += "<td> <p align='left'> <font color='Yellow'> <b>" + container['created'] + "</b></font></td>"
    html_text += "</tr>"
    html_text += "</table>"

    return html_text


def dopq_status_widget_richtext_formatting(data):
    # Formatting
    if data['Queue Status'] == "running":
        data['Queue Status'] = "Running"

    if data['Provider Status'] == "running":
        data['Provider Status'] = "Running"

    html_text = ""
    html_text += "<table>"
    html_text += "<tr>"
    html_text += "<th width='15%'></th>"
    html_text += "<th width='15%'></th>"
    html_text += "</tr>"
    html_text += "<tr>"
    html_text += "<td> <p align='left'> <font color=#1261a0><u><b>Priority Queue Status:</b></u></td>"
    html_text += "<td> <p align='center'> <font color=#ff4d00><b>" + data['Queue Status'] + " ... </b></font></td>"
    html_text += "</tr>"

    html_text += "<tr>"
    html_text += "<th width='15%'></th>"
    html_text += "<th width='10%'></th>"
    html_text += "<th width='18%'></th>"
    html_text += "<th width='15%'></th>"
    html_text += "</tr>"

    html_text += "<tr>"
    html_text += "<td> <p align='right'> <font color=green><b>Uptime:</b></td>"
    html_text += "<td> <p align='center'> <font color=#ffffff><b>" + data["Queue Uptime"] + "</b></font></td>"
    html_text += "<td> <p align='center'> <font color=#ff7a01><b>Launched Since:</b></td>"
    html_text += "<td> <p align='center'> <font color=#ffffff><b>" + data["Queue Starttime"] + "</b></font></td>"
    html_text += "</tr>"


    html_text += "<tr>"
    html_text += "<th width='12%'></th>"
    html_text += "<th width='15%'></th>"
    html_text += "</tr>"
    html_text += "<tr>"
    html_text += "<td> <p align='right'> <font color=#1261a0><u><b>Provider Status:</b></u></td>"
    html_text += "<td> <p align='center'> <font color=#ff4d00><b>" + data["Provider Status"] + " ... </b></font></td>"
    html_text += "</tr>"

    html_text += "<tr>"
    html_text += "<th width='15%'></th>"
    html_text += "<th width='10%'></th>"
    html_text += "<th width='18%'></th>"
    html_text += "<th width='15%'></th>"
    html_text += "</tr>"

    html_text += "<tr>"
    html_text += "<td> <p align='right'> <font color=green><b>Uptime:</b></td>"
    html_text += "<td> <p align='center'> <font color=#ffffff><b>" + data["Provider Uptime"] + "</b></font></td>"
    html_text += "<td> <p align='center'> <font color=#ff7a01><b>Launched Since:</b></td>"
    html_text += "<td> <p align='center'> <font color=#ffffff><b>" + data["Provider Starttime"] + "</b></font></td>"
    html_text += "</tr>"
    html_text += "</table>"

    return html_text


def user_status_widget_richtext_formatting(container):
    html_text = ""
    html_text += "<table>"
    html_text += "<tr>"
    html_text += "<th width='12%'></th>"
    html_text += "<th width='15%'></th>"
    html_text += "<th width='15%'></th>"
    html_text += "<th width='15%'></th>"
    html_text += "<th width='18%'></th>"
    html_text += "<th width='7%'></th>"
    html_text += "<th width='18%'></th>"
    html_text += "<th width='7%'></th>"
    html_text += "</tr>"

    html_text += "<tr>"
    html_text += "<td> <p align='right'> <font color=#1261a0><u><b>User:</b></u></td>"
    html_text += "<td> <p align='center'> <font color='salmon'><b>" + container['user'] + "</b></font></td>"
    html_text += "<td> <p align='right'> <font color='red'><b><u>Penalty:</u><b></td>"
    html_text += "<td> <p align='center'> <b><font color=#1261a0>" + str(container['penalty']) + "</font></b></td>"
    html_text += "<td> <p align='right'> <font color='#ff7a01'><b>Containers Run:</b></font></td>"
    html_text += "<td> <p align='left'><b>" + str(container['containers run']) + "</b></td>"
    html_text += "<td> <p align='right'> <font color='green'><b>Containers Enqueued:</b></font></td>"
    html_text += "<td> <p align='left'><b>" + str(container['containers enqueued']) + "</b></td>"
    html_text += "</tr>"
    html_text += "</table>"

    return html_text


def running_containers_richtext_formatting(container, cnt):
    html_text = ""
    html_text += "<span style='color:#ff0000;'><b><u> Container No.:</u> " + str(cnt) + "</b></span>"
    html_text += "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
    html_text += "<u>Container Name:</u> <span style='color:salmon;'><b>" + container["name"] + "</b></span>"
    html_text += "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
    html_text += "<u>Container Status:</u> <span style='color:red;'><b>" + container["status"] + "</b></span>"
    html_text += "<table>"
    html_text += "<tr>"
    html_text += "<th width='20%'></th>"
    html_text += "<th width='20%'></th>"
    html_text += "<th width='20%'></th>"
    html_text += "<th width='20%'></th>"
    html_text += "</tr>"

    html_text += "<tr>"
    html_text += "<td> <p align='right'> Docker Name: </td>"

    if container['docker name'] == "":
        html_text += "<td> <p align='left'> <font color='darkcyan' size='2'><b>Not Assigned</b></font></td>"
    else:
        html_text += "<td> <p align='left'> <font color='green'><b>" + container['docker name'] + "</b></font></td>"

    html_text += "<td> <p align='right'> Executor: </td>"
    html_text += "<td> <p align='left'> <font color='Yellow'><b>" + container['executor'] + "</b></font></td>"
    html_text += "</tr>"

    html_text += "<tr>"
    html_text += "<td> <p align='right'> Uptime: </td>"
    if container['run_time']== "":
        html_text += "<td> <p align='left'> <font color='darkcyan' size='2'> <b>Not Yet Started</b></font></td>"
    else:
        html_text += "<td> <p align='left'> <font color='Yellow'><b>" + container['run_time'] + "</b></font></td>"

    html_text += "<td> <p align='right'> Created: </td>"
    if container['created']== "":
        html_text += "<td> <p align='left'> <font color='darkcyan' size='2'><b>Not Yet Created</b></font></td>"
    else:
        html_text += "<td> <p align='left'> <font color='Yellow'> <b>" + container['created'] + "</b></font></td>"
    html_text += "</tr>"

    html_text += "<tr>"
    html_text += "<td> <p align='right'> CPU Usage: </td>"
    if container['cpu'] is None:
        html_text += "<td> <p align='left'> <font color='darkcyan' size='2'> <b>None</b></font></td>"
    else:
        html_text += "<td> <p align='left'> <font color='Yellow'><b>" + container['cpu'] + "</b></font></td>"

    html_text += "<td> <p align='right'> Memory Usage: </td>"
    if container['memory'] is None:
        html_text += "<td> <p align='left'> <font color='darkcyan' size='2'><b>None</b></font></td>"
    else:
        html_text += "<td> <p align='left'> <font color='Yellow'> <b>" + container['memory'] + "</b></font></td>"
    html_text += "</tr>"


    html_text += "<tr>"
    html_text += "<td> <p align='right'> GPU Minor: </td>"
    gpu_info = container['gpu']
    if str(gpu_info[0]['id']) is None:
        html_text += "<td> <p align='left'> <font color='darkcyan'> <b>None</b></font></td>"
    else:
        html_text += "<td> <p align='left'> <font color='Yellow'><b>" + str(gpu_info[0]['id']) + "</b></font></td>"

    html_text += "<td> <p align='right'> GPU Usage: </td>"

    if str(gpu_info[0]['usage']) is None:
        html_text += "<td> <p align='left'> <font color='darkcyan' size='2'><b>None</b></font></td>"
    else:
        html_text += "<td> <p align='left'> <font color='Yellow'> <b>" + str(gpu_info[0]['usage']) + "</b></font></td>"
    html_text += "</tr>"

    html_text += "</table>"

    return html_text


def enqueued_containers_richtext_formatting(container, cnt):
    html_text = ""
    html_text += "<span style='color:#ff0000;'><b> Container No.: " + str(cnt) + "</b></span>"
    html_text += "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
    html_text += "Container Name: <span style='color:#00ff00;'><b>" + container["name"] + "</b></span>"
    html_text += "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
    html_text += "Container Status: <span style='color:#00ff00;'><b>" + container["status"] + "</b></span>"
    html_text += "<hr>"
    html_text += "<table>"
    html_text += "<tr>"
    html_text += "<th width='25%'></th>"
    html_text += "<th width='20%'></th>"
    html_text += "<th width='25%'></th>"
    html_text += "<th width='25%'></th>"
    html_text += "</tr>"

    html_text += "<tr>"
    html_text += "<td> <p align='right'> Docker Name: </td>"

    if container['docker name'] == "":
        html_text += "<td> <p align='left'> <font color='darkcyan' size='2'><b>Not Assigned</b></font></td>"
    else:
        html_text += "<td> <p align='left'> <font color='green'><b>" + container['docker name'] + "</b></font></td>"

    html_text += "<td> <p align='right'> Executor: </td>"
    html_text += "<td> <p align='left'> <font color='Yellow'><b>" + container['executor'] + "</b></font></td>"
    html_text += "</tr>"
    html_text += "<tr>"
    html_text += "<td> <p align='right'> Uptime: </td>"

    if container['run_time']== "":
        html_text += "<td> <p align='left'> <font color='darkcyan' size='2'> <b>Not Yet Started</b></font></td>"
    else:
        html_text += "<td> <p align='left'> <font color='Yellow'><b>" + container['run_time'] + "</b></font></td>"

    html_text += "<td> <p align='right'> Created: </td>"

    if container['created']== "":
        html_text += "<td> <p align='left'> <font color='darkcyan' size='2'><b>Not Yet Created</b></font></td>"
    else:
        html_text += "<td> <p align='left'> <font color='Yellow'> <b>" + container['created'] + "</b></font></td>"

    html_text += "</tr>"
    html_text += "</table>"

    return html_text


main_window_layout = """
            QWidget{
                background-color: rgb(240, 255, 240);
                margin:2px;
            }
            """

userstats_title_bar = """
            QLabel{
                color: rgb(0, 0, 0);
                background: qradialgradient(cx:0, cy:0, radius: 1, fx:0.5, fy:0.5, stop:0 rgb(25, 102, 255), stop:1 rgb(220,20,60));
                border-radius: 5px;
                border-width: 2px;
                border-style: solid;
                border-color: black;
            }
            """

status_title_bar = """
            QLabel{
                color: rgb(0, 0, 0);
                background: qradialgradient(cx:0, cy:0, radius: 1, fx:0.5, fy:0.5, stop:0 rgb(25, 102, 255), stop:1 rgb(178,34,34));
                border-radius: 5px;
                border-width: 2px;
                border-style: solid;
                border-color: black;
            }
            """

running_cont_title_bar = """
            QLabel{
                color: rgb(0, 0, 0);
                background: qradialgradient(cx:0, cy:0, radius: 1, fx:0.5, fy:0.5, stop:0 rgb(128, 255, 128), stop:1 rgb(128, 0, 255));
                border-radius: 5px;
                border-width: 2px;
                border-style: solid;
                border-color: black;
            }
            """

enqueued_cont_title_bar = """
            QLabel{
                color: rgb(0, 0, 0);
                background: qradialgradient(cx:0, cy:0, radius: 1, fx:0.5, fy:0.5, stop:0 rgb(25, 102, 255), stop:1 rgb(25, 255, 102));
                border-radius: 5px;
                border-width: 2px;
                border-style: solid;
                border-color: black;
            }
            """

history_title_bar = """
            QLabel{
                color: rgb(0, 0, 0);
                background: qradialgradient(cx:0, cy:0, radius: 1, fx:0.5, fy:0.5, stop:0 rgb(255, 25, 255), stop:1 rgb(68, 0, 204));
                border-radius: 5px;
                border-width: 2px;
                border-style: solid;
                border-color: black;
            }
            """
#color: rgb(250,250,210);
# background-color: rgba(0, 41, 59, 255);

dockwidget_layout = """
            QWidget{
                color: rgb(250,250,210);
                font: Georgia;
                font-size: 11pt;
                background-color: rgb(0, 0, 0);
                border-radius: 10px;
                border-width: 2px;
                border-color: rgb(0, 0, 0);
                border-style: solid;
            }
            """

listwidget_label_layout = """
            QLabel{
                font-family:Georgia, serif;
                border-radius: 10px;
                border-width: 2px;
                border-color: rgb(0, 125, 200);
                border-style: solid;
            }
            """

dopq_stat_label_layout = """
            QLabel{
                font-family:Georgia, serif;
                border-color: rgb(0, 125, 200);
                border-style: none;
            }
            """

subwindow_titlebar_layout = """
            QLabel{
                background-color: rgba(0, 41, 59, 255);
                font-family:Georgia, serif;
                border-color: rgb(0, 0, 0);
                border-style: none;
            }
            """

# Layout for the Main Window Header section

dockwidget_main_header_layout = """
            QWidget{
                color: rgb(250,250,210);
                background: qradialgradient(cx:0, cy:0, radius: 1, fx:0.5, fy:0.5, stop:0 rgb(75,0,130), stop:1  rgb(0,191,255));
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
