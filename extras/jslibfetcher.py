import os
import requests
import sys

download_errors = []

ALLOWED = "allowed"
WARNING = "warning"

ANGULARJS_VERSIONS = {
    WARNING: [
        "1.5.7",
    ],
}

BACKBONE_VERSIONS = {
    ALLOWED: [
        "1.0.0",
        "1.1.0",
        "1.1.1",
        "1.1.2",
    ]
}

DOJO_VERSIONS = {
    ALLOWED: [
        "1.5.0",
        "1.5.1",
        "1.6.0",
        "1.6.1",
        "1.7.0",
        "1.7.1",
        "1.7.2",
        "1.7.3",
        "1.8.0",
        "1.8.1",
        "1.8.2",
        "1.8.3",
        "1.8.4",
        "1.8.5",
        "1.8.6",
        "1.9.0",
        "1.9.1",
        "1.9.2",
        "1.9.3",
    ]
}

JQUERY_VERSIONS = {
    WARNING: [
        "1.5",
        "1.5.1",
        "1.5.2",
        "1.6",
        "1.6.1",
        "1.6.2",
        "1.6.3",
        "1.6.4",
        "1.7",
        "1.7.1",
        "1.7.2",
        "1.8.0",
        "1.8.1",
        "1.8.2",
        "1.8.3",
        "1.9.0",
        "1.9.1",
        "1.10.0",
        "1.10.1",
        "1.10.2",
        "1.11.0",
        "1.11.1",
        "1.11.2",
        "1.11.3",
        "1.12.0",
        "1.12.1",
        "1.12.2",
        "1.12.3",
        "1.12.4",
    ],
    ALLOWED: [
        "2.0.0",
        "2.0.1",
        "2.0.2",
        "2.0.3",
        "2.1.0",
        "2.1.1",
        "2.1.2",
        "2.1.3",
        "2.1.4",
        "2.2.0",
        "2.2.1",
        "2.2.2",
        "2.2.3",
        "2.2.4",
        "3.0.0",
    ]
}

JQUERYUI_VERSIONS = {
    ALLOWED: [
        "1.8.8",
        "1.8.9",
        "1.8.10",
        "1.8.11",
        "1.8.12",
        "1.8.13",
        "1.8.14",
        "1.8.15",
        "1.8.16",
        "1.8.17",
        "1.8.18",
        "1.8.19",
        "1.8.20",
        "1.8.21",
        "1.8.22",
        "1.8.23",
        "1.8.24",
        "1.9.0",
        "1.9.1",
        "1.9.2",
        "1.10.0",
        "1.10.1",
        "1.10.2",
        "1.10.3",
        "1.10.4",
        "1.11.0",
        "1.11.1",
        "1.11.2",
        "1.11.3",
        "1.11.4",
        "1.12.0",
    ]
}

MOMENTJS_VERSIONS = {
    ALLOWED: [
        "2.9.0",
        "2.10.2",
        "2.10.3",
        "2.10.5",
        "2.10.6",
    ]
}

MOOTOOLS_VERSIONS = {
    ALLOWED: [
        "1.3.1",
        "1.3.2",
        "1.4.0",
        "1.4.1",
        "1.4.2",
        "1.4.3",
        "1.4.4",
        "1.4.5",
        "1.5.0",
    ]
}

PROTOTYPE_VERSIONS = {
    ALLOWED: [
        "1.7.1.0",
        "1.7.2.0",
    ]
}

UNDERSCORE_VERSIONS = {
    ALLOWED: [
        "1.1.4",
        "1.1.5",
        "1.1.7",
        "1.2.0",
        "1.2.1",
        "1.2.2",
        "1.2.3",
        "1.2.4",
        "1.3.0",
        "1.3.1",
        "1.3.2",
        "1.3.3",
        "1.4.0",
        "1.4.1",
        "1.4.2",
        "1.4.3",
        "1.4.4",
        "1.5.0",
        "1.5.1",
        "1.5.2",
        "1.6.0",
        "1.7.0",
        "1.8.0",
        "1.8.1",
        "1.8.2",
        "1.8.3",
    ]
}


def process(url, rule, file):
    dest_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                               sys.argv[1], rule)

    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)

    destination = os.path.join(dest_folder, file)
    if os.path.exists(destination):
        return

    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(destination, "wb") as code:
            code.write(response.content)
            print "Downloaded: {}".format(url)
    except requests.exceptions.HTTPError as e:
        global download_errors
        download_errors.append((response.url, response.status_code, response.reason))


def get_pattern(prefix, url_pattern, library):
    for rule, versions in library.iteritems():
        for version in versions:
            url = url_pattern % version
            process(url, rule, "%s.%s.%s" % (prefix, version, url.split("/")[-1]))


def get_patterns():
    # AngularJS
    get_pattern("angularjs",
                "https://code.angularjs.org/%s/angular.js",
                ANGULARJS_VERSIONS)
    get_pattern("angularjs",
                "https://code.angularjs.org/%s/angular.min.js",
                ANGULARJS_VERSIONS)

    # Backbone
    get_pattern("backbone",
                "https://raw.githubusercontent.com/jashkenas/backbone/%s/backbone.js",
                BACKBONE_VERSIONS)
    get_pattern("backbone",
                "https://raw.githubusercontent.com/jashkenas/backbone/%s/backbone-min.js",
                BACKBONE_VERSIONS)

    # Dojo Toolkit
    get_pattern("dojo",
                "https://download.dojotoolkit.org/release-%s/dojo.js",
                DOJO_VERSIONS)
    get_pattern("dojo",
                "https://download.dojotoolkit.org/release-%s/dojo.js.uncompressed.js",
                DOJO_VERSIONS)

    # jQuery
    get_pattern("jquery",
                "https://code.jquery.com/jquery-%s.js",
                JQUERY_VERSIONS)
    get_pattern("jquery",
                "https://code.jquery.com/jquery-%s.min.js",
                JQUERY_VERSIONS)

    # jQueryUI
    get_pattern("jqueryui",
                "https://code.jquery.com/ui/%s/jquery-ui.min.js",
                JQUERYUI_VERSIONS)
    get_pattern("jqueryui",
                "https://code.jquery.com/ui/%s/jquery-ui.js",
                JQUERYUI_VERSIONS)

    # moment.js
    get_pattern("moment",
                "https://raw.githubusercontent.com/moment/moment/%s/moment.js",
                MOMENTJS_VERSIONS)
    get_pattern("moment",
                "https://raw.githubusercontent.com/moment/moment/%s/min/moment.min.js",
                MOMENTJS_VERSIONS)

    # MooTools
    get_pattern("mootools",
                "https://ajax.googleapis.com/ajax/libs/mootools/%s/mootools-yui-compressed.js",
                MOOTOOLS_VERSIONS)
    get_pattern("mootools",
                "https://ajax.googleapis.com/ajax/libs/mootools/%s/mootools.js",
                MOOTOOLS_VERSIONS)

    # Prototype.js
    get_pattern("prototype",
                "https://ajax.googleapis.com/ajax/libs/prototype/%s/prototype.js",
                PROTOTYPE_VERSIONS)

    # Underscore
    get_pattern("underscore",
                "https://raw.github.com/documentcloud/underscore/%s/underscore.js",
                UNDERSCORE_VERSIONS)
    get_pattern("underscore",
                "https://raw.github.com/documentcloud/underscore/%s/underscore-min.js",
                UNDERSCORE_VERSIONS)

print "Downloading third-party library files..."
get_patterns()
if download_errors:
    for url, code, reason in download_errors:
        print "Failed: {} is '{}' ({}).".format(url, reason, code)
    print "Some files failed to download, please check the output above...Exiting."
    sys.exit(1)
print "Downloading third-party library files complete."
