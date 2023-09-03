#!/usr/bin/env python
import typer
from typing_extensions import Annotated
from proxmoxlib import proxmox
import os

app = typer.Typer(no_args_is_help=True)
vms = typer.Typer(no_args_is_help=True)
containers = typer.Typer(no_args_is_help=True)
nodes = typer.Typer(no_args_is_help=True)
storages = typer.Typer(no_args_is_help=True)
config = typer.Typer(no_args_is_help=True)
networks = typer.Typer(no_args_is_help=True)
tasks = typer.Typer(no_args_is_help=True,pretty_exceptions_enable=False,pretty_exceptions_short=False)
cluster = typer.Typer(no_args_is_help=True)
ha = typer.Typer(no_args_is_help=True)
ha_groups = typer.Typer(no_args_is_help=True)
ha_resources = typer.Typer(no_args_is_help=True)
vms_status = typer.Typer(no_args_is_help=True)
replications = typer.Typer(no_args_is_help=True)
containers_status = typer.Typer(no_args_is_help=True)
access = typer.Typer(no_args_is_help=True)

permissions = typer.Typer(no_args_is_help=True)
groups = typer.Typer(no_args_is_help=True)
users = typer.Typer(no_args_is_help=True)
roles = typer.Typer(no_args_is_help=True)
acl = typer.Typer(no_args_is_help=True)
password = typer.Typer(no_args_is_help=True)
ticket = typer.Typer(no_args_is_help=True)

inventory = typer.Typer(no_args_is_help=True)
tags = typer.Typer(no_args_is_help=True)

access.add_typer(groups, name="groups")
access.add_typer(users, name="users")
access.add_typer(roles, name="roles")
access.add_typer(acl, name="acl")
access.add_typer(password, name="password")
access.add_typer(permissions, name="permissions")
access.add_typer(ticket, name="ticket")

app.add_typer(vms, name="vms")
app.add_typer(containers, name="containers", help="Containers related functions")
app.add_typer(nodes, name="nodes", help="Nodes related functions")
app.add_typer(inventory, name="inventory", help="Ansible inventory related functions")
app.add_typer(config, name="config")
app.add_typer(tasks, name="tasks")
app.add_typer(cluster, name="cluster")
app.add_typer(replications, name="replications")
app.add_typer(access, name="access")

nodes.add_typer(networks, name="networks")
vms.add_typer(tags, name="tags", help="vms and containers tags related functions")

ha.add_typer(ha_groups, name="groups", help="manage ha groups")
ha.add_typer(ha_resources, name="resources", help="manage ha resources")

cluster.add_typer(storages, name="storages", help="cluster storage commands")
cluster.add_typer(ha, name="ha", help="high availibility commands")

p = proxmox()

### PERMISSIONS ###

# @roles.command("list")
# def roles_list(
#     format: Annotated[str, typer.Option()] = "table"
# ):
#     p.list_roles(format=format)


# @acl.command("list")
# def acl_list(
#     format: Annotated[str, typer.Option()] = "table"
# ):
#     p.list_acl(format=format)

# @acl.command("path")
# def acl_path():
#     print(", ".join(p.acl_path_list()))

# @acl.command("create")
# def acl_create(
#     path: Annotated[str,typer.Option()],
#     roles: Annotated[str,typer.Option()],
#     groups: Annotated[str,typer.Option()] = "",
#     propagate: Annotated[bool,typer.Option()] = True,
#     tokens: Annotated[str,typer.Option()] = "",
#     users: Annotated[str,typer.Option()] = ""
# ):
#     p.create_acl(
#         path=path,
#         roles=roles,
#         groups=groups,
#         propagate=propagate,
#         tokens=tokens,
#         users=users
#     )

# @users.command("list")
# def users_list(
#     format: Annotated[str, typer.Option()] = "table"
# ):
#     p.list_users(format=format)

# @users.command("create")
# def users_create(
#     name: str,
#     password: Annotated[str, typer.Option()] = "",
#     firstname: Annotated[str, typer.Option()] = "",
#     lastname: Annotated[str, typer.Option()] = "",
#     comment: Annotated[str, typer.Option()] = "",
#     email: Annotated[str, typer.Option()] = "",
#     enable: Annotated[bool, typer.Option()] = True,
#     expire: Annotated[int, typer.Option()] = 0,
#     groups: Annotated[str, typer.Option()] = "",
#     keys: Annotated[str, typer.Option()] = "" 
# ):
#     p.create_user(
#         name=name, password=password,
#         firstname=firstname, lastname=lastname,
#         comment=comment, email=email,
#         enable=enable, expire=expire,
#         groups=groups,keys=keys
#     )

# @users.command("password")
# def users_password(
#     name: str,
#     password: str
# ):
#     p.update_password(name=name, password=password)

# @users.command("update")
# def users_update(
#     name: str,
#     firstname: Annotated[str, typer.Option()] = "",
#     lastname: Annotated[str, typer.Option()] = "",
#     comment: Annotated[str, typer.Option()] = "",
#     email: Annotated[str, typer.Option()] = "",
#     enable: Annotated[bool, typer.Option()] = True,
#     expire: Annotated[int, typer.Option()] = 0,
#     groups: Annotated[str, typer.Option()] = "",
#     keys: Annotated[str, typer.Option()] = "" 
# ):
#     p.update_user(
#         name=name,
#         firstname=firstname, lastname=lastname,
#         comment=comment, email=email,
#         enable=enable, expire=expire,
#         groups=groups,keys=keys
#     )

# @users.command("delete")
# def users_delete(name: str):
#     p.delete_user(name=name)

# @groups.command("list")
# def groups_list(
#     format: Annotated[str, typer.Option()] = "table"
# ):
#     p.list_groups(format=format)

# @groups.command("create")
# def groups_create(
#     name: str,
#     comment: Annotated[str, typer.Option()] = ""
# ):
#     p.create_group(comment=comment, name=name)

# @groups.command("delete")
# def groups_list(
#     name: str
# ):
#     p.delete_group(name=name)

# @groups.command("update")
# def groups_list(
#     name: str,
#     comment: Annotated[str, typer.Option()] = "",
#     users: Annotated[str, typer.Option()] = ""
# ):
#     p.update_group(name=name, comment=comment)


### CONFIG ####

@config.command("show")
def config_show():
    # display current config if exist
    p.dump_config()

@config.command("create")
def config_create(
    hosts: Annotated[str, typer.Option()], 
    user: Annotated[str, typer.Option()], 
    password: Annotated[str, typer.Option()]
):
    # generate config
    p.create_config(hosts=hosts, user=user, password=password)

### CLUSTER ###

@cluster.command("status")
def cluster_status(format: str = "table"):
    p.get_cluster_status(format=format)

@cluster.command("log")
def cluster_log(
    out: str = "table", 
    max: int = 100,
    nodes: str = "pve1,pve2,pve3",
    severities: str = "panic,alert,critical,error,warning,notice,info,debug"
):
    # show cluster log
    p.get_cluster_log(format=out, max=max, nodes=nodes,severities=severities)

@storages.command("list")
def storage_list():
    # list storages
    p.get_storages(format="table")

@ha_groups.command("list")
def ha_groups_list():
    # list cluster ha groups
    p.get_ha_groups(format="table")

@ha_groups.command("create")
def ha_groups_create(
        group: Annotated[str, typer.Option()],
        nodes: Annotated[str, typer.Option()],
        restricted: Annotated[str, typer.Option()] = False,
        nofailback: Annotated[bool, typer.Option()] = False
    ):
    # create a cluster ha group
    p.create_ha_group(
        group=group,
        nodes=nodes,
        restricted=restricted,
        nofailback=nofailback
    )

@ha_groups.command("delete")
def ha_groups_delete(
        group: Annotated[str, typer.Option()]
    ):
    # create a cluster ha group
    p.delete_ha_group(
        group=group
    )

@ha_resources.command("list")
def ha_resources_list():
    p.get_ha_resources()

@ha_resources.command("add")
def ha_resources_add(
    group: Annotated[str, typer.Option()],
    filter: Annotated[str, typer.Option()] = None,
    vmid: Annotated[int, typer.Option()] = None,
    comment: Annotated[str, typer.Option()] = "",
    max_relocate: Annotated[int, typer.Option()] = 1,
    max_restart: Annotated[int, typer.Option()] = 1,
    state: Annotated[str, typer.Option()] = "started"
    ):
    p.add_ha_resources(
        filter = filter,
        vmid = vmid,
        group = group,
        comment = comment,
        max_relocate = max_relocate,
        max_restart = max_restart,
        state = state
    )

@ha_resources.command("delete")
def ha_resources_delete(
    filter: Annotated[str, typer.Option()] = None,
    vmid: Annotated[int, typer.Option()] = None
):
    p.delete_ha_resources(filter=filter, vmid=vmid)

@ha_resources.command("migrate")
def ha_resources_migrate(
    node: Annotated[str, typer.Option()],
    filter: Annotated[str, typer.Option()] = None,
    vmid: Annotated[int, typer.Option()] = None
):
    p.migrate_ha_resources(filter=filter, vmid=vmid, node=node)

@ha_resources.command("relocate")
def ha_resources_relocate(
    node: Annotated[str, typer.Option()],
    filter: Annotated[str, typer.Option()] = None,
    vmid: Annotated[int, typer.Option()] = None
):
    p.relocate_ha_resources(filter=filter, vmid=vmid, node=node)


### CONTAINERS ###
# containers dev stopped until i found a way to get containers ip address
# @containers.command("list")
# def containers_list(filter: str = "^.*", out: str = "table"):
#     # list containers with optional regex filter on name
#     p.get_containers(format=out, filter=filter)

# @containers.command("nextId")
# def containers_next_id():
#     """get the next available vm/container id"""
#     print(p.get_next_id(max=1000))

# @containers_status.command("stop")
# def containers_stop(filter: Annotated[str, typer.Option()] = "^.*", vmid: Annotated[int, typer.Option()] = None):
#     if id:
#         # TODO: stop container by id
#         pass
#     else:
#         # stop vms matching filter (regex) on name
#         p.status_containers("stop", filter=filter)

# @containers_status.command("start")
# def containers_start(filter: Annotated[str, typer.Option()] = "^.*", vmid: Annotated[int, typer.Option()] = None):
#     if id:
#         # TODO: start container by id
#         pass
#     else:
#         # start vms matching filter (regex) on name
#         p.status_containers("start", filter=filter)

### VMS ###

@vms.command("resize")
def vms_disk_resize(
    size: Annotated[str, typer.Option()],
    vmid: Annotated[int, typer.Option()] = None,
    vmname: Annotated[int, typer.Option()] = None,
    disk: Annotated[str, typer.Option()] = None
    
):
    p.vms_resize_disk(
        vmid=vmid,
        vmname=vmname,
        size=size,
        disk=disk
    )

@vms.command("dump_config")
def vms_dump_config(vmid: str):
    config = p.vms_config_get(vmid)
    p.output(format="json", data=config)

@vms.command("set")
def vms_set(
    vmid: Annotated[int, typer.Option()] = None,
    vmname: Annotated[str, typer.Option()] = None,
    cores: Annotated[int, typer.Option()] = None,
    sockets: Annotated[int, typer.Option()] = None,
    cpulimit: Annotated[int, typer.Option()] = None,
    memory: Annotated[int, typer.Option()] = None,
    ipconfig: Annotated[str, typer.Option()] = None, 
    cipassword: Annotated[str, typer.Option()] = None, 
    citype: Annotated[str, typer.Option()] = None, 
    ciuser: Annotated[str, typer.Option()] = None    
):
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
        citype=citype
    )

@vms.command("migrate")
def vms_migrate(target_node: Annotated[str, typer.Option()], vmid: Annotated[str, typer.Option()] = None, filter: Annotated[str, typer.Option()] = None):
    # migrate vms matching filter to a specified target_node
    if not vmid:
        filter = "^.*$"
    p.migrate_vms(filter=filter, target_node=target_node, vmid=vmid)

@vms.command("list")
def vms_list(filter: str = "^.*", out: str = "table", nodes: str = None, status: str = "stopped,running"):
    """list vms with optional regex filter on name"""
    p.get_vms(format=out, filter=filter, nodes=nodes, status=status)

@vms.command("nextId")
def vms_next_id():
    """get the next available vm/container id"""
    print(p.get_next_id())

@vms.command("start")
def vms_status(filter: Annotated[str, typer.Option()] = None, vmid: Annotated[int, typer.Option()] = None):
    # start vms based on a regexp filter on name or by vmid
    vms_status_apply(filter, vmid, "start")

@vms.command("stop")
def vms_status(filter: Annotated[str, typer.Option()] = None, vmid: Annotated[int, typer.Option()] = None):
    # stop vms based on a regexp filter on name or by vmid    
    vms_status_apply(filter, vmid, "stop")

@vms.command("reset")
def vms_status(filter: Annotated[str, typer.Option()] = None, vmid: Annotated[int, typer.Option()] = None):
    # reset vms based on a regexp filter on name or by vmid    
    vms_status_apply(filter, vmid, "reset")

@vms.command("suspend")
def vms_status(filter: Annotated[str, typer.Option()] = None, vmid: Annotated[int, typer.Option()] = None):
    # reset vms based on a regexp filter on name or by vmid    
    vms_status_apply(filter, vmid, "reset")

@vms.command("clone")
def vms_clone(
    vmid: Annotated[int, typer.Option()], 
    name: Annotated[str, typer.Option()], 
    description: Annotated[str, typer.Option()] = "", 
    full: Annotated[bool, typer.Option("--full")] = False,
    storage: Annotated[str, typer.Option()] = None,
    target: Annotated[str, typer.Option()] = None,
    block: Annotated[bool, typer.Option("--block")] = False,
    duplicate: Annotated[int, typer.Option("--duplicate")] = None
):
    # clone an existing vm
    data=p.clone_vm(
        vmid, 
        name, 
        description=description, 
        full=1, 
        storage=storage, 
        target=target, 
        block=block, 
        duplicate=duplicate
    )
    p.output(format="internal", data=data)

@vms.command("delete")
def vms_delete(
    filter: Annotated[str, typer.Option()] = None, 
    vmid: Annotated[int, typer.Option()] = None, 
    confirm: Annotated[bool, typer.Option("--confirm")] = False,
    block: Annotated[bool, typer.Option("--block")] = False):
    # delete vms matching regex filter applied on vm name or by vmid.
    # vmid and filter are mutualy exclusive
    if not vmid and not filter:
        raise Exception("You must specify one of vmid or filter options")
    if vmid and filter:
        raise Exception("vmid and filter options are mutualy exclusive")
    if not confirm: 
        if vmid: 
            confirm = typer.confirm("Do you realy want to delete vm %s" % vmid)
        if filter:
            confirm = typer.confirm("Do you realy want to delete vms matching filter %s" % filter)
    if not confirm:
        raise typer.Abort()
    else:
        p.output(format="internal", data=p.delete_vms(filter=filter, vmid=vmid, block=block))

def vms_status_apply(filter, vmid, status):
    if vmid and filter:
        print("You can't specify a filter and a vmid at the same time")
        typer.Exit(2)
    else:
        p.status_vms(status=status, filter=filter, vmid=vmid)

@tags.command("set")
def tags_set(tags: str, filter: Annotated[str, typer.Option()] = "^.*"):
    p.set_tags(tags=tags, filter=filter)

@tags.command("list")
def tags_list():
    p.list_tags()

### NODES ###

@nodes.command("list")
def nodes_list(filter: str = "^.*", out: str = "table"):
    # list nodes with optional regex filter on name
    p.get_nodes(format=out, filter=filter)

@nodes.command("networks")
def networks_list(nodes: Annotated[str, typer.Option()], types: Annotated[str, typer.Option()] = "bridge,bond,eth,alias,vlan,OVSBridge,OVSBond,OVSPort,OVSIntPort,any_bridge,any_local_bridge", out: Annotated[str,typer.Option()] = "table"):
    # list all network for a subset of nodes
    p.get_networks(format=out, nodes=nodes, types=types)

@nodes.command("tasks")
def tasks_show(nodes: Annotated[str, typer.Option()] = None):
    p.get_tasks(format="table",nodes=nodes)


### INVENTORY ###

@inventory.command("save")
def inventory_save(path: str, out: Annotated[str, typer.Option()] = "yaml"):
    p.inventory(save=path, format=out)

@inventory.command("show")
def inventory_show(out: Annotated[str, typer.Option()] = "yaml"):
    p.inventory(format=out)

### MAIN ###

if __name__ == "__main__":
    app()
