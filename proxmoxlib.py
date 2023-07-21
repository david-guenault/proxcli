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

class proxmox:
    def __init__(self):
        self.load_config()
        self.proxmox_instance = self.proxmox()
    # config
    def load_config(self):
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
            self.table_style = self.get_table_style(config["data"]["style"])
            self.table_colorize = dict([ v.split(':') for v in config["data"]["colorize"].split(",") ])
            return True
        else:
            raise("Config file not found")
    # table
    def get_table_style(self, style):
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
    # api
    def proxmox(self):
        self.select_active_node()
        return ProxmoxAPI(
            self.host,
            user=self.username,
            password=self.password,
            verify_ssl=False
        )
    # node
    def select_active_node(self):
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
    # output
    def output(self, headers=None, data=[], format="json", save=False):
        """
        print data on specified format
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

    def table(self, headers, data, width=180):
        """
        Display data as table
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
                if cell in self.table_colorize.keys():
                    new_data_row.append(colored(cell,self.table_colorize[cell]))
                else:
                    new_data_row.append(cell)
            table.rows.append(tuple(new_data_row))
        return table        

    def ismatching(self, regex, data):
        if not re.match(regex, data):
            return False
        else:
            return True

    def get_nodes(self, format="internal", filter=None):
        """
        Get all node as a list
        """
        nodes = self.proxmox_instance.nodes.get()
        if filter:
            nodes = [n for n in nodes if self.ismatching(filter, n["node"])]
        return self.output(headers=self.headers_nodes, data=nodes, format=format)

    def get_container_config(self, vmid):
        containers = self.get_containers(format="internal", filter=".*")
        container = [c for c in containers if c["vmid"] == vmid]
        if len(container) == 1:
            node = container[0]["node"]
        else:
            raise Exception("container with id %s not found" % vmid)
        config = self.proxmox_instance.nodes(node).lxc(vmid).config.get()
        return config

    def get_vm_public_ip(self,node, vmid, type="ipv4"):
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

    def get_containers(self, format="json", filter=None):
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

    def get_vms(self, format="json", filter=None, nodes=None, status="stopped,running"):
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

    def migrate_vms(self, target_node, filter=None):
        vms = self.get_vms(format="internal")
        for vm in vms:
            if self.ismatching(filter, vm["name"]):
                # this vm match filter 
                # first get current node
                source_node = vm["node"]
                # now try to migrate 
                self.proxmox_instance.nodes(source_node).qemu(vm["vmid"]).migrate.post(**{'node':source_node,'target':target_node,'vmid':vm["vmid"]})
                rprint("Migration vm %s from %s to %s " % (vm["name"], source_node, target_node))

    def set_tags(self, tags="", filter=None):
        vms = self.get_vms(format="json", filter=filter)
        for vm in vms:
            self.proxmox_instance.nodes(vm["node"]).qemu(vm["vmid"]).config.put(**{'tags': tags})

    def list_tags(self):
        # get a list of all tags present in all vms
        vms = self.get_vms(format="internal")
        extract = [v["tags"] for v in vms if len(v["tags"]) > 0]
        tags = [element.replace(";", ",").split(",") for element in extract]
        tags = list(set([item for sublist in tags for item in sublist]))
        print(", ".join(tags))

    def inventory(self, bind_users=[], save=False, format="yaml"):
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

    def get_ids(self):
        vms = self.get_vms(format="internal")
        containers = self.get_containers(format="internal")
        vms_ids = [int(v["vmid"]) for v in vms]
        containers_ids = [int(c["vmid"]) for c in containers]
        ids = vms_ids + containers_ids
        return ids

    def get_available_ids(self, min=100, max=199999999):
        ids = sorted(self.get_ids())
        complete_sequence = []
        for i in range(min, max, 1):
            complete_sequence.append(i)
        missing = [v for v in complete_sequence if v not in ids]
        return missing

    def get_next_id(self, min=100, max=199999999):
        return self.get_available_ids(min=min, max=max)[0]

    def delete(self, filter=None):
        '''
        delete vms by name regex pattern
        only stoped vms are removed
        '''
        if not filter:
            return []
        vms = self.get_vms(format="internal", filter=filter)
        for vm in vms:
            self.proxmox_instance.nodes(vm["node"]).qemu(vm["vmid"]).delete()

    def status_vms(self,status=None, filter=None, vmid=None):
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

    def status_containers(self,status=None, filter=None):
        """set status of containers matching filter"""
        containers = self.get_containers(format="internal", filter=filter)
        if not containers: 
            return False
        results = []
        for container in containers:
            results.append(self.proxmox_instance.nodes(container["node"]).lxc(container["vmid"]).status.post(status))

    def get_storages(self,format="json"):
        """list storages"""
        nodes = self.get_nodes(format="internal")
        all_storages = []
        for node in nodes:
            storages = self.proxmox_instance.nodes(node["node"]).storage.get()
            for storage in storages:
                storage["node"] = node["node"]
                all_storages.append(storage)
        return self.output(headers=self.headers_storage, data=all_storages, format=format)            
        
    def create_config(self, hosts=None, user=None, password=None):
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
        [data]
        colorize=online:green,offline:red,running:green,stopped:red,k3s:yellow
        style=STYLE_BOX        
        ''' % (hosts, user,password)
        config_file = "%s/.proxmox" % os.environ.get("HOME")
        if not os.path.exists(config_file):
            h = open(config_file, "w")
            h.write(config)
            h.close()
        else:
            print("A configuration already exist at %s" % config_file)

    def get_nodes_network(self, nodes=None, type="bridge,bond,eth,alias,vlan,OVSBridge,OVSBond,OVSPort,OVSIntPort,any_bridge,any_local_bridge", format="internal"):
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

    def dump_config(self):
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