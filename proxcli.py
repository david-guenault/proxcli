#!/usr/bin/env python
"""Proxcli is a remote proxmox cluster management tool"""
import sys
import typer
from typing_extensions import Annotated
from proxmoxlib import Proxmox
import proxcli_exceptions

app = typer.Typer(no_args_is_help=True)
vms = typer.Typer(no_args_is_help=True)
nodes = typer.Typer(no_args_is_help=True)
storages = typer.Typer(no_args_is_help=True)
storages_content = typer.Typer(no_args_is_help=True)
config = typer.Typer(no_args_is_help=True)
networks = typer.Typer(no_args_is_help=True)
tasks = typer.Typer(
    no_args_is_help=True, pretty_exceptions_enable=False,
    pretty_exceptions_short=False)
cluster = typer.Typer(no_args_is_help=True)
ha = typer.Typer(no_args_is_help=True)
ha_groups = typer.Typer(no_args_is_help=True)
ha_resources = typer.Typer(no_args_is_help=True)
vms_status_start = typer.Typer(no_args_is_help=True)
replications = typer.Typer(no_args_is_help=True)
inventory = typer.Typer(no_args_is_help=True)
tags = typer.Typer(no_args_is_help=True)

app.add_typer(vms, name="vms")
app.add_typer(nodes, name="nodes", help="Nodes related functions")
app.add_typer(
    inventory, name="inventory",
    help="Ansible inventory related functions")
app.add_typer(config, name="config")
app.add_typer(tasks, name="tasks")
app.add_typer(cluster, name="cluster")
app.add_typer(replications, name="replications")
nodes.add_typer(storages, name="storages")
storages.add_typer(storages_content, name="content")
nodes.add_typer(networks, name="networks")
vms.add_typer(
    tags,
    name="tags",
    help="vms and containers tags related functions")

ha.add_typer(ha_groups, name="groups", help="manage ha groups")
ha.add_typer(ha_resources, name="resources", help="manage ha resources")

cluster.add_typer(ha, name="ha", help="high availibility commands")

p = Proxmox()


# CONFIG #

@config.command("show")
def config_show():
    """ Display proxcli config file content
    Parameters:
    Returns:
    """
    p.dump_config()


@config.command("create")
def config_create(
    hosts: Annotated[str, typer.Option()],
    user: Annotated[str, typer.Option()],
    password: Annotated[str, typer.Option()]
) -> None:
    """Create a default proxcli config file
    Parameters:
        hosts: Coma separated list of proxmox hostnames/ip
        user: proxmox username
        password: proxmox password
    Returns:
    """
    p.create_config(hosts=hosts, user=user, password=password)


# CLUSTER #


@cluster.command("status")
def cluster_status(
    output_format: Annotated[str, typer.Option()] = "table"
) -> None:
    """Get and display cluster status
    Parameters:
        format: cluster status output format (json, yaml, table)
    Returns:
    """
    p.get_cluster_status(output_format=output_format)


@cluster.command("log")
def cluster_log(
    output_format: Annotated[str, typer.Option()] = "table",
    max_items: int = 100,
    proxmox_nodes: str = "pve1,pve2,pve3",
    severities: str = "panic,alert,critical,error,warning,notice,info,debug"
) -> None:
    """Show cluster logs
        Parameters:
        Returns:
    """
    p.get_cluster_log(
        output_format=output_format,
        max_items=max_items,
        proxmox_nodes=proxmox_nodes,
        severities=severities)


@storages.command("list")
def storage_list():
    """list storages"""
    p.get_storages(output_format="table")


@ha_groups.command("list")
def ha_groups_list():
    """list cluster ha groups"""
    p.get_ha_groups(output_format="table")


@ha_groups.command("create")
def ha_groups_create(
        group: Annotated[str, typer.Option()],
        proxmox_nodes: Annotated[str, typer.Option()],
        restricted: Annotated[bool, typer.Option()] = False,
        nofailback: Annotated[bool, typer.Option()] = False
):
    """create a cluster ha group"""
    p.create_ha_group(
        group=group,
        proxmox_nodes=proxmox_nodes,
        restricted=restricted,
        nofailback=nofailback
    )


@ha_groups.command("delete")
def ha_groups_delete(
    group: Annotated[str, typer.Option()]
):
    """create a cluster ha group"""
    p.delete_ha_group(
        group=group
    )


@ha_resources.command("list")
def ha_resources_list(
    filter_name: Annotated[str, typer.Option()] = ""
):
    """list ha resources"""
    p.get_ha_resources(output_format="table", filter_name=filter_name)


@ha_resources.command("add")
def ha_resources_create(
    group: Annotated[str, typer.Option()],
    name: Annotated[str, typer.Option()] = "",
    vmid: Annotated[int, typer.Option()] = -1,
    comment: Annotated[str, typer.Option()] = "",
    max_relocate: Annotated[int, typer.Option()] = 1,
    max_restart: Annotated[int, typer.Option()] = 1,
    state: Annotated[str, typer.Option()] = "started"
):
    """create an ha resource"""
    p.create_ha_resource(
        name=name,
        vmid=vmid,
        group=group,
        comment=comment,
        max_relocate=max_relocate,
        max_restart=max_restart,
        state=state
    )


@ha_resources.command("delete")
def ha_resources_delete(
    filter_name: Annotated[str, typer.Option()] = "",
    vmid: Annotated[int, typer.Option()] = -1
):
    """delete an ha resource"""
    p.delete_ha_resources(
        filter_name=filter_name,
        vmid=vmid
    )


@ha_resources.command("migrate")
def ha_resources_migrate(
    proxmox_node: Annotated[str, typer.Option()],
    filter_name: Annotated[str, typer.Option()] = "",
    vmid: Annotated[int, typer.Option()] = -1,
    block: Annotated[bool, typer.Option()] = False
):
    """migrate an ha resource"""
    p.migrate_ha_resources(
        filter_name=None if filter_name == "" else filter_name,
        vmid=None if vmid == -1 else vmid,
        proxmox_node=proxmox_node,
        block=block
    )


@ha_resources.command("relocate")
def ha_resources_relocate(
    proxmox_node: Annotated[str, typer.Option()],
    filter_name: Annotated[str, typer.Option()] = "",
    vmid: Annotated[int, typer.Option()] = -1,
    block: Annotated[bool, typer.Option()] = False
):
    """relocate ha resource"""
    p.relocate_ha_resources(
        filter_name=filter_name,
        vmid=vmid,
        proxmox_node=proxmox_node,
        block=block
    )


# VMS #


@vms.command("resize")
def vms_disk_resize(
    size: Annotated[str, typer.Option()],
    vmid: Annotated[int, typer.Option()] = -1,
    vmname: Annotated[str, typer.Option()] = "",
    disk: Annotated[str, typer.Option()] = ""
):
    """resize a vm disk"""
    p.resize_vms_disk(
        vmid=vmid,
        vmname=vmname,
        size=size,
        disk=disk
    )


@vms.command("dump_config")
def vms_dump_config(vmid: str):
    """dump vm config"""
    vm_config = p.get_vms_config(vmid)
    p.output(output_format="json", data=vm_config)


@vms.command("set")
def vms_set(
    vmid: Annotated[int, typer.Option()] = -1,
    vmname: Annotated[str, typer.Option()] = "",
    cores: Annotated[int, typer.Option()] = -1,
    sockets: Annotated[int, typer.Option()] = -1,
    cpulimit: Annotated[int, typer.Option()] = -1,
    memory: Annotated[int, typer.Option()] = -1,
    ipconfig: Annotated[str, typer.Option()] = "",
    cipassword: Annotated[str, typer.Option()] = "",
    citype: Annotated[str, typer.Option()] = "",
    ciuser: Annotated[str, typer.Option()] = "",
    boot: Annotated[str, typer.Option] = "",
    sshkey: Annotated[str, typer.Option] = ""
):
    """set vm parameters"""
    p.set_vms(
        vmid=vmid,
        vmname=vmname,
        cores=cores,
        sockets=sockets,
        cpulimit=cpulimit,
        memory=memory,
        ipconfig=ipconfig,
        cipassword=cipassword,
        ciuser=ciuser,
        citype=citype,
        boot=boot,
        sshkey=sshkey
    )


@vms.command("migrate")
def vms_migrate(
    target_node: Annotated[str, typer.Option()],
    vmid: Annotated[str, typer.Option()] = "",
    filter_name: Annotated[str, typer.Option()] = ""
):
    """migrate vms matching filter to a specified target_node"""
    if not vmid:
        filter_name = "^.*$"
    p.migrate_vms(filter_name=filter_name, proxmox_node=target_node, vmid=vmid)


@vms.command("list")
def vms_list(
    filter_name: str = "^.*",
    output_format: Annotated[str, typer.Option()] = "table",
    proxmox_node: Annotated[str, typer.Option()] = "",
    status: Annotated[str, typer.Option()] = "stopped,running"
):
    """list vms with optional regex filter on name"""
    p.get_vms(
        output_format=output_format,
        filter_name=filter_name,
        proxmox_nodes=proxmox_node,
        status=status
    )


@vms.command("nextId")
def vms_next_id():
    """get the next available vm/container id"""
    print(p.get_next_id())


@vms.command("start")
def vms_start(
    filter_name: Annotated[str, typer.Option()] = "",
    vmid: Annotated[int, typer.Option()] = -1
):
    """start vms based on a regexp filter on name or by vmid"""
    vms_status_apply(
        filter_name,
        vmid,
        "start"
    )


@vms.command("stop")
def vms_stop(
    filter_name: Annotated[str, typer.Option()] = "",
    vmid: Annotated[int, typer.Option()] = -1
):
    """stop vms based on a regexp filter on name or by vmid"""
    vms_status_apply(
        filter_name,
        vmid,
        "stop"
    )


@vms.command("reset")
def vms_reset(
    filter_name: Annotated[str, typer.Option()] = "",
    vmid: Annotated[int, typer.Option()] = -1
):
    """reset vms based on a regexp filter on name or by vmid"""
    vms_status_apply(
        filter_name,
        vmid,
        "reset"
    )


@vms.command("suspend")
def vms_suspend(
    filter_name: Annotated[str, typer.Option()] = "",
    vmid: Annotated[int, typer.Option()] = -1
):
    """reset vms based on a regexp filter on name or by vmid    """
    vms_status_apply(filter_name, vmid, "reset")


@vms.command("clone")
def vms_clone(
    vmid: Annotated[int, typer.Option()],
    name: Annotated[str, typer.Option()],
    vm_description: Annotated[str, typer.Option()] = "",
    full_clone: Annotated[bool, typer.Option()] = False,
    storage: Annotated[str, typer.Option()] = "",
    target: Annotated[str, typer.Option()] = "",
    block: Annotated[bool, typer.Option()] = False,
    duplicate: Annotated[int, typer.Option()] = 1
) -> None:
    """clone an existing vm"""
    p.clone_vm(
        vmid,
        name,
        description=vm_description,
        full=1 if full_clone else 0,
        storage=storage,
        target=target,
        block=block,
        duplicate=duplicate
    )


@vms.command("delete")
def vms_delete(
    filter_name: Annotated[str, typer.Option()] = "",
    vmid: Annotated[int, typer.Option()] = -1,
    confirm: Annotated[bool, typer.Option()] = False,
    block: Annotated[bool, typer.Option()] = False
):
    """delete vms matching regex filter applied on vm name or by vmid.
    vmid and filter are mutualy exclusive"""
    if vmid == -1 and filter_name == "":
        raise proxcli_exceptions.VmIdentificationException()
    if vmid > 0 and filter_name != "":
        raise proxcli_exceptions.VmIdMutualyExclusiveException()
    if not confirm:
        if vmid > 0:
            confirm = typer.confirm(
                f"Do you realy want to delete vm {vmid}"
            )
        if filter_name != "":
            confirm = typer.confirm(
                (
                    f'Do you realy want to delete vms '
                    f'matching filter {filter_name}'
                )
            )
        if not confirm:
            raise typer.Abort()
    p.output(
        output_format="internal",
        data=p.delete_vms(
            fitler_name=filter_name,
            vmid=vmid,
            block=block
        )
    )


def vms_status_apply(filter_name, vmid, status):
    """apply a status to a vm (start, stop, suspend ....)"""
    vmid = None if int(vmid) == -1 else vmid
    if vmid and filter_name:
        print("You can't specify a filter and a vmid at the same time")
    else:
        p.set_vms_status(status=status, filter_name=filter_name, vmid=vmid)


@tags.command("set")
def tags_set(
    vm_tags: Annotated[str, typer.Option()],
    set_mode: Annotated[str, typer.Option()] = "replace",
    filter_name: Annotated[str, typer.Option()] = "^.*"
):
    """set vm tags"""
    p.set_tags(tags=vm_tags, filter_name=filter_name, set_mode=set_mode)


@tags.command("list")
def tags_list():
    """list unique existing tags"""
    p.get_tags()


# NODES #


@nodes.command("list")
def nodes_list(
    filter_name: Annotated[str, typer.Option()] = "^.*",
    output_format: Annotated[str, typer.Option()] = "table"
):
    """list nodes with optional regex filter on name"""
    p.get_nodes(output_format=output_format, filter_name=filter_name)


@networks.command("list")
def networks_list(
    proxmox_nodes: Annotated[str, typer.Option()],
    output_format: Annotated[str, typer.Option()] = "table"
):
    """list all network for a subset of nodes"""

    p.get_nodes_network(
        proxmox_nodes=proxmox_nodes,
        output_format=output_format
    )


@nodes.command("tasks")
def tasks_list(
    proxmox_nodes: Annotated[str, typer.Option()]
):
    """list nodes tasks"""
    p.get_tasks(
        output_format="table",
        proxmox_nodes=proxmox_nodes
    )


# INVENTORY #


@inventory.command("save")
def inventory_save(
    path: Annotated[str, typer.Option()] = "",
    exclude_tag: Annotated[str, typer.Option()] = "",
    filter_name: Annotated[str, typer.Option()] = "",
    output_format: Annotated[str, typer.Option()] = "yaml"
):
    """save ansible inventory"""
    if output_format not in ("json", "yaml"):
        print("Only json and yaml are valid options value for output-format")
        sys.exit(2)
    p.inventory(
        save=path,
        exclude_tag=exclude_tag,
        output_format=output_format,
        filter_name=filter_name
    )


@inventory.command("show")
def inventory_show(
    exclude_tag: Annotated[str, typer.Option()] = "",
    filter_name: Annotated[str, typer.Option()] = "",
    output_format: Annotated[str, typer.Option()] = "yaml"
):
    """display computed ansible inventory"""
    if output_format not in ("json", "yaml"):
        print("Only json and yaml are valid options value for output-format")
        sys.exit(2)
    p.inventory(
        output_format=output_format,
        exclude_tag=exclude_tag,
        filter_name=filter_name
    )


# STORAGES #


@storages.command("upload")
def storages_upload(
    file: Annotated[str, typer.Option()],
    storage: Annotated[str, typer.Option()],
    proxmox_node: Annotated[str, typer.Option()],
    content: Annotated[str, typer.Option()] = "iso",
):
    """upload iso or disk image to proxmox nodes"""
    p.storages_upload(
        file=file,
        storage=storage,
        proxmox_node=proxmox_node,
        content=content
    )


@storages_content.command("list")
def storages_content_list(
    storage: Annotated[str, typer.Option()],
    proxmox_node: Annotated[str, typer.Option()] = "",
    output_format: Annotated[str, typer.Option()] = "table",
    content_type: Annotated[str, typer.Option()] = "",
    content_format: Annotated[str, typer.Option()] = "",
    filter_orphaned: Annotated[str, typer.Option()] = "YES,NO,N/A"
):
    """list storage content"""
    p.get_storage_content(
        proxmox_node=proxmox_node,
        storage=storage,
        content_type=content_type,
        content_format=content_format,
        output_format=output_format,
        filter_orphaned=filter_orphaned
    )


@storages_content.command("clean_orphaned")
def storages_content_clean_orphaned(
    storage: Annotated[str, typer.Option()],
    proxmox_node: Annotated[str, typer.Option()],
    confirm: Annotated[bool, typer.Option()] = True,
    content_type: Annotated[str, typer.Option()] = "",
    content_format: Annotated[str, typer.Option()] = ""
):
    """list storage content"""
    p.clean_orphaned_storage_content(
        proxmox_node=proxmox_node,
        storage=storage,
        confirm=confirm,
        content_type=content_type,
        content_format=content_format,
    )


# MAIN #

if __name__ == "__main__":
    app()
