def history_containers_richtext_formatting(container, cnt):
    html_text = ""
    html_text += "<span style='color:#5b270b; font-size:14'><b> &nbsp; <u>Container No. " + str(cnt) + "</u></b></span>"
    #html_text += "<hr>"
    html_text += "<table>"
    html_text += "<tr>"
    html_text += "<th width='20%'></th>"
    html_text += "<th width='20%'></th>"
    html_text += "<th width='15%'></th>"
    html_text += "<th width='25%'></th>"
    html_text += "<th width='15%'></th>"
    html_text += "<th width='15%'></th>"
    html_text += "</tr>"

    html_text += "<tr>"
    html_text += "<td> <p align='left'> Container Name: </td>"
    html_text += "<td> <p align='right'> <font color='salmon'><b>" + container["name"] + "</b></font></td>"

    html_text += "<td> <p align='right'> Docker Name: </td>"
    if container['docker name'] == "":
        html_text += "<td> <p align='left'> <font color='darkcyan' size='2'><b>Not Assigned</b></font></td>"
    else:
        html_text += "<td> <p align='left'> <font color='green'><b>" + container['docker name'] + "</b></font></td>"

    html_text += "<td> <p align='right'> Executor: </td>"
    html_text += "<td> <p align='left'> <font color='blue'><b>" + container['executor'] + "</b></font></td>"
    html_text += "</tr>"

    # 2nd row
    html_text += "<tr>"
    # 2nd row, col 1
    html_text += "<td> <p align='right'> Container Status: </td>"
    html_text += "<td> <p align='left'> <font color='red'><b>" + container["status"] + "</b></font></td>"
    # 2nd row, col 2
    html_text += "<td> <p align='right'> Uptime: </td>"
    if container['run_time']== "":
        html_text += "<td> <p align='left'> <font color='darkcyan' size='2'> <b>Not Yet Started</b></font></td>"
    else:
        html_text += "<td> <p align='left'> <font color='blue'><b>" + container['run_time'] + "</b></font></td>"
    # 2nd row, col 3
    html_text += "<td> <p align='right'> Created: </td>"
    if container['created']== "":
        html_text += "<td> <p align='left'> <font color='darkcyan' size='2'><b>Not Yet Created</b></font></td>"
    else:
        html_text += "<td> <p align='left'> <font color='blue'> <b>" + container['created'] + "</b></font></td>"
    html_text += "</tr>"

    html_text += "</table>"
    html_text += "<hr>"

    return html_text


dockwidget_layout = """
            QWidget{
                background-color: rgb(0, 55, 66);
                border-width: 3px;
                border-color: rgb(75, 75, 75);
            }
            """
