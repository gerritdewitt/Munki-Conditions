#!/usr/bin/env python

# ad-status.py
# Script for populating Munki Conditions that report on
# connectivity to Active Directory.  When used in conjunction
# with a conditional managed install for an AD directory service
# config profile, unbound systems may be bound automatically.
# References: Refer to the markdown files in the source tree
# (ReadMe.md and those in the Documentation folder).

# Written by Gerrit DeWitt (gdewitt@gsu.edu)
# This file created 2015-08-25 (extensions), 2015-09-11 (initial installcheck scripts for bundle eligibility), 2015-11-10 (extensions), 2015-11-24 (extensions/conditions), 2016-02-16, 2016-06-15, 2016-06-27.
# Copyright Georgia State University.
# This script uses publicly-documented methods known to those skilled in the art.

# Variables:
global AD_FOREST, AD_DOMAIN
# Edit to meet your needs:
# If domain is forest, these are the same.
AD_FOREST = "forest.org"
AD_DOMAIN = "domain.forest.org"

global AD_TEST_USER_NAME, AD_TEST_USER_EXPECTED_UID
# Edit to meet your needs:
AD_TEST_USER_NAME = "test-domain-user"
AD_TEST_USER_EXPECTED_UID = "1234567"
global DEPENDENT_CONFIG_PROFILE_IDENTIFIERS
# Edit to meet your needs:
DEPENDENT_CONFIG_PROFILE_IDENTIFIERS = ["org.sample.config.profile.active-directory","org.sample.config.profile.8021X"]

import sys, plistlib, xml, subprocess, os, logging, pwd, time
this_dir = os.path.dirname(os.path.realpath(__file__))
shared_support_dir = os.path.join(this_dir,'shared-support')
sys.path.append(shared_support_dir)
import conditions_common

def lookup_test_user(given_name,given_uid):
    '''Looks up the given user account.  Returns true iff the UID matches the given one.'''
    measured_uid = -1000
    try:
        measured_uid = pwd.getpwnam(given_name).pw_uid
    except KeyError:
        pass
    if int(measured_uid) == int(given_uid):
        return True
    else:
        return False

def dsconfigad_verify_forest_and_domain(given_forest,given_domain):
    '''Runs dsconfigad -show and inspects its output.
        Returns true iff the system seems bound to the domain.'''
    # Defaults:
    output = ''
    output_dict = {}
    measured_forest = ''
    measured_domain = ''
    # Call dsconfigad:
    try:
        output = subprocess.check_output(['/usr/sbin/dsconfigad',
                                          '-xml',
                                          '-show'])
    except subprocess.CalledProcessError:
        pass
    # Try to parse output:
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
    if measured_forest.lower() == given_forest.lower() and measured_domain.lower() == given_domain.lower():
        return True
    else:
        return False

def dig_lookup_dns_srv(given_forest,given_domain):
    '''Performs DNS-SRV queries to see if we have domain controllers available.
        Returns true if dig found a DNS-SRV record for the global catalog for our domain.
        Returns false otherwise.'''
    # Defaults:
    ad_gc_available = False
    this_try = 0
    max_tries = 5
    # Call dig:
    while True:
        output = ''
        output_array = []
        answer_section_index = -1
        try:
            output = subprocess.check_output(['/usr/bin/dig',
                                              '-t',
                                              'SRV',
                                              '_gc._tcp.%s' % given_forest])
        except subprocess.CalledProcessError:
            pass
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
            try:
                first_srv_record = output_array[answer_section_index +1]
                if first_srv_record.find(given_domain) != -1:
                    ad_gc_available = True
                    break
            except ValueError:
                pass
        # Break if we exceed max tries:
        if this_try >= max_tries:
            break
        # Increment:
        this_try += 1
        time.sleep(5)
    # Return:
    return ad_gc_available

def main():
    '''Main logic for this script'''
    # Default: Assume not on network and all bools False:
    ad_status = "not-on-network"
    ad_dns_srv_found = False
    ad_test_user_lookup = False
    ad_test_dsconfigad = False
    
    # Network test:
    ad_dns_srv_found = dig_lookup_dns_srv(AD_FOREST,AD_DOMAIN)
    
    # Perform AD tests and evaluate iff on network:
    if ad_dns_srv_found:
        ad_test_user_lookup = lookup_test_user(AD_TEST_USER_NAME,AD_TEST_USER_EXPECTED_UID)
        ad_test_dsconfigad = dsconfigad_verify_forest_and_domain(AD_FOREST,AD_DOMAIN)
        if ad_test_user_lookup and ad_test_dsconfigad:
            ad_status = "on-network-communicating"
        else:
            ad_status = "on-network-unbound"

    # If unbound, clear out any data in Munki so that profiles
    # for binding may be reinstalled:
    if ad_status == "on-network-unbound":
        conditions_common.clear_munki_config_profile_data(DEPENDENT_CONFIG_PROFILE_IDENTIFIERS)

    # Write Conditions:
    conditions_common.write_conditions({"ad_dns_srv_found":ad_dns_srv_found,
                     "ad_test_user_lookup":ad_test_user_lookup,
                     "ad_test_dsconfigad":ad_test_dsconfigad,
                     "ad_status":ad_status,
                     })
    # Finish:
    sys.exit(0)

# Run main.
if __name__ == "__main__":
    main()
