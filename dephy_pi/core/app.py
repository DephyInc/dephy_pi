from cleo import Application
from cleo.config import ApplicationConfig as BaseApplicationConfig
from clikit.api.formatter import Style

from dephy_pi.commands.create import CreateCommand


# ============================================
#             DephyPiApplication
# ============================================
class DephyPiApplication(Application):
    """
    Defines the base `dephy_pi` command.
    """

    # -----
    # constructor
    # -----
    def __init__(self):
        super().__init__(config=ApplicationConfig())
        self._get_commands()

    # -----
    # _get_commands
    # -----
    def _get_commands(self):
        command_list = [
            CreateCommand,
        ]
        for command in command_list:
            self.add(command())


# ============================================
#              ApplicationConfig
# ============================================
class ApplicationConfig(BaseApplicationConfig):
    """
    Handles configuration of the CLI.
    """

    # -----
    # configure
    # -----
    def configure(self):
        super().configure()

        self.add_style(Style("c1").fg("cyan"))
        self.add_style(Style("c2").fg("default").bold())
        self.add_style(Style("info").fg("blue"))
        self.add_style(Style("comment").fg("green"))
        self.add_style(Style("error").fg("red").bold())
        self.add_style(Style("warning").fg("yellow").bold())
        self.add_style(Style("debug").fg("default").dark())
        self.add_style(Style("success").fg("green"))

        # Dark variants
        self.add_style(Style("c1_dark").fg("cyan").dark())
        self.add_style(Style("c2_dark").fg("default").bold().dark())
        self.add_style(Style("success_dark").fg("green").dark())
