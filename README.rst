================
pytest-reportlog
================

|python| |version| |anaconda| |ci| |black|

.. |version| image:: http://img.shields.io/pypi/v/pytest-reportlog.svg
  :target: https://pypi.python.org/pypi/pytest-reportlog

.. |anaconda| image:: https://img.shields.io/conda/vn/conda-forge/pytest-reportlog.svg
    :target: https://anaconda.org/conda-forge/pytest-reportlog

.. |ci| image:: https://github.com/pytest-dev/pytest-reportlog/workflows/build/badge.svg
  :target: https://github.com/pytest-dev/pytest-reportlog/actions

.. |python| image:: https://img.shields.io/pypi/pyversions/pytest-reportlog.svg
  :target: https://pypi.python.org/pypi/pytest-reportlog/

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
  :target: https://github.com/ambv/black

Replacement for the ``--resultlog`` option, focused in simplicity and extensibility.

.. note::
    This plugin was created so developers can try out the candidate to replace the
    `deprecated --resultlog <https://docs.pytest.org/en/latest/deprecations.html#result-log-result-log>`__ option.

    If you use ``--resultlog``, please try out ``--report-log`` and provide feedback.

Usage
=====

The ``--report-log=FILE`` option writes *report logs* into a file as the test session executes.

Each line of the report log contains a self contained JSON object corresponding to a testing event,
such as a collection or a test result report. The file is guaranteed to be flushed after writing
each line, so systems can read and process events in real-time.

Each JSON object contains a special key ``$report_type``, which contains a unique identifier for
that kind of report object. For future compatibility, consumers of the file should ignore reports
they don't recognize, as well as ignore unknown properties/keys in JSON objects that they do know,
as future pytest versions might enrich the objects with more properties/keys.


Example
-------

Consider this file:

.. code-block:: python

    # content of test_report_example.py


    def test_ok():
        assert 5 + 5 == 10


    def test_fail():
        assert 4 + 4 == 1


::

    $ pytest test_report_example.py -q --report-log=log.json
    .F                                                                 [100%]
    ================================ FAILURES ================================
    _______________________________ test_fail ________________________________

        def test_fail():
    >       assert 4 + 4 == 1
    E       assert (4 + 4) == 1

    test_report_example.py:6: AssertionError
    ------------------ generated report log file: log.json -------------------
    ======================== short test summary info =========================
    FAILED test_report_example.py::test_fail - assert (4 + 4) == 1
    1 failed, 1 passed in 0.01s


The generated ``log.json`` will contain a JSON object per line:

::

    $ cat log.json
    {"pytest_version": "7.2.1", "$report_type": "SessionStart"}
    {"nodeid": "", "outcome": "passed", "longrepr": null, "result": null, "sections": [], "$report_type": "CollectReport"}
    {"nodeid": "test_report_example.py", "outcome": "passed", "longrepr": null, "result": null, "sections": [], "$report_type": "CollectReport"}
    {"nodeid": "test_report_example.py::test_ok", "location": ["test_report_example.py", 0, "test_ok"], "keywords": {"test_ok": 1, "test_report_example.py": 1, "pytest-reportlog": 1}, "outcome": "passed", "longrepr": null, "when": "setup", "user_properties": [], "sections": [], "duration": 9.839799895416945e-05, "start": 1674651583.6440034, "stop": 1674651583.6441023, "$report_type": "TestReport"}
    {"nodeid": "test_report_example.py::test_ok", "location": ["test_report_example.py", 0, "test_ok"], "keywords": {"test_ok": 1, "test_report_example.py": 1, "pytest-reportlog": 1}, "outcome": "passed", "longrepr": null, "when": "call", "user_properties": [], "sections": [], "duration": 8.005800191313028e-05, "start": 1674651583.6442027, "stop": 1674651583.644283, "$report_type": "TestReport"}
    {"nodeid": "test_report_example.py::test_ok", "location": ["test_report_example.py", 0, "test_ok"], "keywords": {"test_ok": 1, "test_report_example.py": 1, "pytest-reportlog": 1}, "outcome": "passed", "longrepr": null, "when": "teardown", "user_properties": [], "sections": [], "duration": 6.103400301071815e-05, "start": 1674651583.644366, "stop": 1674651583.6444275, "$report_type": "TestReport"}
    {"nodeid": "test_report_example.py::test_fail", "location": ["test_report_example.py", 4, "test_fail"], "keywords": {"test_fail": 1, "test_report_example.py": 1, "pytest-reportlog": 1}, "outcome": "passed", "longrepr": null, "when": "setup", "user_properties": [], "sections": [], "duration": 6.432399823097512e-05, "start": 1674651583.6445801, "stop": 1674651583.644645, "$report_type": "TestReport"}
    {"nodeid": "test_report_example.py::test_fail", "location": ["test_report_example.py", 4, "test_fail"], "keywords": {"test_fail": 1, "test_report_example.py": 1, "pytest-reportlog": 1}, "outcome": "failed", "longrepr": {"reprcrash": {"path": "/home/rafal/sources/misc/pytest-reportlog/test_report_example.py", "lineno": 6, "message": "assert (4 + 4) == 1"}, "reprtraceback": {"reprentries": [{"type": "ReprEntry", "data": {"lines": ["    def test_fail():", ">       assert 4 + 4 == 1", "E       assert (4 + 4) == 1"], "reprfuncargs": {"args": []}, "reprlocals": null, "reprfileloc": {"path": "test_report_example.py", "lineno": 6, "message": "AssertionError"}, "style": "long"}}], "extraline": null, "style": "long"}, "sections": [], "chain": [[{"reprentries": [{"type": "ReprEntry", "data": {"lines": ["    def test_fail():", ">       assert 4 + 4 == 1", "E       assert (4 + 4) == 1"], "reprfuncargs": {"args": []}, "reprlocals": null, "reprfileloc": {"path": "test_report_example.py", "lineno": 6, "message": "AssertionError"}, "style": "long"}}], "extraline": null, "style": "long"}, {"path": "/home/rafal/sources/misc/pytest-reportlog/test_report_example.py", "lineno": 6, "message": "assert (4 + 4) == 1"}, null]]}, "when": "call", "user_properties": [], "sections": [], "duration": 0.00014615400141337886, "start": 1674651583.6447048, "stop": 1674651583.6448512, "$report_type": "TestReport"}
    {"nodeid": "test_report_example.py::test_fail", "location": ["test_report_example.py", 4, "test_fail"], "keywords": {"test_fail": 1, "test_report_example.py": 1, "pytest-reportlog": 1}, "outcome": "passed", "longrepr": null, "when": "teardown", "user_properties": [], "sections": [], "duration": 9.126199802267365e-05, "start": 1674651583.6515481, "stop": 1674651583.6516397, "$report_type": "TestReport"}
    {"exitstatus": 1, "$report_type": "SessionFinish"}


License
=======

Distributed under the terms of the `MIT`_ license.

.. _MIT: https://github.com/pytest-dev/pytest-mock/blob/master/LICENSE
