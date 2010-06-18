
import decorator

APPLICATIONS = {
    "{ec8030f7-c20a-464f-9b0e-13a3a9e97384}": "firefox",
    "{86c18b42-e466-45a9-ae7a-9b95ba6f5640}": "mozilla",
    "{3550f703-e582-4d05-9a08-453d09bdfdc6}": "thunderbird",
    "{718e30fb-e89b-41dd-9da7-e25a45638b28}": "sunbird",
    "{92650c4d-4b8e-4d2a-b7eb-24ecf4f6b63a}": "seamonkey",
    "{a23983c0-fd0e-11dc-95ff-0800200c9a66}": "fennec"
}
APPROVED_APPLICATIONS = {
    # Firefox =============================
    "{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
        ['0.3', '0.6', '0.7', '0.7+', '0.8', '0.8+', '0.9.x', '0.9',
        '0.9.0+', '0.9.1+', '0.9.2+', '0.9.3', '0.9.3+', '0.9+',
        '0.10', '0.10.1', '0.10+', '1.0', '1.0.1', '1.0.2', '1.0.3',
        '1.0.4', '1.0.5', '1.0.6', '1.0.7', '1.0.8', '1.0+', '1.4',
        '1.4.0', '1.4.1', '1.5b1', '1.5b2', '1.5', '1.5.0.4',
        '1.5.0.*', '2.0a1', '2.0a2', '2.0a3', '2.0b1', '2.0b2', '2.0',
        '2.0.0.4', '2.0.0.8', '2.0.0.*', '3.0a1', '3.0a2', '3.0a3',
        '3.0a4', '3.0a5', '3.0a6', '3.0a7', '3.0a8pre', '3.0a8',
        '3.0a9', '3.0b1', '3.0b2pre', '3.0b2', '3.0b3pre', '3.0b3',
        '3.0b4pre', '3.0b4', '3.0b5pre', '3.0b5', '3.0pre', '3.0',
        '3.0.9', '3.0.11', '3.0.12', '3.0.*', '3.1a1pre', '3.1a1',
        '3.1a2pre', '3.1a2', '3.1b1pre', '3.1b1', '3.1b2pre', '3.1b2',
        '3.1b3pre', '3.1b3', '3.5b4pre', '3.5b4', '3.5b5pre', '3.5',
        '3.5.*', '3.6a1pre', '3.6a1', '3.6a2pre', '3.6b1pre', '3.6b2',
        '3.6', '3.6.*', '3.7a1pre', '3.7a1', '3.7a2pre', '3.7a2',
        '3.7a3pre', '3.7a3', '3.7a4pre', '3.7a4', '3.7a5pre'],
    # Mozilla =============================
    "{86c18b42-e466-45a9-ae7a-9b95ba6f5640}":
        ['1.0', '1.1', '1.3', '1.4', '1.4.1', '1.5', '1.5.1', '1.6',
        '1.7', '1.7.7', '1.7.*', '1.8a', '1.8a3', '1.8a4', '1.8a5',
        '1.8a6', '1.8b1', '1.8', '1.8+'],
    # Thunderbird =========================
    "{3550f703-e582-4d05-9a08-453d09bdfdc6}":
        ['0.3', '0.4', '0.5', '0.6', '0.7', '0.7.1', '0.7.1+', '0.7.2',
        '0.7.3', '0.7.3+', '0.7+', '0.8', '0.8+', '0.9', '0.9+', '1.0',
        '1.0.2', '1.0.6', '1.0.8', '1.1a1', '1.0+', '1.5b', '1.5b1',
        '1.5b2', '1.5', '1.5.0.4', '1.5.0.5', '1.5.0.*', '2.0a1',
        '2.0b1', '2.0b2', '2.0', '2.0.0.8', '2.0.0.*', '3.0a1pre',
        '3.0a1', '3.0a2pre', '3.0a2', '3.0a3', '3.0b1pre', '3.0b1',
        '3.0b2pre', '3.0b2', '3.0b3pre', '3.0b3', '3.0b4pre', '3.0b4',
        '3.0pre', '3.0', '3.0.1', '3.0.*', '3.1a1pre', '3.1a1',
        '3.1b1pre', '3.1b1', '3.1b2pre', '3.1b2', '3.1pre', '3.1',
        '3.1.*', '3.2a1pre'],
    # Sunbird =============================
    "{718e30fb-e89b-41dd-9da7-e25a45638b28}":
        ['0.2', '0.3a1', '0.3a2', '0.2+', '0.3', '0.3.1', '0.4a1',
        '0.5', '0.6a1', '0.7pre', '0.7', '0.8pre', '0.8', '0.9pre',
        '0.9', '1.0b1', '1.0pre'],
    # SeaMonkey ===========================
    "{92650c4d-4b8e-4d2a-b7eb-24ecf4f6b63a}":
        ['1.0a', '1.0', '1.0.*', '1.1a', '1.1b', '1.1', '1.1.*',
        '1.5a', '2.0a', '2.0a1pre', '2.0a1', '2.0a2pre', '2.0a2',
        '2.0a3pre', '2.0a3', '2.0b1pre', '2.0b1', '2.0b2pre', '2.0b2',
        '2.0pre', '2.0', '2.0.1', '2.0.*', '2.1a1pre', '2.1a1',
        '2.1a2pre', '2.1a2'],
    # Fennec ==============================
    "{a23983c0-fd0e-11dc-95ff-0800200c9a66}":
        ['0.1', '0.7', '1.0a1', '1.0b1', '1.0b2pre', '1.0b2',
        '1.0b6pre', '1.0', '1.0.*', '1.1a1', '1.1a2pre', '1.1b1',
        '1.1.*', '2.0a1pre']
}


@decorator.register_test(tier=2)
def test_targetedapplications(err, package_contents=None,
                              xpi_package=None):
    """Tests to make sure that the targeted applications in the
    install.rdf file are legit and that any associated files (I'm
    looking at you, SeaMonkey) are where they need to be."""
    
    if not err.get_resource("has_install_rdf"):
        return
    
    install = err.get_resource("install_rdf")
    
    # Search through the install.rdf document for the SeaMonkey
    # GUID string.
    ta_predicate = install.uri("targetApplication")
    ta_guid_predicate = install.uri("id")
    ta_min_ver = install.uri("minVersion")
    ta_max_ver = install.uri("maxVersion")
    
    used_targets = [];
    
    vererr_pattern = "Invalid version number (%s) for application %s"
    mismatch_pattern = "Version numbers for %s are invalid."
    
    # Isolate all of the bnodes referring to target applications
    for target_app in install.get_objects(None, ta_predicate):
        
        # Get the GUID from the target application
        
        for ta_guid in install.get_objects(target_app,
                                           ta_guid_predicate):
            
            used_targets.append(ta_guid)
            
            if ta_guid == "{92650c4d-4b8e-4d2a-b7eb-24ecf4f6b63a}":
                
                # Time to test for some install.js.
                if not "install.js" in package_contents:
                    err.warning("Missing install.js for SeaMonkey.",
                                """SeaMonkey requires install.js, which
                                was not found. install.rdf indicates
                                that the addon supports SeaMonkey.""",
                                "install.rdf")
                    # Only reject if it's a dictionary.
                    if err.detected_type == 2:
                        err.reject = True
                
                break
            
            if ta_guid in APPROVED_APPLICATIONS:
                
                # Grab the minimum and maximum version numbers.
                min_version = install.get_object(target_app, ta_min_ver)
                max_version = install.get_object(target_app, ta_max_ver)
                
                app_versions = APPROVED_APPLICATIONS[ta_guid]
                
                # Ensure that the version numbers are in the app's
                # list of acceptable version numbers.
                
                try:
                    if min_version is not None:
                        min_ver_pos = app_versions.index(min_version)
                except ValueError:
                    err.error(vererr_pattern % (min_version, ta_guid),
                              """The minimum version that was specified
                              is not an acceptable version number for
                              the Mozilla product that it corresponds
                              with.""",
                              "install.rdf")
                    continue
                    
                try:
                    if max_version is not None:
                        max_ver_pos = app_versions.index(max_version)
                except ValueError:
                    err.error(vererr_pattern % (max_version, ta_guid),
                              """The maximum version that was specified
                              is not an acceptable version number for
                              the Mozilla product that it corresponds
                              with.""",
                              "install.rdf")
                    continue
                
                # Now we need to check to see if the version numbers
                # are in the right order.
                if min_version is not None and \
                   max_version is not None and \
                   min_ver_pos > max_ver_pos:
                    err.error(mismatch_error % ta_guid,
                              """The veresion numbers provided for the
                              application in question are not in the
                              correct order. The maximum version must
                              be greater than the minimum version.""",
                              "install.rdf")
    
    no_duplicate_targets = set(used_targets)
    
    if len(used_targets) != len(no_duplicate_targets):
        err.warning("Found duplicate <em:targetApplication> elements.",
                    """Multiple targetApplication elements were found
                    in the install.manifest file that refer to the same
                    application GUID. There should not be duplicate
                    target applications entries.""",
                    "install.rdf")
    
    # This finds the UUID of the supported applications and puts it in
    # a fun and easy-to-use format for use in other tests.
    supports = []
    for target in used_targets:
        key = str(target)
        if key in APPLICATIONS:
            supports.append(APPLICATIONS[key])
    err.save_resource("supports", supports)
    

