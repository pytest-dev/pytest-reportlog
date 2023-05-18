import json
from typing import Dict, Any, TextIO

from _pytest.pathlib import Path

import pytest


def pytest_addoption(parser):
    group = parser.getgroup("terminal reporting", "report-log plugin options")
    group.addoption(
        "--report-log",
        action="store",
        metavar="path",
        default=None,
        help="Path to line-based json objects of test session events.",
    )
    group.addoption(
        "--report-log-exclude-logs-on-passed-tests",
        action="store_true",
        default=False,
        help="Don't capture logs for passing tests",
    )


def pytest_configure(config):
    report_log = config.option.report_log
    if report_log and not hasattr(config, "workerinput"):
        config._report_log_plugin = ReportLogPlugin(config, Path(report_log))
        config.pluginmanager.register(config._report_log_plugin)


def pytest_unconfigure(config):
    report_log_plugin = getattr(config, "_report_log_plugin", None)
    if report_log_plugin:
        report_log_plugin.close()
        del config._report_log_plugin


def _open_filtered_writer(log_path: Path) -> TextIO:
    if log_path.suffix == ".gz":
        import gzip

        return gzip.open(log_path, "wt", encoding="UTF-8")
    elif log_path.suffix == ".bz2":
        import bz2

        return bz2.open(log_path, "wt", encoding="UTF-8")
    elif log_path.suffix == ".xz":
        import lzma

        return lzma.open(log_path, "wt", encoding="UTF-8")
    else:
        # line buffer for text mode to ease tail -f
        return log_path.open("wt", buffering=1, encoding="UTF-8")


class ReportLogPlugin:
    def __init__(self, config, log_path: Path):
        self._config = config
        self._log_path = log_path

        log_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = _open_filtered_writer(log_path)

    def close(self):
        if self._file is not None:
            self._file.close()
            self._file = None

    def _write_json_data(self, data):
        try:
            json_data = json.dumps(data)
        except TypeError:
            data = cleanup_unserializable(data)
            json_data = json.dumps(data)
        self._file.write(json_data + "\n")
        self._file.flush()

    def pytest_sessionstart(self):
        data = {"pytest_version": pytest.__version__, "$report_type": "SessionStart"}
        self._write_json_data(data)

    def pytest_sessionfinish(self, exitstatus):
        data = {"exitstatus": exitstatus, "$report_type": "SessionFinish"}
        self._write_json_data(data)

    def pytest_runtest_logreport(self, report):
        data = self._config.hook.pytest_report_to_serializable(
            config=self._config, report=report
        )
        if (
            self._config.option.report_log_exclude_logs_on_passed_tests
            and data.get("outcome", "") == "passed"
        ):
            data["sections"] = [
                s
                for s in data["sections"]
                if s[0]
                not in [
                    "Captured log setup",
                    "Captured log call",
                    "Captured log teardown",
                ]
            ]

        self._write_json_data(data)

    def pytest_warning_recorded(self, warning_message, when, nodeid, location):
        data = {
            "category": (
                warning_message.category.__name__ if warning_message.category else None
            ),
            "filename": warning_message.filename,
            "lineno": warning_message.lineno,
            "message": warning_message.message,
        }
        extra_data = {
            "$report_type": "WarningMessage",
            "when": when,
            "location": location,
        }
        data.update(extra_data)
        self._write_json_data(data)

    def pytest_collectreport(self, report):
        data = self._config.hook.pytest_report_to_serializable(
            config=self._config, report=report
        )
        self._write_json_data(data)

    def pytest_terminal_summary(self, terminalreporter):
        terminalreporter.write_sep("-", f"generated report log file: {self._log_path}")


def cleanup_unserializable(d: Dict[str, Any]) -> Dict[str, Any]:
    """Return new dict with entries that are not json serializable by their str()."""
    result = {}
    for k, v in d.items():
        try:
            json.dumps({k: v})
        except TypeError:
            v = str(v)
        result[k] = v
    return result
