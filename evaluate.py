#!/usr/bin/env python

# Yue Chen, Matt Clarke-Lauer
# Northeastern University

import xml.etree.ElementTree as ET
import sys, copy
from select import select

# -----------------------------------------------------------------------------
# Function map:
#
# |-- main_loop
#    |-- evaluate (pop, pop mt)
#       |-- process (push, push1)
#       |-- assign (assign)
#       |-- if0 (if true, if false)
#       |-- while0 (while0)
#          |-- expr (ref, add)
#          |-- trans
#          |-- ref
#          |-- replace
# |-- raise_error
# |-- fatal_error
# |-- check_number
# |-- ReadXmlFromStdIn
# |-- PrintXMLToStdout
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# CEK Statement Processing Functions
# -----------------------------------------------------------------------------

# Main loop: If it is not the final state, continue the loop
def main_loop():
    global current, def_stack, ctrl_stack
    while(not (current.tag == 'void' \
               and len(ctrl_stack) == 1 \
               and ctrl_stack[-1] == empty)):
        if current.tag == 'void':
            if ctrl_stack[-1]:
                # Pop from the queue in the control stack
                current = ctrl_stack[-1].pop(0)
            else:
                # Pop mt
                def_stack.pop()
                ctrl_stack.pop(-1)
        else:
            evaluate(current)

# Main evaluation procedure
def evaluate(element):
    if element.tag == 'block':
        block(element)
    elif element.tag == 'assign':
        assign(element)
    elif element.tag == 'if0':
        if0(element)
    elif element.tag == 'while0':
        while0(element)
    else:
        raise_error('ERROR: evaluate error')

# Process "block"
def block(block):
    global current
    # Initialize signal
    signal = 0
    temp_queue = []
    for child in block:
        # Declarations could be empty
        if child.tag == 'declarations':
            d = trans(child)
            def_stack.append(d)
        elif child.tag == 'assign' or \
             child.tag == 'if0' or \
             child.tag == 'while0' or\
             child.tag == 'block':
            if signal == 0:
                current = child
                signal = 1
            else:
                # Push transition
                temp_queue.append(copy.deepcopy(child))
                if signal != 2:
                    ctrl_stack.append(temp_queue)
                signal = 2
    if signal == 1:
        # Push1 transition
        ctrl_stack.append(empty)

# Process "assign"
def assign(element):
    global current, not_finish
    not_finish = 1
    expr(element[1])
    if not_finish == 0:
        return
    else:
        # Assign transition
        var = element[0].attrib['label']
        for d in reversed(def_stack):
            if var in d:
                val = element[1].attrib['val']
                if check_number(val):
                    d[var] = float(val)
                    break
                else:
                    raise_error('ERROR: n is not a number')
        current = ET.Element('void')

# Process "if0"
def if0(element):
    global current, not_finish
    not_finish = 1
    expr(element[0])
    if not_finish == 0:
        return
    else:
        val = element[0].attrib['val']
        if check_number(val):
            value = float(element[0].attrib['val'])
        else:
            raise_error('ERROR: n is not a number')
        if value == 0:
            current = element[1]
        else:
            current = element[2]

# Process "while0"
def while0(element):
    global current
    # Here we generate a new object
    temp = copy.deepcopy(element)
    new = ET.Element('if0')
    new.append(copy.deepcopy(element[0]))
    sub = ET.SubElement(new,'block')
    ET.SubElement(sub,'declarations')
    for i in xrange(1,len(temp)):
       sub.append(temp[i])
    sub.append(temp)
    sub = ET.SubElement(new,'void')
    current = new


# -----------------------------------------------------------------------------
# CEK Expression Processing Function 
# -----------------------------------------------------------------------------

# To evaluate the expression, ONE step each time
def expr(e):
    global not_finish
    if not_finish:
        # If this is a variable, find its value
        if e.tag == 'var':
            var = e.attrib['label']
            e.clear()
            e.tag = 'num'
            # Ref transition
            e.set('val',str(ref(var)))
            not_finish = 0
            return
        # If this is a number, just return
        elif e.tag == 'num':
            return
        # If this is an addition, do it when two of the parameters
        # are both numbers
        elif e.tag == 'pls':
            expr(e[0])
            expr(e[1])
            if not_finish and e[0].tag != 'pls' and e[1].tag != 'pls':
                # Add transition
                val1 = e[0].attrib['val']; val2 = e[1].attrib['val']
                if check_number(val1) and check_number(val2):
                    result = float(val1) + float(val2)
                    e.clear()
                    e.tag = 'num'
                    e.set('val',str(result))
                    not_finish = 0
                    return
                else:
                    raise_error('ERROR: n is not a number')
        else:
            raise_error('ERROR: expr error')


# -----------------------------------------------------------------------------
# Auxiliary Declaration-related Functions
# -----------------------------------------------------------------------------

# Translate declarations into the dictionary format
def trans(decl):
    queue = []
    d = {}
    for i in decl:
        if i.tag == 'var':
            queue.append(i.attrib['label'])
        elif i.tag == 'num':
            var = queue.pop(0)
            val = i.attrib['val']
            if check_number(val):
                value = float(val)
                d[var] = value
            else:
                raise_error('ERROR: n is not a number')
        else:
            raise_error('ERROR: trans error')
    return d

# Find the value of variables in the current stack
def ref(var):
    global def_stack
    for d in reversed(def_stack):
        if var in d:
            return d[var]
    # If cannot find the value, there are free variables
    raise_error('ERROR: Free variable!')

# Replace the variables in the XML object
def replace(child):
    queue = []
    if child.tag == 'declarations':
        for i in child:
            if i.tag == 'var':
                var = i.attrib['label']
                queue.append(var)
            elif i.tag == 'num':
                var = queue.pop(0)
                num = ref(var)
                num = ('%f' % num).rstrip('0').rstrip('.')
                i.set('val',str(num))


# -----------------------------------------------------------------------------
# Auxiliary Error/Debugging Functions
# -----------------------------------------------------------------------------

# Check if it is a number
def check_number(string):
    try:
        n = float(string)
        if n == "nan" or n=="inf" or n=="-inf":
            return False
    except ValueError:
        return False
    return True

# Raises error and prints message
def raise_error(message = ''):
    print message
    raise Exception("ERROR")
    
# Prints message and exits program
def fatal_error(message = ''):
    print message
    sys.exit(1)


# -----------------------------------------------------------------------------
# XML Functions
# -----------------------------------------------------------------------------

# Read XML from stdin
def ReadXmlFromStdIn():
    try:
        # Validate input format
        if len(sys.argv) >= 2:
            print 'USAGE: "$ ./evaluate < in > out"'
            sys.exit(1)

        # Input validation, in case of no input
        timeout = 0
        rlist, _, _ = select([sys.stdin], [], [], timeout)
        if rlist:
            # Read file into a text string
            text = sys.stdin.read()
        else:
            raise_error('ERROR: No input')
    except Exception:
        print 'USAGE: "$ ./evaluate < in > out"'
        sys.exit(1)
    
    try:
        return ET.fromstring(text)
    except:
        fatal_error('ERROR: Wrong XML format')

# Print XML 
def PrintXMLToStdout(root):
    try:
        output = ET.Element('block')
        output.append(root[0])
    except:
        print 'ERROR: Replacement error'

    try:
        # Generate XML format output
        sys.stdout.write( ET.tostring(output, encoding="us-ascii").strip() )
    except:
        print 'ERROR: Output error'


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

# Main Program: 
#   Read xml and evalute using CEK machine
#   Once final state is reached print to stdout
if __name__ == '__main__':

    # Read xml file from stdin
    root = ReadXmlFromStdIn() 

    # Initialize CEK registers
    current = root      # Control String
    def_stack = []      # Definition stack
    ctrl_stack = []     # Control stack
    
    # Initialize empty list for comparisons
    empty = []          # Empty list
    
    # A signal for controlling expression evaluation
    not_finish = 0
    
    # Evaluate XML input    
    try:
        # Check the configuration of root
        if len(root) > 1:
            main_loop()
            # Replace the variables in the XML-format object with the ones
            # in def_stack, and generate the output block
            replace(root[0])
            PrintXMLToStdout(root)
        # Empty block
        elif len(root) == 0:
            fatal_error('ERROR: Empty block')
        # Only have declarations
        elif len(root) == 1:
            PrintXMLToStdout(root)
            sys.exit(1)
    except Exception:
        fatal_error('ERROR: Main loop error')
