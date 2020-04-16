import json

import pytest
from _pytest.reports import BaseReport

from pytest_reportlog.plugin import cleanup_unserializable


def test_basics(testdir, tmp_path, pytestconfig):
    """Basic testing of the report log functionality.

    We don't test the test reports extensively because they have been
    tested already in ``test_reports``.
    """
    testdir.makepyfile(
        """
        def test_ok():
            pass

        def test_fail():
            assert 0
    """
    )

    log_file = tmp_path / "log.json"

    result = testdir.runpytest("--report-log", str(log_file))
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    result.stdout.fnmatch_lines(["* generated report log file: {}*".format(log_file)])

    json_objs = [json.loads(x) for x in log_file.read_text().splitlines()]
    assert len(json_objs) == 10

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

    # rest of the json objects should be unserialized into report objects; we don't test
    # the actual report object extensively because it has been tested in ``test_reports``
    # already.
    pm = pytestconfig.pluginmanager
    for json_obj in json_objs[1:-1]:
        rep = pm.hook.pytest_report_from_serializable(
            config=pytestconfig, data=json_obj
        )
        assert isinstance(rep, BaseReport)


def test_xdist_integration(testdir, tmp_path):
    pytest.importorskip("xdist")
    testdir.makepyfile(
        """
        def test_ok():
            pass

        def test_fail():
            assert 0
    """
    )
    fn = tmp_path / "result.log"
    result = testdir.runpytest("-n2", "--report-log={}".format(fn))
    result.stdout.fnmatch_lines("*1 failed, 1 passed*")

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
