Print Queues Condition (_print-queues.py_)
----------
*Purpose:* This condition script reads metadata from Munki manifest files (cached as of the previous Munki check-in), looking for custom dictionaries describing print queues added to the *_metadata* key in each.  It adds the defined print queues if necessary; otherwise, it simply maintains their CUPS attributes.  After it finishes, it writes a single array of dictionaries to the conditions file:
* **managed_print_queues**: Array of Dictionaries.  This is a union of any unique dictionaries found in the *_metadata:print_queues* array in each cached manifest.  It also includes result and timestamp keys indicating if adding/modifying the queues was successful and when the event happened.

*Requirements:*
In addition to the Munki Conditions being deployed...
 * At least one print queue defined in the metadata of at least one manifest.
 * The computer must have the correct printer driver software installed.  Specifically, the PPD file must exist at the specified path on each client.  Typically, this can be accomplished by adding the printer driver software as a managed install to the same group manifest.

Expected Input Data
----------
Details for each print queue are expected to be defined using this structure in each manifest's *_metadata* dictionary:
* *print_queues*:  an array of dictionaries, where each dictionary contains these keys to describe the print queue:
    * *name* (string, required): A name for the CUPS print queue.  Cannot have spaces.  Also used for the display name.
    * *ppd_path* (string, required): The path to the PPD file for the queue as it is (or would be) installed on the client's filesystem.
    * *device_uri* (string, required): The CUPS URI for the printer; for example, *smb://server/queue*.
    * *kerberos_auth_required* (boolean, optional): If the queue requires Kerberos authentication, set this to true.  Otherwise, omit it.
    * *additional_cups_opts* (array of strings, optional): These are key-value pairs that would be passed to *lpadmin* with various -o switches.
    * *display_name* (string, optional): An optional friendly name for the queue to be displayed in the UI.

Additional Notes
----------
* The client system must be bound to and communicating with Active Directory for queues that require Kerberos authentication.  Its system clock must be within five minutes of the time on the KDC.
* The PPD for the print queue to be added must be installed.  If not, the queue is skipped.  This condition script will keep trying to add the printer, so, if the PPD is installed later, the queue will be added upon next check-in.
* This condition script does *not* remove any print queues.  It only adds to them.  To that end consider the following:
    * If the group manifest's *print_queues* key is edited and a queue is removed, that queue **will remain** on any computers that have already added it.
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
