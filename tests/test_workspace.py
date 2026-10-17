import unittest

from agentwhite.server import AgentWhiteHandler
from agentwhite.workspace_ui import WORKSPACE_HTML


class WorkspaceSmokeTests(unittest.TestCase):
    def test_server_reports_v03(self):
        self.assertEqual(AgentWhiteHandler.server_version, "AgentWhite/0.3")

    def test_workspace_ui_contains_persistent_navigation(self):
        self.assertIn("TARGET WORKSPACE", WORKSPACE_HTML)
        self.assertIn("SAVED ACCESS", WORKSPACE_HTML)
        self.assertIn("history", WORKSPACE_HTML)
        self.assertIn("Run This Test", WORKSPACE_HTML)


if __name__ == "__main__":
    unittest.main()
