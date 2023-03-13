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
    return ret

def to_cwf(fname): ## Convert an HTML file to Compressed Web Format, including a symbol table
    cont = ""
    ## CWF grammar: ignoring the header, CWF is quite simple. Read a byte, do something based on it. Byte 0 is a tag, and the next utf-8 number is what tag number,
    ## based on the reftable in the header. UTF-8 encoded for now. Then, either 0 (no ID) or a 1-indexed reference to an ID in the reftable, and 1-indexed references
    ## to classes in the reftable until the next 0 (just 0 if no classes). Properties are a bit more complex - a 1-indexed reference to an ID in the reftable
    ## gives the property name, then there's a null-terminated string with the property value (note: for boolean properties, the string will just be the byte 1).
    ## A 0 property id indicates the end of the tag. NULL-termination is kewl.
    ## Byte 1 is an ending tag. No content - vors generates the endings based on the current tag level.
    ## Byte 2 is just content. Null-terminated string.
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
                if "id" in properties:
                    if not properties["id"] in idReference:
                        idReference.append(properties["id"])
                    ret += chr(idReference.index(properties["id"]) + 1)
                    del properties["id"]
                else:
                    ret += chr(0)
                if "class" in properties:
                    for c in properties["class"].split(" "):
                        if not c in classReference:
                            classReference.append(c)
                        ret += chr(classReference.index(c) + 1)
                    del properties["class"]
                ret += chr(0)
                for key in properties:
                    if not key in propertyReference:
                        propertyReference.append(key)
                    ret += chr(propertyReference.index(key) + 1)
                    ret += properties[key] if type(properties[key]) == str else chr(1)
                    ret += chr(0)
                ret += chr(0)
        return ret

    def handleCommand(cmd):
        print("command:", cmd)
        return ""

    def handleContent(cont):
        return chr(2) + cont + chr(0)

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

def from_cwf(data, pretty=False):
    ret = "<!DOCTYPE html>"
    if pretty:
        ret += "\n\n"
    mode = 0
    classBuf = ""
    valueBuf = ""
    tagLevel = []
    for char in data:
        b = ord(char)
        tabs = "\t" * len(tagLevel)
        if mode == 0:
            if b == 0:
                if pretty:
                    ret += tabs
                ret += "<"
                mode = 1
            elif b == 1:
                if pretty:
                    ret += "\t" * (len(tagLevel) - 1)
                ret += "</" + tagReference[tagLevel[-1]] + ">"
                if pretty:
                    ret += "\n"
                del tagLevel[-1]
            elif b == 2:
                if pretty:
                    ret += tabs
                mode = 6
        elif mode == 1:
            ret += tagReference[b - 1]
            tagLevel.append(b - 1)
            mode = 2
        elif mode == 2:
            if b > 0:
                ret += " id=\"" + idReference[b - 1] + "\""
            mode = 3
        elif mode == 3:
            if b == 0:
                classBuf = classBuf.strip()
                if classBuf != "":
                    ret += " class=\"" + classBuf + "\""
                    classBuf = ""
                mode = 4
            else:
                classBuf += classReference[b - 1] + " "
        elif mode == 4:
            if b == 0:
                ret += ">"
                if pretty:
                    ret += "\n"
                mode = 0
            else:
                ret += " " + propertyReference[b - 1]
                mode = 5
        elif mode == 5:
            if b == 0:
                if not (len(valueBuf) == 1 and ord(valueBuf[0]) == 1):
                    ret += "=\"" + valueBuf + "\""
                valueBuf = ""
                mode = 4
            else:
                valueBuf += char
        elif mode == 6:
            if b == 0:
                mode = 0
                if pretty:
                    ret += "\n"
            else:
                ret += char
    return ret

ret = to_cwf("base.html")
print(ret)

print(tagReference)
print(idReference)
print(classReference)
print(symbolReference)
print(propertyReference)

print(list(bytes(ret, "utf-8")))
print(from_cwf(ret, pretty=True))