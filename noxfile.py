import nox


# ============================================
#                    lint
# ============================================
@nox.session
def lint(session):
    session.install("black", "flake8")
    session.run("black", ".")
    session.run("flake8", "--max-line-length", "88", ".")


# ============================================
#                    test
# ============================================
@nox.session
def test(session):
    session.install("pytest")
    session.run("pytest", "-sv", "tests/")
