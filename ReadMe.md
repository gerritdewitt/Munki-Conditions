About this Repository
----------
This repository contains materials for creating an Apple Installer package for deploying Munki conditional scripts.  The package's root is _package-root_ within this tree.

The condition scripts are meant to be deployed to client systems.  Inside _package-root_, you'll see that they are deployed to _usr/local/munki/conditions_, so munki will execute them on each check-in.<sup>1,2</sup>.

About Conditions
----------
Munki Conditions are key-value pairs stored in a conditions plist file.  These pairs are written by scripts deployed into the _/usr/local/munki/conditions/_ directory.  Whenever munki checks in, it deletes the conditions file and runs the scripts.  Thus, the conditions plist is updated on each check-in.  The information stored in it can be used by munki to determine if certain optional installs, managed installs, or managed updates are to be offered.  It's important to note that the condition scripts are executed *first*, as their data must be present so that munki can interpret various conditional items it receives in the manifests.  The conditions plist file is _/Library/Managed Installs/ConditionalItems.plist_.

Conditions involve two components:
* Creating and deploying a condition script.  To understand how to do this, you should be familiar with how munki works (pkginfo, catalogs, manifests), and with our procedure for adding items to the munki repository.  The condition script is deployed to the client just like any other item munki would deploy.  After deployment, it is first run whenever munki attempts its next check-in.  The munki project documents specifications for these scripts, and several examples are provided online<sup>1,2</sup>.
* Offering items conditionally - for example, offering certain optional installs based on the results of the conditional scripts - is done by adding a conditions dictionary to the manifest with the offering.  This is best done by manually editing the appropriate manifest in the munki repository.  Munki's _manifestutil_ does not have commands for manipulating conditional offerings.

Creating the Condition Scripts Package
----------
* Edit the conditional scripts to meet your needs.
* **ad-status.py**: Make sure to edit and specify:
   - the names of your forest (AD_FOREST) and domain (AD_DOMAIN)
   - the identifiers of any configuration profiles that should be removed if unbinding:  (This condition will unbind systems if it determines they are on the network but not properly communicating with AD so your automation for re-binding can key off of its output.) Typically, these are profiles that would be re-installed when re-bound.  For example, if you bind to AD with a configuration profile, that profile would need to be removed prior to rebinding.  Also any profiles with AD Certificate payloads should be removed so they may be reinstalled; for example, you might have a Wi-Fi payload for EAP-TLS that carries an AD Certificate payload. 
- **admin-groups.py**: Edit and specify the DIRECTORY_SEARCH_NODE path so that GUIDs for various groups to be nested can be determined by searching that directory node.
* To build the installer package, simply run the _make-installer-pkg.sh_ script.  The script is interactive; it will produce an Apple Installer package.

Deploying the Condition Scripts with Munki
----------
To deploy the conditions, add the resulting installer package to the Munki repository and configure it as a managed install for all systems.  For GSU, we add all conditions to the _configuration_ catalog and deploy them via the _includes/conditions_ manifest (which is included by reference in all our manifests).

For example:
<pre>
# Copy to repo:
sudo cp Munki_Conditions-2017.01.pkg /mounts/munki-repo/pkgs/
# Generate pkginfo:
sudo -s
makepkginfo --unattended_install --name Munki_Conditions --displayname="Munki Conditions" \
--pkgvers=2017.01 --catalog=configuration --developer="GSU" --category="Misc" \
/mounts/munki-repo/pkgs/Munki_Conditions-2017.01.pkg > /mounts/munki-repo/pkgsinfo/Munki_Conditions-2017.01
exit
# Update catalogs:
sudo makecatalogs
# Add to manifest:
sudo manifestutil add-pkg GSU_Munki_Conditions --section managed_installs --manifest includes/conditions
</pre>

Author
----------
Written by Gerrit DeWitt (gdewitt@gsu.edu)
Copyright Georgia State University

Sources
----------
1. https://github.com/munki/munki/wiki/Conditional-Items
2. https://github.com/timsutton/munki-conditions
