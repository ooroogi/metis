#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ooroogi@gmail.com
# https://github.com/ooroogi/metis

import time
from typing import Any
from .menu import select, multi_select, sectioned_select, ECOLORS, Style, popup_select, get_last_menu_render, set_last_menu_render, register_banner, get_banner_lines, get_last_section_index
import os, sys
import subprocess


def run_shell_command(cmd: str) -> int:
    """Run a shell command using bash on Windows/MSYS, os.system elsewhere."""
    if sys.platform == 'win32':
        # Use bash explicitly on Windows (Git Bash/MSYS)
        import shutil
        git_bash = shutil.which('bash')
        if git_bash is None:
            git_bash = 'bash'
        return subprocess.call([git_bash, '-c', cmd])
    else:
        return os.system(cmd)


# Special return code to indicate task was cancelled (skip logging)
TASK_CANCELLED = -999

def _format_duration(seconds: float) -> str:
    """Format duration in a human-readable way."""
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {mins}m {secs:.0f}s"


def _print_table(logs: list):
    """Print logs as a formatted table.

    logs: list of tuples (section, title, status, duration, is_success, selections)
    """
    if not logs:
        return

    # Build display titles (with selections appended if present)
    display_titles = []
    for log in logs:
        title = log[1]
        selections = log[5] if len(log) > 5 and log[5] else ''
        if selections:
            display_titles.append(f"{title} - {selections}")
        else:
            display_titles.append(title)

    # Calculate column widths
    section_width = max(len(log[0]) for log in logs)
    section_width = max(section_width, 7)  # minimum "Section"
    task_width = max(len(t) for t in display_titles)
    task_width = max(task_width, 4)  # minimum "Task"
    status_width = 6  # "Status" header
    duration_width = max(len(log[3]) for log in logs)
    duration_width = max(duration_width, 8)  # minimum "Duration"

    # Table characters
    tl, tr, bl, br = '┌', '┐', '└', '┘'
    h, v = '─', '│'
    lm, rm, tm, bm, cross = '├', '┤', '┬', '┴', '┼'

    # Column widths with padding
    c0 = section_width + 2
    c1 = task_width + 2
    c2 = status_width + 2
    c3 = duration_width + 2

    # Print table
    print()
    # Top border
    print(f"{tl}{h * c0}{tm}{h * c1}{tm}{h * c2}{tm}{h * c3}{tr}")
    # Header
    print(f"{v} {'Section':<{section_width}} {v} {'Task':<{task_width}} {v} {'Status':<{status_width}} {v} {'Duration':>{duration_width}} {v}")
    # Header separator
    print(f"{lm}{h * c0}{cross}{h * c1}{cross}{h * c2}{cross}{h * c3}{rm}")
    # Data rows — group by section, show divider between every row
    for i, log in enumerate(logs):
        section, _, status, duration, is_success = log[:5]
        display_title = display_titles[i]
        bg_color = ECOLORS.BG_GREEN if is_success else ECOLORS.BG_RED
        status_box = f"  {bg_color}  {Style.RESET_ALL}  "  # 2 spaces + 2 colored chars + 2 spaces = 6 chars
        # Show section name only on first row of each group
        prev_section = logs[i - 1][0] if i > 0 else None
        section_label = section if section != prev_section else ''
        print(f"{v} {section_label:<{section_width}} {v} {display_title:<{task_width}} {v} {status_box} {v} {duration:>{duration_width}} {v}")
        # Row divider (except after last row)
        if i < len(logs) - 1:
            next_section = logs[i + 1][0]
            if section != next_section:
                # Section boundary — full divider
                print(f"{lm}{h * c0}{cross}{h * c1}{cross}{h * c2}{cross}{h * c3}{rm}")
            else:
                # Same section — skip section column divider
                print(f"{v} {' ' * section_width} {lm}{h * c1}{cross}{h * c2}{cross}{h * c3}{rm}")
    # Bottom border
    print(f"{bl}{h * c0}{bm}{h * c1}{bm}{h * c2}{bm}{h * c3}{br}")
    print()

class Task:
    title = ''
    cmd = ''
    param = None
    stop_on_error = True
    tm = None
    section = ''

    def __init__(self, title, cmd, param=None, stop_on_error=True):
        self.title = title
        self.cmd = cmd
        self.param = param
        self.stop_on_error = stop_on_error
        self.section = ''

    def set_tm(self, tm):
        if self.tm is not None:
            exit(1)
        self.tm = tm
        if len(self.title) > self.tm.title_max_length:
            self.tm.title_max_length = len(self.title)

    def __call__(self, **kwargs):
        if self.stop_on_error and self.tm.is_error_occurred:
            return
        start = time.perf_counter()
        res = 0
        if isinstance(self.cmd, str):
            res = run_shell_command(self.cmd)
        else:
            res = self.cmd(**kwargs)

        # If task was cancelled (e.g., user pressed Esc in popup), skip logging
        if res == TASK_CANCELLED:
            return TASK_CANCELLED

        took = time.perf_counter() - start
        msg = ''
        if res != 0:
            if self.stop_on_error:
                self.tm.is_error_occurred = True

        # Get selections from Modal if applicable
        selections = ''
        if isinstance(self.cmd, Modal) and self.cmd.last_selections:
            selections = ' / '.join(str(v) for v in self.cmd.last_selections.values())

        self.tm.logs.append((self.section, self.title, msg, _format_duration(took), res == 0, selections))
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
        if self.tm is not None:
            exit(1)
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
    persistent = False
    _rebuild_fn = None
    banner = None

    def __init__(self):
        self.list = {}
        self.logs = []
        self.title_max_length = 0
        self.is_error_occurred = False
        self.banner = None
        self.persistent = False
        self._rebuild_fn = None

    def set_banner(self, banner: str):
        """Set a banner to display before each menu."""
        self.banner = banner
        # Register banner with menu system for proper state management
        register_banner(banner)
        return self

    def add(self, task):
        self.list[str(task)] = task
        task.set_tm(self)

    def set_only_once(self):
        self.only_once = True

    def set_persistent(self, rebuild_fn=None):
        """Keep UI alive after selection. rebuild_fn is called before each redraw to refresh sections/banner."""
        self.persistent = True
        self._rebuild_fn = rebuild_fn

    def run_tasks(self, select_func, **kwargs):
        res = 0
        while True:
            sys.stdout.write(Style.RESET_ALL)
            self.logs = []
            self.is_error_occurred = False

            # Banner is drawn by sectioned_select (registered via set_banner)
            tasks = select_func(self.list)
            if not tasks or (isinstance(tasks, list) and len(tasks) == 0):
                # In persistent mode, empty result means on_submit handled it — rebuild and continue
                if self.persistent:
                    if self._rebuild_fn:
                        self._rebuild_fn()
                    sys.stdout.write('\x1b[H\x1b[2J\x1b[3J')
                    sys.stdout.flush()
                    continue
                break

            if not isinstance(tasks, list):
                tasks = [tasks]

            start = time.perf_counter()

            task_cancelled = False
            for task in tasks:
                res = task(**kwargs)
                if res == TASK_CANCELLED:
                    task_cancelled = True
                    break  # User cancelled, go back to menu
                if res != 0:
                    if self.logs:
                        _print_table(self.logs)
                    return res

            # Only print results table if task wasn't cancelled (skip in persistent mode)
            if not task_cancelled and self.logs and not self.persistent:
                _print_table(self.logs)

            # Only exit if only_once is set AND task completed (not cancelled)
            if self.only_once and not task_cancelled:
                break

            # Persistent mode: rebuild and clear screen for fresh redraw
            if self.persistent and not task_cancelled:
                if self._rebuild_fn:
                    self._rebuild_fn()
                sys.stdout.write('\x1b[H\x1b[2J\x1b[3J')
                sys.stdout.flush()

        return res

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        print('task manager call')

class SingleTaskManager(TaskManager):
    def __init__(self):
        super().__init__()

    def __call__(self, **kwargs):
        return self.run_tasks(select, **kwargs)

class MultiTaskManager(TaskManager):
    title = ''
    is_expanded = False
    chosen = []

    def __init__(self, title=''):
        super().__init__()
        self.title = title

    def __call__(self, **kwargs):
        return self.run_tasks(multi_select, **kwargs)

    def expand(self):
        if not self.is_expanded:
            self.chosen = multi_select(self.list)
        else:
            self.is_expanded = True
        return self.chosen

    def set_tm(self, tm):
        pass

class Section:
    """
    A section that groups related tasks together.

    Usage:
        build = Section('Build')
        build.add(Task('cargo check', cargo_check))
        build.add(Task('cargo build', cargo_build))

        m = SectionedTaskManager()
        m.add_section(build)
    """
    def __init__(self, name: str, multi: bool = False, on_submit=None):
        self.name = name
        self.multi = multi
        self.on_submit = on_submit  # callback(selected_tasks) for multi sections
        self.tasks = {}  # {task_title: Task}
        self._separator_count = 0

    def add(self, task):
        """Add a task to this section. Returns self for chaining."""
        task.section = self.name
        key = str(task)
        # Handle separators (empty title) with unique keys
        if key == '':
            key = f'\x00sep{self._separator_count}'  # Use null char prefix to avoid collision
            self._separator_count += 1
        self.tasks[key] = task
        return self

    def splitter(self):
        """Add a visual separator line. Returns self for chaining."""
        key = f'\x00sep{self._separator_count}'
        self._separator_count += 1
        self.tasks[key] = None
        return self

    def __str__(self):
        return self.name

    def __len__(self):
        return len(self.tasks)


class Modal:
    """
    A multi-step popup selection modal.

    Usage:
        modal = Modal('Server Control')
        modal.add_step('Target', {'all': 'all', 'instances': 'instances'})
        modal.add_step('Action', {'start': 'start', 'stop': 'stop'})
        modal.set_command(lambda selections: f'./stress.sh {selections["Action"]} {selections["Target"]}')

        # Use with Task
        stress.add(Task('Server', modal))
    """

    def __init__(self, name: str, min_width: int = None):
        self.name = name
        self.steps = []  # List of (title, items) tuples
        self._command = None  # Command template or callable
        self.last_selections = {}  # Store selections after completion
        self.min_width = min_width

    def add_step(self, title: str, items: dict) -> 'Modal':
        """Add a selection step. Returns self for chaining."""
        self.steps.append((title, items, False))  # (title, items, is_dynamic)
        return self

    def add_dynamic_step(self, title: str, items_fn: callable) -> 'Modal':
        """Add a dynamic selection step where items depend on previous selections.
        items_fn: callable(selections: dict) -> dict
        Returns self for chaining.
        """
        self.steps.append((title, items_fn, True))  # (title, items_fn, is_dynamic)
        return self

    def set_command(self, cmd) -> 'Modal':
        """Set the command to execute after all selections.
        cmd can be:
        - A string with {StepTitle} placeholders
        - A callable(selections: dict) -> str|int
        Returns self for chaining.
        """
        self._command = cmd
        return self

    def __call__(self, **kwargs) -> int:
        """Execute the modal flow. Handles state management internally."""
        if not self.steps:
            return 0

        import re
        def strip_ansi(text):
            return re.sub(r'\x1b\[[0-9;]*m', '', text)

        def calc_popup_width(title, items):
            t = type(items)
            lst = list(items.keys()) if t is dict else list(items) if t is set else items
            max_item_len = max(len(str(item)) for item in lst)
            title_len = len(title)
            inner_width = max(max_item_len + 4, title_len + 2)
            if self.min_width is not None:
                inner_width = max(inner_width, self.min_width)
            return inner_width + 2  # +2 for borders

        # Save original menu state for ESC handling
        original_menu = get_last_menu_render()
        original_bg_width = max(len(strip_ansi(line)) for line in original_menu) if original_menu else 40

        # Track background states for each step (for going back)
        # backgrounds[i] = background to use for step i
        backgrounds = [original_menu]

        # Track cursor positions for each step (for restoring when going back)
        # cursor_positions[i] = selected index for step i
        cursor_positions = [0] * len(self.steps)

        # Track absolute right edge of each popup (for calculating next popup position)
        # popup_right_edges[i] = absolute column of popup i's right edge
        popup_right_edges = []

        selections = {}  # {step_title: selected_value}
        step_index = 0

        while step_index < len(self.steps):
            title, items_or_fn, is_dynamic = self.steps[step_index]
            items = items_or_fn(selections) if is_dynamic else items_or_fn
            popup_width = calc_popup_width(title, items)

            # Calculate absolute column position (share 2 chars with previous pane's right border)
            if step_index == 0:
                # First popup: share 2 chars with main menu's right border
                popup_col = original_bg_width - 2
            else:
                # Subsequent popups: share 2 chars with previous popup's right border
                popup_col = popup_right_edges[step_index - 1] - 2

            # Track this popup's right edge (for next popup)
            if step_index >= len(popup_right_edges):
                popup_right_edges.append(popup_col + popup_width)

            row_offset = step_index

            is_first_step = (step_index == 0)
            is_last_step = (step_index == len(self.steps) - 1)

            # Set the background for this step
            set_last_menu_render(backgrounds[step_index])

            selected_key = popup_select(
                title,
                items,
                return_key=True,
                width=self.min_width,
                stack_display=not is_last_step,  # Stack display for all but last
                keep_display=is_last_step,  # Keep display on last step
                no_restore_on_esc=True,  # We handle ESC ourselves
                row_offset=row_offset,
                popup_col=popup_col,
                initial_index=cursor_positions[step_index],  # Restore cursor position
            )

            if selected_key is None:
                # ESC pressed
                if is_first_step:
                    # ESC on first step - clear screen including scrollback and return cancelled
                    sys.stdout.write('\x1b[H\x1b[2J\x1b[3J')
                    sys.stdout.flush()
                    return TASK_CANCELLED
                else:
                    # ESC on subsequent step - go back to previous step
                    # Calculate actual display height (background may have been extended by popup)
                    bg_height = len(backgrounds[step_index])
                    banner_height = len(get_banner_lines())
                    menu_height = bg_height - banner_height
                    popup_height = 4 + len(items)  # title + separator + top/bottom borders + items
                    popup_row = banner_height + max(1, (menu_height - popup_height) // 2) + row_offset
                    current_height = max(bg_height, popup_row + popup_height)

                    step_index -= 1
                    # Remove the selection for the step we're going back to
                    prev_title = self.steps[step_index][0]
                    if prev_title in selections:
                        del selections[prev_title]
                    # Trim backgrounds list and popup_right_edges
                    while len(backgrounds) > step_index + 1:
                        backgrounds.pop()
                    while len(popup_right_edges) > step_index:
                        popup_right_edges.pop()
                    # Move cursor up by current display height to get back to menu start
                    bg = backgrounds[step_index]
                    sys.stdout.write(f'\x1b[{current_height}A')
                    # Clear from cursor down and redraw
                    sys.stdout.write('\x1b[J')
                    for line in bg:
                        sys.stdout.write(line + '\n')
                    sys.stdout.flush()
                    continue

            # Store selection and cursor position
            selections[title] = items[selected_key]
            # Save cursor position (find index of selected key)
            item_keys = list(items.keys())
            cursor_positions[step_index] = item_keys.index(selected_key) if selected_key in item_keys else 0

            # Save the merged display as background for next step (if not last)
            if not is_last_step:
                # popup_select with stack_display=True saved the merged display
                backgrounds.append(get_last_menu_render())

            step_index += 1

        # All steps completed - save selections for result table
        self.last_selections = selections.copy()

        # Execute command
        if self._command is None:
            return 0

        if callable(self._command):
            result = self._command(selections)
            if isinstance(result, str):
                return run_shell_command(result)
            return result if result is not None else 0
        else:
            # String template with {StepTitle} placeholders
            cmd = self._command
            for title, value in selections.items():
                cmd = cmd.replace('{' + title + '}', str(value))
            return run_shell_command(cmd)

    def __str__(self):
        return self.name


class SectionedTaskManager(TaskManager):
    """
    Task manager with tabbed sections. Use Tab to switch between sections.

    Usage:
        m = SectionedTaskManager()

        build = Section('Build')
        build.add(Task('cargo check', cargo_check))
        m.add_section(build)

        docker = Section('Docker')
        docker.add(Task('renew docker', sol_renew_docker))
        m.add_section(docker)

        m()
    """
    _sections = []  # List[Section]

    def __init__(self):
        super().__init__()
        self._sections = []

    def add_section(self, section: Section):
        """Add a Section object to the manager."""
        self._sections.append(section)
        for task in section.tasks.values():
            if task is None:  # Skip separators
                continue
            task.set_tm(self)
            self.list[str(task)] = task
        return self

    def clear_sections(self):
        """Remove all sections and tasks. Used with set_persistent() to rebuild UI."""
        self._sections = []
        self.list = {}

    def _build_sections_dict(self):
        """Build sections dict for sectioned_select."""
        return {sec.name: sec.tasks for sec in self._sections}

    def _build_multi_map(self):
        """Build per-section multi mode map."""
        return {sec.name: sec.multi for sec in self._sections}

    def get_menu_width(self):
        """Calculate menu width based on sections (excluding banner)."""
        sections = self._build_sections_dict()
        section_names = list(sections.keys())
        multi_map = self._build_multi_map()
        any_multi = any(multi_map.values())

        max_item_len = 0
        for sec_items in sections.values():
            t = type(sec_items)
            lst = list(sec_items.keys()) if t is dict else list(sec_items) if t is set else sec_items
            for item in lst:
                if len(str(item)) > max_item_len:
                    max_item_len = len(str(item))

        tab_width = sum(len(name) + 2 for name in section_names) + (len(section_names) - 1) * 3 + 4
        item_width = max_item_len + (10 if any_multi else 6)
        return max(item_width, tab_width)

    def __call__(self, **kwargs):
        def sectioned_selector(flat_list):
            result = sectioned_select(self._build_sections_dict(), multi=self._build_multi_map())
            # If multi-select returned a list and the section has on_submit, call it
            if isinstance(result, list):
                sec = self._sections[get_last_section_index()]
                if sec.on_submit:
                    sec.on_submit(result)
                    return []  # Signal no individual tasks to run
            return result

        return self.run_tasks(sectioned_selector, **kwargs)


class SectionedMultiTaskManager(TaskManager):
    """
    Task manager with tabbed sections and multi-select support.
    """
    _sections = []

    def __init__(self):
        super().__init__()
        self._sections = []

    def add_section(self, section: Section):
        """Add a Section object to the manager."""
        self._sections.append(section)
        for task in section.tasks.values():
            if task is None:  # Skip separators
                continue
            task.set_tm(self)
            self.list[str(task)] = task
        return self

    def _build_sections_dict(self):
        return {sec.name: sec.tasks for sec in self._sections}

    def __call__(self, **kwargs):
        def sectioned_selector(flat_list):
            return sectioned_select(self._build_sections_dict(), multi=True)
        return self.run_tasks(sectioned_selector, **kwargs)