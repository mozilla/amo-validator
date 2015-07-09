"""
Presumably, the purpose of this module is to load things in an order such
that they do not cause import loops. Given how easy it is, at the moment,
to cause import loops by making trivial changes, this presumption is likely
valid.

It probably also has the effect of making sure each of these modules registers
its testcases in the appropriate places before we begin running tests.
"""
import validator.testcases.chromemanifest
# Import this before content to avoid import loops.
import validator.testcases.javascript.traverser
import validator.testcases.content
import validator.testcases.installrdf
import validator.testcases.jetpack
import validator.testcases.l10ncompleteness
import validator.testcases.langpack
import validator.testcases.packagelayout
import validator.testcases.targetapplication
import validator.testcases.themes
