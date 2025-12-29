#!/usr/bin/env python3
import os
import tarfile
import tempfile
import shutil
import subprocess
import json
import re

COMMAND_MAP = {
    "journalctl": ("misc", "all-journalctl.out"),
    "lsblk": ("misc", "lsblk.out"),
    "blkid": ("misc", "blkid.out"),
    "ip addr show": ("misc", "ip.out"),
    "mount": ("misc", "mount.out"),
    "uptime": ("misc", "uptime.out"),
    "date": ("misc", "date.out"),
    "pxctl version": ("misc", "px-version.out"),
    "pxctl status": ("misc", "px-status.out"),
    "pxctl service kvdb members": ("misc", "px-kvdb.out"),
    "pxctl sv k m": ("misc", "px-kvdb.out"),
    "pxctl alerts show": ("misc", "px-alerts.out"),
    "pxctl a s": ("misc", "px-alerts.out"),
    "pxctl alerts show -j": ("misc", "px-alerts-show.out"),
    "pxctl a s -j": ("misc", "px-alerts-show.out"),
    "pxctl clouddrive list": ("misc", "px-clouddrive-list.out"),
    "pxctl cd l": ("misc", "px-clouddrive-list.out"),
}

def print_help():
    print("""
Portworx pxctl (offline diag shell)

Volume commands:
  pxctl volume list | pxctl v l
  pxctl volume list -j
  pxctl volume list -j <volume-id>
  pxctl volume inspect <volume-id> | pxctl v i <volume-id>
  pxctl volume inspect -j <volume-id>

Cluster / system:
  pxctl status
  pxctl version
  pxctl service kvdb members | pxctl sv k m
  pxctl alerts show
  pxctl alerts show -j
  pxctl clouddrive list
  pxctl config show | pxctl config s
  pxctl clusteruuid show | pxctl clusteruuid s

Host commands:
  journalctl
  lsblk
  blkid
  ip addr show
  mount
  uptime
  date

Notes:
  - '-j' may appear anywhere in the command
  - Pipes supported: | grep | egrep | less | more
  - Type 'exit' or 'quit' to leave
""")

def extract_diag(tar_path):
    tmp = tempfile.mkdtemp(prefix="px-diag-")
    with tarfile.open(tar_path, "r:gz") as tar:
        for m in tar.getmembers():
            m.name = m.name.lstrip("/")
            tar.extract(m, tmp)
    return tmp

def find_misc_folder(base):
    root = os.path.join(base, "var/lib/osd/diagfiles")
    for d in os.listdir(root):
        misc = os.path.join(root, d, "misc")
        if os.path.isdir(misc):
            return misc
    return None

def find_etc_folder(base):
    root = os.path.join(base, "var/lib/osd/diagfiles")
    for d in os.listdir(root):
        etc = os.path.join(root, d, "etc/pwx")
        if os.path.isdir(etc):
            return etc
    return None

def stream_file(path, pipe=None):
    if pipe in ("less", "more"):
        pager = subprocess.Popen([pipe], stdin=subprocess.PIPE, text=True)
        with open(path) as f:
            for line in f:
                pager.stdin.write(line)
        pager.stdin.close()
        pager.wait()
        return

    with open(path) as f:
        for line in f:
            if pipe:
                if pipe.startswith("grep ") and pipe[5:].strip() not in line:
                    continue
                if pipe.startswith("egrep ") and not re.search(pipe[6:].strip(), line):
                    continue
            print(line.rstrip())

def parse_command(cmd):
    parts = cmd.split()
    is_json = "-j" in parts
    parts = [p for p in parts if p != "-j"]
    vol_id = next((p for p in parts if p.isdigit()), None)
    base_cmd = " ".join(p for p in parts if not p.isdigit())
    return base_cmd, is_json, vol_id

def load_volumes(misc):
    with open(os.path.join(misc, "px-volumes.out")) as f:
        return json.load(f)

def human_size(b):
    b = int(b)
    for u in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if b < 1024:
            return f"{b} {u}"
        b //= 1024

def yes_no(value):
    return "yes" if value else "no"

def format_shared(spec):
    if spec.get("sharedv4"):
        return "v4"
    elif spec.get("shared"):
        return "yes"
    else:
        return "no"

def volume_list(misc):
    vols = load_volumes(misc)

    print(
        "ID                      NAME                                    "
        "SIZE    HA  SHARED ENCRYPTED PROXY-VOLUME IO_PRIORITY STATUS"
    )

    for v in vols:
        state = (
            "attached on " + v["attached_on"]
            if v["attached_on"]
            else "detached"
        )

        shared = format_shared(v["spec"])
        encrypted = yes_no(v["spec"].get("encrypted", False))
        proxy = yes_no(v["spec"].get("proxy_volume", False))

        print(
            f'{v["id"]:23} '
            f'{v["locator"].get("name",""):40} '
            f'{human_size(v["spec"]["size"]):7} '
            f'{v["spec"]["ha_level"]:3} '
            f'{shared:7} '
            f'{encrypted:9} '
            f'{proxy:12} '
            f'{v["spec"].get("cos","").upper():8} '
            f'{v["status"]} - {state}'
        )

def volume_inspect(v):
    print(f'Volume                   :  {v["id"]}')
    print(f'Name                     :  {v["locator"].get("name","")}')
    print(f'Size                     :  {human_size(v["spec"]["size"])}')
    print(f'Format                   :  {v["spec"].get("format","")}')
    print(f'HA                       :  {v["spec"]["ha_level"]}')
    print(f'IO Priority              :  {v["spec"].get("cos","")}')
    print(f'Creation time            :  {v.get("ctime","")}')
    print(f'Shared                   :  {format_shared(v["spec"])}')
    print(f'Status                   :  {v["status"]}')
    print(f'State                    :  {"attached: " + v["attached_on"] if v["attached_on"] else "detached"}')
    print(f'Last Attached            :  {v.get("detach_time","")}')
    print(f'Device Path              :  {v.get("device_path","")}')
    print(f'Bytes used               :  {human_size(v.get("usage",0))}')
    labels = v["spec"].get("volume_labels",{})
    if labels:
        print("Labels                   :  " + ",".join(f"{k}={v}" for k,v in labels.items()))
    mo = v["spec"].get("mount_options",{}).get("options",{})
    if mo:
        print("Mount Options            :  " + ",".join(mo.keys()))
    print("Replica sets on nodes:")
    for i, rs in enumerate(v.get("replica_sets",[])):
        print(f"    Set {i}")
        for n,p in zip(rs["nodes"], rs["pool_uuids"]):
            print(f"      Node           : {n}")
            print(f"       Pool UUID     : {p}")

def main():
    import sys
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <diag.tar.gz>")
        return

    base = extract_diag(sys.argv[1])
    misc = find_misc_folder(base)
    etc = find_etc_folder(base)

    try:
        while True:
            cmd = input("pxctl> ").strip()

            if not cmd:
                continue

            if cmd in ("exit", "quit"):
                break

            if cmd in ("pxctl", "help", "?", "pxctl help", "pxctl --help"):
                print_help()
                continue

            if "|" in cmd:
                left, pipe = map(str.strip, cmd.split("|", 1))
            else:
                left, pipe = cmd, None

            base_cmd, is_json, vol_id = parse_command(left)

            if base_cmd in ("pxctl volume list", "pxctl v l"):
                vols = load_volumes(misc)
                if is_json:
                    print(json.dumps(
                        [v for v in vols if not vol_id or v["id"] == vol_id],
                        indent=2
                    ))
                else:
                    volume_list(misc)
                continue

            if base_cmd in ("pxctl volume inspect", "pxctl v i"):
                vols = load_volumes(misc)
                v = next((v for v in vols if v["id"] == vol_id), None)
                if not v:
                    print(f"Volume {vol_id} not found")
                elif is_json:
                    print(json.dumps(v, indent=2))
                else:
                    volume_inspect(v)
                continue

            if base_cmd in ("pxctl config show", "pxctl config s"):
                stream_file(os.path.join(etc, "config.json"))
                continue

            if base_cmd in ("pxctl clusteruuid show", "pxctl clusteruuid s"):
                stream_file(os.path.join(etc, "cluster_uuid"))
                continue

            if base_cmd in COMMAND_MAP:
                loc, fname = COMMAND_MAP[base_cmd]
                root = misc if loc == "misc" else etc
                stream_file(os.path.join(root, fname), pipe)
            else:
                print("Unknown command")

    finally:
        shutil.rmtree(base)

if __name__ == "__main__":
    main()
