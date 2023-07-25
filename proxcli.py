#!/usr/bin/env python
import typer
from typing_extensions import Annotated
from proxmoxlib import proxmox

app = typer.Typer(no_args_is_help=True)
vms = typer.Typer(no_args_is_help=True)
containers = typer.Typer(no_args_is_help=True)
nodes = typer.Typer(no_args_is_help=True)
storages = typer.Typer(no_args_is_help=True)
config = typer.Typer(no_args_is_help=True)
networks = typer.Typer(no_args_is_help=True)
tasks = typer.Typer(no_args_is_help=True,pretty_exceptions_enable=False,pretty_exceptions_short=False)

vms_status = typer.Typer(no_args_is_help=True)

containers_status = typer.Typer(no_args_is_help=True)

inventory = typer.Typer(no_args_is_help=True)
tags = typer.Typer(no_args_is_help=True)

app.add_typer(vms, name="vms")
app.add_typer(containers, name="containers", help="Containers related functions")
app.add_typer(nodes, name="nodes", help="Nodes related functions")
app.add_typer(inventory, name="inventory", help="Ansible inventory related functions")
app.add_typer(storages, name="storages")
app.add_typer(config, name="config")
app.add_typer(tasks, name="tasks")

nodes.add_typer(networks, name="networks")
vms.add_typer(tags, name="tags", help="vms and containers tags related functions")
p = proxmox()

### CONFIG ####

@config.command("show")
def config_show():
    # display current config if exist
    p.dump_config()

@config.command("create")
def config_create(hosts: Annotated[str, typer.Option()], user: Annotated[str, typer.Option()], password: Annotated[str, typer.Option()]):
    # generate config
    p.create_config(hosts, user, password)

### STORAGE ###

@storages.command("list")
def storage_list():
    # list storages
    p.get_storages(format="table")

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
    print(p.get_next_id(max=1000))

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
