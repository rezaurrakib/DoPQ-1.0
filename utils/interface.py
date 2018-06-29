import curses
import time
import gpu

X_L = 2
Y_T = 6
HORIZONTAL_RATIO = 0.5
VERTICAL_RATIO = 0.3


def run_interface(dopq):
    curses.wrapper(main, dopq)


def main(screen, dopq):

    # init
    screen.nodelay(True)
    curses.curs_set(0)
    screen.clear()

    # define color pairs
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)

    # define a keymapping to all interface funtions
    functions = {ord('l'): read_container_logs,
                 ord('r'): reload_config,
                 ord('s'): shutdown_queue,
                 ord('h'): display_commands}

    while True:

        screen.clear()

        subwindows = setup_subwindows(screen)

        # fancy print
        print_header(screen)

        print_status(subwindows[0], dopq)
        subwindows[0].refresh()

        print_line(subwindows[1],'test', 'testings')

        # get user input char
        key = screen.getch()
        curses.flushinp()

        # execute function corresponding to pressed key
        if key in functions.keys():
            functions[key](screen, dopq)

        time.sleep(0.2)


def pick_color(status):
    """
    helper for choosing an appropriate color for a status string
    :param status: status string
    :return: curses.colo_pair or 0 if status was not matched
    """

    if status == 'not started':
        return curses.color_pair(3)
    elif status == 'created':
        return curses.color_pair(3)
    elif status == 'paused':
        return curses.color_pair(3)
    elif status == 'running':
        return curses.color_pair(4)
    elif status == 'terminated':
        return curses.color_pair(5)
    elif status == 'exited':
        return curses.color_pair(5)
    else:
        return 0


def print_line(screen, key, value, attrs=[], color=False, n_tabs=1, newline=0, x_l=X_L):

    # TODO rewrite to accept process and print out uptime as well
    screen.addstr(key + ':')
    attrs_or = 0
    attrs = [attrs] if not isinstance(attrs, list) else attrs
    for attr in attrs:
        attrs_or = attrs_or | attr
    if color:
        attrs_or = attrs_or | pick_color(value)
    screen.addstr('\t'*n_tabs + value, attrs_or)
    if newline:
        move_to_next_line(screen, newline, x_l=x_l)


def print_container():
    pass


def print_status(subwindow, dopq):

    x_l = 9
    # print status header
    header = '~~Status~~'
    height, width = subwindow.getmaxyx()
    subwindow.move(0, (width - len(header))//2)
    subwindow.addstr(header, curses.A_BOLD | curses.color_pair(2))

    # init cursor position within subwindow
    move_to_next_line(subwindow, Y_T//2, x_l)

    # get status info
    queue_status = 'running'#dopq.status
    if queue_status == 'running':
        queue_uptime, queue_starttime = '1d 5h 34m', 'Fri Jun 29 at 11:21:44 AM'#dopq.uptime
    else:
        queue_uptime, queue_starttime = '', ''

    provider_status = 'running'  # dopq.provider.status
    if provider_status == 'running':
        provider_uptime, provider_starttime = '1d 5h 34m', 'Fri Jun 29 at 11:21:44 AM' #dopq.provider.uptime
    else:
        provider_uptime, provider_starttime = '', ''
    free_gpus, assigned_gpus = gpu.get_gpus_status()

    # print status of the queue
    print_line(subwindow, 'queue status', queue_status, curses.A_BOLD, True, 2, newline=1, x_l=x_l)
    if queue_status == 'running':
        print_line(subwindow, '\t\tuptime', queue_uptime, x_l=x_l)
        print_line(subwindow, '\t   start time', queue_starttime, newline=2, x_l=x_l)
    else:
        move_to_next_line(subwindow, 1, x_l=x_l)

    # exit funciton if queue is down
    if queue_status == 'terminated':
        return None

    # print status of the provider
    print_line(subwindow, 'provider status', provider_status, curses.A_BOLD, True, 1, newline=1, x_l=x_l)
    if provider_status == 'running':
        print_line(subwindow, '\t\tuptime', provider_uptime, x_l=x_l)
        print_line(subwindow, '\t   start time', provider_starttime, newline=2, x_l=x_l)
    else:
        move_to_next_line(subwindow,1, x_l=x_l)

    # print gpu information
    print_line(subwindow, 'free gpus', str(free_gpus), newline=True, x_l=x_l)
    print_line(subwindow, 'assigned gpus', str(assigned_gpus), x_l=x_l)


def read_container_logs(screen, dopq):
    screen.clear()
    print_header(screen)
    screen.addsstr('reading container logs is not implemented yet....soon!', curses.A_BOLD)


def reload_config(screen, dopq):

    # TODO this should be implemented as a method in dop-q for better separation
    screen.clear()
    screen.addstr('reloading config', curses.A_BOLD)
    screen.refresh()
    dopq.config = dopq.parse_config(dopq.configfile)
    screen.addstr('.', curses.A_BOLD)
    screen.refresh()
    dopq.paths = dopq.config['paths']
    screen.addstr('.', curses.A_BOLD)
    screen.refresh()
    provider = dopq.provider
    screen.addstr('.', curses.A_BOLD)
    screen.refresh()
    provider.paths = dopq.config['paths']
    screen.addstr('.', curses.A_BOLD)
    screen.refresh()
    provider.fetcher_conf = dopq.config['fetcher']
    screen.addstr('.', curses.A_BOLD)
    screen.refresh()
    provider.builder_conf = dopq.config['builder']
    screen.addstr('.', curses.A_BOLD)
    screen.refresh()
    provider.docker_conf = dopq.config['docker']
    screen.addstr('.', curses.A_BOLD)
    screen.refresh()
    screen.addstr('done!', curses.A_BOLD)
    screen.refresh()
    time.sleep(2)


def shutdown_queue(screen, dopq):

    # TODO same as reload_config, no tampering with class members
    screen.clear()
    print_header(screen)
    max_dots = 10
    dopq.term_flag.value = 1
    while dopq.status == 'running' or dopq.provider.status == 'running':
        screen.deleteln()
        screen.addstr('shutting down queue', curses.A_BOLD)
        screen.refresh()
        dots = 0
        while dots <= max_dots:
            screen.addstr('.', curses.A_BOLD)
            screen.refresh()
            dots += 1
            time.sleep(0.1)
        move_to_next_line(screen, 0)    # move to beginning of the same line
    screen.addstr('done!', curses.A_BOLD)
    move_to_next_line(screen)
    time.sleep(2)


def display_commands(screen, dopq):
    screen.clear()
    print_header(screen)
    help_str = ['\tl:\tread container logs',
                '\tr:\treload config',
                '\ts:\tshutdown queue']
    addstr(screen, 'possible commands:', 2)
    addstr_multiline(screen, help_str)
    move_to_next_line(screen, 3)
    screen.addstr('press q to return to the interface', curses.A_BOLD)

    key = 0
    while key != ord('q'):
        key = screen.getch()
        curses.flushinp()
        time.sleep(0.1)
    screen.clear()


def addstr(screen, string, n_newlines=1, x_l=X_L):
    screen.addstr(string)
    move_to_next_line(screen, n_newlines, x_l)
    screen.refresh()


def addstr_multiline(screen, string_list, n_newlines=1, x_l=X_L):

    for string in string_list:
        addstr(screen, string, n_newlines, x_l)


def setup_subwindows(screen):

    # get size of the window adjusted for borders
    height, width = screen.getmaxyx()
    height, width = height-1.5*Y_T, width-2*X_L
    horizontal_gap, vertical_gap = X_L//2, Y_T//6

    # TODO finish gaps
    status_window = screen.subwin(int(VERTICAL_RATIO * height - vertical_gap//2),       # height
                                  int(HORIZONTAL_RATIO * width - horizontal_gap//2),    # width
                                  Y_T,                                                  # y
                                  X_L)                                                  # x

    container_window = screen.subwin(int((1-VERTICAL_RATIO)*height-vertical_gap//2),    # height
                                     int(HORIZONTAL_RATIO*width-horizontal_gap//2),     # width
                                     Y_T + int(VERTICAL_RATIO*height + vertical_gap),   # y
                                     X_L)                                               # x

    user_penalty_window = screen.subwin(int(VERTICAL_RATIO*height - vertical_gap//2),         # height
                                        int((1-HORIZONTAL_RATIO)*width - horizontal_gap//2),  # width
                                        Y_T,                                                  # y
                                        X_L + int(HORIZONTAL_RATIO*width + horizontal_gap))   # x

    list_window = screen.subwin(int((1-VERTICAL_RATIO)*height - vertical_gap//2),        # height
                                int((1-HORIZONTAL_RATIO)*width - horizontal_gap//2),     # width
                                Y_T + int(VERTICAL_RATIO*height + vertical_gap),         # y
                                X_L + int(HORIZONTAL_RATIO*width + horizontal_gap))      # x
    status_window.box()
    container_window.box()
    user_penalty_window.box()
    list_window.box()

    return status_window, container_window, user_penalty_window, list_window


def print_header(screen):
    border_characters = [0]*2 + ['=']*2 + ['#']*4
    screen.border(*border_characters)
    y, x = move_to_next_line(screen, n_times=2)
    banner_length = 29
    _, width = screen.getmaxyx()
    start_position = (width - X_L - banner_length)//2
    screen.move(y, start_position)
    screen.addstr('  Do', curses.color_pair(2) | curses.A_BOLD)
    screen.addstr('cker ', curses.color_pair(2))
    screen.addstr('P', curses.color_pair(2) | curses.A_BOLD)
    screen.addstr('riority ', curses.color_pair(2))
    screen.addstr('Q', curses.color_pair(2) | curses.A_BOLD)
    screen.addstr('ueue -- ', curses.color_pair(2))
    screen.addstr('DoP-Q', curses.color_pair(2) | curses.A_BOLD)
    move_to_next_line(screen)
    screen.hline('~', (width - 2*X_L), curses.color_pair(2))
    move_to_next_line(screen, Y_T-3)
    screen.refresh()


def move_to_next_line(screen, n_times=1, x_l=X_L):
    y, _ = screen.getyx()
    new_y, new_x = y + n_times*1, x_l
    screen.move(new_y, new_x)

    return new_y, new_x


if __name__ == '__main__':
    dopq = ''
    run_interface(dopq)
