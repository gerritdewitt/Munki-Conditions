About this Repository
----------
This repository contains materials for creating an Apple Installer package for deploying Munki conditional scripts.  The package's root is _package-root_ within this tree.

The condition scripts are menat to be deployed to client systems.  Inside _package-root_, you'll see that they are deployed to _usr/local/munki/conditions_, so munki will execute them on each check-in.<sup>1,2</sup>.

About Conditions
----------
Munki Conditions are key-value pairs stored in a conditions plist file.  These pairs are written by scripts deployed into the _/usr/local/munki/conditions/_ directory.  Whenever munki checks in, it deletes the conditions file and runs the scripts.  Thus, the conditions plist is updated on each check-in.  The information stored in it can be used by munki to determine if certain optional installs, managed installs, or managed updates are to be offered.  It's important to note that the condition scripts are executed *first*, as their data must be present so that munki can interpret various conditional items it receives in the manifests.  The conditions plist file is _/Library/Managed Installs/ConditionalItems.plist_.

Conditions involve two components:
* Creating and deploying a condition script.  To understand how to do this, you should be familiar with how munki works (pkginfo, catalogs, manifests), and with our procedure for adding items to the munki repository.  The condition script is deployed to the client just like any other item munki would deploy.  After deployment, it is first run whenever munki attempts its next check-in.  The munki project documents specifications for these scripts, and several examples are provided online<sup>1,2</sup>.
* Offering items conditionally - for example, offering certain optional installs based on the results of the conditional scripts - is done by adding a conditions dictionary to the manifest with the offering.  This is best done by manually editing the appropriate manifest in the munki repository.  Munki's _manifestutil_ does not have commands for manipulating conditional offerings.

Creating the Condition Scripts Package
----------
* Edit the conditional scripts to meet your needs.  For example, these conditions have some global variables that will be specific to your enterprise:
      - **ad-test.py**
      - **admin-groups.py**
* To build the installer package, simply run the _make-installer-pkg.sh_ script.  The script is interactive; it will produce an Apple Installer package.

Deploying the Condition Scripts with Munki
----------
To deploy the conditions, add the resulting installer package to the Munki repository and configure it as a managed install for all systems.  For GSU, we add all conditions to the _configuration_ catalog and deploy them via the _includes/conditions_ manifest (which is included by reference in all our manifests).

For example:
<pre>
# Copy to repo:
sudo cp GSU_Munki_Conditions-2016.06.pkg /mounts/munki-repo/pkgs/
# Generate pkginfo:
sudo -s
makepkginfo --unattended_install --name GSU_Munki_Conditions --displayname="GSU Munki Conditions" \
--pkgvers=2016.06 --catalog=configuration --developer="GSU" --category="Misc" \
/mounts/munki-repo/pkgs/GSU_Munki_Conditions-2016.06.pkg > /mounts/munki-repo/pkgsinfo/GSU_Munki_Conditions-2016.06
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
