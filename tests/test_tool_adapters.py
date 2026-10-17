import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from agentwhite.tool_adapters import TOOL_ACTIONS, list_tool_actions, run_tool_action
from agentwhite.tool_history import ToolRunStore
from agentwhite.tool_registry import TOOL_CATALOG


class ToolAdapterTests(unittest.TestCase):
    def test_every_registered_tool_has_a_ui_adapter(self):
        registered = {str(row["id"]) for row in TOOL_CATALOG}
        adapted = {action.tool_id for action in TOOL_ACTIONS}
        self.assertEqual(registered, adapted)

    def test_all_current_tool_buttons_are_passive_fixed_and_never_auto_chain(self):
        rows = list_tool_actions({a.tool_id for a in TOOL_ACTIONS})
        self.assertGreaterEqual(len(rows), 24)
        for row in rows:
            self.assertEqual(row["effect"], "PASSIVE")
            self.assertEqual(row["scope"], "local-host")
            self.assertFalse(row["accepts_arbitrary_args"])
            self.assertFalse(row["auto_chain"])

    def test_fixed_command_uses_shell_false_and_bounded_argv(self):
        completed = SimpleNamespace(returncode=0, stdout="Kismet 1.0", stderr="")
        with patch("agentwhite.tool_adapters.shutil.which", return_value="/usr/bin/kismet"), patch(
            "agentwhite.tool_adapters.subprocess.run", return_value=completed
        ) as runner:
            result = run_tool_action("kismet.version")
        self.assertFalse(result["auto_chain"])
        self.assertEqual(result["result"]["returncode"], 0)
        args, kwargs = runner.call_args
        self.assertEqual(args[0], ["/usr/bin/kismet", "--version"])
        self.assertFalse(kwargs["shell"])
        self.assertEqual(kwargs["timeout"], 10)

    def test_proxmark_adapter_uses_only_known_client_and_help_flag(self):
        completed = SimpleNamespace(returncode=0, stdout="help", stderr="")
        with patch("agentwhite.tool_adapters.shutil.which", side_effect=lambda x: "/usr/bin/pm3" if x == "pm3" else None), patch(
            "agentwhite.tool_adapters.subprocess.run", return_value=completed
        ) as runner:
            result = run_tool_action("proxmark3.client")
        self.assertEqual(result["result"]["argv"], ["pm3", "--help"])
        self.assertFalse(runner.call_args.kwargs["shell"])

    def test_missing_executable_is_not_silently_faked(self):
        with patch("agentwhite.tool_adapters.shutil.which", return_value=None):
            with self.assertRaises(FileNotFoundError):
                run_tool_action("hackrf.inventory")


class ToolHistoryTests(unittest.TestCase):
    def test_tool_run_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ToolRunStore(Path(tmp) / "test.db")
            run_id = store.add_run(
                tool_id="hackrf",
                action_id="hackrf.inventory",
                label="Inspect HackRF Hardware",
                effect="PASSIVE",
                scope="local-host",
                status="success",
                started_at="2026-10-17T12:00:00+00:00",
                elapsed_ms=55,
                result={"auto_chain": False, "result": {"serial": "test"}},
            )
            row = store.list_runs()[0]
            self.assertEqual(row["id"], run_id)
            self.assertEqual(row["elapsed_ms"], 55)
            self.assertFalse(row["result"]["auto_chain"])


if __name__ == "__main__":
    unittest.main()
