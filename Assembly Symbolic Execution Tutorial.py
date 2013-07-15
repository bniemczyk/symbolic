# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# Using SyMath for symbolic execution of assembly languages
# =========================================================
# 
# At it's core, symath allows a programming paradigm called _symbolic programming_.
# Even though symbolic programming is often associated with mathematical programming, this
# is not always the case.  This tutorial will walk you through using symath to treat x86 assembly
# language as symbolic data and 'execute' it without hard values.

# <markdowncell>

# Initialization of SyMath
# ------------------------

# <codecell>

import symath
from symath import symbols, wilds, WildResults # these will be used a lot

# <markdowncell>

# You can set symath to display integers in hex if you would like as well, this is nice when working with x86 code

# <codecell>

symath.Number.IFORMAT = hex

# <markdowncell>

# Registers and Expressions involving them
# ----------------------------------------

# <markdowncell>

# ### Creating symbols for registers

# <codecell>

registers = (eax,ebx,ecx,edx,esi,edi,esp,ebp,eflags) = symbols('eax ebx ecx edx esi edi esp ebp eflags')
registers

# <markdowncell>

# Notice that symbols will always equal themselves, but never another symbol

# <codecell>

eax == eax

# <codecell>

eax == ebx

# <codecell>

eax == symbols('eax')

# <markdowncell>

# ### Arithmetic and Bit operations
# 
# Running a arithmetic or bit operation with a symbolic operand returns a symbolic result instead of numerical.

# <codecell>

eax + ebx

# <codecell>

eax & ebx

# <markdowncell>

# Symath can also include numerical values in symbolic expressions

# <codecell>

eax + 4

# <codecell>

expression = eax + 0
expression

# <markdowncell>

# SyMath knows many _simplification_ rules, which can be applied by calling .simplify()

# <codecell>

expression.simplify()

# <codecell>

(ebx ^ ebx).simplify()

# <codecell>

(eax & ecx & eax | ebx).simplify()

# <markdowncell>

# It's important to note that .simplify() may change the order of operands, or even change the operations _but only when it does not matter mathematically_ even if it does not simplify
# the expression

# <codecell>

(ecx & eax).simplify()

# <codecell>

(ecx - ebx).simplify()

# <markdowncell>

# It does this so that it is easy to put an expression in canonical form which allows easy equality tests

# <codecell>

(ecx & eax) == (eax & ecx)

# <codecell>

(ecx & eax).simplify() == (eax & ecx).simplify()

# <markdowncell>

# We can also replace parts of an expression that we know the value of

# <codecell>

expression = ebx + ecx - (edx & (edi | esi))
expression

# <codecell>

expression = expression.substitute({edx: 0})
expression

# <codecell>

expression = expression.simplify()
expression

# <markdowncell>

# Symbols can also be used as functions inside an expression and this is how we will represent assembly instructions (you can automatically get symbolic representations of instructions from IDA using the seperate [Revtools package](http://github.com/bniemczyk/revtools)

# <codecell>

MOV = symbols('MOV')
MOV(eax, ebx)

# <markdowncell>

# ### TODO: Indexing expressions

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

machine_state

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
machine_state

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
# With pattern matching in hand, it's pretty easy now to write a funcion that takes a symbolic instruction and a machine state, then returns a new machine state.
# 
# The only real trick is if one of the operands is a MEMORY expression, we need to make sure we replace anything in it with the values that we have in machine_state

# <codecell>

from copy import copy

instructions = (MOV, ADD, SUB, XOR) = symbols('MOV ADD SUB XOR')

def execute_sym_instruction(instruction, machine_state=None):
    
    # if now machine state was passed, start with a clean one
    if machine_state == None:
        machine_state = build_initial_machine_state()
    
    # otherwise make a copy
    else:
        machine_state = copy(machine_state)
        
    # src and dst operands are extracted during instruction matching
    src,dst,opsize,randominst = wilds('src dst opsize randominst')
    operands = WildResults()
    
    # resolve MEMORY() expressions
    if instruction.match(randominst(MEMORY(opsize, dst), src), operands):
        instruction = operands.randominst(MEMORY(operands.opsize, operands.dst.substitute(machine_state)), operands.src)
    
    if instruction.match(randominst(dst, MEMORY(opsize, src)), operands):
        instruction = operands.randominst(operands.dst, MEMORY(operands.opsize, operands.src.substitute(machine_state)))
    
    # do pattern matching and execute correct logic
    if instruction.match(MOV(dst, src), operands):
        _s = machine_state[operands.src] if operands.src in machine_state else operands.src
        machine_state[operands.dst] = _s
        
    elif instruction.match(ADD(dst, src), operands):
        _s = machine_state[operands.src] if operands.src in machine_state else operands.src
        _d = machine_state[operands.dst] if operands.dst in machine_state else operands.dst
        machine_state[operands.dst] = (_d + _s).simplify()
        machine_state[eflags] = machine_state[operands.dst]
        
    elif instruction.match(SUB(dst, src), operands):
        _s = machine_state[operands.src] if operands.src in machine_state else operands.src
        _d = machine_state[operands.dst] if operands.dst in machine_state else operands.dst
        machine_state[operands.dst] = (_d - _s).simplify()
        machine_state[eflags] = machine_state[operands.dst]
        
    elif instruction.match(XOR(dst, src), operands):
        _s = machine_state[operands.src] if operands.src in machine_state else operands.src
        _d = machine_state[operands.dst] if operands.dst in machine_state else operands.dst
        machine_state[operands.dst] = (_d ^ _s).simplify()
        machine_state[eflags] = machine_state[operands.dst]
    
    # TODO: add the rest of the x86 instructions, of course we won't do this because we have a better
    # scheme later
        
    else:
        raise Exception("Unknown instruction passed: %s" % (instruction,))
        
    return machine_state

# <codecell>

# a quick example
execute_sym_instruction(SUB(eax, ebx))

# <markdowncell>

# ### Executing a sequence of instructions
# 
# Executing a list of instructions is as simple as executing each instruction one by one and keeping the modifications to the machine state

# <codecell>

def execute_sym_instruction_list(insts, machine_state=None):
    
    for inst in insts:
        machine_state = execute_sym_instruction(inst, machine_state)
        
    return machine_state

# <codecell>

XOR,MOV = symbols('XOR MOV')
_sample_insts = [
                 XOR(eax, eax),
                 ADD(ecx, 0x4),
                 MOV(MEMORY(0x4, ecx), eax),
                 MOV(ebx, MEMORY(4, ecx))
                 ]

_state = execute_sym_instruction_list(_sample_insts)
_state

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
            handler - a function that takes arguments (instruction, operands [to be populated])
        '''
        
        self._handlers.appendleft((pattern, handler))
        
    def execute_single_instruction(self, instruction, machine_state=None):
        
        # make sure our handlers do not clobber each other
        if machine_state == None:
            machine_state = build_initial_machine_state()
        else:
            machine_state = copy(machine_state)
            
        operands = WildResults()
            
        # loop through handlers and execute the first one that matches
        for h in self._handlers:
            
            tester = h[0]
            handles = False
            
            if type(tester) == type(lambda x: x):
                handles = tester(instruction, operands)
            else:
                handles = instruction.match(tester, operands)
                
            if handles:
                return h[1](machine_state, operands)
            
        # no handler was found, so abort
        raise Exception("No handler found for %s" % (instruction,))
        
    def execute_instruction_list(self, insts, machine_state=None):
        for inst in insts:
            machine_state = self.execute_single_instruction(inst, machine_state)
        
        return machine_state

# <markdowncell>

# #### MOV handler
# TODO: description

# <codecell>

MOV = symbols('MOV')

def add_x86_32bit_mov_handler(iexecuter):
    src,dst = wilds('src dst')
    handler_ptrn = MOV(dst, src)
    
    def _handler(machine_state, operands):
        w,n = wilds("w n")
        for k in operands:
            if operands[k].match(MEMORY(n, w)):
                operands[k] = MEMORY(operands[k][1], operands[k][2].substitute(machine_state))
                
        _s = machine_state[operands.src] if operands.src in machine_state else operands.src
        machine_state[operands.dst] = _s
        return machine_state
        
    iexecuter.add_handler(handler_ptrn, _handler)

# <markdowncell>

# #### LEA handler
# TODO: description

# <codecell>

LEA = symbols('LEA')

def add_x86_32bit_lea_handler(iexecuter):
    src,dst = wilds('src dst')
    handler_ptrn = lambda inst, operands: inst.match(LEA(dst, MEMORY(4, src)), operands) and operands.dst in registers
    
    def _handler(machine_state, operands):
        _s = operands.src.substitute(machine_state).simplify()
        machine_state[operands.dst] = _s
        return machine_state
    
    iexecuter.add_handler(handler_ptrn, _handler)
    

# <markdowncell>

# #### Two operand 32-bit arithmetic instruction handlers
# 
# Many arithmetic instructions in the form of
# 
# _INST dest, src_
# 
# perform some arithmetic on it's operands and then update the destination and EFLAGS registers.  We can generalize this behaviour.  Right now we will only work with 32 bit registers because smaller registers require special handling due to the fact that they clobber parts of the larger registers.

# <codecell>

arithmetic_instructions = (ADD,SUB,MUL,IMUL,DIV,IDIV,AND,OR,XOR) = symbols('ADD SUB MUL IMUL DIV IDIV AND OR XOR')

def add_x86_32bit_arithmetic_handlers(iexecuter):
    
    def build_handler(instruction, symoperator=None):
        src,dst = wilds('src dst')
        handler_ptrn = instruction(dst, src) # build the pattern to match
        
        def _handler(machine_state, operands): # our actual handler
            
            # update the operands MEMORY references
            w,n = wilds('w n')
            for k in operands:
                if operands[k].match(MEMORY(n, w)):
                    operands[k] = MEMORY(operands[k][1], operands[k][2].substitute(machine_state))
            
            # if we know the value of either operand, grab it
            subbedops = WildResults()
            subbedops['src'] = machine_state[operands.src] if operands.src in machine_state else operands.src
            subbedops['dst'] = machine_state[operands.dst] if operands.dst in machine_state else operands.dst
            
            # run the provided function
            rslt = symoperator(subbedops)
            rslt = rslt.simplify()
            
            # update machine state and return
            machine_state[operands.dst] = rslt
            machine_state[eflags] = rslt
            return machine_state
            
        return (handler_ptrn, _handler)
    
    iexecuter.add_handler(*build_handler(ADD, lambda r: r.dst + r.src))
    iexecuter.add_handler(*build_handler(SUB, lambda r: r.dst - r.src))
    iexecuter.add_handler(*build_handler(MUL, lambda r: r.dst * r.src))
    iexecuter.add_handler(*build_handler(IMUL, lambda r: r.dst * r.src))
    iexecuter.add_handler(*build_handler(DIV, lambda r: r.dst / r.src))
    iexecuter.add_handler(*build_handler(IDIV, lambda r: r.dst / r.src))
    iexecuter.add_handler(*build_handler(AND, lambda r: r.dst & r.src))
    iexecuter.add_handler(*build_handler(OR, lambda r: r.dst | r.src))
    iexecuter.add_handler(*build_handler(XOR, lambda r: r.dst ^ r.src))

# <markdowncell>

# #### Inc and Dec handlers

# <codecell>

INC,DEC = symbols('INC DEC')

def add_x86_32bit_inc_dec_handler(iexec):
    src, w, n = wilds('src w n')
            
    def _inc_handler(machine_state, operands):
        if operands.src.match(MEMORY(n, w)):
            operands['src'] = MEMORY(operands.src[1], operands.src[2].substitute(machine_state))
            
        _s = machine_state[operands.src] if operands.src in machine_state else operands.src
        machine_state[operands.src] = (_s + 1).simplify()
        return machine_state
    
    iexec.add_handler(INC(src), _inc_handler)
    
    def _dec_handler(machine_state, operands):
        if operands.src.match(MEMORY(n, w)):
            operands['src'] = MEMORY(operands.src[1], operands.src[2].substitute(machine_state))
            
        _s = machine_state[operands.src] if operands.src in machine_state else operands.src
        machine_state[operands.src] = (_s - 1).simplify()
        return machine_state
    
    iexec.add_handler(DEC(src), _dec_handler)

# <markdowncell>

# #### Stack operations
# TODO

# <markdowncell>

# #### CALL handler
# 
# TODO

# <markdowncell>

# #### BRANCH instruction handlers
# 
# TODO:
# 
# notes - add CONSTRAINT(address) registers to machine_state

# <markdowncell>

# ### Creating an IExecuter factory and using it
# 
# It's easy to wrap up our add_*_handler functions into a factory method so that we do not have
# to call them by hand repeatedly

# <codecell>

def executer_x86_factory():
    iexec = IExecuter()
    add_x86_32bit_mov_handler(iexec)
    add_x86_32bit_lea_handler(iexec)
    add_x86_32bit_arithmetic_handlers(iexec)
    add_x86_32bit_inc_dec_handler(iexec)
    return iexec

# <markdowncell>

# #### A quick test run of what we have so far

# <codecell>

_sample_insts = [
                 XOR(eax, eax), # set eax to 0
                 LEA(eax, MEMORY(0x4, eax + 0xff)), # a common trick used by compilers for quick arithmetic
                 DEC(eax), # eax should now be 0xfe
                 ADD(ecx, 0x4), # ecx is it's original value + 4
                 MOV(MEMORY(0x4, ecx), eax),
                 MOV(edx, ecx), # copy ecx to edx
                 MOV(ebx, MEMORY(0x4, edx)), # ebx is now equal to eax
                 INC(ebx), INC(ebx), # add 2 to ebx, setting it to 0x100
                 AND(ebx, 0xff) # clear all but the bottom byte of ebx, effectively setting it to 0
                 ]

# now run the sample instructions
iexec = executer_x86_factory()
iexec.execute_instruction_list(_sample_insts)

# <markdowncell>

# Note that ebx is correctly 0, even though it had to go through multiple arithmetic operations and memory accesses that were indexed by different registers.

# <markdowncell>

# Selecting Interesting instruction sequences to execute
# ------------------------------------------------------
# 
# TODO

