import os
import subprocess as sub

import pytest
import gi

gi.require_version("UMockdev", "1.0")
from gi.repository import UMockdev

from dephy_pi.utilities import disk_utils as du


# ============================================
#         test_get_removable_drives
# ============================================
@pytest.mark.parametrize("nRemovables", [0, 1, 2])
def test_get_removable_drives(nRemovables):
    devFile = f"nRemovables_{nRemovables}.umockdev"
    devFile = os.path.join(os.path.abspath(__file__), "data", devFile)
    testbed = UMockdev.Testbed.new()
    testbed.add_from_file(devFile)
    removables = du.get_removable_drives()
    assert len(removables) == nRemovables


# ============================================
#          test_get_disk_partitions
# ============================================
@pytest.mark.parametrize("nPartitions", [0, 1, 2])
def test_get_disk_partitions():
    devFile = f"nPartitions_{nPartitions}.umockdev"
    devFile = os.path.join(os.path.abspath(__file__), "data", devFile)
    testbed = UMockdev.Testbed.new()
    testbed.add_from_file(devFile)
    partitions = du.get_disk_partitions(disk)
    assert len(removables) == nRemovables
