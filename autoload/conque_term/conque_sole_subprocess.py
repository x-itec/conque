# FILE:     autoload/conque_term/conque_sole_subprocess.py {{{
# AUTHOR:   Nico Raffo <nicoraffo@gmail.com>
# WEBSITE:  http://conque.googlecode.com
# MODIFIED: __MODIFIED__
# VERSION:  __VERSION__, for Vim 7.0
# LICENSE:
# Conque - Vim terminal/console emulator
# Copyright (C) 2009-__YEAR__ Nico Raffo
#
# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE. }}}

""" ConqueSoleSubprocess {{{

Creates a new subprocess with it's own (hidden) console window.

Mirrors console window text onto a block of shared memory (mmap), along with
text attribute data. Also handles translation of text input into the format
Windows console expects.

Sample Usage:

    sh = ConqueSoleSubprocess()
    sh.open("cmd.exe", "unique_str")

    shm_in = ConqueSoleSharedMemory(mem_key = "unique_str", mem_type = "input", ...)
    shm_out = ConqueSoleSharedMemory(mem_key = "unique_str", mem_type = "output", ...)

    output = shm_out.read(...)
    shm_in.write("dir\r")
    output = shm_out.read(...)

Requirements:

    * Python for Windows extensions. Available at http://sourceforge.net/projects/pywin32/
    * Must be run from process attached to an existing console.

}}} """

import time
import re
import os
import ctypes

from conque_globals import *
from conque_win32_util import *
from conque_sole_shared_memory import *


class ConqueSoleSubprocess():

    # Class properties {{{

    #window = None
    handle = None
    pid = None

    # input / output handles
    stdin = None
    stdout = None

    # size of console window
    window_width = 160
    window_height = 40

    # max lines for the console buffer
    buffer_width = 160
    buffer_height = 100

    # keep track of the buffer number at the top of the window
    top = 0
    line_offset = 0

    # buffer height is CONQUE_SOLE_BUFFER_LENGTH * output_blocks
    output_blocks = 1

    # cursor position
    cursor_line = 0
    cursor_col = 0

    # console data, array of lines
    data = []

    # console attribute data, array of array of int
    attributes = []
    attribute_cache = {}

    # default attribute
    default_attribute = 7

    # shared memory objects
    shm_input = None
    shm_output = None
    shm_attributes = None
    shm_stats = None
    shm_command = None
    shm_rescroll = None
    shm_resize = None

    # are we still a valid process?
    is_alive = True

    # running in fast mode
    fast_mode = 0

    # used for periodic execution of screen and memory redrawing
    screen_redraw_ct = 0
    mem_redraw_ct = 0

    # }}}

    # ****************************************************************************
    # initialize class instance

    def __init__(self): # {{{

        pass

    # }}}

    # ****************************************************************************
    # Create proccess cmd

    def open(self, cmd, mem_key, options={}): # {{{

        logging.debug('cmd is: ' + cmd)

        self.reset = True

        try:
            # if we're already attached to a console, then unattach
            try:
                ctypes.windll.kernel32.FreeConsole()
            except:
                pass

            # set buffer height
            self.buffer_height = CONQUE_SOLE_BUFFER_LENGTH
            logging.info(str(options))
            if 'LINES' in options and 'COLUMNS' in options:
                self.window_width = options['COLUMNS']
                self.window_height = options['LINES']
                self.buffer_width = options['COLUMNS']

            # fast mode
            self.fast_mode = options['FAST_MODE']

            # console window options
            si = STARTUPINFO()

            # hide window
            si.dwFlags |= STARTF_USESHOWWINDOW
            si.wShowWindow = SW_HIDE
            #si.wShowWindow = SW_MINIMIZE

            # process options
            flags = NORMAL_PRIORITY_CLASS | CREATE_NEW_PROCESS_GROUP | CREATE_UNICODE_ENVIRONMENT | CREATE_NEW_CONSOLE

            # created process info
            pi = PROCESS_INFORMATION()

            logging.debug('using path ' + os.path.abspath('.'))

            # create the process!
            res = ctypes.windll.kernel32.CreateProcessW(None, u(cmd), None, None, 0, flags, None, u('.'), ctypes.byref(si), ctypes.byref(pi))

            logging.info(str(res))
            logging.info(str(ctypes.GetLastError()))
            logging.info(str(ctypes.FormatError(ctypes.GetLastError())))
            self.pid = pi.dwProcessId
            self.handle = pi.hProcess
            logging.info('process pid is ' + str(self.pid))
            logging.debug(str(self.handle))

            # attach ourselves to the new console
            # console is not immediately available
            for i in range(10):
                time.sleep(1)
                try:
                    logging.debug('attempt ' + str(i))
                    res = ctypes.windll.kernel32.AttachConsole(self.pid)

                    logging.debug('attach result')
                    logging.debug(str(res))
                    logging.debug(str(ctypes.GetLastError()))
                    logging.debug(str(ctypes.FormatError(ctypes.GetLastError())))

                    break
                except:
                    logging.info(traceback.format_exc())
                    pass

            # get input / output handles
            self.stdout = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
            self.stdin = ctypes.windll.kernel32.GetStdHandle(STD_INPUT_HANDLE)

            # set buffer size
            size = COORD(self.buffer_width, self.buffer_height)
            res = ctypes.windll.kernel32.SetConsoleScreenBufferSize(self.stdout, size)
            logging.debug('buffer size: ' + str(size.to_str()))

            logging.debug('size result')
            logging.debug(str(res))
            logging.debug(str(ctypes.GetLastError()))
            logging.debug(str(ctypes.FormatError(ctypes.GetLastError())))

            # prev set size call needs to process
            time.sleep(0.2)

            # set window size
            self.set_window_size(self.window_width, self.window_height)

            # set utf-8 code page
            if 'CODE_PAGE' in options and options['CODE_PAGE'] > 0:
                if ctypes.windll.kernel32.IsValidCodePage(ctypes.c_uint(options['CODE_PAGE'])):
                    logging.info('setting code page to ' + str(options['CODE_PAGE']))
                    ctypes.windll.kernel32.SetConsoleCP(ctypes.c_uint(options['CODE_PAGE']))
                    ctypes.windll.kernel32.SetConsoleOutputCP(ctypes.c_uint(options['CODE_PAGE']))

            # init shared memory
            self.init_shared_memory(mem_key)

            # init read buffers
            self.tc = ctypes.create_unicode_buffer(self.buffer_width)
            self.ac = ctypes.create_unicode_buffer(self.buffer_width)

            return True

        except:
            logging.info(traceback.format_exc())
            return False

    # }}}

    # ****************************************************************************
    # create shared memory objects

    def init_shared_memory(self, mem_key): # {{{

        buf_info = self.get_buffer_info()
        logging.debug('-------------------------------------')
        logging.debug(buf_info.to_str())
        logging.debug('-------------------------------------')

        self.shm_input = ConqueSoleSharedMemory(CONQUE_SOLE_INPUT_SIZE, 'input', mem_key)
        self.shm_input.create('write')
        self.shm_input.clear()

        self.shm_output = ConqueSoleSharedMemory(self.buffer_height * self.buffer_width, 'output', mem_key, True)
        self.shm_output.create('write')
        self.shm_output.clear()

        if not self.fast_mode:
            self.shm_attributes = ConqueSoleSharedMemory(self.buffer_height * self.buffer_width, 'attributes', mem_key, True, chr(buf_info.wAttributes), encoding='latin-1')
            self.shm_attributes.create('write')
            self.shm_attributes.clear()

        self.shm_stats = ConqueSoleSharedMemory(CONQUE_SOLE_STATS_SIZE, 'stats', mem_key, serialize=True)
        self.shm_stats.create('write')
        self.shm_stats.clear()

        self.shm_command = ConqueSoleSharedMemory(CONQUE_SOLE_COMMANDS_SIZE, 'command', mem_key, serialize=True)
        self.shm_command.create('write')
        self.shm_command.clear()

        self.shm_resize = ConqueSoleSharedMemory(CONQUE_SOLE_RESIZE_SIZE, 'resize', mem_key, serialize=True)
        self.shm_resize.create('write')
        self.shm_resize.clear()

        self.shm_rescroll = ConqueSoleSharedMemory(CONQUE_SOLE_RESCROLL_SIZE, 'rescroll', mem_key, serialize=True)
        self.shm_rescroll.create('write')
        self.shm_rescroll.clear()

        return True

    # }}}

    # ****************************************************************************
    # check for and process commands

    def check_commands(self): # {{{

        cmd = self.shm_command.read()

        if cmd:

            # shut it all down
            if cmd['cmd'] == 'close':

                # clear command
                self.shm_command.clear()

                self.close()
                return

        cmd = self.shm_resize.read()

        if cmd:

            # clear command
            self.shm_resize.clear()

            # resize console
            if cmd['cmd'] == 'resize':

                logging.info('resizing window to ' + str(cmd['data']['width']) + 'x' + str(cmd['data']['height']))

                # only change buffer width if it's larger
                if cmd['data']['width'] > self.buffer_width:
                    self.buffer_width = cmd['data']['width']

                # always change console width and height
                self.window_width = cmd['data']['width']
                self.window_height = cmd['data']['height']

                # reset the console
                buf_info = self.get_buffer_info()
                self.reset_console(buf_info, add_block=False)

        # }}}

    # ****************************************************************************
    # read from windows console and update output buffer

    def read(self, timeout=0): # {{{

        # no point really
        if self.screen_redraw_ct == 0 and not self.is_alive():
            stats = {'top_offset': 0, 'default_attribute': 0, 'cursor_x': 0, 'cursor_y': self.cursor_line, 'is_alive': 0}
            logging.info('is dead')
            self.shm_stats.write(stats)
            return

        # check for commands
        self.check_commands()

        # emulate timeout by sleeping timeout time
        if timeout > 0:
            read_timeout = float(timeout) / 1000
            #logging.debug("sleep " + str(read_timeout) + " seconds")
            time.sleep(read_timeout)

        # get cursor position
        buf_info = self.get_buffer_info()
        curs_line = buf_info.dwCursorPosition.Y
        curs_col = buf_info.dwCursorPosition.X

        # set update range
        if curs_line != self.cursor_line or self.top != buf_info.srWindow.Top or self.screen_redraw_ct == CONQUE_SOLE_SCREEN_REDRAW:
            self.screen_redraw_ct = 0
            logging.debug('screen redraw')
            read_start = self.top
            read_end = buf_info.srWindow.Bottom + 1
        else:
            logging.debug('no screen redraw')
            read_start = curs_line
            read_end = curs_line + 1

        # vars used in for loop
        coord = COORD(0, 0)
        chars_read = ctypes.c_int(0)

        # read new data
        for i in range(read_start, read_end):

            coord.Y = i

            res = ctypes.windll.kernel32.ReadConsoleOutputCharacterW(self.stdout, ctypes.byref(self.tc), self.buffer_width, coord, ctypes.byref(chars_read))
            ctypes.windll.kernel32.ReadConsoleOutputAttribute(self.stdout, ctypes.byref(self.ac), self.buffer_width, coord, ctypes.byref(chars_read))

            t = self.tc.value
            a = self.ac.value

            # add data
            if i >= len(self.data):
                self.data.append(t)
                self.attributes.append(a)
            else:
                self.data[i] = t
                self.attributes[i] = a

            #logging.debug(str(chars_read))
            #logging.info('---')
            #logging.info(t)
            #for i in range(0, len(t)):
            #    logging.info("char " + t[i])
            #    logging.info("char " + str(ord(t[i])))
            #logging.debug("attributes " + str(i) + " is: " + str(a))

        # write new output to shared memory
        if self.mem_redraw_ct == CONQUE_SOLE_MEM_REDRAW:
            self.mem_redraw_ct = 0
            logging.debug('mem redraw')
            for i in range(0, len(self.data)):
                self.shm_output.write(text=self.data[i], start=self.buffer_width * i)
                if not self.fast_mode:
                    self.shm_attributes.write(text=self.attributes[i], start=self.buffer_width * i)
        else:
            logging.debug('no mem redraw')
            for i in range(read_start, read_end):
                self.shm_output.write(text=self.data[i], start=self.buffer_width * i)
                if not self.fast_mode:
                    self.shm_attributes.write(text=self.attributes[i], start=self.buffer_width * i)
                #self.shm_output.write(text=''.join(self.data[read_start:read_end]), start=read_start * self.buffer_width)
                #self.shm_attributes.write(text=''.join(self.attributes[read_start:read_end]), start=read_start * self.buffer_width)

        # write cursor position to shared memory
        stats = {'top_offset': buf_info.srWindow.Top, 'default_attribute': buf_info.wAttributes, 'cursor_x': curs_col, 'cursor_y': curs_line, 'is_alive': 1}
        self.shm_stats.write(stats)
        #logging.debug('wtf cursor: ' + str(buf_info))

        # adjust screen position
        self.top = buf_info.srWindow.Top
        self.cursor_line = curs_line

        # check for reset
        if curs_line > buf_info.dwSize.Y - 200:
            self.reset_console(buf_info)

        # increment redraw counters
        self.screen_redraw_ct += 1
        self.mem_redraw_ct += 1

        return None

    # }}}

    # ****************************************************************************
    # clear the console and set cursor at home position

    def reset_console(self, buf_info, add_block=True): # {{{

        # sometimes we just want to change the buffer width,
        # in which case no need to add another block
        if add_block:
            self.output_blocks += 1

        # close down old memory
        self.shm_output.close()
        self.shm_output = None

        if not self.fast_mode:
            self.shm_attributes.close()
            self.shm_attributes = None

        # new shared memory key
        mem_key = 'mk' + str(time.time())

        # reallocate memory
        self.shm_output = ConqueSoleSharedMemory(self.buffer_height * self.buffer_width * self.output_blocks, 'output', mem_key, True)
        self.shm_output.create('write')
        self.shm_output.clear()

        # backfill data
        if len(self.data[0]) < self.buffer_width:
            for i in range(0, len(self.data)):
                self.data[i] = self.data[i] + ' ' * (self.buffer_width - len(self.data[i]))
        self.shm_output.write(''.join(self.data))

        if not self.fast_mode:
            self.shm_attributes = ConqueSoleSharedMemory(self.buffer_height * self.buffer_width * self.output_blocks, 'attributes', mem_key, True, chr(buf_info.wAttributes), encoding='latin-1')
            self.shm_attributes.create('write')
            self.shm_attributes.clear()

        # backfill attributes
        if len(self.attributes[0]) < self.buffer_width:
            for i in range(0, len(self.attributes)):
                self.attributes[i] = self.attributes[i] + chr(buf_info.wAttributes) * (self.buffer_width - len(self.attributes[i]))
        if not self.fast_mode:
            self.shm_attributes.write(''.join(self.attributes))

        # notify wrapper of new output block
        self.shm_rescroll.write({'cmd': 'new_output', 'data': {'blocks': self.output_blocks, 'mem_key': mem_key}})

        # set buffer size
        size = COORD(X=self.buffer_width, Y=self.buffer_height * self.output_blocks)
        logging.debug('new buffer size: ' + str(size))
        res = ctypes.windll.kernel32.SetConsoleScreenBufferSize(self.stdout, size)

        logging.debug('buf size result')
        logging.debug(str(res))
        logging.debug(str(ctypes.GetLastError()))
        logging.debug(str(ctypes.FormatError(ctypes.GetLastError())))

        # prev set size call needs to process
        time.sleep(0.2)

        # set window size
        self.set_window_size(self.window_width, self.window_height)

        # init read buffers
        self.tc = ctypes.create_unicode_buffer(self.buffer_width)
        self.ac = ctypes.create_unicode_buffer(self.buffer_width)

    # }}}

    # ****************************************************************************
    # write text to console. this function just parses out special sequences for
    # special key events and passes on the text to the plain or virtual key functions

    def write(self): # {{{

        # get input from shared mem
        text = self.shm_input.read()

        # nothing to do here
        if text == u(''):
            return

        logging.info(u('writing: ') + text)

        # clear input queue
        self.shm_input.clear()

        # split on VK codes
        chunks = CONQUE_WIN32_REGEX_VK.split(text)

        # if len() is one then no vks
        if len(chunks) == 1:
            self.write_plain(text)
            return

        logging.debug('split!: ' + str(chunks))

        # loop over chunks and delegate
        for t in chunks:

            if t == '':
                continue

            if CONQUE_WIN32_REGEX_VK.match(t):
                logging.debug('match!: ' + str(t[2:-2]))
                self.write_vk(t[2:-2])
            else:
                self.write_plain(t)

    # }}}

    # ****************************************************************************

    def write_plain(self, text): # {{{

        li = INPUT_RECORD * len(text)
        list_input = li()

        for i in range(0, len(text)):

            # create keyboard input
            ke = KEY_EVENT_RECORD()
            ke.bKeyDown = ctypes.c_byte(1)
            ke.wRepeatCount = ctypes.c_short(1)

            cnum = ord(text[i])
            logging.debug('writing char: ' + str(cnum))
            ke.wVirtualKeyCode = ctypes.windll.user32.VkKeyScanW(cnum)
            ke.wVirtualScanCode = ctypes.c_short(ctypes.windll.user32.MapVirtualKeyW(int(cnum), 0))

            if cnum > 31:
                ke.uChar.UnicodeChar = uchr(cnum)
            elif cnum == 3:
                ctypes.windll.kernel32.GenerateConsoleCtrlEvent(0, self.pid)
                ke.uChar.UnicodeChar = uchr(cnum)
                ke.wVirtualKeyCode = ctypes.windll.user32.VkKeyScanW(cnum + 96)
                ke.dwControlKeyState |= LEFT_CTRL_PRESSED
            else:
                ke.uChar.UnicodeChar = uchr(cnum)
                if cnum in CONQUE_WINDOWS_VK_INV:
                    ke.wVirtualKeyCode = cnum
                else:
                    ke.wVirtualKeyCode = ctypes.windll.user32.VkKeyScanW(cnum + 96)
                    ke.dwControlKeyState |= LEFT_CTRL_PRESSED

            logging.info(str(ord(text[i])) + ' ' + text[i])
            logging.info(ke.dwControlKeyState)

            kc = INPUT_RECORD(KEY_EVENT)
            kc.Event.KeyEvent = ke
            list_input[i] = kc

            #logging.debug(kc.to_str())

        # write input array
        events_written = ctypes.c_int()
        res = ctypes.windll.kernel32.WriteConsoleInputW(self.stdin, list_input, len(text), ctypes.byref(events_written))

        logging.debug('foo')
        logging.debug('events written ' + str(events_written))
        logging.debug(str(res))
        logging.debug(str(ctypes.GetLastError()))
        logging.debug(str(ctypes.FormatError(ctypes.GetLastError())))


    # }}}

    # ****************************************************************************

    def write_vk(self, vk_code): # {{{
        logging.debug('virtual key code' + str(vk_code))

        code = None
        ctrl_pressed = False

        # this could be made more generic when more attributes
        # other than ctrl_pressed are available
        vk_attributes = vk_code.split(';')
        logging.debug(vk_attributes)
        for attr in vk_attributes:
            if attr == CONQUE_VK_ATTR_CTRL_PRESSED:
                ctrl_pressed = True
            else:
                code = attr

        li = INPUT_RECORD * 1

        # create keyboard input
        ke = KEY_EVENT_RECORD()
        ke.uChar.UnicodeChar = uchr(0)
        ke.wVirtualKeyCode = ctypes.c_short(int(code))
        ke.wVirtualScanCode = ctypes.c_short(ctypes.windll.user32.MapVirtualKeyW(int(code), 0))
        ke.bKeyDown = ctypes.c_byte(1)
        ke.wRepeatCount = ctypes.c_short(1)

        # set enhanced key mode for arrow keys
        if code in CONQUE_WINDOWS_VK_ENHANCED:
            logging.debug('enhanced key!')
            ke.dwControlKeyState |= ENHANCED_KEY

        if ctrl_pressed:
            ke.dwControlKeyState |= LEFT_CTRL_PRESSED

        kc = INPUT_RECORD(KEY_EVENT)
        kc.Event.KeyEvent = ke
        list_input = li(kc)

        # write input array
        events_written = ctypes.c_int()
        res = ctypes.windll.kernel32.WriteConsoleInputW(self.stdin, list_input, 1, ctypes.byref(events_written))

        logging.debug('events written ' + str(events_written))
        logging.debug(str(res))
        logging.debug(str(ctypes.GetLastError()))
        logging.debug(str(ctypes.FormatError(ctypes.GetLastError())))

    # }}}

    # ****************************************************************************

    def close(self): # {{{

        # record status
        self.is_alive = False
        try:
            stats = {'top_offset': 0, 'default_attribute': 0, 'cursor_x': 0, 'cursor_y': self.cursor_line, 'is_alive': 0}
            self.shm_stats.write(stats)
        except:
            pass

        pid_list = (ctypes.c_int * 10)()
        num = ctypes.windll.kernel32.GetConsoleProcessList(pid_list, 10)

        logging.debug("\n".join(self.data))

        current_pid = os.getpid()

        logging.info('closing down!')
        logging.info(str(self.pid))
        logging.info(str(pid_list))

        # kill subprocess pids
        for pid in pid_list[0:num]:
            if not pid:
                break

            # kill current pid last
            if pid == current_pid:
                continue
            try:
                self.close_pid(pid)
            except:
                logging.info(traceback.format_exc())
                pass

        # kill this process
        try:
            self.close_pid(current_pid)
        except:
            logging.info(traceback.format_exc())
            pass

    def close_pid(self, pid):
        logging.info('killing pid ' + str(pid))
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, 0, pid)
        ctypes.windll.kernel32.TerminateProcess(handle, -1)
        ctypes.windll.kernel32.CloseHandle(handle)

    # }}}

    # ****************************************************************************
    # check process health

    def is_alive(self): # {{{

        status = ctypes.windll.kernel32.WaitForSingleObject(self.handle, 1)

        if status == 0:
            logging.info('process is no longer alive!')
            self.is_alive = False

        return self.is_alive

        # }}}


    # ****************************************************************************
    # return screen data as string

    def get_screen_text(self): # {{{

        return "\n".join(self.data)

        # }}}

    # ****************************************************************************

    def set_window_size(self, width, height): # {{{

        logging.debug('*** setting window size')

        # get current window size object
        window_size = SMALL_RECT(0, 0, 0, 0)

        # buffer info has maximum window size data
        buf_info = self.get_buffer_info()
        logging.debug(str(buf_info.to_str()))

        # set top left corner
        window_size.Top = 0
        window_size.Left = 0

        # set bottom right corner
        if buf_info.dwMaximumWindowSize.X < width:
            logging.debug(str(buf_info.dwMaximumWindowSize.X) + '<' + str(width))
            window_size.Right = buf_info.dwMaximumWindowSize.X - 1
        else:
            window_size.Right = width - 1

        if buf_info.dwMaximumWindowSize.Y < height:
            logging.debug('b')
            window_size.Bottom = buf_info.dwMaximumWindowSize.Y - 1
        else:
            window_size.Bottom = height - 1

        logging.debug('window size: ' + str(window_size.to_str()))

        # set the window size!
        res = ctypes.windll.kernel32.SetConsoleWindowInfo(self.stdout, ctypes.c_bool(True), ctypes.byref(window_size))

        logging.debug('win size result')
        logging.debug(str(res))
        logging.debug(str(ctypes.GetLastError()))
        logging.debug(str(ctypes.FormatError(ctypes.GetLastError())))

        # reread buffer info to get final console max lines
        buf_info = self.get_buffer_info()
        logging.debug('buffer size: ' + str(buf_info))
        self.window_width = buf_info.srWindow.Right + 1
        self.window_height = buf_info.srWindow.Bottom + 1

        # }}}

    # ****************************************************************************
    # get buffer info, used a lot

    def get_buffer_info(self): # {{{

        buf_info = CONSOLE_SCREEN_BUFFER_INFO()
        ctypes.windll.kernel32.GetConsoleScreenBufferInfo(self.stdout, ctypes.byref(buf_info))

        return buf_info

        # }}}


# vim:foldmethod=marker
