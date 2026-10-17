from __future__ import annotations

from . import server
from .mode_ui import enable_mode_switch
from .onboarding import enable_first_run_mode_prompt
from .setup_prompt import SETUP_PROMPT_HTML


def prepare_ui() -> None:
    if SETUP_PROMPT_HTML not in server.HTML:
        server.HTML = server.HTML.replace("</body>", SETUP_PROMPT_HTML + "</body>")
    enable_first_run_mode_prompt()
    enable_mode_switch()


def main() -> None:
    prepare_ui()
    server.main()
