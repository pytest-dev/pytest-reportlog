import json
from collections import defaultdict
from typing import TextIO
import bz2, gzip, lzma, io
import pytest
from pathlib import Path
from _pytest.reports import BaseReport

from pytest_reportlog.plugin import cleanup_unserializable, _open_filtered_writer

from typing import Protocol, Literal


class OpenerModule(Protocol):
    def open(self, path: Path, mode: Literal["rt"]) -> TextIO: ...


@pytest.mark.parametrize(
    "filename, opener_module",
    [
        ("test.jsonl", io),
        ("test.unknown", io),
        ("test.jsonl.gz", gzip),
        ("test.jsonl.bz2", bz2),
        ("test.jsonl.xz", lzma),
    ],
)
def test_open_filtered(filename: str, opener_module: OpenerModule, tmp_path: Path):
    path = tmp_path / filename
    with _open_filtered_writer(path) as fp:
        fp.write("test\n")
    with opener_module.open(path, "rt") as fp2:
        assert fp2.read() == "test\n"


def test_basics(testdir, tmp_path, pytestconfig):
    """Basic testing of the report log functionality.

    We don't test the test reports extensively because they have been
    tested already in ``test_reports``.
    """
    p = testdir.makepyfile(
        """
        import warnings

        def test_ok():
            pass

        def test_fail():
            assert 0

        def test_warning():
            warnings.warn("message", UserWarning)
        """
    )

    log_file = tmp_path / "log.json"

    result = testdir.runpytest("--report-log", str(log_file))
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    result.stdout.fnmatch_lines([f"* generated report log file: {log_file}*"])

    json_objs = [json.loads(x) for x in log_file.read_text().splitlines()]
    if pytest.version_tuple[0] < 8:
        assert len(json_objs) == 14
    else:
        # In pytest 8 it produces an extra CollectReport for the extra pytest.Directory being collected.
        assert len(json_objs) == 15

    # first line should be the session_start
    session_start = json_objs[0]
    assert session_start == {
        "pytest_version": pytest.__version__,
        "$report_type": "SessionStart",
    }

    # last line should be the session_finish
    session_start = json_objs[-1]
    assert session_start == {
        "exitstatus": pytest.ExitCode.TESTS_FAILED,
        "$report_type": "SessionFinish",
    }

    split = defaultdict(list)
    for obj in json_objs:
        split[obj["$report_type"] == "WarningMessage"].append(obj)
    [warning] = split[True]
    json_objs = split[False]

    assert warning == {
        "$report_type": "WarningMessage",
        "category": "UserWarning",
        "when": "runtest",
        "message": "message",
        "lineno": 10,
        "location": None,  # seems to be hard-coded to None
        "filename": str(p),
    }

    # rest of the json objects should be unserialized into report objects; we don't test
    # the actual report object extensively because it has been tested in ``test_reports``
    # already.
    pm = pytestconfig.pluginmanager
    for json_obj in json_objs[1:-1]:
        rep = pm.hook.pytest_report_from_serializable(
            config=pytestconfig, data=json_obj
        )
        assert isinstance(rep, BaseReport)


@pytest.mark.parametrize(
    "exclude", [True, False], ids=["exclude on pass", "include logs on pass"]
)
def test_exclude_logs_for_passing_tests(testdir, tmp_path, exclude):
    passing_log_entry = "THIS TEST PASSED!"
    passing_stdout_entry = "PASSED WITH STDOUT ENTRY"
    passing_stderr_entry = "PASSED WITH STDERR ENTRY"
    failing_log_entry = "THIS TEST FAILED!"
    failing_stdout_entry = "FAILED WITH STDOUT ENTRY"
    failing_stderr_entry = "FAILED WITH STDERR ENTRY"
    testdir.makepyfile(
        f"""
        import sys
        import logging

        logger = logging.getLogger(__name__)

        def test_ok():
            logger.warning("{passing_log_entry}")
            sys.stdout.write("{passing_stdout_entry}")
            sys.stderr.write("{passing_stderr_entry}")

        def test_fail():
            logger.warning("{failing_log_entry}")
            sys.stdout.write("{failing_stdout_entry}")
            sys.stderr.write("{failing_stderr_entry}")
            assert 0
        """
    )
    fn = tmp_path / "result.log"
    if exclude:
        result = testdir.runpytest(
            f"--report-log={fn}", "--report-log-exclude-logs-on-passed-tests"
        )
    else:
        result = testdir.runpytest(f"--report-log={fn}")
    result.stdout.fnmatch_lines("*1 failed, 1 passed*")

    log = fn.read_text("UTF-8")
    if exclude:
        assert passing_log_entry not in log
        assert passing_stdout_entry not in log
        assert passing_stderr_entry not in log
    else:
        assert passing_log_entry in log
        assert passing_stdout_entry in log
        assert passing_stderr_entry in log
    assert failing_log_entry in log
    assert failing_stdout_entry in log
    assert failing_stderr_entry in log


def test_xdist_integration(testdir, tmp_path):
    pytest.importorskip("xdist")
    testdir.makepyfile(
        """
        import warnings

        def test_ok():
            pass

        def test_fail():
            assert 0

        def test_warning():
            warnings.warn("message", UserWarning)
        """
    )
    fn = tmp_path / "result.log"
    result = testdir.runpytest("-n2", f"--report-log={fn}")
    result.stdout.fnmatch_lines("*1 failed, 2 passed, 1 warning*")

    lines = fn.read_text("UTF-8").splitlines()
    data = json.loads(lines[0])
    assert data == {
        "pytest_version": pytest.__version__,
        "$report_type": "SessionStart",
    }


def test_cleanup_unserializable():
    """Unittest for the cleanup_unserializable function"""
    good = {"x": 1, "y": ["a", "b"]}
    new = cleanup_unserializable(good)
    assert new == good

    class C:
        def __str__(self):
            return "C instance"

    bad = {"x": 1, "y": ["a", "b"], "c": C()}
    new = cleanup_unserializable(bad)
    assert new == {"x": 1, "c": "C instance", "y": ["a", "b"]}


def test_subtest(pytester, tmp_path):
    """Regression test for #90."""
    pytester.makepyfile(
        """
        def test_foo(subtests):
            with subtests.test():
                pass
    """
    )
    fn = tmp_path / "result.log"
    result = pytester.runpytest(f"--report-log={fn}")
    result.stdout.fnmatch_lines("*1 passed in*")
    lines = fn.read_text("UTF-8").splitlines()
    for line in lines:
        data = json.loads(line)
        assert "$report_type" in data
