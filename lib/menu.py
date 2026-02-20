#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ooroogi@gmail.com
# https://github.com/ooroogi/metis

import os
import sys
from colorama import Fore, Back, Style, init

def _setup_windows_console():
    """Enable UTF-8, VT processing, and proper font on Windows console."""
    if sys.platform != 'win32':
        return
    try:
        import ctypes
        from ctypes import wintypes, Structure, sizeof, byref

        kernel32 = ctypes.windll.kernel32
        # Enable ANSI escape sequences
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        # UTF-8 codepage
        kernel32.SetConsoleOutputCP(65001)
        kernel32.SetConsoleCP(65001)

        # Set console font to Consolas (raster fonts break unicode widths)
        class CONSOLE_FONT_INFOEX(Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("nFont", wintypes.DWORD),
                ("dwFontSize", wintypes._COORD),
                ("FontFamily", wintypes.UINT),
                ("FontWeight", wintypes.UINT),
                ("FaceName", ctypes.c_wchar * 32),
            ]

        font = CONSOLE_FONT_INFOEX()
        font.cbSize = sizeof(CONSOLE_FONT_INFOEX)
        font.dwFontSize.Y = 18
        font.FontFamily = 0x36  # FF_MODERN | FIXED_PITCH
        font.FontWeight = 400
        font.FaceName = "Consolas"
        kernel32.SetCurrentConsoleFontEx(
            kernel32.GetStdHandle(-11), False, byref(font))

        # Resize and center console window (cmd/conhost only, skip for Windows Terminal/Warp)
        if not os.environ.get("WT_SESSION") and not os.environ.get("WARP_IS_LOCAL_SHELL_SESSION"):
            os.system("mode con cols=80 lines=40")
            _hwnd = kernel32.GetConsoleWindow()
            if _hwnd:
                user32 = ctypes.windll.user32
                user32.SetProcessDPIAware()
                _sw, _sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
                _r = wintypes.RECT()
                user32.GetWindowRect(_hwnd, byref(_r))
                _cw, _ch = _r.right - _r.left, _r.bottom - _r.top
                user32.SetWindowPos(_hwnd, 0, (_sw - _cw) // 2, (_sh - _ch) // 2, 0, 0, 0x0001)
    except Exception:
        pass

    # Reconfigure Python stdout/stderr to UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

_setup_windows_console()

# Key codes
KEY_TAB = 9
KEY_SHIFT_TAB = 15
KEY_ENTER = 13
KEY_LF = 10
KEY_SPACE = 32
KEY_ESC = 27
KEY_CTRL_C = 3
KEY_UP = 72
KEY_DOWN = 80
KEY_RIGHT = 77
KEY_LEFT = 75
KEY_HOME = 71
KEY_END = 79

# Cross-platform getch implementation
try:
    from msvcrt import getch  # Windows
    def get_key():
        ch = ord(getch())
        if ch == 9:  # Tab
            return KEY_TAB
        return ch
except ImportError:
    def get_key():  # Unix/Linux/macOS
        import tty, termios, select, os
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = os.read(fd, 1).decode('utf-8')
            if ch == '\x1b':  # ESC sequence for arrow keys
                # Use select to check if more bytes are available (with short timeout)
                # Arrow keys send \x1b followed by more bytes immediately
                # Plain ESC key sends only \x1b
                if select.select([fd], [], [], 0.1)[0]:
                    next_ch = os.read(fd, 2).decode('utf-8')
                    if next_ch == '[A':  # Up arrow
                        return KEY_UP
                    elif next_ch == '[B':  # Down arrow
                        return KEY_DOWN
                    elif next_ch == '[C':  # Right arrow
                        return KEY_RIGHT
                    elif next_ch == '[D':  # Left arrow
                        return KEY_LEFT
                    elif next_ch == '[H':  # Home
                        return KEY_HOME
                    elif next_ch == '[F':  # End
                        return KEY_END
                    elif next_ch == '[Z':  # Shift+Tab
                        return KEY_SHIFT_TAB
                    else:
                        return KEY_ESC
                else:
                    # No more bytes available - it's a plain ESC key
                    return KEY_ESC
            elif ch == '\r':
                return KEY_ENTER
            elif ch == '\n':
                return KEY_LF
            elif ch == '\x03':  # Ctrl+C
                return KEY_CTRL_C
            elif ch == '\t':  # Tab
                return KEY_TAB
            else:
                return ord(ch)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

class ECOLORS:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    # Background colors
    BG_GREEN = '\033[42m'
    BG_RED = '\033[41m'

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

        if key_code == KEY_ENTER or key_code == KEY_LF:  # enter
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
        elif multi and key_code == KEY_SPACE:  # space
            selected[curr] = not selected[curr]
        elif key_code == KEY_UP:  # up arrow
            curr = up(curr, lst)
        elif key_code == KEY_DOWN:  # down arrow
            curr = down(curr, lst)
        elif key_code == KEY_HOME:  # home
            curr = 0
        elif key_code == KEY_END:  # end
            curr = len(lst) - 1
        elif key_code == KEY_ESC or key_code == KEY_CTRL_C:  # esc or ctrl+c
            exit()
            # return [] if multi else None
        sys.stdout.write('\x1b[{0}A'.format(len(lst) + 2))

def select(getin):
    return _menu_core(getin, multi=False)

def multi_select(getin):
    return _menu_core(getin, multi=True)

# Global to store the last rendered menu state for popup overlay
_last_menu_render = []
# Global to store the last selected section index
_last_section_index = 0
# Global to store the last selected item index within section
_last_item_index = 0
# Global to store the banner lines (registered separately)
_banner_lines = []

def get_last_menu_render():
    """Get the last rendered menu lines for use as popup background."""
    global _last_menu_render
    return _last_menu_render.copy()

def set_last_menu_render(lines):
    """Set the last rendered menu lines (used for restoring state when going back)."""
    global _last_menu_render
    _last_menu_render = lines.copy() if lines else []

def get_last_section_index():
    """Get the last selected section index."""
    global _last_section_index
    return _last_section_index

def set_last_section_index(idx):
    """Set the last selected section index."""
    global _last_section_index
    _last_section_index = idx

def get_last_item_index():
    """Get the last selected item index."""
    global _last_item_index
    return _last_item_index

def set_last_item_index(idx):
    """Set the last selected item index."""
    global _last_item_index
    _last_item_index = idx

def register_banner(banner: str):
    """Register a banner to be included in menu state.
    The banner will be prepended to menu renders for proper state management.
    """
    global _banner_lines
    if banner:
        _banner_lines = banner.rstrip('\n').split('\n')
    else:
        _banner_lines = []

def get_banner_lines():
    """Get the registered banner lines."""
    global _banner_lines
    return _banner_lines.copy()

def clear_banner():
    """Clear the registered banner."""
    global _banner_lines
    _banner_lines = []

def sectioned_select(sections, multi=False):
    """
    Sectioned menu with Tab navigation between sections.

    Args:
        sections: dict of {section_name: items} where items is dict/list/set
        multi: bool or dict of {section_name: bool} for per-section multi mode

    Returns:
        Selected item(s) from the chosen section

    Controls:
        Tab / Right Arrow: Next section
        Shift+Tab / Left Arrow: Previous section
        Up/Down Arrow: Navigate items in current section
        Enter: Select item
        Space: Toggle selection (multi mode)
        Esc/Ctrl+C: Exit
    """
    global _last_menu_render
    global _last_section_index
    global _last_item_index

    if not sections:
        return [] if multi else None

    section_names = list(sections.keys())
    _multi_map = multi if isinstance(multi, dict) else None
    _any_multi = any(_multi_map.values()) if _multi_map else bool(multi)

    def is_multi(section_idx=None):
        if _multi_map:
            return _multi_map.get(section_names[section_idx if section_idx is not None else curr_section], False)
        return bool(multi)

    # Restore last section, but clamp to valid range
    curr_section = min(_last_section_index, len(section_names) - 1)
    selected = {}  # {section_idx: [bool, ...]} for multi mode
    prev_total_lines = 0  # Track previously drawn lines for clearing leftover lines

    def get_current_items():
        items = sections[section_names[curr_section]]
        t = type(items)
        return list(items.keys()) if t is dict else list(items) if t is set else items

    def get_max_width():
        max_item_len = 0
        for sec_items in sections.values():
            t = type(sec_items)
            lst = list(sec_items.keys()) if t is dict else list(sec_items) if t is set else sec_items
            for item in lst:
                if len(str(item)) > max_item_len:
                    max_item_len = len(str(item))
        # Tab width: " name " per tab, " │ " separators, "│ " and " │" borders
        tab_width = sum(len(name) + 2 for name in section_names) + (len(section_names) - 1) * 3 + 4
        # Item width: "│ →·item │" = item + 6, with checkboxes +10
        item_width = max_item_len + (10 if _any_multi else 6)
        # Banner width: align banner box with menu box width
        banner_width = max((len(line.rstrip()) for line in _banner_lines), default=0)
        return max(item_width, tab_width, banner_width)

    def build_tabs_lines(width):
        """Build tab lines as strings instead of printing."""
        lines = []
        # Top border
        lines.append(f"┌{'─' * (width - 2)}┐")
        # Tab bar
        tabs_plain = []
        tabs_colored = []
        for idx, name in enumerate(section_names):
            tab_text = f" {name} "
            tabs_plain.append(tab_text)
            if idx == curr_section:
                tabs_colored.append(f"{Back.LIGHTBLUE_EX}{tab_text}{Style.RESET_ALL}")
            else:
                tabs_colored.append(tab_text)
        line_plain = ' │ '.join(tabs_plain)
        line_colored = ' │ '.join(tabs_colored)
        total_padding = width - len(line_plain) - 4
        left_pad = total_padding // 2
        right_pad = total_padding - left_pad
        lines.append(f"│ {' ' * left_pad}{line_colored}{' ' * right_pad} │")
        lines.append(f"├{'─' * (width - 2)}┤")
        return lines

    def draw_tabs(width):
        for line in build_tabs_lines(width):
            sys.stdout.write(line + '\n')

    def is_separator(item):
        """Check if item is a separator (empty string or special separator key)."""
        s = str(item)
        return s == '' or s.startswith('\x00sep')

    def build_items_lines(items, width):
        """Build item lines as strings instead of printing."""
        lines = []
        inner_width = width - 4  # space for "│ " and " │"
        if not items:
            lines.append(f"│ (empty){' ' * (inner_width - 7)} │")
            return lines

        _cur_multi = is_multi()
        sel_list = selected.get(curr_section, [False] * len(items)) if _cur_multi else None

        for idx, item in enumerate(items):
            if is_separator(item):
                line_len = inner_width - 4
                lines.append(f"│ {'  '}{'─' * line_len}{'  '} │")
                continue

            color = ''
            arrow = '→ ' if idx == curr_item else '  '
            chosen = ''
            if _cur_multi:
                chosen = ' [√] ' if sel_list[idx] else ' [ ] '
                color = ECOLORS.OKGREEN if sel_list[idx] else ''
            if idx == curr_item:
                color = ECOLORS.OKBLUE
            content = f"{arrow}{chosen}{item}"
            padding = ' ' * max(0, inner_width - len(content))
            lines.append(f"│ {color}{content}{Style.RESET_ALL}{padding} │")
        return lines

    def draw_items(items, width):
        lines = build_items_lines(items, width)
        for line in lines:
            sys.stdout.write(line + '\n')
        return len(lines)

    def find_next_selectable(start, direction, items):
        """Find the next non-separator item in the given direction."""
        if not items:
            return start
        count = len(items)
        pos = start
        for _ in range(count):
            pos = (pos + direction) % count
            if not is_separator(items[pos]):
                return pos
        return start  # All items are separators

    def find_first_selectable(items):
        """Find the first non-separator item."""
        for i, item in enumerate(items):
            if not is_separator(item):
                return i
        return 0

    def clear_lines(num_lines, width):
        """Clear extra lines when switching to a section with fewer items."""
        for _ in range(num_lines):
            sys.stdout.write(' ' * width + '\n')

    def get_total_lines(items):
        # top border + tabs line + separator + items + bottom border
        return 3 + max(len(items), 1) + 1

    width = get_max_width()

    # Initialize curr_item - restore last position if valid, otherwise first selectable
    initial_items = get_current_items()
    if _last_item_index < len(initial_items) and not is_separator(initial_items[_last_item_index]):
        curr_item = _last_item_index
    else:
        curr_item = find_first_selectable(initial_items)

    while True:
        items = get_current_items()
        curr_total_lines = get_total_lines(items)

        # Initialize selection list for this section if needed
        if is_multi() and curr_section not in selected:
            selected[curr_section] = [False] * len(items)

        # Build and store menu lines for popup overlay support (including banner)
        menu_lines = []
        menu_lines.extend(build_tabs_lines(width))
        menu_lines.extend(build_items_lines(items, width))
        menu_lines.append(f"└{'─' * (width - 2)}┘")
        # Include banner in saved state for proper popup positioning
        _last_menu_render = _banner_lines + menu_lines

        # Draw the banner (if registered) and menu
        # On first draw, include banner; on redraws (cursor moved up), skip banner
        if prev_total_lines == 0 and _banner_lines:
            for line in _banner_lines:
                sys.stdout.write(line + '\n')
        for line in menu_lines:
            sys.stdout.write(line + '\n')

        # Clear any extra lines from previous section if it was longer
        extra_lines = prev_total_lines - curr_total_lines
        if extra_lines > 0:
            clear_lines(extra_lines, width)
            # Move cursor back up after clearing
            sys.stdout.write('\x1b[{0}A'.format(extra_lines))

        key_code = get_key()

        if key_code == KEY_ENTER or key_code == KEY_LF:
            if not items or is_separator(items[curr_item]):
                sys.stdout.write('\x1b[{0}A'.format(curr_total_lines))
                continue
            if is_multi():
                sel_list = selected.get(curr_section, [])
                res = []
                sec_items = sections[section_names[curr_section]]
                t = type(sec_items)
                for i, sel in enumerate(sel_list):
                    if sel:
                        res.append(items[i] if t is set else sec_items[items[i]] if t is dict else sec_items[i])
                if not res:
                    # Nothing toggled — use current cursor item
                    res.append(items[curr_item] if t is set else sec_items[items[curr_item]] if t is dict else sec_items[curr_item])
                print()
                _last_section_index = curr_section
                _last_item_index = curr_item
                return res
            else:
                print()
                _last_section_index = curr_section  # Save section before returning
                _last_item_index = curr_item  # Save item position before returning
                sec_items = sections[section_names[curr_section]]
                t = type(sec_items)
                if t is dict:
                    return sec_items[items[curr_item]]
                if t is set:
                    return items[curr_item]
                return sec_items[curr_item]
        elif key_code == KEY_TAB or key_code == KEY_RIGHT:
            curr_section = (curr_section + 1) % len(section_names)
            _last_section_index = curr_section  # Save section on change
            _last_item_index = 0  # Reset item position on section change
            new_items = get_current_items()
            curr_item = find_first_selectable(new_items)
        elif key_code == KEY_SHIFT_TAB or key_code == KEY_LEFT:
            curr_section = (curr_section - 1) % len(section_names)
            _last_section_index = curr_section  # Save section on change
            _last_item_index = 0  # Reset item position on section change
            new_items = get_current_items()
            curr_item = find_first_selectable(new_items)
        elif is_multi() and key_code == KEY_SPACE and items and not is_separator(items[curr_item]):
            selected[curr_section][curr_item] = not selected[curr_section][curr_item]
        elif key_code == KEY_UP and items:
            curr_item = find_next_selectable(curr_item, -1, items)
        elif key_code == KEY_DOWN and items:
            curr_item = find_next_selectable(curr_item, 1, items)
        elif key_code == KEY_HOME and items:
            curr_item = find_first_selectable(items)
        elif key_code == KEY_END and items:
            # Find last selectable
            for i in range(len(items) - 1, -1, -1):
                if not is_separator(items[i]):
                    curr_item = i
                    break
        elif key_code == KEY_ESC or key_code == KEY_CTRL_C:
            exit()

        # Move cursor up to redraw
        sys.stdout.write('\x1b[{0}A'.format(curr_total_lines))
        prev_total_lines = curr_total_lines

def restore_menu_with_popup(title, selected_item, items, width=None):
    """
    Restore the main menu display with a popup overlay showing the selected item.
    Used to show visual feedback after command execution.

    Args:
        title: The popup title
        selected_item: The key of the selected item to highlight
        items: The items dict that was shown in the popup
        width: Optional width override
    """
    import re

    def strip_ansi(text):
        return re.sub(r'\x1b\[[0-9;]*m', '', text)

    background_lines = get_last_menu_render()
    if not background_lines:
        return

    t = type(items)
    lst = list(items.keys()) if t is dict else list(items) if t is set else items

    # Find the index of selected item
    curr = 0
    for i, item in enumerate(lst):
        if item == selected_item:
            curr = i
            break

    bg_width = max(len(strip_ansi(line)) for line in background_lines) if background_lines else 40

    # Calculate popup dimensions
    max_item_len = max(len(str(item)) for item in lst)
    title_len = len(title)
    inner_width = max(max_item_len + 4, title_len + 2)

    if width is not None:
        inner_width = width

    max_popup_width = bg_width - 8
    if inner_width > max_popup_width:
        inner_width = max_popup_width

    popup_width = inner_width + 2

    # Box drawing characters
    TL, TR, BL, BR = '┌', '┐', '└', '┘'
    H, V = '─', '│'
    LT, RT = '├', '┤'

    # Colors
    BC = Fore.LIGHTBLUE_EX
    BG = Back.BLACK

    # Build popup lines
    popup_lines = []
    popup_lines.append(f"{BG}{BC}{TL}{H * inner_width}{TR}{Style.RESET_ALL}")

    display_title = title[:inner_width-2] if len(title) > inner_width-2 else title
    title_padding = (inner_width - len(display_title)) // 2
    title_line = ' ' * title_padding + display_title + ' ' * (inner_width - title_padding - len(display_title))
    popup_lines.append(f"{BG}{BC}{V}{Fore.WHITE}{title_line}{BC}{V}{Style.RESET_ALL}")

    popup_lines.append(f"{BG}{BC}{LT}{H * inner_width}{RT}{Style.RESET_ALL}")

    for idx, item in enumerate(lst):
        item_str = str(item)
        max_item_display = inner_width - 4
        if len(item_str) > max_item_display:
            item_str = item_str[:max_item_display-2] + '..'

        if idx == curr:
            arrow = ' › '
            content = f"{arrow}{item_str}"
            content_padded = content + ' ' * (inner_width - len(content))
            popup_lines.append(f"{BG}{BC}{V}{Fore.LIGHTBLUE_EX}{content_padded}{BC}{V}{Style.RESET_ALL}")
        else:
            content = f"   {item_str}"
            content_padded = content + ' ' * (inner_width - len(content))
            popup_lines.append(f"{BG}{BC}{V}{Fore.WHITE}{content_padded}{BC}{V}{Style.RESET_ALL}")

    popup_lines.append(f"{BG}{BC}{BL}{H * inner_width}{BR}{Style.RESET_ALL}")

    # Calculate popup position
    popup_height = len(popup_lines)
    popup_col = max(4, (bg_width - popup_width) // 2 + 22)
    popup_row = max(1, (len(background_lines) - popup_height) // 2)

    # Merge and display
    result = []
    total_needed = popup_row + len(popup_lines)
    bg_copy = background_lines.copy()
    while len(bg_copy) < total_needed:
        bg_copy.append(' ' * bg_width)

    for i in range(len(bg_copy)):
        bg_line = bg_copy[i]
        bg_plain = strip_ansi(bg_line)
        if len(bg_plain) < bg_width:
            bg_plain = bg_plain + ' ' * (bg_width - len(bg_plain))

        is_selected_line = '→' in bg_plain

        popup_idx = i - popup_row
        if 0 <= popup_idx < len(popup_lines):
            popup_line = popup_lines[popup_idx]
            popup_plain_len = len(strip_ansi(popup_line))

            left_bg = bg_plain[:popup_col]
            right_start = popup_col + popup_plain_len
            right_bg = bg_plain[right_start:bg_width]

            if is_selected_line:
                merged = f"{ECOLORS.OKBLUE}{left_bg}{Style.RESET_ALL}{popup_line}{ECOLORS.OKBLUE}{right_bg}{Style.RESET_ALL}"
            else:
                merged = f"{Fore.LIGHTBLACK_EX}{left_bg}{Style.RESET_ALL}{popup_line}{Fore.LIGHTBLACK_EX}{right_bg}{Style.RESET_ALL}"
            result.append(merged)
        else:
            if is_selected_line:
                result.append(bg_line)
            else:
                result.append(f"{Fore.LIGHTBLACK_EX}{bg_plain}{Style.RESET_ALL}")

    # Print the merged display
    for line in result:
        sys.stdout.write(line + '\n')
    sys.stdout.flush()


def calc_popup_width(*item_sets):
    """
    Calculate the minimum width needed to fit all item sets.
    Use this to get a consistent width for multiple related popups.

    Args:
        *item_sets: Variable number of dict/list/set of items

    Returns:
        int: The inner width needed (not including borders)
    """
    max_len = 0
    for items in item_sets:
        t = type(items)
        lst = list(items.keys()) if t is dict else list(items) if t is set else items
        for item in lst:
            if len(str(item)) > max_len:
                max_len = len(str(item))
    return max_len + 4  # +4 for arrow and padding


def popup_select(title, items, background_lines=None, return_key=False, width=None, clear_on_select=False, keep_display=False, stack_display=False, no_restore_on_esc=False, row_offset=0, popup_col=None, initial_index=0):
    """
    Display a popup dialog that overlays on top of existing content.
    The popup is drawn over the background, which is redrawn each frame.

    Args:
        title: The title to display in the popup header
        items: dict {display_label: value} or list of items
        background_lines: list of strings representing the background (auto-detected if None)
        return_key: if True, return the key instead of value (for dict)
        width: optional fixed width for the popup
        clear_on_select: if True, clear the display instead of restoring background after selection
        keep_display: if True, keep the current display (menu+popup) as-is and just move cursor below
        stack_display: if True, save the current display as background for the next popup (stacked selection)
        no_restore_on_esc: if True, don't restore background on ESC (caller will handle cleanup)
        row_offset: additional row offset for popup position (for stacked modals)
        popup_col: absolute column position for popup (if None, auto-calculated)
        initial_index: initial cursor position (for restoring position when going back)

    Returns:
        Selected value (or key if return_key=True), or None if cancelled
    """
    import re

    if not items:
        return None

    t = type(items)
    lst = list(items.keys()) if t is dict else list(items) if t is set else items
    # Use initial_index but clamp to valid range
    curr = min(initial_index, len(lst) - 1) if lst else 0

    def strip_ansi(text):
        """Remove ANSI escape codes from text for length calculation."""
        return re.sub(r'\x1b\[[0-9;]*m', '', text)

    # Use last rendered menu as background if not provided
    if background_lines is None:
        background_lines = get_last_menu_render()
        if not background_lines:
            background_lines = [''] * 10

    # Get the width of the background menu
    bg_width = max(len(strip_ansi(line)) for line in background_lines) if background_lines else 40

    # Calculate popup dimensions - fit within the menu
    max_item_len = max(len(str(item)) for item in lst)
    title_len = len(title)
    inner_width = max(max_item_len + 4, title_len + 2)

    # Apply explicit width if provided
    if width is not None:
        inner_width = width

    # Ensure popup fits within menu (leave 4 chars margin on each side)
    # Skip this constraint when popup_col is specified (popup is outside the menu)
    if popup_col is None:
        max_popup_width = bg_width - 8
        if inner_width > max_popup_width:
            inner_width = max_popup_width

    popup_width = inner_width + 2  # +2 for borders

    # Box drawing characters (single-line for lighter appearance)
    TL, TR, BL, BR = '┌', '┐', '└', '┘'
    H, V = '─', '│'
    LT, RT = '├', '┤'

    def build_popup_lines():
        """Build the popup box lines."""
        lines = []

        # Colors
        BC = Fore.LIGHTBLUE_EX  # Border color
        BG = Back.BLACK  # Dark background for contrast

        # Top border
        lines.append(f"{BG}{BC}{TL}{H * inner_width}{TR}{Style.RESET_ALL}")

        # Title bar (truncate if needed, no bold)
        display_title = title[:inner_width-2] if len(title) > inner_width-2 else title
        title_padding = (inner_width - len(display_title)) // 2
        title_line = ' ' * title_padding + display_title + ' ' * (inner_width - title_padding - len(display_title))
        lines.append(f"{BG}{BC}{V}{Fore.WHITE}{title_line}{BC}{V}{Style.RESET_ALL}")

        # Separator
        lines.append(f"{BG}{BC}{LT}{H * inner_width}{RT}{Style.RESET_ALL}")

        # Items
        for idx, item in enumerate(lst):
            item_str = str(item)
            # Truncate item if too long
            max_item_display = inner_width - 4  # " › " or "   " takes 3, plus 1 padding
            if len(item_str) > max_item_display:
                item_str = item_str[:max_item_display-2] + '..'

            if idx == curr:
                arrow = ' › '
                content = f"{arrow}{item_str}"
                content_padded = content + ' ' * (inner_width - len(content))
                lines.append(f"{BG}{BC}{V}{Fore.LIGHTBLUE_EX}{content_padded}{BC}{V}{Style.RESET_ALL}")
            else:
                content = f"   {item_str}"
                content_padded = content + ' ' * (inner_width - len(content))
                lines.append(f"{BG}{BC}{V}{Fore.WHITE}{content_padded}{BC}{V}{Style.RESET_ALL}")

        # Bottom border
        lines.append(f"{BG}{BC}{BL}{H * inner_width}{BR}{Style.RESET_ALL}")

        return lines

    def merge_popup_with_background(bg_lines, popup_lines, popup_row, popup_col):
        """Merge popup on top of background, creating the overlay effect."""
        result = []

        # Ensure we have enough background lines
        total_needed = popup_row + len(popup_lines)
        while len(bg_lines) < total_needed:
            bg_lines.append(' ' * bg_width)

        for i in range(len(bg_lines)):
            bg_line = bg_lines[i]
            bg_plain = strip_ansi(bg_line)
            # Pad to bg_width
            if len(bg_plain) < bg_width:
                bg_plain = bg_plain + ' ' * (bg_width - len(bg_plain))

            # Check if this line contains the selected item (has >arrow)
            is_selected_line = '→' in bg_plain

            popup_idx = i - popup_row
            if 0 <= popup_idx < len(popup_lines):
                # This line has popup content - merge it
                popup_line = popup_lines[popup_idx]
                popup_plain_len = len(strip_ansi(popup_line))

                # Get left portion of background
                left_bg = bg_plain[:popup_col]

                # Get right portion of background
                right_start = popup_col + popup_plain_len
                right_bg = bg_plain[right_start:bg_width]

                # Background portions are always dimmed
                # Each popup handles its own selection highlighting internally
                left_colored = f"{Fore.LIGHTBLACK_EX}{left_bg}{Style.RESET_ALL}"
                right_colored = f"{Fore.LIGHTBLACK_EX}{right_bg}{Style.RESET_ALL}"

                # Popup line already has its own coloring (selected item is light blue)
                merged = f"{left_colored}{popup_line}{right_colored}"
                result.append(merged)
            else:
                # No popup on this line - dim everything in background
                # Only the current (topmost) popup should show colors
                result.append(f"{Fore.LIGHTBLACK_EX}{bg_plain}{Style.RESET_ALL}")

        return result

    # Calculate popup position
    popup_lines_built = build_popup_lines()
    popup_height = len(popup_lines_built)
    # Use absolute position if provided, otherwise center + shift right
    if popup_col is None:
        popup_col = max(4, (bg_width - popup_width) // 2 + 22)

    # Position popup to overlap with middle of MENU portion (not banner)
    # Banner is at the top, so offset popup_row by banner height
    banner_height = len(_banner_lines)
    menu_height = len(background_lines) - banner_height
    popup_row = banner_height + max(1, (menu_height - popup_height) // 2) + row_offset

    num_bg_lines = len(background_lines)

    # Move cursor up to overwrite the menu area
    # +1 accounts for the newline from sectioned_select's print() or previous popup's trailing newline
    sys.stdout.write(f'\x1b[{num_bg_lines + 1}A')

    first_draw = True
    drawn_lines = 0

    while True:
        popup_lines_built = build_popup_lines()

        # Merge popup with background
        display = merge_popup_with_background(
            background_lines.copy(),
            popup_lines_built,
            popup_row,
            popup_col
        )

        # Move cursor up if redrawing
        if not first_draw:
            sys.stdout.write(f'\x1b[{drawn_lines}A')
        first_draw = False

        # Draw merged content
        for line in display:
            sys.stdout.write('\x1b[2K')  # Clear line
            sys.stdout.write(line + '\n')
        sys.stdout.flush()

        drawn_lines = len(display)

        # Get input
        key_code = get_key()

        if key_code == KEY_ENTER or key_code == KEY_LF:
            if keep_display or stack_display:
                # Keep display as-is, just add newline to position cursor below
                sys.stdout.write('\n')
                sys.stdout.flush()
                if stack_display:
                    # Save the current merged display as background for next popup
                    global _last_menu_render
                    _last_menu_render = display.copy()
            elif clear_on_select:
                # Clear all lines instead of restoring background
                sys.stdout.write(f'\x1b[{drawn_lines}A')
                for _ in range(drawn_lines):
                    sys.stdout.write('\x1b[2K\n')
                # Move cursor back to top
                sys.stdout.write(f'\x1b[{drawn_lines}A')
                sys.stdout.flush()
            else:
                # Restore background (main menu) so it stays visible
                sys.stdout.write(f'\x1b[{drawn_lines}A')
                for line in background_lines:
                    sys.stdout.write('\x1b[2K' + line + '\n')
                # Clear any extra lines if popup extended beyond background
                extra = drawn_lines - num_bg_lines
                if extra > 0:
                    for _ in range(extra):
                        sys.stdout.write('\x1b[2K\n')
                    # Move cursor back up so it's just below the background
                    sys.stdout.write(f'\x1b[{extra}A')
                # Add newline to match sectioned_select behavior (for +1 offset if another popup follows)
                sys.stdout.write('\n')
                sys.stdout.flush()

            if return_key:
                return lst[curr]
            if t is dict:
                return items[lst[curr]]
            return lst[curr]

        elif key_code == KEY_UP:
            curr = (curr - 1) % len(lst)

        elif key_code == KEY_DOWN:
            curr = (curr + 1) % len(lst)

        elif key_code == KEY_HOME:
            curr = 0

        elif key_code == KEY_END:
            curr = len(lst) - 1

        elif key_code == KEY_ESC or key_code == KEY_CTRL_C:
            if no_restore_on_esc:
                # Caller will handle cleanup
                return None
            # Move cursor up and restore background
            sys.stdout.write(f'\x1b[{drawn_lines}A')
            for line in background_lines:
                sys.stdout.write('\x1b[2K' + line + '\n')
            # Clear any extra lines if popup extended beyond background
            extra = drawn_lines - len(background_lines)
            for _ in range(extra):
                sys.stdout.write('\x1b[2K\n')
            # Move cursor back to bottom of background for next popup
            if extra > 0:
                sys.stdout.write(f'\x1b[{extra}A')
            # Add newline to position cursor below the restored display
            sys.stdout.write('\n')
            sys.stdout.flush()
            return None


init()