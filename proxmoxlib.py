#!/usr/bin/env python
from proxmoxer import ProxmoxAPI
import urllib3
from beautifultable import BeautifulTable
import json
import re
import yaml
import os
import configparser
from termcolor import colored
import requests
from rich import print as rprint
urllib3.disable_warnings()
from proxmoxer.tools import Tasks
from datetime import datetime
import enum

class proxmox:
    def __init__(self) -> None:
        self.load_config()
        self.proxmox_instance = self.proxmox()
    
    ### UTILITY ###
    
    def load_config(self) -> None:
        """load configuration"""
        configfile = os.path.expanduser('~') + "/.proxmox"
        if os.path.exists(configfile):
            config = configparser.ConfigParser()
            config.read(os.path.abspath(configfile))
            self.username = config["credentials"]["user"]
            self.password = config["credentials"]["password"]
            self.hosts = config["credentials"]["hosts"].split(",")
            self.headers_nodes = config["headers"]["nodes"].split(",")
            self.headers_qemu = config["headers"]["qemu"].split(",")
            self.headers_lxc = config["headers"]["lxc"].split(",")
            self.headers_storage = config["headers"]["storage"].split(",")
            self.headers_tasks = config["headers"]["tasks"].split(",")
            self.headers_ha_groups = config["headers"]["ha_groups"].split(",")
            self.table_style = self.get_table_style(config["data"]["style"])
            self.task_polling_interval = config["tasks"]["polling_interval"]
            self.task_timeout = config["tasks"]["timeout"]
            self.table_colorize = dict([ v.split(':') for v in config["data"]["colorize"].split(",") ])
        else:
            raise("Config file not found")
    
    def select_active_node(self) -> None:
        """
        select the first available node 
        iterate over nodes, ping and set self.host property
        """
        
        for host in self.hosts:
            url = "https://%s:8006" % host
            try:
                result = requests.get(url,timeout=1, allow_redirects=True, verify=False)
                self.host = host
                break
            except Exception as e:
                pass
    
    def get_table_style(self, style) -> enum.Enum:
        """set beautiful table display style from string"""
        if style == "STYLE_DEFAULT":
            return BeautifulTable.STYLE_DEFAULT
        elif style == "STYLE_NONE":
            return BeautifulTable.STYLE_NONE
        elif style == "STYLE_DOTTED":
            return BeautifulTable.STYLE_DOTTED
        elif style == "STYLE_SEPARATED":
            return BeautifulTable.STYLE_SEPARATED
        elif style == "STYLE_COMPACT":
            return BeautifulTable.STYLE_COMPACT
        elif style == "STYLE_MYSQL":
            return BeautifulTable.STYLE_MYSQL
        elif style == "STYLE_MARKDOWN":
            return BeautifulTable.STYLE_MARKDOWN
        elif style == "STYLE_RST":
            return BeautifulTable.STYLE_RST
        elif style == "STYLE_BOX":
            return BeautifulTable.STYLE_BOX
        elif style == "STYLE_BOX_DOUBLED":
            return BeautifulTable.STYLE_BOX_DOUBLED
        elif style == "STYLE_BOX_ROUNDED":
            return BeautifulTable.STYLE_BOX_ROUNDED
        elif style == "STYLE_GRID":
            return BeautifulTable.STYLE_GRID
        else: 
            return BeautifulTable.STYLE_BOX

    def output(self, headers=None, data=[], format="internal", save=False) :
        """
        print data on specified format 
        default to internal (raw data is returned instead of displaying)
        """
        if format == "json":
            data = json.dumps(data, indent=2)
        elif format == "yaml":
            data = yaml.dump(data)
        elif format == "table":
            data = self.table(headers=headers, data=data)            
        elif format == "internal":
            return data
        if save:
            h = open(save, "w")
            h.write(data)
            h.close()
        else:
            if format == "yaml" or format == "json":
                rprint(data)
            else:
                print(data)

    def readable_date(self, timestamp) :
        """convert unix timestamp to human readable date time"""
        return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')        

    def table(self, headers, data, width=180) :
        """
        Display list of dict as table
        """
        table = BeautifulTable(maxwidth=width)
        table.set_style(self.table_style)
        table.columns.header = headers
        for element in data:
            datarow = []
            for header in headers:
                try:
                    datarow.append(element[header])
                except:
                    datarow.append("")
            new_data_row = []
            for cell in datarow:
                if len(str(cell)) > 0:
                    words = list(self.table_colorize.keys())
                    match = [word for word in words if word in str(cell)]
                    if len(match) == 1:
                        new_data_row.append(colored(cell, self.table_colorize[match[0]]))
                    else:
                        new_data_row.append(cell)
                else:
                    new_data_row.append("")
            table.rows.append(tuple(new_data_row))
        return table

    def ismatching(self, regex, data) :
        """shortcut method used to check is a string match a regex"""
        if not re.match(regex, data):
            return False
        else:
            return True

    def taskBlock(self, task) :
        '''
        Poll a task until the task is finished or timed out
            Paramaters:
                task (str): a task identifier (UPID:<node_name>:<pid_in_hex>:<pstart_in_hex>:<starttime_in_hex>:<type>:<id (optional)>:<user>@<realm>:)
            Returns:
                result (dict); a dict with all the task information (see https://proxmoxer.github.io/docs/2.0/tools/tasks/#blocking_status)
        '''
        print("Waiting for task %s to finish" % task)
        result = Tasks.blocking_status(prox=self.proxmox_instance, task_id=task, timeout=int(self.task_timeout), polling_interval=float(self.task_polling_interval))        

    def proxmox(self) :
        """create proxmox api instance from the first available node found"""
        self.select_active_node()
        return ProxmoxAPI(
            self.host,
            user=self.username,
            password=self.password,
            verify_ssl=False
        )

    ### CLUSTER ###

    def get_ha_groups(self, format="internal"):
        """list cluster ha groups"""
        hagroups = self.proxmox_instance.cluster.ha.groups.get()
        print(hagroups)
        return self.output(headers=self.headers_ha_groups, data=hagroups, format=format)

    def create_ha_group(self, group, nodes, nofailback=False, restricted=False):
        '''
            create a hagroup
            Parameters:
                group (str): the ha group name
                nodes (str): <node>[:<pri>]{,<node>[:<pri>]}*
                                List of cluster node members, where a priority can be given to each node. A resource bound to a group will run on the available nodes with the highest priority. If there are more nodes in the highest priority class, the services will get distributed to those nodes. The priorities have a relative meaning only.
                nofailback (bool):
                restricted (bool):
                tyep (enum):
            Returns:
                result (bool): true if success, false if failure
        '''

        nofailback = 0 if nofailback == False else 1
        restricted = 0 if restricted == False else 1
        self.proxmox_instance.cluster.ha.groups.post(**{
            "group": group,
            "nodes": nodes,
            "nofailback": nofailback,
            "restricted": restricted
        })

    def delete_ha_groups(self, group):
        self.proxmox_instance.cluster.ha.groups.delete(group)


    def get_storages(self,format="json") :
        """list storages"""
        nodes = self.get_nodes(format="internal")
        available_nodes = [n for n in nodes if n["status"] == "online"]
        if len(available_nodes) > 0:
            query_node = available_nodes[0]
        else:
            raise Exception("No nodes available")
        
        all_storages = []
        
        storages = self.proxmox_instance.storage.get()
        for storage in storages:
            all_storages.append(storage)
        return self.output(headers=self.headers_storage, data=all_storages, format=format)            

    ### NODES ###

    def get_nodes(self, format="internal", filter=None) :
        '''
        Get all node as a list

            Parameters:
                TODO
            Returns:
                TODO

        '''
        nodes = self.proxmox_instance.nodes.get()
        if filter:
            nodes = [n for n in nodes if self.ismatching(filter, n["node"])]
        return self.output(headers=self.headers_nodes, data=nodes, format=format)

    def get_tasks(self, format="internal", errors=0,limit=50,source="all",vmid=None,nodes=None) :
        available_nodes = self.get_nodes(format="internal")
        available_nodes = [n["node"] for n in available_nodes if n["status"] == "online"]
        if not nodes:
            nodes = available_nodes
        else:
            nodes = nodes.split(",")
            nodes = [n for n in nodes if n in available_nodes]

        tasks = []
        for node in nodes:
            t = self.proxmox_instance.nodes(node).tasks.get(**{
                "errors": errors,
                "limit": limit,
                "source": source,
                "vmid": None
            })
            tasks += t
        tasks = [t for t in tasks if t["node"] in nodes]
        tasks = sorted(tasks, key=lambda d: d['starttime'],reverse=True)
        for t in tasks:
            t['starttime'] = self.readable_date(t['starttime'])
            t['endtime'] = self.readable_date(t['endtime'])
        self.output(headers=self.headers_tasks, data=tasks, format=format)

    def get_nodes_network(self, nodes=None, type="bridge,bond,eth,alias,vlan,OVSBridge,OVSBond,OVSPort,OVSIntPort,any_bridge,any_local_bridge", format="internal") :
        if not nodes or not types: 
            return []
        else:
            nodes = nodes.split(",")
            types = types.split(",")
        networks = []
        for node in nodes:
            result = self.proxmox_instance.node(node).network.get()
            for net in result:
                net["node"] = node
                networks.append(net)
        self.output(headears=None, data=networks)


    ### VMS ###

    def get_vm_public_ip(self,node, vmid, type="ipv4") :
        '''
        retrieve vm public ip only work with qemu vms

            Parameters:
                TODO
            Returns:
                TODO
        '''
        try:
            interfaces = self.proxmox_instance.nodes(node).qemu(vmid).agent.get("network-get-interfaces")
            for interface in interfaces["result"]:
                if interface["name"] == "lo":
                    pass
                else:
                    for ipaddress in interface["ip-addresses"]:
                        if ipaddress["ip-address-type"] != type:
                            pass
                        else:
                            ip = ipaddress["ip-address"]
                            break
        except Exception as e:
            ip = None
        return ip

    def get_vms(self, format="json", filter=None, nodes=None, status="stopped,running") :
        '''
        retrieve a list of qemu vms and print on stdout in the specified format

            Parameters: 
                format  (str): output format (table, yaml, json, internal).
                filter  (str): regex applied on vm name to filter result
                nodes   (str): coma separated list of nodes from which to retrieve vms lisst
                status  (str): coma separated list of vms status 
            Returns:
                list of vms in the specified format
        '''
        all_nodes = self.get_nodes()
        updated_vms = []
        
        if not nodes:
            all_nodes = [n for n in all_nodes if n["status"] == "online"]
        else:
            nodes = nodes.split(",")
            all_nodes = [n for n in all_nodes if n["status"] == "online" and n["node"] in nodes]
        nodes = all_nodes

        status = status.split(",")

        for node in nodes:
            vms = self.proxmox_instance.nodes(node["node"]).qemu.get()
            for vm in vms:
                    # add on which node the vm is running
                    vm["node"] = node["node"]
                    # add ip address if found
                    vm["ip"] = self.get_vm_public_ip(node=vm["node"], vmid=vm["vmid"])
                    # if tags are empty create an empty key:value pair
                    if "tags" not in vm.keys():
                        vm["tags"] = ""
                    # filter on status
                    if vm["status"] in status:
                        # apply filter on vms 
                        if filter and self.ismatching(filter, vm["name"]):
                            updated_vms.append(vm)
                        elif not filter:
                            updated_vms.append(vm)
        return self.output(headers=self.headers_qemu, data=updated_vms, format=format)            

    def migrate_vms(self, target_node, filter=None, vmid=None) :
        if filter and vmid:
            raise Exception("filter and vmid arguments are mutualy exclusive")
        vms = self.get_vms(format="internal")                
        if vmid:
            vms = [v for v in vms if int(v["vmid"]) == int(vmid)]
            if len(vms) != 1:
                raise Exception("vm %s could not be found on any node")
            else:
                vm = vms[0]
            try:
                self.proxmox_instance.nodes(vm["node"]).qemu(vmid).migrate.post(**{'node':vm["node"],'target':target_node,'vmid':vmid})
            except Exception as e:
                print(e)
            rprint("Migration vm %s from %s to %s " % (vm["name"], vm["node"], target_node))
        else:
            
            for vm in vms:
                if self.ismatching(filter, vm["name"]):
                    # this vm match filter 
                    # first get current node
                    source_node = vm["node"]
                    # now try to migrate 
                    self.proxmox_instance.nodes(source_node).qemu(vm["vmid"]).migrate.post(**{'node':source_node,'target':target_node,'vmid':vm["vmid"]})
                    rprint("Migration vm %s from %s to %s " % (vm["name"], source_node, target_node))

    def set_tags(self, tags="", filter=None) :
        vms = self.get_vms(format="json", filter=filter)
        for vm in vms:
            self.proxmox_instance.nodes(vm["node"]).qemu(vm["vmid"]).config.put(**{'tags': tags})

    def list_tags(self) :
        # get a list of all tags present in all vms
        vms = self.get_vms(format="internal")
        extract = [v["tags"] for v in vms if len(v["tags"]) > 0]
        tags = [element.replace(";", ",").split(",") for element in extract]
        tags = list(set([item for sublist in tags for item in sublist]))
        print(", ".join(tags))

    def delete_vms(self, filter=None, vmid=None, block=True) :
        '''
        delete vms matching specified regex applied on vm names
        only stoped vms are removed
        filter and vmid are mutualy exclusive
            Parameters:
                filter (string): regex filter applied on vms names (only the matching vms will be deleted)
                vmid (int): vm id to delete
                block (bool): if True will wait for each deletion to end. 
            Returns
                True if success
        '''
        vms = self.get_vms(format="internal", filter=filter)
        if vmid:
            if not vmid in [ v["vmid"] for v in vms ]:
                raise Exception("specified vmid not found on any available nodes")
            vm = [v for v in vms if vmid == v["vmid"]][0]
            if vm["status"] != "stopped":
                raise Exception("vm %s (%s) must be stopped before deletion" % (vm["name"], vmid))
            result = self.proxmox_instance.nodes(vm["node"]).qemu(vmid).delete()
            if block:
                result = self.taskBlock(result)           
                self.output(data=result, format="internal")                
        else:
            results = []
            if len(vms) == 0:
                raise Exception("No vms found matching filter %s" % filter)
            for vm in vms:
                if vm["status"] == "stopped":
                    results.append(self.proxmox_instance.nodes(vm["node"]).qemu(vm["vmid"]).delete())

            for result in results:
                if block:
                    print("Wait for deletion task %s to finish" % result)
                    self.taskBlock(result)
                else:
                    print("Deletion task started %s" % result)
        return True

    def status_vms(self,status=None, filter=None, vmid=None) :
        """set status of vms matching filter or vmid"""
        vms = self.get_vms(format="internal", filter=filter)
        if not vms: 
            return False
        results = []
        if not vmid:
            for vm in vms:
                results.append(self.proxmox_instance.nodes(vm["node"]).qemu(vm["vmid"]).status.post(status))
        else:
            vm = [v for v in vms if v["vmid"] == vmid]
            if len(vm) == 1:
                node = vm[0]["node"]
                results.append(self.proxmox_instance.nodes(node).qemu(vmid).status.post(status))

    def clone_vm(self, vmid, name, description=None, full=None, storage=None, target=None, block=True, duplicate=None) :
        """
            Clone a vm.
            Parameters:
                vmid (int): the vm id to be cloned from
                name (str): name of the cloned vm
                description (str): description of the cloned vm
                full (bool): full clone if true else linked clone
                storage (str): which storage to use for the cloned vm
                target (str): the target not for the cloned vm
                block (bool): if true will wait for each clone to be finished (this prevent io saturation for exemple on NFS)
                duplicate (int): how many clone to produce ? (each vm name is suffixed with an integer index)
            Return: a list of 
        """
        vms = self.get_vms(format="internal")
        vm = [v for v in vms if vmid == v["vmid"]]
        if len(vm) == 0:
            raise Exception("Unable to find vm %s" % vmid)
        else:
            vm = vm[0]

        if vm["status"] != "stopped":
            raise Exception("VM must be stopped before cloning")

        src_node = vm["node"]
        dst_node = target

        if not duplicate:
            result = self.proxmox_instance.nodes(src_node).qemu(vmid).clone.post(**{
                "newid": self.get_next_id(max=500),
                "node": src_node,
                "vmid": int(vmid),
                "name": name,
                "description": description,
                "full": full,
                "storage": storage,
                "target": dst_node
            })
            if block: 
                result = self.taskBlock(result)
        else:
            results = []
            for index in range(duplicate):
                instance_name = "%s-%s" % (name, str(index))
                result = self.proxmox_instance.nodes(src_node).qemu(vmid).clone.post(**{
                    "newid": self.get_next_id(max=500),
                    "node": src_node,
                    "vmid": int(vmid),
                    "name": instance_name,
                    "description": description,
                    "full": full,
                    "storage": storage,
                    "target": dst_node
                })
                if block:
                    result = self.taskBlock(result)
                    results.append(result)
                

        return result

    ### CONTAINERS (need rework) ###

    def get_container_config(self, vmid) :
        """retrieve container configuration"""
        containers = self.get_containers(format="internal", filter=".*")
        container = [c for c in containers if c["vmid"] == vmid]
        if len(container) == 1:
            node = container[0]["node"]
        else:
            raise Exception("container with id %s not found" % vmid)
        config = self.proxmox_instance.nodes(node).lxc(vmid).config.get()
        return config

    def status_containers(self,status=None, filter=None) :
        """set status of containers matching filter"""
        containers = self.get_containers(format="internal", filter=filter)
        if not containers: 
            return False
        results = []
        for container in containers:
            results.append(self.proxmox_instance.nodes(container["node"]).lxc(container["vmid"]).status.post(status))


    def get_containers(self, format="internal", filter=None) :
        """retrieve a list of containers
        display the list in the specified format or return raw data if format is internal (default)
        a regexp filter can be specified to reduce the list 
        """
        nodes = self.get_nodes(format="internal")
        updated_vms = []
        nodes = [n for n in nodes if n["status"] == "online"]
        for node in nodes:
            vms = self.proxmox_instance.nodes(node["node"]).lxc.get()
            for vm in vms:
                    # add on which node the vm is running
                    vm["node"] = node["node"]
                    # if tags are empty create an empty key:value pair
                    if "tags" not in vm.keys():
                        vm["tags"] = ""
                    # apply filter on vms 
                    if filter and self.ismatching(filter, vm["name"]):
                        updated_vms.append(vm)
                    elif not filter:
                        updated_vms.append(vm)
        return self.output(headers=self.headers_lxc, data=updated_vms, format=format)   

    ### CONTAINER AND VMS 
    
    def get_ids(self) :
        '''
        return a list of existing containers and vms ids
        '''
        vms = self.get_vms(format="internal")
        containers = self.get_containers(format="internal")
        vms_ids = [int(v["vmid"]) for v in vms]
        containers_ids = [int(c["vmid"]) for c in containers]
        ids = vms_ids + containers_ids
        return ids    

    def get_available_ids(self, min=100, max=199999999) :
        '''
        build a list of available containers and vms ids in the specified range
        '''
        ids = sorted(self.get_ids())
        complete_sequence = []
        for i in range(min, max, 1):
            complete_sequence.append(i)
        missing = [v for v in complete_sequence if v not in ids]
        return missing

    def get_next_id(self, min=100, max=199999999) :
        '''
        get the next available container or vm id
        if the id sequence contains hole, it will return the first available hole
        ex: 1,2,3,5 > next available id is 4 (fill the hole)
            Parameters:
                TODO
            Returns:
                TODO
        '''
        return self.get_available_ids(min=min, max=max)[0]

    ### INVENTORY ###

    def inventory(self, bind_users=[], save=False, format="yaml") :
        vms = self.get_vms(format="internal")
        bind = {}
        vms_enhanced = []
        for vm in vms:
            ip = self.get_vm_public_ip(vm["node"], vm["vmid"])
            vm["ip"] = ip
            vms_enhanced.append(vm)

        inventory = {}

        if len(bind_users) > 0:
            bind = dict([v.split(':') for v in bind_users])

        for vm in vms_enhanced:
            if vm["ip"]:
                if not "all" in inventory.keys():
                    inventory["all"] = {}

                if not "hosts" in inventory["all"].keys():
                    inventory["all"]["hosts"] = {}

                if not "children" in inventory["all"].keys():
                    inventory["all"]["children"] = {}

                inventory["all"]["hosts"][vm["name"]] = {"ansible_host": vm["ip"]}
                
                for tag in vm["tags"].replace(";",",").split(","):
                    if not tag in inventory["all"]["children"].keys():
                        inventory["all"]["children"][tag] = {"hosts": {}}
                    inventory["all"]["children"][tag]["hosts"][vm["name"]] = {"ansible_host": vm["ip"]}
                    # if tag in bind.keys():
                    #     inventory["all"]["hosts"][vm["name"]]["ansible_user"] = bind[tag]
                    #     for host in inventory["all"]["children"][tag]["hosts"].keys():
                    #         inventory["all"]["children"][tag]["hosts"][host]["ansible_user"] = bind[tag]


        self.output(data = inventory, format=format, save=save)

    ### CONFIG ###
 
    def create_config(self, hosts=None, user=None, password=None) :
        config = '''
        [credentials]
        hosts=%s
        user=%s
        password=%s
        [headers]
        nodes=node,status
        qemu=vmid,name,status,pid,node,cpu,mem,template,ip,tags
        lxc=vmid,name,status,pid,node,cpu,mem,ip,tags
        storage=storage,node,content,type,active,enabled,shared,used_fraction
        tasks=starttime,endtime,node,user,type,id,status
        [data]
        colorize=online:green,offline:red,running:green,stopped:red,k3s:yellow,failed:red,error:red,OK:green,problems:red
        style=STYLE_BOX
        [tasks]
        polling_interval=1
        timeout=300

        ''' % (hosts, user,password)
        config_file = "%s/.proxmox" % os.environ.get("HOME")
        if not os.path.exists(config_file):
            h = open(config_file, "w")
            h.write(config)
            h.close()
        else:
            print("A configuration already exist at %s" % config_file)


    def dump_config(self) :
        config_file = "%s/.proxmox" % os.environ.get("HOME")
        if os.path.exists(config_file):
            h = open(config_file, "r")
            config = h.read()
            h.close()
            print(config)
        else:
            print("Config does not exist yet.")
            print("Generate config with the following command")
            print("proxmox config create --hosts host1,host2,...,hostn --user user --password password")
    

        