from pickle import *
import json
from tkinter.filedialog import askopenfilename
from dec2ter import *
from ter2dec import *
from log import Log

class Equation:
    def __init__(self, system, arguments, destinations):
        self.system = system
        self.arguments = arguments
        self.destinations = destinations


# Microgate = few inputs, 1 output, 1 equation, hard coded
MICROGATES = {
    "NOT": [2,1,0],
    "NNOT": [2,1,0],
    "PNOT": [2,1,0],
    "NCONS": [[2,1,1],
              [1,1,1],
              [1,1,0]],
    "NANY": [[2,2,1],
             [2,1,0],
             [1,0,0]],
    "NAND": [[2,2,2],
             [2,1,1],
             [2,1,0]],
    "NOR": [[2,1,0],
            [1,1,0],
            [0,0,0]],
    "BI_NOT": [1,2,1],
    "BI_NAND": [[2,2,2],
                [2,2,2],
                [2,2,1]],
    "BI_NOR": [[2,2,1],
               [2,2,1],
               [1,1,1]]
}

# Microsystem = few inputs, few output, many equations, hard coded & generated
MICROSYSTEMS = {
    "AND": {
        "nbrstate": 4,
        "nbrinput": 2,
        "nbroutput": 1,
        "equations": [ # 2 layers
            Equation("NAND", [0,1], [2]),
            Equation("NOT", [2], [3])
        ]
    },
    "CONS": {
        "nbrstate": 4,
        "nbrinput": 2,
        "nbroutput": 1,
        "equations": [ # 2 layers
            Equation("NCONS", [0,1], [2]),
            Equation("NOT", [2], [3])
        ]
    },
    "OR": {
        "nbrstate": 4,
        "nbrinput": 2,
        "nbroutput": 1,
        "equations": [ # 2 layers
            Equation("NOR", [0,1], [2]),
            Equation("NOT", [2], [3])
        ]
    },
    "ANY": {
        "nbrstate": 4,
        "nbrinput": 2,
        "nbroutput": 1,
        "equations": [ # 2 layers
            Equation("NANY", [0,1], [2]),
            Equation("NOT", [2], [3])
        ]
    },
    "MUL": {
        "nbrstate": 6,
        "nbrinput": 2,
        "nbroutput": 1,
        "equations": [ # 4 layers
            Equation("NAND", [0,1], [2]),
            Equation("NOR", [0,1], [3]),
            Equation("NOT", [3], [4]),
            Equation("NAND", [2,4], [5])
        ]
    },
    "NMUL": {
        "nbrstate": 6,
        "nbrinput": 2,
        "nbroutput": 1,
        "equations": [ # 4 layers
            Equation("NOR", [0,1], [2]),
            Equation("NAND", [0,1], [3]),
            Equation("NOT", [3], [4]),
            Equation("NOR", [2,4], [5])
        ]
    },
    "SUM": {
        "nbrstate": 9,
        "nbrinput": 2,
        "nbroutput": 1,
        "equations": [ # 4 layers
            Equation("NANY", [0,1], [2]),
            Equation("NOT", [2], [3]),
            Equation("NCONS", [0,1], [4]),
            Equation("NANY", [3,4], [5]),
            Equation("NCONS", [0,1], [6]),
            Equation("NOT", [6], [7]),
            Equation("NANY", [5,7], [8])
        ]
    },
    "NSUM": {
        "nbrstate": 10,
        "nbrinput": 2,
        "nbroutput": 1,
        "equations": [ # 5 layers
            Equation("NANY", [0,1], [2]),
            Equation("NOT", [2], [3]),
            Equation("NCONS", [0,1], [4]),
            Equation("NANY", [3,4], [5]),
            Equation("NCONS", [0,1], [6]),
            Equation("NOT", [6], [7]),
            Equation("NANY", [5,7], [8]),
            Equation("NOT", [8], [9])
        ]
    },
    "ABS": {
        "nbrstate": 3,
        "nbrinput": 1,
        "nbroutput": 1,
        "equations": [ # 5 layers
            Equation("NOT", [0], [1]),
            Equation("NAND", [0,1], [2])
        ]
    },
    "BI_AND": {
        "nbrstate": 4,
        "nbrinput": 2,
        "nbroutput": 1,
        "equations": [ # 2 layers
            Equation("BI_NAND", [0,1], [2]),
            Equation("BI_NOT", [2], [3])
        ]
    },
    "BI_OR": {
        "nbrstate": 4,
        "nbrinput": 2,
        "nbroutput": 1,
        "equations": [ # 2 layers
            Equation("BI_NOR", [0,1], [2]),
            Equation("BI_NOT", [2], [3])
        ]
    },
    "BI_XOR": {
        "nbrstate": 6,
        "nbrinput": 2,
        "nbroutput": 1,
        "equations": [ # 3 layers
            Equation("BI_NAND", [0,1], [2]),
            Equation("BI_NAND", [0,2], [3]), 
            Equation("BI_NAND", [1,2], [4]),
            Equation("BI_NAND", [3,4], [5]) 
        ]
    },
    "BI_XNOR": {
        "nbrstate": 6,
        "nbrinput": 2,
        "nbroutput": 1,
        "equations": [ # 3 layers
            Equation("BI_NOR", [0,1], [2]),
            Equation("BI_NOR", [0,2], [3]), 
            Equation("BI_NOR", [1,2], [4]),
            Equation("BI_NOR", [3,4], [5])
        ]
    }
}

def genEquation_microSystemGate(gate, inputNets, outputNets):
    microsystem = MicroSystem(**MICROSYSTEMS[gate])
    return Equation(microsystem, inputNets, outputNets)

class MicroSystem:
    def __init__(self, nbrstate, nbrinput, nbroutput, equations):
        self.state = [3 for k in range(nbrstate)]
        self.nbrinput = nbrinput
        self.nbroutput = nbroutput
        self.equations = equations

    def load(self, arguments):
        self.state[:self.nbrinput] = arguments
    
    def update(self):
        next_state = self.state.copy()
        for equation in self.equations:
            system = equation.system
            if type(system) is str:
                if len(equation.arguments)==1:
                    if self.state[equation.arguments[0]]==3: next_state[equation.destinations[0]]=3
                    else: next_state[equation.destinations[0]] = MICROGATES[equation.system] [self.state[equation.arguments[0]]]
                elif len(equation.arguments)==2:
                    if self.state[equation.arguments[0]]==3 or self.state[equation.arguments[1]]==3: next_state[equation.destinations[0]]=3
                    else: next_state[equation.destinations[0]] = MICROGATES[equation.system] [self.state[equation.arguments[0]]] [self.state[equation.arguments[1]]]
            elif type(system) is MicroSystem:
                system.load([self.state[coord] for coord in equation.arguments])
                system.update()
                results = system.retrieve()
                for net,value in zip(equation.destinations , results):
                    if value<3: next_state[net] = value
        self.state = next_state

    def retrieve(self):
        return self.state[-self.nbroutput:]

# System = many inputs, many outpus, many equations, generated & loaded
class System:
    def __init__(self, nbrstate, nbrinput, nbroutput, tag2input, tag2output, equations, name="unnamed_system"):
        self.state = [3 for k in range(nbrstate)]
        self.nbrinput = nbrinput
        self.nbroutput = nbroutput
        self.tag2input = tag2input
        self.tag2output = tag2output
        self.equations = equations
        self.name = name

    def load(self, arguments):
        for tag, value in arguments.items():
            self.state[self.tag2input[tag]] = value

    def update(self):
        next_state = self.state.copy()
        for equation in self.equations:
            system = equation.system
            if type(system) is str:
                if len(equation.arguments)==1:
                    if self.state[equation.arguments[0]]==3: next_state[equation.destinations[0]]=3
                    else: next_state[equation.destinations[0]] = MICROGATES[equation.system] [self.state[equation.arguments[0]]]
                elif len(equation.arguments)==2:
                    if self.state[equation.arguments[0]]==3 or self.state[equation.arguments[1]]==3: next_state[equation.destinations[0]]=3
                    else: next_state[equation.destinations[0]] = MICROGATES[equation.system] [self.state[equation.arguments[0]]] [self.state[equation.arguments[1]]]
            elif type(system) is MicroSystem:
                system.load([self.state[coord] for coord in equation.arguments])
                system.update()
                results = system.retrieve()
                for net,value in zip(equation.destinations , results):
                    if value<3: next_state[net] = value
            elif type(system) is System or type(system) is Memory or type(system) is Register: # add new Algrebraic system type here !!
                arguments = {tag:self.state[net] for tag,net in equation.arguments.items()}
                system.load(arguments)
                system.update()
                results = system.retrieve()
                for tag,net in equation.destinations.items():
                    if results[tag]<3: next_state[net] = results[tag]
        self.state = next_state
    
    def retrieve(self):
        return {tag:self.state[self.tag2output[tag]] for tag in self.tag2output}
    
    def reset(self):
        self.state = [3 for k in range(nbrstate)]


# NonAlgebraicSystem = many inputs, many outpus, transfer function, loaded
class NonAlgebraicSystem:
    def __init__(self, nbrinput, nbroutput, tag2input, tag2output, data, updateFunction, drawFunction=None, name="unnamed_system"):
        self.state = [3 for k in range(nbrinput+nbroutput)]
        self.nbrinput = nbrinput
        self.nbroutput = nbroutput
        self.tag2input = tag2input
        self.tag2output = tag2output
        self.data = data
        self.updateFunction = updateFunction
        self.drawFunction = drawFunction
        self.name = name
    
    def load(self, arguments):
        for tag, value in arguments.items():
            self.state[self.tag2input[tag]] = value
    
    def update(self):
        self.updateFunction(self.state, self.tag2input, self.tag2output, self.data)
    
    def retrieve(self):
        return {tag:self.state[self.tag2output[tag]] for tag in self.tag2output}
    
    def reset(self):
        self.state = [3 for k in range(nbrstate)]
    
    def draw(self):
        return self.drawFunction(state, data)


def updateRAM(state, tag2input, tag2output, data):
    print(data)
    address = 0
    for k in range(data["addrsize"]):
        if state[tag2input["A{}".format(k)]]==3: address += 3**k
        else: address += (3**k)*state[tag2input["A{}".format(k)]]
    if state[tag2input["RW"]]==2:
        word = data["memory"][address]
        print("Memory word read : {}".format(word))
        wordter = dec2ter(word)
        for k in range(data["wordsize"]):
            if k>=len(wordter): state[tag2output["Q{}".format(k)]]=0
            else: state[tag2output["Q{}".format(k)]]=wordter[k]
    elif state[tag2input["RW"]]==1:
        for k in range(data["wordsize"]):
            state[tag2output["Q{}".format(k)]]=3
    elif state[tag2input["RW"]]==0:
        word = 0
        for k in range(data["wordsize"]):
            if state[tag2input["D{}".format(k)]]<3: word += 3**k
            else: word += (3**k)*state[tag2input["D{}".format(k)]]
        print("Memory word writen : {}".format(word))
        data["memory"][address] = word
        for k in range(data["wordsize"]):
            state[tag2output["Q{}".format(k)]]=3
def drawRAM(state, data):
    return "Memory"

class Memory(NonAlgebraicSystem):
    def __init__(self, filepath=""):
        self.filepath = filepath
        f = open(filepath,'rb')
        data = json.load(f)
        f.close()
        nbrinput = data["addrsize"]
        nbroutput = data["wordsize"]
        tag2input = { **{"RW":0} , **{"A{}".format(k) : k+1 for k in range(nbrinput)} , **{"D{}".format(k) : nbrinput+k+1 for k in range(nbrinput)} }
        tag2output = {"Q{}".format(k) : nbrinput+k for k in range(nbroutput)}
        NonAlgebraicSystem.__init__(self, 2*nbrinput+1, nbroutput, tag2input, tag2output, data, updateRAM, drawRAM)
    
    def reset(self):
        f = open(filepath,'rb')
        data = json.load(f)
        f.close()
        if nbrinput != data["addrsize"] or nbroutput != data["wordsize"]: print("New file not compatible !")
        else:
            self.state = [3 for k in range(nbrstate)]
            self.data = data

def updateREG(state, tag2input, tag2output, data):
    if state[tag2input["RW"]]==2:
        for k in range(data["wordsize"]):
            state[tag2output["Q{}".format(k)]]=data["data{}".format(k)]
    elif state[tag2input["RW"]]==1:
        for k in range(data["wordsize"]):
            state[tag2output["Q{}".format(k)]]=3
    elif state[tag2input["RW"]]==0:
        for k in range(data["wordsize"]):
            if state[tag2input["D{}".format(k)]]==3: data["data{}".format(k)]=1
            else: data["data{}".format(k)]=state[tag2input["D{}".format(k)]]
            state[tag2output["Q{}".format(k)]]=3
def drawREG(state, data):
    return "Register"

class Register(NonAlgebraicSystem):
    def __init__(self, wordsize):
        data = { **{"wordsize":wordsize} , **{"data{}".format(k):1 for k in range(wordsize)} }
        nbrinput = wordsize
        nbroutput = wordsize
        tag2input = { **{"RW":0} , **{"D{}".format(k) : k+1 for k in range(nbrinput)} }
        tag2output = {"Q{}".format(k) : 1+nbrinput+k for k in range(nbroutput)}
        NonAlgebraicSystem.__init__(self, nbrinput+1, nbroutput, tag2input, tag2output, data, updateREG, drawREG)

    def reset(self):
        self.state = [3 for k in range(nbrstate)]
        for k in range(data["wordsize"]):
            data["data{}".format(k)]=1
