## Vors (proper noun, temp name)
## An HTML templating and minifying engine
import sys


## these are global because they're used by unload and by load
idReference = []
classReference = []
tagReference = []
symbolReference = []
propertyReference = [] ## Properties besides class and id


def parseTagdata(tD):
    mode = 0
    ret = {}
    nameBuf = ""
    valueBuf = ""
    escape = False
    for i in range(0, len(tD)):
        x = tD[i]
        if mode == 0:
            if x == " ":
                nameBuf = nameBuf.strip()
                mode = 5
            elif x == "=":
                mode = 1
            else:
                nameBuf += x
        elif mode == 1:
            if x == '"':
                mode = 2
        elif mode == 2:
            if x == '"' and not escape:
                valueBuf = valueBuf.strip()
                mode = 3
            else:
                escape = False
                if x == '\\':
                    escape = True
                else:
                    valueBuf += x
        elif mode == 3:
            mode = 0
            ret[nameBuf.strip()] = valueBuf.strip()
            valueBuf = ""
            nameBuf = x
        elif mode == 5:
            if not x in [" ", "="]:
                ret[nameBuf] = True
                nameBuf = x
                mode = 0
            else:
                if x == "=":
                    mode = 1
    if len(nameBuf) > 0:
        if len(valueBuf) > 0:
            ret[nameBuf] = valueBuf
        else:
            ret[nameBuf] = True
    print(ret)

def to_cwf(fname): ## Convert an HTML file to Compressed Web Format, including a symbol table
    cont = ""
    ## CWF grammar: ignoring the header, CWF is quite simple. Read a byte, do something based on it. Byte 0 is a tag, and the next utf-8 number is what tag number,
    ## based on the reftable in the header. UTF-8 encoded for now. Then, either 0 (no ID) or a 1-indexed reference to an ID in the reftable, and 1-indexed references
    ## to classes in the reftable until the next 0 (just 0 if no classes). Properties are a bit more complex - a 1-indexed reference to an ID in the reftable
    ## gives the property name, then there's a null-terminated string with the property value. A 0 property id indicates the end of the tag. NULL-termination is kewl.
    ## Byte 1 is an ending tag. No content - vors generates the endings based on the current tag level.
    ## Byte 2 is just content. Next utf-8 character is the content-length, and everything after that is... content. Content is expected to be written directly to
    ## the output file - Vors will not alter it. [] commands and <> inside content are considered separators, of course.
    file = open(fname)
    tagBuf = ""
    commandBuf = ""
    contentBuf = ""
    mode = 0

    def handleTag(tag):
        global classReference
        global idReference
        global tagReference
        global propertyReference
        ret = ""
        if not tag.startswith("!DOCTYPE"): ## doctype html is ignored; it'll be added on final HTML generation
            if tag[0] == "/":
                ret = chr(1)
            else:
                tagName = tag.split(" ")[0]
                tagData = tag[len(tagName):].strip()
                properties = parseTagdata(tagData)
                ret = chr(0)
                if not tagName in tagReference:
                    tagReference.append(tagName)
                ret += chr(tagReference.index(tagName) + 1)
        return ret

    def handleCommand(cmd):
        print("command:", cmd)
        return ""

    def handleContent(cont):
        return chr(2) + chr(len(cont)) + cont

    for char in file.read():
        if mode == 0:
            if char == "<":
                mode = 1
            elif char == "[":
                mode = 2
            else:
                contentBuf += char
            if char in ["<", "["]:
                contentBuf = contentBuf.strip()
                if contentBuf != "":
                    cont += handleContent(contentBuf)
                    contentBuf = ""
        elif mode == 1:
            if char == ">":
                cont += handleTag(tagBuf.strip())
                tagBuf = ""
                mode = 0
            else:
                tagBuf += char
        elif mode == 2:
            if char == "]":
                cont += handleCommand(commandBuf.strip())
                commandBuf = ""
                mode = 0
            else:
                commandBuf += char
    return "VORS" + cont

ret = to_cwf("base.html")
print(ret)

print(tagReference)
print(idReference)
print(classReference)
print(symbolReference)
print(propertyReference)

print(list(bytes(ret, "utf-8")))