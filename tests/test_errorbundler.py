
import json
from StringIO import StringIO

import errorbundler
from errorbundler import ErrorBundle

#{"messages": [{"message": "Invalid chrome.manifest object/predicate.", "type": "error", "description": "'override' entry does not match chrome://*/locale/*"}], "detected_type": 4, "success": false}

def test_json():
    "Tests the JSON output capability of the error bundler."
    
    outbuffer = StringIO()
    
    # Use the StringIO as an output buffer.
    bundle = ErrorBundle(outbuffer, True) # No color since no output
    bundle.set_type(4)
    
    bundle.error("error", "description")
    bundle.warning("warning", "description")
    bundle.info("info", "description")
    
    bundle.print_json()
    
    outbuffer.seek(0)
    
    results = json.load(outbuffer)
    
    assert len(results["messages"]) == 3
    assert results["detected_type"] == 4
    assert not results["success"]
    
def test_boring():
    "Tests that boring output strips out color sequences."
    
    outbuffer = StringIO()
    
    # Use the StringIO as an output buffer.
    bundle = ErrorBundle(outbuffer, True) # No color since no output
    bundle.error("<<BLUE>><<GREEN>><<YELLOW>>")
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
    bundle.error("error")
    bundle.warning("warning")
    bundle.info("info")
    bundle.save_resource("test", True)
    
    # Push a state
    bundle.push_state("test.xpi")
    
    bundle.set_type(2)
    bundle.error("nested error")
    bundle.warning("nested warning")
    bundle.info("nested info")
    
    # Push another state
    bundle.push_state("test2.xpi")
    
    bundle.set_type(3)
    bundle.error("super nested error")
    bundle.warning("super nested warning")
    bundle.info("super nested info")
    
    bundle.pop_state()
    
    bundle.pop_state()
    
    # Load the JSON output as an object.
    bundle.print_json()
    output = json.loads(outbuffer.getvalue())
    
    # Run some basic tests
    assert output["detected_type"] == 4
    assert len(output["messages"]) == 9
    
    print output
    
    messages = ["error",
                "warning",
                "info",
                "test.xpi > nested error",
                "test.xpi > nested warning",
                "test.xpi > nested info",
                "test.xpi > test2.xpi > super nested error",
                "test.xpi > test2.xpi > super nested warning",
                "test.xpi > test2.xpi > super nested info"]
    
    for message in output["messages"]:
        print message
        
        assert message["message"] in messages
        messages.remove(message["message"])
        
        assert message["message"].endswith(message["type"])
    
    assert not messages
    
    assert bundle.get_resource("test")
