#!/usr/bin/env python

from lib.task import *

def sample(name):
    print('lambda_sample: ' + name)
    return 0

multi_tasks = MultiTask('multi tasks',
    [
        Task('run a', lambda: sample('a')),
        Task('run b', lambda: sample('b')),
    ]
)

if __name__ == '__main__':
    task_manager_sample = MultiTaskManager()
    task_manager_sample.add(multi_tasks)
    task_manager_sample.add(Task('task with lambda', lambda: sample('hello')))
    task_manager_sample.add(Task('os.system sample', 'echo hi'))
    task_manager_sample()