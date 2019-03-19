from microgates import MICROGATES

VERBOSE = False

class Equation:
    def __init__(self, system, arguments, destinations):
        self.system = system
        self.arguments = arguments
        self.destinations = destinations

class System:
    def __init__(self, nbrstate, equations):
        self.state = [1 for k in range(nbrstate)]
        self.equations = equations
    def load(self, arguments):
        self.state[:len(arguments)] = arguments
    def update(self):
        next_state = self.state.copy()
        if VERBOSE : print("Début update : next_state = {}  ;  state = {}".format(next_state, self.state))
        for equation in self.equations:
            system = equation.system
            if type(system) is System:
                if VERBOSE : print("Complex system")
                arguments = [self.state[i] for i in equation.arguments]
                system.load(arguments)
                system.update()
                retrieved = system.retrieve(len(equation.destinations))
                for i in range(len(retrieved)):
                    destination = equation.destinations[i]
                    next_state[destination] = retrieved[i]
            else:
                if VERBOSE : print("Microgate : "+equation.system)
                if len(equation.arguments)==1:
                    next_state[equation.destinations[0]] = MICROGATES[equation.system] [self.state[equation.arguments[0]]]
                    if VERBOSE : print("state[{}] = {}({}) = {}".format(equation.destinations[0] , equation.system , self.state[equation.arguments[0]] , MICROGATES[equation.system] [self.state[equation.arguments[0]]]))
                elif len(equation.arguments)==2:
                    next_state[equation.destinations[0]] = MICROGATES[equation.system] [self.state[equation.arguments[0]]] [self.state[equation.arguments[1]]]
                    if VERBOSE : print("state[{}] = {}({} , {}) = {}".format(equation.destinations[0] , equation.system , self.state[equation.arguments[0]] , self.state[equation.arguments[1]] , MICROGATES[equation.system] [self.state[equation.arguments[0]]] [self.state[equation.arguments[1]]]))
                if VERBOSE : print("Current next_state = {}".format(next_state))
        self.state = next_state
        if VERBOSE : print("Fin update : next_state = {}  ;  state = {}".format(next_state, self.state))
    def printState(self):
        print(self.state)
        if VERBOSE : print("\n\n")
    def retrieve(self, nbrreturns):
        return self.state[-nbrreturns:]

S1 = System(4,[
    Equation("NAND", [0, 1], [2]),
    Equation("NOT", [2], [3])
])
S2 = System(4,[
    Equation("NAND", [0, 1], [2]),
    Equation("NOT", [2], [3])
])

S3 = System(6,[
    Equation(S1, [0, 1], [3]),
    Equation(S2, [3, 2], [4]),
    Equation("NOT", [4], [5])
])

print("\n\n")

S3.load([1,1,1]) ; S3.update() ; S3.printState()
S3.load([1,1,1]) ; S3.update() ; S3.printState()
S3.load([1,1,1]) ; S3.update() ; S3.printState()
S3.load([2,1,1]) ; S3.update() ; S3.printState()
S3.load([2,1,1]) ; S3.update() ; S3.printState()
S3.load([2,1,1]) ; S3.update() ; S3.printState()
S3.load([2,2,1]) ; S3.update() ; S3.printState()
S3.load([2,2,1]) ; S3.update() ; S3.printState()
S3.load([2,2,1]) ; S3.update() ; S3.printState()
S3.load([2,2,2]) ; S3.update() ; S3.printState()
S3.load([2,2,2]) ; S3.update() ; S3.printState()
S3.load([2,2,2]) ; S3.update() ; S3.printState()