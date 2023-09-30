#!/usr/bin/env pytest
"""Test proxmoxlib output method"""
import urllib3
from proxmoxlib import Proxmox

urllib3.disable_warnings()


def test_output_raw():
    """test raw output"""
    proxmox_instance = Proxmox()
    headers = "c1,c2,c3"
    data = [
        ("a", "b", " c")
    ]
    result = proxmox_instance.output(
        data=data,
        headers=headers,
        output_format="internal"
    )
    assert isinstance(result, list)
    assert result[0][0] == "a"


def test_output_json():
    """test raw output"""
    proxmox_instance = Proxmox()
    data = [
        ("a", "b", " c")
    ]
    proxmox_instance.output(
        data=data,
        output_format="json"
    )


def test_output_yaml():
    """test raw output"""
    proxmox_instance = Proxmox()
    data = [
        ("a", "b", " c")
    ]
    proxmox_instance.output(
        data=data,
        output_format="yaml"
    )


def test_output_table():
    """test table output"""
    proxmox_instance = Proxmox()
    data = [
        {"c1": "a", "c2": "b", "c3":  "c"}
    ]
    proxmox_instance.output(
        data=data,
        headers="c1,c2,c3",
        output_format="table"
    )
