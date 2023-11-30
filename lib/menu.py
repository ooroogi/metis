#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from colorama import Fore, Back, Style, init
from msvcrt import getch

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
            
def select(getin):
    curr = 0

    t = type(getin)

    if t is dict: lst = list(getin.keys())
    elif t is set: lst = list(getin)
    else: lst = getin

    max = 0
    for item in lst:
        length = len(item)
        if length > max: max = length + 1

    print()
    while True:
        sys.stdout.write(max*'─')
        sys.stdout.write('\n')
        for index in range(len(lst)):
            color = ''

            if index == curr:
                arrow = '→'
                color = ECOLORS.OKBLUE
            else:
                arrow = '  '
                color = ''

            sys.stdout.write(color + ' ' + arrow + ' ' + lst[index] + '  \n' + Style.RESET_ALL)

        sys.stdout.write(max*'─')
        sys.stdout.write('\n')

        key = ord(getch())

        if key == 13: #enter
            print()
            if t is dict: return getin[lst[curr]]
            if t is set: return lst[curr]
            else: return getin[curr]
        elif key == 72: #up
            curr = up(curr, lst)
        elif key == 80: #down
            curr = down(curr, lst)
        elif key == 71: #home
            curr = 0
        elif key == 79: #end
            curr = len(lst) - 1
        elif key == 27:  # esc
            return None
        elif key == 3:  # crtl + c
            return None

        sys.stdout.write('\x1b[{0}A'.format(len(lst) + 2))

    print()

def multi_select(getin):
    if len(getin) == 0: return

    curr = 0
    t = type(getin)

    if t is dict: lst = list(getin.keys())
    elif t is set: lst = list(getin)
    else: lst = getin

    selected = [False] * len(lst)

    max = 0
    for item in lst:
        length = len(item)
        if length > max: max = length + 12

    while True:
        sys.stdout.write(max*'─')
        sys.stdout.write('\n')
        for index in range(len(lst)):
            color = ''

            if selected[index] is True:
                chosen = ' [√] '
                color = ECOLORS.OKGREEN
            else: chosen = ' [ ] '

            if index == curr:
                arrow = '→'
                color = ECOLORS.OKBLUE
            else: arrow = '  '

            sys.stdout.write(color + arrow + chosen + lst[index] + ' \n' + Style.RESET_ALL)

        sys.stdout.write(max*'─')
        sys.stdout.write('\n')

        key = ord(getch())

        if key == 13:  # enter
            res = []
            # selected[curr] = True
            for i in range(0, len(selected)):
                if selected[i] is True:
                    if t is set: res.append(lst[i])
                    else: res.append(getin[lst[i]])

            if res == []: continue

            print()
            return res
        elif key == 32: # space
            selected[curr] = not selected[curr]
        elif key == 72:  # up
            curr = up(curr, lst)
        elif key == 80:  # down
            curr = down(curr, lst)
        elif key == 71:  # home
            curr = 0
        elif key == 79:  # end
            curr = len(lst) - 1
        elif key == 27:  # esc
            return []
        elif key == 3:  # crtl + c
            return []

        sys.stdout.write('\x1b[{0}A'.format(len(lst) + 2))

init()