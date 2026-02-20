#!/usr/bin/env python

import sys, subprocess
from pathlib import Path
from lib.bootstrap import ensure_init
ensure_init()
from lib.task import *
from lib.task import TASK_CANCELLED, Modal

# Settings management
script_dir = Path(__file__).parent
# Convert Windows path to MSYS/Git Bash format (C:/... -> /c/...)
_posix_path = script_dir.as_posix()
if len(_posix_path) >= 2 and _posix_path[1] == ':':
    script_dir_posix = '/' + _posix_path[0].lower() + _posix_path[2:]
else:
    script_dir_posix = _posix_path

def set_terminal_title(title):
    """Set the terminal window title."""
    sys.stdout.write(f'\033]0;{title}\007')
    sys.stdout.flush()

def get_git_branch(repo_dir):
    try:
        result = subprocess.run(
            ['git', '-C', str(repo_dir), 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ''

if __name__ == '__main__':
    set_terminal_title('metis')
    m = SectionedTaskManager()
    m.set_only_once()

    multi = Section('Multi', multi=True)
    multi.add(Task('echo hello', 'echo hello'))
    multi.add(Task('echo world', 'echo world'))
    m.add_section(multi)

    modal_a = Modal('Modal A')
    modal_a.add_step('menu 1', {
        '1': '1',
        '2': '2',
    })
    modal_a.add_step('menu 2', {
        '3': '3',
        '4': '4',
    })
    modal_a.set_command(
        lambda s: f'echo {" ".join(s)}')

    modal = Section('Modal')
    modal.add(Task('Modal A', modal_a))
    m.add_section(modal)

    # Build banner with info box matching menu width
    width = m.get_menu_width()
    inner = width - 2
    branch = get_git_branch(script_dir)
    path_str = str(script_dir)

    # Truncate path if needed
    if len(path_str) > inner - 2:
        path_str = '..' + path_str[-(inner - 4):]
    path_line = f'│ {path_str:<{inner - 2}} │'
    branch_line = f'│ {branch:<{inner - 2}} │' if branch else None

    art = r'''metis'''
    box = f"┌{'─' * inner}┐" + '\n' + path_line
    if branch_line:
        box += '\n' + branch_line
    box += '\n' + f"└{'─' * inner}┘"
    banner = art + '\n\n' + box
    m.set_banner(banner)

    m()
