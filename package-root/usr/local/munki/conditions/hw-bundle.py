#!/usr/bin/env python

# hw-bundle.py
# Script for populating Munki Conditions:
# Adds the approximate date of manufacture and a key indicating
# if the Mac has a hardware bundle license for iMovie, GarageBand,
# Pages, Numbers, and Keynote.
# References: Refer to the markdown files in the source tree
# (ReadMe.md and those in the Documentation folder).

# Written by Gerrit DeWitt (gdewitt@gsu.edu)
# This file created 2015-08-25 (extensions), 2015-09-11 (initial installcheck scripts for bundle eligibility), 2015-11-10 (extensions), 2015-11-24 (extensions/conditions), 2016-02-16, 2016-06-15.
# Copyright Georgia State University.
# This script uses publicly-documented methods known to those skilled in the art.

# Earlist date when this app was included in Apple Hardware Bundle:
global HW_BUNDLE_MIN_DATE_STR
HW_BUNDLE_MIN_DATE_STR = "2013-10-23"

import sys, plistlib, xml, subprocess, os, logging
from datetime import datetime
this_dir = os.path.dirname(os.path.realpath(__file__))
shared_support_dir = os.path.join(this_dir,'shared-support')
sys.path.append(shared_support_dir)
import conditions_common

def system_profiler_fetch_serial():
    '''Calls System Profiler to get the computer's hardware serial number.
        Returns None if something bad happened.'''
    # Defaults:
    output = None
    output_dict = {}
    serial_number= ''
    # Run command:
    try:
        output = subprocess.check_output(['/usr/sbin/system_profiler',
                                          'SPHardwareDataType',
                                          '-xml'])
    except subprocess.CalledProcessError:
        pass
    # Try to get serial_number key:
    if output:
        try:
            output_dict = plistlib.readPlistFromString(output)
        except xml.parsers.expat.ExpatError:
            pass
    if output_dict:
        try:
            serial_number = output_dict[0]['_items'][0]['serial_number']
        except KeyError:
            pass
        except IndexError:
            pass
    # Return:
    return serial_number

def manufacture_date_from_serial(given_serial):
    '''Given a serial, return the date of production for this Mac.
        Only works for the 12-digit serial format.
        Returns a date or None.'''
    # Constants:
    year_letters_array_1 = ["C","F","H","K","M","P","R","T","W","Y"]
    year_letters_array_2 = ["D","G","J","L","N","Q","S","V","X","Z"]
    week_codes_array = ["1","2","3","4","5","6","7","8","9","C",
                        "D","F","G","H","J","K","L","M","N","P",
                        "Q","R","T","V","W","X","Y"]
    # Defaults:
    year_base = 2010
    week_base = 0
    year_index = -1
    week_index = -1
    # Catch old Apple serials:
    if len(given_serial) != 12:
        return None
    else: # 2010 and later format:
        year_letter = given_serial[3]
        week_code = given_serial[4]
        # Get year index and adjust week base if required:
        try:
            year_index = year_letters_array_1.index(year_letter)
        except ValueError:
            pass
        try:
            year_index = year_letters_array_2.index(year_letter)
            week_base = 27
        except ValueError:
            pass
        # Get week index:
        try:
            week_index = week_codes_array.index(week_code)
        except ValueError:
            pass
        # Year:
        year = year_index + year_base
        # Week:
        week = week_index + week_base
        # Catch indices that could not be determined:
        if (year < year_base) or (week < week_base):
            return None
        # Make approximate manufacture date:
        birthday_str = "%(y)s-W%(w)s-0" % {"y":year,"w":week}
        birthday = datetime.strptime(birthday_str,"%Y-W%W-%w")
        return birthday

def main():
    '''Main logic for this script'''
    # Get hardware serial and manufacture date:
    system_serial = system_profiler_fetch_serial()
    system_manufacture_date = manufacture_date_from_serial(system_serial)
    # Get HW Bundle eligibility:
    system_hw_bundle_oct_2013 = False
    bundle_eligible_date = datetime.strptime(HW_BUNDLE_MIN_DATE_STR,"%Y-%m-%d")
    if system_manufacture_date >= bundle_eligible_date:
        system_hw_bundle_oct_2013 = True
    # Write Conditions:
    conditions_common.write_conditions({"system_manufacture_date":system_manufacture_date,"system_hw_bundle_oct_2013":system_hw_bundle_oct_2013})
    # Finish:
    sys.exit(0)

# Run main.
if __name__ == "__main__":
    main()
