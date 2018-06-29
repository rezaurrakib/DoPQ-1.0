import curses
import time
import gpu

X_L = 2
Y_T = 4
HORIZONTAL_RATIO = 0.5
VERTICAL_RATIO = 0.3


class Window(object):

    def __init__(self, screen, offset, indent, header=None):

        self.screen = screen
        self.offset = offset
        self.indent = indent
        self.header = header[0] if header is not None else ''
        self.header_attr = header[1] if header is not None else 0

        # define constants
        self.OFFSET = offset
        self.INDENT = indent

        # define some attributes
        self.BOLD = curses.A_BOLD
        self.CYAN = curses.color_pair(2)
        self.YELLOW = curses.color_pair(3)
        self.GREEN = curses.color_pair(4)
        self.RED = curses.color_pair(5)

    @property
    def size(self):
        return self.screen.getmaxyx()

    @property
    def yx(self):
        return self.screen.getyx()

    def reset(self):
        self.indent = self.INDENT
        self.offset = self.OFFSET

    def next_line(self, skip_lines=1):
        y, _ = self.yx
        new_x = self.indent
        new_y = y + skip_lines

        return self.navigate(new_y, new_x)

    def addstr(self, string, attrs=0, newline=0, indent=None, center=False):

        # center string if flag is set otherwise indent if indent is not None
        x = (self.size[1] - len(string)) // 2 if center else indent
        self.navigate(x=x)
        self.screen.addstr(string, attrs)
        self.next_line(newline)

    def addline(self, string_list, newline=0, center=False):

        # protection against generators
        if iter(string_list) is iter(string_list):
            raise TypeError('Window.addline expects an iterable, not a generator!')

        # get length of aggregated string if center flag is set
        if center:
            total_length = 0
            for string in string_list:

                #account for possibility of string attributes
                try:
                    total_length += len(string[0])
                except Exception:
                    total_length += len(string)
            center = (self.size[1] - total_length) // 2
            self.navigate(x=center)

        # print the strings in string list sequentially
        for string in string_list:
            attr = 0

            # check if string hast attributes
            try:
                attr = string[1]
                string = string[0]
            except Exception:
                pass

            self.addstr(string, attr, newline)

    def addmutliline(self, string_multiline, newline=0, center=False):

        # protection against generators
        if iter(string_multiline) is iter(string_multiline):
            raise TypeError('Window.addline expects an iterable, not a generator!')

        for line in string_multiline:
            self.addline(string_list=line, newline=newline, center=center)

    def navigate(self, y=None, x=None):
        current_y, current_x = self.yx
        new_y = y if y is not None else current_y
        new_x = x if x is not None else current_x
        self.screen.move(new_y, new_x)

        return new_y, new_x

    def refresh(self):
        self.screen.refresh()

    def clear(self):
        self.screen.clear()

    def getch(self):
        return self.screen.getch()


class SubWindow(Window):

    def __init__(self, parent, height, width, y, x, header, offset=None, indent=None, func=(lambda *args, **kwargs: None)):

        self.parent = parent
        self.offset = offset if offset is not None else parent.offset
        self.indent = indent if indent is not None else parent.indent
        super(SubWindow, self).__init__(parent.screen, self.offset, self.indent)
        self.screen = self.parent.subwin(height, width, x, y)
        self.pos_x = x
        self.pos_y = y
        self.height = height
        self.width = width
        self.header = header
        self.header_attr = parent.header_attr
        self.func = func

        self.redraw()

    def __call__(self, *args, **kwargs):

        self.func(self.screen, *args, **kwargs)

    def redraw(self):
        self.screen.clear()
        self.screen.box()
        self.addstr(string=self.header, attrs=self.header_attr, center=True)
        self.refresh()


class Interface(Window):

    def __init__(self, dopq, functions, screen, offset, indent, header, v_ratio=0.25, h_ratio=0.5, interval=0.2):

        super(Interface, self).__init__(screen, offset, indent, header)
        self.dopq = dopq
        self.provider = self.dopq.provider
        self.v_ration = v_ratio
        self.h_ration = h_ratio
        self.functions = functions
        self.interval = interval

        self.screen.nodelay(True)
        curses.curs_set(0)
        self.clear()

        self.subwindows = self.split_screen()

    def __call__(self, *args, **kwargs):

        # fancy print
        self.print_header()

        while True:

            # display information in the subwindows
            self.print_information()

            # refresh main window and all subwindows
            self.refresh()

            # get user input char
            key = self.getch()
            curses.flushinp()

            time.sleep(self.interval)

    def subwin(self, *args, **kwargs):
        return SubWindow(parent=self, *args, **kwargs)

    def split_screen(self):

        # get size of the window adjusted for borders
        win_height, win_width = self.size
        win_height, win_width = win_height - 1.5 * self.offset, win_width - 2 * self.indent
        horizontal_gap, vertical_gap = self.indent // 2, self.offset // 6

        # calculate subwindow sizes
        sub_height_upper = int(VERTICAL_RATIO * win_height - vertical_gap // 2)
        sub_height_lower = int((1 - VERTICAL_RATIO) * win_height - vertical_gap // 2)
        sub_width_left = int(HORIZONTAL_RATIO * win_width - horizontal_gap // 2)
        sub_width_right = int((1 - HORIZONTAL_RATIO) * win_width - horizontal_gap // 2)

        # create subwindows
        subwindows = {
            'status': self.subwin(height=sub_height_upper,
                                  width=sub_width_left,
                                  y=self.offset,
                                  x=self.indent,
                                  header='~~Status~~',
                                  func=print_status),
            'containers': self.subwin(height=sub_height_lower,
                                       width=sub_width_left,
                                       y=self.offset + sub_height_upper + vertical_gap,
                                       x=self.indent,
                                       header='~~Running Containers~~',
                                       func=print_containers),
            'penalties': self.subwin(height=sub_height_upper,
                                     width=sub_width_right,
                                     y=self.offset,
                                     x=self.indent + sub_width_left + horizontal_gap,
                                     header='~~User Penalties~~',
                                     func=print_penalties),
            'history': self.subwin(height=sub_height_lower // 2,
                                   width= sub_width_right,
                                   y=self.offset + sub_height_upper + vertical_gap,
                                   x=self.indent + sub_width_left + horizontal_gap,
                                   header='~~History~~',
                                   func=print_history),
            'enqueued': self.subwin(height=sub_height_lower // 2,
                                    width=sub_width_right,
                                    y=self.offset + sub_height_upper + sub_height_lower // 2 + vertical_gap,
                                    x=self.indent + sub_width_left + horizontal_gap,
                                    header='~~Enqueued Containers~~',
                                    func=print_enqueued)
                    }

        return subwindows

    def print_information(self):

        for sub in self.subwindows.values():
            sub(self.dopq)

    def redraw(self):

        for sub in self.subwindows.values():
            sub.redraw()

    def refresh(self):

        self.screen.refresh()
        for sub in self.subwindows.values():
            sub.refresh()

    def print_header(self):
        string_line = [('Do', self.bold | self.cyan),
                       'cker ',
                       ]


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

    subwindows = setup_subwindows(screen)

    # fancy print
    print_header(screen)

    # define a keymapping to all interface funtions
    functions = {ord('l'): read_container_logs,
                 ord('r'): reload_config,
                 ord('s'): shutdown_queue,
                 ord('h'): display_commands}

    while True:

        print_status(subwindows['status'], dopq)
        print_containers(subwindows['containers'], dopq)
        print_penalties(subwindows['penalties'], dopq)
        print_history(subwindows['history'], dopq)
        print_enqueued(subwindows['enqueued'], dopq)

        # refresh all subwindows
        screen.refresh()
        for subwindow in subwindows.values():
            subwindow.refresh()

        # get user input char
        key = screen.getch()
        curses.flushinp()

        # execute function corresponding to pressed key
        if key in functions.keys():
            subwindows = execute_function(functions[key], screen, dopq)

        time.sleep(0.2)


def execute_function(func, screen, dopq):
    screen.clear()
    print_header(screen)
    func(screen=screen, dopq=dopq)
    screen.clear()
    print_header(screen)
    return setup_subwindows(screen)


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


def print_key_value_pair(screen, key, value, attrs=[], color=False, n_tabs=1, newline=0, x_l=X_L):

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


def print_status(subwindow, dopq):

    x_l = 9
    # print status header
    print_subwindow_header(subwindow, '~~Status~~', y_t=Y_T//2)

    # init cursor position within subwindow
    move_to_next_line(subwindow, 0, x_l)

    # get status info # TODO remove testing dummies!!!
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
    print_key_value_pair(subwindow, 'queue status', queue_status, curses.A_BOLD, True, 2, newline=1, x_l=x_l)
    if queue_status == 'running':
        print_key_value_pair(subwindow, '\t\tuptime', queue_uptime, x_l=x_l)
        print_key_value_pair(subwindow, '\t   start time', queue_starttime, newline=2, x_l=x_l)
    else:
        move_to_next_line(subwindow, 1, x_l=x_l)

    # exit funciton if queue is down
    if queue_status == 'terminated':
        return None

    # print status of the provider
    print_key_value_pair(subwindow, 'provider status', provider_status, curses.A_BOLD, True, 1, newline=1, x_l=x_l)
    if provider_status == 'running':
        print_key_value_pair(subwindow, '\t\tuptime', provider_uptime, x_l=x_l)
        print_key_value_pair(subwindow, '\t   start time', provider_starttime, newline=2, x_l=x_l)
    else:
        move_to_next_line(subwindow,1, x_l=x_l)

    # print gpu information
    print_key_value_pair(subwindow, 'free gpus', str(free_gpus), newline=True, x_l=x_l)
    print_key_value_pair(subwindow, 'assigned gpus', str(assigned_gpus), x_l=x_l)


def print_containers(subwindow, dopq):

    x_l = 1
    y_t = 2

    print_subwindow_header(subwindow, '~~Running Containers~~', x_l)

    class DummyContainer():
        def container_stats(self, runtime_stats=True):
            import psutil

            # build base info
            base_info = {'name': 'dummy', 'executor': 'dummy the dummy', 'run_time': 'forever'}

            # also show runtime info?
            if runtime_stats:

                # cpu_stats = stats_dict['cpu_stats']
                cpu_usage_percentage = psutil.cpu_percent()

                # calc memory usage
                mem_stats = {'usage': 20, 'limit': 100}
                mem_usage = mem_stats['usage'] * 100.0 / mem_stats['limit']

                # add base runtime info
                base_info['cpu_mem'] = {'cpu': cpu_usage_percentage, 'memory': mem_usage}

                # add gpu info, if required
                gpu_info = gpu.get_gpu_infos(0)
                base_info['gpu'] = [
                    {'id': gpu_dt['id'], 'usage': gpu_dt['memoryUsed'] * 100.0 / gpu_dt['memoryTotal']}
                    for gpu_dt in gpu_info.values()]

            return base_info

    running_containers = [DummyContainer()]*3#dopq.running_containers
    n_running_containers = len(running_containers)

    # subdivide window
    height, width = subwindow.getmaxyx()
    step = int(height // n_running_containers)

    def print_single_container(y, container, subwindow=subwindow, x_l=x_l):
        _, x = subwindow.getyx()
        subwindow.move(y, x_l)
        info = container.container_stats()
        addstr(subwindow, info['name'], attrs=curses.A_BOLD)
        subwindow.hline('-', width-2*x_l)
        move_to_next_line(subwindow, x_l=x_l)
        #addstr(subwindow, )

    offset, _ = subwindow.getyx()
    for i, container in enumerate(running_containers):
        print_single_container(i*step+offset, container)


def print_penalties(subwindow, dopq):

    x_l = 9

    print_subwindow_header(subwindow, '~~User Penalties~~')


def print_history(subwindow, dopq):

    x_l = 9

    print_subwindow_header(subwindow, '~~History~~')


def print_enqueued(subwindow, dopq):

    x_l = 9

    print_subwindow_header(subwindow, '~~Enqueued Containers~~')


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


def addstr(screen, string, n_newlines=1, x_l=X_L, attrs=0):
    screen.addstr(string, attrs)
    move_to_next_line(screen, n_newlines, x_l)
    screen.refresh()


def addstr_multiline(screen, string_list, n_newlines=1, x_l=X_L):

    for string in string_list:
        addstr(screen, string, n_newlines, x_l)


def setup_subwindows(screen):

    # get size of the window adjusted for borders
    win_height, win_width = screen.getmaxyx()
    win_height, win_width = win_height-1.5*Y_T, win_width-2*X_L
    horizontal_gap, vertical_gap = X_L//2, Y_T//6

    # calculate subwindow sizes
    sub_height_upper = int(VERTICAL_RATIO * win_height - vertical_gap // 2)
    sub_height_lower = int((1 - VERTICAL_RATIO) * win_height - vertical_gap // 2)
    sub_width_left = int(HORIZONTAL_RATIO * win_width - horizontal_gap // 2)
    sub_width_right = int((1 - HORIZONTAL_RATIO) * win_width - horizontal_gap // 2)

    # create subwindows
    subwindows = {}
    subwindows['status'] = screen.subwin(sub_height_upper, sub_width_left, Y_T, X_L)
    subwindows['containers'] = screen.subwin(sub_height_lower, sub_width_left, Y_T + sub_height_upper + vertical_gap, X_L)
    subwindows['penalties'] = screen.subwin(sub_height_upper, sub_width_right, Y_T, X_L + sub_width_left + horizontal_gap)
    subwindows['history'] = screen.subwin(sub_height_lower // 2, sub_width_right,
                                   Y_T + sub_height_upper + vertical_gap, X_L + sub_width_left + horizontal_gap)
    subwindows['enqueued'] = screen.subwin(sub_height_lower // 2, sub_width_right,
                                Y_T + sub_height_upper + sub_height_lower//2 + vertical_gap, X_L + sub_width_left + horizontal_gap)

    # draw boxes in subwindows
    for subwindow in subwindows.values():
        subwindow.box()

    return subwindows


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


def print_subwindow_header(subwindow, header, x_l=X_L, y_t=Y_T):

    height, width = subwindow.getmaxyx()
    subwindow.move(0, (width - len(header)) // 2)
    subwindow.addstr(header, curses.A_BOLD | curses.color_pair(2))
    move_to_next_line(subwindow, n_times=y_t, x_l=x_l)


def move_to_next_line(screen, n_times=1, x_l=X_L):
    y, _ = screen.getyx()
    new_y, new_x = y + n_times*1, x_l
    screen.move(new_y, new_x)

    return new_y, new_x


if __name__ == '__main__':
    run_interface('')