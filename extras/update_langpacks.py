import os
from fnmatch import fnmatch
from tempfile import NamedTemporaryFile
from zipfile import ZipFile


PACKAGE_MAPPINGS = {"Fennec.app": "fennec",
                    "Firefox.app": "firefox",
                    "SeaMonkey.app": "seamonkey",
                    "Thunderbird.app": "thunderbird",}


def copy_to_zip(read_zip, write_zip, pattern, prefix=""):
    for member in read_zip.namelist():
        if fnmatch(member, pattern):
            filename = member.split("/")[-1]
            write_zip.writestr("%s%s" % (prefix, filename),
                               read_zip.read(member))


def copy_to_new_zip(callback, read_zip, pattern, prefix=""):
    with NamedTemporaryFile("w") as temp:
        with ZipFile(temp.name, "w") as write_zip:
            copy_to_zip(read_zip, write_zip, pattern, prefix)

        callback(temp.name)


def main():
    for package in os.listdir("language_controls/"):
        if package.startswith(".") or package not in PACKAGE_MAPPINGS:
            continue

        platform = PACKAGE_MAPPINGS[package]
        path = "language_controls/%s" % package
        jar = ZipFile("../validator/testcases/langpacks/%s.xpi" % platform, "w")

        if platform == "firefox":
            # Firefox puts this stuff in omni.ja.
            with ZipFile("%s/Contents/MacOS/omni.ja" % path, "r") as omni_ja:
                #print list(x for x in omni_ja.namelist() if x.startswith("chrome/"))
                jar.writestr("chrome.manifest",
                             omni_ja.read("chrome/localized.manifest"))

                # Copy the chrome/en-US/ directory to /en-US.jar in the new zip.
                def callback(name):
                    jar.write(name, "en-US.jar")
                copy_to_new_zip(callback, omni_ja, "chrome/en-US/*")

        elif platform in ("thunderbird", "seamonkey", ):
            # Thunderbird puts stuff in omni.ja, too,
            with ZipFile("%s/Contents/MacOS/omni.ja" % path, "r") as omni_ja:
                jar.writestr("chrome.manifest",
                             omni_ja.read("chrome/localized.manifest"))

                # Copy the chrome/en-US/ directory to /en-US.jar in the new zip.
                def callback(name):
                    jar.write(name, "en-US.jar")
                copy_to_new_zip(callback, omni_ja, "chrome/en-US/*")

        else:
            jar.write("%s/Contents/MacOS/chrome/localized.manifest" % path,
                      "chrome.manifest")
            jar.write("%s/Contents/MacOS/chrome/en-US.jar" % path,
                      "en-US.jar")

        jar.close()


if __name__ == "__main__":
    main()

