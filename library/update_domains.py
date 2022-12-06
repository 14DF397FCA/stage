#!/usr/bin/python3.6

# Copyright: (c) 2019, Gennadii Ilyashenko <gennadii.ilyashenko@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
import random
import subprocess
from typing import List, Dict

#   Get list of opened ports
CMD = "netstat -lntu | awk 'NR>2{print $4}' | sed 's/.*://' | sort -n | uniq"

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'gennadii.ilyashenko@gmail.com'
}

DOCUMENTATION = '''
---
module: update_domains

short_description: This module is using to generate random ports for locations

version_added: "2.9"

description:
    - "This module is using to generate random ports for locations in deployment staging"

options:
    domains:
        description:
            - Set variable locations
        required: true
    domain_name:
        description:
            - Set base domain
        required: true
    lower_port:
        description:
            - Used to generate random port, with this int parameters we set lower border of random port
        required: false
        default: 20000
    upper_port:
        description:
            - Used to generate random port, with this int parameters we set upper border of random port
        required: false
        default: 30000

author:
    - Gennadiy Ilyashenko (gennadii.ilyashenko@gmail.com)
'''

EXAMPLES = '''
# Pass in a message
- update_domains:
    data: "{{ domains }}"
  register: out
  tags: deploy
# Set result back to source variable
- set_fact:
    locations: "{{ out.data }}"
  tags: deploy
# See result
- debug:
    msg: "For location {{ item.location }} will use port {{ item }}"
  when: item.port is defined
  loop: "{{ locations }}"
  tags: deploy
'''

RETURN = '''
data:
    description: Update locations, with random ports
    type: list
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule


def get_opened_ports() -> List[int]:
    def extract_port(raw):
        return raw if raw[-1] != "\\n" else raw[0:-1]

    ps = subprocess.Popen(CMD, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    a = []
    for line in ps.stdout:
        a.append(int(extract_port(line.decode())))
    return a


def random_port(lower_port: int, upper_port: int) -> int:
    return random.randint(lower_port, upper_port)


def get_random_port(lower_port: int, upper_port: int) -> int:
    opened_ports = get_opened_ports()

    rand_port = random_port(lower_port=lower_port, upper_port=upper_port)
    while rand_port in opened_ports:
        rand_port = random_port(lower_port=lower_port, upper_port=upper_port)
    return rand_port


def update_domains(domains: List, staging_path: str, domain_name: str, nginx_vhost_path: str,
                   lower_port: int = 20000, upper_port: int = 30000, tls_generate: bool = None,
                   disable_sha1_header: bool = None,
                   base_auth: Dict = None) -> List:
    for domain in domains:
        #   When name is equal to "~" (tilda) - set up "domain_name" as FQDN
        if domain["name"] == "~":
            domain["fqdn"] = domain_name
        #   If value of "name" ends with "." (dot) consider that variable contain FQDN
        #   NOTE: FQDN should be resolvable and reachable
        elif str(domain["name"]).endswith("."):
            domain["fqdn"] = domain["name"][:-1]
        #   If value of "name" ends with ".~" (dot and tilda) consider that "name" contain name of subdomain for base domain (~)
        elif str(domain["name"]).endswith(".~"):
            sub = str(domain["name"]).split(".~")[0]
            domain["fqdn"] = f"{sub}.{domain_name}"
        #   In this case we just assign FQDN equal as domain name
        #   Behavior like "name" is equal to "~" (tilda)
        else:
            domain["fqdn"] = domain_name

        if base_auth is not None and "base_auth" not in domain:
            domain["base_auth"] = base_auth

        if "base_auth" in domain:
            base_auth_file: Dict = dict()
            base_auth_file["username"] = domain["base_auth"]["username"]
            base_auth_file["password"] = domain["base_auth"]["password"]
            base_auth_file["base_auth_file_name"] = f"{staging_path}/{domain['fqdn']}.base_auth"
            domain["base_auth"] = base_auth_file

        if disable_sha1_header is not None and "disable_sha1_header" not in domain:
            domain["disable_sha1_header"] = disable_sha1_header

        if tls_generate is not None and "tls_generate" not in domain:
            domain["tls_generate"] = tls_generate

        if "tls_generate" in domain:
            if domain["tls_generate"]:
                tls_enabled: Dict = dict()
                tls_enabled["tls_fullchain"] = f"{staging_path}/{domain['fqdn']}.fullchain.pem"
                tls_enabled["tls_key"] = f"{staging_path}/{domain['fqdn']}.privkey.pem"
                tls_enabled["tls_csr"] = f"{staging_path}/{domain['fqdn']}.csr"
                tls_enabled["tls_crt"] = f"{staging_path}/{domain['fqdn']}.crt"
                tls_enabled["tls_account_key"] = f"{staging_path}/{domain['fqdn']}.account.key"
                tls_enabled["tls_intermediate"] = f"{staging_path}/{domain['fqdn']}.intermediate.pem"
                tls_enabled["tls_acme_nginx_path"] = f"{nginx_vhost_path}/{domain['fqdn']}.conf"
                domain["tls_enabled"] = tls_enabled

        for location in domain["locations"]:
            if "port_name" in location:
                location["port"] = get_random_port(lower_port=lower_port, upper_port=upper_port)
    return domains


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        domains=dict(type='list', required=True),
        domain_name=dict(type="str", required=True),
        staging_path=dict(type="str", required=True),
        nginx_vhost_path=dict(type="str", required=True),
        tls_generate=dict(type="bool", required=True),
        disable_sha1_header=dict(type="bool", required=True),
        base_auth=dict(type="dict", required=True),
        lower_port=dict(type="int", required=False, default=20000),
        upper_port=dict(type="int", required=False, default=30000),
    )

    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    update_domains(domains=module.params["domains"],
                   staging_path=module.params["staging_path"],
                   domain_name=module.params["domain_name"],
                   nginx_vhost_path=module.params["nginx_vhost_path"],
                   tls_generate=module.params["tls_generate"],
                   base_auth=module.params["base_auth"],
                   disable_sha1_header=module.params["disable_sha1_header"],
                   lower_port=module.params["lower_port"],
                   upper_port=module.params["upper_port"])

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    result['domains'] = module.params['domains']

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    if module.params['domains'] == list():
        module.fail_json(msg='You requested this to fail', **result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
