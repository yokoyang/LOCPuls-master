# * coding:UTF-8
# *_author_='Yang'
import re

commentline = 0
blankline = 0
codeline = 0


def init():
    global commentline, blankline, codeline

    commentline = 0
    blankline = 0
    codeline = 0


def output(filename):
    global commentline, blankline, codeline
    print
    print "/*********************************************/"
    print "file name: ", filename
    print "code line: ", codeline
    print "comment line: ", commentline
    print "blank line: ", blankline
    print "total line: ", codeline + commentline + blankline
    print "comment rate: ", (commentline / float(codeline))
    print "/*********************************************/"


def count_c_like(filename):
    try:
        f = open(filename, 'r')
    except IOError, e:
        print
        print e
        return None

    global commentline, blankline, codeline

    iscomment = False
    for eachLine in f:
        if iscomment:
            commentline += 1
            if eachLine.find("*/", 0) != -1:
                iscomment = False
        elif re.match(" *//", eachLine) is not None:
            commentline += 1
        elif re.match(" */\*", eachLine) is not None:
            commentline += 1
            if re.search("/\*.*\*/", eachLine) is None:
                iscomment = True
        elif eachLine.isspace():
            blankline += 1
        else:
            codeline += 1

    f.close()
    return "OK"


def count_mk_like(filename):
    try:
        f = open(filename, 'r')
    except IOError, e:
        print
        print e
        return None

    global commentline, blankline, codeline
    for eachLine in f:
        if eachLine.isspace():
            blankline += 1
        elif re.match(" *#", eachLine) is not None:
            commentline += 1
        else:
            codeline += 1

    f.close()
    return "OK"


def main():
    try:
        f = open("filelist.txt", 'r')
    except IOError, e:
        print e
        raw_input('Press ENTER key to exit')
        return None
    global filename

    for eachLine in f:
        filename = eachLine.strip()
        if filename == '':
            continue

        init()
        result = "OK"
        # 如果是.min、.mk，.py这种代码的话
        if re.search("\.min$|\.mk$|\.py$", filename) is not None:
            result = count_mk_like(filename)
            print 'hhh'
        else:
            result = count_c_like(filename)

        if result == "OK":
            output(filename)

    f.close()
    raw_input('Press ENTER key to exit')


if __name__ == '__main__':
    main()
