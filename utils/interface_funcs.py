import curses
import time

X_L = 2
Y_T = 4

def reload_config(screen, dopq):

    # TODO this should be implemented as a method in dop-q for better separation
    screen.erase()
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
        screen.navigate(x=screen.indent)    # move to beginning of the same line
    screen.addstr('done!', curses.A_BOLD)



def display_commands(screen, *args):
    help_str = [['\tl:\tread container logs'],
                ['\tr:\treload config'],
                ['\ts:\tshutdown queue']]
    screen.addstr('possible commands:', newline=2)
    screen.addmultiline(screen, help_str)
    screen.nextline(newline=3)
    screen.addstr('press q to return to the interface', screen.BOLD)

    key = 0
    while key != ord('q'):
        key = screen.getch()
        curses.flushinp()
        time.sleep(0.1)


def read_container_logs(screen, dopq):

    screen.addsstr('reading container logs is not implemented yet....soon!', curses.A_BOLD)


FUNCTIONS = {ord('l'): read_container_logs,
                 ord('r'): reload_config,
                 ord('s'): shutdown_queue,
                 ord('h'): display_commands}