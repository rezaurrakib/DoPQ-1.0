import curses
import time


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

        # fancy print
        print_header(screen)

        print_status(screen, dopq)

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
    screen.addstr('\n')


def print_container()


def print_status(screen, dopq, user=[]):

    # print status of the queue
    queue_status = 'running'#dopq.status
    print_line(screen, 'queue status', queue_status, curses.A_BOLD, True, 2)

    # exit funciton if queue is down
    if queue_status == 'terminated':
        exit(0)

    # print status of the provider
    provider_status = 'running'  # dopq.provider.status
    print_line(screen, 'provider status', provider_status, curses.A_BOLD, True)




def read_container_logs(screen, dopq):
    screen.clear()
    print_header(screen)
    screen.addsstr('\n  reading container logs is not implemented yet....soon!', curses.A_BOLD)


def reload_config(screen, dopq):
    screen.clear()
    screen.addstr('\n  reloading config', curses.A_BOLD)
    screen.getch()
    dopq.config = dopq.parse_config(dopq.configfile)
    screen.addstr('.', curses.A_BOLD)
    screen.getch()
    dopq.paths = dopq.config['paths']
    screen.addstr('.', curses.A_BOLD)
    screen.getch()
    provider = dopq.provider
    screen.addstr('.', curses.A_BOLD)
    screen.getch()
    provider.paths = dopq.config['paths']
    screen.addstr('.', curses.A_BOLD)
    screen.getch()
    provider.fetcher_conf = dopq.config['fetcher']
    screen.addstr('.', curses.A_BOLD)
    screen.getch()
    provider.builder_conf = dopq.config['builder']
    screen.addstr('.', curses.A_BOLD)
    screen.getch()
    provider.docker_conf = dopq.config['docker']
    screen.addstr('.', curses.A_BOLD)
    screen.getch()
    screen.addstr('done!', curses.A_BOLD)
    screen.getch()
    time.sleep(2)


def shutdown_queue(screen, dopq):
    screen.clear()
    print_header(screen)
    max_dots = 10
    dopq.term_flag.value = 1
    while dopq.status == 'running' or dopq.provider.status == 'running':
        screen.deleteln()
        screen.addstr('\r  shutting down queue', curses.A_BOLD)
        screen.getch()
        dots = 0
        while dots <= max_dots:
            screen.addstr('.', curses.A_BOLD)
            screen.getch()
            dots += 1
            time.sleep(0.1)
    screen.addstr('done!\n', curses.A_BOLD)
    time.sleep(2)


def display_commands(screen, dopq):
    screen.clear()
    print_header(screen)
    help_str = '\tl:\tread container logs\n' \
               '\tr:\treload config\n' \
               '\ts:\tshutdown queue\n'
    screen.addstr('\n  possible commands:\n\n')
    screen.addstr(help_str)
    screen.addstr('\n\n\n  press q to return to the interface', curses.A_BOLD)

    key = 0
    while key != ord('q'):
        key = screen.getch()
        curses.flushinp()
        time.sleep(0.1)
    screen.clear()


def print_header(screen):
    screen.addstr('  Do', curses.color_pair(2) | curses.A_BOLD)
    screen.addstr('cker ', curses.color_pair(2))
    screen.addstr('P', curses.color_pair(2) | curses.A_BOLD)
    screen.addstr('riority ', curses.color_pair(2))
    screen.addstr('Q', curses.color_pair(2) | curses.A_BOLD)
    screen.addstr('ueue -- ', curses.color_pair(2))
    screen.addstr('DoP-Q\n', curses.color_pair(2) | curses.A_BOLD)
    screen.hline('~', 50, curses.color_pair(2))
    screen.addstr('\n'*2) # TODO fix bug where the hline disappears when adding another string


if __name__ == '__main__':
    dopq = ''
    run_interface(dopq)
