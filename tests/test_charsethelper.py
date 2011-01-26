# -*- coding: utf-8 -*-
import os
import validator.testcases.charsethelper as charsethelper

def _do_test(path):
    "Performs a test on a JS file"
    
    text = open(path).read()
    assert charsethelper.decode(text) == u"täst"

def test_latin1():
    "Tests utf-8 encoding is properly decoded"
    _do_test("tests/resources/charsethelper/latin_1.txt")

def test_utf8():
    "Tests utf-8 w/o BOM encoding is properly decoded"
    _do_test("tests/resources/charsethelper/utf-8.txt")

def test_utf8():
    "Tests utf-8 with BOM encoding is properly decoded"
    _do_test("tests/resources/charsethelper/utf-8-bom.txt")

def test_utf16le():
    "Tests utf-16 Little Endian encoding is properly decoded"
    _do_test("tests/resources/charsethelper/utf-16le.txt")

def test_utf16be():
    "Tests utf-16 Big Endian encoding is properly decoded"
    _do_test("tests/resources/charsethelper/utf-16be.txt")
    
def test_utf32le():
    "Tests utf-32 Little Endian encoding is properly decoded"
    _do_test("tests/resources/charsethelper/utf-32le.txt")

def test_utf32be():
    "Tests utf-32 Big Endian encoding is properly decoded"
    _do_test("tests/resources/charsethelper/utf-32be.txt")
