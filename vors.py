## Vors (proper noun, temp name)
## An HTML templating and minifying engine
import sys


def to_cwf(fname): ## Convert an HTML file to Compressed Web Format, including a symbol table
    symbols = []
    cont = ""
    ## symbols are utf-8 numbers referencing an index in the above list, which is appended to the top of the file.
    file = open(fname, "rb")
    for byte in file.read():
        char = chr(byte)
        print(char)
    for x in symbols:
        pass
    return "VORS" + cont

to_cwf("base.html")
