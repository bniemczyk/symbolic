# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# Using SyMath for symbolic execution of assembly languages
# =========================================================
# 
# At it's core, symath allows a programming paradigm called _symbolic programming_.
# Even though symbolic programming is often associated with mathematical programming, this
# is not always the case, and this tutorial will walk you through using symath to create
# a symbolic execution of a small subset of the x86 assembly language.

# <markdowncell>

# Initialization of SyMath
# ------------------------

# <codecell>

from symath import symbols, wilds, WildResults

# <markdowncell>

# Registers and Expressions involving them
# ----------------------------------------

# <markdowncell>

# ### Creating symbols for registers

# <codecell>

registers = (eax,ebx,ecx,edx,esi,edi,esp,ebp,eflags) = symbols('eax ebx ecx edx esi edi esp ebp eflags')
print registers

# <markdowncell>

# Notice that symbols will always equal themselves, but never another symbol

# <codecell>

print eax == eax

# <codecell>

print eax == ebx

# <codecell>

print eax == symbols('eax')

# <markdowncell>

# ### Arithmetic and Bit operations
# 
# Running a arithmetic or bit operation with a symbolic operand returns a symbolic result instead of numerical.

# <codecell>

print eax + ebx

# <codecell>

print eax & ebx

# <markdowncell>

# Symath can also include numerical values in symbolic expressions

# <codecell>

print eax + 4

# <codecell>

expression = eax + 0
print expression

# <markdowncell>

# SyMath knows many _simplification_ rules, which can be applied by calling .simplify()

# <codecell>

print expression.simplify()

# <codecell>

print (ebx ^ ebx).simplify()

# <codecell>

print (eax & ecx & eax | ebx).simplify()

# <markdowncell>

# It's important to note that .simplify() may change the order of operands, or even change the operations _but only when it does not matter mathematically_ even if it does not simplify
# the expression

# <codecell>

print (ecx & eax).simplify()

# <codecell>

print (ecx - ebx).simplify()

# <markdowncell>

# It does this so that it is easy to put an expression in canonical form which allows easy equality tests

# <codecell>

print (ecx & eax) == (eax & ecx)

# <codecell>

print (ecx & eax).simplify() == (eax & ecx).simplify()

# <markdowncell>

# We can also replace parts of an expression that we know the value of

# <codecell>

expression = ebx + ecx - (edx & (edi | esi))
print expression

# <codecell>

expression = expression.substitute({edx: 0})
print expression

# <codecell>

expression = expression.simplify()
print expression

# <markdowncell>

# Symbols can also be used as functions inside an expression and this is how we will represent assembly instructions (you can automatically get symbolic representations of instructions from IDA using the seperate [Revtools package](http://github.com/bniemczyk/revtools)

# <codecell>

MOV = symbols('MOV')
print MOV(eax, ebx)

# <markdowncell>

# Executing Instructions
# ----------------------
# 
# ### Representing machine state
# 
# 
# We need to represent the state of registers and the state of memory in a machine between execution of each instruction, before we decide how to do this though
# we should explore how we will *point* to specific addresses (that we do not know the actual address of).
# 
# One way to do this is to initialize each register to some initial value, and then represent our memory references as:
# 
# MEMORY(SIZE, _some calculation involving initial values_)

# <codecell>

# machine_state can get large, so it's better to pretty print it
import pprint
pp = pprint.PrettyPrinter()

MEMORY = symbols('MEMORY')

def build_initial_machine_state():
    return {
                 esp: symbols('initial_esp'),
                 ebp: symbols('initial_ebp'),
                 eax: symbols('initial_eax'),
                 ebx: symbols('initial_ebx'),
                 ecx: symbols('initial_ecx'),
                 edx: symbols('initial_edx'),
                 edi: symbols('initial_edi'),
                 esi: symbols('initial_esi')
                 }

machine_state = build_initial_machine_state()

pp.pprint(machine_state)

# <markdowncell>

# As we discover (or reference) values in memory, we want to update our machine_state variable
# 
# _push(edx)_
# 
# should modify the value of esp and also add a new MEMORY value.  Manually this would be done as the code below shows.

# <codecell>

# update the value of esp
machine_state[esp] = (machine_state[esp] - 4).simplify()

# set the location in memory pointed to by the new value of esp
machine_state[MEMORY(4, machine_state[esp])] = machine_state[edi]

# print the machine state
pp.pprint(machine_state)

# <markdowncell>

# ### Pattern Matching
# 
# Obviously we don't want to execute instructions manually as above but instead write code that can execute any instruction given a machine state automatically.  This is much easier to do with a concept called _pattern matching_.
# 
# Pattern matching allows you to determine if a symbolic expression matches a pattern an (optionally) extract values from it, similar to using a regular expression on text.  To include *wildcards* you need to create an instance of a wild with the wilds() function and to capture the values of wilds you need to use the WildResults class.  It is easiest to show with some examples.

# <codecell>

a,b = wilds("a b") # used as wildcard placeholders, these will match any subexpression
results = WildResults() # used to store the subexpression results of pattern matches

expression = MOV(eax, ebx)
print expression

# <codecell>

print expression.match(MOV(eax, ebx)) # it will match because they are exactly the same

# <codecell>

print expression.match(MOV(eax, ecx)) # will not match because they differ

# <codecell>

print expression.match(MOV(eax, a)) # will match because a is a wild and will match any subexpression

# <codecell>

expression.match(MOV(eax, a), results) # results now holds the values matched by wilds
print results

# <codecell>

print results.a # you can also access the values of wilds from results with the dot notation

# <markdowncell>

# ### Executing a single instruction
# 
# With pattern matching in hand, it's pretty easy now to write a funcion that takes a symbolic instruction and a machine state, then returns a new machine state

# <codecell>

from copy import copy

instructions = (MOV, ADD, SUB) = symbols('MOV ADD SUB')

def execute_sym_instruction(instruction, machine_state=None):
    
    # if now machine state was passed, start with a clean one
    if machine_state == None:
        machine_state = build_initial_machine_state()
    
    # otherwise make a copy
    else:
        machine_state = copy(machine_state)
        
    # src and dst operands are extracted during instruction matching
    src,dst,opsize = wilds('src dst opsize')
    operands = WildResults()
    
    if instruction.match(MOV(dst, src), operands):
        machine_state[operands.dst] = machine_state[operands.src]
        
    elif instruction.match(ADD(dst, src), operands):
        machine_state[operands.dst] = (machine_state[operands.dst] + machine_state[operands.src]).simplify()
        machine_state[eflags] = machine_state[operands.dst]
        
    elif instruction.match(SUB(dst, src), operands):
        machine_state[operands.dst] = (machine_state[operands.dst] - machine_state[operands.src]).simplify()
        machine_state[eflags] = machine_state[operands.dst]
    
    # TODO: add the rest of the x86 instructions
        
    else:
        raise Exception("Unknown instruction passed: %s" % (instruction,))
        
    return machine_state

# <codecell>

# a quick example
execute_sym_instruction(SUB(eax, ebx))

# <markdowncell>

# ### Building a flexible instruction handling class
# 
# The above scheme (lots of hard-coded if tests) works, but is not ideal.  We would really like to be able to dynamically add handlers for different patterns, so that's it is easy to customize
# at runtime.  This makes it so that you can set the effects of specific function calls etc... without having to execute the full function.
# 
# Doing it this way will also allow us to specialize instructions later when we do things like add support for the smaller registers (ax,al,ah,etc...)

# <codecell>

from collections import deque

class IExecuter(object):
    
    def __init__(self):
        self._handlers = deque()
        
    def add_handler(self, pattern, handler):
        '''
        Adds a handler

        params:
            pattern - the pattern (or lambda that takes a WildResults and returns a boolean) this handles, the last register handler that matches will be what is called
            handler - a function that takes arguments (machine_state, operands)
        '''
        
        self._handlers.pushfront((pattern, handler))
        
    def execute(self, instruction, machine_state=None):
        
        # make sure our handlers do not clobber each other
        if machine_state == None:
            machine_state = build_initial_machine_state()
        else:
            machine_state = copy(machine_state)
            
        operands = WildResults()
            
        # loop through handlers and execute the first one that matches
        for h in self._handlers:
            
            tester = h[0]
            if type(tester) == type(lambda x: x):
                handles = tester(operands)
            else:
                handles = tester.match(instruction, operands)
                
            if handles:
                return h[1](machine_state, operands)
            
        # no handler was found, so abort
        raise Exception("No handler found for %s" % (instruction,))

