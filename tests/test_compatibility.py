from nose.tools import eq_

import validator.constants
from validator.decorator import version_range
from validator.testcases.markup.markuptester import MarkupParser
import validator.testcases.scripting as scripting
from validator.decorator import version_range
from js_helper import _do_real_test_raw
from validator.errorbundler import ErrorBundle


# TODO: During a refactor, move this to the decorator's tests.
def test_version_range():
    """
    Tests that the appropriate versions after the specified versions are
    returned.
    """

    new_versions = {"1": {"guid": "foo",
                          "versions": map(str, range(10))}}
    eq_(version_range("foo", "8", app_versions=new_versions), ["8", "9"])
    eq_(version_range("foo", "5", app_versions=new_versions),
            ["5", "6", "7", "8", "9"])


def test_version_range_before():
    """Test the `before` parameter of version_range."""

    new_versions = {"1": {"guid": "foo",
                          "versions": map(str, range(10))}}

    eq_(version_range("foo", "5", "6", app_versions=new_versions), ["5"])
    eq_(version_range("foo", "8", "50", app_versions=new_versions), ["8", "9"])


def test_navigator_language():
    """
    Test that 'navigator.language' is flagged as potentially
    incompatible with FX5.
    """

    err = _do_real_test_raw("""
    alert(navigator.language);
    """)
    assert not err.failed()
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw("""
    alert(navigator.language);
    """, versions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                    version_range("firefox", "5.0")})
    assert not err.failed()
    assert err.compat_summary["errors"]


def test_menu_item_compat():
    """
    Test that compatibility warnings are raised for the stuff from bug 660349.
    """

    def _run_test(data, name="foo.xul", should_fail=False):
        def test(versions):
            err = ErrorBundle()
            err.supported_versions = versions
            parser = MarkupParser(err)
            parser.process(name,
                           data,
                           name.split(".")[-1])
            print err.print_summary(verbose=True)
            assert not err.failed()
            return err

        err = test({"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                        version_range("firefox", "6.0a1")})
        if should_fail:
            assert err.notices
            assert err.compat_summary["warnings"]
        else:
            assert not err.notices

        assert not test({}).notices

    # Test that the testcase doesn't apply to non-XUL files.
    err = _run_test("""
    <foo>
        <bar insertbefore="webConsole" />
    </foo>
    """, name="foo.xml")

    # Test that a legitimate testcase will fail.
    err = _run_test("""
    <foo>
        <bar insertbefore="what,webConsole,evar" />
    </foo>
    """, should_fail=True)

    # Test that the testcase only applies to the proper attribute values.
    err = _run_test("""
    <foo>
        <bar insertbefore="something else" />
    </foo>
    """)


def test_window_top():
    """
    Test that 'window.top' (a reserved global variable as of Firefox 6) is
    flagged as incompatible.
    """

    err = _do_real_test_raw("""
    window.top = "foo";
    top = "bar";
    """)
    print err.print_summary(verbose=True)
    assert not err.failed()
    assert not err.notices

    err = _do_real_test_raw("""
    window.top = "foo";
    """, versions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                       version_range("firefox", "6.0a1")})
    print err.print_summary(verbose=True)
    assert not err.failed()
    assert err.notices
    assert err.compat_summary["warnings"]

    err = _do_real_test_raw("""
    top = "foo";
    """, versions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                       version_range("firefox", "6.0a1")})
    print err.print_summary(verbose=True)
    assert not err.failed()
    assert err.notices
    assert err.compat_summary["warnings"]


def test_custom_addon_types():
    """
    Test that registering custom add-on types is flagged as being incompatible
    with Firefox 6.
    """

    err = _do_real_test_raw("""
    AddonManagerPrivate.registerProvider();
    """)
    print err.print_summary(verbose=True)
    assert not err.failed()
    assert not err.notices

    err = _do_real_test_raw("""
    AddonManagerPrivate.registerProvider();
    """, versions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                       version_range("firefox", "6.0a1")})
    print err.print_summary(verbose=True)
    assert not err.failed()
    assert err.notices
    assert err.compat_summary["errors"]


def test_fx7_regex_xpcom():
    """
    Test that the obsoleted "simple" XPCOM interfaces are flagged from FX7.
    """

    err = _do_real_test_raw("""
    var x = "nsIDOMDocumentStyle";
    """)
    assert not err.failed()
    assert not err.notices
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw("""
    var x = "nsIDOMDocumentStyle";
    """, versions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                       version_range("firefox", "7.0a1")})
    assert not err.failed()
    assert err.notices
    assert err.compat_summary["errors"]


def test_fx7_nsinavhistoryobserver():
    """Test that nsINavHistoryObserver is flagged."""

    err = _do_real_test_raw("""
    var x = "nsINavHistoryObserver";
    """)
    assert not err.failed()
    assert not err.notices
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw("""
    var x = "nsINavHistoryObserver";
    """, versions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                       version_range("firefox", "7.0a1")})
    assert not err.failed()
    assert err.notices
    assert err.compat_summary["errors"]


def test_fx7_markupdocumentviewer():
    """Test that nsIMarkupDocumentViewer_MOZILLA_2_0_BRANCH is flagged."""

    err = _do_real_test_raw("""
    var x = "nsIMarkupDocumentViewer_MOZILLA_2_0_BRANCH";
    """)
    assert not err.failed()
    assert not err.notices
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw("""
    var x = "nsIMarkupDocumentViewer_MOZILLA_2_0_BRANCH";
    """, versions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                       version_range("firefox", "7.0a1")})
    assert not err.failed()
    assert err.notices
    assert err.compat_summary["warnings"]


def test_fx7_nsIDOMFile():
    """Test that nsIDOMFile methods are flagged."""

    err = _do_real_test_raw("""
    var x = Components.classes.createInstance(
        Components.interfaces.nsIDOMFile);
    x.getAsBinary();
    """)
    assert not err.failed(fail_on_warnings=False)
    assert not err.notices
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw("""
    var x = Components.classes["foo"].createInstance(
        Components.interfaces.nsIDOMFile);
    x.getAsDataURL();
    """, versions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                       version_range("firefox", "7.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert len(err.notices) == 1
    assert err.compat_summary["errors"]

    err = _do_real_test_raw("""
    var x = document.getElementById("whatever");
    x.getAsDataURL();
    """, versions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                       version_range("firefox", "7.0a1")})
    assert not err.failed()
    assert len(err.notices) == 1
    assert err.compat_summary["errors"]


def test_fx7_nsIJSON():
    """Test that nsIJSON methods are flagged."""

    err = _do_real_test_raw("""
    var x = Components.classes["foo"].createInstance(
        Components.interfaces.nsIJSON);
    x.encode();
    """)
    assert not err.failed(fail_on_warnings=False)
    assert not err.notices
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw("""
    var x = Components.classes["foo"].createInstance(
        Components.interfaces.nsIJSON);
    x.encode();
    """, versions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                       version_range("firefox", "7.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert len(err.notices) == 1
    assert err.compat_summary["warnings"]


def test_fx8_compat():
    """Test that FX8 compatibility tests are run."""

    err = _do_real_test_raw("""
    var x = "nsISelection2";
    """)
    assert not err.failed()
    assert not err.notices

    err = _do_real_test_raw("""
    var x = "nsISelection2";
    """, versions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                       version_range("firefox", "8.0a1")})
    assert not err.failed()
    assert err.notices
    assert err.compat_summary["errors"]

    err = _do_real_test_raw("""
    var x = "nsIDOMWindowInternal";
    """)
    assert not err.failed()
    assert not err.notices

    err = _do_real_test_raw("""
    var x = "nsIDOMWindowInternal";
    """, versions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                       version_range("firefox", "8.0a1")})
    assert not err.failed()
    assert err.notices
    assert err.compat_summary["warnings"]

    err = _do_real_test_raw("""
    var x = "ISO8601DateUtils";
    """)
    assert not err.failed()
    assert not err.notices

    err = _do_real_test_raw("""
    var x = "ISO8601DateUtils";
    """, versions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                       version_range("firefox", "8.0a1")})
    assert not err.failed()
    assert err.notices
    assert err.compat_summary["errors"]


def futureCompatWarning(code, version):
    err = _do_real_test_raw(code)
    assert not err.failed()
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw(
        code,
        versions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                      version_range("firefox", version)})
    assert not err.failed()
    assert err.compat_summary["warnings"]


def futureCompatError(code, version):
    err = _do_real_test_raw(code)
    assert not err.failed(fail_on_warnings=False)
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw(
        code,
        versions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                      version_range("firefox", version)})
    assert err.failed(fail_on_warnings=False)
    assert err.compat_summary["errors"]


def test_fx9_navigator_taintEnabled():
    """
    'navigator.taintEnabled' is flagged as incompatible with FX9.
    """
    futureCompatWarning('alert(navigator.taintEnabled);', '9.0a1')


def test_fx9_691569():
    """
    baseURIObject, nodePrincipal, documentURIObject are flagged as
    unavailable in non-chrome contexts in FX9.
    """
    futureCompatWarning('alert(document.documentURIObject);', '9.0a1')
    futureCompatWarning('alert(document.nodePrincipal);', '9.0a1')
    futureCompatWarning('alert(document.baseURIObject);', '9.0a1')


def test_fx9_nsIGlobalHistory3():
    """
    nsIGlobalHistory3 is flagged as incompatible in Firefox 9.
    """
    futureCompatWarning(
        'var x = "nsIGlobalHistory3";',
        '9.0a1')


def test_fx9_nsIURLParser_parsePath():
    """
    nsIURLParser.parsePath takes 8 args instead of 10 now.
    """
    futureCompatError(
        """
        var URLi = Components.classes["@mozilla.org/network/url-parser;1?auth=maybe"].
                       createInstance(Components.interfaces.nsIURLParser);
        var filepathPos = {}, filepathLen = {}, paramPos = {}, paramLen = {},
            queryPos = {}, queryLen = {}, refPos = {}, refLen = {};
        URLi.parsePath(urlObj.path, -1, filepathPos, filepathLen, paramPos,
                       paramLen, queryPos, queryLen, refPos, refLen);
        """,
        '9.0a1')

    err = _do_real_test_raw(
        """
        var URLi = Components.classes["@mozilla.org/network/url-parser;1?auth=maybe"].
                       createInstance(Components.interfaces.nsIURLParser);
        var filepathPos = {}, filepathLen = {}, queryPos = {}, queryLen = {},
            refPos = {}, refLen = {};
        URLi.parsePath(urlObj.path, -1, filepathPos, filepathLen, queryPos,
                       queryLen, refPos, refLen);
        """,
        versions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                      version_range("firefox", "9.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert not err.compat_summary["errors"]


def test_fx9_nsIURL_param():
    """
    nsIURL.param no longer exists in Firefox 9.
    """
    futureCompatError(
        """
        var myURI = {};
        var myURL = myURI.QueryInterface(Components.interfaces.nsIURL);
        alert(myURL.param);
        """,
        '9.0a1')


def test_fx9_nsIBrowserHistory_removePages():
    """
    nsIBrowserHistory.removePages() takes 2 arguments instead of 3 in
    Firefox 9.
    """
    futureCompatError(
        """
        var browserHistory = Components.classes[
                                 "@mozilla.org/browser/global-history;2"]
                             .getService(
                                 Components.interfaces.nsIBrowserHistory);
        browserHistory.removePages(uriList, uriList.length, false);
        """,
        '9.0a1')

    err = _do_real_test_raw(
        """
        var browserHistory = Components.classes[
                                 "@mozilla.org/browser/global-history;2"]
                             .getService(
                                 Components.interfaces.nsIBrowserHistory);
        browserHistory.removePages(uriList, uriList.length);
        """,
        versions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                      version_range("firefox", "9.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert not err.compat_summary["errors"]


def test_fx9_nsIBrowserHistory_register():
    """
    nsIBrowserHistory.registerOpenPage() and
    nsIBrowserHistory.unregisterOpenPage() no longer exist in
    Firefox 9.
    """
    futureCompatError(
        """
        var browserHistory = Components.classes[
                                 "@mozilla.org/browser/global-history;2"]
                             .getService(
                                 Components.interfaces.nsIBrowserHistory);
        alert(browserHistory.registerOpenPage);
        """,
        '9.0a1')
    futureCompatError(
        """
        var browserHistory = Components.classes[
                                 "@mozilla.org/browser/global-history;2"]
                             .getService(
                                 Components.interfaces.nsIBrowserHistory);
        alert(browserHistory.unregisterOpenPage);
        """,
        '9.0a1')


def test_fx9_nsIEditor_saveDefaultDictionary():
    """
    nsIEditorSpellCheck.saveDefaultDictionary is gone in Firefox 9.
    """
    futureCompatError(
        """
        var spellChecker = Components.classes[
                               '@mozilla.org/editor/editorspellchecker;1']
                           .createInstance(
                               Components.interfaces.nsIEditorSpellCheck);
        alert(spellChecker.saveDefaultDictionary);
        """,
        '9.0a1')


def test_fx9_nsIEditor_updateDefaultDictionary():
    """
    nsIEditorSpellCheck.UpdateDefaultDictionary takes no arguments in
    Firefox 9.
    """
    futureCompatError(
        """
        var spellChecker = Components.classes[
                               '@mozilla.org/editor/editorspellchecker;1']
                           .createInstance(
                               Components.interfaces.nsIEditorSpellCheck);
        spellChecker.UpdateCurrentDictionary(null);
        """,
        '9.0a1')

    err = _do_real_test_raw(
        """
        var spellChecker = Components.classes[
                               '@mozilla.org/editor/editorspellchecker;1']
                           .createInstance(
                               Components.interfaces.nsIEditorSpellCheck);
        spellChecker.UpdateCurrentDictionary();
        """,
        versions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                      version_range("firefox", "9.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert not err.compat_summary["errors"]


def test_fx9_geo_prefs():
    """
    The 'geo.wifi.uri' and 'geo.wifi.protocol' prefs aren't set in
    Firefox 9; referring to them produces a compatibility error.
    """
    futureCompatError("""
    var Application = Components.classes["@mozilla.org/fuel/application;1"]
                      .getService(Components.interfaces.fuelIApplication);
    this._uri = Application.prefs.get('geo.wifi.uri');
    """,
    '9.0a1')
    futureCompatError("""
    var Application = Components.classes["@mozilla.org/fuel/application;1"]
                      .getService(Components.interfaces.fuelIApplication);
    this._protocol = Application.prefs.get('geo.wifi.protocol');
    """,
    '9.0a1')


def test_tb6_nsIImapMailFolderSink():
    """Test that nsIImapMailFolderSink.setUrlState is flagged."""

    err = _do_real_test_raw("""
    var x = Components.classes["foo"].createInstance(
        Components.interfaces.nsIImapMailFolderSink);
    x.setUrlState();
    """)
    assert not err.failed(fail_on_warnings=False)
    assert not err.notices
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw("""
    var x = Components.classes["foo"].createInstance(
        Components.interfaces.nsIImapMailFolderSink);
    x.setUrlState();
    """, versions={'{3550f703-e582-4d05-9a08-453d09bdfdc6}':
                       version_range("thunderbird", "6.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert len(err.notices) == 1
    assert err.compat_summary["errors"]


def test_tb6_nsIImapProtocol():
    """Test that nsIImapProtocol.NotifyHdrsToDownload is flagged."""

    err = _do_real_test_raw("""
    var x = Components.classes["foo"].createInstance(
        Components.interfaces.nsIImapProtocol);
    x.NotifyHdrsToDownload();
    """)
    assert not err.failed(fail_on_warnings=False)
    assert not err.notices
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw("""
    var x = Components.classes["foo"].createInstance(
        Components.interfaces.nsIImapProtocol);
    x.NotifyHdrsToDownload();
    """, versions={'{3550f703-e582-4d05-9a08-453d09bdfdc6}':
                       version_range("thunderbird", "6.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert len(err.notices) == 1
    assert err.compat_summary["errors"]


def test_flag_getSelection():
    """Test that document.getSelection is flagged in FX8."""

    err = _do_real_test_raw("""
    var x = document.getSelection();
    """)
    assert not err.failed()
    assert not err.notices
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw("""
    var x = document.getSelection();
    """, versions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                       version_range("firefox", "8.0a1", "9.0a1")})
    assert not err.failed()
    assert len(err.notices) == 1
    assert err.compat_summary["errors"]


def test_tb7_nsIMsgThread():
    """Test that nsIMsgThread.GetChildAt is flagged."""

    err = _do_real_test_raw("""
    var x = Components.classes["foo"].createInstance(
        Components.interfaces.nsIMsgThread);
    x.GetChildAt();
    """)
    assert not err.failed(fail_on_warnings=False)
    assert not err.notices
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw("""
    var x = Components.classes["foo"].createInstance(
        Components.interfaces.nsIMsgThread);
    x.GetChildAt();
    """, versions={'{3550f703-e582-4d05-9a08-453d09bdfdc6}':
                       version_range("thunderbird", "7.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert len(err.notices) == 1
    assert err.compat_summary["errors"]


def test_tb7_mail_attachment_api():
    """Test that the old mail attachment global functions are flagged."""

    err = _do_real_test_raw("""
    createNewAttachmentInfo();
    saveAttachment();
    attachmentIsEmpty();
    openAttachment();
    detachAttachment();
    cloneAttachment();
    """)
    assert not err.failed()
    assert not err.notices
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw("""
    createNewAttachmentInfo();
    saveAttachment();
    attachmentIsEmpty();
    openAttachment();
    detachAttachment();
    cloneAttachment();
    """, versions={'{3550f703-e582-4d05-9a08-453d09bdfdc6}':
                       version_range("thunderbird", "7.0a1")})
    assert not err.failed()
    assert len(err.notices) == 6
    assert err.compat_summary["errors"]


def test_tb7_dictUtils_removal():
    """Test that dictUtils.js imports are flagged"""

    err = _do_real_test_raw("""
    var x = 'Components.utils.import("resource:///modules/dictUtils.js");';
    """)
    assert not err.failed()
    assert not err.notices

    err = _do_real_test_raw("""
    var x = 'Components.utils.import("resource:///modules/dictUtils.js");';
    """, versions={'{3550f703-e582-4d05-9a08-453d09bdfdc6}':
                       version_range("thunderbird", "7.0a1")})
    assert not err.failed()
    assert err.notices
    assert err.compat_summary["errors"]

def test_tb7_deRDF_addressbook():
    """Test that addressbook rdf sources are flagged"""

    err = _do_real_test_raw("""
    var x = 'datasources="rdf:addressdirectory" ref="moz-abdirectory://"';
    """)
    assert not err.failed()
    assert not err.notices

    err = _do_real_test_raw("""
    var x = 'datasources="rdf:addressdirectory" ref="moz-abdirectory://"';
    """, versions={'{3550f703-e582-4d05-9a08-453d09bdfdc6}':
                       version_range("thunderbird", "7.0a1")})
    assert not err.failed()
    assert err.notices
    assert err.compat_summary["errors"]

    err = _do_real_test_raw("""
    var x = 'GetResource(SomeText)    .  QueryInterface(6inTestxnsIAbDirectory);';
    """)
    assert not err.failed()
    assert not err.notices

    err = _do_real_test_raw("""
    var x = "GetResource(SomeText)  .  QueryInterface(Some8678StuffnsIAbDirectory)";
    """, versions={'{3550f703-e582-4d05-9a08-453d09bdfdc6}':
                       version_range("thunderbird", "7.0a1")})
    assert not err.failed()
    assert err.notices
    assert err.compat_summary["errors"]


def test_tb8_nsIMsgSearchScopeTerm():
    """Test that nsIMsgSearchScopeTerm.mailFile & inputStream are flagged."""

    err = _do_real_test_raw("""
    var x = Components.classes["foo"].createInstance(
        Components.interfaces.nsIMsgSearchScopeTerm);
    x.mailFile();
    x.inputStream();
    """)
    assert not err.failed(fail_on_warnings=False)
    assert not err.notices
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw("""
    var x = Components.classes["foo"].createInstance(
        Components.interfaces.nsIMsgSearchScopeTerm);
    x.mailFile();
    x.inputStream();
    """, versions={'{3550f703-e582-4d05-9a08-453d09bdfdc6}':
                       version_range("thunderbird", "8.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert len(err.notices) == 2
    assert err.compat_summary["errors"]


def test_tb9_compatibility():
    """Test that gComposeBundle, FocusOnFirstAttachment, WhichPaneHasFocus are flagged."""

    err = _do_real_test_raw("""
    var x = "";
    x = gComposeBundle();
    FocusOnFirstAttachment();
    WhichPaneHasFocus();
    """)
    assert not err.failed(fail_on_warnings=False)
    assert not err.notices
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw("""
    var x = "";
    x = gComposeBundle();
    FocusOnFirstAttachment();
    WhichPaneHasFocus();
    """, versions={'{3550f703-e582-4d05-9a08-453d09bdfdc6}':
                       version_range("thunderbird", "9.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert len(err.notices) == 3
    assert err.compat_summary["errors"]


def test_isSameNode():
    """Test that isSameNode is dead in FX10."""
    futureCompatError("alert(x.isSameNode(foo));", "10.0")


def test_isElementContentWhitespace():
    """Test that isElementContentWhitespace is dead in FX10."""
    futureCompatError("alert(x.isElementContentWhitespace);", "10.0")

