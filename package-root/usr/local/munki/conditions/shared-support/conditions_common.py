#!/usr/bin/env python

# conditions_common.py
# Common methods for shared by all conditions.
# References: Refer to the markdown files in the source tree
# (ReadMe.md and those in the Documentation folder).

# Written by Gerrit DeWitt (gdewitt@gsu.edu)
# This file created 2015-08-25 (extensions), 2015-09-11 (initial installcheck scripts for bundle eligibility)
# 2015-11-10 (extensions), 2015-11-24 (extensions/conditions), 2016-02-16, 2016-06-15, 2016-06-28
# 2017-01-13, 2017-03-08.
# Copyright Georgia State University.
# This script uses publicly-documented methods known to those skilled in the art.

# Location of Munki plists:
global MUNKI_CONDITIONS_PATH
MUNKI_CONDITIONS_PATH = "/Library/Managed Installs/ConditionalItems.plist"

import plistlib, xml, subprocess, os, logging

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
