#!/usr/bin/env python3

import requests
import json
import os

PROXMOX_URL = os.getenv("PROXMOX_URL")
PROXMOX_TOKEN_ID = os.getenv("PROXMOX_TOKEN_ID")
PROXMOX_TOKEN_SECRET = os.getenv("PROXMOX_TOKEN_SECRET")

headers = {
    "Authorization": f"PVEAPIToken={PROXMOX_TOKEN_ID}={PROXMOX_TOKEN_SECRET}"
}

inventory = {
    "_meta": {"hostvars": {}},
    "all": {"hosts": []}
}

def get_vms():
    r = requests.get(f"{PROXMOX_URL}/api2/json/cluster/resources?type=vm", headers=headers, verify=False)
    return r.json()["data"]

def get_vm_ip(node, vmid):
    r = requests.get(
        f"{PROXMOX_URL}/api2/json/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces",
        headers=headers,
        verify=False
    )
    data = r.json()["data"]
    for interface in data:
        if interface["name"] == "lo":
            continue
        for ip in interface.get("ip-addresses", []):
            if ip["ip-address-type"] == "ipv4":
                return ip["ip-address"]
    return None

for vm in get_vms():
    if vm["status"] != "running":
        continue

    node = vm["node"]
    vmid = vm["vmid"]
    name = vm["name"]

    ip = get_vm_ip(node, vmid)

    if ip:
        inventory["all"]["hosts"].append(name)
        inventory["_meta"]["hostvars"][name] = {
            "ansible_host": ip
        }

print(json.dumps(inventory))
