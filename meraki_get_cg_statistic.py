import json
import requests
import platform                 # for getting the operating system name
import sys


# check if scirpt is executed on linux system
if platform.system().lower() != 'linux':
    print(f'ERROR\nThis scrpit work only on Linux systemes')
    sys.exit()
else:
    from tabulate import tabulate   # for formating print results


def get_user_input(message, error_message):
    # collect user input and make sure it is not blank
    x = input(message)
    while len(x.strip()) == 0:
        x = input(error_message)
    return x

def check_user_input_number(user_input, all_org_list):
    # check if user input is number and in valid range
    try:
        int(user_input)
        if int(user_input) <= 0 or int(user_input) > len(all_org_list):
            return False
        else:
            return True
    except ValueError:
        return False

def api_request(url):
    try:                                                    # try to send API call
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:            # in case of error exit out from script
        raise SystemExit(err)

def get_all_organizations():
    # using API key, get all availbe organizations
    print(f'Collecting all organization names:')
    url = f'https://dashboard.meraki.com/api/v0/organizations/'
    response_json = api_request(url)
    return response_json


def print_organization_name(all_org):
    # print all organizatin names to the screen, user will chose one in get_organization_id
    counter = 1
    for org in all_orgs:
        print(f"{counter}) {org['name']}")
        counter += 1

def get_organization_id(all_org_list):
    # get organization id for organization user chose
    organization_number = get_user_input('\nChose Organization (number) from the list: ', \
    'Input cannot be empty. Chose a number: ')         # collect organization name for user input
    
    # check if users has eneterd valid number and if yes return org id
    if check_user_input_number(organization_number, all_org_list) == False:
        get_organization_id(all_org_list)
    else:
        return all_org_list[int(organization_number)-1]['id']


def get_networks(org_id):
    # get all network names and ids, save the result to the list
    print(f'Collecting Networks')
    url = f'https://dashboard.meraki.com/api/v0/organizations/{org_id}/networks'
    response_json = api_request(url)
    
    networks = []
    for network in response_json:
        tmp_dict = {}
        tmp_dict["id"] = network['id']
        tmp_dict["name"] = network['name']
        networks.append(tmp_dict)

    return(networks)

def get_cellular_gateways(org_id):
    # get statistics from all cellular gateways in the organization
    print(f'Collecting cellular gateways statistics')
    url = f'https://dashboard.meraki.com/api/v1/organizations/{org_id}/cellularGateway/uplink/statuses'
    response_json = api_request(url)

    return response_json

def network_gateways(networks, gateways):
    # description
    results_list = []
    for gateway in gateways:
        for network in networks:
            tmp_list = []
            if gateway['networkId'] == network['id']:
                tmp_list.extend((
                    network['name'],
                    gateway['lastReportedAt'],
                    gateway['model']
                    ))
                if gateway['uplinks']:
                    if gateway['uplinks'][0]['status'] == 'failed':     # chage font color if status is failed
                        tmp_list.append(f"\033[1;31;40m{gateway['uplinks'][0]['status']}\033[1;37;40m")
                    else:
                        tmp_list.append(gateway['uplinks'][0]['status'])
                    tmp_list.extend((
                        gateway['uplinks'][0]['provider'],
                        gateway['uplinks'][0]['connectionType']
                        ))
                    if gateway['uplinks'][0]['signalStat']:
                        tmp_list.append(gateway['uplinks'][0]['signalStat'])
                results_list.append(tmp_list)
    return results_list

def print_results(results_list):
    # print to cosole information gathered in def get_data_print
    print(tabulate(results_list, headers=['Location', 'Last Reported At', 'Model', 'Status', 'Provider', 'Connection Type', 'Signal Strength']))

# get user input
key = get_user_input('Enter Meraki API key: ', \
    'Input cannot be empty. Enter API key: ')                   # collect API key for user input     


# format console output
print('-' * 20 + '\n')

# prepare http headers
headers = {'X-Cisco-Meraki-API-Key': key}

all_orgs = get_all_organizations()                                  # get all organizations
print_organization_name(all_orgs)                                   # print organizations
org_id = get_organization_id(all_orgs)                              # get organization id
# format console output
print('-' * 20 + '\n')
networks = get_networks(org_id)                                     # get networks
gateways = get_cellular_gateways(org_id)                            # get cellular gateways statistics
gateways_statistic = network_gateways(networks, gateways)           # corelate networks and gateways information
sorted_gw_stat = sorted(gateways_statistic, key=lambda x: x[0])     # sort the statistic list by location name

# format console output
print('-' * 20 + '\n')

print_results(sorted_gw_stat)           # print to the screen