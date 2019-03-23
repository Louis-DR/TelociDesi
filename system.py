from pickle import *

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
            elif type(system) is System:
                arguments = {tag:self.state[net] for tag,net in equation.arguments.items()}
                system.load(arguments)
                system.update()
                results = system.retrieve()
                for tag,net in equation.destinations.items():
                    next_state[net] = results[tag]
        self.state = next_state
    
    def retrieve(self):
        return {tag:self.state[self.tag2output[tag]] for tag in self.tag2output}

    def printState(self):
        print(self.state)


# NonAlgebraicSystem = many inputs, many outpus, transfer function, loaded
# class NonAlgebraicSystem:




# S1 = System(4,{"inputA":0 , "inputB":1 , "output":3},[
#     Equation("NAND", [0, 1], [2]),
#     Equation("NOT", [2], [3])
# ])
# S2 = System(4,{"inputA":0 , "inputB":1 , "output":3},[
#     Equation("NAND", [0, 1], [2]),
#     Equation("NOT", [2], [3])
# ])

# S3 = System(6,{"A":0 , "B":1 , "C":2},[
#     Equation(S1, {"inputA":0 , "inputB":1}, {"output":3}),
#     Equation(S2, {"inputA":3 , "inputB":2}, {"output":4}),
#     Equation("NOT", [4], [5])
# ])

# print("\n\n")

# S3.load({"A":1 , "B":1 , "C":1}) ; S3.update() ; S3.printState()
# S3.load({"A":1 , "B":1 , "C":1}) ; S3.update() ; S3.printState()
# S3.load({"A":1 , "B":1 , "C":1}) ; S3.update() ; S3.printState()
# S3.load({"A":1 , "B":1 , "C":1}) ; S3.update() ; S3.printState()
# print("tick")
# S3.load({"A":2 , "B":1 , "C":1}) ; S3.update() ; S3.printState()
# S3.load({"A":2 , "B":1 , "C":1}) ; S3.update() ; S3.printState()
# S3.load({"A":2 , "B":1 , "C":1}) ; S3.update() ; S3.printState()
# S3.load({"A":2 , "B":1 , "C":1}) ; S3.update() ; S3.printState()
# print("tick")
# S3.load({"A":2 , "B":2 , "C":1}) ; S3.update() ; S3.printState()
# S3.load({"A":2 , "B":2 , "C":1}) ; S3.update() ; S3.printState()
# S3.load({"A":2 , "B":2 , "C":1}) ; S3.update() ; S3.printState()
# S3.load({"A":2 , "B":2 , "C":1}) ; S3.update() ; S3.printState()
# print("tick")
# S3.load({"A":2 , "B":2 , "C":2}) ; S3.update() ; S3.printState()
# S3.load({"A":2 , "B":2 , "C":2}) ; S3.update() ; S3.printState()
# S3.load({"A":2 , "B":2 , "C":2}) ; S3.update() ; S3.printState()
# S3.load({"A":2 , "B":2 , "C":2}) ; S3.update() ; S3.printState()
# S3.load({"A":2 , "B":2 , "C":2}) ; S3.update() ; S3.printState()
# S3.load({"A":2 , "B":2 , "C":2}) ; S3.update() ; S3.printState()



# S_microgates = System(7,2,5,{"A":0 , "B":1 , "nand":2 , "nor":3 , "ncons":4 , "nany":5 , "not":6},[
#     Equation("NAND", [0, 1], [2]),
#     Equation("NOR", [0, 1], [3]),
#     Equation("NCONS", [0, 1], [4]),
#     Equation("NANY", [0, 1], [5]),
#     Equation("NOT", [0], [6])
# ])
# print("\n\n")
# S_microgates.load({"A":0 , "B":0}) ; S_microgates.update() ; S_microgates.printState()
# S_microgates.load({"A":0 , "B":1}) ; S_microgates.update() ; S_microgates.printState()
# S_microgates.load({"A":0 , "B":2}) ; S_microgates.update() ; S_microgates.printState()
# S_microgates.load({"A":1 , "B":0}) ; S_microgates.update() ; S_microgates.printState()
# S_microgates.load({"A":1 , "B":1}) ; S_microgates.update() ; S_microgates.printState()
# S_microgates.load({"A":1 , "B":2}) ; S_microgates.update() ; S_microgates.printState()
# S_microgates.load({"A":2 , "B":0}) ; S_microgates.update() ; S_microgates.printState()
# S_microgates.load({"A":2 , "B":1}) ; S_microgates.update() ; S_microgates.printState()
# S_microgates.load({"A":2 , "B":2}) ; S_microgates.update() ; S_microgates.printState()



# S_microsystem = System(10,2,8,{"A":0 , "B":1 , "and":2 , "or":3 , "cons":4 , "any":5 , "mul":6 , "nmul":7 , "sum":8 , "nsum":9},[
#     genEquation_microSystemGate("AND", [0, 1], [2]),
#     genEquation_microSystemGate("OR", [0, 1], [3]),
#     genEquation_microSystemGate("CONS", [0, 1], [4]),
#     genEquation_microSystemGate("ANY", [0, 1], [5]),
#     genEquation_microSystemGate("MUL", [0, 1], [6]),
#     genEquation_microSystemGate("NMUL", [0, 1], [7]),
#     genEquation_microSystemGate("SUM", [0, 1], [8]),
#     genEquation_microSystemGate("NSUM", [0, 1], [9]),
# ])
# print("\n\n")
# S_microsystem.load({"A":0 , "B":0}) ; [S_microsystem.update() for i in range(5)] ; S_microsystem.printState()
# S_microsystem.load({"A":0 , "B":1}) ; [S_microsystem.update() for i in range(5)] ; S_microsystem.printState()
# S_microsystem.load({"A":0 , "B":2}) ; [S_microsystem.update() for i in range(5)] ; S_microsystem.printState()
# S_microsystem.load({"A":1 , "B":0}) ; [S_microsystem.update() for i in range(5)] ; S_microsystem.printState()
# S_microsystem.load({"A":1 , "B":1}) ; [S_microsystem.update() for i in range(5)] ; S_microsystem.printState()
# S_microsystem.load({"A":1 , "B":2}) ; [S_microsystem.update() for i in range(5)] ; S_microsystem.printState()
# S_microsystem.load({"A":2 , "B":0}) ; [S_microsystem.update() for i in range(5)] ; S_microsystem.printState()
# S_microsystem.load({"A":2 , "B":1}) ; [S_microsystem.update() for i in range(5)] ; S_microsystem.printState()
# S_microsystem.load({"A":2 , "B":2}) ; [S_microsystem.update() for i in range(5)] ; S_microsystem.printState()