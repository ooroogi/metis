#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from colorama import Fore, Back, Style, init

# Cross-platform getch implementation
try:
    from msvcrt import getch  # Windows
    def get_key():
        return ord(getch())
except ImportError:
    def get_key():  # Unix/Linux/macOS
        import tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == '\x1b':  # ESC sequence for arrow keys
                next_ch = sys.stdin.read(2)
                if next_ch == '[A':  # Up arrow
                    return 72  # Windows up arrow code
                elif next_ch == '[B':  # Down arrow
                    return 80  # Windows down arrow code
                elif next_ch == '[C':  # Right arrow
                    return 77
                elif next_ch == '[D':  # Left arrow
                    return 75
                elif next_ch == '[H':  # Home
                    return 71
                elif next_ch == '[F':  # End
                    return 79
                else:
                    return 27  # ESC
            elif ch == '\r':
                return 13  # Enter
            elif ch == '\n':
                return 10  # Line feed
            elif ch == '\x03':  # Ctrl+C
                return 3
            else:
                return ord(ch)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

class ECOLORS:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[96m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def walk_level(some_dir, target_list, file=False, level=0):
    some_dir = some_dir.rstrip(os.path.sep)
    assert os.path.isdir(some_dir)
    num_sep = some_dir.count(os.path.sep)
    for root, dirs, files in os.walk(some_dir):
        if file == False:
            for i in dirs:
                target_list.append(i)
        else:
            for i in files:
                target_list.append(i)
                
        num_sep_this = root.count(os.path.sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]

def down(curr, lst):
    if curr == len(lst) - 1:
        return 0
    else:
        return curr + 1
        
def up(curr, lst):
    if curr == 0:
        return len(lst) - 1
    else:
        return curr - 1
            
def _menu_core(getin, multi=False):
    if len(getin) == 0: return [] if multi else None

    t = type(getin)
    lst = list(getin.keys()) if t is dict else list(getin) if t is set else getin
    curr = 0
    selected = [False] * len(lst) if multi else None
    max_len = max(len(item) for item in lst) + (12 if multi else 1)

    while True:
        sys.stdout.write(max_len * '─' + '\n')
        for idx, item in enumerate(lst):
            color = ''
            arrow = '→ ' if idx == curr else '  '
            chosen = ''
            if multi:
                chosen = ' [√] ' if selected[idx] else ' [ ] '
                color = ECOLORS.OKGREEN if selected[idx] else ''
            if idx == curr:
                color = ECOLORS.OKBLUE
            sys.stdout.write(f"{color}{arrow}{chosen}{item} \n{Style.RESET_ALL}")
        sys.stdout.write(max_len * '─' + '\n')

        key_code = get_key()
        
        if key_code == 13 or key_code == 10:  # enter (CR or LF)
            if multi:
                res = []
                for i, sel in enumerate(selected):
                    if sel:
                        res.append(lst[i] if t is set else getin[lst[i]])
                if not res: continue
                print()
                return res
            else:
                print()
                if t is dict: return getin[lst[curr]]
                if t is set: return lst[curr]
                return getin[curr]
        elif multi and key_code == 32:  # space
            selected[curr] = not selected[curr]
        elif key_code == 72:  # up arrow
            curr = up(curr, lst)
        elif key_code == 80:  # down arrow
            curr = down(curr, lst)
        elif key_code == 71:  # home
            curr = 0
        elif key_code == 79:  # end
            curr = len(lst) - 1
        elif key_code == 27 or key_code == 3:  # esc or ctrl+c
            exit()
            # return [] if multi else None
        sys.stdout.write('\x1b[{0}A'.format(len(lst) + 2))

def select(getin):
    return _menu_core(getin, multi=False)

def multi_select(getin):
    return _menu_core(getin, multi=True)

init()