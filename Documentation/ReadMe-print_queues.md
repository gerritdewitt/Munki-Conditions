Print Queues Condition (_print-queues.py_)
----------
*Purpose:* This condition script reads metadata from Munki manifest files (cached as of the previous Munki check-in), looking for custom dictionaries describing print queues added to the *_metadata* key in each.  It adds the defined print queues if necessary; otherwise, it simply maintains their CUPS attributes.  After it finishes, it writes a single array of dictionaries to the conditions file:
* _managed_print_queues_: Array of Dictionaries.  This is a union of any unique dictionaries found in the *_metadata:print_queues* array in each cached manifest.  It also includes result and timestamp keys indicating if adding/modifying the queues was successful and when the event happened.

*Requirements:*
In addition to the Munki Conditions being deployed...
 * At least one print queue defined in the metadata of at least one manifest.
 * The computer must have the correct printer driver software installed.  Specifically, the PPD file must exist at the specified path on each client.  Typically, this can be accomplished by adding the printer driver software as a managed install to the same group manifest.

Expected Input Data
----------
Details for each print queue are expected to be defined using this structure in each manifest's __metadata_ dictionary:
* *print_queues*:  an array of dictionaries, where each dictionary contains these keys to describe the print queue:
    * _name_ (string, required): A name for the CUPS print queue.  Cannot have spaces.  Also used for the display name.
    * _ppd_path_ (string, required): The path to the PPD file for the queue as it is (or would be) installed on the client's filesystem.
    * _device_uri_ (string, required): The CUPS URI for the printer; for example, _smb://server/queue_.
    * _kerberos_auth_required_ (boolean, optional): If the queue requires Kerberos authentication, set this to true.  Otherwise, omit it.
    * _additional_cups_opts_ (array of strings, optional): These are &#8220;key value&#8221; pairs that would be passed to _lpadmin_ with various -o switches.
    * _display_name_ (string, optional): An optional &#8220;friendly name&#8221; for the queue to be displayed in the UI.

Additional Notes
----------
* The client system must be bound to and communicating with Active Directory for queues that require Kerberos authentication.  Its system clock must be within five minutes of the time on the KDC.
* The PPD for the print queue to be added must be installed.  If not, the queue is skipped.  This condition script will keep trying to add the printer, so, if the PPD is installed later, the queue will be added upon next check-in.
* This condition script does *not* remove any print queues.  It only adds to them.  To that end consider the following:
    * If the group manifest's _print_queues_ key is edited and a queue is removed, that queue will remain on any computers that have already added it.
    * If a computer is re-assigned to another computer group manifest, any print queues added by direction of the first group manifest will remain.
    * If the URI (server path or queue name) change, this condition script simply adds a new queue.  It does not remove a previous one.
     

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
3. https://github.com/munki/munki/wiki/Managing-Printers-With-Munki
4. https://developer.apple.com/library/mac/documentation/Darwin/Reference/ManPages/man8/lpadmin.8.html
5. https://developer.apple.com/library/mac/documentation/Darwin/Reference/ManPages/man1/lpoptions.1.html
