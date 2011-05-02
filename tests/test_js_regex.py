from js_helper import _do_test_raw

def test_valid():
    "Tests a valid string in a JS bit"

    assert not _do_test_raw("var x = 'network.foo';").failed()

def test_basic_regex_fail():
    "Tests that a simple Regex match causes a warning"

    assert _do_test_raw("var x = 'network.http';").failed()

def test_js_category_regex_fail():
    "Tests that JS category registration causes a warning"

    assert _do_test_raw("addCategory('JavaScript global property')").failed()
    assert _do_test_raw("addCategory('JavaScript-global-property')").failed()

def test_dom_mutation_fail():
    """Test that DOM mutation events raise a warning."""

    assert not _do_test_raw("foo.DOMAttr = bar;").failed()
    assert _do_test_raw("foo.DOMAttrModified = bar;").failed()

def test_bug_548645():
    "Tests that banned entities are disallowed"

    results =  _do_test_raw("""
    var y = newThread;
    var x = foo.newThread;
    var w = foo["newThread"];
    """)
    print results.message_count
    assert results.message_count == 3

def test_bug_652575():
    """Ensure that capability.policy gets flagged."""
    assert _do_test_raw("var x = 'capability.policy';").failed()

