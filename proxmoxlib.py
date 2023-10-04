#!/usr/bin/env python
"""proxmoxlib module for managing promox cluster remotely"""
from datetime import datetime
import enum
import inspect
from typing import Any
from urllib import parse as urllib_parse
import json
import re
import os
import configparser
import shutil
import yaml
import requests
from beautifultable import BeautifulTable
import urllib3
from termcolor import colored
from rich import print as rprint
from proxmoxer import ResourceException
from proxmoxer import ProxmoxAPI
from proxmoxer.tools import Tasks
import proxcli_exceptions

urllib3.disable_warnings()


class Proxmox():
    """proxmox api helper"""
    def __init__(self) -> None:
        result = self.load_config()
        self.host = ""
        if result:
            self.proxmox_instance = self.proxmox()

    # UTILITY #

    def get_terminal_width(self) -> int:
        """shortcut to shutil.get_terminal_size()[0]"""
        return shutil.get_terminal_size()[0]

    def get_caller(self) -> str:
        """get the calling method"""
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        print(calframe)
        return calframe[1][3]

    def load_config(self) -> bool:
        """load configuration"""
        configfile = os.path.expanduser('~') + "/.proxmox"
        if os.path.exists(configfile):
            config = configparser.ConfigParser()
            config.read(os.path.abspath(configfile))
            self.username = config["credentials"]["user"]
            self.password = config["credentials"]["password"]
            self.hosts = config["credentials"]["hosts"].split(",")
            headers = config["headers"]
            self.headers_nodes = headers["nodes"].split(",")
            self.headers_qemu = headers["qemu"].split(",")
            self.headers_lxc = headers["lxc"].split(",")
            self.headers_storage = headers["storage"].split(",")
            self.headers_tasks = headers["tasks"].split(",")
            self.headers_ha_groups = headers["ha_groups"].split(",")
            self.headers_ha_resources = headers["ha_resources"].split(",")
            self.headers_cluster_log = headers["cluster_log"].split(",")
            self.headers_cluster_status = headers["cluster_status"].split(",")
            self.headers_cluster_status_node = headers[
                "cluster_status_node"
            ].split(",")
            self.headers_node_networks = headers["node_networks"].split(",")
            self.table_style = self.get_table_style(config["data"]["style"])
            self.task_polling_interval = config["tasks"]["polling_interval"]
            self.task_timeout = config["tasks"]["timeout"]
            self.table_colorize = dict(
                [v.split(':') for v in config["data"]["colorize"].split(",")]
            )
            return True
        else:
            return False

    def select_active_node(self) -> None:
        """
        select the first available node
        iterate over nodes, ping and set self.host property
        """
        for host in self.hosts:
            values = (host,)
            url = f"https://{values[0]}:8006"
            try:
                requests.get(
                    url,
                    timeout=1,
                    allow_redirects=True,
                    verify=False
                )
                self.host = host
                break
            finally:
                pass

    def get_table_style(self, style) -> enum.Enum:
        """set beautiful table display style from string"""
        if hasattr(BeautifulTable, style):
            selected_style = getattr(BeautifulTable, style)
        else:
            selected_style = getattr(BeautifulTable, "STYLE_BOX")
        return selected_style

    def output(
            self,
            data,
            headers=None,
            output_format="internal",
            save=False
    ) -> Any:
        """
        print data on specified format
        default to internal (raw data is returned instead of displaying)
        """
        # immediately return data if using for internal use
        if output_format == "internal":
            return data

        if output_format == "json":
            data = json.dumps(data, indent=2)
        elif output_format == "yaml":
            data = yaml.dump(data)
        elif output_format == "table":
            data = self.table(headers=headers, data=data)

        if save:
            with open(file=save, encoding="utf-8", mode="w") as handle:
                handle.write(str(data))
                handle.close()
        else:
            if output_format == "yaml" or output_format == "json":
                rprint(data)
            else:
                print(data)

    def readable_date(self, timestamp) -> str:
        """convert unix timestamp to human readable date time"""
        return datetime.utcfromtimestamp(
            timestamp).strftime('%Y-%m-%d %H:%M:%S')

    def table(self, headers, data, width=None) -> BeautifulTable:
        """
        Display list of dict as table
        """
        width = self.get_terminal_width() if not width else width
        table = BeautifulTable(maxwidth=width)
        table.set_style(self.table_style)
        table.columns.header = headers
        for element in data:
            datarow = []
            for header in headers:
                if header in element:
                    datarow.append(element[header])
                else:
                    datarow.append('')
            new_data_row = []
            for cell in datarow:
                if len(str(cell)) > 0:
                    words = list(self.table_colorize.keys())
                    match = [word for word in words if word in str(cell)]
                    if len(match) == 1:
                        new_data_row.append(
                            colored(cell, self.table_colorize[match[0]]))
                    else:
                        new_data_row.append(cell)
                else:
                    new_data_row.append("")
            table.rows.append(tuple(new_data_row))
        return table

    def ismatching(self, regex, data) -> bool:
        """shortcut method used to check is a string match a regex"""
        if not re.match(regex, data):
            return False
        else:
            return True

    def task_block(self, task) -> Any:
        """
        Poll a task until the task is finished or timed out
            Paramaters:
                task (str): a task identifier
                UPID:<n>:<ph>:<ps>:<st>:<t>:<id>:<u>@<r>:)
                n: node name
                ph: pid in hex format
                ps: pstart in hex
                st: start tim in hex
                t: type
                id: id (optional)
                u: user
                r: realm
            Returns:
                result (dict): a dict with all the task information
                https://proxmoxer.github.io/docs/2.0/tools/tasks/#blocking_status
        """
        print(f"Waiting for task {(task,)} to finish")
        return Tasks.blocking_status(
            prox=self.proxmox_instance,
            task_id=task,
            timeout=int(self.task_timeout),
            polling_interval=float(self.task_polling_interval))

    def proxmox(self) -> ProxmoxAPI:
        """create proxmox api instance from the first available node found"""
        self.select_active_node()
        return ProxmoxAPI(
            self.host,
            user=self.username,
            password=self.password,
            verify_ssl=False
        )

    # STORAGE #
    def storages_upload(
        self,
        file,
        node,
        storage,
        content
    ) -> None:
        """upload image or iso file to proxmox node"""
        with open(str(file), 'rb') as file_handler:
            storage = self.proxmox_instance.nodes(node).storage(storage)
            storage.upload.post(content=content, filename=file_handler)

    # CLUSTER #

    def get_cluster_status(self, output_format="internal") -> None:
        """Description of the function/method.

        Parameters:
            <param>: Description of the parameter

        Returns:
            <variable>: Description of the return value
        """
        status = []
        status = self.proxmox_instance.cluster.status.get()
        if isinstance(status, list):
            cluster_status = [
                c for c in status if c["type"] == "cluster"]
            cluster_status_node = [
                c for c in status if c["type"] == "node"]

            self.output(
                output_format=output_format,
                headers=self.headers_cluster_status,
                data=cluster_status
            )
            self.output(
                output_format=output_format,
                headers=self.headers_cluster_status_node,
                data=cluster_status_node)

    def get_cluster_log(
            self,
            nodes,
            severities,
            output_format="internal",
            max_items=100
    ) -> Any:
        """get cluster logs

        Args:
            format (str, optional): _description_. Defaults to "internal".
            max (int, optional): _description_. Defaults to 100.
        """

        translate_severity = {
            '0': "panic",
            '1': "alert",
            '2': "critical",
            '3': "error",
            '4': "warning",
            '5': "notice",
            '6': "info",
            '7': "debug"
        }
        logs = self.proxmox_instance.cluster.log.get(**{'max': max_items})
        if not logs:
            logs = []
        nodes = [n.strip() for n in nodes.split(",")]
        severities = [s.strip() for s in severities.split(",")]
        filtered_logs = []
        for log in logs:
            log["severity"] = translate_severity[str(log["pri"])]
            log["date"] = self.readable_date(log["time"])
            if log["severity"] in severities:
                if len(nodes) == 0:
                    filtered_logs.append(log)
                else:
                    if log["node"] in nodes:
                        filtered_logs.append(log)

        if len(filtered_logs) == 0:
            return

        return self.output(
            headers=self.headers_cluster_log,
            data=filtered_logs,
            output_format=output_format
        )

    def get_ha_groups(self, output_format="internal") -> Any:
        """list cluster ha groups"""
        hagroups = self.proxmox_instance.cluster.ha.groups.get()
        return self.output(
            headers=self.headers_ha_groups,
            data=hagroups,
            output_format=output_format
        )

    def create_ha_group(
            self,
            group,
            nodes,
            nofailback=False,
            restricted=False
    ) -> None:
        """
            create a hagroup
            Parameters:
                group (str): the ha group name
                nodes (str): List of cluster node members
                nofailback (bool):
                restricted (bool):
                type (enum):
            Returns:
                result (bool): true if success, false if failure
        """

        nofailback = 0 if nofailback is False else 1
        restricted = 0 if restricted is False else 1
        self.proxmox_instance.cluster.ha.groups.post(**{
            "group": group,
            "nodes": nodes,
            "nofailback": nofailback,
            "restricted": restricted
        })

    def delete_ha_group(self, group) -> None:
        """delete cluster ha group

        Args:
            group (str): cluster ha group name to delete
        """
        self.proxmox_instance.cluster.ha.groups.delete(group)

    def get_ha_resources(
            self,
            output_format="table",
            filter_name="^.*$"
    ) -> Any:
        """retrieve a list of cluster ha resources with named cluster ha groups

        Returns:
            list: list of ha resources
        """
        resources = self.proxmox_instance.cluster.ha.resources.get()
        if not resources:
            resources = []
        for resource in resources:
            vmid = resource["sid"].split(":")[-1]
            virtual_machine = self.get_vm_by_id_or_name(vmid=vmid)
            resource["name"] = virtual_machine["name"]
            resource["vmid"] = vmid
        resources = [r for r in resources if re.match(filter_name, r["name"])]
        return self.output(
            headers=self.headers_ha_resources,
            data=resources,
            output_format=output_format
        )

    def create_ha_resource(
            self,
            group,
            name=None,
            vmid=None,
            comment="",
            max_relocate=1,
            max_restart=1,
            state="started"
    ) -> None:
        """add a resource to ha group"""
        if name:
            vms = self.get_vms(
                output_format="internal",
                filter_name=name
            )
            vms = [] if not vms else vms
            for virtual_machine in vms:
                print(
                    (
                        f"Adding resource {(virtual_machine['vmid'],)} "
                        f"to group {(group,)}"
                    )
                )
                self.proxmox_instance.cluster.ha.resources.post(**{
                    'sid': virtual_machine["vmid"],
                    'comment': comment,
                    'group': group,
                    'max_relocate': max_relocate,
                    'max_restart': max_restart,
                    'state': state
                })
        if vmid:
            print(f"Adding resource {(vmid,)} to group {(group,)}")
            self.proxmox_instance.cluster.ha.resources.post(**{
                'sid': str(vmid),
                'comment': comment,
                'group': group,
                'max_relocate': max_relocate,
                'max_restart': max_restart,
                'state': state
            })

    def vm_ha_resource_managed(self, vmid):
        """checker if a vm is ha managed"""
        resources = self.get_ha_resources(output_format="internal")
        resources = [str(r["vmid"]) for r in resources]
        return True if str(vmid) in resources else False

    def delete_ha_resources(self, filter_name=None, vmid=None) -> None:
        """delete resource from ha group"""
        if filter_name:
            resources = self.get_ha_resources(
                output_format="internal",
                filter_name=filter_name
            )
            for resource in resources:
                if int(resource["vmid"]) > 0:
                    print(f"Removing resource {(resource['vmid'],)}")
                    ha_endpoint = self.proxmox_instance.cluster.ha
                    ha_endpoint.resources.delete(resource["vmid"])

        if vmid > 0:
            print(f"Removing resource {(vmid,)}")
            self.proxmox_instance.cluster.ha.resources.delete(vmid)

    def migrate_ha_resources(
            self,
            proxmox_node=None,
            filter_name=None,
            vmid=None,
            block=False,
            block_max_try=3
    ) -> None:
        """migrate a resource from ha group"""
        resources = []
        if filter_name and filter_name != "":
            resources = self.get_ha_resources(
                output_format="internal",
                filter_name=filter_name
            )
            resources = [] if not resources else resources
        if vmid and vmid > 0:
            resources = [self.get_resource_by_id_or_name(vmid=vmid)]

        for resource in resources:
            print(
                (
                    f"migrating resource {(resource['vmid'],)} "
                    f"to node {(proxmox_node,)}"
                )
            )
            ha_group = self.proxmox_instance.cluster.ha
            ha_group.resources(resource["vmid"]).migrate.post(
                **{'node': proxmox_node})
            if block:
                current_try = 0
                current_node = "unknown"
                virtual_machine_status = "unknown"
                print("Waiting for migration to finish")
                while (
                    current_node != proxmox_node or
                    virtual_machine_status != "running" or
                    current_try < block_max_try
                ):
                    resource = self.get_vm_by_id_or_name(
                        vmid=resource["vmid"]
                    )
                    if resource and resource["node"] != proxmox_node:
                        vmid = resource["vmid"]
                        virtual_machine_status = resource["status"]
                    else:
                        break
                    current_try += 1

    def get_resource_by_id_or_name(self, vmid=None, resource_name=None) -> Any:
        """get reosurce by its id or name"""
        resources = self.get_ha_resources(output_format="internal")
        resources = [] if not resources else resources
        if vmid:
            resource = [v for v in resources if v["vmid"] == int(vmid)]
        else:
            resource = [v for v in resources if v["name"] == resource_name]
        if len(resource) == 0:
            return False
        return resource[0]

    def relocate_ha_resources(
            self,
            proxmox_node,
            filter_name=None,
            vmid=None,
            block=False,
            block_max_try=3
    ) -> None:
        """relocate ha resource"""
        print((
            f"node {proxmox_node} "
            f"filter {filter_name} "
            f"id {vmid} "
            f"block {block}"
        ))
        resources = []
        if filter_name and filter_name != "":
            resources = self.get_ha_resources(
                output_format="internal",
                filter_name=filter_name
            )
            resources = [] if not resources else resources
        if vmid and vmid > 0:
            resources = [self.get_resource_by_id_or_name(vmid=vmid)]

        for resource in resources:
            print(
                (
                    f"relocating resource {(resource['vmid'],)} "
                    f"to node {(proxmox_node,)}"
                )
            )
            ha_group = self.proxmox_instance.cluster.ha
            ha_group.resources(resource["vmid"]).relocate.post(
                **{'node': proxmox_node})
            if block:
                current_try = 0
                current_node = "unknown"
                virtual_machine_status = "unknown"
                print("Waiting for relocation to finish")
                while (
                    current_node != proxmox_node or
                    virtual_machine_status != "running" or
                    current_try < block_max_try
                ):
                    resource = self.get_vm_by_id_or_name(
                        vmid=resource["vmid"]
                    )
                    if resource and resource["node"] != proxmox_node:
                        vmid = resource["vmid"]
                        virtual_machine_status = resource["status"]
                    else:
                        break
                    current_try += 1

    def get_storages(self, output_format="json") -> Any:
        """list storages"""
        # nodes = self.get_nodes(format="internal")
        # nodes = [] if not nodes else nodes
        # available_nodes = [n for n in nodes if n["status"] == "online"]
        # if len(available_nodes) > 0:
        #     query_node = available_nodes[0]
        # else:
        #     raise ProxmoxClusterDownException

        all_storages = []

        storages = self.proxmox_instance.storage.get()
        storages = [] if not storages else storages
        for storage in storages:
            all_storages.append(storage)
        return self.output(
            headers=self.headers_storage,
            data=all_storages,
            output_format=output_format
        )

    # NODES #

    def get_nodes(
            self,
            output_format="internal",
            filter_name=None
    ) -> Any:
        '''
        Get all node as a list

            Parameters:
                TODO
            Returns:
                TODO

        '''
        proxmox_nodes = self.proxmox_instance.nodes.get()
        proxmox_nodes = [] if not proxmox_nodes else proxmox_nodes
        if filter_name:
            proxmox_nodes = [
                n for n in list(proxmox_nodes) if self.ismatching(
                    filter_name, n["node"]
                )
            ]

        return self.output(
            headers=self.headers_nodes,
            data=proxmox_nodes,
            output_format=output_format
        )

    def get_tasks(
            self,
            output_format="internal",
            errors=0,
            limit=50,
            source="all",
            proxmox_nodes=None
    ) -> Any:
        """get tasks from nodes"""
        available_nodes = self.get_nodes(output_format="internal")
        available_nodes = [
            n["node"] for n in available_nodes if n["status"] == "online"]
        if not proxmox_nodes:
            proxmox_nodes = available_nodes
        else:
            proxmox_nodes = proxmox_nodes.split(",")
            proxmox_nodes = [n for n in proxmox_nodes if n in available_nodes]

        tasks = []
        for node in proxmox_nodes:
            node_tasks = self.proxmox_instance.nodes(node).tasks.get(**{
                "errors": errors,
                "limit": limit,
                "source": source,
                "vmid": None
            })
            node_tasks = [] if not node_tasks else node_tasks
            tasks += node_tasks
        tasks = [t for t in tasks if t["node"] in proxmox_nodes]
        tasks = sorted(tasks, key=lambda d: d['starttime'], reverse=True)
        for node_tasks in tasks:
            node_tasks['starttime'] = self.readable_date(
                node_tasks['starttime'])
            if 'endtime' in node_tasks:
                node_tasks['endtime'] = self.readable_date(
                    node_tasks['endtime'])
            else:
                node_tasks['endtime'] = ""
        self.output(
            headers=self.headers_tasks,
            data=tasks,
            output_format=output_format
        )

    def get_nodes_network(
            self,
            nodes=None,
            output_format="table"
    ) -> Any:
        """get the default ip address from a node"""
        if not nodes:
            return []
        nodes = nodes.split(",")
        networks = []
        for node in nodes:
            result = self.proxmox_instance.nodes(node).network.get()
            result = [] if not result else result
            for net in result:
                net["node"] = node
                networks.append(net)
        self.output(
            data=networks,
            output_format=output_format,
            headers=self.headers_node_networks
        )

    # VMS #

    def get_vm_by_id_or_name(self, vmid=None, vmname=None) -> Any:
        """get vm by its id or name"""
        vms = self.get_vms(output_format="internal")
        vms = [] if not vms else vms
        virtual_machine = None
        if vmid:
            virtual_machine = [v for v in vms if v["vmid"] == int(vmid)]
        else:
            virtual_machine = [v for v in vms if v["name"] == vmname]
        if len(virtual_machine) == 0:
            return False
        return virtual_machine[0]

    def get_vms_config(self, vmid) -> Any:
        """get virtual machine config"""
        virtual_machine = self.get_vm_by_id_or_name(vmid=vmid)
        virtual_machine = {} if not virtual_machine else virtual_machine
        node = virtual_machine["node"]
        vmid = virtual_machine["vmid"]
        config = self.proxmox_instance.get(
            f"nodes/{node}/qemu/{vmid}/config"
        )
        return config

    def resize_vms_disk(self, size, vmid=None, vmname=None, disk=None) -> None:
        """resize the first virtual machine disk"""
        virtual_machine = self.get_vm_by_id_or_name(vmid, vmname)
        if not virtual_machine:
            raise proxcli_exceptions.ProxmoxVmNotFoundException
        node = virtual_machine["node"]
        vmid = virtual_machine["vmid"] if not vmid else vmid
        config = self.get_vms_config(vmid)
        if not config:
            raise proxcli_exceptions.ProxmoxVmConfigGetException
        if not disk:
            # if disk is not specified resize the default boot disk
            boot = config["boot"].split(";")
            disk = [v for v in boot if "order" in v][0].split("=")[1]
        self.proxmox_instance.nodes(node).qemu(vmid).resize.put(
            **{"disk": disk, "size": size}
        )

    def set_vms(
                self,
                vmid,
                vmname,
                cores,
                sockets,
                cpulimit,
                memory,
                ipconfig=None,
                cipassword=None,
                citype=None,
                ciuser=None,
                boot=None,
                sshkey=None
    ) -> None:
        """set vm config parameters"""
        virtual_machine = self.get_vm_by_id_or_name(vmid, vmname)
        if not virtual_machine:
            raise proxcli_exceptions.ProxmoxVmNotFoundException
        node = virtual_machine["node"]
        vmid = virtual_machine["vmid"] if not vmid else vmid

        data = {}

        if cores and cores > 0:
            data["cores"] = cores
        if sockets and sockets > 0:
            data["sockets"] = sockets
        if cpulimit and cpulimit > 0:
            data["cpulimit"] = cpulimit
        if memory and memory > 0:
            data["memory"] = memory
        if cipassword and len(cipassword) > 0:
            data["cipassword"] = cipassword
        if citype and len(citype) > 0:
            data["citype"] = citype
        if ciuser and len(ciuser) > 0:
            data["ciuser"] = ciuser
        if ipconfig and len(ipconfig) > 0:
            data["ipconfig0"] = ipconfig
        if boot and len(boot) > 0:
            data["boot"] = boot
        if sshkey and len(sshkey) > 0:
            data["sshkeys"] = urllib_parse.quote(sshkey.strip(), safe='')
        self.proxmox_instance.nodes(node).qemu(vmid).config.put(**data)

    def get_vm_public_ip(self, node, vmid, net_type="ipv4") -> Any:
        '''
        retrieve vm public ip only work with qemu vms

            Parameters:
                TODO
            Returns:
                TODO
        '''
        interfaces = None
        try:
            agent = self.proxmox_instance.nodes(node).qemu(vmid).agent
            interfaces = agent.get("network-get-interfaces")
        except ResourceException:
            pass

        vm_ip = None
        if interfaces:
            for interface in interfaces["result"]:
                if interface["name"] == "lo":
                    pass
                else:
                    for ipaddress in interface["ip-addresses"]:
                        if ipaddress["ip-address-type"] != net_type:
                            pass
                        else:
                            vm_ip = ipaddress["ip-address"]
                            break
        else:
            vm_ip = "Agent not running"
        return vm_ip

    def get_vms(
            self,
            output_format="json",
            filter_name=None,
            nodes=None,
            status="stopped,running"
    ) -> Any:
        '''
        retrieve a list of qemu vms and print on stdout in the specified format

            Parameters:
                format  (str): output format (table, yaml, json, internal).
                filter  (str): regex applied on vm name to filter result
                nodes   (str): coma separated list of nodes from which to
                               retrieve vms lisst
                status  (str): coma separated list of vms status
            Returns:
                list of vms in the specified format
        '''
        all_nodes = self.get_nodes()
        updated_vms = []

        if not nodes and all_nodes:
            all_nodes = [n for n in all_nodes if n["status"] == "online"]
        else:
            nodes = str(nodes).split(",")
            all_nodes = [] if not all_nodes else all_nodes
            all_nodes = [n for n in all_nodes if
                         n["status"] == "online" and n["node"] in nodes]
        nodes = all_nodes

        status = status.split(",")

        for node in nodes:
            vms = self.proxmox_instance.nodes(node["node"]).qemu.get()
            vms = [] if not vms else vms
            for virtual_machine in vms:
                # add on which node the vm is running
                virtual_machine["node"] = node["node"]
                # add ip address if found
                if (
                    "status" in virtual_machine and
                    virtual_machine["status"] == "running"
                ):
                    try:
                        virtual_machine["ip"] = self.get_vm_public_ip(
                            node=virtual_machine["node"],
                            vmid=virtual_machine["vmid"]
                        )
                    except KeyError:
                        virtual_machine["ip"] = "N/A"
                else:
                    virtual_machine["ip"] = "N/A"
                # if tags are empty create an empty key:value pair
                if "tags" not in virtual_machine.keys():
                    virtual_machine["tags"] = ""
                # filter on status
                if virtual_machine["status"] in status:
                    # apply filter on vms
                    if filter_name and self.ismatching(
                        filter_name,
                        virtual_machine["name"]
                    ):
                        updated_vms.append(virtual_machine)
                    elif not filter_name:
                        updated_vms.append(virtual_machine)
        return self.output(
            headers=self.headers_qemu,
            data=updated_vms,
            output_format=output_format
        )

    def migrate_vms(self, target_node, filter_name=None, vmid=None) -> None:
        """migrate vm from a node to another one"""
        if filter_name and vmid:
            raise proxcli_exceptions.VmIdMutualyExclusiveException
        vms = self.get_vms(output_format="internal")
        vms = [] if not vms else vms
        if vmid:
            vms = [v for v in vms if int(v["vmid"]) == int(vmid)]
            if len(vms) != 1:
                raise proxcli_exceptions.ProxmoxVmNotFoundException
            else:
                virtual_machine = vms[0]
            node = self.proxmox_instance.nodes(virtual_machine["node"])
            node.qemu(vmid).migrate.post(
                **{
                    'node': virtual_machine["node"],
                    'target': target_node,
                    'vmid': vmid
                }
            )
        else:
            for virtual_machine in vms:
                if self.ismatching(filter_name, virtual_machine["name"]):
                    # this vm match filter
                    # first get current node
                    source_node = virtual_machine["node"]
                    # now try to migrate
                    node = self.proxmox_instance.nodes(source_node)
                    node.qemu(virtual_machine["vmid"]).migrate.post(
                        **{
                            'node': source_node,
                            'target': target_node,
                            'vmid': virtual_machine["vmid"]
                        }
                    )
                    rprint(
                        (
                            f"Migration vm {virtual_machine['name']}"
                            f"from {source_node}"
                            f"to {target_node}"
                        )
                    )

    def set_tags(self, tags="", filter_name=None) -> None:
        """set virtual machine tags"""
        vms = self.get_vms(output_format="internal", filter_name=filter_name)
        vms = [] if not vms else vms
        for virtual_machine in vms:
            node = self.proxmox_instance.nodes(virtual_machine["node"])
            node.qemu(virtual_machine["vmid"]).config.put(**{'tags': tags})

    def get_tags(self) -> None:
        """list virtual machine tags"""
        # get a list of all tags present in all vms
        vms = self.get_vms(output_format="internal")
        vms = [] if not vms else vms
        extract = [v["tags"] for v in vms if len(v["tags"]) > 0]
        tags = [element.replace(";", ",").split(",") for element in extract]
        tags = list(set([item for sublist in tags for item in sublist]))
        print(", ".join(tags))

    def delete_vms(self, fitler_name="", vmid=-1, block=True) -> None:
        """ delete vms matching specified regex applied on vm names """
        virtual_machines = self.get_vms(
            output_format="internal",
            filter_name=fitler_name
        )
        if not virtual_machines:
            virtual_machines = []
        if vmid > 0:
            if vmid not in [v["vmid"] for v in virtual_machines]:
                raise proxcli_exceptions.ProxmoxVmNotFoundException
            virtual_machine = [
                v for v in virtual_machines if vmid == v["vmid"]
            ][0]
            if virtual_machine["status"] != "stopped":
                raise proxcli_exceptions.ProxmoxVmNeedStopException
            node = self.proxmox_instance.nodes(virtual_machine["node"])
            delete_job_id = node.qemu(vmid).delete()
            if block:
                self.task_block(delete_job_id)
        else:
            results = []
            if len(virtual_machines) == 0:
                raise proxcli_exceptions.ProxmoxVmNotFoundException
            for virtual_machine in virtual_machines:
                if virtual_machine["status"] == "stopped":
                    node = self.proxmox_instance.nodes(virtual_machine["node"])
                    results.append(
                        node.qemu(virtual_machine["vmid"]).delete())
            for result in results:
                if block:
                    print(
                        f"Wait for deletion task {result} to finish"
                    )
                    self.task_block(result)
                else:
                    print(f"Deletion task started {result}]")

    def set_vms_status(self, status=None, filter_name=None, vmid=None) -> Any:
        """set status of vms matching filter or vmid"""
        vms = self.get_vms(output_format="internal", filter_name=filter_name)
        if not vms:
            return False
        results = []
        if not vmid:
            for virtual_machine in vms:
                node = self.proxmox_instance.nodes(virtual_machine["node"])
                results.append(
                    node.qemu(virtual_machine["vmid"]).status.post(status)
                )
        else:
            virtual_machine = [v for v in vms if v["vmid"] == vmid]
            if len(virtual_machine) == 1:
                node = virtual_machine[0]["node"]
                results.append(
                    self.proxmox_instance.nodes(node).qemu(vmid).status.post(
                        status
                    )
                )

    def clone_vm(
            self,
            vmid,
            name,
            description=None,
            full=None,
            storage=None,
            target=None,
            block=True,
            duplicate=None
    ) -> None:
        """Clone a vm."""
        vms = self.get_vms(output_format="internal")
        virtual_machine = [v for v in vms if vmid == v["vmid"]]
        if len(virtual_machine) == 0:
            raise proxcli_exceptions.ProxmoxVmNotFoundException
        else:
            virtual_machine = virtual_machine[0]

        if virtual_machine["status"] != "stopped":
            raise proxcli_exceptions.ProxmoxVmNeedStopException

        src_node = virtual_machine["node"]
        dst_node = target

        if not duplicate:
            node = self.proxmox_instance.nodes(src_node)
            result = node.qemu(vmid).clone.post(
                **{
                    "newid": self.get_next_id(),
                    "node": src_node,
                    "vmid": int(vmid),
                    "name": name,
                    "description": description,
                    "full": full,
                    "storage": storage,
                    "target": dst_node
                }
            )
            if block:
                self.task_block(result)
        else:
            for index in range(duplicate):
                instance_name = f"{name}-{str(index)}"
                node = self.proxmox_instance.nodes(src_node)
                result = node.qemu(vmid).clone.post(**{
                    "newid": self.get_next_id(),
                    "node": src_node,
                    "vmid": int(vmid),
                    "name": instance_name,
                    "description": description,
                    "full": full,
                    "storage": storage,
                    "target": dst_node
                })
                if block:
                    self.task_block(result)

    def get_next_id(self) -> Any:
        """get next available container/vm id"""
        return self.proxmox_instance.cluster.nextid.get()

    # INVENTORY #

    def inventory(
        self,
        save="",
        output_format="yaml",
        include_tag="",
        exclude_tag="",
        filter_name=""

    ) -> None:
        """
            generate ansible inventory from virtual machine tags
            display or save in file
        """
        vms = self.get_vms(output_format="internal")
        vms_enhanced = []
        for virtual_machine in vms:
            if virtual_machine["status"] == "running":
                vm_ip = self.get_vm_public_ip(
                    virtual_machine["node"],
                    virtual_machine["vmid"]
                )
                virtual_machine["ip"] = vm_ip
            if filter_name != "":
                if re.match(
                    filter_name,
                    virtual_machine["name"]
                ):
                    vms_enhanced.append(virtual_machine)
            else:
                vms_enhanced.append(virtual_machine)

        inventory = {}

        for virtual_machine in vms_enhanced:
            if virtual_machine["ip"] and virtual_machine["ip"] != "N/A":
                if "all" not in inventory:
                    inventory["all"] = {}

                if "hosts" not in inventory["all"]:
                    inventory["all"]["hosts"] = {}

                if "children" not in inventory["all"]:
                    inventory["all"]["children"] = {}

                inventory["all"]["hosts"][virtual_machine["name"]] = {
                    "ansible_host": virtual_machine["ip"]
                }

                exclude_tags = exclude_tag.split(",")
                tags = virtual_machine["tags"].replace(
                    ";", ","
                ).split(",")
                process = False
                if exclude_tags != "":
                    if len(list(set(exclude_tags) & set(tags))) == 0:
                        process = True
                if process:
                    for tag in virtual_machine["tags"].replace(
                        ";", ","
                    ).split(","):
                        if virtual_machine["ip"] != "N/A":
                            if tag not in inventory["all"]["children"].keys():
                                inventory["all"]["children"][tag] = {
                                    "hosts": {}
                                }
                            inventory["all"]["children"][tag]["hosts"][
                                virtual_machine["name"]
                            ] = {"ansible_host": virtual_machine["ip"]}

        if save != "":
            with open(save, "w", encoding="utf-8", ) as file_handle:
                file_handle.write(yaml.dump(inventory))
        else:
            if len(inventory) > 0:
                self.output(data=inventory, output_format=output_format)

    # CONFIG #

    def create_config(self, hosts=None, user=None, password=None) -> None:
        """create a proxcli configuration file"""
        config = (
            f"[credentials]\n"
            f"hosts={hosts}\n"
            f"user={user}\n"
            f"password={password}\n"
            f"[headers]\n"
            f"nodes=node,status\n"
            f"qemu=vmid,name,status,pid,node,cpu,mem,template,ip,tags\n"
            f"lxc=vmid,name,status,pid,node,cpu,mem,ip,tags\n"
            f"storage=storage,node,content,type,active,enabled,shared,\
used_fraction\n"
            f"tasks=starttime,endtime,node,user,type,id,status\n"
            f"ha_groups=group,type,nodes,digest,restricted,nofailback\n"
            f"ha_resources=vmid,name,group,type,digest,\
sid,max_relocate,state\n"
            f"cluster_log=date,severity, user,msg,node,pid,tag,uid\n"
            f"cluster_status=id,type,quorate,version,name,nodes\n"
            f"cluster_status_node=id,nodeid,online,name,type,local,ip,level\n"
            f"node_networks=node,iface,active,method,address,cidr,netmask,\
gateway,bridge_ports,bridge_stp,type,priority,autostart,\
method6,bridge_fd\n"
            f"[data]\n"
            f"colorize=online:green,offline:red,running:green,stopped:red,k3s:\
yellow,failed:red,error:red,OK:green,problems:red,panic:red,\
alert:red,critical:red,warning:orage,notice:blue,info:blue,\
RUNNING:blue,debug:violet\n"
            f"style=STYLE_BOX\n"
            f"[tasks]\n"
            f"polling_interval=1\n"
            f"timeout=300\n"
        )
        home = os.environ.get("HOME")
        config_file = f"{home}/.proxmox"
        if not os.path.exists(config_file):
            with open(config_file, "w", encoding="utf-8") as file_handle:
                file_handle.write(config)
                print("Config file created at ~/.proxmox")
        else:
            print(
                f"A configuration already exist at {config_file}"
            )

    def dump_config(self) -> None:
        """dump proxcli configuration to stdout"""
        home = os.environ.get("HOME")
        config_file = f"{home}/.proxmox"
        if os.path.exists(config_file):
            config = ""
            with open(config_file, "r", encoding="utf-8") as file_handle:
                config = file_handle.read()
            print(config)
        else:
            print("Config does not exist yet.")
            print("Generate config with the following command")
            print("proxmox config create --hosts host1,host2,...,hostn "
                  "--user user --password password")
