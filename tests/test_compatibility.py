from nose.tools import eq_

import validator.constants
from validator.constants import FIREFOX_GUID, THUNDERBIRD_GUID as TB_GUID
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
    """, versions={FIREFOX_GUID: version_range("firefox", "5.0")})
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

        err = test({FIREFOX_GUID: version_range("firefox", "6.0a1")})
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
    """, versions={FIREFOX_GUID: version_range("firefox", "6.0a1")})
    print err.print_summary(verbose=True)
    assert not err.failed()
    assert err.notices
    assert err.compat_summary["warnings"]

    err = _do_real_test_raw("""
    top = "foo";
    """, versions={FIREFOX_GUID: version_range("firefox", "6.0a1")})
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
    """, versions={FIREFOX_GUID: version_range("firefox", "6.0a1")})
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
    """, versions={FIREFOX_GUID: version_range("firefox", "7.0a1")})
    assert err.failed()
    assert len(err.warnings) == 1
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
    """, versions={FIREFOX_GUID: version_range("firefox", "7.0a1")})
    assert not err.failed()
    assert err.notices
    assert err.compat_summary["errors"]


def test_fx7_markupdocumentviewer():
    """Test that nsIMarkupDocumentViewer_MOZILLA_2_0_BRANCH is flagged."""

    err = _do_real_test_raw("""
    var x = "nsIMarkupDocumentViewer_MOZILLA_2_0_BRANCH";
    """)
    assert not err.failed()
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw("""
    var x = "nsIMarkupDocumentViewer_MOZILLA_2_0_BRANCH";
    """, versions={FIREFOX_GUID: version_range("firefox", "7.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert err.warnings
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
    """, versions={FIREFOX_GUID: version_range("firefox", "7.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert len(err.notices) == 1
    assert err.compat_summary["errors"]

    err = _do_real_test_raw("""
    var x = document.getElementById("whatever");
    x.getAsDataURL();
    """, versions={FIREFOX_GUID: version_range("firefox", "7.0a1")})
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
    """, versions={FIREFOX_GUID: version_range("firefox", "7.0a1")})
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
    """, versions={FIREFOX_GUID: version_range("firefox", "8.0a1")})
    assert err.failed()
    assert err.warnings
    assert err.compat_summary["errors"]

    err = _do_real_test_raw("""
    var x = "nsIDOMWindowInternal";
    """)
    assert not err.failed()
    assert not err.notices

    err = _do_real_test_raw("""
    var x = "nsIDOMWindowInternal";
    """, versions={FIREFOX_GUID: version_range("firefox", "8.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert err.warnings
    assert err.compat_summary["warnings"]

    err = _do_real_test_raw("""
    var x = "ISO8601DateUtils";
    """)
    assert not err.failed()
    assert not err.notices

    err = _do_real_test_raw("""
    var x = "ISO8601DateUtils";
    """, versions={FIREFOX_GUID: version_range("firefox", "8.0a1")})
    assert err.failed()
    assert err.compat_summary["errors"]


def futureCompatWarning(code, version, fails=True):
    err = _do_real_test_raw(code)
    assert not err.failed()
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw(
        code,
        versions={FIREFOX_GUID: version_range("firefox", version)})
    if fails:
        assert err.failed()
    else:
        assert not err.failed()
        assert err.notices
    assert err.compat_summary["warnings"]


def futureCompatError(code, version):
    err = _do_real_test_raw(code)
    assert not err.failed()
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw(
        code,
        versions={FIREFOX_GUID: version_range("firefox", version)})
    print err.print_summary()
    assert err.failed()
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
    futureCompatWarning('alert(document.documentURIObject);', '9.0a1',
                        fails=False)
    futureCompatWarning('alert(document.nodePrincipal);', '9.0a1',
                        fails=False)
    futureCompatWarning('alert(document.baseURIObject);', '9.0a1',
                        fails=False)


def test_fx9_nsIGlobalHistory3():
    """
    nsIGlobalHistory3 is flagged as incompatible in Firefox 9.
    """
    futureCompatWarning('var x = "nsIGlobalHistory3";', "9.0a1")


def test_fx9_nsIURLParser_parsePath():
    """
    nsIURLParser.parsePath takes 8 args instead of 10 now.
    """
    futureCompatError(
        """
        var URLi = Components.classes[
                        "@mozilla.org/network/url-parser;1?auth=maybe"].
                       createInstance(Components.interfaces.nsIURLParser);
        var filepathPos = {}, filepathLen = {}, paramPos = {}, paramLen = {},
            queryPos = {}, queryLen = {}, refPos = {}, refLen = {};
        URLi.parsePath(urlObj.path, -1, filepathPos, filepathLen, paramPos,
                       paramLen, queryPos, queryLen, refPos, refLen);
        """,
        '9.0a1')

    err = _do_real_test_raw(
        """
        var URLi = Components.classes[
                        "@mozilla.org/network/url-parser;1?auth=maybe"].
                       createInstance(Components.interfaces.nsIURLParser);
        var filepathPos = {}, filepathLen = {}, queryPos = {}, queryLen = {},
            refPos = {}, refLen = {};
        URLi.parsePath(urlObj.path, -1, filepathPos, filepathLen, queryPos,
                       queryLen, refPos, refLen);
        """,
        versions={FIREFOX_GUID: version_range("firefox", "9.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert not err.compat_summary["errors"]


def test_fx9_nsIURL_param():
    """
    nsIURL.param no longer exists in Firefox 9.
    """
    futureCompatError("""
    var myURI = {};
    var myURL = myURI.QueryInterface(Components.interfaces.nsIURL);
    alert(myURL.param);
    """, '9.0a1')


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
        versions={FIREFOX_GUID: version_range("firefox", "9.0a1")})
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
        versions={FIREFOX_GUID: version_range("firefox", "9.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert not err.compat_summary["errors"]


def test_fx9_geo_prefs():
    """
    The 'geo.wifi.uri' and 'geo.wifi.protocol' prefs aren't set in
    Firefox 9; referring to them produces a compatibility error.
    """
    futureCompatError("""
    var app = Components.classes["@mozilla.org/fuel/application;1"]
                      .getService(Components.interfaces.fuelIApplication);
    var _uri = app.prefs.get('geo.wifi.uri');
    """, '9.0a1')
    futureCompatError("""
    var app = Components.classes["@mozilla.org/fuel/application;1"]
                      .getService(Components.interfaces.fuelIApplication);
    var _protocol = app.prefs.get('geo.wifi.protocol');
    """, '9.0a1')


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
    """, versions={TB_GUID: version_range("thunderbird", "6.0a1")})
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
    """, versions={TB_GUID: version_range("thunderbird", "6.0a1")})
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
    """, versions={FIREFOX_GUID: version_range("firefox", "8.0a1", "9.0a1")})
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
    """, versions={TB_GUID: version_range("thunderbird", "7.0a1")})
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
    """, versions={TB_GUID: version_range("thunderbird", "7.0a1")})
    assert not err.failed()
    assert len(err.notices) == 6
    assert err.compat_summary["errors"]


def test_tb7_dictUtils_removal():
    """Test that dictUtils.js imports are flagged"""

    err = _do_real_test_raw("""
    var x = 'Components.utils.import("resource:///modules/dictUtils.js");';
    """)
    assert not err.failed()
    assert not err.warnings

    err = _do_real_test_raw("""
    var x = 'Components.utils.import("resource:///modules/dictUtils.js");';
    """, versions={TB_GUID: version_range("thunderbird", "7.0a1")})
    assert err.failed()
    assert err.warnings
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
    """, versions={TB_GUID: version_range("thunderbird", "7.0a1")})
    assert not err.failed()
    assert err.notices
    assert err.compat_summary["errors"]

    err = _do_real_test_raw("""
    var x = 'GetResource(SomeText).QueryInterface(6inTestxnsIAbDirectory);';
    """)
    assert not err.failed()
    assert not err.notices

    err = _do_real_test_raw("""
    var x = "GetResource(SomeText).QueryInterface(Some8678StuffnsIAbDirectory)";
    """, versions={TB_GUID: version_range("thunderbird", "7.0a1")})
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
    """, versions={TB_GUID: version_range("thunderbird", "8.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert len(err.notices) == 2
    assert err.compat_summary["errors"]


def test_tb9_compatibility():
    """
    Test that gComposeBundle, FocusOnFirstAttachment, WhichPaneHasFocus are
    flagged.
    """

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
    """, versions={TB_GUID: version_range("thunderbird", "9.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert len(err.notices) == 3
    assert err.compat_summary["errors"]


def test_isSameNode():
    """Test that isSameNode is dead in FX10."""
    futureCompatError("alert(x.isSameNode(foo));", "10.0")


def test_replaceWholeText():
    """Test that replaceWholeText is dead in FX10."""
    futureCompatError("alert(x.replaceWholeText());", "10.0")


def test_isElementContentWhitespace():
    """Test that isElementContentWhitespace is dead in FX10."""
    futureCompatError("alert(x.isElementContentWhitespace);", "10.0")


def test_xml_document_properties():
    """
    Test that the xmlEncoding, xmlVersion, and xmlStandalone objects are dead
    for the document object in Gecko 10.
    """
    futureCompatError("alert(document.xmlEncoding);", "10.0")
    futureCompatError("alert(document.xmlVersion);", "10.0")
    futureCompatError("alert(document.xmlStandalone);", "10.0")
    # Test that the object translates properly.
    futureCompatError("alert(content.document.xmlEncoding);", "10.0")


def test_xml_properties():
    """
    Test that the xmlEncoding, xmlVersion, and xmlStandalone objects are dead
    in Gecko 10.
    """
    futureCompatError("alert(foo.xmlEncoding);", "10.0")
    futureCompatError("alert(foo.xmlVersion);", "10.0")
    futureCompatError("alert(foo.xmlStandalone);", "10.0")


def test_nsIDOMNSHTMLFrameElement():
    futureCompatError("""
        var URLi = Components.classes["foo"].
                       createInstance(Components.interfaces.nsIDOMNSHTMLFrameElement);
        """, '10.0')


def test_nsIDOMNSHTMLElement():
    futureCompatError("""
        var URLi = Components.classes["foo"].
                       createInstance(Components.interfaces.nsIDOMNSHTMLElement);
        """, '10.0')


def test_nsIBrowserHistory_lastPageVisited():
    futureCompatError("""
        var BH = Components.classes["foo"].
                       createInstance(Components.interfaces.nsIBrowserHistory);
        alert(BH.lastPageVisited);
        """, '10.0')


def test_tb10_compatibility():
    """
    Test that MsgDeleteMessageFromMessageWindow, goToggleSplitter,
    AddMessageComposeOfflineObserver, and RemoveMessageComposeOfflineObserver
    are flagged.
    """

    err = _do_real_test_raw("""
    var x = "";
    x = MsgDeleteMessageFromMessageWindow();
    goToggleSplitter();
    AddMessageComposeOfflineObserver();
    RemoveMessageComposeOfflineObserver();
    x = gDownloadManagerStrings.get();
    """)
    assert not err.failed(fail_on_warnings=False)
    assert not err.warnings
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw("""
    var x = "";
    x = MsgDeleteMessageFromMessageWindow();
    goToggleSplitter();
    AddMessageComposeOfflineObserver();
    RemoveMessageComposeOfflineObserver();
    x = gDownloadManagerStrings.get();
    """, versions={TB_GUID: version_range("thunderbird", "10.0a1")})
    assert err.failed()
    assert len(err.warnings) == 1
    assert len(err.notices) == 4
    assert err.compat_summary["errors"]


def test_fx11_compatibility():
    """Test that changes in FX11 are flagged."""

    err = _do_real_test_raw("""
    var x = "nsICharsetResolver";
    """)
    assert not err.failed()
    assert not err.warnings

    err = _do_real_test_raw("""
    var x = "nsICharsetResolver";
    """, versions={FIREFOX_GUID: version_range("firefox", "11.0a1")})
    assert err.failed()
    assert err.warnings
    assert err.compat_summary["errors"]


def test_fx11_omni_jar():
    """
    Test that in Firefox 11, omni.jar is flagged as having been renamed.
    """
    err = _do_real_test_raw("""
    var x = "omni.jar";
    """)
    assert not err.failed(fail_on_warnings=False)
    assert not err.warnings
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw("""
    var x = "omni.jar";
    """, versions={FIREFOX_GUID: version_range("firefox", "11.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert err.warnings
    assert err.compat_summary["errors"]


def test_tb11_compatibility():
    """
    Test that the changed/removed interfaces for Thunderbird 11 are flagged.
    """

    err = _do_real_test_raw("""
    var x = Components.classes["foo"].createInstance(
        Components.interfaces.nsIMsgQuote);
    x.quoteMessage();
    var y = Components.classes["foo"].createInstance(
        Components.interfaces.nsIMailtoUrl);
    y.GetMessageContents();
    """)
    assert not err.failed(fail_on_warnings=False)
    assert not err.warnings
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw("""
    var x = Components.classes["foo"].createInstance(
        Components.interfaces.nsIMsgQuote);
    x.quoteMessage();
    var y = Components.classes["foo"].createInstance(
        Components.interfaces.nsIMailtoUrl);
    y.GetMessageContents();
    """, versions={TB_GUID: version_range("thunderbird", "11.0a1")})
    assert err.failed
    assert len(err.notices) == 2
    assert err.compat_summary["errors"]


def test_tb12_compatibility():
    """
    Test that the changed/removed interfaces for Thunderbird 12 are flagged.
    """

    err = _do_real_test_raw("""
    var x = Components.classes["foo"].createInstance(
        Components.interfaces.nsIMsgDBService);
    x.openMailDBFromFile();
    var y = Components.classes["foo"].createInstance(
        Components.interfaces.nsIMsgDatabase);
    y.Open();
    """)
    assert not err.failed(fail_on_warnings=False)
    assert not err.warnings
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw("""
    var x = Components.classes["foo"].createInstance(
        Components.interfaces.nsIMsgDBService);
    x.openMailDBFromFile();
    var y = Components.classes["foo"].createInstance(
        Components.interfaces.nsIMsgDatabase);
    y.Open();
    """, versions={TB_GUID: version_range("thunderbird", "12.0a1")})
    assert err.failed
    assert len(err.notices) == 2
    assert err.compat_summary["errors"]

def test_tb13_compatibility():
    """
    Test that the changed/removed interfaces for Thunderbird 13 are flagged.
    """
    err = _do_real_test_raw("""
    var x = Components.classes["foo"].createInstance(
        Components.interfaces.nsIMsgLocalMailFolder);
    x.addMessage();
    var y = Components.classes["foo"].createInstance(
        Components.interfaces.nsIMsgNewsFolder);
    y.getGroupUsernameWithUI();
    """)
    assert not err.failed(fail_on_warnings=False)
    assert not err.warnings
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw("""
    var x = Components.classes["foo"].createInstance(
        Components.interfaces.nsIMsgLocalMailFolder);
    x.addMessage();
    var y = Components.classes["foo"].createInstance(
        Components.interfaces.nsIMsgNewsFolder);
    y.getGroupUsernameWithUI();
    """, versions={TB_GUID: version_range("thunderbird", "13.0a1")})
    assert err.failed
    assert len(err.notices) == 2
    assert err.compat_summary["errors"]

    # Test the regex checks
    err = _do_real_test_raw("""
    var x = serverPageInit();
    var x = loginPageInit();
    var x = serverPageValidate();
    var x = serverPageUnload();
    var x = loginPageValidate();
    var x = setupBccTextbox();
    var x = setupCcTextbox();
    """, versions={TB_GUID: version_range("thunderbird", "13.0a1")})
    assert err.failed
    assert len(err.notices) == 7
    assert err.compat_summary["errors"]

    # Make sure only the desired functions are causing errors
    err = _do_real_test_raw("""
    var x = serverPage();
    var x = clientPageInit();
    """, versions={TB_GUID: version_range("thunderbird", "13.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert not err.notices
    assert not err.compat_summary["errors"]

def test_requestAnimationFrame():
    """
    Test that requestAnimationFrame requires at least one parameter.
    """

    err = _do_real_test_raw("""
    requestAnimationFrame(foo);
    """, versions={FIREFOX_GUID: version_range("firefox", "11.0a1")})
    assert not err.failed()

    err = _do_real_test_raw("""
    requestAnimationFrame();
    """, versions={FIREFOX_GUID: version_range("firefox", "11.0a1")})
    assert err.failed()
    assert err.compat_summary["errors"]


def test_fx12_interfaces():
    """
    Test that the Firefox 12 compatibility error interfaces throw compatibility
    errors when they're supposed to.
    """
    err = _do_real_test_raw("""
    var x = '<foo chromemargin="1">';
    """, versions={FIREFOX_GUID: version_range("firefox", "12.0a1")})
    assert not err.failed()
    assert not err.warnings
    assert err.notices
    assert err.compat_summary["errors"]

    err = _do_real_test_raw("""
    var x = window.documentCharsetInfo;
    """, versions={FIREFOX_GUID: version_range("firefox", "12.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert err.compat_summary["errors"]

    err = _do_real_test_raw("""
    var x = Components.interfaces.nsIJetpack;
    """, versions={FIREFOX_GUID: version_range("firefox", "12.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert err.compat_summary["errors"]

    err = _do_real_test_raw("""
    var x = Components.interfaces.nsIJetpackService;
    """, versions={FIREFOX_GUID: version_range("firefox", "12.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert err.compat_summary["errors"]

    err = _do_real_test_raw("""
    var x = Components.interfaces.nsIProxyObjectManager;
    """, versions={FIREFOX_GUID: version_range("firefox", "12.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert err.compat_summary["errors"]


def test_fx13_interfaces():
    """
    Test that the Gecko 13 compatibility warnings and errors for matched
    patterns are thrown when they're supposed to.
    """

    err = _do_real_test_raw("""
    var x = Components.interfaces.nsILivemarkService;
    """, versions={FIREFOX_GUID: version_range("firefox", "13.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert err.compat_summary["errors"]

    err = _do_real_test_raw("""
    var x = Components.interfaces.nsIPrefBranch2;
    """, versions={FIREFOX_GUID: version_range("firefox", "13.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert err.compat_summary["warnings"]

    err = _do_real_test_raw("""
    var x = Components.interfaces.nsIScriptableUnescapeHTML;
    """, versions={FIREFOX_GUID: version_range("firefox", "13.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert err.compat_summary["warnings"]

    err = _do_real_test_raw("""
    var x = Components.interfaces.nsIAccessNode;
    """, versions={FIREFOX_GUID: version_range("firefox", "13.0a1")})
    assert not err.failed(fail_on_warnings=False)
    assert err.compat_summary["errors"]


def test_globalStorage_flagged():
    """
    Test that all references to `globalStorage` are flagged with a warning and
    a compatibility error.
    """

    err = _do_real_test_raw("""
    var x = window.globalStorage["foo"];
    """)
    assert not err.failed()

    err = _do_real_test_raw("""
    var x = window.globalStorage["foo"];
    """, versions={FIREFOX_GUID: version_range("firefox", "13.0a1")})
    assert err.failed()
    assert err.compat_summary["errors"]


def test_excludeItemsIfParentHasAnnotation():
    """
    Test that `excludeItemsIfParentHasAnnotation` is flagged for Gecko 13.
    """

    err = _do_real_test_raw("""
    var x = window.excludeItemsIfParentHasAnnotation;
    """)
    assert not err.failed()

    err = _do_real_test_raw("""
    var x = window.excludeItemsIfParentHasAnnotation;
    """, versions={FIREFOX_GUID: version_range("firefox", "13.0a1")})
    assert err.failed()
    assert err.compat_summary["errors"]


def test_startendMarker():
    """
    Test that _startMarker and _endMarker are properly flagged in Gecko 13.
    """

    err = _do_real_test_raw("""
    var foo = bar();
    var x = foo._startMarker;
    var x = foo._endMarker;
    """)
    assert not err.failed()

    err = _do_real_test_raw("""
    var foo = bar();
    var x = foo._startMarker;
    """, versions={FIREFOX_GUID: version_range("firefox", "13.0a1")})
    assert not err.failed()
    assert err.notices
    assert err.compat_summary["errors"]

    err = _do_real_test_raw("""
    var foo = bar();
    var x = foo._endMarker;
    """, versions={FIREFOX_GUID: version_range("firefox", "13.0a1")})
    assert not err.failed()
    assert err.notices
    assert err.compat_summary["errors"]

    err = _do_real_test_raw("""
    var foo = bar();
    foo._startMarker = 1;
    """, versions={FIREFOX_GUID: version_range("firefox", "13.0a1")})
    assert not err.failed()
    assert err.notices
    assert err.compat_summary["errors"]

    err = _do_real_test_raw("""
    var foo = bar();
    foo._endMarker = 1;
    """, versions={FIREFOX_GUID: version_range("firefox", "13.0a1")})
    assert not err.failed()
    assert err.notices
    assert err.compat_summary["errors"]

