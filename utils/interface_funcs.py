import curses
import time
import os

X_L = 2
Y_T = 4


def reload_config(screen, dopq):

    # create function for updates
    def update_report_fn(msg):
        screen.erase()
        screen.addstr(msg, curses.A_BOLD)
        screen.refresh()

    # let dop-q do the reload of the configuration
    dopq.reload_config(update_report_fn)

    # wait
    time.sleep(2)


def shutdown_queue(screen, dopq):

    screen.indent = 10
    screen.navigate(x=screen.indent)

    screen.addstr('shutting down queue...', curses.A_BOLD)
    screen.refresh()

    dopq.stop()
    screen.addstr('done!', curses.A_BOLD)

    time.sleep(15)



def display_commands(screen, *args):
    screen.indent = 10
    screen.navigate(x=screen.indent)
    help_str = [['\tl:\tread container logs'],
                ['\tr:\treload config'],
                ['\ts:\tshutdown queue']]
    screen.addstr('possible commands:', newline=2)
    screen.addmultiline(help_str)
    screen.nextline(newline=3)
    screen.addstr('press q to return to the interface', screen.BOLD)

    key = 0
    while key != ord('q'):
        key = screen.getch()
        curses.flushinp()
        time.sleep(0.1)


def show_container_logs(screen, dopq):

    screen.addstr('reading container logs is not implemented yet....soon!', curses.A_BOLD)


def show_queue_log(screen, dopq):

    logfile = dopq.logfile
    with open(logfile, 'r') as logfile:
        n_lines = len(logfile.readline())

        # set up scrollable pad in window
        pass





FUNCTIONS = {ord('l'): show_queue_log,
                 ord('r'): reload_config,
                 ord('s'): shutdown_queue,
                 ord('h'): display_commands}