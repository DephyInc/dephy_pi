import os
import subprocess as sub
import sys
import tempfile

from cleo import Command

from dephy_pi.utilities.disk_utils import get_disk_mount_point
from dephy_pi.utilities.disk_utils import get_disk_partitions
from dephy_pi.utilities.disk_utils import get_removable_drives
from dephy_pi.utilities.network_utils import get_aws_resource


# ============================================
#                CreateCommand
# ============================================
class CreateCommand(Command):
    """
    Sets up an SD card with Dephy's raspberry pi image.

    create
    """

    # -----
    # constructor
    # -----
    def __init__(self):
        super().__init__()
        self.bucketName = "dephy-public-binaries"
        self.remoteFile = "mypi.iso"
        self.sdDrive = None
        self.partitions = None
        self.rootfs = None

    # -----
    # handle
    # -----
    def handle(self):
        self._get_sd_drive()
        self._unmount_partitions()
        with tempfile.NamedTemporaryFile() as localFile:
            self._download_iso(localFile)
            self._flash(localFile)
        self._get_rootfs()
        with tempfile.TemporaryDirectory() as mountPoint:
            process = sub.Popen(["sudo", "mount", self.rootfs, mountPoint])
            process.wait()
            self._setup_wifi(mountPoint)
            self._setup_hostname(mountPoint)
            process = sub.Popen(["sudo", "umount", self.rootfs])
            process.wait()
        process = sub.Popen(["sudo", "eject", self.sdDrive.device_node])
        process.wait()
        self.line("<success>Done!</success>")

    # -----
    # _get_sd_drive
    # -----
    def _get_sd_drive(self):
        self.line("<c2>Finding SD card...</c2>")
        try:
            removableDrives = get_removable_drives()
        except OSError:
            self.line("\t- <error>Error</error>: `dephy_pi` only runs on Linux.")
            sys.exit(1)
        if len(removableDrives) == 0:
            msg = (
                "\t- <error>Error</error>: Unable to find a valid SD card for flashing."
            )
            self.line(msg)
            sys.exit(1)
        elif len(removableDrives) == 1:
            self.sdDrive = removableDrives[0]
        else:
            msg = "\t- <warning>Multiple removable drives found</warning>. "
            msg += "Please select the one with the sd card to flash:"
            removableDrives.append("None of the above.")
            self.sdDrive = self.choice(msg, removableDrives)
            if self.sdDrive == "None of the above.":
                msg = "\t- <error>Error</error>: Unable to find a valid SD card for "
                msg += "flashing."
                self.line(msg)
        msg = f"\t- <warning>Found sd card at: </warning>{self.sdDrive.device_node}"
        self.line(msg)

    # -----
    # _unmount_partitions
    # -----
    def _unmount_partitions(self):
        self.line("<c2>Unmounting partitions...</c2>")
        try:
            self.partitions = get_disk_partitions(self.sdDrive)
        except OSError:
            self.line("\t- <error>Error</error>: `dephy_pi` only runs on Linux.")
            sys.exit(1)
        for partition in self.partitions:
            mountPoint = get_disk_mount_point(partition)
            if mountPoint:
                try:
                    sub.check_output(
                        ["umount", mountPoint], text=True, stderr=sub.STDOUT
                    )
                    msg = f"\t- <warning>Unmounted</warning>: `{partition}` from "
                    msg += f"`{mountPoint}`"
                    self.line(msg)
                except sub.CalledProcessError:
                    msg = "\t- <error>Error</error>: "
                    msg += f"Failed to unmount partition `{partition}` "
                    msg += f"from mount point `{mountPoint}`"
                    self.line(msg)
                    sys.exit(1)

    # -----
    # _download_iso
    # -----
    def _download_iso(self, localFile):
        """
        Downloads and verifies the Raspberry Pi iso from AWS.
        """
        s3 = get_aws_resource("s3")
        fileSize = s3.Bucket(self.bucketName).Object(self.remoteFile).content_length
        progBar = self.progress_bar(fileSize)
        progBar.set_message("<c2>Downloading iso:</c2>")
        progBar.set_format("%message% [%bar%] %percent:3s%% %elapsed%")
        progBar.set_redraw_frequency(1000)
        progBar.start()

        def _download_progress(chunk):
            progBar.advance(chunk)

        s3.Bucket(self.bucketName).download_file(
            self.remoteFile, localFile.name, Callback=_download_progress
        )
        progBar.set_message("<c2>Download complete!</c2>")
        progBar.finish()
        self.line("")

    # -----
    # _flash
    # -----
    def _flash(self, localFile):
        progBar = self.progress_bar()
        progBar.set_message("<c2>Flashing...</c2>")
        progBar.set_format("%message% [%bar%] %elapsed%")
        cmd = [
            "sudo",
            "dd",
            # f"if={localFile.name}",
            "if=mypi.iso",
            f"of={self.sdDrive.device_node}",
            "bs=32M",
            "conv=fsync",
        ]
        # Since we're not waiting after calling cmd, the progress bar gets
        # printed over the prompt for the user's password required by sudo.
        # If we wait, though, then we can't advance the progress bar. So,
        # we call a brief sleep command with a wait call to get the user's
        # password so when cmd calls sudo we don't need to prompt
        process = sub.Popen(["sudo", "sleep", "0.1"])
        process.wait()
        process = sub.Popen(cmd, stdout=sub.PIPE, text=True, stderr=sub.STDOUT)
        progBar.start()
        while True:
            result = process.poll()
            progBar.advance()
            if result is not None:
                break
        progBar.set_message("<c2>Flash complete!</c2>")
        progBar.finish()
        self.line("")

    # -----
    # _get_rootfs
    # -----
    def _get_rootfs(self):
        with tempfile.TemporaryDirectory() as mountPoint:
            for partition in self.partitions:
                process = sub.Popen(["sudo", "mount", partition, mountPoint])
                process.wait()
                content = os.listdir(mountPoint)
                process = sub.Popen(["sudo", "umount", partition])
                process.wait()
                if "root" in content:
                    self.rootfs = partition
                    break

    # -----
    # _setup_wifi
    # -----
    def _setup_wifi(self, mountPoint):
        # Get network details
        ssid = self.ask("Enter the WiFi network to connect your Pi to: ")
        psk = self.secret("Enter the network's password: ")

        # Encrypt the password before writing it to the conf file
        process = sub.Popen(
            ["wpa_passphrase", ssid, psk], stdout=sub.PIPE, stderr=sub.STDOUT, text=True
        )
        process.wait()

        # Parse the output, which includes both stdout and stderr as a tuple
        output = process.communicate()[0]
        assert output.startswith("network=")

        wpaSupplicant = os.path.join(
            mountPoint, "etc", "wpa_supplicant", "wpa_supplicant.conf"
        )

        # Change permissions to allow modifying the supplicant file
        process = sub.Popen(["sudo", "chmod", "a=rw", wpaSupplicant])
        process.wait()

        # Write the new data
        with open(wpaSupplicant, "a") as fd:
            fd.write(output)

    # -----
    # _setup_hostname
    # -----
    def _setup_hostname(self, mountPoint):
        # https://tinyurl.com/mr424544
        hostname = self.ask("Enter a hostname for your pi: ")
        hostFile = os.path.join(mountPoint, "etc", "hostname")

        # Change permissions to allow modifying the file
        process = sub.Popen(["sudo", "chmod", "a=rw", hostFile])
        process.wait()

        # Write the new hostname
        with open(hostFile, "a") as fd:
            fd.write(hostname)

        # Modify the hosts file, too
        hostFile = os.path.join(mountPoint, "etc", "hosts")
        process = sub.Popen(["sudo", "chmod", "a=rw", hostFile])
        process.wait()
        process = sub.Popen(
            [
                "sudo",
                "sed",
                "-i",
                r"s/\(127\.0\.0\.1\s*\)localhost/\1" + f"{hostname}/",
                hostFile,
            ]
        )
        process.wait()
