#!/usr/bin/env python

# Yue Chen, Matt Clarke-Lauer
# Northeastern University

import xml.etree.ElementTree as ET
import os,sys

TEST_NUMBER = 8

# Compare if the two XMLs are equal
def compareET(et1, et2):
    same = True
    if et1.tag == et2.tag and\
    et1.attrib == et2.attrib and\
    len(et1) == len(et2):
        index = 0
        same = True
        while index < len(et1):
            same = same and compareET(et1[index],et2[index])
            index += 1
    else:
        same = False
    return same

# Run the test
def test(source,result):
    tmp = os.popen("./evaluate < " + './test/'+ source + '.xml').read()
    tmp1 = os.popen("cat " + './test/' + result + '_result.xml').read()
    root = ET.fromstring(tmp)
    root1 = ET.fromstring(tmp1)
    return compareET(root, root1)

try:
    for i in xrange(1,TEST_NUMBER+1):
        if not test(str(i), str(i)):
            print 'Evaluation of ' + str(i) + '.xml fails.'
            sys.exit(1)
    print "All tests are successful!"
except Exception:
    print 'ERROR'
