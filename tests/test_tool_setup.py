import unittest
from unittest.mock import patch

from agentwhite.tool_setup import (
    BUNDLED_PYTHON_TOOLS,
    WINDOWS_WINGET_RECIPES,
    augment_tools,
    classify_setup,
    run_setup,
)


class ToolSetupTests(unittest.TestCase):
    def test_core_python_engines_are_declared_bundled(self):
        for tool_id in {"bleak", "scapy", "python-can", "pyserial", "pyusb"}:
            self.assertIn(tool_id, BUNDLED_PYTHON_TOOLS)

    def test_platform_mismatch_is_not_reported_as_generic_missing(self):
        tool = {
            "id": "kismet",
            "name": "Kismet",
            "installed": False,
            "platforms": ["linux"],
            "hardware": ["Wi-Fi adapter"],
        }
        with patch("agentwhite.tool_setup.current_platform", return_value="windows"):
            state = classify_setup(tool)
        self.assertEqual(state["state"], "unsupported-platform")
        self.assertFalse(state["installable"])

    def test_nmap_windows_recipe_is_fixed(self):
        self.assertEqual(WINDOWS_WINGET_RECIPES["nmap"]["package_id"], "Insecure.Nmap")

    def test_wireshark_windows_recipe_is_fixed(self):
        self.assertEqual(
            WINDOWS_WINGET_RECIPES["tshark"]["package_id"],
            "WiresharkFoundation.Wireshark",
        )

    def test_setup_command_does_not_accept_arbitrary_arguments(self):
        completed = type("Done", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()
        with patch("agentwhite.tool_setup.current_platform", return_value="windows"), patch(
            "agentwhite.tool_setup.shutil.which", return_value=r"C:\\Windows\\winget.exe"
        ), patch("agentwhite.tool_setup.subprocess.run", return_value=completed) as runner:
            result = run_setup("nmap")
        args, kwargs = runner.call_args
        argv = args[0]
        self.assertEqual(argv[0], r"C:\\Windows\\winget.exe")
        self.assertEqual(argv[1:5], ["install", "--id", "Insecure.Nmap", "--exact"])
        self.assertFalse(kwargs["shell"])
        self.assertFalse(result["auto_chain"])

    def test_augment_tools_adds_setup_metadata(self):
        rows = [{"id": "bleak", "installed": True, "platforms": ["windows"], "hardware": []}]
        augmented = augment_tools(rows)
        self.assertEqual(augmented[0]["setup"]["state"], "ready")


if __name__ == "__main__":
    unittest.main()
