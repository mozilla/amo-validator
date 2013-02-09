from helper import CompatTestCase
from validator.compat import TB7_DEFINITION


class TestTB7Compat(CompatTestCase):
    """Test that compatibility tests for Thunderbird 7 are properly executed."""

    VERSION = TB7_DEFINITION

    def test_nsIMsgThread(self):
        for method in self.run_xpcom_for_compat(
                "nsIMsgThread", ["GetChildAt()"]):
            self.assert_silent()
            self.assert_compat_error(type_="notice")

    def test_mail_attachment(self):
        """Test that the old mail attachment global functions are flagged."""
        functions = ["createNewAttachmentInfo",
                     "saveAttachment",
                     "attachmentIsEmpty",
                     "openAttachment",
                     "detachAttachment",
                     "cloneAttachment"]
        for function in functions:
            self.run_script_for_compat("%s()" % function)
            self.assert_silent()
            self.assert_compat_error(type_="notice")

    def test_dictUtils_removal(self):
        """Test that dictUtils.js imports are flagged."""
        self.run_script_for_compat(
                'Components.utils.import("resource:///modules/dictUtils.js");')
        self.assert_silent()
        self.assert_compat_error(type_="warning")

    def test_deRDF_addressbook(self):
        """Test that addressbook RDF sources are flagged."""

        self.run_script_for_compat("""
        var x = 'datasources="rdf:addressdirectory" ref="moz-abdirectory://"';
        """)
        self.assert_silent()
        self.assert_compat_error(type_="notice")

        self.run_script_for_compat("""
        var x = 'GetResource(SomeText).QueryInterface(6inTestxnsIAbDirectory);';
        """)
        self.assert_silent()
        self.assert_compat_error(type_="notice")
