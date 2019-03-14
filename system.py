from microgates import MICROGATES

class Equation:
    def __init__(self, system, arguments, destiantions):
        self.system = system
        self.arguments = arguments
        self.destiantions = destiantions

class System:
    def load(self, arguments):
        self.state[:len(arguments)] = arguments
    def update(self):
        for equation in self.equations:
            system = equation.system
            next_state = [1 for i in range(len(self.state))]
            if type(system) is System:
                arguments = [self.state[i] for i in equation.arguments]
                system.load(arguments)
                system.update()
                retrieved = system.retrieve(len(equation.destinations))
                for i in range(len(retrieved)):
                    destination = equation.destinations[i]
                    next_state[destination] = retrieved[i]
                self.state = next_state
            else:
                if len(equation.arguments)==1:
                    next_state[equation.destinations[0]] = MICROGATES[equation.system] [equation.arguments[0]]
                elif len(equation.arguments)==2:
                    next_state[equation.destinations[0]] = MICROGATES[equation.system] [equation.arguments[0]] [equation.arguments[1]]
    def retrieve(self, nbrreturns):
        return self.state[-nbrreturns:]