
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
