import os

def make_tree(path):
        "Renders the AST tree for a code file."
        f = open("stage/%s" % path, 'r')
        data = f.read()
        f.close()

        data = data.replace("\\", "\\\\")
        data = data.replace("\n", "\\n")
        data = data.replace("\r", "\\r")
        data = data.replace("\t", "\\t")
        data = data.replace("\"", "\\\"")
        data = data.replace("'", "\\'")

        data = 'JSON.stringify(Reflect.parse("%s"))' % data
        data = "print(%s)" % data

        temp = open("/tmp/temp.js", 'w')
        temp.write(data)
        temp.close()

        shell = os.popen("/home/clouserw/temp/spidermonkey/js/src/Linux_DBG.OBJ/js /tmp/temp.js >> output")

for item in os.listdir("stage"):
        if item.startswith("."):
                continue
        print item
        make_tree(item)
