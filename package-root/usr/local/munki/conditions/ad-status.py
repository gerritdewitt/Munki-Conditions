#!/usr/bin/env python

# ad-status.py
# Script for populating Munki Conditions that report on
# connectivity to Active Directory.  When used in conjunction
# with a conditional managed install for an AD directory service
# config profile, unbound systems may be bound automatically.
# References: Refer to the markdown files in the source tree
# (ReadMe.md and those in the Documentation folder).

# Written by Gerrit DeWitt (gdewitt@gsu.edu)
# This file created 2015-08-25 (extensions), 2015-09-11 (initial installcheck scripts for bundle eligibility)
# 2015-11-10 (extensions), 2015-11-24 (extensions/conditions), 2016-02-16, 2016-06-15, 2016-06-27
# 2017-01-13, 2017-02-20.
# Copyright Georgia State University.
# This script uses publicly-documented methods known to those skilled in the art.

# Variables:
global AD_FOREST, AD_DOMAIN
AD_FOREST = "example.org"
AD_DOMAIN = "domain.example.org"
global DEPENDENT_CONFIG_PROFILE_IDENTIFIERS
DEPENDENT_CONFIG_PROFILE_IDENTIFIERS = ["org.sample.config.profile.active-directory","org.sample.config.profile.8021X"]

import sys, plistlib, xml, subprocess, os, logging, time
this_dir = os.path.dirname(os.path.realpath(__file__))
shared_support_dir = os.path.join(this_dir,'shared-support')
sys.path.append(shared_support_dir)
import conditions_common

def dscl_lookup_computer_record(given_forest,given_domain,given_computer_account):
    '''Looks up the given computer account using dscl to test communication
        with the domain.  Returns true iff:
        1. dscl can communicate with AD, and
        2. dscl can look up and read attributes of the computer record, and
        3. the computer record's meta node location contains the
           given domain or forest.
        Otherwise, returns false.'''
    # Defaults:
    record_in_domain_or_forest = False
    # Loop:
    t = 1
    while True:
        if t > 5:
            break
        # Call dscl:
        output_dict = {}
        try:
            output = subprocess.check_output(['/usr/bin/dscl',
                                              '-plist',
                                              '/Search',
                                              'read',
                                              'Computers/%s' % given_computer_account])
        except subprocess.CalledProcessError:
            output = ''
        if output:
            output_dict = plistlib.readPlistFromString(output)
        if output_dict:
            break
        # Sleep and try again if no output:
        time.sleep(5)
        t += 1
    # Parse output:
    try:
        meta_node_attr = output_dict['dsAttrTypeStandard:AppleMetaNodeLocation']
    except KeyError:
        meta_node_attr = []
    for m in meta_node_attr:
        if given_forest.lower() in m.lower():
            record_in_domain_or_forest = True
        if given_domain.lower() in m.lower():
            record_in_domain_or_forest = True
    # Return:
    return record_in_domain_or_forest

def dsconfigad_get_computer_record(given_forest,given_domain):
    '''Runs dsconfigad -show and inspects its output.
        Returns the computer record name if all these conditions are met:
        1. macOS thinks the system is bound, and
        2. the forest and domain match what we expect, and
        3. dsconfigad returns a computer record name.
        In all other cases, a blank string is returned.'''
    # Defaults:
    measured_forest = ''
    measured_domain = ''
    computer_account = ''
    # Call dsconfigad:
    try:
        output = subprocess.check_output(['/usr/sbin/dsconfigad',
                                          '-xml',
                                          '-show'])
    except subprocess.CalledProcessError:
        output = ''
    # Try to parse output:
    output_dict = {}
    if output:
        try:
            output_dict = plistlib.readPlistFromString(output)
        except xml.parsers.expat.ExpatError:
            pass
    if output_dict:
        try:
            measured_forest = output_dict['General Info']['Active Directory Forest']
        except KeyError:
            pass
        try:
            measured_domain = output_dict['General Info']['Active Directory Domain']
        except KeyError:
            pass
        try:
            computer_account = output_dict['General Info']['Computer Account']
        except KeyError:
            pass
    # If forest and domain match, and we have a computer record,
    # return that record name.
    if measured_forest.lower() == given_forest.lower() and measured_domain.lower() == given_domain.lower():
        if computer_account:
            return computer_account
    # Otherwise, return blank string:
    return ''

def dig_lookup_dns_srv(given_forest,given_domain):
    '''Performs DNS-SRV queries to see if we have domain controllers available.
        Returns true if dig found a DNS-SRV record for the global catalog for our domain.
        Returns false otherwise.'''
    # Defaults:
    ad_gc_available = False
    # Loop:
    t = 1
    while True:
        if t > 5:
            break
        output_array = []
        answer_section_index = -1
        # Call dig:
        try:
            output = subprocess.check_output(['/usr/bin/dig',
                                              '-t',
                                              'SRV',
                                              '_gc._tcp.%s' % given_forest])
        except subprocess.CalledProcessError:
            output = ''
        # Try to parse output:
        if output:
            output_array = output.split('\n')
        if output_array:
            try:
                answer_section_index = output_array.index(';; ANSWER SECTION:')
            except ValueError:
                pass
        # Break if answer section has our domain:
        if answer_section_index >= 0:
            for i in range(answer_section_index+1,len(output_array)):
                if given_domain.lower() in output_array[i].lower():
                    ad_gc_available = True
                    break
                if given_forest.lower() in output_array[i].lower():
                    ad_gc_available = True
                    break
                if ';' in output_array[i]: # new section; ignore from here
                    break
        # Sleep and try again if no output:
        t += 1
        time.sleep(5)
    # Return:
    return ad_gc_available

def main():
    '''Main logic for this script'''
    # Assume not on network unless we prove otherwise.
    ad_status = "not-on-network"

    # Network test:
    logging.info('Looking for DNS-SRV records...')
    ad_dns_srv_found = dig_lookup_dns_srv(AD_FOREST,AD_DOMAIN)
    # Basic info from macOS:
    logging.info('Getting information from dsconfigad...')
    dsconfigad_computer_record = dsconfigad_get_computer_record(AD_FOREST,AD_DOMAIN)
    # Connectivity test should be false unless we determine the test is necessary:
    dscl_lookup_result = False
    
    # If on network, assume unbound unless we prove otherwise.
    if ad_dns_srv_found:
        logging.info('On network: DNS-SRV records found.')
        ad_status = "on-network-unbound"
    # If on network and macOS thinks it is bound, test for connectivity.
    if ad_dns_srv_found and dsconfigad_computer_record:
        logging.info('dsconfigad indicates system bound using %s' % dsconfigad_computer_record)
        dscl_lookup_result = dscl_lookup_computer_record(AD_FOREST,AD_DOMAIN,dsconfigad_computer_record)
        if dscl_lookup_result:
            ad_status = "on-network-communicating"

    # If unbound, clear out any data in Munki so that profiles
    # for binding may be reinstalled:
    if ad_status == "on-network-unbound":
        for profile_identifier in DEPENDENT_CONFIG_PROFILE_IDENTIFIERS:
            conditions_common.remove_profile(profile_identifier)

    # Write Conditions:
    conditions_common.write_conditions({"ad_dns_srv_found":ad_dns_srv_found,
                                       "computer_record":dsconfigad_computer_record,
                                       "dscl_lookup_result":dscl_lookup_result,
                                       "ad_status":ad_status,
                     })
    # Finish:
    sys.exit(0)

# Run main.
if __name__ == "__main__":
    main()
