import json
import nose
import sys
from StringIO import StringIO

import validator.errorbundler as errorbundler
from validator.errorbundler import ErrorBundle
from validator.contextgenerator import ContextGenerator


def test_json():
    """Test the JSON output capability of the error bundler."""

    # Use the StringIO as an output buffer.
    bundle = ErrorBundle() # No color since no output
    bundle.set_type(4)
    bundle.set_tier(4)
    bundle.set_tier(3)

    bundle.error((), "error", "description")
    bundle.warning((), "warning", "description")
    bundle.notice((), "notice", "description")

    results = json.loads(bundle.render_json())

    print results

    assert len(results["messages"]) == 3
    assert results["detected_type"] == 'langpack'
    assert not results["success"]
    assert results["ending_tier"] == 4


def test_boring():
    """Test that boring output strips out color sequences."""

    stdout = sys.stdout
    sys.stdout = StringIO()

    # Use the StringIO as an output buffer.
    bundle = ErrorBundle()
    bundle.error((), "<<BLUE>><<GREEN>><<YELLOW>>")
    bundle.print_summary(no_color=True)

    outbuffer = sys.stdout
    sys.stdout = stdout
    outbuffer.seek(0)

    assert outbuffer.getvalue().count("<<GREEN>>") == 0


def test_type():
    """
    Test that detected type is being stored properly in the error bundle.
    """

    bundle = ErrorBundle()

    bundle.set_type(5)
    assert bundle.detected_type == 5


def test_states():
    """Test that detected type is preserved, even in subpackages."""

    # Use the StringIO as an output buffer.
    bundle = ErrorBundle()

    # Populate the bundle with some test data.
    bundle.set_type(4)
    bundle.error((), "error")
    bundle.warning((), "warning")
    bundle.notice((), "notice")
    bundle.save_resource("test", True)

    # Push a state
    bundle.push_state("test.xpi")

    bundle.set_type(2)
    bundle.error((), "nested error")
    bundle.warning((), "nested warning")
    bundle.notice((), "nested notice")

    # Push another state
    bundle.push_state("test2.xpi")

    bundle.set_type(3)
    bundle.error((), "super nested error")
    bundle.warning((), "super nested warning")
    bundle.notice((), "super nested notice")

    # Test that nested compatibility messages retain their value
    bundle.notice("comp", "Compat Test notice", compatibility_type="error")

    bundle.pop_state()

    bundle.pop_state()

    # Load the JSON output as an object.
    output = json.loads(bundle.render_json())

    # Run some basic tests
    assert output["detected_type"] == "langpack"
    assert len(output["messages"]) == 10

    print output

    messages = ["error",
                "warning",
                "notice",
                "nested error",
                "nested warning",
                "nested notice",
                "super nested error",
                "super nested warning",
                "super nested notice",
                "Compat Test notice"]

    for message in output["messages"]:
        print message

        assert message["message"] in messages
        messages.remove(message["message"])

        assert message["message"].endswith(message["type"])

        if message["id"] == "comp":
            assert message["compatibility_type"] == "error"

    assert not messages

    assert bundle.get_resource("test")


def test_file_structure():
    """
    Test the means by which file names and line numbers are stored in errors,
    warnings, and messages.
    """

    # Use the StringIO as an output buffer.
    bundle = ErrorBundle(True) # No color since no output

    # Populate the bundle with some test data.
    bundle.error((), "error", "", "file1", 123)
    bundle.error((), "error", "", "file2")
    bundle.error((), "error")

    # Push a state
    bundle.push_state("foo")

    bundle.warning((), "warning", "", "file4", 123)
    bundle.warning((), "warning", "", "file5")
    bundle.warning((), "warning")

    bundle.pop_state()

    # Load the JSON output as an object.
    output = json.loads(bundle.render_json())

    # Do the same for friendly output
    output2 = bundle.print_summary(verbose=False)

    # Do the same for verbose friendly output
    output3 = bundle.print_summary(verbose=True)

    # Run some basic tests
    assert len(output["messages"]) == 6
    assert len(output2) < len(output3)

    print output
    print "*" * 50
    print output2
    print "*" * 50
    print output3
    print "*" * 50

    messages = ["file1", "file2", "",
                ["foo", "file4"], ["foo", "file5"], ["foo", ""]]

    for message in output["messages"]:
        print message

        assert message["file"] in messages
        messages.remove(message["file"])

        if isinstance(message["file"], list):
            pattern = message["file"][:]
            pattern.pop()
            pattern.append("")
            file_merge = " > ".join(pattern)
            print file_merge
            assert output3.count(file_merge)
        else:
            assert output3.count(message["file"])

    assert not messages


def test_notice():
    """Test notice-related functions of the error bundler."""

    # Use the StringIO as an output buffer.
    bundle = ErrorBundle()

    bundle.notice((), "")

    # Load the JSON output as an object.
    output = json.loads(bundle.render_json())

    # Run some basic tests
    assert len(output["messages"]) == 1

    print output

    has_ = False

    for message in output["messages"]:
        print message

        if message["type"] == "notice":
            has_ = True

    assert has_
    assert not bundle.failed()
    assert not bundle.failed(True)


def test_notice_friendly():
    """
    Test notice-related human-friendly text output functions of the error
    bundler.
    """

    # Use the StringIO as an output buffer.
    bundle = ErrorBundle()

    bundle.notice((), "foobar")

    # Load the JSON output as an object.
    output = bundle.print_summary(verbose=True, no_color=True)
    print output

    assert output.count("foobar")


def test_initializer():
    """Test that the __init__ paramaters are doing their jobs."""

    e = ErrorBundle()
    assert e.determined
    assert e.get_resource("listed")

    e = ErrorBundle(determined=False)
    assert not e.determined
    assert e.get_resource("listed")

    e = ErrorBundle(listed=False)
    assert e.determined
    assert not e.get_resource("listed")


def test_json_constructs():
    """This tests some of the internal JSON stuff so we don't break zamboni."""

    e = ErrorBundle()
    e.set_type(1)
    e.error(("a", "b", "c"),
            "Test")
    e.error(("a", "b", "foo"),
            "Test")
    e.error(("a", "foo", "c"),
            "Test")
    e.error(("a", "foo", "c"),
            "Test")
    e.error(("b", "foo", "bar"),
            "Test")
    e.warning((), "Context test",
              context=("x", "y", "z"))
    e.warning((), "Context test",
              context=ContextGenerator("x\ny\nz\n"),
              line=2,
              column=0)
    e.notice((), "none")
    e.notice((), "line",
             line=1)
    e.notice((), "column",
             column=0)
    e.notice((), "line column",
             line=1,
             column=1)

    results = e.render_json()
    print results
    j = json.loads(results)

    assert "detected_type" in j
    assert j["detected_type"] == "extension"

    assert "message_tree" in j
    tree = j["message_tree"]

    assert "__errors" not in tree
    assert not tree["a"]["__messages"]
    assert tree["a"]["__errors"] == 4
    assert not tree["a"]["b"]["__messages"]
    assert tree["a"]["b"]["__errors"] == 2
    assert not tree["a"]["b"]["__messages"]
    assert tree["a"]["b"]["c"]["__errors"] == 1
    assert tree["a"]["b"]["c"]["__messages"]

    assert "messages" in j
    for m in (m for m in j["messages"] if m["type"] == "warning"):
        assert m["context"] == ["x", "y", "z"]

    for m in (m for m in j["messages"] if m["type"] == "notice"):
        if "line" in m["message"]:
            assert m["line"] is not None
            assert isinstance(m["line"], int)
            assert m["line"] > 0
        else:
            assert m["line"] is None

        if "column" in m["message"]:
            assert m["column"] is not None
            assert isinstance(m["column"], int)
            assert m["column"] > -1
        else:
            assert m["column"] is None


def test_json_compatibility():
    """Test compatibility elements in the JSON output."""

    err = ErrorBundle()
    err.notice(
        err_id="m1",
        notice="Compat error",
        description="Compatibility error 1",
        compatibility_type="error")

    err.notice(
        err_id="m2",
        notice="Compat error",
        description="Compatibility error 2",
        compatibility_type="error")

    err.warning(
        err_id="m3",
        warning="Compat notice",
        description="Compatibility notice 1",
        compatibility_type="notice")

    err.warning(
        err_id="m4",
        warning="Compat warning",
        description="Compatibility warning 1",
        compatibility_type="warning")

    err.warning(
        err_id="m5",
        warning="Compat warning",
        description="Compatibility warning 1",
        compatibility_type="warning")

    err.error(
        err_id="foo",
        error="Something else",
        description="An error that has nothign to do with compatibility")

    results = err.render_json()
    jdata = json.loads(results)

    assert "compatibility_summary" in jdata
    nose.tools.eq_(jdata["compatibility_summary"],
                   {"errors": 2,
                    "warnings": 2,
                    "notices": 1})
    reference = {"m1": "error",
                 "m2": "error",
                 "m3": "notice",
                 "m4": "warning",
                 "m5": "warning"}

    assert "messages" in jdata and len(jdata["messages"])
    for message in jdata["messages"]:
        if message["id"] in reference:
            print (message["id"],
                   reference[message["id"]],
                   message["compatibility_type"])
            nose.tools.eq_(reference[message["id"]],
                           message["compatibility_type"])


def test_pushable_resources():
    """
    Test that normal resources are preserved but pushable ones are pushed.
    """

    e = ErrorBundle()
    e.save_resource("nopush", True)
    e.save_resource("push", True, pushable=True)

    assert e.get_resource("nopush")
    assert e.get_resource("push")

    e.push_state()

    assert e.get_resource("nopush")
    assert not e.get_resource("push")

    e.save_resource("pushed", True, pushable=True)
    assert e.get_resource("pushed")

    e.pop_state()

    assert e.get_resource("nopush")
    assert e.get_resource("push")
    assert not e.get_resource("pushed")


def test_forappversions():
    """Test that app version information is passed to the JSON."""

    app_test_data = {"guid": ["version1", "version2"]}

    e = ErrorBundle()
    e.supported_versions = {"guid": ["version1"]}
    e.error(err_id=("foo", ), error="Test", for_appversions=app_test_data)
    # This one should not apply.
    e.error(err_id=("foo", ), error="Test",
            for_appversions={"fooguid": ["bar", "baz"]})

    e.warning(err_id=("foo", ), warning="Test", for_appversions=app_test_data)

    # Give one its data from the decorator
    e.version_requirements = app_test_data
    e.notice(err_id=("foo", ), notice="Test")

    j = e.render_json()
    jdata = json.loads(j)
    assert len(jdata["messages"]) == 3
    for m in jdata["messages"]:
        assert m["for_appversions"] == app_test_data

