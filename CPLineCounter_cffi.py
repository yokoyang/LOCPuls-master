#!/usr/bin/python
# -*- coding: utf-8 -*-


import os, sys


detailCountInfo = []
rawCountInfo = [0, 0, 0, 0, 0]


def CalcLinesCh(line, isBlockComment):
    lineType, lineLen = 0, len(line)
    if not lineLen:
        return lineType

    line = line + '\n' #添加一个字符防止iChar+1时越界
    iChar, isLineComment = 0, False
    while iChar < lineLen:
        if line[iChar] == ' ' or line[iChar] == '\t':   #空白字符
            iChar += 1; continue
        elif line[iChar] == '/' and line[iChar+1] == '/': #行注释
            isLineComment = True
            lineType |= 2; iChar += 1 #跳过'/'
        elif line[iChar] == '/' and line[iChar+1] == '*': #块注释开始符
            isBlockComment[0] = True
            lineType |= 2; iChar += 1
        elif line[iChar] == '*' and line[iChar+1] == '/': #块注释结束符
            isBlockComment[0] = False
            lineType |= 2; iChar += 1
        else:
            if isLineComment or isBlockComment[0]:
                lineType |= 2
            else:
                lineType |= 1
        iChar += 1

    return lineType   #Bitmap：0空行，1代码，2注释，3代码和注释


def CalcLinesPy(line, isBlockComment):
    #isBlockComment[single quotes, double quotes]
    lineType, lineLen = 0, len(line)
    if not lineLen:
        return lineType

    line = line + '\n\n' #添加两个字符防止iChar+2时越界
    iChar, isLineComment = 0, False
    while iChar < lineLen:
        if line[iChar] == ' ' or line[iChar] == '\t':   #空白字符
            iChar += 1; continue
        elif line[iChar] == '#':            #行注释
            isLineComment = True
            lineType |= 2
        elif line[iChar:iChar+3] == "'''":  #单引号块注释
            if isBlockComment[0] or isBlockComment[1]:
                isBlockComment[0] = False
            else:
                isBlockComment[0] = True
            lineType |= 2; iChar += 2
        elif line[iChar:iChar+3] == '"""':  #双引号块注释
            if isBlockComment[0] or isBlockComment[1]:
                isBlockComment[1] = False
            else:
                isBlockComment[1] = True
            lineType |= 2; iChar += 2
        else:
            if isLineComment or isBlockComment[0] or isBlockComment[1]:
                lineType |= 2
            else:
                lineType |= 1
        iChar += 1

    return lineType   #Bitmap：0空行，1代码，2注释，3代码和注释


from cffi import FFI
CFuncObj, ffiBuilder = None, FFI()
def LoadCExtLib():
    try:
        global CFuncObj
        ffiBuilder.cdef('''
        unsigned int CalcLinesCh(char *line, unsigned char isBlockComment[2]);
        unsigned int CalcLinesPy(char *line, unsigned char isBlockComment[2]);
        ''')
        CFuncObj = ffiBuilder.dlopen('CalcLines.dll')
    except Exception: #不捕获系统退出(SystemExit)和键盘中断(KeyboardInterrupt)异常
        pass


def CalcLines(fileType, line, isBlockComment):
    try:
        bCmmtArr = ffiBuilder.new('unsigned char[2]', isBlockComment)
        if fileType is 'ch': #is(同一性运算符)判断对象标识(id)是否相同，较==更快
            lineType = CFuncObj.CalcLinesCh(line, bCmmtArr)
        else:
            lineType = CFuncObj.CalcLinesPy(line, bCmmtArr)

        isBlockComment[0] = True if bCmmtArr[0] else False
        isBlockComment[1] = True if bCmmtArr[1] else False
        #不能采用以下写法，否则本函数返回后isBlockComment列表内容仍为原值
        #isBlockComment = [True if i else False for i in bCmmtArr]
    except Exception, e:
        #print e; sys.exit()
        if fileType is 'ch':
            lineType = CalcLinesCh(line, isBlockComment)
        else:
            lineType = CalcLinesPy(line, isBlockComment)

    return lineType


def SafeDiv(dividend, divisor):
    if divisor: return float(dividend)/divisor
    elif dividend:       return -1
    else:                return 0

gProcFileNum = 0
def CountFileLines(filePath, isRawReport=True, isShortName=False):
    fileExt = os.path.splitext(filePath)
    if fileExt[1] == '.c' or fileExt[1] == '.h':
        fileType = 'ch'
    elif fileExt[1] == '.py': #==(比较运算符)判断对象值(value)是否相同
        fileType = 'py'
    else:
        return

    global gProcFileNum; gProcFileNum += 1
    #因无法判知输出是否通过命令行重定向至文件(sys.stdout未变，sys.argv不含">out")，
    #以下进度提示将换行写入输出文件内。假定代码文件数目为N，输出文件内将含N行进度信息。
    #目前只能利用重定向缺省只影响标准输出的特点，将进度信息由标准错误输出至控制台；
    #同时增加-o选项，以显式地区分标准输出和文件写入，降低使用者重定向的可能性。
    sys.stderr.write('%d files processed...\r'%gProcFileNum)

    isBlockComment = [False]*2  #或定义为全局变量，以保存上次值
    lineCountInfo = [0]*5       #[代码总行数, 代码行数, 注释行数, 空白行数, 注释率]
    with open(filePath, 'r') as file:
        for line in file:
            lineType = CalcLines(fileType, line.strip(), isBlockComment)
            lineCountInfo[0] += 1
            if   lineType == 0:  lineCountInfo[3] += 1
            elif lineType == 1:  lineCountInfo[1] += 1
            elif lineType == 2:  lineCountInfo[2] += 1
            elif lineType == 3:  lineCountInfo[1] += 1; lineCountInfo[2] += 1
            else:
                assert False, 'Unexpected lineType: %d(0~3)!' %lineType

    if isRawReport:
        global rawCountInfo
        rawCountInfo[:-1] = [x+y for x,y in zip(rawCountInfo[:-1], lineCountInfo[:-1])]
        rawCountInfo[-1] += 1
    elif isShortName:
        lineCountInfo[4] = SafeDiv(lineCountInfo[2], lineCountInfo[2]+lineCountInfo[1])
        detailCountInfo.append([os.path.basename(filePath), lineCountInfo])
    else:
        lineCountInfo[4] = SafeDiv(lineCountInfo[2], lineCountInfo[2]+lineCountInfo[1])
        detailCountInfo.append([filePath, lineCountInfo])


SORT_ORDER = (lambda x:x[0], False)
def SetSortArg(sortArg=None):
    global SORT_ORDER
    if not sortArg:
        return
    if any(s in sortArg for s in ('file', '0')): #条件宽松些
    #if sortArg in ('rfile', 'file', 'r0', '0'):
        keyFunc = lambda x:x[1][0]
    elif any(s in sortArg for s in ('code', '1')):
        keyFunc = lambda x:x[1][1]
    elif any(s in sortArg for s in ('cmmt', '2')):
        keyFunc = lambda x:x[1][2]
    elif any(s in sortArg for s in ('blan', '3')):
        keyFunc = lambda x:x[1][3]
    elif any(s in sortArg for s in ('ctpr', '4')):
        keyFunc = lambda x:x[1][4]
    elif any(s in sortArg for s in ('name', '5')):
        keyFunc = lambda x:x[0]
    else: #因argparse内已限制排序参数范围，此处也可用assert
        print >>sys.stderr, 'Unsupported sort order(%s)!' %sortArg
        return

    isReverse = sortArg[0]=='r' #False:升序(ascending); True:降序(decending)
    SORT_ORDER = (keyFunc, isReverse)

def ReportCounterInfo(isRawReport=True, stream=sys.stdout):
     #代码注释率 = 注释行 / (注释行+有效代码行)
    print >>stream, 'FileLines  CodeLines  CommentLines  BlankLines  CommentPercent  %s'\
          %(not isRawReport and 'FileName' or '')

    if isRawReport:
       print >>stream, '%-11d%-11d%-14d%-12d%-16.2f<Total:%d Code Files>' %(rawCountInfo[0],\
             rawCountInfo[1], rawCountInfo[2], rawCountInfo[3], \
             SafeDiv(rawCountInfo[2], rawCountInfo[2]+rawCountInfo[1]), rawCountInfo[4])
       return

    total = [0, 0, 0, 0]
    #对detailCountInfo排序。缺省按第一列元素(文件名)升序排序，以提高输出可读性。
    detailCountInfo.sort(key=SORT_ORDER[0], reverse=SORT_ORDER[1])
    for item in detailCountInfo:
        print >>stream, '%-11d%-11d%-14d%-12d%-16.2f%s' %(item[1][0], item[1][1], item[1][2], \
              item[1][3], item[1][4], item[0])
        total[0] += item[1][0]; total[1] += item[1][1]
        total[2] += item[1][2]; total[3] += item[1][3]
    print >>stream, '-' * 90  #输出90个负号(minus)或连字号(hyphen)
    print >>stream, '%-11d%-11d%-14d%-12d%-16.2f<Total:%d Code Files>' \
          %(total[0], total[1], total[2], total[3], \
          SafeDiv(total[2], total[2]+total[1]), len(detailCountInfo))


import argparse
def ParseCmdArgs(argv=sys.argv):
    parser = argparse.ArgumentParser(usage='%(prog)s [options] target',
                      description='Count lines in code files.')
    parser.add_argument('target', nargs='*',
           help='space-separated list of directories AND/OR files')
    parser.add_argument('-k', '--keep', action='store_true',
           help='do not walk down subdirectories')
    parser.add_argument('-d', '--detail', action='store_true',
           help='report counting result in detail')
    parser.add_argument('-b', '--basename', action='store_true',
           help='do not show file\'s full path')
##    sortWords = ['0', '1', '2', '3', '4', '5', 'file', 'code', 'cmmt', 'blan', 'ctpr', 'name']
##    parser.add_argument('-s', '--sort',
##        choices=[x+y for x in ['','r'] for y in sortWords],
##        help='sort order: {0,1,2,3,4,5} or {file,code,cmmt,blan,ctpr,name},' \
##             "prefix 'r' means sorting in reverse order")
    parser.add_argument('-s', '--sort',
           help='sort order: {0,1,2,3,4,5} or {file,code,cmmt,blan,ctpr,name}, ' \
             "prefix 'r' means sorting in reverse order")
    parser.add_argument('-o', '--out',
           help='save counting result in OUT')
    parser.add_argument('-c', '--cache', action='store_true',
           help='use cache to count faster(unreliable when files are modified)')
    parser.add_argument('-v', '--version', action='version',
           version='%(prog)s 3.0 by xywang')

    args = parser.parse_args()
    return (args.keep, args.detail, args.basename, args.sort, args.out, args.cache, args.target)


def ParseTargetList(targetList):
    fileList, dirList = [], []
    if targetList == []:
        targetList.append(os.getcwd())
    for item in targetList:
        if os.path.isfile(item):
            fileList.append(os.path.abspath(item))
        elif os.path.isdir(item):
            dirList.append(os.path.abspath(item))
        else:
            print >>sys.stderr, "'%s' is neither a file nor a directory!" %item
    return [fileList, dirList]


def CountDir(dirList, isKeep=False, isRawReport=True, isShortName=False):
    for dir in dirList:
        if isKeep:
            for file in os.listdir(dir):
                CountFileLines(os.path.join(dir, file), isRawReport, isShortName)
        else:
            for root, dirs, files in os.walk(dir):
               for file in files:
                  CountFileLines(os.path.join(root, file), isRawReport, isShortName)


def CountFile(fileList, isRawReport=True, isShortName=False):
    for file in fileList:
        CountFileLines(file, isRawReport, isShortName)


def LineCounter(isKeep=False, isRawReport=True, isShortName=False, targetList=[]):
    fileList, dirList = ParseTargetList(targetList)
    if fileList != []:
        CountFile(fileList, isRawReport, isShortName)
    if dirList != []:
        CountDir(dirList, isKeep, isRawReport, isShortName)



CACHE_FILE = 'Counter.dump'
CACHE_DUMPER, CACHE_GEN = None, None

from json import dump, JSONDecoder
def CounterDump(data):
    global CACHE_DUMPER
    if CACHE_DUMPER == None:
        CACHE_DUMPER = open(CACHE_FILE, 'w')
    dump(data, CACHE_DUMPER)

def ParseJson(jsonData):
    endPos = 0
    while True:
        jsonData = jsonData[endPos:].lstrip()
        try:
            pyObj, endPos = JSONDecoder().raw_decode(jsonData)
            yield pyObj
        except ValueError:
            break

def CounterLoad():
    global CACHE_GEN
    if CACHE_GEN == None:
        CACHE_GEN = ParseJson(open(CACHE_FILE, 'r').read())

    try:
        return next(CACHE_GEN)
    except StopIteration, e:
        return []


def shouldUseCache(keep, detail, basename, cache, target):
    if not cache:  #未指定启用缓存
        return False

    try:
        (_keep, _detail, _basename, _target) = CounterLoad()
    except (IOError, EOFError, ValueError): #缓存文件不存在或内容为空或不合法
        return False

    if keep == _keep and detail == _detail and basename == _basename \
       and sorted(target) == sorted(_target):
        return True
    else:
        return False



def main():
    global gIsStdout, rawCountInfo, detailCountInfo
    (keep, detail, basename, sort, out, cache, target) = ParseCmdArgs()
    stream = sys.stdout if not out else open(out, 'w')
    SetSortArg(sort); LoadCExtLib()
    cacheUsed = shouldUseCache(keep, detail, basename, cache, target)
    if cacheUsed:
        try:
            (rawCountInfo, detailCountInfo) = CounterLoad()
        except (EOFError, ValueError), e: #不太可能出现
            print >>sys.stderr, 'Unexpected Cache Corruption(%s), Try Counting Directly.'%e
            LineCounter(keep, not detail, basename, target)
    else:
       LineCounter(keep, not detail, basename, target)

    ReportCounterInfo(not detail, stream)
    CounterDump((keep, detail, basename, target))
    CounterDump((rawCountInfo, detailCountInfo))




if __name__ == '__main__':
    from time import clock
    startTime = clock()
    main()
    endTime = clock()
    print >>sys.stderr, 'Time Elasped: %.2f sec.' %(endTime-startTime)
