# Offline PXCTL Simulator

This Python script simulates pxctl commands offline by reading pre-captured diagnostic files. Useful for inspecting Portworx volumes, cluster info, and system state without a live cluster.

# Requirements
Python 3.x

# Usage
./px-diag-analyzer.py <diag.tar.gz>

Once inside the interactive prompt:
pxctl>

Help Page
Type pxctl at the prompt to see the help page:

Offline PXCTL Help
```
Volume Commands:
  pxctl volume list | pxctl v l           Show summary of all volumes
  pxctl volume list -j | pxctl v l -j    Show full JSON of all volumes
  pxctl volume list -j <volume-id>       Show JSON of a specific volume
  pxctl volume inspect <volume-id> | pxctl v i <volume-id>    Show detailed volume info
  pxctl volume inspect <volume-id> -j    Show JSON of a specific volume

Cluster & Config Commands:
  pxctl config show | pxctl config s     Show offline cluster configuration
  pxctl clusteruuid show | pxctl clusteruuid s   Show cluster UUID
  pxctl version                           Show Portworx version
  pxctl status                            Show cluster status

Service & Alerts:
  pxctl service kvdb members | pxctl sv k m   Show KVDB members
  pxctl alerts show | pxctl a s               Show alerts
  pxctl alerts show -j | pxctl a s -j        Show alerts in JSON
  pxctl clouddrive list | pxctl cd l         Show cloud drive info

System Commands (offline):
  uptime       Show system uptime
  date         Show system date
  journalctl   Show logs
  lsblk        Show block devices
  blkid        Show block IDs
  ip addr show Show network interfaces
  mount        Show mounted filesystems

Other:
  Press Enter to continue (no action)
  exit, quit   Exit the simulator
```

