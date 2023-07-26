# Introduction

proxcli aim to be a unique client for proxmox running over proxmox api. It is not as complete as proxmox tooling but have the hability to work at cluster level from a remote computer. It will never implement all proxmox feature, it is a sysop tool used for daily tasks. 

Feel free to contribute with suggestion, documentation or code. 

David GUENAULT (david dot guenault at gmail dot com)

# technical credits

Thx to:

- proxmox for this wonderful piece of technology
- typer (and click) for the cli argument management
- proxmoxer for the api wrapper against proxmox api

# installation

just issue the command **make** within this repository. It will install all the required libraries within a virtualenv

```bash
make
```

You can also install it with the classical command

``` bash
python setup.py install
```

# configuration
you can easyli generate a configuration skeleton with the following command:

```bash
proxcli config save --host [comma separated list of pve nodes names] --user [username] --password []
```

The configuration will be stored at: **$HOME/.proxmox**

NB: specify all of your pvenodes. If a node fail, proxcli will try to connect to the first available pve node

# configuration customization

TBD

# before using

proxcli is installed in a virtualenv. Don't forget to activate before using

```bash 
source /path/to/repository/venv/bin/activate
```

# Commands tree

Here is an overview of the available commands in proxcli

```
proxmox
    config
        create --hosts --user --password
        show
    inventory
        save --out --path
        show --out
    nodes
        list --filter --out
        networks --nodes --types --out [not implemented yet]
        tasks --nodes 
        storages
            list --out --nodes [Not implemented yet]
    cluster
        storages
            list
        log [not implemented yet]
    vms
        list --filter --out --nodes --status
        migrate --target-node  [ --vmid | --filter ]
        nextId
        reset 
        start [--filter | --vmid ]
        stop [--filter | --vmid ]
        suspend [--filter | --vmid ]
        reset [--filter | --vmid ]
        delete [--filter | --vmid ]
        clone --vmid --source-node --target-node --description --full --name --storage --pool  
        tags
            set --tags --filter
            list 
```