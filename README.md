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

just issue the command **make** within this repository. It will install all the required libraries within a virtualenv. you just have to activate virtualenvironment to use proxcli

```bash
make
source venv/bin/activate
proxcli --help
```

You can also install it with the classical command

``` bash
python setup.py install
proxcli --help
```

Or through pip

```bash
pip install -r requirements
python proxcli.py --help
```

# upgrading

Just pull the new branch ans issue the command from within the repository

``` bash
python setup.py
```

# configuration

The configuration will be stored at: **$HOME/.proxmox**

NB: specify all of your pvenodes. If a node fail, proxcli will try to connect to the first available pve node

```ini
[credentials]
hosts=host1,host2,...,hostn
user=user
password=password
[headers]
nodes=node,status
qemu=vmid,name,status,pid,node,cpu,mem,template,ip,tags
lxc=vmid,name,status,pid,node,cpu,mem,ip,tags
storage=storage,node,content,type,active,enabled,shared,used_fraction
tasks=starttime,endtime,node,user,type,id,status
ha_groups=group,type,nodes,digest,restricted,nofailback
ha_resources=vmid,name,group,type,digest,sid,max_relocate,state
cluster_log=date,severity, user,msg,node,pid,tag,uid
cluster_status=id,type,quorate,version,name,nodes
cluster_status_node=id,nodeid,online,name,type,local,ip,level
[data]
colorize=online:green,offline:red,running:green,stopped:red,k3s:yellow,failed:red,error:red,OK:green,problems:red,panic:red,alert:red,critical:red,warning:orage,notice:blue,info:blue,debug:violet
style=STYLE_BOX
[tasks]
polling_interval=1
timeout=300
```

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