import nox


# ============================================
#                    lint
# ============================================
@nox.session
def lint(session):
    session.install("black", "flake8")
    session.run("black", "./dephy_pi")
    session.run("black", "./tests")
    session.run("flake8", "--max-line-length", "88", "./dephy_pi")


# ============================================
#                    test
# ============================================
@nox.session(python=["3.8", "3.9"])
def test(session):
    session.install("pytest", "pycairo", "PyGObject", "pyudev")
    session.run("umockdev-run", "--", "pytest", "-sv", "tests/")
