import platform

import psutil

if platform.system() == "Linux":
    import pyudev


# ============================================
#            get_removable_drives
# ============================================
def get_removable_drives():
    """
    Wrapper for calling the os-specific version of
    `get_removable_drives`. Needed because libudev isn't available on
    Windows; it uses the Windows Device Manager.

    Returns
    -------
    List
        A list of all of the removable drives connected to the system.
    """
    if platform.system() == "Linux":
        return _get_removable_drives_linux()
    else:
        raise OSError


# ============================================
#        _get_removable_drives_linux
# ============================================
def _get_removable_drives_linux():
    """
    Obtains the list of all removable drives connected to the system.

    Returns
    -------
    List
        A list of all of the removable drives connected to the system.
    """
    context = pyudev.Context()
    removables = []
    devices = context.list_devices(subsystem="block", DEVTYPE="disk")

    for dev in devices:
        if dev.attributes.asstring("removable") == "1":
            removables.append(dev)

    return removables


# ============================================
#             get_disk_partitions
# ============================================
def get_disk_partitions(disk):
    """
    Wrapper for calling the os-specific version of
    `get_disk_paritions`. Needed because libudev isn't available on
    Windows; it uses the Windows Device Manager.

    Parameters
    ----------
    disk : pyudev.device._device.Device
        The disk for which we want the partitions.

    Returns
    -------
    List
        List of the device nodes for each child of `disk` that has a
        device type of "partition".
    """
    if platform.system() == "Linux":
        return _get_disk_partitions_linux(disk)
    else:
        raise OSError


# ============================================
#         _get_disk_partitions_linux
# ============================================
def _get_disk_partitions_linux(disk):
    """
    Finds the partitions for the given disk on Linux.

    Parameters
    ----------
    disk : pyudev.device._device.Device
        The disk for which we want the partitions.

    Returns
    -------
    List
        List of the device nodes for each child of `disk` that has a
        device type of "partition".
    """
    diskPartitions = []
    context = pyudev.Context()

    partitions = context.list_devices(
        subsystem="block", DEVTYPE="partition", parent=disk
    )

    for pt in partitions:
        diskPartitions.append(pt.device_node)

    return diskPartitions


# ============================================
#            get_disk_mount_point
# ============================================
def get_disk_mount_point(disk):
    """
    Wrapper for calling the os-specific version of
    `get_disk_mount_point`. Needed because libudev isn't available on
    Windows; it uses the Windows Device Manager.

    Parameters
    ----------
    disk : str
        The name of the disk for which we want the mount point.

    Returns
    -------
    str | None
        The disk's mount point. If it's unmounted then it's `None`.
    """
    if platform.system() == "Linux":
        return _get_disk_mount_point_linux(disk)
    else:
        raise OSError("Only Linux is supported, currently!")


# ============================================
#         _get_disk_mount_point_linux
# ============================================
def _get_disk_mount_point_linux(disk):
    """
    Determines whether or not the given disk is mounted. If so, we get
    its mount point. If not, the mount point is flagged as `None`.

    Parameters
    ----------
    disk : str
        The name of the disk for which we want the mount point.

    Returns
    -------
    str | None
        The disk's mount point. If it's unmounted then it's `None`.
    """
    mountPoint = None

    # psutil shows only the mounted partitions
    for pt in psutil.disk_partitions():
        if pt.device == disk:
            mountPoint = pt.mountpoint
            break

    return mountPoint
