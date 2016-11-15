#!/usr/bin/env python

# conditions_common.py
# Common methods for shared by all conditions.
# References: Refer to the markdown files in the source tree
# (ReadMe.md and those in the Documentation folder).

# Written by Gerrit DeWitt (gdewitt@gsu.edu)
# This file created 2015-08-25 (extensions), 2015-09-11 (initial installcheck scripts for bundle eligibility), 2015-11-10 (extensions), 2015-11-24 (extensions/conditions), 2016-02-16, 2016-06-15, 2016-06-28.
# Copyright Georgia State University.
# This script uses publicly-documented methods known to those skilled in the art.

# Location of Munki plists:
global MUNKI_CONDITIONS_PATH, MUNKI_CONFIG_PROFILE_DATA_PATH
MUNKI_CONDITIONS_PATH = "/Library/Managed Installs/ConditionalItems.plist"
MUNKI_CONFIG_PROFILE_DATA_PATH = "/Library/Managed Installs/ConfigProfileData.plist"

import plistlib, xml, os, logging

def clear_munki_config_profile_data(given_identifiers_array):
    '''Removes specified dictionaries by name from the Munki Config Profile Data file.'''
    # Defaults:
    identifiers_dict = {}
    # Try reading file:
    if os.path.exists(MUNKI_CONFIG_PROFILE_DATA_PATH):
        try:
            identifiers_dict = plistlib.readPlist(MUNKI_CONFIG_PROFILE_DATA_PATH)
        except xml.parsers.expat.ExpatError:
            pass
    if identifiers_dict:
       # Remove identifiers if present:
        for identifier in given_identifiers_array:
            try:
                del identifiers_dict[identifier]
                logging.info("Removed config profile identifier %s from Munki Config Profile Data file." % identifier)
            except KeyError:
                pass
        # Write plist:
        try:
            plistlib.writePlist(identifiers_dict,MUNKI_CONFIG_PROFILE_DATA_PATH)
        except TypeError:
            logging.error("Failed to write changes to the Munki Config Profile Data file: %s" % MUNKI_CONFIG_PROFILE_DATA_PATH)

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