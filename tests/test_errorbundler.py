import json
import sys
from StringIO import StringIO

import validator.errorbundler as errorbundler
from validator.errorbundler import ErrorBundle

def test_json():
    "Tests the JSON output capability of the error bundler."
    
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
    "Tests that boring output strips out color sequences."
    
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
    """Tests that detected type is being stored properly in the error
    bundle."""
    
    bundle = ErrorBundle()
    
    bundle.set_type(5)
    assert bundle.detected_type == 5

def test_states():
    """Tests that detected type is preserved, even in subpackages."""
    
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
    
    bundle.pop_state()
    
    bundle.pop_state()
    
    # Load the JSON output as an object.
    output = json.loads(bundle.render_json())
    
    # Run some basic tests
    assert output["detected_type"] == "langpack"
    assert len(output["messages"]) == 9
    
    print output
    
    messages = ["error",
                "warning",
                "notice",
                "nested error",
                "nested warning",
                "nested notice",
                "super nested error",
                "super nested warning",
                "super nested notice"]
    
    for message in output["messages"]:
        print message
        
        assert message["message"] in messages
        messages.remove(message["message"])
        
        assert message["message"].endswith(message["type"])
    
    assert not messages
    
    assert bundle.get_resource("test")


def test_file_structure():
    """Tests the means by which file names and line numbers are stored
    in errors, warnings, and messages."""
    
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
    """Tests notice-related functions of the error bundler."""
    
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


def test_notice_friendly():
    """Tests notice-related human-friendly text output functions of the
    error bundler."""
    
    # Use the StringIO as an output buffer.
    bundle = ErrorBundle()
    
    bundle.notice((), "foobar")
    
    # Load the JSON output as an object.
    output = bundle.print_summary(verbose=True, no_color=True)
    print output
    
    assert output.count("foobar")

def test_initializer():
    "Tests that the __init__ paramaters are doing their jobs"

    e = ErrorBundle()
    assert e.determined
    assert e.get_resource("listed")

    e = ErrorBundle(determined=False)
    assert not e.determined
    assert e.get_resource("listed")

    e = ErrorBundle(listed=False)
    assert e.determined
    assert not e.get_resource("listed")

