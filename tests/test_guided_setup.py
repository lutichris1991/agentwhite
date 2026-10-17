import unittest
from pathlib import Path

from agentwhite.setup_prompt import SETUP_PROMPT_HTML


class GuidedSetupTests(unittest.TestCase):
    def test_first_run_prompt_has_one_button_update_flow(self):
        self.assertIn("AGENT WHITE · TOOL SETUP", SETUP_PROMPT_HTML)
        self.assertIn("Update Tools", SETUP_PROMPT_HTML)
        self.assertIn("Not now", SETUP_PROMPT_HTML)
        self.assertIn("/api/tools", SETUP_PROMPT_HTML)
        self.assertIn("/api/tool-setup", SETUP_PROMPT_HTML)
        self.assertNotIn("/api/tool-setup-all", SETUP_PROMPT_HTML)
        self.assertNotIn("/api/tool-setup-status", SETUP_PROMPT_HTML)

    def test_windows_launchers_use_guided_app_entrypoint(self):
        root = Path(__file__).resolve().parents[1]
        installer = (root / "install_windows.ps1").read_text(encoding="utf-8")
        batch = (root / "run_agentwhite.bat").read_text(encoding="utf-8")
        self.assertIn("app.py", installer)
        self.assertIn("app.py", batch)
        self.assertIn("first launch", installer.lower())


if __name__ == "__main__":
    unittest.main()
