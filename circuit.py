class Component:
    def __init__(self, type, n1, n2, value):
        self.type = type  # R, L, C, G
        self.n1 = n1      # Node 1
        self.n2 = n2      # Node 2
        self.value = value  # Value of the component

class Termination:
    def __init__(self, type, value):
        self.type = type  # VT, RS, IN, GS, RL, Fstart, Fend, Nfreqs
        self.value = value

class Output:
    def __init__(self, name, unit=None):
        self.name = name  # Output parameter name, e.g., Vin, Vout, etc.
        self.unit = unit  # Unit of the parameter, e.g., V (Volts), A (Amps), etc.

class Circuit:
    def __init__(self):
        self.components = []
        self.terminations = {}
        self.outputs = []
        
    def add_component(self, type, n1, n2, value):
        self.components.append(Component(type, n1, n2, value))

    def set_termination(self, type, value):
        self.terminations[type] = Termination(type, value)

    def add_output(self, name, unit):
        self.outputs.append(Output(name, unit))
