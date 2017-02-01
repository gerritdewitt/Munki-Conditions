#!/usr/bin/env python

# network-hw.py
# Script for populating Munki Conditions that report on
# network hardware capabilities of the computer.
# References: Refer to the markdown files in the source tree
# (ReadMe.md and those in the Documentation folder).

# Written by Gerrit DeWitt (gdewitt@gsu.edu)
# This file created 2015-08-25 (extensions), 2015-09-11 (initial installcheck scripts for bundle eligibility)
# 2015-11-10 (extensions), 2015-11-24 (extensions/conditions), 2016-02-16, 2016-06-15, 2016-06-27
# 2017-01-13, 2017-01-26, 2017-01-31.
# Copyright Georgia State University.
# This script uses publicly-documented methods known to those skilled in the art.

import sys, plistlib, xml, subprocess, os, logging, time
this_dir = os.path.dirname(os.path.realpath(__file__))
shared_support_dir = os.path.join(this_dir,'shared-support')
sys.path.append(shared_support_dir)
import conditions_common

# Types of interfaces on which this condition reports:
global NETWORK_INTERFACES_TYPES_LIST
NETWORK_INTERFACES_TYPES_LIST = []
NETWORK_INTERFACES_TYPES_LIST.append('ethernet')
NETWORK_INTERFACES_TYPES_LIST.append('airport')
NETWORK_INTERFACES_TYPES_LIST.append('wi-fi')

def system_profiler_get_ethernet_and_wifi_info():
    '''Runs system_profiler SPNetworkDataType and parses output.
        Returns an array of dictionaries containing attributes
        for the network interface types on which we should report.'''
    # Defaults:
    output_dict = {}
    net_items_array = []
    filtered_net_items_array = []
    # Run system_profiler:
    try:
        output = subprocess.check_output(['/usr/sbin/system_profiler',
                                          'SPNetworkDataType',
                                          '-xml'])
    except subprocess.CalledProcessError:
        output = ''
    # Parse output:
    if output:
        try:
            output_dict = plistlib.readPlistFromString(output)
        except xml.parsers.expat.ExpatError:
            pass
    if output_dict:
        try:
            net_items_array = output_dict[0]['_items']
        except IndexError:
            pass
        except KeyError:
            pass
    for net_item in net_items_array:
        should_include_item = False
        try:
            if net_item['type'].lower() in NETWORK_INTERFACES_TYPES_LIST:
                should_include_item = True
        except KeyError:
            continue
        # Gather a minimal set of network identification data:
        if should_include_item:
            filtered_net_item = {}
            try:
                filtered_net_item['interface'] = net_item['interface']
            except KeyError:
                filtered_net_item['interface'] = ''
            try:
                filtered_net_item['name'] = net_item['_name']
            except KeyError:
                filtered_net_item['name'] = ''
            try:
                filtered_net_item['type'] = net_item['type']
            except KeyError:
                filtered_net_item['type'] = ''
            # MAC address:
            filtered_net_item['hw_address'] = ''
            try:
                eth_dict = net_item['Ethernet']
            except KeyError:
                eth_dict = {}
            if eth_dict:
                try:
                    filtered_net_item['hw_address'] = eth_dict['MAC Address']
                except KeyError:
                    pass
            # Append:
            if filtered_net_item['interface'] and filtered_net_item['hw_address']:
                filtered_net_items_array.append(filtered_net_item)
    # Return:
    return filtered_net_items_array

def system_has_wifi(given_interface_array):
    '''Returns true iff the given array of interfaces
        has at least one that's a Wi-Fi (AirPort) type.'''
    wifi_present = False
    for net_item in given_interface_array:
        if net_item['type'].lower() in ["airport","wi-fi"]:
            wifi_present = True
            break
    return wifi_present

def main():
    '''Main logic for this script'''
    ethernet_and_wifi_interfaces = system_profiler_get_ethernet_and_wifi_info()
    has_wi_fi = system_has_wifi(ethernet_and_wifi_interfaces)
    # Write Conditions:
    conditions_common.write_conditions({"ethernet_and_wifi_interfaces":ethernet_and_wifi_interfaces,
                                       "has_wi_fi":has_wi_fi})
    # Finish:
    sys.exit(0)

# Run main.
if __name__ == "__main__":
    main()
