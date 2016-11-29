Active Directory Status Condition (_ad-status.py_)
----------
*Purpose:* Adds the following keys to the Munki Conditions file to report on connectivity to Active Directory (AD):
* _ad_dns_srv_found_: Boolean.  True iff AD DNS records for our domain were found.
* _ad_test_user_lookup_: Boolean.  True iff looking up a test user and verifying its UID worked.
* _ad_test_dsconfigad_: Boolean.  True iff _dsconfigad_ indicates we are bound to the domain with our preferences.
* _ad_status_: String with fixed values:
   * _not-on-network_: Indicates that the system is *not* on the network because DNS-SRV records weren't found (_ad_dns_srv_found_, _ad_test_user_lookup_, and _ad_test_dsconfigad_ are all False).
   * _on-network-communicating_: Indicates that the system is on the network and both AD tests passed (_ad_dns_srv_found_, _ad_test_user_lookup_, and _ad_test_dsconfigad_ are all True).
   * _on-network-unbound_: Indicates that the system is on the network, but at least one of the AD tests failed  (_ad_dns_srv_found_ is True, but one or both of _ad_test_user_lookup_ and _ad_test_dsconfigad_ are False).

It should be obvious that _ad_dns_srv_found_ is a necessary condition.  If DNS-SRV records are not found, we assume the system is off network and we skip other AD tests.

*How it Works:*  This script performs a series of tests to determine if the computer on which it runs should be bound to AD.  Lookup of DNS-SRV records is accomplished with _dig_, test user ID lookup is performed using the _pwd_ Python module, and _dsconfigad_ is called to read AD binding defaults.

Relationship with AD Config Profile
----------
Per the munki documentation and online examples<sup>1,2</sup>, optional installs, mandatory installs, etc. can be offered conditionally.  If the _ad_status_ is _on-network-unbound_, then the configuration profile for binding to AD is offered as a managed install:<pre>
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
7. https://developer.apple.com/library/mac/documentation/Darwin/Reference/ManPages/man1/id.1.html
8. https://docs.python.org/2/library/pwd.html
9. https://developer.apple.com/library/mac/documentation/Darwin/Reference/ManPages/man8/dsconfigad.8.html
