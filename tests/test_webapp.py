# -*- coding: utf-8 -*-
import copy
import json
import os
import tempfile

from nose.tools import eq_

import validator.constants
from validator.errorbundler import ErrorBundle
import validator.webapp


def test_test_path():
    """Test the test_path function."""

    eq_(validator.webapp.test_path("/foo/bar"), True)
    eq_(validator.webapp.test_path("/foo/bar", True), True)
    eq_(validator.webapp.test_path("//foo/bar"), False)
    eq_(validator.webapp.test_path("//foo/bar", True), False)
    eq_(validator.webapp.test_path("http://asdf/"), False)
    eq_(validator.webapp.test_path("data:asdf"), False)
    eq_(validator.webapp.test_path("data:asdf", True), True)


def _detect(err, data):
    """Run the webapp tests on the file."""

    err.detected_type = validator.constants.PACKAGE_WEBAPP
    with tempfile.NamedTemporaryFile(delete=False) as t:
        if isinstance(data, str):
            t.write(data)
        else:
            t.write(json.dumps(data))
        name = t.name
    validator.webapp.detect_webapp(err, name)
    err.print_summary(verbose=True)
    err.render_json()
    os.unlink(name)


def _get_json():
    return copy.deepcopy({
        "version": "1.0",
        "name": "MozillaBall",
        "description": "Exciting Open Web development action!",
        "icons": {
            "16": "/img/icon-16.png",
            "48": "/img/icon-48.png",
            "128": "/img/icon-128.png"
        },
        "widget": {
            "path": "/widget.html",
            "width": 100,
            "height": 200
        },
        "developer": {
            "name": "Mozilla Labs",
            "url": "http://mozillalabs.com"
        },
        "installs_allowed_from": [
            "https://appstore.mozillalabs.com"
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
        "default_locale": "en"
    })


def test_webapp_pass():
    """Test that a bland webapp file throws no errors."""

    err = ErrorBundle()
    _detect(err, _get_json())
    print err.print_summary(verbose=True)
    assert not err.failed()


def test_webapp_fail_parse():
    """Test that invalid JSON is reported."""

    err = ErrorBundle()
    _detect(err, "}{")
    assert err.failed()


def test_webapp_missing_required():
    """Test that missing the name element is a bad thing."""

    err = ErrorBundle()
    data = _get_json()
    del data["name"]
    _detect(err, data)
    assert err.failed()


def test_webapp_invalid_name():
    """Test that the name element is a string."""

    err = ErrorBundle()
    data = _get_json()
    data["name"] = ["foo", "bar"]
    _detect(err, data)
    assert err.failed()


def test_webapp_maxlengths():
    """Test that certain elements are capped in length."""

    err = ErrorBundle()
    data = _get_json()
    data["name"] = "%" * 129
    _detect(err, data)
    assert err.failed()


def test_webapp_invalid_keys():
    """Test that unknown elements are flagged"""

    err = ErrorBundle()
    data = _get_json()
    data["foobar"] = "hello"
    _detect(err, data)
    assert err.failed()


def test_webapp_warn_extra_keys():
    err = ErrorBundle()
    data = _get_json()
    data["locales"]["es"]["foo"] = "hello"
    _detect(err, data)
    assert err.failed()


def test_webapp_icons_not_dict():
    """Test that the icons property is a dictionary."""

    err = ErrorBundle()
    data = _get_json()
    data["icons"] = ["data:foo/bar.png"]
    _detect(err, data)
    assert err.failed()


def test_webapp_icons_data_url():
    """Test that webapp icons can be data URLs."""

    err = ErrorBundle()
    data = _get_json()
    data["icons"]["asdf"] = "data:foo/bar.png"
    _detect(err, data)
    assert err.failed()


def test_webapp_icons_relative_url():
    """Test that webapp icons cannot be relative URLs."""

    err = ErrorBundle()
    data = _get_json()
    data["icons"]["128"] = "foo/bar"
    _detect(err, data)
    assert err.failed()


def test_webapp_icons_absolute_url():
    """Test that webapp icons can be absolute URLss."""

    err = ErrorBundle()
    data = _get_json()
    data["icons"]["128"] = "/foo/bar"
    _detect(err, data)
    assert not err.failed()


def test_webapp_no_locales():
    """Test that locales are not required."""

    err = ErrorBundle()
    data = _get_json()
    del data["default_locale"]
    del data["locales"]
    _detect(err, data)
    assert not err.failed()


def test_webapp_no_default_locale():
    """Test that locales require default_locale."""

    err = ErrorBundle()
    data = _get_json()
    del data["default_locale"]
    _detect(err, data)
    print err.print_summary(verbose=True)
    assert err.failed()


def test_webapp_invalid_locale_keys():
    """Test that locales only contain valid keys."""

    err = ErrorBundle()
    data = _get_json()
    # Banned locale element.
    data["locales"]["es"]["default_locale"] = "foo"
    _detect(err, data)
    assert err.failed()

    err = ErrorBundle()
    data = _get_json()
    del data["locales"]["es"]["name"]
    _detect(err, data)
    assert not err.failed()


def test_webapp_installs_allowed_from_not_list():
    """Test that the installs_allowed_from path is a list."""

    err = ErrorBundle()
    data = _get_json()
    data["installs_allowed_from"] = "foobar"
    _detect(err, data)
    assert err.failed()


def test_webapp_bad_installs_allowed_from_path():
    """Test that the installs_allowed_from path is valid."""

    err = ErrorBundle()
    data = _get_json()
    data["installs_allowed_from"].append("foo/bar")
    _detect(err, data)
    assert err.failed()


def test_webapp_launch_path_not_string():
    """Test that the launch path is a string."""

    err = ErrorBundle()
    data = _get_json()
    data["launch_path"] = [123]
    _detect(err, data)
    assert err.failed()


def test_webapp_bad_launch_path():
    """Test that the launch path is valid."""

    err = ErrorBundle()
    data = _get_json()
    data["launch_path"] = "data:asdf"
    _detect(err, data)
    assert err.failed()


def test_webapp_widget_not_dict():
    """Test that the widget property is a dict."""

    err = ErrorBundle()
    data = _get_json()
    data["widget"] = "foo"
    _detect(err, data)
    assert err.failed()


def test_webapp_bad_widget_path():
    """Test that the widget path is valid."""

    err = ErrorBundle()
    data = _get_json()
    data["widget"]["path"] = "data:asdf"
    _detect(err, data)
    assert err.failed()


def test_webapp_bad_widget_size():
    """Test that the widget size is valid."""

    err = ErrorBundle()
    data = _get_json()
    data["widget"]["height"] = 100000
    _detect(err, data)
    assert err.failed()


def test_webapp_bad_widget_keys():
    """Test that the widget keys are valid."""

    err = ErrorBundle()
    data = _get_json()
    data["widget"]["extra"] = "foo"
    _detect(err, data)
    assert err.failed()


def test_webapp_bad_widget_missing():
    """Test that the widget keys are present."""

    err = ErrorBundle()
    data = _get_json()
    del data["widget"]["path"]
    _detect(err, data)
    assert err.failed()


def test_webapp_dev_not_dict():
    """Test that the developer property must be a dict"""

    err = ErrorBundle()
    data = _get_json()
    data["developer"]["developer"] = "foo"
    _detect(err, data)
    assert err.failed()


def test_webapp_bad_dev_keys():
    """Test that the developer keys are present."""

    err = ErrorBundle()
    data = _get_json()
    del data["developer"]["name"]
    _detect(err, data)
    assert err.failed()


def test_webapp_bad_dev_url():
    """Test that the developer keys are correct."""

    err = ErrorBundle()
    data = _get_json()
    data["developer"]["url"] = "foo"
    _detect(err, data)
    assert err.failed()

