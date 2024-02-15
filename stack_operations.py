"""Description of the module.

Classes:
    <class>

Functions:
    <function>

Misc. variables:
    <variable>
"""
import os
import json
import sys
# from deepdiff import DeepDiff
import dictdiffer
from termcolor import colored
from proxmoxlib import Proxmox
from proxmoxlib import HaResource
from proxmoxlib import VmProperties
from stack_config import StackConfig


class StackOperations():
    """Description of the class.

    Args:
        <arg> (<type>): Description of the arg.

    Variables:
        <variable> (<type>): Description of the variable.
    """

    def __init__(self, config_file_path, default_file_path) -> None:
        self.proxmox_instance = Proxmox()
        self.expanded_config = StackConfig(
            config_file=config_file_path,
            default_file=default_file_path
        ).load_config()

    def stack_diff(self, state, desired):
        """Description of the function/method.

        Parameters:
            <param>: Description of the parameter

        Returns:
            <variable>: Description of the return value
        """
        dd = dictdiffer.diff(state, desired)
        ha_groups_update = {
            "added": [],
            "removed": [],
            "updated": {}
        }
        instances_update = {
            "added": [],
            "removed": [],
            "updated": {}
        }
        for item in dd:
            if item[0] == "add":
                if item[1] == "instances":
                    instances = [i[0] for i in item[2]]
                    for instance in instances:
                        instances_update["added"].append(
                            instance
                        )
                if "instances" in item[1] and "tags" in item[1]:
                    # add a tag to an existing instance
                    _, instance, _ = item[1].split(".")
                    for tag_change in item[2]:
                        print(f"update instance {instance} add tag {tag_change[1]} ")
                        instances_update["updated"].setdefault(
                            instance, {"tags": {
                                "added": [],
                                "removed": []
                            }}
                        )
                        # added tag is ('add', 'instances.talos-0.tags', [(1, 'kubernetes')])
                        for tag in item[2]:
                            if tag[1] not in instances_update[
                                "updated"
                            ][instance]["tags"]["added"]:
                                instances_update["updated"][instance]["tags"][
                                    "added"
                                ].append(tag[1])

                elif item[1] == "ha_groups":
                    ha_groups = [h[0] for h in item[2]]
                    for ha_group in ha_groups:
                        ha_groups_update["added"].append(
                            ha_group
                        )
            elif (item[0] == "change"):
                if "ha_groups" in item[1]:
                    _, ha_group, ha_group_property = item[1].split(".")
                    old_value = item[2][0]
                    new_value = item[2][1]
                    ha_groups_update["updated"].setdefault(
                        ha_group, {}
                    )
                    ha_groups_update["updated"][
                        ha_group
                    ][ha_group_property] = {
                        "old": old_value,
                        "new": new_value
                    }
                elif "instances" in item[1]:
                    if "tags" in item[1]:
                        _, instance, _, _ = item[1]
                        instances_update["updated"].setdefault(
                            instance, {
                                "tags": {
                                    "added": [],
                                    "removed": []
                                }
                            }
                        )
                        instances_update["updated"][instance][
                            "tags"
                        ]["removed"].append(item[2][0])
                        instances_update["updated"][instance][
                            "tags"
                        ]["added"].append(item[2][1])

                    else:
                        _, instance, instance_property = item[1].split(".")
                        old_value = item[2][0]
                        new_value = item[2][1]
                        instances_update["updated"].setdefault(
                            instance, {"tags": {
                                "added": [],
                                "removed": []
                            }}
                        )
                        instances_update["updated"][instance][
                            instance_property
                        ] = {
                            "old": old_value,
                            "new": new_value
                        }
            elif item[0] == "remove" and "tags" in item[1]:
                # special case
                # this is an instance update
                # with removed tags
                _, instance, _ = item[1].split(".")
                for tag in item[2]:
                    instances_update["updated"].setdefault(
                        instance,
                        {"tags": {
                            "removed": [],
                            "added": []
                        }}
                    )
                    if instance not in instances_update["updated"]:
                        instances_update["updated"][instance] = {}
                    instances_update[
                        "updated"
                    ][instance]["tags"]["removed"].append(tag[1])
            elif item[0] == "remove" and "tags" not in item[1]:
                if item[1] == "instances":
                    instances = [i[0] for i in item[2]]
                    for instance in instances:
                        instances_update["removed"].append(
                            instance
                        )
                elif item[1] == "ha_groups":
                    ha_groups = [h[0] for h in item[2]]
                    for ha_group in ha_groups:
                        ha_groups_update["removed"].append(
                            ha_group
                        )
        return {
            "ha_groups": ha_groups_update,
            "instances": instances_update
        }
        

    def stack_plan(self, stack_name):
        """Description of the function/method.

        Parameters:
            <param>: Description of the parameter

        Returns:
            <variable>: Description of the return value
        """
        state_file = os.path.abspath(
            os.path.expanduser(
                f"~/.proxcli/{stack_name}.state"
            )
        )
        if not os.path.exists(state_file):
            print("State file {state_file} does not exists")
            state = {
                "ha_groups": {},
                "instances": {}
            }
        else:
            with open(
                file=state_file,
                mode="r",
                encoding="utf-8"
            ) as handle:
                state = json.loads(handle.read())

        desired = self.expanded_config["provision_instances"][stack_name]

        differences = self.stack_diff(state=state, desired=desired)
        print(
            json.dumps(
                differences,
                indent=2
            )
        )
        self.stack_write_plan(
            stack_plan=differences,
            stack_name=stack_name
        )
        self.stack_show_plan(stack_name=stack_name)

    def stack_show_plan(self, stack_name):
        """Description of the function/method.

        Parameters:
            <param>: Description of the parameter

        Returns:
            <variable>: Description of the return value
        """
        print(
            colored(
                "-- remove [ha resource | ha group | instance ]",
                color="red"
            )
        )
        print(
            colored(
                "++ add [ha group | instance ]", color="green"
            )
        )
        print(
            colored(
                "== update [ha resource | ha group | instance ]",
                color="blue"
            )
        )
        print("")
        differences = self.load_stack_data(stack_name=stack_name, file_type="plan")
        desired = self.expanded_config["provision_instances"][stack_name]
        for ha_group in differences["ha_groups"]["removed"]:
            # before removing ha group we must remove ha resources
            ha_resources = self.proxmox_instance.get_ha_resources(
                output_format="internal",
                group=f"{stack_name}-{ha_group}"
            )
            for ha_resource in ha_resources:
                print(colored(
                    f"-- ha resource: {ha_resource['name']}",
                    color="red"
                ))
            print(colored(
                f"-- ha group {stack_name}-{ha_group}",
                color="red"
            ))

        for ha_group in differences["ha_groups"]["added"]:
            print(
                colored(f"++ ha group {stack_name}-{ha_group}", color="green"))
            content = desired["ha_groups"][ha_group]
            for hag_property, value in content.items():
                print(colored(f"    {hag_property} = {value}", color="green"))

        ha_resources_changes = {}
        for ha_group in differences["ha_groups"]["updated"]:
            print(
                colored(f"== ha group {stack_name}-{ha_group}", color="blue"))
            content = differences["ha_groups"]["updated"][ha_group]
            for prop, val in content.items():
                if prop not in ("max_restart", "max_relocate"):
                    print(
                        colored(
                            (
                                f"    {prop}: {val['old']} "
                                f"-> {val['new']}"
                            ),
                            color="blue"
                        )
                    )
                else:
                    ha_resources_changes.setdefault(
                        f"{stack_name}-{ha_group}", {}
                    )
                    ha_resources_changes[
                        f"{stack_name}-{ha_group}"
                    ][prop] = val
            for ha_resource, changes in ha_resources_changes.items():
                print(
                    colored(
                        f"== ha resource {ha_resource}",
                        color="blue"
                    )
                )
                for prop, change in changes.items():
                    print(
                        colored(
                            (
                                f"    {prop}: {change['old']} "
                                f"-> {change['new']}"
                            ),
                            color="blue"
                        )
                    )
            ha_resources_changes = {}

        for instance in differences["instances"]["removed"]:
            print(
                colored(
                    f"-- instance {stack_name}-{instance}",
                    color="red"
                )
            )

        for instance in differences["instances"]["added"]:
            print(
                colored(
                    f"++ instance {stack_name}-{instance}",
                    color="green"
                )
            )
            for prop, val in self.expanded_config["provision_instances"][
                stack_name
            ]["instances"][instance].items():
                if prop == "password":
                    val = "**********"
                print(
                    colored(
                        f"    {prop} = {val}",
                        color="green"
                    )
                )

        for instance, updated_data in differences["instances"][
            "updated"
        ].items():
            print(
                colored(
                    f"== instance {stack_name}-{instance}",
                    color="blue"
                )
            )
            for prop, val in updated_data.items():
                if prop == "tags":
                    print(colored(
                        "    tags:",
                        color="blue"
                    ))
                    for tag_removed in val["removed"]:
                        print(colored(
                            f"        -- {tag_removed}",
                            color="red"

                        ))
                    for tag_added in val["added"]:
                        print(colored(
                            f"        ++ {tag_added}",
                            color="green"

                        ))
                else:
                    print(colored(
                        f"    {prop}: {val['old']} -> {val['new']}",
                        color="blue"
                    ))

    def load_stack_data(self, stack_name, file_type):
        """Description of the function/method.

        Parameters:
            <param>: Description of the parameter

        Returns:
            <variable>: Description of the return value
        """
        if file_type == "state":
            file_name = f"~/.proxcli/{stack_name}.state"
        else:
            file_name = f"~/.proxcli/{stack_name}.plan"
        file = os.path.abspath(
            os.path.expanduser(
                file_name
            )
        )
        if not os.path.exists(file):
            print(f"file {file} does not exists")
            data = None
        else:
            with open(
                file=file,
                mode="r",
                encoding="utf-8"
            ) as handle:
                data = json.loads(handle.read())
        return data

    def stack_apply(self, stack_name):
        """Description of the function/method.

        Parameters:
            <param>: Description of the parameter

        Returns:
            <variable>: Description of the return value
        """

        differences = self.load_stack_data(
            stack_name=stack_name,
            file_type="plan"
        )
        if not differences:
            print(colored(
                "No plan is available to be applied",
                color="red"
            ))
            sys.exit(2)
        desired = self.expanded_config["provision_instances"][stack_name]
        # HA GROUP REMOVE
        hag_diff = differences["ha_groups"]
        for ha_group in hag_diff["removed"]:
            print(colored(
                f"-- ha group {stack_name}-{ha_group}",
                color="red"
            ))
            self.proxmox_instance.delete_ha_resources_by_group_name(
                group=f"{stack_name}-{ha_group}"
            )
            self.proxmox_instance.delete_ha_group(
                group=f"{stack_name}-{ha_group}"
            )
        # HA GROUP ADD
        for ha_group in differences["ha_groups"]["added"]:
            print(
                colored(
                    (
                        f"++ ha group {stack_name}-"
                        f"{ha_group}"
                    ),
                    color="green"
                )
            )
            content = desired["ha_groups"][ha_group]
            if not self.proxmox_instance.exists_ha_group(
                ha_group=f"{stack_name}-{ha_group}"
            ):
                self.proxmox_instance.create_ha_group(
                    group=f"{stack_name}-{ha_group}",
                    proxmox_nodes=content["nodes"],
                    nofailback=content["nofailback"],
                    restricted=content["restricted"]
                )
        # HA GROUP UPDATE
        for ha_group in differences["ha_groups"]["updated"]:
            print(colored(
                f"== update ha group {ha_group}",
                color="blue"
            ))
            content = differences["ha_groups"]["updated"][ha_group]
            self.proxmox_instance.update_ha_group(
                group=f"{stack_name}-{ha_group}",
                proxmox_nodes=content[
                    "nodes"
                ]["new"] if "nodes" in content else None,
                nofailback=content[
                    "nofailback"
                ]["new"] if "nofailback" in content else None,
                restricted=content[
                    "restricted"
                ]["new"] if "restricted" in content else None
            )
            if "max_restart" in content or "max_relocate" in content:
                # also update ha resource for those properties
                resources = self.proxmox_instance.get_ha_resources(
                    group=f"{stack_name}-{ha_group}",
                    output_format="internal"
                )
                for resource in resources:
                    self.proxmox_instance.update_ha_resource(
                        ha_resource=HaResource(
                            sid=resource["sid"],
                            comment=None,
                            delete=None,
                            digest=None,
                            group=None,
                            state=None,
                            max_relocate=content[
                                "max_relocate"
                            ]["new"] if "max_relocate" in resources else None,
                            max_restart=content[
                                "max_restart"
                            ]["new"] if "max_restart" in resources else None
                        )
                    )
        # INSTANCE REMOVE
        for instance in differences["instances"]["removed"]:
            print(
                colored(
                    f"-- instance {stack_name}-{instance}",
                    color="red"
                )
            )
            if self.proxmox_instance.exists_vm(
                virtual_machine_name=f"{stack_name}-{instance}"
            ):
                # stop vms
                vm_instance = self.proxmox_instance.get_vm_by_id_or_name(
                    vmname=f"{stack_name}-{instance}"
                )
                self.proxmox_instance.set_vms_status(
                    vmid=vm_instance["vmid"],
                    status="stop"
                )
                self.proxmox_instance.vms_wait_for_status(
                    status="stopped",
                    vmid=vm_instance["vmid"]
                )
                # remove vms resources from ha groups
                try:
                    self.proxmox_instance.delete_ha_resources(
                        vmid=vm_instance["vmid"]
                    )
                except Exception:
                    pass
                # remove vm
                self.proxmox_instance.delete_vms(
                    vmid=vm_instance["vmid"]
                )
            else:
                print(
                    colored(
                        f"VM Instance {instance} does not exist",
                        color="red"    
                    )
                )
        # INSTANCE ADDED
        for instance in differences["instances"]["added"]:
            print(
                colored(
                    f"++ instance {stack_name}-{instance}",
                    color="green"
                )
            )
            if not self.proxmox_instance.exists_vm(
                virtual_machine_name=f"{stack_name}-{instance}"
            ):
                print(f"Create vm instance {stack_name}-{instance}")
                cfg_instances = desired["instances"][instance]
                cfg_groups = desired["ha_groups"]
                self.proxmox_instance.clone_vm(
                    vmid=cfg_instances["clone"],
                    name=f"{stack_name}-{instance}",
                    full=1 if cfg_instances["full_clone"] else 0,
                    storage=cfg_instances["disk_storage"],
                    target=cfg_instances["target"],
                    block=True,
                    duplicate=0,
                    proxmox_nodes=cfg_instances["nodes"]
                )

            vmid = self.proxmox_instance.get_vm_by_id_or_name(
                vmname=f"{stack_name}-{instance}"
            )["vmid"]
            cfg_instances["vmid"] = vmid
            print((
                f"Update parameters for instance "
                f"{stack_name}-{instance}"
            ))
            with open(
                file=os.path.abspath(os.path.expanduser(
                    cfg_instances["sshkey"]
                )),
                mode="r",
                encoding="utf-8"
            ) as handle:
                sshkey = handle.read()

            self.proxmox_instance.set_vms(
                filter_name="",
                sockets=-1,
                cpulimit=-1,
                vmid=vmid,
                vmname="",
                cores=cfg_instances["cores"],
                memory=cfg_instances["memory"],
                ipconfig=cfg_instances["ipconfig"],
                cipassword=cfg_instances["password"],
                ciuser=cfg_instances["user"],
                sshkey=sshkey
            )
            print(f"resize vm instance {stack_name}-{instance} disk")
            self.proxmox_instance.resize_vms_disk(
                vmid=vmid,
                size=cfg_instances["disk_size"],
                disk=cfg_instances["disk_device"]
            )
            # set tags
            print(f"set tags for vm instance {stack_name}-{instance}")
            self.proxmox_instance.set_tags(
                tags=";".join(cfg_instances["tags"]),
                filter_name=f'^{stack_name}-{instance}',
                set_mode="replace"
            )
            print((
                f"Add vm instance {stack_name}-{instance} "
                f"to ha group {stack_name}-{cfg_instances['ha_group']}"
            ))
            self.proxmox_instance.create_ha_resource(
                group=f"{stack_name}-{cfg_instances['ha_group']}",
                vmid=vmid,
                max_relocate=cfg_groups[
                    cfg_instances['ha_group']
                ]["max_relocate"],
                max_restart=cfg_groups[
                    cfg_instances['ha_group']
                ]["max_restart"]
            )
        # INSTANCE UPDATE (at least one property update)
        for instance, updated_data in differences["instances"][
            "updated"
        ].items():
            print(colored(
                    f"== instance {stack_name}-{instance}",
                    color="blue"
            ))
            # get current vm specification
            vm = self.proxmox_instance.get_vm_by_id_or_name(
                vmname=f"{stack_name}-{instance}"
            )
            # get disk name
            disk_device = self.expanded_config[
                "provision_instances"
            ][stack_name]["instances"][instance]["disk_device"]
            # # stop instance
            self.proxmox_instance.set_vms_status(
                status="stop",
                vmid=vm["vmid"]
            )
            self.proxmox_instance.vms_wait_for_status(
                status="stopped",
                vmid=vm["vmid"]
            )
            # get the currents tags as a list with some cleaning
            current_tags = vm["tags"].replace(",", ";").split(";")
            current_tags = [v.strip() for v in current_tags]
            updated_properties = {}

            # # iterate over updated instance properties
            for prop, val in updated_data.items():
                # queue updated tags
                if prop == "tags":
                    for tag_removed in val["removed"]:
                        if tag_removed in current_tags:
                            current_tags.remove(tag_removed)
                    for tag_added in val["added"]:
                        if tag_added not in current_tags:
                            current_tags.append(tag_added)
                else:
                    # queue updated properties
                    updated_properties[prop] = val
            # update effectively tags
            self.proxmox_instance.set_tags(
                tags=";".join(current_tags),
                filter_name=f"^{stack_name}-{instance}"
            )
            # update properties (capacity / auth)
            sk = None
            if "sshkey" in updated_properties:
                with open(
                    file=updated_properties["sshkey"]["new"],
                    encoding="utf-8",
                    mode="r"
                ) as handle:
                    sk = handle.read()
            do_update_vm = False
            properties = updated_properties.keys()
            properties = [
                p for p in properties if p not in [
                    "disk_size",
                    "tags"
                ]
            ]
            do_update_vm = True if len(properties) > 0 else False
            if do_update_vm:
                self.proxmox_instance.set_vms(
                    vmid=vm["vmid"],
                    vmname=f"{stack_name}-{instance}",
                    filter_name="",
                    sockets=None,
                    cpulimit=None,
                    cores=updated_properties[
                        "cores"
                    ]["new"] if "cores" in updated_properties else None,
                    memory=updated_properties[
                        "memory"
                    ]["new"] if "memory" in updated_properties else None,
                    ipconfig=updated_properties[
                        "ipconfig"
                    ]["new"] if "ipconfig" in updated_properties else None,
                    cipassword=updated_properties[
                        "cipassword"
                    ]["new"] if "cipassword" in updated_properties else None,
                    ciuser=updated_properties[
                        "ciuser"
                    ]["new"] if "ciuser" in updated_properties else None,
                    sshkey=sk if "sshkey" in updated_properties else None
                )
            # update disk size if needed
            if "disk_size" in updated_properties:
                self.proxmox_instance.set_vms_status(
                    status="stop",
                    vmid=vm["vmid"]
                )
                self.proxmox_instance.resize_vms_disk(
                    vmid=vm["vmid"],
                    size=updated_properties["disk_size"]["new"],
                    disk=disk_device
                )
            self.proxmox_instance.set_vms_status(
                status="start",
                vmid=vm["vmid"]
            )
        # UPDATE STACK STATE
        self.stack_write_state(
            stack_name=stack_name,
            stack_config=desired
        )
        # REMOVE PLAN FILE
        os.remove(
            os.path.abspath(
                os.path.expanduser(f"~/.proxcli/{stack_name}.plan")
            )
        )

    def stack_write_plan(self, stack_name, stack_plan):
        """Description of the function/method.

        Parameters:
            <param>: Description of the parameter

        Returns:
            <variable>: Description of the return value
        """
        if not os.path.exists(os.path.expanduser("~/.proxcli")):
            os.makedirs(os.path.expanduser("~/.proxcli/"))
        state_file = os.path.expanduser(f"~/.proxcli/{stack_name}.plan")
        with open(file=state_file, mode="w", encoding="utf-8") as handle:
            handle.write(json.dumps(stack_plan, indent=2))

    def stack_write_state(self, stack_name, stack_config):
        """Description of the function/method.

        Parameters:
            <param>: Description of the parameter

        Returns:
            <variable>: Description of the return value
        """
        stack_config = self.expanded_config["provision_instances"][stack_name]
        if not os.path.exists(os.path.expanduser("~/.proxcli")):
            os.makedirs(os.path.expanduser("~/.proxcli/"))
        state_file = os.path.expanduser(f"~/.proxcli/{stack_name}.state")
        with open(file=state_file, mode="w", encoding="utf-8") as handle:
            handle.write(json.dumps(stack_config, indent=2))

    def stack_delete(self, stack):
        """Description of the function/method.

        Parameters:
            <param>: Description of the parameter

        Returns:
            <variable>: Description of the return value
        """
        stack_config = self.expanded_config["provision_instances"][stack]
        instances = stack_config["instances"]
        groups = stack_config["ha_groups"]
        print("delete ha resources")
        self.proxmox_instance.delete_ha_resources(
            filter_name=f"^{stack}-"
        )
        for group, _ in groups.items():
            if not self.proxmox_instance.exists_ha_group(f"{stack}-{group}"):
                print(f"ha group {stack}-{group} does not exist")
            else:
                print(f"delete ha_group {stack}-{group}")
                self.proxmox_instance.delete_ha_group(
                    group=f"{stack}-{group}"
                )
        for instance, _ in instances.items():
            vm = self.proxmox_instance.get_vm_by_id_or_name(
                vmname=f"{stack}-{instance}"
            )
            if not vm:
                print(f"vm instance {stack}-{instance} not found")
            else:
                vmid = vm["vmid"]
                if vm["status"] == "running":
                    print(f"Stop instance {stack}-{instance}")
                    self.proxmox_instance.set_vms_status(
                        status="stop",
                        vmid=vmid
                    )
                    self.proxmox_instance.vms_wait_for_status(
                        status="stopped",
                        vmid=vmid
                    )
                print(f"remove instance {stack}-{instance}")
                self.proxmox_instance.delete_vms(
                    fitler_name=f"^{stack}-{instance}"
                )
        state_file = os.path.expanduser(f"~/.proxcli/{stack}.state")
        if os.path.exists(state_file):
            os.remove(state_file)


if __name__ == "__main__":
    CONFIG_BASE = "/home/david/Documents/infrastructure/vars/proxcli/"
    config_file = f"{CONFIG_BASE}/proxcli.yml"
    default_file = f"{CONFIG_BASE}/default.yml"
    so = StackOperations(
        config_file_path=config_file,
        default_file_path=default_file
    )

