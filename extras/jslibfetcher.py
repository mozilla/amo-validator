import urllib
import os

def get_pattern(prefix, url_pattern, versions):

    for version in versions:
        version = version
        url = url_pattern % version
        name = "%s.%s.%s" % (prefix, version, url.split("/")[-1])

        if os.path.exists("jslibs/%s" % name):
            continue

        try:
            print url
            urllib.urlretrieve(url, "jslibs/%s" % name)
        except Exception:
            print "Failed"

DOJO_VERSIONS = ("1.1.1", "1.2.0", "1.2.3", "1.3.0", "1.3.1", "1.3.2", "1.4.0",
                 "1.4.1", "1.4.3", "1.5", "1.5.1", "1.6", "1.6.1")
# Google doesn't yet host EXT4.*
EXT_VERSIONS = ("3.0.0", "3.1.0")
JQUERY_CODE_VERSIONS = ("1.0.pack", "1.0.1.pack", "1.0.1", "1.0.2.pack",
                        "1.0.2", "1.0.3.pack", "1.0.3", "1.0.4.pack", "1.0.4",
                        "1.1.pack", "1.1", "1.1.1.pack", "1.1.1", "1.1.2.pack",
                        "1.1.2", "1.1.3.pack", "1.4.min", "1.4", "1.4.1.min",
                        "1.4.1", "1.4.2.min", "1.4.2", "1.4.3.min", "1.4.4",
                        "1.5.min", "1.5", "1.5.1.min", "1.5.1", "1.5.2.min",
                        "1.5.2", "1.6.min", "1.6", "1.6.1.min", "1.6.1",
                        "1.6.2.min", "1.6.2", "1.6.3.min", "1.6.3",
                        "1.6.4.min", "1.6.4", "1.7.min", "1.7", "1.7.1.min",
                        "1.7.1", )
JQUERY_GCODE_VERSIONS = ("1.1.3", "1.1.3.1.pack", "1.1.3.1", "1.1.4.pack",
                         "1.1.4", "1.2.min", "1.2.pack", "1.2", "1.2.1.min",
                         "1.2.1.pack", "1.2.1", "1.2.2.pack", "1.2.2.min",
                         "1.2.2", "1.2.3.pack", "1.2.3.min", "1.2.3",
                         "1.2.4.min", "1.2.4.pack", "1.2.4", "1.2.5.min",
                         "1.2.5.pack", "1.2.5", "1.2.6.min", "1.2.6.pack",
                         "1.2.6", "1.3.min", "1.3", "1.3.1.min", "1.3.1",
                         "1.3.2.min", "1.3.2")
JQUERYUI_VERSIONS = ("1.5.2", "1.5.3", "1.6.0", "1.7.0", "1.7.1", "1.7.2",
                     "1.7.3", "1.8.0", "1.8.1", "1.8.2", "1.8.4", "1.8.5",
                     "1.8.6", "1.8.7", "1.8.8", "1.8.9", "1.8.10", "1.8.11",
                     "1.8.12", "1.8.13", "1.8.14", "1.8.15", "1.8.16")
MOOTOOLS_VERSIONS = ("1.1.1", "1.1.2", "1.2.1", "1.2.2", "1.2.3", "1.2.4",
                     "1.2.5", "1.3.0", "1.3.1", "1.3.2", "1.4.0", "1.4.1")
PROTOTYPE_VERSIONS = ("1.6.0.2", "1.6.0.3", "1.6.1.0", "1.7.0.0")
SCRIPTACULOUS_VERSIONS = ("1.8.1", "1.8.2", "1.8.3", "1.9.0")
SWFOBJECT_VERSIONS = ("2.1", "2.2")
YUI_VERSIONS = ("2.6.0", "2.7.0", "2.8.0r4", "2.8.1", "2.8.2", "2.9.0")
YUI_NEW_VERSIONS = ("3.3.0", )


get_pattern("dojo",
            "https://ajax.googleapis.com/ajax/libs/dojo/%s/dojo/dojo.xd.js",
            DOJO_VERSIONS)
get_pattern("dojo",
            "https://ajax.googleapis.com/ajax/libs/dojo/%s/dojo/dojo.xd.js.uncompressed.js",
            DOJO_VERSIONS)
DOJO_V = lambda v:"http://download.dojotoolkit.org/" \
                  "release-%s/dojo-release-%s/release/dojo-release-%s/" \
                  "dojo/%%s" % (v, v, v)
urllib.urlretrieve(DOJO_V("1.0.3") % "dojo.js",
                   "jslibs/dojo.1.0.3.js")
urllib.urlretrieve(DOJO_V("1.0.3") % "dojo.js.uncompressed.js",
                   "jslibs/dojo.uncompressed.1.0.3.js")

urllib.urlretrieve(DOJO_V("1.1.2") % "dojo.js",
                   "jslibs/dojo.1.1.2.js")
urllib.urlretrieve(DOJO_V("1.1.2") % "dojo.js.uncompressed.js",
                   "jslibs/dojo.uncompressed.1.1.2.js")

urllib.urlretrieve(DOJO_V("1.2.4") % "dojo.js",
                   "jslibs/dojo.1.2.4.js")
urllib.urlretrieve(DOJO_V("1.2.4") % "dojo.js.uncompressed.js",
                   "jslibs/dojo.uncompressed.1.2.4.js")

urllib.urlretrieve(DOJO_V("1.3.3") % "dojo.js",
                   "jslibs/dojo.1.3.3.js")
urllib.urlretrieve(DOJO_V("1.3.3") % "dojo.js.uncompressed.js",
                   "jslibs/dojo.uncompressed.1.3.3.js")

# EXT.js
get_pattern("ext-core",
            "https://ajax.googleapis.com/ajax/libs/ext-core/%s/ext-core.js",
            EXT_VERSIONS)
get_pattern("ext-debug",
            "https://ajax.googleapis.com/ajax/libs/ext-core/%s/ext-core-debug.js",
            EXT_VERSIONS)

# jQuery
get_pattern("jquery",
            "http://code.jquery.com/jquery-%s.js",
            JQUERY_CODE_VERSIONS)
get_pattern("jquery",
            "http://jqueryjs.googlecode.com/files/jquery-%s.js",
            JQUERY_GCODE_VERSIONS)

# jQueryUI
get_pattern("jqueryui",
            "https://ajax.googleapis.com/ajax/libs/jqueryui/%s/jquery-ui.min.js",
            JQUERYUI_VERSIONS)
get_pattern("jqueryui",
            "https://ajax.googleapis.com/ajax/libs/jqueryui/%s/jquery-ui.js",
            JQUERYUI_VERSIONS)

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

# Scriptaculous
get_pattern("scriptaculous",
            "https://ajax.googleapis.com/ajax/libs/scriptaculous/%s/scriptaculous.js",
            SCRIPTACULOUS_VERSIONS)

# SWFObject
get_pattern("swfobject",
            "https://ajax.googleapis.com/ajax/libs/swfobject/%s/swfobject.js",
            SWFOBJECT_VERSIONS)
get_pattern("swfobject",
            "https://ajax.googleapis.com/ajax/libs/swfobject/%s/swfobject_src.js",
            SWFOBJECT_VERSIONS)

# Old-style YUI loader libraries:
get_pattern("yui",
            "https://ajax.googleapis.com/ajax/libs/yui/%s/build/yuiloader/"
            "yuiloader-min.js",
            YUI_VERSIONS)
get_pattern("yui",
            "https://ajax.googleapis.com/ajax/libs/yui/%s/build/yuiloader/"
            "yuiloader.js",
            YUI_VERSIONS)

# New-style YUI libraries
get_pattern("yui",
            "https://ajax.googleapis.com/ajax/libs/yui/%s/build/yui/yui.min.js",
            YUI_NEW_VERSIONS)
get_pattern("yui",
            "https://ajax.googleapis.com/ajax/libs/yui/%s/build/yui/yui.js",
            YUI_NEW_VERSIONS)
