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
# 2017-01-13, 2017-02-20, 2017-03-08,10.
# Copyright Georgia State University.
# This script uses publicly-documented methods known to those skilled in the art.

# Variables:
global AD_FOREST, AD_DOMAIN
AD_FOREST = "example.org"
AD_DOMAIN = "domain.example.org"
global AD_TESTS_MAX_TRIES
AD_TESTS_MAX_TRIES = int(2)
global AD_MAX_CONSECUTIVE_FAILURES
AD_MAX_CONSECUTIVE_FAILURES = int(2)

global DEPENDENT_CONFIG_PROFILE_IDENTIFIERS
DEPENDENT_CONFIG_PROFILE_IDENTIFIERS = ["org.sample.config.profile.active-directory","org.sample.config.profile.8021X"]
global NTP_SERVER
NTP_SERVER = "ntp.example.org"

global AD_FAILURES_HISTORY_FILE_PATH
AD_FAILURES_HISTORY_FILE_PATH = "/Library/Managed Installs/ActiveDirectoryFailures.plist"


import sys, plistlib, xml, subprocess, os, logging, time, datetime
this_dir = os.path.dirname(os.path.realpath(__file__))
shared_support_dir = os.path.join(this_dir,'shared-support')
sys.path.append(shared_support_dir)
import conditions_common

def macos_ntpdate(given_ntp_server):
    '''Calls ntpdate and attempts to update the system clock.
        Returns true if successful, false otherwise.'''
    try:
        subprocess.check_call(['/usr/sbin/ntpdate',
                                          '-u',
                                          given_ntp_server])
        return True
    except subprocess.CalledProcessError:
        return False

def remove_sys_keychain_override():
    '''Attempts to remove the DefaultKeychain key from
        /Library/Preferences/com.apple.security.plist.
        Using defaults here since the plist may be a binplist.'''
    plist_path = "/Library/Preferences/com.apple.security.plist"
    try:
        subprocess.check_call(['/usr/bin/defaults',
                               'delete',
                               plist_path,
                               'DefaultKeychain'])
        return True
    except subprocess.CalledProcessError:
        return False

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
    t = 0
    while t < 5:
        t += 1
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
    t = 0
    while (not ad_gc_available) and (t < 5):
        t += 1
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
        # Sleep:
        time.sleep(5)
    # Return:
    return ad_gc_available

def increment_dscl_failure_count():
    '''Sets or increments a counter and timestamp to track
        Active Directory communications errors.
        Returns a failure count (of at least 1).'''
    # Defaults:
    dscl_failures_dict = {"failure_count":0,
                        "failure_timestamps":[]}
    read_dscl_failures_dict = {}
    # Try to read existing failure data:
    if os.path.exists(AD_FAILURES_HISTORY_FILE_PATH):
        try:
            read_dscl_failures_dict = plistlib.readPlist(AD_FAILURES_HISTORY_FILE_PATH)
        except xml.parsers.expat.ExpatError:
            pass
    dscl_failures_dict.update(read_dscl_failures_dict)
    # Note this failure:
    dscl_failures_dict['failure_count'] += 1
    dscl_failures_dict['failure_timestamps'].append(datetime.datetime.utcnow())
    # Write failure data:
    try:
        plistlib.writePlist(dscl_failures_dict,AD_FAILURES_HISTORY_FILE_PATH)
    except TypeError:
        logging.error("Failed to write AD failure history to: %s" % AD_FAILURES_HISTORY_FILE_PATH)
    except IOError:
        logging.error("Failed to write AD failure history to: %s" % AD_FAILURES_HISTORY_FILE_PATH)
    # Return failure count:
    return dscl_failures_dict['failure_count']

def remove_dscl_failure_data():
    '''Removes the file tracking AD connectivity failures.'''
    # Try to read existing failure data:
    if os.path.exists(AD_FAILURES_HISTORY_FILE_PATH):
        try:
            os.unlink(AD_FAILURES_HISTORY_FILE_PATH)
        except IOError:
            logging.error("Failed to remove AD failure history: %s" % AD_FAILURES_HISTORY_FILE_PATH)

def main():
    '''Main logic for this script'''
    # Assume not on network unless we prove otherwise.
    ad_status = "not-on-network"
    # Assume failure count is zero unless we prove otherwise.
    dscl_failure_count = 0
    # Assume dscl lookup is false unless network and dsconfigad tests pass:
    ad_dscl_tests_pass = False

    # Network test:
    logging.info('Looking for DNS-SRV records...')
    on_network = dig_lookup_dns_srv(AD_FOREST,AD_DOMAIN)
    # Basic info from macOS:
    logging.info('Getting information from dsconfigad...')
    dsconfigad_computer_record = dsconfigad_get_computer_record(AD_FOREST,AD_DOMAIN)
    
    # On-network tests loop:
    # Condition necessity and sufficiency Venn Diagram:
    # ( not dsconfigad_computer_record          )( dsconfigad_computer_record )
    # ( not ad_dscl_tests_pass                          )( ad_dscl_tests_pass )
    t = 0
    while on_network and (t < AD_TESTS_MAX_TRIES) and (ad_status != "on-network-communicating"):
        # Counter:
        t += 1
        logging.info('On network: DNS-SRV records found.  Performing other tests...')
        # First: If on network and macOS thinks it is bound, test for connectivity using dscl:
        if dsconfigad_computer_record:
            logging.info('dsconfigad indicates system bound using %s' % dsconfigad_computer_record)
            logging.info('Testing connectivity using dscl...')
            ad_dscl_tests_pass = dscl_lookup_computer_record(AD_FOREST,AD_DOMAIN,dsconfigad_computer_record)
            if ad_dscl_tests_pass:
                ad_status = "on-network-communicating"
                logging.info('The dscl tests passed.')
                # If bound, remove failure count information (if present):
                remove_dscl_failure_data()

        # If on network but dscl tests fail:
        if not ad_dscl_tests_pass: # dsconfigad could go either way
            ad_status = "on-network-unbound"
            logging.error('The dscl tests failed or dsconfigad indicates unbound!')

        # Special subset of dscl tests failing; system thinks it's bound, so
        # try a couple of things that might correct a transitory communications error.
        if not ad_dscl_tests_pass and dsconfigad_computer_record:
            # 1 - Update system clock.
            logging.error('Attempting to update system clock...')
            if not macos_ntpdate(NTP_SERVER):
                logging.error('...NTP update against %s failed!' % NTP_SERVER)
            else:
                logging.error('...NTP update complete.')
            time.sleep(5)
            # 2 - Remove DefaultKeychain key from com.apple.security.plist.
            logging.error('Removing DefaultKeychain key from com.apple.security.plist if necessary...')
            # This can fix a situation where macOS tries sourcing the computer (trust)
            # account password from a keychain other than the System.keychain.
            if not remove_sys_keychain_override():
                logging.error('...removing DefaultKeychain key failed (perhaps not present).')
            else:
                logging.error('...removed DefaultKeychain key.')
            time.sleep(5)
            
    # If unbound, increment the failure count:
    if ad_status == "on-network-unbound":
        dscl_failure_count = increment_dscl_failure_count()

    # If unbound, and we are past our failure count:
    # Clear out any data in Munki so that profiles
    # for binding may be reinstalled:
    if (ad_status == "on-network-unbound") and (dscl_failure_count >= AD_MAX_CONSECUTIVE_FAILURES):
        for profile_identifier in DEPENDENT_CONFIG_PROFILE_IDENTIFIERS:
            conditions_common.remove_profile(profile_identifier)

    # Write Conditions:
    conditions_common.write_conditions({"ad_on_network":on_network,
                                       "ad_computer_record":dsconfigad_computer_record,
                                       "ad_dscl_tests_pass":ad_dscl_tests_pass,
                                       "ad_status":ad_status,
                     })
    # Finish:
    sys.exit(0)

# Run main.
if __name__ == "__main__":
    main()
