import unittest
from unittest.mock import patch

from agentwhite.server import AgentWhiteHandler
from agentwhite.tool_registry import POLICY_DEFAULTS, TOOL_CATALOG, list_tools
from agentwhite.tools_ui import TOOLS_HTML


class ToolRegistryTests(unittest.TestCase):
    def test_catalog_has_broad_protocol_coverage(self):
        self.assertGreaterEqual(len(TOOL_CATALOG), 20)
        categories = " ".join(str(row.get("category", "")).lower() for row in TOOL_CATALOG)
        for expected in ["wi-fi", "bluetooth", "rfid", "sdr", "zigbee", "can", "usb", "serial", "embedded"]:
            self.assertIn(expected, categories)

    def test_operator_control_is_global_default(self):
        self.assertTrue(POLICY_DEFAULTS["requires_enrollment"])
        self.assertFalse(POLICY_DEFAULTS["auto_chain"])
        self.assertTrue(POLICY_DEFAULTS["persist_results"])
        self.assertTrue(POLICY_DEFAULTS["record_timing"])
        self.assertTrue(POLICY_DEFAULTS["record_remediation"])

    def test_every_tool_gets_policy_and_status(self):
        with patch("agentwhite.tool_registry.shutil.which", return_value=None), patch(
            "agentwhite.tool_registry.importlib.util.find_spec", return_value=None
        ):
            rows = list_tools()
        self.assertEqual(len(rows), len(TOOL_CATALOG))
        for row in rows:
            self.assertIn("policy", row)
            self.assertFalse(row["policy"]["auto_chain"])
            self.assertIn("installed", row)
            self.assertIn("bundle_policy", row)
            self.assertIn(row["effect"], {"PASSIVE", "ACTIVE", "DISRUPTIVE"})

    def test_nmap_is_not_marked_for_bundling(self):
        nmap = next(row for row in TOOL_CATALOG if row["id"] == "nmap")
        self.assertEqual(nmap["bundle_policy"], "external-only")

    def test_tool_center_is_easy_button_driven(self):
        self.assertEqual(AgentWhiteHandler.server_version, "AgentWhite/0.5")
        self.assertIn("TOOL CENTER", TOOLS_HTML)
        self.assertIn("QUICK ACTIONS", TOOLS_HTML)
        self.assertIn("TOOL FAMILIES", TOOLS_HTML)
        self.assertIn("TOOL HISTORY", TOOLS_HTML)
        self.assertIn("AUTO-CHAIN OFF", TOOLS_HTML)
        self.assertIn("Run", TOOLS_HTML)
        self.assertIn("WI-FI", TOOLS_HTML)
        self.assertIn("BLUETOOTH", TOOLS_HTML)
        self.assertIn("RFID / NFC", TOOLS_HTML)
        self.assertIn("RF / SDR / ZIGBEE", TOOLS_HTML)
        self.assertIn("USB / SERIAL", TOOLS_HTML)
        self.assertIn("CAN / AUTO", TOOLS_HTML)


if __name__ == "__main__":
    unittest.main()
