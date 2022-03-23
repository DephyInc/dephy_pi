import os
import subprocess as sub
import sys
import tempfile

from cleo import Command

from dephy_pi.utilities.disk_utils import get_disk_mount_point
from dephy_pi.utilities.disk_utils import get_disk_partitions
from dephy_pi.utilities.disk_utils import get_removable_drives
from dephy_pi.utilities.network_utils import s3_download


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
        self.localFile = None
        self.sdDrive = None
        self.partitions = None
        self.rootfs = None

    # -----
    # handle
    # -----
    def handle(self):
        # Find correct drive
        self._get_sd_drive()
        # Make sure the sd card partitions are unmounted
        self._unmount_partitions()
        # Get rootfs partition
        self._get_rootfs()
        with tempfile.NamedTemporaryFile() as self.localFile:
            # Download iso file
            s3_download(self.bucketName, self.remoteFile, self.localFile.name)
            # Flash sd card
            self._flash()
        # Edit wifi config (edit wpa_supplicant.conf file)
        self._setup_wifi()
        # Edit hostname
        self._setup_hostname()
        # Eject usb
        process = sub.Popen(["sudo", "eject", self.sdDrive])
        process.wait()

    # -----
    # _get_sd_drive
    # -----
    def _get_sd_drive(self):
        removableDrives = get_removable_drives()
        if len(removableDrives) == 0:
            self.line("Drive not found.")
            sys.exit(1)
        elif len(removableDrives) == 1:
            self.sdDrive = removableDrives[0]
        else:
            msg = "Multiple removable drives found. Please select the "
            msg += "one with the sd card to flash:"
            self.sdDrive = self.choice(msg, removableDrives)

    # -----
    # _unmount_partitions
    # -----
    def _unmount_partitions(self):
        self.partitions = get_disk_partitions(self.sdDrive)
        for partition in self.partitions:
            mountPoint = get_disk_mount_point(partition)
            if mountPoint:
                process = sub.Popen(["umount", mountPoint])
                process.wait()

    # -----
    # _flash
    # -----
    def _flash(self):
        cmd = [
            "sudo",
            "dd",
            f"if={self.localFile.name}",
            f"of={self.sdDrive.device_node}",
            "bs=32M",
            "conv=fsync",
        ]
        process = sub.Popen(cmd, stdout=sub.PIPE, text=True)
        while True:
            result = process.poll()
            if result is not None:
                break

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
    def _setup_wifi(self):
        # Get network details
        ssid = self.ask("Enter the WiFi network to connect your Pi to: ")
        psk = self.secret("Enter the network's password: ")

        # Encrypt the password before writing it to the conf file
        process = sub.Popen(
            ["wpa_passphrase", ssid, psk], stdout=sub.PIPE, stderr=sub.STDOUT, text=True
        )
        process.wait()
        del psk

        # Parse the output, which includes both stdout and stderr as a tuple
        output = process.communicate()[0]
        assert output.startswith("network=")

        # Mount the rootfs
        with tempfile.TemporaryDirectory() as mountPoint:
            process = sub.Popen(["sudo", "mount", self.rootfs, mountPoint])
            process.wait()

            wpaSupplicant = os.path.join(
                mountPoint, "etc", "wpa_supplicant", "wpa_supplicant.conf"
            )

            # Change permissions to allow modifying the supplicant file
            process = sub.Popen(["sudo", "chmod", "a=rw", wpaSupplicant])
            process.wait()

            # Write the new data
            with open(wpaSupplicant, "a") as fd:
                fd.write(output)

            process = sub.Popen(["sudo", "umount", self.rootfs])
            process.wait()

    # -----
    # _setup_hostname
    # -----
    def _setup_hostname(self):
        # https://tinyurl.com/mr424544
        hostname = self.ask("Enter a hostname for your pi: ")

        with tempfile.TemporaryDirectory() as mountPoint:
            process = sub.Popen(["sudo", "mount", self.rootfs, mountPoint])
            process.wait()

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
                    r"s/\(127\.0\.0\.1\s*\)localhost/\1"+f"{hostname}/",
                    hostFile,
                ]
            )
            process.wait()

            process = sub.Popen(["sudo", "umount", self.rootfs])
            process.wait()
