from validator.constants import PACKAGE_THEME
from validator.contextgenerator import ContextGenerator
from validator.testcases.javascript import traverser
from validator.testcases.javascript.jsshell import get_tree


def test_js_file(err, filename, data, line=0, context=None, pollutable=False):
    'Test a JS file by parsing and analyzing its tokens.'

    if err.detected_type == PACKAGE_THEME:
        err.warning(
                err_id=('testcases_scripting',
                        'test_js_file',
                        'theme_js'),
                warning='JS run from full theme',
                description='Themes should not contain executable code.',
                filename=filename,
                line=line)

    before_tier = None
    # Set the tier to 4 (Security Tests)
    if err is not None:
        before_tier = err.tier
        err.set_tier(3)

    tree = get_tree(data, filename=filename, err=err)
    if not tree:
        if before_tier:
            err.set_tier(before_tier)
        return

    # Generate a context if one is not available.
    if context is None:
        context = ContextGenerator(data)

    t = traverser.Traverser(err, filename, line, context=context,
                            is_jsm=(filename.endswith('.jsm') or
                                    'EXPORTED_SYMBOLS' in data))
    t.pollutable = pollutable
    t.run(tree)

    # Reset the tier so we don't break the world
    if err is not None:
        err.set_tier(before_tier)


def test_js_snippet(err, data, filename, line=0, context=None):
    'Process a JS snippet by passing it through to the file tester.'

    if not data:
        return

    # Wrap snippets in a function to prevent the parser from freaking out
    # when return statements exist without a corresponding function.
    data = '(function(){%s\n})()' % data

    test_js_file(err, filename, data, line, context, pollutable=False)
