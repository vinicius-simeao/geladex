#!/usr/bin/env python3

import requests
import json
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXMOX_URL = os.getenv("PROXMOX_URL")
PROXMOX_TOKEN_ID = os.getenv("PROXMOX_TOKEN_ID")
PROXMOX_TOKEN_SECRET = os.getenv("PROXMOX_TOKEN_SECRET")

if not PROXMOX_URL or not PROXMOX_TOKEN_ID or not PROXMOX_TOKEN_SECRET:
    print(json.dumps({"_meta": {"hostvars": {}}, "all": {"hosts": []}}))
    exit(0)

headers = {
    "Authorization": f"PVEAPIToken={PROXMOX_TOKEN_ID}={PROXMOX_TOKEN_SECRET}"
}

inventory = {
    "_meta": {"hostvars": {}},
    "all": {"hosts": []}
}

def safe_request(url):
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def get_vms():
    data = safe_request(f"{PROXMOX_URL}/api2/json/cluster/resources?type=vm")
    if data and "data" in data:
        return data["data"]
    return []

def get_vm_ip(node, vmid):
    data = safe_request(
        f"{PROXMOX_URL}/api2/json/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces"
    )

    if not data or "data" not in data or not data["data"]:
        return None

    for interface in data["data"]:
        if interface.get("name") == "lo":
            continue

        for ip in interface.get("ip-addresses", []):
            if ip.get("ip-address-type") == "ipv4":
                address = ip.get("ip-address")
                if address and not address.startswith("127."):
                    return address

    return None

for vm in get_vms():
    if vm.get("status") != "running":
        continue

    node = vm.get("node")
    vmid = vm.get("vmid")
    name = vm.get("name")

    if not node or not vmid or not name:
        continue

    ip = get_vm_ip(node, vmid)

    if ip:
        inventory["all"]["hosts"].append(name)
        inventory["_meta"]["hostvars"][name] = {
            "ansible_host": ip
        }

print(json.dumps(inventory))
