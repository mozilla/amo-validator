# -*- coding: utf-8 -*-
import json
import os
import tempfile
import types

from nose.tools import eq_

from helper import TestCase
import validator.constants
from validator.errorbundler import ErrorBundle
from validator.specs.webapps import WebappSpec
import validator.webapp


class TestWebappAccessories(TestCase):
    """
    Test that helper functions for webapp manifests work as they are intended
    to.
    """

    def test_path(self):
        """Test that paths are tested properly for allowances."""

        s = WebappSpec("{}", ErrorBundle())

        eq_(s._path_valid("*"), False)
        eq_(s._path_valid("*", can_be_asterisk=True), True)
        eq_(s._path_valid("/foo/bar"), False)
        eq_(s._path_valid("/foo/bar", can_be_absolute=True), True)
        eq_(s._path_valid("//foo/bar"), False)
        eq_(s._path_valid("//foo/bar", can_be_absolute=True), False)
        eq_(s._path_valid("//foo/bar", can_be_relative=True), False)
        eq_(s._path_valid("http://asdf/"), False)
        eq_(s._path_valid("https://asdf/"), False)
        eq_(s._path_valid("ftp://asdf/"), False)
        eq_(s._path_valid("http://asdf/", can_have_protocol=True), True)
        eq_(s._path_valid("https://asdf/", can_have_protocol=True), True)
        # No FTP for you!
        eq_(s._path_valid("ftp://asdf/", can_have_protocol=True), False)
        eq_(s._path_valid("data:asdf"), False)
        eq_(s._path_valid("data:asdf", can_be_data=True), True)


class TestWebapps(TestCase):

    def setUp(self):
        super(TestWebapps, self).setUp()
        self.listed = False

        self.data = {
            "version": "1.0",
            "name": "MozBall",
            "description": "Exciting Open Web development action!",
            "icons": {
                "16": "/img/icon-16.png",
                "48": "/img/icon-48.png",
                "128": "/img/icon-128.png"
            },
            "developer": {
                "name": "Mozilla Labs",
                "url": "http://mozillalabs.com"
            },
            "installs_allowed_from": [
                "https://appstore.mozillalabs.com",
                "HTTP://mozilla.com/AppStore"
            ],
            "launch_path": "/index.html",
            "locales": {
                "es": {
                    "name": "Foo Bar",
                    "description": "¡Acción abierta emocionante del desarrollo",
                    "developer": {
                        "url": "http://es.mozillalabs.com/"
                    }
                },
                "it": {
                    "description": "Azione aperta emozionante di sviluppo di!",
                    "developer": {
                        "url": "http://it.mozillalabs.com/"
                    }
                }
            },
            "default_locale": "en",
            "screen_size": {
                "min_width": "600",
                "min_height": "300"
            },
            "required_features": [
                "touch", "geolocation", "webgl"
            ],
            "orientation": "landscape",
            "fullscreen": "true"
        }

    def analyze(self):
        """Run the webapp tests on the file."""
        self.detected_type = validator.constants.PACKAGE_WEBAPP
        self.setup_err()
        with tempfile.NamedTemporaryFile(delete=False) as t:
            if isinstance(self.data, types.StringTypes):
                t.write(self.data)
            else:
                t.write(json.dumps(self.data))
            name = t.name
        validator.webapp.detect_webapp(self.err, name)
        os.unlink(name)

    def test_pass(self):
        """Test that a bland webapp file throws no errors."""
        self.analyze()
        self.assert_silent()

    def test_bom(self):
        """Test that a plain webapp with a BOM won't throw errors."""
        self.setup_err()
        validator.webapp.detect_webapp(
            self.err, "tests/resources/unicodehelper/utf8_webapp.json")
        self.assert_silent()

    def test_fail_parse(self):
        """Test that invalid JSON is reported."""
        self.data = "}{"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_missing_required(self):
        """Test that missing the name element is a bad thing."""
        del self.data["name"]
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_invalid_name(self):
        """Test that the name element is a string."""
        self.data["name"] = ["foo", "bar"]
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_long_name(self):
        """Test that long names are flagged for truncation in Gaia."""
        self.data["name"] = "This is a long name."
        self.analyze()
        self.assert_failed(with_warnings=True)

    def test_maxlengths(self):
        """Test that certain elements are capped in length."""
        self.data["name"] = "%" * 129
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_invalid_keys(self):
        """Test that unknown elements are flagged"""
        self.data["foobar"] = "hello"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_warn_extra_keys(self):
        """Test that extra keys are flagged."""
        self.data["locales"]["es"]["foo"] = "hello"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_icons_not_dict(self):
        """Test that the icons property is a dictionary."""
        self.data["icons"] = ["data:foo/bar.png"]
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_icons_data_url(self):
        """Test that webapp icons can be data URLs."""
        self.data["icons"]["asdf"] = "data:foo/bar.png"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_icons_relative_url(self):
        """Test that webapp icons cannot be relative URLs."""
        self.data["icons"]["128"] = "foo/bar"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_icons_absolute_url(self):
        """Test that webapp icons can be absolute URLs."""
        def test_icon(self, icon):
            self.setUp()
            self.data["icons"]["128"] = icon
            self.analyze()
            self.assert_silent()

        for icon in ['/foo/bar', 'http://foo.com/bar', 'https://foo.com/bar']:
            yield test_icon, self, icon

    def test_icons_has_min_selfhosted(self):
        del self.data["icons"]["128"]
        self.analyze()
        self.assert_silent()

    def test_icons_has_min_listed(self):
        self.listed = True
        self.data["installs_allowed_from"] = \
                validator.constants.DEFAULT_WEBAPP_MRKT_URLS
        del self.data["icons"]["128"]
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_no_locales(self):
        """Test that locales are not required."""
        del self.data["locales"]
        self.analyze()
        self.assert_silent()

    def test_no_default_locale(self):
        """Test that locales require default_locale."""
        del self.data["default_locale"]
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_invalid_locale_keys(self):
        """Test that locales only contain valid keys."""
        # Banned locale element.
        self.data["locales"]["es"]["default_locale"] = "foo"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_invalid_locale_keys_missing(self):
        """Test that locales aren't missing any required elements."""
        del self.data["locales"]["es"]["name"]
        self.analyze()
        self.assert_silent()

    def test_installs_allowed_from_not_list(self):
        """Test that the installs_allowed_from path is a list."""
        self.data["installs_allowed_from"] = "foobar"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_bad_installs_allowed_from_path(self):
        """Test that the installs_allowed_from path is valid."""
        self.data["installs_allowed_from"].append("foo/bar")
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_no_amo_installs_allowed_from(self):
        """Test that installs_allowed_from should include Marketplace."""
        # self.data does not include a marketplace URL by default.
        self.listed = True
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_amo_iaf(self):
        """Test that the various Marketplace URLs work."""

        # Test that the Marketplace production URL is acceptable.
        self.setUp()
        orig_iaf = self.data["installs_allowed_from"]

        def test_iaf(self, iaf, url):
            self.setUp()
            self.data["installs_allowed_from"] = iaf + [url]
            self.analyze()
            self.assert_silent()

        for url in validator.constants.DEFAULT_WEBAPP_MRKT_URLS:
            yield test_iaf, self, orig_iaf, url

    def test_iaf_wildcard(self):
        """Test that installs_allowed_from can contain a wildcard."""
        self.listed = True
        self.data["installs_allowed_from"].append("*")
        self.analyze()
        self.assert_silent()

    def test_installs_allowed_from_protocol(self):
        """
        Test that if the developer includes a URL in the `installs_allowed_from`
        parameter that is a valid Marketplace URL but uses HTTP instead of
        HTTPS, we flag it as using the wrong protocol and not as an invalid URL.
        """
        self.listed = True
        bad_url = validator.constants.DEFAULT_WEBAPP_MRKT_URLS[0].replace(
                "https", "http")

        self.data["installs_allowed_from"] = (bad_url, )
        self.analyze()
        self.assert_failed(with_errors=True)
        self.assert_got_errid(("spec", "webapp", "iaf_bad_mrkt_protocol", ))

    def test_launch_path_not_string(self):
        """Test that the launch path is a string."""
        self.data["launch_path"] = [123]
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_bad_launch_path(self):
        """Test that the launch path is valid."""
        self.data["launch_path"] = "data:asdf"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_bad_launch_path_protocol(self):
        """Test that the launch path cannot have a protocol."""
        self.data["launch_path"] = "http://foo.com/bar"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_bad_launch_path_absolute(self):
        """Test that the launch path is absolute."""
        self.data["launch_path"] = "/foo/bar"
        self.analyze()
        self.assert_silent()

    def test_widget_deprecated(self):
        """Test that the widget property is deprecated."""
        self.data["widget"] = {
            "path": "/butts.html",
            "width": 100,
            "height": 200
        }
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_dev_missing(self):
        """Test that the developer property can be absent."""
        del self.data["developer"]
        self.analyze()
        self.assert_silent()

    def test_dev_not_dict(self):
        """Test that the developer property must be a dict."""
        self.data["developer"] = "foo"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_bad_dev_keys(self):
        """Test that the developer keys are present."""
        del self.data["developer"]["name"]
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_bad_dev_url(self):
        """Test that the developer keys are correct."""
        self.data["developer"]["url"] = "foo"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_screen_size_missing(self):
        """Test that the 'screen_size' property can be absent."""
        del self.data["screen_size"]
        self.analyze()
        self.assert_silent()

    def test_screen_size_is_dict(self):
        """Test that the 'screen_size' property must be a dict."""
        self.data["screen_size"] = "foo"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_screen_size_contains_pair(self):
        """Test that 'screen_size' must contain at least one key/value pair."""
        self.data["screen_size"] = {}
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_bad_screen_size_key(self):
        """Test that the 'screen_size' keys are correct."""
        self.data["screen_size"]["max_width"] = "500"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_bad_screen_size_value(self):
        """Test that the 'screen_size' keys are correct."""
        self.data["screen_size"]["min_width"] = "500px"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_required_features_missing(self):
        """Test that the 'required_features' property can be absent."""
        del self.data["screen_size"]
        self.analyze()
        self.assert_silent()

    def test_required_features_is_list(self):
        """Test that the 'required_features' property must be a list."""
        self.data["required_features"] = "fart"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_required_features_missing(self):
        """Test that 'required_features' can be absent."""
        del self.data["required_features"]
        self.analyze()
        self.assert_silent()

    def test_required_features_empty(self):
        """Test that 'required_features' can be an empty list."""
        self.data["required_features"] = []
        self.analyze()
        self.assert_silent()

    def test_orientation_missing(self):
        """Test that the 'orientation' property can be absent."""
        del self.data["orientation"]
        self.analyze()
        self.assert_silent()

    def test_orientation_is_string(self):
        """Test that the 'orientation' property must be a string."""
        self.data["orientation"] = {}
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_orientation_cannot_be_empty(self):
        """Test that 'orientation' cannot be an empty string."""
        self.data["orientation"] = ""
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_orientation_valid_value(self):
        """Test that 'orientation' must have a valid value."""
        def test_orientation(self, orientation):
            self.setUp()
            self.data["orientation"] = orientation
            self.analyze()
            self.assert_silent()

        for key in ("portrait", "landscape", "portrait-secondary",
                    "landscape-secondary",):
            yield test_orientation, self, key

    def test_orientation_bad_value(self):
        """Test that 'orientation' cannot have an invalid value."""
        self.data["orientation"] = "fart"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_orientation_empty_value(self):
        """Test that 'orientation' cannot have an empty value."""
        self.data["orientation"] = ""
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_fullscreen_missing(self):
        """Test that the 'fullscreen' property can be absent."""
        del self.data["fullscreen"]
        self.analyze()
        self.assert_silent()

    def test_fullscreen_is_string(self):
        """Test that the 'fullscreen' property must be a string."""
        self.data["fullscreen"] = {}
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_fullscreen_cannot_be_empty(self):
        """Test that 'fullscreen' cannot be an empty string."""
        self.data["fullscreen"] = ""
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_fullscreen_valid_value(self):
        """Test that 'fullscreen' must have a valid value."""
        def test_fullscreen(self, value):
            self.setUp()
            self.data["fullscreen"] = key
            self.analyze()
            self.assert_silent()

        for key in ("true", "false", ):
            yield test_fullscreen, self, key

    def test_fullscreen_bad_value(self):
        """Test that 'fullscreen' cannot have an invalid value."""
        self.data["fullscreen"] = "fart"
        self.analyze()
        self.assert_failed(with_errors=True)

