import sys
from datetime import datetime
from rich.console import Console

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

class Logger:
    def __init__(self):
        self.__console = Console()

    def info(self, log, exit=0):
        now = datetime.now().strftime("%H:%M:%S")
        log_str = f"[bold green][{now}][/] [bold yellow][VizX Core][/] [deep_sky_blue1]INFO:[/] [bold bright_white]{log}[/]"
        self.__console.print(log_str)
        if exit == 1:
            sys.exit()

    def error(self, log, exit=0):
        now = datetime.now().strftime("%H:%M:%S")
        log_str = f"[bold green][{now}][/] [bold yellow][VizX Core][/] [bold red]ERROR:[/] [bold bright_white]{log}[/]"
        self.__console.print(log_str)
        if exit == 1:
            sys.exit()

    def warning(self, log, exit=0):
        now = datetime.now().strftime("%H:%M:%S")
        log_str = f"[bold green][{now}][/] [bold yellow][VizX Core][/] [bold red]WARNING:[/] [bold bright_white]{log}[/]"
        self.__console.print(log_str)
        if exit == 1:
            sys.exit()

logger = Logger()