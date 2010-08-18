
import json
from StringIO import StringIO

import validator.errorbundler as errorbundler
from validator.errorbundler import ErrorBundle

#{"messages": [{"message": "Invalid chrome.manifest object/predicate.", "type": "error", "description": "'override' entry does not match chrome://*/locale/*"}], "detected_type": 4, "success": false}

def test_json():
    "Tests the JSON output capability of the error bundler."
    
    outbuffer = StringIO()
    
    # Use the StringIO as an output buffer.
    bundle = ErrorBundle(outbuffer, True) # No color since no output
    bundle.set_type(4)
    
    bundle.error((), "error", "description")
    bundle.warning((), "warning", "description")
    bundle.info((), "info", "description")
    
    bundle.print_json()
    
    outbuffer.seek(0)
    
    results = json.load(outbuffer)
    
    print results
    
    assert len(results["messages"]) == 3
    assert results["detected_type"] == 'langpack'
    assert not results["success"]
    
def test_boring():
    "Tests that boring output strips out color sequences."
    
    outbuffer = StringIO()
    
    # Use the StringIO as an output buffer.
    bundle = ErrorBundle(outbuffer, True) # No color since no output
    bundle.error((), "<<BLUE>><<GREEN>><<YELLOW>>")
    bundle.print_summary()
    
    outbuffer.seek(0)
    
    assert outbuffer.getvalue().count("<<GREEN>>") == 0

def test_type():
    """Tests that detected type is being stored properly in the error
    bundle."""
    
    bundle = ErrorBundle(None, True)
    
    bundle.set_type(5)
    assert bundle.detected_type == 5

def test_states():
    """Tests that detected type is preserved, even in subpackages."""
    
    outbuffer = StringIO()
    
    # Use the StringIO as an output buffer.
    bundle = ErrorBundle(outbuffer, True) # No color since no output
    
    # Populate the bundle with some test data.
    bundle.set_type(4)
    bundle.error((), "error")
    bundle.warning((), "warning")
    bundle.info((), "info")
    bundle.save_resource("test", True)
    
    # Push a state
    bundle.push_state("test.xpi")
    
    bundle.set_type(2)
    bundle.error((), "nested error")
    bundle.warning((), "nested warning")
    bundle.info((), "nested info")
    
    # Push another state
    bundle.push_state("test2.xpi")
    
    bundle.set_type(3)
    bundle.error((), "super nested error")
    bundle.warning((), "super nested warning")
    bundle.info((), "super nested info")
    
    bundle.pop_state()
    
    bundle.pop_state()
    
    # Load the JSON output as an object.
    bundle.print_json()
    output = json.loads(outbuffer.getvalue())
    
    # Run some basic tests
    assert output["detected_type"] == "langpack"
    assert len(output["messages"]) == 9
    
    print output
    
    messages = ["error",
                "warning",
                "info",
                "nested error",
                "nested warning",
                "nested info",
                "super nested error",
                "super nested warning",
                "super nested info"]
    
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
    
    outbuffer = StringIO()
    outbuffer2 = StringIO()
    
    # Use the StringIO as an output buffer.
    bundle = ErrorBundle(outbuffer, True) # No color since no output
    
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
    bundle.print_json()
    output = json.loads(outbuffer.getvalue())
    
    # Do the same for friendly output
    bundle.handler.pipe = outbuffer2
    bundle.print_summary(False)
    output2 = outbuffer2.getvalue()
    outbuffer2.seek(0)
    
    # Do the same for verbose friendly output
    bundle.print_summary(True)
    output3 = outbuffer2.getvalue()
    
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


def test_info():
    """Tests notice-related functions of the error bundler."""
    
    outbuffer = StringIO()
    
    # Use the StringIO as an output buffer.
    bundle = ErrorBundle(outbuffer, True) # No color since no output
    
    bundle.info((), "info")
    
    # Load the JSON output as an object.
    bundle.print_json()
    output = json.loads(outbuffer.getvalue())
    
    # Run some basic tests
    assert len(output["messages"]) == 1
    
    print output
    
    has_info = False
    
    for message in output["messages"]:
        print message
        
        if message["type"] == "info":
            has_info = True
    
    assert has_info
    assert not bundle.failed()


def test_info_friendly():
    """Tests notice-related human-friendly text output functions of the
    error bundler."""
    
    outbuffer = StringIO()
    
    # Use the StringIO as an output buffer.
    bundle = ErrorBundle(outbuffer, True) # No color since no output
    
    bundle.info((), "foobar")
    
    # Load the JSON output as an object.
    bundle.print_summary(True)
    output = outbuffer.getvalue()
    
    print output
    
    assert output.count("foobar")

