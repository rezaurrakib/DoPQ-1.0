import curses
import time
import gpu

X_L = 2
Y_T = 5
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


def print_line(screen, key, value, attrs=[], color=False, n_tabs=1):

    screen.addstr('  ' + key + ':')
    attrs_or = 0
    attrs = [attrs] if not isinstance(attrs, list) else attrs
    for attr in attrs:
        attrs_or = attrs_or | attr
    if color:
        attrs_or = attrs_or | pick_color(value)
    screen.addstr('\t'*n_tabs + value, attrs_or)
    move_to_next_line(screen)


def print_container():
    pass


def print_status(subwindow, dopq):

    # init cursor position within subwindow
    subwindow.move(2, 2)

    # print status of the queue
    queue_status = 'running'#dopq.status
    print_line(subwindow, 'queue status', queue_status, curses.A_BOLD, True)

    # exit funciton if queue is down
    if queue_status == 'terminated':
        exit(0)

    # print status of the provider
    provider_status = 'running'  # dopq.provider.status
    print_line(subwindow, 'provider status', provider_status, curses.A_BOLD, True)

    # print gpu information
    free_gpus, assigned_gpus = gpu.get_gpus_status()
    #print_line(subwindow, 'free gpus', str(free_gpus), n_tabs=2)
    #print_line(subwindow, 'assigned gpus', str(assigned_gpus))


def read_container_logs(screen, dopq):
    screen.clear()
    print_header(screen)
    screen.addsstr('reading container logs is not implemented yet....soon!', curses.A_BOLD)


def reload_config(screen, dopq):
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
    height, width = height-Y_T, width-X_L

    status_window = screen.subwin(int(VERTICAL_RATIO*height), int(HORIZONTAL_RATIO*width), Y_T, X_L)
    container_window = screen.subwin(int((1-VERTICAL_RATIO)*height), int(HORIZONTAL_RATIO*width),
                                     Y_T + int(VERTICAL_RATIO*height), X_L)
    user_penalty_window = screen.subwin(int(VERTICAL_RATIO*height), int((1-HORIZONTAL_RATIO)*width),
                                     Y_T, X_L + int(HORIZONTAL_RATIO*width))
    history_window = screen.subwin(int((1-VERTICAL_RATIO)*height), int((1-HORIZONTAL_RATIO)*width),
                                     Y_T + int(VERTICAL_RATIO*height), X_L + int(HORIZONTAL_RATIO*width))
    status_window.box()
    container_window.box()
    user_penalty_window.box()
    history_window.box()

    return status_window, container_window, user_penalty_window, history_window


def print_header(screen):
    screen.box()
    move_to_next_line(screen)
    screen.addstr('  Do', curses.color_pair(2) | curses.A_BOLD)
    screen.addstr('cker ', curses.color_pair(2))
    screen.addstr('P', curses.color_pair(2) | curses.A_BOLD)
    screen.addstr('riority ', curses.color_pair(2))
    screen.addstr('Q', curses.color_pair(2) | curses.A_BOLD)
    screen.addstr('ueue -- ', curses.color_pair(2))
    screen.addstr('DoP-Q', curses.color_pair(2) | curses.A_BOLD)
    move_to_next_line(screen)
    screen.hline('~', 50, curses.color_pair(2))
    move_to_next_line(screen, Y_T-2)
    screen.refresh()


def move_to_next_line(screen, n_times=1, x_l=X_L):
    y, _ = screen.getyx()
    new_y, new_x = y + n_times*1, x_l
    screen.move(new_y, new_x)


if __name__ == '__main__':
    dopq = ''
    run_interface(dopq)
