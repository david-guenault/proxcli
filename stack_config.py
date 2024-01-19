#!/usr/bin/env python
import os
import yaml
from ipaddress import ip_address
from proxmoxlib import Proxmox
import json


class StackConfig():

    def __init__(self, config_file, default_file) -> None:
        self.config_file = config_file
        self.default_file = default_file
        self.config = {}
        self.proxmox = Proxmox()

    def get_stack_data(self, stack):
        s = {
            "ha_groups": {},
            "instances": {}
        }
        ''' load ha groups '''
        ha_groups = self.proxmox.get_ha_groups(output_format="internal")
        ha_groups = [
            group for group in ha_groups if group["group"].startswith(stack)
        ]
        for group in ha_groups:
            group_name = group["group"].replace(f"{stack}-", "")
            del group["group"]
            del group["digest"]
            del group["type"]
            group["restricted"] = False if group["restricted"] == 0 else True
            group["nofailback"] = False if group["nofailback"] == 0 else True
            s["ha_groups"][group_name] = group
        ''' load instances '''
        instances = self.proxmox.get_vms(
            output_format="internal",
            filter_name=f"^{stack}"
        )
        
        for instance in instances:
            del instance["vmid"]
            del instance["cpu"]
            del instance["diskread"]
            del instance["netout"]
            del instance["disk"]
            del instance["diskwrite"]
            del instance["pid"]
            del instance["netin"]
            del instance["uptime"]
            del instance["serial"]
            del instance["ip"]
            instance_name = instance["name"].replace(f"{stack}-", "")
            del instance["name"]
            s["instances"][instance_name] = instance

        print(json.dumps(s, indent=2))
        # ha_groups_resources = self.proxmox.get_ha_resources(output_format="internal")

    def load_yaml(self, file):
        """load yaml file"""
        if not os.path.exists(file) or not os.path.exists(file):
            raise f"file not found {file}"
        else:
            with open(file) as handler:
                content = yaml.safe_load(handler)
            return content

    def merge_default(
        self,
        default,
        config
    ):
        """merge all parameters"""
        default_instances_values = default["provision_template"]
        default_ha_groups_values = default["ha_groups_template"]
        merged_instances = {}
        for kp, vp in config["provision_instances"].items():
            merged_instances[kp] = {}
            merged_instances[kp]["instances"] = {}
            merged_instances[kp]["ha_groups"] = {}
            for ki, vi in vp["instances"].items():
                merged_instances[kp]["instances"][ki] = (default_instances_values
                                                        | vi)
            for kh, vh in vp["ha_groups"].items():
                mvh = vh if vh else {}
                merged_instances[kp]["ha_groups"][kh] = default_ha_groups_values | mvh 
        return {"provision_instances": merged_instances}

    def expand(self, config):
        """expand config for instances with count > 1 and ip static"""
        expanded = {"provision_instances": {}}
        for project, project_config in config["provision_instances"].items():
            if project not in expanded["provision_instances"]:
                expanded["provision_instances"][project] = {
                    "ha_groups": {},
                    "instances": {}
                }
            for instance, instance_config in project_config["instances"].items():
                if (
                    "ipsequence" in instance_config and
                    instance_config["ipsequence"]
                ):
                    new = instance_config.copy()
                    del new["ipsequence"]
                    if "ip6" in new["ipconfig"]:
                        i, g = new["ipconfig"].split(",")
                        i = i.split("=")[-1].strip()
                        g = g.split("=")[-1].strip()
                        ip = ip_address(i)
                        iptype = "ip6"
                        gwtype = "gw6"
                        mask = None
                        gateway = g
                    else:
                        n, g = new["ipconfig"].split(",")
                        n = n.split("=")[-1].strip()
                        g = g.split("=")[-1].strip()
                        ip, mask = n.split("/")
                        ip = ip_address(ip)
                        iptype = "ip"
                        gwtype = "gw"
                        mask = int(mask)
                        gateway = g
                    for index in range(0, new["count"]):
                        nexthost = new.copy()
                        if iptype == "ip6":
                            nextip = str(ip_address(int(ip)+index))
                        else:
                            nextip = str(ip_address(int(ip)+index)) + "/" + str(mask)
                        nextname = f'{instance+"-"+str(index)}'
                        nexthost["ipconfig"] = (
                            f'{iptype}={nextip},{gwtype}'
                            f'={gateway}'
                        )
                        nexthost["count"] = 1
                        expanded["provision_instances"][project]["instances"][nextname] = nexthost
                else:
                    expanded["provision_instances"][project]["instances"][instance] = project_config["instances"][instance]
            expanded[
                "provision_instances"
            ][project]["ha_groups"] = project_config["ha_groups"]
        return expanded

    def load_config(self):
        config = self.load_yaml(self.config_file)
        default = self.load_yaml(self.default_file)
        merged = self.merge_default(default=default, config=config)
        expanded = self.expand(merged)
        return expanded
