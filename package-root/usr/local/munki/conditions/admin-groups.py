#!/usr/bin/env python

# admin-groups.py
# Manages nesting of directory-based groups in the local admin group
# as specified in manifest metadata. This includes adding and removing
# groups if the _metadata:nested_admin_groups array exists.
# Reports any nested admin groups as a condition.
# References: Refer to the markdown files in the source tree
# (ReadMe.md and those in the Documentation folder).

# Written by Gerrit DeWitt (gdewitt@gsu.edu)
# This file created 2015-08-25, 2015-09-02 (extensions), 2015-09-11 (initial installcheck scripts for bundle eligibility), 2015-11-10 (extensions), 2015-11-24 (extensions/conditions), 2016-02-16, 2016-02-26, 2016-03-01,02, 2016-06-15.
# Copyright Georgia State University.
# This script uses publicly-documented methods known to those skilled in the art.

# Location of munki manifests on the client:
global MUNKI_MANIFESTS_PATH
MUNKI_MANIFESTS_PATH = "/Library/Managed Installs/manifests"

# Directory node from which we reference groups to nest.
# Node path is what dscl reports.
global DIRECTORY_SEARCH_NODE
DIRECTORY_SEARCH_NODE = "/Active Directory/YOURDOMAIN/All Domains"

import sys, plistlib, xml, subprocess, os, logging
this_dir = os.path.dirname(os.path.realpath(__file__))
shared_support_dir = os.path.join(this_dir,'shared-support')
sys.path.append(shared_support_dir)
import conditions_common

def get_included_manifest_names_from_given_manifest(given_manifest_name):
    '''Reads the given manifest's included_manifests array.  Returns a list
        of included ones.'''
    # Defaults:
    given_manifest_dict = {}
    included_manifests_list = []
    # Try reading input manifest file to dict:
    given_manifest_path = os.path.join(MUNKI_MANIFESTS_PATH,given_manifest_name)
    if os.path.exists(given_manifest_path):
        try:
            given_manifest_dict = plistlib.readPlist(given_manifest_path)
        except xml.parsers.expat.ExpatError:
            pass
    # Try reading the included_manifests key from the given_manifest_dict:
    if given_manifest_dict:
        try:
            included_manifests_list = given_manifest_dict['included_manifests']
        except KeyError:
            pass
    # Return:
    return included_manifests_list

def make_list_of_applicable_manifests():
    '''Produces a flat list of manifests which are relevant to this computer.'''
    # Defaults:
    processed_manifest_names_list = []
    queued_manifest_names_list = ['client_manifest.plist']
    # Loop:
    while True:
        # Init:
        new_manifests_list = []
        for manifest_name in queued_manifest_names_list:
            new_manifests_list_from_this_manifest_name = get_included_manifest_names_from_given_manifest(manifest_name)
            # This new manifest list can contain duplicates (we filter them when adding to the queue in the next for loop).
            new_manifests_list.extend(new_manifests_list_from_this_manifest_name)
            # Mark as processed (but prevent duplicates):
            if manifest_name not in processed_manifest_names_list:
                processed_manifest_names_list.append(manifest_name)
        # Break if new manifests list is empty:
        if not new_manifests_list:
            break
        # Add any new ones to queue:
        for manifest_name in new_manifests_list:
            if manifest_name not in queued_manifest_names_list:
                queued_manifest_names_list.append(manifest_name)
        # Remove processed manifests from queue:
        for manifest_name in queued_manifest_names_list:
            if manifest_name in processed_manifest_names_list:
                queued_manifest_names_list.remove(manifest_name)

    # Return:
    return processed_manifest_names_list

def make_list_of_admin_groups(given_manifest_names_list):
    '''Given a list of manifest names, examine their metadata, looking for nested_admin_groups keys.
        Build a list of dictionaries from that information.'''
    # Defaults:
    admin_group_names_list = []
    admin_group_dicts_list = []
    exclude_admins_from_dsconfigad = False
    # Read each manifest's _metadata:print_nested_admin_groups key,
    # creating a list of unique group names.
    for manifest_name in given_manifest_names_list:
        # Determine the manifest path:
        manifest_path = os.path.join(MUNKI_MANIFESTS_PATH,manifest_name)
        # Defaults:
        manifest_dict = {}
        manifest_metadata_dict = {}
        manifest_admin_group_names_list = []
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
                    manifest_admin_group_names_list = manifest_metadata_dict['nested_admin_groups']
                except KeyError:
                    pass
                try:
                    # One true flips this parameter; cannot be flipped back with a false:
                    if manifest_metadata_dict['exclude_admins_from_dsconfigad']:
                        exclude_admins_from_dsconfigad = True
                except KeyError:
                    pass
        # Build up the list of admin group names:
        for group_name in manifest_admin_group_names_list:
            if group_name not in admin_group_names_list:
                admin_group_names_list.append(group_name)
    # Build list of dicts describing groups:
    for group_name in admin_group_names_list:
        the_group_dict = {}
        the_group_dict['name'] = group_name
        the_group_dict['guid'] = osx_dscl_get_guid(group_name)
        if the_group_dict['guid']:
            admin_group_dicts_list.append(the_group_dict)
    # Return the filtered list:
    return admin_group_dicts_list, exclude_admins_from_dsconfigad

def get_list_of_admin_groups_from_dsconfigad():
    '''Read dsconfigad/AD binding prefs to get a list of admin groups that were specified there.
        Build a list of dictionaries from that information.'''
    # Defaults:
    admin_group_names_list = []
    admin_group_dicts_list = []
    # Run dsconfigad and parse output.
    try:
        output = subprocess.check_output(['/usr/sbin/dsconfigad',
                                          '-show',
                                          '-xml'])
    except subprocess.CalledProcessError:
        print "Unable to obtain AD config from dsconfigad."
    if output:
        try:
            output_dict = plistlib.readPlistFromString(output)
        except xml.parsers.expat.ExpatError:
            pass
    if output_dict:
        try:
            admin_group_names_list = output_dict['Administrative']['Allowed admin groups']
        except KeyError:
            pass
    # Build list of dicts describing groups:
    for group_name in admin_group_names_list:
        the_group_dict = {}
        the_group_dict['name'] = group_name
        the_group_dict['guid'] = osx_dscl_get_guid(group_name)
        if the_group_dict['guid']:
            admin_group_dicts_list.append(the_group_dict)
    # Return the filtered list:
    return admin_group_dicts_list

def osx_dscl_get_guid(given_group_name):
    '''Calls dscl to get the GUID of the given named group.
        Searches in DIRECTORY_SEARCH_NODE.
        Returns None if anything bad happens.'''
    # Defaults:
    output = ''
    output_dict = {}
    guid_key_array = []
    guid = None
    # Run dscl and parse output - try to get the GeneratedUID attribute.
    try:
        output = subprocess.check_output(['/usr/bin/dscl',
                                          '-plist',
                                          DIRECTORY_SEARCH_NODE,
                                          'read',
                                          'Groups/%s' % given_group_name,
                                          'GeneratedUID'])
    except subprocess.CalledProcessError:
        print "Unable to read GeneratedUID for %s with dscl." % given_group_name
    if output:
        try:
            output_dict = plistlib.readPlistFromString(output)
        except xml.parsers.expat.ExpatError:
            pass
    if output_dict:
        try:
            guid_key_array = output_dict['dsAttrTypeStandard:GeneratedUID']
        except KeyError:
            pass
    if guid_key_array:
        try:
            guid = guid_key_array[0]
        except KeyError, NameError:
            pass
    # Return:
    return guid

def osx_dscl_list_nested_admin_groups():
    '''Returns an array of GUIDs from the NestedGroups attribute of the admin group.'''
    # Defaults:
    output = ''
    output_dict = {}
    nested_groups_array = []
    # Run dscl to get the NestedGroups key for the admin group:
    try:
        output = subprocess.check_output(['/usr/bin/dscl',
                                          '-plist',
                                          '/Local/Default',
                                          'read',
                                          'Groups/admin',
                                          'NestedGroups'])
    except subprocess.CalledProcessError:
        print "Unable to read NestedGroups for the admin group with dscl."
    if output:
        try:
            output_dict = plistlib.readPlistFromString(output)
        except xml.parsers.expat.ExpatError:
            pass
    if output_dict:
        try:
            nested_groups_array = output_dict['dsAttrTypeStandard:NestedGroups']
        except KeyError:
            pass
    # Return:
    return nested_groups_array

def osx_dseditgroup_add_group_to_admin_group(given_group_dict):
    '''Calls dseditgroup to nest the given group in the local admin group.'''
    # Try to nest:
    try:
        subprocess.check_call(['/usr/sbin/dseditgroup',
                               '-o',
                               'edit',
                               '-a',
                               given_group_dict['name'],
                               '-t',
                               'group',
                               'admin'])
        return True
    except subprocess.CalledProcessError:
        return False

def osx_dscl_remove_nested_admin_group(given_group_guid):
    '''Removes the given GUID from the NestedGroups attribute of the admin group.
        Returns true/false.'''
    try:
        subprocess.check_call(['/usr/bin/dscl',
                               '/Local/Default',
                               'delete',
                               'Groups/admin',
                               'NestedGroups',
                               given_group_guid])
        return True
    except subprocess.CalledProcessError:
        return False

def create_attr_difference_list(given_minuend_list_of_attrs,given_subtrahend_list_of_dicts,given_subtrahend_dict_key):
    '''Given a minuend array of attrs and a subtrahend array of dicts, for each dict
        in the subtrahend, if its attribute is in the minuend, remove it.
        Return any remaining elements of the minuend.'''
    for dict in given_subtrahend_list_of_dicts:
        try:
            given_minuend_list_of_attrs.remove(dict[given_subtrahend_dict_key])
        except ValueError:
            pass
    return given_minuend_list_of_attrs

def main():
    '''Main logic for this script'''
    # Results array: A list of true/false values we'll use to look for errors
    # Starts with one true so we don't have an empty list. We will compare against
    # an intersection of its elements, so adding a true does not throw off that logic.
    results_array = [True]
    overall_result = False
    # Get names of group manifests to which this computer is a member:
    group_manifest_names = make_list_of_applicable_manifests()
    # Construct list of admin groups that should be present:
    requested_admin_group_dicts_list, exclude_dsconfigad_admin_groups = make_list_of_admin_groups(group_manifest_names)
    # Enumerate existing nested groups:
    measured_admin_group_guids_list = osx_dscl_list_nested_admin_groups()

    # Manage admin groups iff we have a list:
    # When off network, we expect this list to be empty (because GUIDs could not be resolved).
    if requested_admin_group_dicts_list:
        # Add groups from dsconfigad to the requested list if appropriate:
        if not exclude_dsconfigad_admin_groups:
            dsconfigad_admin_group_dicts_list = get_list_of_admin_groups_from_dsconfigad()
            for group_dict in dsconfigad_admin_group_dicts_list:
                if group_dict not in requested_admin_group_dicts_list:
                    requested_admin_group_dicts_list.append(group_dict)
        # Add groups to the admin group:
        for group_dict in requested_admin_group_dicts_list:
            if group_dict['guid'] not in measured_admin_group_guids_list:
                results_array.append(osx_dseditgroup_add_group_to_admin_group(group_dict))
        # Measure nested admin groups again (after additions):
        measured_admin_group_guids_list = osx_dscl_list_nested_admin_groups()
        # Take desired away from measured:
        difference_list = create_attr_difference_list(measured_admin_group_guids_list,requested_admin_group_dicts_list,'guid')
        # If anything is left, remove it:
        if difference_list:
            for group_guid in difference_list:
                results_array.append(osx_dscl_remove_nested_admin_group(group_guid))

    # Assemble and write Conditions:
    if False not in results_array:
        overall_result = True
    conditions_common.write_conditions({"admin_groups_success":overall_result,"nested_admin_group_guids":osx_dscl_list_nested_admin_groups()})
    # Finish:
    sys.exit(0)

# Run main.
if __name__ == "__main__":
    main()
