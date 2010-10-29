==============================
 addons.mozilla.org Validator
==============================
-------------
 Version 1.0
-------------

This validator is a proposed replacement for the current add-on
validator available at addons.mozilla.org. It is written entirely in
python.

Prerequisites
=============

Python Libraries:

- argparse
- cssutils
- rdflib
- chardet

Python Libraries for Testing:

- nose
- coverage

You can install everything you need for running and testing with ::

    pip install -r requirements.txt

Spidermonkey
------------

A working copy of Spidermonkey (debug or non-debug is fine) is a required. The
version installed must include support for the Parser API. Downloading and
installing the latest copy of Tracemonkey from http://mg.mozilla.org/ will
include this API.

Documentation on getting the latest Spidermonkey source:

https://developer.mozilla.org/En/SpiderMonkey/Getting_SpiderMonkey_source_code#Getting_the_latest_SpiderMonkey_source_code

Once Spidermonkey is installed, the path to the JavaScript shell must be
specified in the /validator/constants.php file in the
`SPIDERMONKEY_INSTALLATION` variable. If this variable is set to `None`, no
JavaScript tests will be run.

Running
=======

Run the validator as follows ::

	python addon-validator <path to xpi> [-t <expected type>] [-o <output type>] [-v] [--file <output file>] [--boring] [--selfhosted]

The path to the XPI should point to an XPI file.


Expected Type:
--------------

The expected type should be one of the following values:

any (default)
	Accepts any extension
extension
	Accepts only extensions
theme
	Accepts only themes
dictionary
	Accepts only dictionaries
languagepack
	Accepts only language packs
search
	Accepts only OpenSearch XML files (unpackaged)
multi
	Accepts only multi-item XPI packages

Specifying an expected type will throw an error if the validator
does not detect that particular type when scanning. All addon type
detection mechanisms are used to make this determination.


Output Type:
------------

The output type may be either of the following:

text (default)
	Outputs a textual summary of the addo-on analysis. Supports verbose mode.
json
	Outputs a JSON snippet representing a full summary of the add-on analysis.


Verbose Mode:
-------------

If the "-v" flag is set, the output will include informational
messages in addition to errors and warnings. Informational messages
contain information about the analysis that do not invalidate the
add-on, but are contextually relevant.

Verbose mode will also output detailed descriptions of each summary
item, as well as the file path and line number (if available).

This mode is only supported by certain output types. Output types
that do not support verbose mode will output informational messages by
default.


Output File:
------------

Specifying an output file with the "--file" flag captures the output of
the analysis and stores it to the file specified. Specifying this
option will not produce any output to the command line.

When outputting to a file, Boring Mode is automatically activated.


Boring Mode:
------------

Boring mode, when activated, doesn't print colors to the terminal.

Determined Mode:
----------------

With determination comes perseverance. When in determined mode, the validator
will not stop validating after errors present themselves in a particular tier.
Traditionally, if an error tier fails, subsequent tiers are not executed. This
flag ensures that those tiers are indeed run.

Note that enabling this option may cause issues with certain tests, as some
higher-level tiers depend on information provided by lower tiers. This data
may not be available as the add-on was never meant to make it to the higher
tiers.


Output
======

Text Output Mode:
-----------------

In text output mode ("text"), output is structured in the format of one
message per line. The messages are prefixed by their priority level
(i.e.: "Warning: This is the message").

At the head of the text output is a block describing what the
add-on type was determined to be.


JSON Output Mode:
-----------------

In JSON output mode ("json"), output is formatted as a JSON snippet
containing all messages. The format for the JSON output is that of the
sample document below.

::

	{
		"detected_type": "extension",
		"errors":2,
		"warnings":1,
		"notices":1,
		"success": false,
	    "rejected": false,
		"messagetree":{ /* ... */ },
		"messages": [
			{
				"uid": "123456789",
				"id": ["module", "function", "error"],
				"type": "error",
				"message": "This is the error message text.",
				"description": ["Description of the error message.",
				                "Additional description text"],
				"file": "",
				"line": 0
			},
			{
				"uid": "123456789",
				"id": ["module", "function", "error"],
				"type": "warning",
				"message": "This is the warning message text.",
				"description": "Description of the warning message.",
				"file": "testfile.xml",
				"line": 0
			},
			{
				"uid": "123456789",
				"id": ["module", "function", "error"],
				"type": "notice",
				"message": "This is the informational message text.",
				"description": "Description of the info message."
				"file": "chrome.manifest",
				"line": 21
			},
			{
				"uid": "123456789",
				"id": ["module", "function", "error"],
				"type": "error",
				"message": "test.xpi > An error was found.",
				"description": "This error happened within a subpackage."
				"file": [
					"test.xpi",
					"chrome.manifest"
				],
				"line": 21
			}
		]
	}


The `message_tree` element to the document above contains a series of
JavaScript objects organized into a tree structure. The key of each element in
the tree is the the name of each successive part of the validator that
generated a particular message or set of messages (increasing in specificity as
the depth of the tree increases). Each tree element also includes a series of
additional nodes which provide extra information:

::

	__errors - number - The number of errors generated in this node
	__warnings - number - The number of warnings generated in this node
	__notices - number - The number of messages generated in this node
	__messages - list - A list of UIDs from messages in the `messages` node

JSON Notes:
~~~~~~~~~~~

When a subpackage exists, an angle bracket will delimit the subpackage
name and the message text.

If no applicable file is available (i.e.: when a file is missing), the
`file` value will be empty. If a `file` value is available within a
subpackage, then the `file` attribute will be a list containing the
name of the outermost subpackage's name, followed by each successive
concentric subpackage's name, followed by the name of the file that the
message was generated in. If no applicable file is available within a
subpackage, the `file` attribute is identical, except the last element
of the list in the `file` attribute is an empty string.

For instance, this tree would generate the following messages:

::

	package_to_test.xpi
		|
		|-install.rdf
		|-chrome.manifest
		|-subpackage.xpi
		|  |
		|  |-subsubpackage.xpi
		|     |
		|     |-chrome.manifest
		|     |-install.rdf
		|
		|-subpackage.jar
		   |
		   |-install.rdf

::

	{
		"type": "notice",
		"message": "<em:type> not found in install.rdf",
		"description": " ... ",
		"file": "install.rdf",
		"line": 0
	},
	{
		"type": "error",
		"message": "Invalid chrome.manifest subject: override",
		"description": " ... ",
		"file": "chrome.manifest",
		"line": 7
	},
	{
		"type": "error",
		"message": "subpackage.xpi > install.rdf missing from theme",
		"description": " ... ",
		"file": ["subpackage.xpi", ""],
		"line": 0
	},
	{
		"type": "error",
		"message": "subpackage.xpi > subsubpackage.xpi > Invalid chrome.manifest subject: sytle",
		"description": " ... ",
		"file": ["subpackage.xpi", "subsubpackage.xpi", "chrome.manifest"],
		"line": 5
	}

Batch Testing
=============

As a helpful tool for testing multiple add-ons, the following script will
allow you to validate a whole directory of add-ons. ::

	find /directory/to/scan/ -type f -exec python addon-validator {} -v --file {}.txt \;

The output from this script will be placed in the same folder as the addons.
The name of the output files will be the same as the add-on's name with ".txt"
appended to the end.

Testing
=======

Unit tests can be run with ::

	fab test

or, after setting the proper python path: ::

    nosetests

However, to turn run unit tests with code coverage, the appropriate
command would be: ::

	nosetests --with-coverage --cover-package=validator --cover-skip=validator.argparse,validator.outputhandlers.,validator.main --cover-inclusive --cover-tests

Note that in order to use the --cover-skip nose parameter, you must install the included patch for nose's coverage.py plugin: ::

	extras/cover.py
