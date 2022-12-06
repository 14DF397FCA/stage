#!/usr/bin/python3.6

# Copyright: (c) 2019, Gennadii Ilyashenko <gennadii.ilyashenko@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
import os
import random
import subprocess
from typing import List, Dict
from dotenv import load_dotenv

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


def get_random_port(lower_port: int, upper_port: int):
    opened_ports = get_opened_ports()

    def rand_port():
        return random.randint(lower_port, upper_port)

    rand_port = rand_port()
    while rand_port in opened_ports:
        rand_port = rand_port()
    return rand_port


def load_exists_env(env_file: str):
    if os.path.exists(env_file):
        load_dotenv(dotenv_path=env_file, verbose=True, override=True)


def public_services(services: List, env_file: str, lower_port: int = 20000, upper_port: int = 30000) -> Dict:
    load_exists_env(env_file)

    services_updated: Dict = dict()

    for service_name in services:
        if service_name in os.environ:
            val = str(os.getenv(service_name)).strip()
        else:
            val = get_random_port(lower_port=lower_port, upper_port=upper_port)
        services_updated[service_name] = val

    return services_updated


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        services=dict(type="list", required=True),
        env_file=dict(type="str", required=True),
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
    services_updated = public_services(services=module.params["services"],
                                       env_file=module.params["env_file"],
                                       lower_port=module.params["lower_port"],
                                       upper_port=module.params["upper_port"])

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    result["original_message"] = module.params["services"]
    result["services"] = services_updated
    result["message"] = services_updated

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    if module.params["services"] == list():
        module.fail_json(msg="You requested this to fail", **result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
