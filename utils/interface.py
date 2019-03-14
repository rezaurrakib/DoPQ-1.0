import copy
import types
import curses
import time
import traceback


from . import log
from . import gpu
from . import interface_funcs
from curses import panel
from math import floor, ceil
from collections import OrderedDict


X_L = 2
Y_T = 4
HORIZONTAL_RATIO = 0.5
VERTICAL_RATIO = 0.3
KEY_TAB = 9
LOG = log.get_module_log(__name__)

class Window(object):

    def __init__(self, screen, offset=0, indent=0, header=None):
        """
        Window wraps a curses window object to simplify and streamline navigating, formatting and writing in it
        :param screen: curses window object
        :param offset: number of blank lines to keep at the top of the window
        :param indent: number of whitespaces to keep at the left side of every line
        :param header: title that will be printed at the top of the window
        """

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
        self.BLUE = curses.color_pair(6)

    @property
    def size(self):
        """
        wrapper for getting window height and width
        :return: tuple(height, width)
        """
        return self.screen.getmaxyx()

    @property
    def yx(self):
        """
        wrapper for getting current cursor position
        :return: tuple(y, x)
        """
        return self.screen.getyx()

    def reset(self):
        """
        reset offset and indent to their initial values
        :return: None
        """
        self.indent = self.INDENT
        self.offset = self.OFFSET

    def nextline(self, newline=1):
        """
        move cursor down one or more lines and start at indent position
        :param newline: number of lines to move down
        :return: new coordinates (y, x)
        """
        y, _ = self.yx
        new_x = self.indent
        new_y = y + newline

        return self.navigate(new_y, new_x)

    def addstr(self, string, attrs=0, newline=0, indent=None, center=False, y=None, x=None):
        """
        write a string to the window
        :param string: string to write
        :param attrs: formatting of the string
        :param newline: number of lines to move down after writing
        :param indent: indent to use for this string
        :param center: if True string will be centered in the window
        :return: cursor coordinates after writing the string but before going to newline
        """

        # navigate to coordinates
        if any([coord is not None for coord in (y, x)]):
            self.navigate(y=y, x=x)

        # center string if flag is set otherwise indent if indent is not None
        x = (self.size[1] - len(string)) // 2 if center else indent
        self.navigate(x=x)
        y, x = self.yx
        coords = {'beginning': {'y': y, 'x': x}}
        self.screen.addstr(string, attrs)
        y, x = self.yx
        coords['end'] = {'y': y, 'x': x}
        if newline:
            self.nextline(newline=newline)

        return coords

    def addline(self, string_list, newline=0, center=False, y=None, x=None):
        """
        allows writing a list of strings, each with their own formatting, onto a line in the window
        :param string_list: list of strings and / or (string, formatting) tuples
        :param newline: number of lines to move down after writing
        :param center: if True, line will be centered on the window
        :return: list of cursor coordinates after writing the strings but before going to newline
        """
        # initialize coordinates for return
        coords = []

        # navigate to coordinates
        if any([coord is not None for coord in (y, x)]):
            self.navigate(y=y, x=x)

        # protection against generators
        if iter(string_list) is iter(string_list):
            raise TypeError('Window.addline expects an iterable, not a generator!')

        # get length of aggregated string if center flag is set
        if center:
            total_length = 0
            for string in string_list:

                # account for possibility of string attributes
                if isinstance(string, tuple):
                    total_length += len(string[0])
                else:
                    total_length += len(string)
            center = (self.size[1] - total_length) // 2
            self.navigate(x=center)

        # print the strings in string list sequentially
        for string in string_list:

            # check if string has attributes
            if isinstance(string, tuple):
                attr = string[1]
                string = string[0]
            else:
                attr = 0

            coords.append(self.addstr(string, attr))

        if newline:
            self.nextline(newline=newline)

        return coords

    def addmultiline(self, string_multiline, newline=1, center=False, y=None, x=None):
        """
        allow writing of several lines onto the screen
        :param string_multiline: matrix of strings and / or (string, formatting) tuples
        :param newline: number of lines to move down after writing
        :param center: if True, each line will be centered on the window
        :return: None
        """

        # initialize coordinate matrix for return
        coords = []

        # navigate to coordinates
        if any([coord is not None for coord in (y, x)]):
            self.navigate(y=y, x=x)

        # protection against generators
        if iter(string_multiline) is iter(string_multiline):
            raise TypeError('Window.addline expects an iterable, not a generator!')

        for line in string_multiline:
            coords.append(self.addline(string_list=line, newline=newline, center=center))

        return coords

    def navigate(self, y=None, x=None):
        """
        move cursors to specified position, the unspecified coordinate will remain unchanged
        :param y: y coordinate to navigate to, will remain unchanged if None is given
        :param x: x coordinate to navigate to, will remain unchanged if None is given
        :return: tuple(new y, new x)
        """
        current_y, current_x = self.yx
        new_y = y if y is not None else current_y
        new_x = x if x is not None else current_x
        self.screen.move(new_y, new_x)

        return new_y, new_x

    def refresh(self):
        """
        wrapper for refresh method of the curses window object
        :return: None
        """
        self.screen.refresh()

    def erase(self):
        """
        wrapper for erase method of the curses window object
        :return: None
        """
        self.screen.erase()

    def getch(self):
        """
        wrapper for getch (get character) method of the curses window object
        :return: None
        """
        return self.screen.getch()

    def deleteln(self):
        """
        wrapper for deleteln (delete line) method of the curses window object
        :return: None
        """
        self.screen.deleteln()

    def print_header(self):
        """
        print the window header bold and centered at the top of the window. stored header formatting is also applied
        :return: None
        """

        self.addstr(self.header, self.BOLD | self.header_attr, center=True, y=0, x=0)
        self.navigate(self.offset, self.indent)


class SubWindow(Window):

    def __init__(self, parent, height, width, y, x, header, offset=None, indent=None, func=None, **kwargs):
        """
        this class represents a subwindow embedded in the parent window and is meant to be used for displaying task specific information
        :param parent: instance of Window in which this object will be embedded
        :param height: height of the subwindow
        :param width: width of the subwindow
        :param y: y coordinate of the top left corner
        :param x: x coordinate of the top left corner
        :param header: header string of subwindow. Subwindow uses the header formatting of the parent
        :param offset: number of blank lines to keep at the top of the window
        :param indent: number of whitespaces to keep at the left side of every line
        :param func: DisplayFunction that is executed when this object is called
        """

        self.parent = parent
        offset = offset if offset is not None else parent.offset
        indent = indent if indent is not None else parent.indent
        screen = self.parent.screen.subwin(height, width, y, x)
        super(SubWindow, self).__init__(screen, offset, indent)
        self.pos_x = x
        self.pos_y = y
        self.height = height
        self.width = width
        self.header = header
        self.header_attr = parent.header_attr
        if isinstance(func, type):
            self.func = func(self, self.parent.dopq, **kwargs)
            self.args = []
        elif isinstance(func, types.FunctionType):
            self.func = func
            self.args = [self.screen, self.parent.dopq, ]
        else:
            time.sleep(15)
            self.func = DisplayFunction(self, self.parent.dopq)
            self.args = []

        self.redraw()

    def __call__(self, **kwargs):
        """
        execute self.func when this object is called
        :param args: positional arguments passed to self.func
        :param kwargs: keyword arguments passed to self.func
        :return: returnvalue of self.sunc
        """

        return self.func(*self.args, **kwargs)

    def redraw(self):
        """
        redraws the window borders and header
        :return: None
        """
        self.erase()
        self.screen.box()
        self.print_header()


class SubWindowAndPad(SubWindow):

    def __init__(self, parent, height, width, y, x, header, offset=None, indent=None, func=None, pad_height_factor=3, **kwargs):

        # initialize regular Subwindow
        self.pad_initialized = False
        self.pad_indent = 1 if indent is None else indent
        self.pad_offset = 1 if offset is None else offset
        super(SubWindowAndPad, self).__init__(parent, height, width, y, x, header, offset=0, indent=0, func=func, **kwargs)

        # add a scrollable pad with same width and pad_height_factor * height
        self.pad_height = self.height * pad_height_factor
        pad = curses.newpad(self.pad_height, self.width)

        # define some variables with regard to refreshing the pad
        self.pad_line = 0
        self.top_left = [self.pos_y + 1 + self.pad_offset, self.pos_x + 1 + self.pad_indent]
        self.bottom_right = [self.pos_y + self.height - 2, self.pos_x + self.width - 1 - self.pad_indent]
        self.pad_display_coordinates = self.top_left + self.bottom_right
        self.scroll_limit = self.pad_height - self.height + 1

        # substitute self.screen with pad, move self.screen to self.window
        self.window = self.screen
        self.screen = pad
        if self.args:
            self.args[0] = pad
        self.pad_initialized = True

        # move subwindow underneath pad (panel has to be stored, otherwise it is garbage collected)
        self.panel = panel.new_panel(self.window)
        self.panel.bottom()

        # adjust indent and offset due to pad
        self.indent -= 1 if self.indent > 0 else 0
        self.offset -= 1 if self.offset > 0 else 0

    def refresh(self):
        if self.pad_initialized:
            self.window.refresh()
            self.screen.refresh(self.pad_line, 0, *self.pad_display_coordinates)
        else:
            self.screen.refresh()

    def redraw(self):
        self.erase()
        if self.pad_initialized:
            self.window.box()
        else:
            self.screen.box()
        self.print_header()
        if isinstance(self.func, DisplayFunction) or issubclass(self.func, DisplayFunction):
            self.func.first_call = True

    def print_header(self):
        if self.pad_initialized:
            pad = self.screen
            self.screen = self.window
        super(SubWindowAndPad, self).print_header()
        if self.pad_initialized:
            self.screen = pad

    def scroll_up(self):
        self.pad_line -= 1 if self.pad_line > 0 else 0

    def scroll_down(self):
        self.pad_line += 1 if self.pad_line < self.scroll_limit else 0

    def set_focus(self):
        border_chars = ['|'] * 2 + ['-'] * 2
        self.window.attron(self.BOLD | self.CYAN)
        self.window.border(*border_chars)
        self.window.attroff(self.BOLD | self.CYAN)
        self.print_header()


class Interface(Window):

    def __init__(self, dopq, screen, offset, indent, v_ratio=0.25, h_ratio=0.5, interval=1):
        """
        interface to the docker priority queue object
        :param dopq_ref: instance of DopQ
        :param screen: curses window to use as display
        :param offset: number of blank lines to keep at the top of the window
        :param indent: number of whitespaces to keep at the left side of every line
        :param v_ratio: ratio of top subwindow height to total window height
        :param h_ratio: ratio of left subwindow width to total window width
        :param interval: update interval in seconds
        """

        super(Interface, self).__init__(screen, offset, indent)
        self.header_attr = self.CYAN
        self.dopq = dopq
        self.v_ratio = v_ratio
        self.h_ratio = h_ratio
        self.functions = interface_funcs.FUNCTIONS
        self.interval = interval

        self.screen.nodelay(True)
        curses.curs_set(0)
        self.erase()

        self.subwindows = self.split_screen()

        self.scrollable = [self.subwindows['userstats'], self.subwindows['enqueued'], self.subwindows['history']]
        self.focus = -1

        # draw all borders and headers
        self.redraw()

    def __call__(self, *args, **kwargs):
        """
        infinite loop that displays information and watches for input
        :param args: not used
        :param kwargs: not used
        :return: None
        """

        while True:

            # display information in the subwindows
            self.print_information()

            # loop that catches user interactions with ~0.1 cycle time
            for _ in range(int(self.interval/0.1)):
                # get user input char
                key = self.getch()
                curses.flushinp()

                # run the specified function
                if key in list(self.functions.keys()):
                    self.execute_function(self.functions[key])

                if key == KEY_TAB:

                    # unset focus for current subwindow
                    if self.focus != -1:
                        self.scrollable[self.focus].window.box()
                        self.scrollable[self.focus].print_header()

                    # cycle subwindow focus
                    self.focus += 1 if self.focus < len(self.scrollable) - 1 else -3
                    if self.focus != -1:
                        self.scrollable[self.focus].set_focus()

                if key == ord('+') and self.focus > -1:
                    subwindow = self.scrollable[self.focus]
                    subwindow.scroll_up()

                if key == ord('#') and self.focus > -1:
                    subwindow = self.scrollable[self.focus]
                    subwindow.scroll_down()

                self.refresh()

                time.sleep(0.1)

    def subwin(self, pad=False, *args, **kwargs):
        """
        wrapper for Subwindow.__init__() with self as parent
        :param pad: if True return a SubWindowAndPad instead of SubWindow
        :param args: positional arguments passed to Subwindow()
        :param kwargs: keyword arguments passed to Subwindow()
        :return: instance of Subwindow
        """
        if pad:
            return SubWindowAndPad(parent=self, *args, **kwargs)
        else:
            return SubWindow(parent=self, *args, **kwargs)

    def split_screen(self):
        """
        setup the 5 subwindows that are needed for the interface
        :return: dict of Subwindow instances
        """

        # get size of the window adjusted for borders
        win_height, win_width = self.size
        win_height, win_width = win_height - 1.5 * self.offset, win_width - 2 * self.indent
        horizontal_gap, vertical_gap = self.indent // 2, self.offset // 6

        # calculate subwindow sizes
        sub_height_upper = int(self.v_ratio * win_height - vertical_gap // 2)
        sub_height_lower = int((1 - self.v_ratio) * win_height - vertical_gap // 2)
        sub_width_left = int(self.h_ratio * win_width - horizontal_gap // 2)
        sub_width_right = int((1 - self.h_ratio) * win_width - horizontal_gap // 2)

        # create subwindows
        subwindows = {
            'status': self.subwin(height=sub_height_upper,
                                  width=sub_width_left,
                                  y=self.offset,
                                  x=self.indent,
                                  header='~~Status~~',
                                  func=Status,
                                  indent=self.indent*4),
            'containers': self.subwin(height=sub_height_lower,
                                      width=sub_width_left,
                                      y=self.offset + sub_height_upper + vertical_gap,
                                      x=self.indent,
                                      header='~~Running Containers~~',
                                      func=Containers,
                                      offset=2),
            'userstats': self.subwin(pad=True,
                                     height=sub_height_upper,
                                     width=sub_width_right,
                                     y=self.offset,
                                     x=self.indent + sub_width_left + horizontal_gap,
                                     offset=1,
                                     indent=4,
                                     header='~~User Stats~~',
                                     func=UserStats),
            'enqueued': self.subwin(pad=True,
                                    height=sub_height_lower // 2,
                                    width=sub_width_right,
                                    y=self.offset + sub_height_upper + vertical_gap,
                                    x=self.indent + sub_width_left + horizontal_gap,
                                    offset=1,
                                    indent=4,
                                    pad_height_factor=10,
                                    header='~~Enqueued Containers~~',
                                    func=ContainerList,
                                    mode='enqueued'),
            'history': self.subwin(pad=True,
                                   height=(sub_height_lower // 2) + 1, #+ vertical_gap // 2,
                                   width=sub_width_right,
                                   y=self.offset + sub_height_upper + sub_height_lower // 2 + vertical_gap,
                                   x=self.indent + sub_width_left + horizontal_gap,
                                   offset=1,
                                   indent=4,
                                   pad_height_factor=10,
                                   header='~~History~~',
                                   func=ContainerList,
                                   mode='history')
                    }

        return subwindows

    def print_information(self):
        """
        wrapper for calling all subwindow functions
        :return:
        """

        for sub in list(self.subwindows.values()):
            sub()

    def redraw(self):
        """
        print window header and redraw all subwindows
        :return: None
        """

        self.print_header(self) # print header is a static method

        for sub in list(self.subwindows.values()):
            sub.redraw()

    def refresh(self):
        """
        call refresh on self and all subwindows
        :return: None
        """

        self.screen.refresh()
        for sub in list(self.subwindows.values()):
            sub.refresh()

    @staticmethod # static because i wanted to use this method with instances of Window as well
    def print_header(self):
        """
        customised print_header to write interface header followed by a vertical line
        static, so that it can be called for other windows as well
        :param self: Window instance
        :return: None
        """

        # draw border around the window
        border_characters = [0] * 2 + ['='] * 2 + ['#'] * 4
        self.screen.border(*border_characters)

        # print title
        string_line = [('Do', self.BOLD | self.header_attr),
                       ('cker ', self.header_attr),
                       ('P', self.BOLD | self.header_attr),
                       ('riority ', self.header_attr),
                       ('Q', self.BOLD | self.header_attr),
                       ('ueue -- ', self.header_attr),
                       ('DopQ', self.BOLD | self.header_attr)]
        self.nextline()
        self.addline(string_list=string_line, newline=1, center=True, y=1, x=0)

        self.screen.hline('~', self.size[1]-2*self.indent, self.BOLD | self.header_attr)
        self.nextline(newline=3)

        return self.yx

    def execute_function(self, func):
        """
        prepares a window in which a control function is executed. window is deleted afterwards
        :param func: control function to call
        :return: None
        """

        # make a new window for executing the function in
        height, width = self.size
        new_window = Window(curses.newwin(height, width, 0, 0), self.offset, self.indent, header=('', self.CYAN))

        # print dopq header in the new window
        new_window.navigate(*self.print_header(new_window))

        # execute function
        func(new_window, self.dopq)

        # delete the temporary window
        del new_window

        self.redraw()
        self.print_information()


class DisplayFunction(object):

    def __init__(self, subwindow, dopq):
        """
        class for stateful display functions
        :param subwindow: instance of Subwindow, passed automatically in Interface.split_screen()
        :param dopq: Instance of DopQ
        """
        self.displayed_information = None
        self.template = None
        self.first_call = True
        self.rewrite_all = False
        self.screen = subwindow
        self.dopq = dopq
        self.template = ''
        self.fields = {}

    def __call__(self, *args, **kwargs):
        """
        write template to screen if its the first time calling this class, then update the information in the template
        :param args: not used
        :param kwargs: not used
        :return: None
        """

        if self.first_call:
            self.reset_displayed_information()
            self.write_template()
            self.update()
        else:
            self.update()

    def update(self):
        """
        update displayed information
        :return: None
        """
        raise NotImplementedError('abstract method')

    def write_template(self):
        """
        write template to display on first function call
        :return: None
        """
        raise NotImplementedError('abstract method')

    def update_field(self, string, field, attrs=0):
        """
        fill the field with whitespaces before writing the string
        :param string: string to write to the field
        :param field: field as given in self.fields.values()
        :param attrs: formatting for the string. defaults to 0 (no formatting)
        :return: None
        """
        (y, x), length = field
        self.screen.navigate(y, x)
        self.screen.addstr(' ' * length)
        self.screen.navigate(y, x)
        self.screen.addstr(str(string), attrs)

    def calculate_field_properties(self, fields):
        """
        calculates the length of each field and appends this length to the coordinates already stored in the fields dict
        :return: None
        """
        width = self.screen.size[1] - self.screen.indent

        # cycle items in the ordered dict to calculate lengths
        item_list = list(fields.items())
        for index, (field, coordinates) in enumerate(item_list[:-1]):

            # get the next field name and its coordinates
            next_field, next_coordinates = item_list[index + 1]

            start = coordinates['end']['x']

            # find the end by checking where the next field begins
            if next_coordinates['beginning']['y'] != coordinates['beginning']['y']:
                # next field is in a different line, use window width as endpoint
                end = width - self.screen.indent
            else:
                # next field is in the same line
                end = next_coordinates['beginning']['x']

            length = end - start

            fields[field] = ((coordinates['end']['y'], coordinates['end']['x']), length)

        else:
            # account for the last field
            field, coordinates = item_list[-1]
            fields[field] = ((coordinates['end']['y'], coordinates['end']['x']), width - coordinates['end']['x'])

        return fields

    def reset_displayed_information(self):

        for index, info in enumerate(self.displayed_information):
            if isinstance(info, str):
                self.displayed_information[info] = ''
            else:
                for field in list(info.keys()):
                    self.displayed_information[index][field] = ''


class Status(DisplayFunction):

    def __init__(self, subwindow, dopq):
        """
        initializes template and displayed information
        :param subwindow: instance of Subwindow
        :param dopq: instance of DopQ
        """

        super(Status, self).__init__(subwindow, dopq)

        # init fields
        self.fields = {'queue status': '',
                       'queue uptime': '',
                       'queue starttime': '',
                       'provider status': '',
                       'provider uptime': '',
                       'provider starttime': ''}

        # init information dict
        self.displayed_information = copy.deepcopy(self.fields)

        # init template
        width = self.screen.size[1]
        width_unit = width // 8
        self.template = [[pad_with_spaces('queue:', width_unit)],
                           [pad_with_spaces('uptime:  ', 2*width_unit, 'prepend'),
                            pad_with_spaces('starttime:  ', 2*width_unit, 'prepend')],
                           [''],
                           [pad_with_spaces('provider:', width_unit)],
                           [pad_with_spaces('uptime:  ', 2*width_unit, 'prepend'),
                            pad_with_spaces('starttime:  ', 2*width_unit, 'prepend')],
                           ['']]

    def update(self):
        """
        gathers new information and overwrites only the portions int the template that have changed
        :return: None
        """
        # gather new information
        information = {}
        information['queue status'] = self.dopq.status
        if information['queue status'] == 'running':
            information['queue uptime'], information['queue starttime'] = self.dopq.uptime
            information['provider status'] = self.dopq.provider.status
            if information['provider status'] == 'running':
                information['provider uptime'], information['provider starttime'] = self.dopq.provider.uptime
            else:
                information['provider uptime'], information['provider starttime'] = '', ''
        else:
            information['queue uptime'], information['queue starttime'] = '', ''
            information['provider status'] = ''
            information['provider uptime'], information['provider starttime'] = '', ''

        # update displayed information
        for field, value in list(information.items()):

            # skip if information has not changed
            if value == self.displayed_information[field]:
                continue

            # overwrite information that has changed
            attrs = pick_color(value) | self.screen.BOLD if 'status' in field else 0
            self.update_field(value, self.fields[field], attrs)

        self.displayed_information = information

    def write_template(self):
        """
        writes template to display on first call
        :return:
        """

        # get the beginning and end coordinates for every string in the template
        coordinates = self.screen.addmultiline(self.template)
        fields = {'queue status': coordinates[0][0],
                  'queue uptime': coordinates[1][0],
                  'queue starttime': coordinates[1][1],
                  'provider status': coordinates[3][0],
                  'provider uptime': coordinates[4][0],
                  'provider starttime': coordinates[4][1]
                  }

        # sort the dict according to y coordinates first and x coordinates second
        def sort_fn(item):
            return item[1]['beginning']['y'], item[1]['beginning']['x']

        fields = OrderedDict(sorted(list(fields.items()), key=sort_fn))
        self.fields = self.calculate_field_properties(fields)
        self.first_call = False


class Containers(DisplayFunction):

    def __init__(self, subwindow, dopq):
        """
        initializes fields, displayed_information and form template
        :param subwindow: instance of SubWindowAndPad
        :param dopq: instance of DopQ
        """

        super(Containers, self).__init__(subwindow, dopq)

        width = self.screen.size[1]
        width_unit = width // 8

        # init fields dict
        self.fields = [{'name': '',
                        'status': '',
                        'docker name': '',
                        'executor': '',
                        'run_time': '',
                        'created': '',
                        'cpu': '',
                        'memory': '',
                        'id': '',
                        'usage': ''}]

        # init information dict
        self.displayed_information = []

        # init template
        self.template = {'base': [['name:  ', # name
                                   pad_with_spaces('status:  ', 5 * width_unit, 'prepend')],  # end of first line
                                  ['-' * (width - 2 * self.screen.indent)],  # hline
                                  [pad_with_spaces('docker name:  ', 2 * width_unit, 'prepend'),
                                   pad_with_spaces('executor:  ', 3 * width_unit, 'prepend')], # end of second line
                                  [pad_with_spaces('uptime:  ', 2 * width_unit, 'prepend'),
                                   pad_with_spaces('created:  ', 3 * width_unit, 'prepend')],  # end of third line
                                  [pad_with_spaces('cpu usage:  ', 2 * width_unit, 'prepend'),
                                   pad_with_spaces('memory usage:  ', 3 * width_unit, 'prepend')]],  # end of fourth line

                         'gpu': [pad_with_spaces('gpu minor:  ', 2 * width_unit, 'prepend'),
                                 pad_with_spaces('gpu usage:  ', 3 * width_unit, 'prepend')]}

    def update(self):
        """
        gets new information from the queue and updates the fields that have changed
        :return: None
        """

        # gather new information
        information = []
        containers = copy.copy(self.dopq.running_containers)
        for container in self.dopq.running_containers:
            information.append(container.container_stats())

            # reformat gpu info
            gpu_info = information[-1].pop('gpu', False)
            if gpu_info:
                minors, usages = [], []
                for info in gpu_info:
                    minors.append(info['id'])
                    usages.append(info['usage'])
                information[-1]['id'] = minors
                information[-1]['usage'] = ''.join([str(usage) + '% ' for usage in usages])

        # check if the containers are the same
        rewrite_all = False
        if len(information) != len(self.displayed_information):
            self.write_template(containers)
            rewrite_all = True
        else:
            for index, container in enumerate(self.dopq.running_containers):
                if container.name != self.displayed_information[index]['name']:
                    # rewrite template because gpu settings of the changed container may be different from the previously displayed
                    self.write_template()
                    rewrite_all = True
                    break

        # update displayed information
        for index, container_information in enumerate(information):
            for field, value in list(container_information.items()):

                if rewrite_all or value != self.displayed_information[index][field]:
                    attrs = 0
                    if 'status' in field:
                        attrs = pick_color(value) | self.screen.BOLD
                    elif 'name' in field:
                        attrs = self.screen.BOLD
                    try:
                        self.update_field(value, self.fields[index][field], attrs)
                    except:
                        pass
                else:
                    continue

        # update stored information
        self.displayed_information = information

    def write_template(self, containers=[]):
        """
        write the form template to the screen and get fields
        :return: None
        """
        # clear screen
        self.screen.redraw()

        # combine parts of the template according to number and gpu settings of containers
        templates, use_gpu = [], []
        for container in containers:
                if container.use_gpu:
                    template = copy.deepcopy(self.template['base'])
                    template.append(self.template['gpu'])
                    templates.append(template)
                    use_gpu += [True]
                else:
                    templates.append(self.template['base'])
                    use_gpu += [False]

        # write the template to the display and get fields
        heigth = (self.screen.size[0] - self.screen.offset) // len(templates) if templates else 0
        lines = [self.screen.offset + i*heigth for i, _ in enumerate(templates)]
        fields_list = []
        for index, (line, template) in enumerate(zip(lines, templates)):
            self.screen.navigate(y=line, x=self.screen.indent)
            coordinates = self.screen.addmultiline(template)
            fields = {'name': coordinates[0][0],
                      'status': coordinates[0][1],
                      'docker name': coordinates[2][0],
                      'executor': coordinates[2][1],
                      'run_time': coordinates[3][0],
                      'created': coordinates[3][1],
                      'cpu': coordinates[4][0],
                      'memory': coordinates[4][1]}
            if use_gpu[index]:
                fields['id'] = coordinates[5][0]
                fields['usage'] = coordinates[5][1]

            def sort_fn(item):
                return item[1]['beginning']['y'], item[1]['beginning']['x']

            # sort the fields by their y coordinate first and x coordinate second
            fields = OrderedDict(sorted(list(fields.items()), key=sort_fn))
            fields_list.append(self.calculate_field_properties(fields))

        self.fields = fields_list
        self.first_call = False


class UserStats(DisplayFunction):

    def __init__(self, subwindow, dopq):
        """
        initialize fields, displayed information and form template
        :param subwindow: instance of SubWindowAndPad
        :param dopq: instance of DopQ
        """

        super(UserStats, self).__init__(subwindow, dopq)

        width = self.screen.size[1]
        width_unit = width // 8

        # init fields dict
        self.fields = [{'user': '',
                        'containers run': '',
                        'penalty': '',
                        'containers enqueued': ''}]

        # init information dict
        self.displayed_information = copy.deepcopy(self.fields)

        # init template
        self.template = [['user:  '],
                         ['-' * (width - 2 * self.screen.pad_indent)],  # hline
                         [pad_with_spaces('penalty:  ', width_unit, 'prepend'),
                          pad_with_spaces('containers run:  ', 3 * width_unit, 'prepend'),
                          pad_with_spaces('containers enqueued:  ', 3 * width_unit, 'prepend')]]

        self.height = len(self.template) + 2

    def update(self):
        """
        obtains new information and prints the fields that changed
        :return: NOne
        """

        # get new information from queue
        user_stats = self.dopq.users_stats

        # check if length of the user list has changed, if yes, redraw everything

        if len(user_stats) != len(self.displayed_information):
            self.write_template()
            self.rewrite_all = True

        # cycle users and print their stats if they have changed or if redraw_all
        for index, user in enumerate(user_stats):
            for field, value in list(user.items()):
                if self.rewrite_all or value != self.displayed_information[index][field]:
                    attrs = self.screen.BOLD if 'user' in field else 0
                    self.update_field(value, self.fields[index][field], attrs)
                else:
                    continue

        # update displayed information
        self.displayed_information = user_stats

        self.rewrite_all = False

    def write_template(self):
        """
        write form template to the screen and get fields
        :return: None
        """

        # combine parts of the template according to number and gpu settings of containers
        templates = [self.template] * len(self.dopq.user_list)

        # write the template to the display and get fields
        lines = [self.screen.offset + i * self.height for i, _ in enumerate(templates)]  # starting line for each template
        fields_list = []
        for index, (line, template) in enumerate(zip(lines, templates)):
            self.screen.navigate(y=line, x=self.screen.indent)
            coordinates = self.screen.addmultiline(template)
            fields = {'user': coordinates[0][0],
                      'penalty': coordinates[2][0],
                      'containers run': coordinates[2][1],
                      'containers enqueued': coordinates[2][2]}

            def sort_fn(item):
                return item[1]['beginning']['y'], item[1]['beginning']['x']

            fields = OrderedDict(sorted(list(fields.items()), key=sort_fn))
            fields_list.append(self.calculate_field_properties(fields))

        self.fields = fields_list
        self.first_call = False

        # limit scrolling, so that it stops on the last displayed container
        self.screen.scroll_limit = lines[-2]


class ContainerList(DisplayFunction):

    def __init__(self, subwindow, dopq, mode):
        """
                initializes fields, displayed_information and form template
                :param subwindow: instance of SubWindowAndPad
                :param dopq: instance of DopQ
                """

        super(ContainerList, self).__init__(subwindow, dopq)

        # store which list to fetch on update
        self.mode = mode

        width = self.screen.size[1]
        width_unit = width // 8

        # init fields dict
        self.fields = [{'position': '',
                        'name': '',
                        'status': '',
                        'docker name': '',
                        'executor': '',
                        'run time': '',
                        'created': ''}]

        # init information dict
        self.displayed_information = []

        # init template
        self.template = [['', '  ', # position
                          ' name:  ',  # name
                          pad_with_spaces('status:  ', 5 * width_unit, 'prepend')],  # end of first line
                         ['-' * (width - 2 * self.screen.indent -1 )],  # hline
                         [pad_with_spaces('docker name:  ', 2 * width_unit, 'prepend'),
                          pad_with_spaces('executor:  ', 3 * width_unit, 'prepend')],  # end of second line
                         [pad_with_spaces('uptime:  ', 2 * width_unit, 'prepend'),
                          pad_with_spaces('created:  ', 3 * width_unit, 'prepend')]]  # end of third line

        self.height = len(self.template) + 2
        self.max_containers = self.screen.height // self.height

    def get_list(self):
        """
        obtains the relevant container list from the queue depending on the set mode
        :return: list of Container objects
        """

        if self.mode == 'history':
            container_list = self.dopq.history
        elif self.mode == 'enqueued':
            container_list = self.dopq.container_list
        else:
            raise ValueError('invalid mode of operation: {}'.format(self.mode))

        if len(container_list) > self.max_containers:
            container_list = container_list[:self.max_containers]

        return container_list

    def update(self):
        """
        gets new information from the queue and updates the fields that have changed
        :return: None
        """

        # gather new information
        container_list = self.get_list()
        information = [container.history_info() for container in container_list]
        # check if the container list length is the same
        rewrite_all = False
        if len(information) != len(self.displayed_information):
            self.write_template(len(container_list))
            rewrite_all = True

        # update displayed information
        for index, container_information in enumerate(information):
            container_information['position'] = index
            for field, value in list(container_information.items()):

                # only rewrite field if it has changed
                if rewrite_all or value != self.displayed_information[index][field]:
                    attrs = 0
                    if 'status' in field:
                        attrs = pick_color(value) | self.screen.BOLD
                    elif 'name' in field or 'position' in field:
                        attrs = self.screen.BOLD
                    self.update_field(value, self.fields[index][field], attrs)
                else:
                    continue

        # update stored information
        self.displayed_information = information

    def write_template(self, n_containers=0):
        """
        write the form template to the screen and get fields
        :return: None
        """

        # clear screen
        self.screen.redraw()

        # update number of max containers on display
        self.max_containers = self.screen.pad_height // self.height

        # combine templates according to number of containers in the list
        templates = [self.template] * n_containers

        # write the template to the display and get fields
        lines = [self.screen.offset + i * self.height for i, _ in enumerate(templates)]
        fields_list = []
        for index, (line, template) in enumerate(zip(lines, templates)):
            self.screen.navigate(y=line, x=self.screen.indent)
            coordinates = self.screen.addmultiline(template)
            fields = {'position': coordinates[0][0],
                      'name': coordinates[0][2],
                      'status': coordinates[0][3],
                      'docker name': coordinates[2][0],
                      'executor': coordinates[2][1],
                      'run_time': coordinates[3][0],
                      'created': coordinates[3][1]}

            def sort_fn(item):
                return item[1]['beginning']['y'], item[1]['beginning']['x']

            # sort the fields by their y coordinate first and x coordinate second
            fields = OrderedDict(sorted(list(fields.items()), key=sort_fn))
            fields_list.append(self.calculate_field_properties(fields))

        self.fields = fields_list if fields_list else self.fields
        self.first_call = False

        # limit scrolling, so that it stops on the last displayed container
        self.screen.scroll_limit = lines[-2] if isinstance(lines, list) and len(lines) >= 2 else self.height


def pad_with_spaces(string, total_length, mode='append'):
    string_length = len(string)
    difference = total_length - string_length
    if difference < 0:
        # compact given string to max length
        string = string[:total_length]
        difference = 0

    append, prepend, center = False, False, False
    if mode == 'append':
        append = True
        prepend = False
        center = False
    elif mode == 'prepend':
        append = False
        prepend = True
    elif mode == 'center':
        append = True
        prepend = True
        center = True
    else:
        raise ValueError('unknown mode: {}'.format(mode))

    padding = (' ' * int(floor(difference / (1+center))), ' ' * int(ceil(difference / (1+center))))
    padded_string = (prepend * padding[0]) + string + (append * padding[1])

    return padded_string


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
    elif status == 'dead':
        return curses.color_pair(5)
    else:
        return 0


def run_interface(dopq):
    try:
        curses.wrapper(main, dopq)
    except:
        LOG.error(traceback.format_exc())
    finally:
        gpu.GPU.stop_hardware_monitor()


def main(screen, dopq):
    # define color pairs
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_BLUE, curses.COLOR_BLACK)


    screen.idcok(False)
    screen.idlok(False)

    interface = Interface(dopq, screen, offset=4, indent=2)
    interface()


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


if __name__ == '__main__':
    run_interface('')