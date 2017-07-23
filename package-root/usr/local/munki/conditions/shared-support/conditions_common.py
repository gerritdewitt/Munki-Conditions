#!/usr/bin/env python

# conditions_common.py
# Common methods for shared by all conditions.
# References: Refer to the markdown files in the source tree
# (ReadMe.md and those in the Documentation folder).

# Written by Gerrit DeWitt (gdewitt@gsu.edu)
# This file created 2015-08-25 (extensions), 2015-09-11 (initial installcheck scripts for bundle eligibility)
# 2015-11-10 (extensions), 2015-11-24 (extensions/conditions), 2016-02-16, 2016-06-15, 2016-06-28
# 2017-01-13, 2017-03-08, 2017-07-23.
# Copyright Georgia State University.
# This script uses publicly-documented methods known to those skilled in the art.

# Location of Munki plists:
global MUNKI_CONDITIONS_PATH
MUNKI_CONDITIONS_PATH = "/Library/Managed Installs/ConditionalItems.plist"
# Location of munki manifests on the client:
global MUNKI_MANIFESTS_PATH
MUNKI_MANIFESTS_PATH = "/Library/Managed Installs/manifests"
# Munki ManagedInstalls.plist search paths:
global MUNKI_PREFS_PATHS, TEMP_PREF_PATH
TEMP_PREF_PATH = "/Library/Managed Installs/munki_ManagedInstalls_temp.plist"
MUNKI_PREFS_PATHS = []
MUNKI_PREFS_PATHS.append("/Library/Managed Preferences/ManagedInstalls.plist") # MCX or config profile
MUNKI_PREFS_PATHS.append("/private/var/root/Library/Preferences/ManagedInstalls.plist") # root user domain
MUNKI_PREFS_PATHS.append("/Library/Preferences/ManagedInstalls.plist") # local system domain

import plistlib, xml, subprocess, os, shutil, logging

def plutil_convert_to_xml(given_path):
    '''Converts a binary plist to an XML plist
    suitable for pllistlib to use.'''
    # Call plutil:
    try:
        subprocess.check_call(['/usr/bin/plutil',
                               '-convert',
                               'xml1',
                               given_path])
        return True
    except subprocess.CalledProcessError:
        return False

def remove_profile(given_profile_identifier):
    '''Removes specified Apple Config Profiles.'''
    # Call profiles:
    try:
        subprocess.check_call(['/usr/bin/profiles',
                               '-R',
                               '-p',
                               given_profile_identifier])
        return True
    except subprocess.CalledProcessError:
        return False

def write_conditions(given_dict):
    '''Writes key-value pairs to the Munki Conditions file.'''
    # Defaults:
    conditions_dict = {}
    # Try reading file to dict:
    if os.path.exists(MUNKI_CONDITIONS_PATH):
        try:
            conditions_dict = plistlib.readPlist(MUNKI_CONDITIONS_PATH)
        except xml.parsers.expat.ExpatError:
            pass
    # Update:
    try:
        conditions_dict.update(given_dict)
    except TypeError:
        pass
    # Write plist:
    if conditions_dict:
        try:
            plistlib.writePlist(conditions_dict,MUNKI_CONDITIONS_PATH)
        except TypeError:
            logging.error("Failed to write Munki Conditions: %s" % str(given_dict))
        except IOError:
            logging.error("Failed to write Munki Conditions: %s" % str(given_dict))

def get_included_manifest_names_from_manifest(given_manifest_name):
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
    queued_manifest_names_list = [determine_computer_manifest_name()]
    # Loop:
    while True:
        # Init:
        new_manifests_list = []
        for manifest_name in queued_manifest_names_list:
            new_manifests_list_from_this_manifest_name = get_included_manifest_names_from_manifest(manifest_name)
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
    
def determine_computer_manifest_name():
    '''Method determines the computer manifest name or sub-path
    relative to MUNKI_MANIFESTS_PATH.'''
    if not os.path.exists(MUNKI_MANIFESTS_PATH):
        return ''
    # First choice: Read the client identifier:
    client_identifier = get_client_identifier_key_from_munki_prefs()
    if client_identifier:
        return client_identifier
    # Second choice - look for
    # a file in MUNKI_MANIFESTS_PATH (other than Self Service manifest).
    # Munki 2.8.x used client_manifest.plist.
    manifests_path_children = os.listdir(MUNKI_MANIFESTS_PATH)
    manifests_path_top_files = [ item for item in manifests_path_children if not os.path.isdir(item) ] # exclude subdirs
    manifests_path_top_files = [ item for item in manifests_path_top_files if item.lower() != "selfservemanifest" ] # exclude Self Service manifest
    if len(manifests_path_top_files) == 1:
        return manifests_path_top_files[0] # one item
    # Otherwise return blank (future improvement for other setups):
        return ''
    
def get_client_identifier_key_from_munki_prefs():
    '''Reads the various ManagedInstalls.plist files in search order, returning
    ClientIdentifier, if present, from the highest priority one.'''
    client_identifier = ''
    for pref_path in MUNKI_PREFS_PATHS:
        prefs_dict = {}
        if not os.path.exists(pref_path):
            continue
        # If the pref file is present,
        # make a copy and convert to text.
        try:
            shutil.copy(pref_path,TEMP_PREF_PATH)
            plutil_convert_to_xml(TEMP_PREF_PATH)
        except shutil.Error:
            continue
        try:
            prefs_dict = plistlib.readPlist(TEMP_PREF_PATH)
        except xml.parsers.expat.ExpatError:
            pass
        if prefs_dict:
            try:
                client_identifier = prefs_dict['ClientIdentifier']
            except KeyError:
                pass
        if client_identifier:
            break
    if os.path.exists(TEMP_PREF_PATH):
        try:
            os.unlink(TEMP_PREF_PATH)
        except IOError:
            pass
    return client_identifier
