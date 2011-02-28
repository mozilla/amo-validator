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

