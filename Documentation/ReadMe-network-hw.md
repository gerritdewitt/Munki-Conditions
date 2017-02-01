Network Hardware Status Condition (_network-hw.py_)
----------
*Purpose:* Adds the following keys to the Munki Conditions file to report on network hardware:
* **ethernet_and_wifi_interfaces**: Array of dictionaries representing Wi-Fi and Ethernet interfaces having BSD identifiers and MAC addresses.  Each dictionary contains the following keys:
   - **hw_address**: String.  The MAC address for the interface.
   - **interface**: String.  The identifier like *en0* or *en1*.
   - **name**: String.  The name of the interface as shown in the Network Pane of System Preferences or blank (if no name can be found).
   - **type**: String.  “Ethernet” or “AirPort”.  Used to determine if the system has a Wi-Fi interface (of type AirPort).
* **has_wi_fi**: Boolean.  True iff the list of interfaces has one of type AirPort or Wi-Fi.

*How it Works:*  This script performs runs the command-line version of *system_profiler* and gets *SPNetworkDataType* information in XML format.  It parses that output, looking for Ethernet and Wi-Fi interface information.

Author
----------
Written by Gerrit DeWitt (gdewitt@gsu.edu)
Copyright Georgia State University

Sources
----------
1. Munki
   * https://github.com/munki/munki/wiki/Conditional-Items
   * https://github.com/munki/munki/wiki/Pkginfo-Files
   * https://github.com/munki/munki/wiki/Supported-Pkginfo-Keys
2. https://github.com/timsutton/munki-conditions
3. https://groups.google.com/forum/#!topic/django-users/0YtgYQnMKtM
4. https://developer.apple.com/legacy/library/documentation/Darwin/Reference/ManPages/man8/system_profiler.8.html
