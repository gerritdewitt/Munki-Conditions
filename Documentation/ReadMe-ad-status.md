Active Directory Status Condition (_ad-status.py_)
----------
*Purpose:* Adds the following keys to the Munki Conditions file to report on connectivity to Active Directory (AD):
* **ad_dns_srv_found**: Boolean.  True iff AD DNS records for the forest or domain you specified were found.
* **computer_record**: String.  Name of the computer record as returned by *dsconfigad*; otherwise, blank.
* **dscl_lookup_result**: Boolean.  True iff *dscl* can communicate with AD to read the computer record and its attributes **and** the *AppleMetaNodeLocation* indicates the domain or forest you specified.
* **ad_status**: String with fixed values:
   * **not-on-network**: Indicates that the system is *not* on the network because DNS-SRV records weren't found (*ad_dns_srv_found* was False, *computer_record* may or may not provide a computer name, and *dscl_lookup_result* is False because there was no need to test communication off-network).
   * **on-network-communicating**: Indicates that the system is on the network, is bound to AD, and is communicating with it (*ad_dns_srv_found* was True, *computer_record* provides a computer name, and *dscl_lookup_result* is True).
   * **on-network-unbound**: Indicates that the system is on the network, but AD communication tests failed (*ad_dns_srv_found* was True, *computer_record* may or may not provide a computer name, but *dscl_lookup_result* is False).

*How it Works:*  This script performs a series of tests to determine if the computer on which it runs should be bound to AD.  Lookup of DNS-SRV records is accomplished with *dig*, *dsconfigad* is called to read AD binding defaults, and communications testing is done with *dscl*.

Relationship with AD Config Profile
----------
Per the Munki documentation and online examples<sup>1,2</sup>, optional installs, mandatory installs, etc. can be offered conditionally.

You can use this **ad-status.py** Munki condition with a configuration profile to bind Mac systems to Active Directory.  If the **ad_status** is **on-network-unbound**, then a configuration profile for binding to AD may be offered as a managed install.  Here is an example block for placement in a group or upper-level included manifest:<pre>
	&lt;key>conditional_items&lt;/key>
	&lt;array&gt;
		&lt;dict&gt;
		&lt;key&gt;condition&lt;/key&gt;
		&lt;string&gt;ad_status == "on-network-unbound"&lt;/string&gt;
		&lt;key&gt;managed_installs&lt;/key&gt;
		&lt;array&gt;
                	&lt;string&gt;Configuration_Active_Directory.mobileconfig&lt;/string&gt;
		&lt;/array&gt;
		&lt;/dict&gt;
        &lt;/array&gt;
</pre>

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
3. https://derflounder.wordpress.com/2012/03/29/diagnosing-ad-binding-problems-from-the-command-line/
4. https://support.apple.com/en-us/HT201885
5. https://docs.python.org/2/tutorial/datastructures.html
6. https://developer.apple.com/legacy/library/documentation/Darwin/Reference/ManPages/man1/dig.1.html
7. https://developer.apple.com/library/mac/documentation/Darwin/Reference/ManPages/man8/dsconfigad.8.html
8. https://developer.apple.com/legacy/library/documentation/Darwin/Reference/ManPages/man1/dscl.1.html
