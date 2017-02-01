Hardware Bundles Condition (_hw-bundle.py_)
----------
*Purpose:* Adds the following keys to the Munki Conditions file:
* **system_manufacture_date**: Date.  Approximate date of manufacture determined by decoding the serial number.
* **system_hw_bundle_oct_2013**: Boolean.  True iff it seems the system is eligible for current versions of iMovie, GarageBand, Pages, Numbers, and Keynote by virtue of having a hardware bundle license because *system_manufacture_date* indicates it shipped from Apple on or after October 23, 2013. 

*How it Works:*  This script reads the client's hardware serial number using *systemprofiler*, determining a date of manufacture using a method others have discovered and disclosed<sup>3</sup>.  If the date of manufacture is on or after October 23, 2013, then it considers the computer eligible for the current iLife/iWork hardware bundle.

Conditional Manifest Example
----------
Per the Munki documentation and online examples<sup>1,2</sup>, optional installs, mandatory installs, etc. can be offered conditionally.

You can use this **hw-bundle.py** Munki condition to conditionally offer Apple iMovie, GarageBand, Pages, Numbers, and Keynote if **system_hw_bundle_oct_2013** is true.  Here is an example block for placement in a group or upper-level included manifest:<pre>
	&lt;key>conditional_items&lt;/key>
	&lt;array&gt;
		&lt;dict&gt;
		&lt;key&gt;condition&lt;/key&gt;
		&lt;string&gt;system_hw_bundle_oct_2013 == TRUE&lt;/string&gt;
		&lt;key&gt;optional_installs&lt;/key&gt;
		&lt;array&gt;
                	&lt;string&gt;Apple_Pages&lt;/string&gt;
             		&lt;string&gt;Apple_Numbers&lt;/string&gt;
 		            &lt;string&gt;Apple_Keynote&lt;/string&gt;
        	        &lt;string&gt;Apple_iMovie&lt;/string&gt;
	                &lt;string&gt;Apple_GarageBand&lt;/string&gt;
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
3. http://www.macrumors.com/2010/04/16/apple-tweaks-serial-number-format-with-new-macbook-pro/
4. https://developer.apple.com/library/mac/documentation/Darwin/Reference/ManPages/man8/system_profiler.8.html
5. http://stackoverflow.com/questions/17087314/get-date-from-week-number
6. https://www.apple.com/pr/library/2013/10/23Apple-Introduces-Next-Generation-iWork-and-iLife-Apps-for-OS-X-and-iOS.html
