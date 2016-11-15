#!/bin/sh

#  make-installer-pkg.sh
#  Munki Conditions Package
#  Script for for creating an installer package with Munki Conditions.

# Written by Gerrit DeWitt (gdewitt@gsu.edu)
# 2015-06-15 (MEC), 2015-08-11 (MEC), 2016-01-05 (MEC), 2016-06-17.
# Copyright Georgia State University.
# This script uses publicly-documented methods known to those skilled in the art.
# References: See top level Read Me.

declare -x PATH="/usr/bin:/bin:/usr/sbin:/sbin"

# MARK: VARIABLES

# Control variable:
declare -i CLEANUP_WHEN_DONE=0

# Variables for package:
declare -x THIS_DIR=$(dirname "$0")
declare -x PACKAGE_IDENTIFIER="org.sample.munki.conditions" # edit to suit your organization
declare -x PACKAGE_ROOT_DIR="$THIS_DIR/package-root"

# MARK: build_package()
# Builds the component pkg.
function build_package(){
    # Set permisions on package root:
    chmod -R 0750 "$PACKAGE_ROOT_DIR" && echo "Set permissions on package root."
    # Remove ._ files from package root:
    find "$PACKAGE_ROOT_DIR" -name ._* -exec rm {} \;
    # Remove .DS_Store files from package root:
    find "$PACKAGE_ROOT_DIR" -name .DS_Store -exec rm {} \;
    # Build MEC package:
    pkgbuild --root "$PACKAGE_ROOT_DIR" --identifier "$PACKAGE_IDENTIFIER" --version "$PACKAGE_VERSION" "$PACKAGE_PATH" && echo "Built package."
    if [ ! -f "$PACKAGE_PATH" ]; then
        echo "Error: Failed to build package."
        exit 1
    fi
}

# MARK: pre_cleanup()
# Sets up packaging environment.
function pre_cleanup(){
    if [ -f "$PACKAGE_PATH" ]; then
        rm "$PACKAGE_PATH" && echo "Removed $PACKAGE_PATH."
    fi
}

# MARK: main()
echo "Enter a version number (for example YYYY.MM like 2016.07):"
read PACKAGE_VERSION
declare -x PACKAGE_PATH="$THIS_DIR/YOUR_ORG_Munki_Conditions-$PACKAGE_VERSION.pkg" # edit to suit your needs
pre_cleanup
build_package
