#!/usr/bin/env python

import time
from typing import Any
from .menu import *

class Task:
    title = ''
    cmd = ''
    param = None
    stop_on_error = True
    tm = None

    def __init__(self, title, cmd, param=None, stop_on_error=True):
        self.title = title
        self.cmd = cmd
        self.param = param
        self.stop_on_error = stop_on_error

    def set_tm(self, tm):
        if self.tm is not None:
            exit(1) # not allowed

        self.tm = tm
        
        if len(self.title) > self.tm.title_max_length:
            self.tm.title_max_length = len(self.title)

    def __call__(self, **kwargs):
        if self.stop_on_error and self.tm.is_error_occurred:
            return

        start = time.process_time()
        res = 0
        
        if (isinstance(self.cmd, str)) : res = os.system(self.cmd)
        else: res = self.cmd(**kwargs)
        
        took = time.process_time() - start

        msg = 'success'
        color = ECOLORS.OKGREEN

        if res != 0:
            msg = 'fail'
            color = ECOLORS.WARNING

            if self.stop_on_error:
                self.tm.is_error_occurred = True

        self.tm.logs.append(color + '[' + self.title + ']' + (self.tm.title_max_length - len(self.title) + 1) * ' ' + msg + ' ' * 4 + '[' + str(took) + '] seconds took')

        return res

    def __str__(self):
        return self.title

class MultiTask:
    title = ''
    tasks = []
    param = None
    tm = None

    def __init__(self, title, tasks):
        self.title = title
        self.tasks = tasks

    def set_tm(self, tm):
        if self.tm is not None: exit(1) # not allowed

        for task in self.tasks:
            task.set_tm(tm)

    def __str__(self):
        return self.title

    def __call__(self, **kwargs):
        for task in self.tasks:
            res = task(**kwargs)
            if res != 0:
                return res

        return 0

class TaskManager:
    list = {}
    logs = []
    title_max_length = 0
    is_error_occurred = False
    only_once = False

    def __init__(self):
        self.list = {}
        self.logs = []
        self.title_max_length = 0
        self.is_error_occurred = False

    def add(self, task):
        self.list[str(task)] = task
        task.set_tm(self)

    def set_only_once(self):
        self.only_once = True

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        print('task manager call')

class SingleTaskManager(TaskManager):
    def __init__(self):
        super().__init__()

    def __call__(self, **kwargs):
        res = 0
        while True:
            sys.stdout.write(Style.RESET_ALL)
            self.logs = []
            self.is_error_occurred = False

            task = select(self.list)

            if task is None:
                break

            start = time.process_time()

            res = task(**kwargs)

            print()

            for log in self.logs:
                sys.stdout.write(log)
                print()

            print()

            if self.only_once:
                break

        return res

class MultiTaskManager(TaskManager):
    title = ''
    is_expanded = False
    chosen = []

    def __init__(self, title=''):
        super().__init__()
        self.title = title

    def __call__(self, **kwargs):
        res = 0
        while True:
            sys.stdout.write(Style.RESET_ALL)
            self.logs = []
            self.is_error_occurred = False

            tasks = multi_select(self.list)

            if len(tasks) == 0:
                break

            expanded_tasks = []

            start = time.process_time()

            for task in tasks:
                try:
                    if isinstance(task, MultiTaskManager):
                        for expanded in task.expand():
                            expanded_tasks.append(expanded)
                    else:
                        expanded_tasks.append(task)
                except:
                    None

            for task in expanded_tasks:
                res = task(**kwargs)
                if (res != 0):
                    return res

            print()

            for log in self.logs:
                sys.stdout.write(log)
                print()

            print()

            if self.only_once:
                break

        return res

    def expand(self):
        if not self.is_expanded:
            self.chosen = multi_select(self.list)
        else:
            self.is_expanded = True

        return self.chosen

    def set_tm(self, tm):
        None