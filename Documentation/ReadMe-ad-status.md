Active Directory Status Condition (_ad-status.py_)
----------
*Purpose:* Adds the following keys to the Munki Conditions file to report on connectivity to Active Directory (AD):
* **ad_on_network**: Boolean.  True iff AD DNS records for the forest or domain you specified were found.  When true, it should be interpreted as the computer being on the network so AD connectivity tests should be run.
* **ad_computer_record**: String.  Name of the computer record as returned by *dsconfigad*; otherwise, blank.
* **ad_dscl_tests_pass**: Boolean.  False by default.  True iff *dscl* can communicate with AD to read the computer record and its attributes **and** the *AppleMetaNodeLocation* indicates the domain or forest you specified.  This test is only run if the computer is on the network and *dsconfigad* produced a computer record name.
* **ad_status**: String with fixed values:
   * **not-on-network**: Indicates that the system is *not* on the network because DNS-SRV records weren't found (*ad_on_network* is False, *ad_computer_record* may or may not provide a computer name, and *ad_dscl_tests_pass* is False because there is no need to test communication off-network).
   * **on-network-communicating**: Indicates that the system is on the network, is bound to AD, and is communicating with it (*ad_on_network* is True, *ad_computer_record* provides a computer name, and *ad_dscl_tests_pass* is True).
   * **on-network-unbound**: Indicates that the system is on the network, but AD communication tests failed (*ad_on_network* is True, *ad_computer_record* may or may not provide a computer name, but *ad_dscl_tests_pass* is False).

## How it Works ##

This script performs a series of tests to determine the state of the computer's relationship with AD.  Lookup of DNS-SRV records is accomplished with *dig*, *dsconfigad* is called to read AD binding defaults, and communications testing is done with *dscl*.

In testing for AD connectivity, the main logic employs a while loop.  The script will repeat AD tests a configurable number of times (**AD_TESTS_MAX_TRIES**) while **on_network** is True and **ad_status** is **not** *on-network-communicating*.  During this loop, if dscl indicates the system is bound, the script switches **ad_status** to *on-network-communicating*, the AD failures history file is removed (if possible), and we exit the loop.  Otherwise:
   - As long as the while loop is active, if the **ad_dscl_tests_pass** is False: The script will attempt to set the system clock (ntpdate against **NTP_SERVER**), and it will attempt to remove the *DefaultKeychain* key from */Library/Preferences/com.apple.security.plist*.  This latter “fix” handles cases where some process may have instructed macOS to consider a keychain other than */Library/Keychains/System.keychain* as the System keychain.  Such a redirection would prevent macOS from being able to look up the computer (trust) account details it needs to communicate with AD.  During this phase, we set **ad_status** to *on-network-unbound* in case the loop breaks.
   - After the loop exits, if **ad_status** is still *on-network-unbound*, we update an AD failures count history file.
   - If **ad_status** is *on-network-unbound* and the failures count exceeds the configurable threshold (**AD_MAX_CONSECUTIVE_FAILURES**), the condition script removes the configuration profile used to bind the system to AD.  It may also remove dependent profiles, such as ones with an ADCertificate payload.  The profiles to remove in this case are specified as a list of their identifiers in **DEPENDENT_CONFIG_PROFILE_IDENTIFIERS**.

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
