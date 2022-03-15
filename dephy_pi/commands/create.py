import os
import subprocess as sub
import sys

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
        self.bucketName = None
        self.remoteFile = None
        self.localFile = "dephy_pi.iso"
        self.sdDrive = None
        self.partitions = None
        self.rootfsMountPoint = os.abspath(os.getcwd())

    # -----
    # handle
    # -----
    def handle(self):
        # Download iso file
        s3_download(self.bucketName, self.remoteFile, self.localFile)
        # Find correct drive
        self._get_sd_drive()
        # Make sure the sd card partitions are unmounted
        self._unmount_partitions()
        # Flash sd card
        self._flash()
        # Mount rootfs partition
        self._mount_rootfs()
        # Edit wifi config (edit wpa_supplicant.conf file)
        self._setup_wifi()
        # Edit ssh config (hostname)
        self._setup_hostname()
        # Delete image from user's hdd, unmount, and eject usb
        self._clean_up()

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
            mountPoint = get_disk_mount_point(partition.device_node)
            if mountPoint:
                process = sub.Popen(["umount", mountPoint])
                process.wait()

    # -----
    # _flash
    # -----
    def _flash(self):
        cmd = [
            "dd",
            f"if={self.localFile}",
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
    # _mount_rootfs
    # -----
    def _mount_rootfs(self):
        rootfs = None

        # Select rootfs partition
        for partition in self.partitions:
            if "rootfs" in partition.device_node:
                rootfs = partition
                break

        if not rootfs:
            self.line("Couldn't find rootfs!")
            sys.exit(1)

        # Create mount point (requires sudo)
        process = sub.Popen(["mkdir", self.rootfsMountPoint])
        process.wait()
        process = sub.Popen(["sudo", "mount", rootfs, self.rootfsMountPoint])
        process.wait()

    # -----
    # _setup_wifi
    # -----
    def _setup_wifi(self):
        # TODO: wpa_passphrase creates the entry for the wpa_supplicant.conf file,
        # but it includes the unencrypted psk as a commented-out line in that entry.
        # I'm assuming that line doesn't need to be present in order for the pi
        # to connect to the network? Otherwise, what was the point of encrypting it?
        # I've left it in for now, but it should be parsed out

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

        # Get path to conf file
        wpaSupplicant = os.path.join(
            self.rootfsMountPoint, "/etc/wpa_supplicant/wpa_supplicant.conf"
        )

        # Write network details to file
        process = sub.Popen(["sudo", "echo", output, ">>", wpaSupplicant])
        process.wait()

    # -----
    # _setup_hostname
    # -----
    def _setup_hostname(self):
        # https://tinyurl.com/mr424544
        hostname = self.ask("Enter a hostname for your pi: ")
        hostFile = os.path.join(self.rootfsMountPoint, "/etc/hostname")
        process = sub.Popen(["sudo", "echo", hostname, ">", hostFile])
        process.wait()
        hostFile = os.path.join(self.rootfsMountPoint, "/etc/hosts")
        process = sub.Popen(
            [
                "sudo",
                "sed",
                "-i",
                r"'s/\(127\.0\.0\.1\s*\)localhost/\1"+f"{hostname}/'",
                hostFile,
            ]
        )
        process.wait()

    # -----
    # _clean_up
    # -----
    def _clean_up(self):
        process = sub.Popen(["rm", self.localFile])
        process.wait()
        process = sub.Popen(["sudo", "eject", self.sdDrive])
        process.wait()
