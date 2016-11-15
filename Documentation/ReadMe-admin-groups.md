Admin Groups Condition (_admin-groups.py_)
----------
*Purpose:* This condition script serves two purposes:
   1. It reports a list of GUIDs for groups nested in the local admin group.
   2. It reads metadata from Munki manifest files (cached as of the previous Munki check-in), looking for a list of group names from a central directory domain that should be nested in the local admin group.  If a __metadata:nested_admin_groups_ key with valid information exists in one or more Munki manifests applicable to the computer:
      * Groups specified via the manifest(s) are added to the local admin group (if not already members), and
      * Groups specified in AD binding (dsconfigad) settings are added to the local admin group** (if not already members), and
      * Any other nested groups in the local admin group not in either list are removed.
      
** This setting is configurable.  See Expected Input Data for details.
 
 After it finishes, it writes the following to the conditions file:
* _admin_groups_success_: Boolean. If _false_, indicates the conditional script encountered a problem.
* _nested_admin_group_guids_: Array of GUID strings.  This information is measured using _dscl_; e.g.:
<pre>dscl /Local/Default read Groups/admin NestedGroups</pre>

*Available For:* Any group including the _includes/conditions_ manifest.

Expected Input Data
----------
A list of names for directory-based user groups may be defined in a relevant manifest's __metadata_ dictionary:
* *nested_admin_groups*:  an array of strings, where each string is the name of a directory-based group to nest.
* *exclude_admins_from_dsconfigad*:  optional boolean; if present, admin groups specified in AD binding preferences are not considered to be desired members of the local admin group.
   * This key may be specified in any manifest applicable to the computer; however, if specified in _at least one manifest_, at any level, this setting takes effect.  This allows granular control of the setting down to the computer level.

Additional Notes
----------
* The client system must be bound to and communicating with the directory domain that contains the user groups. No communication or not being bound prevents the script from looking up the group GUIDs.
* The directory-based group must exist when this condition script runs. If a group doesn't exist, it is ignored.  If it is added later and can be found by searching, then it will be added later.

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
3. https://developer.apple.com/library/mac/documentation/Darwin/Reference/ManPages/man8/dseditgroup.8.html
4. https://developer.apple.com/library/mac/documentation/Darwin/Reference/ManPages/man1/dscl.1.html
5. https://github.com/munki/munki/wiki/Managing-Printers-With-Munki