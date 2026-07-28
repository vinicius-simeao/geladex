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
    r = requests.get(
        f"{PROXMOX_URL}/api2/json/cluster/resources?type=vm",
        headers=headers,
        verify=False,
        timeout=10
    )
    r.raise_for_status()
    return r.json()["data"]


def get_vm_ip(node, vmid):
    try:
        r = requests.get(
            f"{PROXMOX_URL}/api2/json/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces",
            headers=headers,
            verify=False,
            timeout=5
        )
        if r.status_code != 200:
            return None
        payload = r.json()
        data = payload.get("data")
        if not data:
            return None
        result = data.get("result", data) if isinstance(data, dict) else data
        for interface in result:
            if interface.get("name") == "lo":
                continue
            for ip in interface.get("ip-addresses", []):
                if ip.get("ip-address-type") == "ipv4" and not ip["ip-address"].startswith("127."):
                    return ip["ip-address"]
        return None
    except (requests.exceptions.RequestException, ValueError, KeyError):
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
