#!/usr/bin/env python

# print-queues.py
# Adds print queues specified in manifest metadata.
# Stores the array of queue dictionaries as a condition.
# References: Refer to the markdown files in the source tree
# (ReadMe.md and those in the Documentation folder).

# Written by Gerrit DeWitt (gdewitt@gsu.edu)
# This file created 2015-08-25, 2015-09-02 (extensions)
# 2015-09-11 (initial installcheck scripts for bundle eligibility), 2015-11-10 (extensions)
# 2015-11-24 (extensions/conditions), 2016-02-16, 2016-02-26, 2016-03-01,02, 2016-06-15
# 2017-07-23.
# Copyright Georgia State University.
# This script uses publicly-documented methods known to those skilled in the art.

# Location of munki manifests on the client:
global MUNKI_MANIFESTS_PATH
MUNKI_MANIFESTS_PATH = "/Library/Managed Installs/manifests"

import sys, plistlib, xml, subprocess, os, logging
from datetime import datetime
this_dir = os.path.dirname(os.path.realpath(__file__))
shared_support_dir = os.path.join(this_dir,'shared-support')
sys.path.append(shared_support_dir)
import conditions_common

def make_list_of_print_queues(given_manifest_names_list):
    '''Given a list of manifest names, examine their metadata, looking for print_queues keys.
        Build a list of print queue dictionaries from that information.'''
    # Defaults:
    print_queue_dicts_list = []
    filtered_print_queue_dicts_list = []
    # Read each manifest's _metadata:print_queues key, adding print queue
    # dicts to the overall print queue array of dicts if not there already.
    for manifest_name in given_manifest_names_list:
        # Determine the manifest path:
        manifest_path = os.path.join(MUNKI_MANIFESTS_PATH,manifest_name)
        # Defaults:
        manifest_dict = {}
        manifest_metadata_dict = {}
        manifest_print_queue_dicts_list = []
        if os.path.exists(manifest_path):
            try:
                manifest_dict = plistlib.readPlist(manifest_path)
            except xml.parsers.expat.ExpatError:
                pass
            if manifest_dict:
                try:
                    manifest_metadata_dict = manifest_dict['_metadata']
                except KeyError:
                    pass
            if manifest_metadata_dict:
                try:
                    manifest_print_queue_dicts_list = manifest_metadata_dict['print_queues']
                except KeyError:
                    pass
        # Build up the list of print queues:
        for print_queue_dict in manifest_print_queue_dicts_list:
            if print_queue_dict not in print_queue_dicts_list:
                print_queue_dicts_list.append(print_queue_dict)
    # Filter print queue list:
    for print_queue_dict in print_queue_dicts_list:
        # Defaults: assume false.
        queue_has_required_attributes = False
        queue_ppd_installed = False
        # Verify required attributes for the print queue:
        try:
            test = print_queue_dict['name']
            test = print_queue_dict['ppd_path']
            test = print_queue_dict['device_uri']
            queue_has_required_attributes = True
        except KeyError:
            pass
        # Verify presence of the PPD:
        if queue_has_required_attributes:
            queue_ppd_installed = os.path.exists(print_queue_dict['ppd_path'])
        # Filter:
        if queue_has_required_attributes and queue_ppd_installed:
            filtered_print_queue_dicts_list.append(print_queue_dict)
    # Return the filtered list:
    return filtered_print_queue_dicts_list

def osx_lpoptions_print_queue_present(given_print_queue_dict):
    '''Calls lpoptions determine if the given print queue is present
        as determined by the presence of a queue with the correct device URI.
        Returns true if so, false otherwise.'''
    # Defaults:
    output = ''
    output_array = []
    measured_device_uri = ''
    queue_present = False
    # Run lpoptions to attributes:
    try:
        output = subprocess.check_output(['/usr/bin/lpoptions',
                                          '-d',
                                          given_print_queue_dict['name']])
    except subprocess.CalledProcessError:
        print "Unable to get attributes for queue %s with lpoptions." % given_print_queue_dict['name']
    output_array = output.split(' ')
    # Look for matching printer URI:
    for attribute in output_array:
        if attribute.find('device-uri') != -1:
            try:
                measured_device_uri = attribute.split('=')[1]
                break
            except IndexError:
                pass
    # Consider the print queue present if the URIs match.
    if measured_device_uri:
        if measured_device_uri.lower() == given_print_queue_dict['device_uri'].lower():
            queue_present = True
    # Return:
    return queue_present

def osx_lpadmin_add_printer(given_print_queue_dict,set_attrs_only):
    '''Calls lpadmin to add the given print queue or just set its attributes.
        Returns true/false.'''
    # Defaults:
    lpadmin_success = False
    kerberos_auth_required = False # auth-info-required not specified
    additional_cups_opts = [] # empty array of other options
    lpadmin_cups_options_array = ['-o','printer-is-shared=False'] # do not share the queue
    print_queue_display_name = given_print_queue_dict['name']
    # Is there a custom display name for the queue?
    try:
        print_queue_display_name = given_print_queue_dict['display_name']
    except KeyError:
        pass
    # Does the queue use Kerberos authentication?
    # Add the CUPS option for Kerberos if necessary.
    try:
        kerberos_auth_required = given_print_queue_dict['kerberos_auth_required']
    except KeyError:
        pass
    if kerberos_auth_required:
        lpadmin_cups_options_array.extend(['-o','auth-info-required=negotiate'])
    # Add other CUPS options specified in the additional_cups_opts array:
    try:
        additional_cups_opts = given_print_queue_dict['additional_cups_opts']
    except KeyError:
        pass
    for cups_opt in additional_cups_opts:
        lpadmin_cups_options_array.extend(['-o',cups_opt])
    # Base args:
    lpadmin_cmd = ['/usr/sbin/lpadmin',
                   '-p',
                   given_print_queue_dict['name'],
                   '-D',
                   print_queue_display_name,
                   '-E',
                   '-P',
                   given_print_queue_dict['ppd_path']]
    # Add other args:
    if not set_attrs_only:
        lpadmin_cmd.extend(['-v',given_print_queue_dict['device_uri']])
    lpadmin_cmd.extend(lpadmin_cups_options_array)
    try:
        subprocess.check_call(lpadmin_cmd)
        lpadmin_success = True
    except subprocess.CalledProcessError:
        pass
    # Return:
    return lpadmin_success

def main():
    '''Main logic for this script'''
    # Get names of group manifests to which this computer is a member:
    group_manifest_names = conditions_common.make_list_of_applicable_manifests()
    # Construct list of print queues that should be present:
    print_queues_array = make_list_of_print_queues(group_manifest_names)
    # Add the print queues if necessary:
    for print_queue_dict in print_queues_array:
        if not osx_lpoptions_print_queue_present(print_queue_dict):
            queue_added = osx_lpadmin_add_printer(print_queue_dict,False)
            print_queue_dict['queue_added'] = queue_added
            print_queue_dict['queue_added_timestamp'] = datetime.utcnow()
        else: # just set attributes:
            queue_attributes_set = osx_lpadmin_add_printer(print_queue_dict,True)
            print_queue_dict['queue_attributes_set'] = queue_attributes_set
            print_queue_dict['queue_attributes_set_timestamp'] = datetime.utcnow()

    # Write Conditions:
    conditions_common.write_conditions({"managed_print_queues":print_queues_array})
    # Finish:
    sys.exit(0)

# Run main.
if __name__ == "__main__":
    main()
