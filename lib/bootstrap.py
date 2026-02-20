import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
PARTS_DIR = ROOT_DIR / "parts"
INIT_MARKER = PARTS_DIR / ".init"
VENV_DIR = ROOT_DIR / ".venv"
VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe" if sys.platform == "win32" else VENV_DIR / "bin" / "python"


def _to_posix(p: Path) -> str:
    """Convert a Windows path to POSIX format for bash (C:\\Users\\... -> /c/Users/...)."""
    s = p.as_posix()
    if len(s) >= 2 and s[1] == ":":
        return "/" + s[0].lower() + s[2:]
    return s


def _register_aliases():
    """Register metis, admin, puffin aliases in bashrc/zshrc using .venv python."""
    venv_python = _to_posix(VENV_PYTHON)
    root = _to_posix(ROOT_DIR)
    aliases = {
        "metis": f"{venv_python} {root}/metis.py",
        "admin": f"{venv_python} {root}/admin.py",
        "puffin": f"{venv_python} {root}/puffin.py",
    }

    for rc in [Path.home() / ".bashrc", Path.home() / ".zshrc"]:
        if not rc.exists():
            continue
        lines = rc.read_text().splitlines()
        # Remove existing aliases
        lines = [l for l in lines if not any(f"alias {name}=" in l for name in aliases)]
        # Add new aliases
        for name, cmd in aliases.items():
            lines.append(f"alias {name}='{cmd}'")
        rc.write_text("\n".join(lines) + "\n")

    print("  Aliases registered (.bashrc/.zshrc)")


def _register_windows_path():
    """Register parts/ directory in Windows user PATH."""
    parts_win = str(PARTS_DIR).replace("/", "\\")
    ps_script = (
        f"$d = '{parts_win}';"
        f"$p = [Environment]::GetEnvironmentVariable('Path', 'User');"
        f"$dirs = if ($p) {{ $p.Split(';') | Where-Object {{ $_ -ne '' -and $_ -notlike '*metis*' }} }} else {{ @() }};"
        f"if ($dirs -contains $d) {{ Write-Host 'PATH exists:' $d }}"
        f"else {{ $dirs += $d; [Environment]::SetEnvironmentVariable('Path', ($dirs -join ';'), 'User'); Write-Host 'PATH added:' $d }}"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_script])
    print("  PATH registered")


def ensure_init():
    """Create .venv, install deps, and register aliases/PATH on first run. Write parts/.init marker on success."""
    if INIT_MARKER.exists():
        return

    print("=== First run: setting up environment ===\n")

    # 1) Create .venv and install colorama
    if not VENV_PYTHON.exists():
        print("  Creating .venv...")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])

    pip = VENV_DIR / ("Scripts" if sys.platform == "win32" else "bin") / "pip"
    print("  Installing colorama...")
    subprocess.check_call([str(pip), "install", "colorama"])

    # 2) Register aliases / PATH
    _register_aliases()
    if sys.platform == "win32":
        _register_windows_path()

    # 3) Write marker
    INIT_MARKER.touch()
    if sys.platform != "win32":
        print("\n  Setup complete. Run: source ~/.bashrc  (or open a new terminal)\n")
    else:
        print("\n  Setup complete. Open a new terminal to use the 'metis' command.\n")
    sys.exit(0)
