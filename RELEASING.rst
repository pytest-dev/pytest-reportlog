Here are the steps on how to make a new release.

1. Create a ``release-VERSION`` branch from ``upstream/main``.
2. Update ``CHANGELOG.rst``.
3. Push the branch to ``upstream`` and open a PR.
4. Once all tests pass, start the ``deploy`` workflow manually from the branch ``release-VERSION``, passing ``VERSION`` as parameter.
5. Merge the PR.
