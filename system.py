VERBOSE = False

class Equation:
    def __init__(self, system, arguments, destinations):
        self.system = system
        self.arguments = arguments
        self.destinations = destinations


# Microgate = few inputs, 1 output, 1 equation
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

# Microsystem = few inputs, 1 output, many equations
# class MicroSystem:

# System = many inputs, many outpus, many equations
class System:
    def __init__(self, nbrstate, tag2state, equations):
        self.state = [1 for k in range(nbrstate)]
        self.tag2state = tag2state
        self.equations = equations

    def load(self, arguments):
        for tag, value in arguments.items():
            self.state[self.tag2state[tag]] = value

    def update(self):
        next_state = self.state.copy()
        if VERBOSE : print("Début update : next_state = {}  ;  state = {}".format(next_state, self.state))
        for equation in self.equations:
            system = equation.system
            if type(system) is System:
                if VERBOSE : print("Complex system")
                arguments = {tag:self.state[self.tag2state[tag]] for tag in equation.arguments}
                system.load(arguments)
                system.update()
                results = system.retrieve()
                for tag,value in results.items():
                    next_state[self.tag2state[tag]] = value
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
    
    def retrieve(self):
        return {tag:self.state[tag] for tag in self.tag2state}

    def printState(self):
        print(self.state)
        if VERBOSE : print("\n\n")

# NonAlgebraicSystem = many inputs, many outpus, transfer function
# class NonAlgebraicSystem:


S1 = System(4,{"inputA":0 , "inputB":1 , "output":3},[
    Equation("NAND", [0, 1], [2]),
    Equation("NOT", [2], [3])
])
S2 = System(4,{"inputA":0 , "inputB":1 , "output":3},[
    Equation("NAND", [0, 1], [2]),
    Equation("NOT", [2], [3])
])

S3 = System(6,{"A":0 , "B":1 , "C":2},[
    Equation(S1, [0, 1], [3]),
    Equation(S2, [3, 2], [4]),
    Equation("NOT", [4], [5])
])

print("\n\n")

S3.load({"A":1 , "B":1 , "C":1}) ; S3.update() ; S3.printState()
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