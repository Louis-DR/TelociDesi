from pickle import *
import json
from tkinter.filedialog import askopenfilename
from dec2ter import *
from log import Log

class Equation:
    def __init__(self, system, arguments, destinations):
        self.system = system
        self.arguments = arguments
        self.destinations = destinations


# Microgate = few inputs, 1 output, 1 equation, hard coded
MICROGATES = {
    "NOT": [2,1,0],
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
            [0,0,0]]
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
    }
}

def genEquation_microSystemGate(gate, inputNets, outputNets):
    microsystem = MicroSystem(**MICROSYSTEMS[gate])
    return Equation(microsystem, inputNets, outputNets)

class MicroSystem:
    def __init__(self, nbrstate, nbrinput, nbroutput, equations):
        self.state = [1 for k in range(nbrstate)]
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
                    next_state[equation.destinations[0]] = MICROGATES[equation.system] [self.state[equation.arguments[0]]]
                elif len(equation.arguments)==2:
                    next_state[equation.destinations[0]] = MICROGATES[equation.system] [self.state[equation.arguments[0]]] [self.state[equation.arguments[1]]]
            elif type(system) is MicroSystem:
                system.load([self.state[coord] for coord in equation.arguments])
                system.update()
                results = system.retrieve()
                for net,value in zip(equation.destinations , results):
                    next_state[net] = value
        self.state = next_state

    def retrieve(self):
        return self.state[-self.nbroutput:]

# System = many inputs, many outpus, many equations, generated & loaded
class System:
    def __init__(self, nbrstate, nbrinput, nbroutput, tag2input, tag2output, equations, name="unnamed_system"):
        self.state = [1 for k in range(nbrstate)]
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
                    next_state[equation.destinations[0]] = MICROGATES[equation.system] [self.state[equation.arguments[0]]]
                elif len(equation.arguments)==2:
                    next_state[equation.destinations[0]] = MICROGATES[equation.system] [self.state[equation.arguments[0]]] [self.state[equation.arguments[1]]]
            elif type(system) is MicroSystem:
                system.load([self.state[coord] for coord in equation.arguments])
                system.update()
                results = system.retrieve()
                for net,value in zip(equation.destinations , results):
                    next_state[net] = value
            elif type(system) is System or type(system) is Memory: # add new Algrebraic system type here !!
                arguments = {tag:self.state[net] for tag,net in equation.arguments.items()}
                system.load(arguments)
                system.update()
                results = system.retrieve()
                for tag,net in equation.destinations.items():
                    next_state[net] = results[tag]
        self.state = next_state
    
    def retrieve(self):
        return {tag:self.state[self.tag2output[tag]] for tag in self.tag2output}


# NonAlgebraicSystem = many inputs, many outpus, transfer function, loaded
class NonAlgebraicSystem:
    def __init__(self, nbrinput, nbroutput, tag2input, tag2output, data, updateFunction, name="unnamed_system"):
        self.state = [1 for k in range(nbrinput+nbroutput)]
        self.nbrinput = nbrinput
        self.nbroutput = nbroutput
        self.tag2input = tag2input
        self.tag2output = tag2output
        self.data = data
        self.updateFunction = updateFunction
        self.name = name
    
    def load(self, arguments):
        for tag, value in arguments.items():
            self.state[self.tag2input[tag]] = value
    
    def update(self):
        self.updateFunction(self.state, self.tag2input, self.tag2output, self.data)
    
    def retrieve(self):
        return {tag:self.state[self.tag2output[tag]] for tag in self.tag2output}


def updateROM(state, tag2input, tag2output, data):
    address = sum([(3**k)*state[tag2input["A{}".format(k)]] for k in range(data["addrsize"])])
    word = data["memory"][address]
    print("Memory word read : {}".format(word))
    wordter = dec2ter(word)
    for k in range(data["wordsize"]):
        if k>=len(wordter): state[tag2output["Q{}".format(k)]]=0
        else: state[tag2output["Q{}".format(k)]]=wordter[k]

class Memory(NonAlgebraicSystem):
    def __init__(self, filepath=""):
        f = open(filepath,'rb')
        data = json.load(f)
        f.close()
        nbrinput = data["addrsize"]
        nbroutput = data["wordsize"]
        tag2input = {"A{}".format(k) : k for k in range(nbrinput)}
        tag2output = {"Q{}".format(k) : nbrinput+k for k in range(nbroutput)}
        NonAlgebraicSystem.__init__(self, nbrinput, nbroutput, tag2input, tag2output, data, updateROM)
        
