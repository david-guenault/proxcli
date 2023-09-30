#!/usr/bin/env python
"""Custom proxcli exceptions"""


class VmIdentificationException(Exception):
    """raised when we have the choice between a filter
    or a vmid to specify vm selection and neither
    vmid nor filter_name is specified"""
    def __init__(
            self,
            message="You must specify one of vmid or filter options"
    ) -> None:
        self.message = message
        super().__init__(self.message)


class VmIdMutualyExclusiveException(Exception):
    """raised when we have the choice between a filter
    or a vmid to specify vm selection and both are specified"""
    def __init__(
            self,
            message="vmid and filter options are mutualy exclusive"
    ) -> None:
        self.message = message
        super().__init__(self.message)


class ProxmoxClusterDownException(Exception):
    """raised when we have no proxmox node availabale"""
    def __init__(
            self,
            message="No nodes available"
    ) -> None:
        self.message = message
        super().__init__(self.message)


class ProxmoxVmNotFoundException(Exception):
    """raised when we have no proxmox node availabale"""
    def __init__(
            self,
            message="virtual machine not found"
    ) -> None:
        self.message = message
        super().__init__(self.message)


class ProxmoxVmMigrateFailedException(Exception):
    """raised when we vm migration fail"""
    def __init__(
            self,
            message="virtual machine not found"
    ) -> None:
        self.message = message
        super().__init__(self.message)


class ProxmoxVmNeedStopException(Exception):
    """raised when we an action on a vm need first to stop the vm"""
    def __init__(
            self,
            message="virtual machine must be stopped before action"
    ) -> None:
        self.message = message
        super().__init__(self.message)


class ProxmoxVmConfigGetException(Exception):
    """raised when we can't get virtual machine config"""
    def __init__(
            self,
            message="Virtual machine config could not be loaded"
    ) -> None:
        self.message = message
        super().__init__(self.message)


class ProxmoxVmGetNetIfacesException(Exception):
    """raised when we can't get virtual machine interfaces"""
    def __init__(
            self,
            message="Could not retrieve Net Ifaces list"
    ) -> None:
        self.message = message
        super().__init__(self.message)
