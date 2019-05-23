# Ternary Logic Circuit Designer and Simulator
from tkinter import *
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from collections import deque
from system import *
import pickle
import json

import time
lasttime = time.time()
def rectime():
    global lasttime
    rt = 1000*(time.time()-lasttime)
    lasttime = time.time()
    return rt

from log import Log
import random

#region [red] CONFIGURATION

TKINTER_SCALING = 1.0
GRID_WIDTH = 50
GRID_HEIGHT = 50
GRID_UNIT = TKINTER_SCALING*40
THICKNESS = TKINTER_SCALING*4

FONT_FAMILY = "Helvetica"
FONT_SIZE = 20
FONT_SIZE_MENU=35

FILE_DIRECTORY = ""
FILE_NAME = "testcircuit2"
PROGRAM_NAME = "testprog"

BUTTON_WIDTH = 6
TOOL_PANEL_WIDTH = TKINTER_SCALING*100

CHRONOGRAM_WIDTH = TKINTER_SCALING*800
CHRONOGRAM_MARGIN_VERTICAL = TKINTER_SCALING*40
CHRONOGRAM_MARGIN_HORIZONTAL = 40

SHIFT_MOVE_PERCENTAGE = 0.5

DT_PER_CC = 5

#endregion


#region [purple] SIMULATION

SYMBOLS = ['-', '0', '+']
GATES = {
    "AND": [[0,0,0],
            [0,1,1],
            [0,1,2]],
    "CONS": [[0,1,1],
             [1,1,1],
             [1,1,2]],
    "MUL": [[2,1,0],
            [1,1,1],
            [0,1,2]],
    "OR": [[0,1,2],
           [1,1,2],
           [2,2,2]],
    "ANY": [[0,0,1],
            [0,1,2],
            [1,2,2]],
    "SUM": [[2,0,1],
            [0,1,2],
            [1,2,0]],
    "BI_AND": [[1,1,1],
               [1,1,1],
               [1,1,2]],
    "BI_OR": [[1,1,2],
              [1,1,2],
              [2,2,2]],
    "BI_XOR": [[1,1,2],
               [1,1,2],
               [2,2,1]]
}
UGATES = {
    "PNOT": [2,2,0],
    "NOT": [2,1,0],
    "NNOT": [2,0,0],
    "ABS": [2,1,2],
    "INC": [1,2,2],
    "DEC": [0,0,1],
    "RTU": [1,2,0],
    "RTD": [2,0,1],
    "CLU": [1,1,2],
    "CLD": [0,1,1],
    "BI_NOT": [1,2,1]
}
NGATES = {
    "NAND" : "AND", 
    "NCONS" : "CONS", 
    "NMUL" : "MUL", 
    "NOR" : "OR", 
    "NANY" : "ANY", 
    "NSUM" : "SUM",
    "BI_NAND" : "BI_AND",
    "BI_NOR" : "BI_OR",
    "BI_XNOR" : "BI_XOR"
}
clockCycle = 0

tag_idgen = 0
loadedSystem_idgen = 0
loadedSystems = {}
loadedSystemToBePlaced_id = None
loadedSystemToBePlaced_type = None
circuitSystem = None

tags = {}
program = {}
recording = {}

def buildSystem():
    global circuitModified
    log0=Log("building the system") #LOGGING
    
    circuitModified=False

    # build the net list
    # log1=Log("building the net list") #LOGGING
    net_idgen = 0
    net2ids = {}
    id2net = {}
    nodesQueue = deque(nodes.keys())
    while nodesQueue:
        currentElement = nodesQueue.popleft()
        if currentElement not in id2net:
            newNet_id = net_idgen
            net_idgen +=1
            net2ids[newNet_id] = []
            netQueue = deque([currentElement])
            while netQueue:
                netQueueElement = netQueue.popleft()
                if netQueueElement not in id2net:
                    id2net[netQueueElement] = newNet_id
                    net2ids[newNet_id].append(netQueueElement)
                    netQueueElementNode = nodes[netQueueElement]
                    for wire_id in netQueueElementNode["wires"]:
                        wire = wires[wire_id]
                        if wire["node_a"] not in net2ids[newNet_id]: netQueue.append(wire["node_a"])
                        if wire["node_b"] not in net2ids[newNet_id]: netQueue.append(wire["node_b"])
    nbrNet = net_idgen
    # log1.stop() #LOGGING

    # build the input output to net dictionary
    # log2 = Log("building the input output to net dictionary") #LOGGING
    tag2inputnet = {}
    tag2outputnet = {}
    for tag_name, tag_id in tags.items():
        if tag_id[0]=='i': tag2inputnet[tag_name] = id2net[inputs[tag_id]["node"]]
        if tag_id[0]=='o': tag2outputnet[tag_name] = id2net[outputs[tag_id]["node"]]
    for input_id,input in inputs.items():
        if input_id not in tags.values():
            tag2inputnet[input_id] = id2net[input["node"]]
    for output_id,output in outputs.items():
        if output_id not in tags.values():
            tag2outputnet[output_id] = id2net[output["node"]]
    # log2.stop() #LOGGING

    # build the list of equations
    # log3 = Log("building the list of equations") #LOGGING
    equations = []
    for gate in gates.values():
        if gate["gate"] in MICROGATES:
            if "input_b" in gate:
                equations.append(Equation(gate["gate"] , [id2net[gate["input_a"]] , id2net[gate["input_b"]]] , [id2net[gate["output"]]]))
            else:
                equations.append(Equation(gate["gate"] , [id2net[gate["input_a"]]] , [id2net[gate["output"]]]))
        elif gate["gate"] in MICROSYSTEMS:
            equations.append(genEquation_microSystemGate(gate["gate"] , [id2net[gate["input_a"]] , id2net[gate["input_b"]]] , [id2net[gate["output"]]]))
    for system in systems.values():
        t_loadedSystem = loadedSystems[system["system"]]
        t_args = {inputtag:id2net[inputnode_id] for inputtag, inputnode_id in system["inputs"].items()}
        t_dest = {outputtag:id2net[outputnode_id] for outputtag, outputnode_id in system["outputs"].items()}
        equations.append(Equation(t_loadedSystem, t_args, t_dest))
    # log3.stop() #LOGGING

    # log4 = Log("creating the system") #LOGGING
    sys = System(nbrNet, len(inputs), len(outputs), tag2inputnet, tag2outputnet, equations, FILE_NAME)
    # log4.stop() #LOGGING

    log0.stop() #LOGGING
    return sys

def loadSystem(systemFileName):
    global loadedSystem_idgen
    global loadedSystems
    f = open(systemFileName,'rb')
    sys = pickle.load(f)
    f.close()
    loadedSystem_id = "ls_"+str(loadedSystem_idgen)
    loadedSystem_idgen +=1
    loadedSystems[loadedSystem_id] = sys
    return loadedSystem_id

def loadMemory(memoryFileName):
    global loadedSystem_idgen
    global loadedSystems
    sys = Memory(memoryFileName)
    loadedSystem_id = "ls_"+str(loadedSystem_idgen)
    loadedSystem_idgen +=1
    loadedSystems[loadedSystem_id] = sys
    return loadedSystem_id

def cleanLoadedSystem():
    global loadedSystemToBePlaced_id
    if loadedSystemToBePlaced_id:
        del loadedSystems[loadedSystemToBePlaced_id]
        loadedSystemToBePlaced_id = None

def simulateCc():
    global circuitSystem
    # log0 = Log("simulating a clock cycle") #LOGGING

    # log1 = Log("checking if the circuit has been modified") #LOGGING
    if circuitModified or circuitSystem==None:
        circuitSystem=buildSystem()
        resetRecording()
    # log1.stop() #LOGGING

    for dt in range(DT_PER_CC):
        simulateDt()
    drawChronogram() #ISSUE HERE
    
    # log0.stop() #LOGGING

def simulateDt():
    global recording
    # log0 = Log("simulating a delta t") #LOGGING

    # log1 = Log("creating and passing the arguments") #LOGGING
    t_args = {}
    for input_id,input in inputs.items():
        if input_id in tags.values():
            for tag,id in tags.items():
                if id == input_id:
                    t_args[tag] = input["value"]
        else: t_args[input_id] = input["value"]
    circuitSystem.load(t_args)
    # log1.stop() #LOGGING

    # log2 = Log("simulating the system") #LOGGING
    circuitSystem.update()
    # log2.stop() #LOGGING

    # log3 = Log("retrieving the results and updating the recordings") #LOGGING
    results = circuitSystem.retrieve()
    for tag,value in results.items():
        if tag in tags.keys():
            outputs[tags[tag]]["value"] = value
        else:
            outputs[tag]["value"] = value
    for input_id,input in inputs.items():
        recording[input_id].append(input["value"])
    for output_id,output in outputs.items():
        recording[output_id].append(output["value"])
    # log3.stop() #LOGGING

    # log4 = Log("drawing the outputs") #LOGGING
    for output in outputs.values(): #ISSUE HERE
        drawOutput(output) #ISSUE HERE
    # log4.stop() #LOGGING
    
    # log0.stop() #LOGGING

def resetSimulation():
    resetRecording()
    for output in outputs.values():
        drawOutput(output)
    for loadedSystem in loadedSystems.values():
        for k in range(len(loadedSystem.state)):
            loadedSystem.state[k] = 1
    buildSystem()
    drawChronogram()

def resetRecording():
    global recording
    for key in inputs:
        recording[key] = []
    for key in probes:
        recording[key] = []
    for key in outputs:
        recording[key] = []

#endregion


#region [blue] CREATION

gate_idgen = 0
system_idgen = 0
node_idgen = 0
wire_idgen = 0
input_idgen = 0
probe_idgen = 0
output_idgen = 0

gates = {}
systems = {}
nodes = {}
wires = {}
inputs = {}
probes = {}
outputs = {}

temp_node = None

view_x = 0
view_y = 0

def createGate(gate, sx, sy):
    global gate_idgen
    global screen
    new_gate = {
        "id": "g_"+str(gate_idgen),
        "gate": gate,
        "x": sx+view_x,
        "y": sy+view_y,
        "clockCycle": 0
    }
    gate_idgen +=1
    for xxx in range(sx-1, sx+6):
        for yyy in range(sy, sy+5):
            screen[xxx][yyy] = new_gate["id"]
    if gate in UGATES:
        new_gate["input_a"] = createNode(sx-1,sy+2, new_gate["id"])
    else:
        new_gate["input_a"] = createNode(sx-1,sy+1, new_gate["id"])   
        new_gate["input_b"] = createNode(sx-1,sy+3, new_gate["id"])
    new_gate["output"] = createNode(sx+5,sy+2, new_gate["id"])
    gates[new_gate["id"]] = new_gate
    drawGate(new_gate)
    canvas.delete("ghost")

def createSystem(sx, sy):
    global system_idgen
    global screen
    t_loadedSystem = loadedSystems[loadedSystemToBePlaced_id]
    t_height = max(t_loadedSystem.nbrinput , t_loadedSystem.nbroutput)+2
    new_system = {
        "id": "s_"+str(system_idgen),
        "system": loadedSystemToBePlaced_id,
        "type": loadedSystemToBePlaced_type,
        "x": sx+view_x,
        "y": sy+view_y,
        "height": t_height,
        "clockCycle": 0
    }
    system_idgen +=1
    for xxx in range(sx-1, sx+6):
        for yyy in range(sy, sy+t_height):
            screen[xxx][yyy] = new_system["id"]
    t_displacement = int(abs(t_loadedSystem.nbrinput-t_loadedSystem.nbroutput)/2)
    new_system["inputs"] = { inputtag : createNode(sx-1,sy+1+k+ (t_displacement if (t_loadedSystem.nbrinput<t_loadedSystem.nbroutput) else 0), new_system["id"], inputtag) for k,inputtag in zip(range(t_loadedSystem.nbrinput),t_loadedSystem.tag2input.keys())}
    new_system["outputs"] = { outputtag : createNode(sx+5,sy+1+k+ (t_displacement if (t_loadedSystem.nbrinput>t_loadedSystem.nbroutput) else 0), new_system["id"], outputtag) for k,outputtag in zip(range(t_loadedSystem.nbroutput),t_loadedSystem.tag2output.keys())}
    systems[new_system["id"]] = new_system
    drawSystem(new_system)
    canvas.delete("ghost")

def createNode(sx,sy,parent=None,tag=None):
    global node_idgen
    global screen
    new_node = {
        "id": "n_"+str(node_idgen),
        "x": sx+view_x,
        "y": sy+view_y,
        "wires": [],
        "parent": parent,
        "clockCycle": 0,
        "value": 1
    }
    node_idgen +=1
    if tag: new_node["tag"] = tag
    screen[sx][sy] = new_node["id"]
    nodes[new_node["id"]] = new_node
    return new_node["id"]

def createWire(sx,sy):
    global temp_node
    global wire_idgen
    node_a = None
    if screen[sx][sy]==None:
        node_a = createNode(sx,sy)
    elif screen[sx][sy][0]=='n': node_a = screen[sx][sy]
    elif screen[sx][sy][0]=='w':
        wire_mod = wires[screen[sx][sy]]
        node_a = createNode(sx,sy)
        cutWire(wire_mod, node_a)
    else: return
    if temp_node == None:
        temp_node = node_a
    else:
        new_wire = {
            "id": "w_"+str(wire_idgen),
            "node_a": node_a,
            "node_b": temp_node
        }
        wire_idgen +=1
        wires[new_wire["id"]] = new_wire
        temp_node = None
        nodes[node_a]["wires"].append(new_wire["id"])
        nodes[new_wire["node_b"]]["wires"].append(new_wire["id"])
        canvas.delete("ghost")
        remove("w_ghost")
        canvas.delete("n_ghost")
        del nodes["n_ghost"]
        drawWire(new_wire)
        updateScreen_wire(new_wire)

def createInput(sx,sy):
    global input_idgen
    new_input = {
        "id": "i_"+str(input_idgen),
        "x": sx+view_x,
        "y": sy+view_y,
        "clockCycle": 0,
        "value": 1
    }
    input_idgen +=1
    new_input["node"] = createNode(sx+1,sy, new_input["id"])
    inputs[new_input["id"]] = new_input
    drawInput(new_input)
    updateScreen_input(new_input)

def createProbe(sx,sy):
    global probe_idgen
    new_probe = {
        "id": "p_"+str(probe_idgen),
        "x": sx+view_x,
        "y": sy+view_y,
        "clockCycle": 0,
        "value": 1
    }
    probe_idgen +=1
    new_probe["node"] = createNode(sx,sy+1, new_probe["id"])
    probes[new_probe["id"]] = new_probe
    drawProbe(new_probe)
    updateScreen_probe(new_probe)

def createOutput(sx,sy):
    global output_idgen
    new_output = {
        "id": "o_"+str(output_idgen),
        "x": sx+view_x,
        "y": sy+view_y,
        "clockCycle": 0,
        "value": 1
    }
    output_idgen +=1
    new_output["node"] = createNode(sx-1,sy, new_output["id"])
    outputs[new_output["id"]] = new_output
    drawOutput(new_output)
    updateScreen_output(new_output)

def cutWire(wire, node):
    global wire_idgen
    new_wire_a = {
        "id": "w_"+str(wire_idgen),
        "node_a": wire["node_a"],
        "node_b": node
    }
    wire_idgen +=1
    new_wire_b = {
        "id": "w_"+str(wire_idgen),
        "node_a": node,
        "node_b": wire["node_b"]
    }
    wire_idgen +=1
    wires[new_wire_a["id"]] = new_wire_a
    wires[new_wire_b["id"]] = new_wire_b
    nodes[wire["node_a"]]["wires"].append(new_wire_a["id"])
    nodes[wire["node_b"]]["wires"].append(new_wire_b["id"])
    nodes[node]["wires"].append(new_wire_a["id"])
    nodes[node]["wires"].append(new_wire_b["id"])
    drawWire(new_wire_a)
    drawWire(new_wire_b)
    updateScreen_wire(new_wire_a)
    updateScreen_wire(new_wire_b)
    nodes[wire["node_a"]]["wires"].remove(wire["id"])
    nodes[wire["node_b"]]["wires"].remove(wire["id"])
    canvas.delete(wire["id"])
    del wires[wire["id"]]

#endregion


#region [cyan] DRAWING

grid_width = GRID_WIDTH
grid_height = GRID_HEIGHT
grid_unit = GRID_UNIT
thickness = THICKNESS

root = Tk()
root.title('Truite')
root.resizable(width=False, height=False)
root.tk.call('tk', 'scaling', TKINTER_SCALING)

canvas_width = grid_width*grid_unit
canvas_height = grid_height*grid_unit

canvas = Canvas(root, width=canvas_width, height=canvas_height)
canvas.create_rectangle(0,0,canvas_width,canvas_height,fill="#EEE",width=0 , tags="content")

screen = [[None for yyy in range(grid_height)] for xxx in range(grid_width)]

def drawAll():
    canvas.delete("content")
    for gate in gates.values():
        drawGate(gate)
    for system in systems.values():
        drawSystem(system)
    for wire in wires.values():
        drawWire(wire)
    for node in nodes.values():
        drawNode(node)
    for input in inputs.values():
        drawInput(input)
    for probe in probes.values():
        drawProbe(probe)
    for output in outputs.values():
        drawOutput(output)
    drawTags()
    drawSelection()

def drawGate_AND(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+1+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+1+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+3+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_arc(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+3+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)

def drawGate_NAND(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+1+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+1+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+3+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_oval(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5-0.4) , grid_unit*(sx+4+0.5+0.8) , grid_unit*(sy+2+0.5+0.4) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+5+0.5-0.2) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_arc(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+3+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)

def drawGate_CONS(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+1+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+1+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+3+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_arc(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+3+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+1) , grid_unit*(sy+1) , grid_unit*(sx+1) , grid_unit*(sy+4) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+1) , grid_unit*(sy+1) , grid_unit*(sx+2) , grid_unit*(sy+1) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+1) , grid_unit*(sy+4) , grid_unit*(sx+2) , grid_unit*(sy+4) , outline="#333" , fill="#333" , width=thickness , tags=tags)

def drawGate_NCONS(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+1+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+1+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+3+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_oval(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5-0.4) , grid_unit*(sx+4+0.5+0.8) , grid_unit*(sy+2+0.5+0.4) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+5+0.5-0.2) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_arc(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+3+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+1) , grid_unit*(sy+1) , grid_unit*(sx+1) , grid_unit*(sy+4) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+1) , grid_unit*(sy+1) , grid_unit*(sx+2) , grid_unit*(sy+1) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+1) , grid_unit*(sy+4) , grid_unit*(sx+2) , grid_unit*(sy+4) , outline="#333" , fill="#333" , width=thickness , tags=tags)

def drawGate_MUL(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_arc(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_rectangle(grid_unit*(sx) , grid_unit*(sy+1+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+1+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx) , grid_unit*(sy+3+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+3+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+3+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx) , grid_unit*(sy+0.5) , grid_unit*(sx) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)

def drawGate_NMUL(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_arc(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_rectangle(grid_unit*(sx) , grid_unit*(sy+1+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+1+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx) , grid_unit*(sy+3+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+3+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_oval(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5-0.4) , grid_unit*(sx+4+0.5+0.8) , grid_unit*(sy+2+0.5+0.4) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+5+0.5-0.2) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+3+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx) , grid_unit*(sy+0.5) , grid_unit*(sx) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)

def drawGate_OR(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_arc(grid_unit*(sx-1+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+1+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_arc(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+1.3) , grid_unit*(sy+1+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+1+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+1.3) , grid_unit*(sy+3+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+3+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+3+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)

def drawGate_NOR(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_arc(grid_unit*(sx-1+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+1+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_arc(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+1.3) , grid_unit*(sy+1+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+1+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+1.3) , grid_unit*(sy+3+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+3+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_oval(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5-0.4) , grid_unit*(sx+4+0.5+0.8) , grid_unit*(sy+2+0.5+0.4) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+5+0.5-0.2) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+3+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)

def drawGate_ANY(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_arc(grid_unit*(sx-1+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+1+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_arc(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+1.3) , grid_unit*(sy+1+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+1+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+1.3) , grid_unit*(sy+3+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+3+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+3+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_arc(grid_unit*(sx+0.5-1+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+0.5+1+0.5) , grid_unit*(sy+4+0.5) , start=-45 , extent=90 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+1.2+0.5) , grid_unit*(sy+0.5+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+0.5+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+1.2+0.5) , grid_unit*(sy+3+0.5+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+3+0.5+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)

def drawGate_NANY(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_arc(grid_unit*(sx-1+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+1+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_arc(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+1.3) , grid_unit*(sy+1+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+1+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+1.3) , grid_unit*(sy+3+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+3+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_oval(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5-0.4) , grid_unit*(sx+4+0.5+0.8) , grid_unit*(sy+2+0.5+0.4) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+5+0.5-0.2) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+3+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_arc(grid_unit*(sx+0.5-1+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+0.5+1+0.5) , grid_unit*(sy+4+0.5) , start=-45 , extent=90 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+1.2+0.5) , grid_unit*(sy+0.5+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+0.5+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+1.2+0.5) , grid_unit*(sy+3+0.5+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+3+0.5+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)

def drawGate_SUM(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_arc(grid_unit*(sx-1+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+1+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_arc(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.9) , grid_unit*(sy+1+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+1+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.9) , grid_unit*(sy+3+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+3+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+3+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_arc(grid_unit*(sx-0.5-1+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx-0.5+1+0.5) , grid_unit*(sy+4+0.5) , start=-55 , extent=110 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)

def drawGate_NSUM(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_arc(grid_unit*(sx-1+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+1+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_arc(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.9) , grid_unit*(sy+1+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+1+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.9) , grid_unit*(sy+3+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+3+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_oval(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5-0.4) , grid_unit*(sx+4+0.5+0.8) , grid_unit*(sy+2+0.5+0.4) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+5+0.5-0.2) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+3+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_arc(grid_unit*(sx-0.5-1+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx-0.5+1+0.5) , grid_unit*(sy+4+0.5) , start=-55 , extent=110 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)

def drawGate_PNOT(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+1+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+3+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+1+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4) , grid_unit*(sx+1+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+2-0.8) , grid_unit*(sy+2+0.5) , grid_unit*(sx+2+0.8) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+2) , grid_unit*(sy+2+0.5-0.8) , grid_unit*(sx+2) , grid_unit*(sy+2+0.5+0.8) , outline="#333" , fill="#333" , width=thickness , tags=tags)

def drawGate_NOT(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+1+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+3+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+1+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4) , grid_unit*(sx+1+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_oval(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5-0.4) , grid_unit*(sx+4+0.5+0.8) , grid_unit*(sy+2+0.5+0.4) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+5+0.5-0.2) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)

def drawGate_NNOT(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+1+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+3+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+1+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4) , grid_unit*(sx+1+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+2-0.8) , grid_unit*(sy+2+0.5) , grid_unit*(sx+2+0.8) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)

def drawGate_ABS(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+1+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+3+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+1+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4) , grid_unit*(sx+1+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+2-0.8) , grid_unit*(sy+2+0.5-0.8) , grid_unit*(sx+2-0.8) , grid_unit*(sy+2+0.5+0.8) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+2) , grid_unit*(sy+2+0.5-0.8) , grid_unit*(sx+2) , grid_unit*(sy+2+0.5+0.8) , outline="#333" , fill="#333" , width=thickness , tags=tags)

def drawGate_INC(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+1+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+3+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+1+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4) , grid_unit*(sx+1+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    SPACING = 0.6
    SIZE = 0.4
    canvas.create_rectangle(grid_unit*(sx+2-SPACING-SIZE) , grid_unit*(sy+2+0.5) , grid_unit*(sx+2-SPACING+SIZE) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+2-SPACING) , grid_unit*(sy+2+0.5-SIZE) , grid_unit*(sx+2-SPACING) , grid_unit*(sy+2+0.5+SIZE) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+2+SPACING-SIZE) , grid_unit*(sy+2+0.5) , grid_unit*(sx+2+SPACING+SIZE) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+2+SPACING) , grid_unit*(sy+2+0.5-SIZE) , grid_unit*(sx+2+SPACING) , grid_unit*(sy+2+0.5+SIZE) , outline="#333" , fill="#333" , width=thickness , tags=tags)

def drawGate_DEC(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+1+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+3+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+1+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4) , grid_unit*(sx+1+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    SPACING = 0.6
    SIZE = 0.4
    canvas.create_rectangle(grid_unit*(sx+2-SPACING-SIZE) , grid_unit*(sy+2+0.5) , grid_unit*(sx+2-SPACING+SIZE) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+2+SPACING-SIZE) , grid_unit*(sy+2+0.5) , grid_unit*(sx+2+SPACING+SIZE) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)

def drawGate_CLU(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+1+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+3+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+1+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4) , grid_unit*(sx+1+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    HEIGHT = 0.8
    ARM = 0.4
    canvas.create_rectangle(grid_unit*(sx+2) , grid_unit*(sy+2+0.5-HEIGHT) , grid_unit*(sx+2) , grid_unit*(sy+2+0.5+HEIGHT) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+2) , grid_unit*(sy+2+0.5-HEIGHT) , grid_unit*(sx+2+ARM) , grid_unit*(sy+2+0.5-HEIGHT+ARM) , grid_unit*(sx+2-ARM) , grid_unit*(sy+2+0.5-HEIGHT+ARM), outline="#333" , fill="#333" , width=thickness , tags=tags)

def drawGate_CLD(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+1+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+3+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+1+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4) , grid_unit*(sx+1+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    HEIGHT = 0.8
    ARM = 0.4
    canvas.create_rectangle(grid_unit*(sx+2) , grid_unit*(sy+2+0.5-HEIGHT) , grid_unit*(sx+2) , grid_unit*(sy+2+0.5+HEIGHT) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+2) , grid_unit*(sy+2+0.5+HEIGHT) , grid_unit*(sx+2+ARM) , grid_unit*(sy+2+0.5+HEIGHT-ARM) , grid_unit*(sx+2-ARM) , grid_unit*(sy+2+0.5+HEIGHT-ARM), outline="#333" , fill="#333" , width=thickness , tags=tags)

def drawGate_RTU(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+1+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+3+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+1+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4) , grid_unit*(sx+1+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    HEIGHT = 0.6
    LENGTH = 0.8
    ARM = 0.3
    canvas.create_arc(grid_unit*(sx+2-LENGTH) , grid_unit*(sy+2+0.5-HEIGHT) , grid_unit*(sx+2+LENGTH) , grid_unit*(sy+2+0.5+HEIGHT) , start=0 , extent=-180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_polygon(grid_unit*(sx+2+LENGTH) , grid_unit*(sy+2+0.1) , grid_unit*(sx+2+LENGTH+ARM) , grid_unit*(sy+2+0.5+0.1) , grid_unit*(sx+2+LENGTH-ARM) , grid_unit*(sy+2+0.5+0.1), outline="#333" , fill="#333" , width=thickness , tags=tags)

def drawGate_RTD(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+1+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+3+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+1+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4) , grid_unit*(sx+1+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    HEIGHT = 0.6
    LENGTH = 0.8
    ARM = 0.3
    canvas.create_arc(grid_unit*(sx+2-LENGTH) , grid_unit*(sy+2+0.5-HEIGHT) , grid_unit*(sx+2+LENGTH) , grid_unit*(sy+2+0.5+HEIGHT) , start=0 , extent=+180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_polygon(grid_unit*(sx+2+LENGTH) , grid_unit*(sy+2+0.9) , grid_unit*(sx+2+LENGTH+ARM) , grid_unit*(sy+2+0.5-0.1) , grid_unit*(sx+2+LENGTH-ARM) , grid_unit*(sy+2+0.5-0.1), outline="#333" , fill="#333" , width=thickness , tags=tags)

def drawGate_BI_AND(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+1+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+1+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+3+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_arc(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)

def drawGate_BI_NAND(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+1+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+1+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+3+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+3+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_oval(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5-0.4) , grid_unit*(sx+4+0.5+0.8) , grid_unit*(sy+2+0.5+0.4) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+5+0.5-0.2) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_arc(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)

def drawGate_BI_OR(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_arc(grid_unit*(sx-1+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+1+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_arc(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+1.3) , grid_unit*(sy+1+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+1+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+1.3) , grid_unit*(sy+3+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+3+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)

def drawGate_BI_NOR(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_arc(grid_unit*(sx-1+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+1+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_arc(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+1.3) , grid_unit*(sy+1+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+1+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+1.3) , grid_unit*(sy+3+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+3+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_oval(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5-0.4) , grid_unit*(sx+4+0.5+0.8) , grid_unit*(sy+2+0.5+0.4) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+5+0.5-0.2) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)

def drawGate_BI_NOT(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+1+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+3+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_polygon(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_oval(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5-0.4) , grid_unit*(sx+4+0.5+0.8) , grid_unit*(sy+2+0.5+0.4) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+5+0.5-0.2) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)

def drawGate_BI_XOR(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_arc(grid_unit*(sx-1+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+1+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_arc(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.9) , grid_unit*(sy+1+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+1+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.9) , grid_unit*(sy+3+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+3+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_arc(grid_unit*(sx-0.5-1+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx-0.5+1+0.5) , grid_unit*(sy+4+0.5) , start=-55 , extent=110 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)

def drawGate_BI_XNOR(sx,sy,id,ghost=False):
    tags="content "+id
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+3+0.5) , grid_unit*(sy+4+0.5) , outline="#EEE" , fill="#EEE" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+4+0.5) , grid_unit*(sx+2+0.5) , grid_unit*(sy+4+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_arc(grid_unit*(sx-1+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+1+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_arc(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+4+0.5) , start=-90 , extent=180 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.9) , grid_unit*(sy+1+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+1+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+0.9) , grid_unit*(sy+3+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+3+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_oval(grid_unit*(sx+4+0.5) , grid_unit*(sy+2+0.5-0.4) , grid_unit*(sx+4+0.5+0.8) , grid_unit*(sy+2+0.5+0.4) , outline="#333" , fill="#EEE" , width=thickness+1 , tags=tags)
    canvas.create_rectangle(grid_unit*(sx+5+0.5-0.2) , grid_unit*(sy+2+0.5) , grid_unit*(sx+5+0.5) , grid_unit*(sy+2+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    canvas.create_arc(grid_unit*(sx-0.5-1+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx-0.5+1+0.5) , grid_unit*(sy+4+0.5) , start=-55 , extent=110 , outline="#333" , width=thickness+1 , style="arc" , tags=tags)

gate_drawing_functions = {
    "AND": drawGate_AND,
    "NAND": drawGate_NAND,
    "CONS": drawGate_CONS,
    "NCONS": drawGate_NCONS,
    "MUL": drawGate_MUL,
    "NMUL": drawGate_NMUL,
    "OR": drawGate_OR,
    "NOR": drawGate_NOR,
    "ANY": drawGate_ANY,
    "NANY": drawGate_NANY,
    "SUM": drawGate_SUM,
    "NSUM": drawGate_NSUM,

    "PNOT": drawGate_PNOT,
    "NOT": drawGate_NOT,
    "NNOT": drawGate_NNOT,
    "ABS": drawGate_ABS,
    "INC": drawGate_INC,
    "DEC": drawGate_DEC,
    "RTU": drawGate_RTU,
    "RTD": drawGate_RTD,
    "CLU": drawGate_CLU,
    "CLD": drawGate_CLD,

    "BI_AND": drawGate_BI_AND,
    "BI_OR": drawGate_BI_OR,
    "BI_NAND": drawGate_BI_NAND,
    "BI_NOR": drawGate_BI_NOR,
    "BI_XOR": drawGate_BI_XOR,
    "BI_XNOR": drawGate_BI_XNOR,
    "BI_NOT": drawGate_BI_NOT
}

def drawGate(gate):
    gate_drawing_functions[gate["gate"]](gate["x"]-view_x, gate["y"]-view_y, gate["id"])

def drawSystem(system):
    canvas.delete(system["id"])
    sx = system["x"] - view_x
    sy = system["y"] - view_y
    tags="content "+system["id"]
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+4+0.5) , grid_unit*(sy+system["height"]-1+0.5) , outline="#333" , fill="#EEE" , width=thickness , tags=tags)
    for inputNode in system["inputs"].values():
        nsx = nodes[inputNode]["x"] - view_x
        nsy = nodes[inputNode]["y"] - view_y
        nodetag = nodes[inputNode]["tag"]
        canvas.create_rectangle(grid_unit*(nsx+0.5) , grid_unit*(nsy+0.5) , grid_unit*(nsx+1+0.5) , grid_unit*(nsy+0.5) , outline="#333" , fill="#EEE" , width=thickness , tags=tags)
        if zoomLevel>=2: canvas.create_text(grid_unit*(nsx+0.5+1.2) , grid_unit*(nsy+0.5) , anchor='w',font=(FONT_FAMILY, FONT_SIZE), fill="black", text=nodetag ,tags=tags)
    for outputNode in system["outputs"].values():
        nsx = nodes[outputNode]["x"] - view_x
        nsy = nodes[outputNode]["y"] - view_y
        nodetag = nodes[outputNode]["tag"]
        canvas.create_rectangle(grid_unit*(nsx+0.5) , grid_unit*(nsy+0.5) , grid_unit*(nsx-1+0.5) , grid_unit*(nsy+0.5) , outline="#333" , fill="#EEE" , width=thickness , tags=tags)
        if zoomLevel>=2: canvas.create_text(grid_unit*(nsx+0.5-1.2) , grid_unit*(nsy+0.5) , anchor='e',font=(FONT_FAMILY, FONT_SIZE), fill="black", text=nodetag ,tags=tags)

def drawWire(wire):
    node_a = nodes[wire["node_a"]]
    node_b = nodes[wire["node_b"]]
    canvas.delete(wire["id"])
    canvas.delete(node_a)
    canvas.delete(node_b)
    sx_a = node_a["x"] - view_x
    sy_a = node_a["y"] - view_y
    sx_b = node_b["x"] - view_x
    sy_b = node_b["y"] - view_y
    tags="content "+wire["id"]
    if sy_a != sy_b:
        canvas.create_rectangle(grid_unit*(sx_a+0.5) , grid_unit*(sy_a+0.5) , grid_unit*(sx_a+0.5) , grid_unit*(sy_b+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    if sx_a != sx_b:
        canvas.create_rectangle(grid_unit*(sx_a+0.5) , grid_unit*(sy_b+0.5) , grid_unit*(sx_b+0.5) , grid_unit*(sy_b+0.5) , outline="#333" , fill="#333" , width=thickness , tags=tags)
    if wire["id"]!="w_ghost":
        drawNode(node_a)
        drawNode(node_b)

def drawNode(node):
    canvas.delete(node["id"])
    if len(node["wires"])>2:
        sx = node["x"] - view_x
        sy = node["y"] - view_y
        tags="content "+node["id"]
        canvas.create_oval(grid_unit*(sx-0.2+0.5) , grid_unit*(sy-0.2+0.5) , grid_unit*(sx+0.2+0.5) , grid_unit*(sy+0.2+0.5) , width=0 , fill="#333" , tags=tags)

def drawInput(input):
    canvas.delete(input["id"])
    sx = input["x"] - view_x
    sy = input["y"] - view_y
    tags="content "+input["id"]
    canvas.create_rectangle(grid_unit*(sx+0.5+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+1+0.5) , grid_unit*(sy+0.5) , width=thickness , outline="#333" , fill="#333" , tags=tags)
    canvas.create_oval(grid_unit*(sx-0.5+0.5) , grid_unit*(sy-0.5+0.5) , grid_unit*(sx+0.5+0.5) , grid_unit*(sy+0.5+0.5) , width=thickness , outline="#333" , fill="#CCC" , tags=tags)
    if input["value"]==0: canvas.create_rectangle(grid_unit*(sx+0.5-0.3) , grid_unit*(sy+0.5) , grid_unit*(sx+0.5+0.3) , grid_unit*(sy+0.5) , width=thickness , outline="#333" , fill="#333" , tags=tags)
    if input["value"]==1: canvas.create_oval(grid_unit*(sx+0.5-0.25) , grid_unit*(sy+0.5-0.25) , grid_unit*(sx+0.5+0.25) , grid_unit*(sy+0.5+0.25) , width=thickness , outline="#333" , fill="#CCC" , tags=tags)
    if input["value"]==2:
        canvas.create_rectangle(grid_unit*(sx+0.5-0.3) , grid_unit*(sy+0.5) , grid_unit*(sx+0.5+0.3) , grid_unit*(sy+0.5) , width=thickness , outline="#333" , fill="#333" , tags=tags)
        canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5-0.3) , grid_unit*(sx+0.5) , grid_unit*(sy+0.5+0.3) , width=thickness , outline="#333" , fill="#333" , tags=tags)

def drawProbe(probe):
    canvas.delete(probe["id"])
    sx = probe["x"] - view_x
    sy = probe["y"] - view_y
    tags="content "+probe["id"]
    canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5+0.5) , grid_unit*(sx+0.5) , grid_unit*(sy+0.5+1) , width=thickness , outline="#333" , fill="#333" , tags=tags)
    canvas.create_polygon(grid_unit*(sx-0.5+0.5) , grid_unit*(sy-0.5+0.5) , grid_unit*(sx+0.5+0.5) , grid_unit*(sy-0.5+0.5) , grid_unit*(sx+0.5+0.5) , grid_unit*(sy+0.5+0.5) , grid_unit*(sx-0.5+0.5) , grid_unit*(sy+0.5+0.5) , width=thickness , outline="#333" , fill="#CCC" , tags=tags)
    if probe["value"]==0: canvas.create_rectangle(grid_unit*(sx+0.5-0.3) , grid_unit*(sy+0.5) , grid_unit*(sx+0.5+0.3) , grid_unit*(sy+0.5) , width=thickness , outline="#333" , fill="#333" , tags=tags)
    if probe["value"]==1: canvas.create_oval(grid_unit*(sx+0.5-0.25) , grid_unit*(sy+0.5-0.25) , grid_unit*(sx+0.5+0.25) , grid_unit*(sy+0.5+0.25) , width=thickness , outline="#333" , fill="#CCC" , tags=tags)
    if probe["value"]==2:
        canvas.create_rectangle(grid_unit*(sx+0.5-0.3) , grid_unit*(sy+0.5) , grid_unit*(sx+0.5+0.3) , grid_unit*(sy+0.5) , width=thickness , outline="#333" , fill="#333" , tags=tags)
        canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5-0.3) , grid_unit*(sx+0.5) , grid_unit*(sy+0.5+0.3) , width=thickness , outline="#333" , fill="#333" , tags=tags)

def drawOutput(output):
    canvas.delete(output["id"])
    sx = output["x"] - view_x
    sy = output["y"] - view_y
    tags="content "+output["id"]
    canvas.create_rectangle(grid_unit*(sx-0.5+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx-1+0.5) , grid_unit*(sy+0.5) , width=thickness , outline="#333" , fill="#333" , tags=tags)
    canvas.create_polygon(grid_unit*(sx-0.6+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+0.5) , grid_unit*(sy+0.6+0.5) , grid_unit*(sx+0.6+0.5) , grid_unit*(sy+0.5) , grid_unit*(sx+0.5) , grid_unit*(sy-0.6+0.5) , width=thickness , outline="#333" , fill="#CCC" , tags=tags)
    if output["value"]==0: canvas.create_rectangle(grid_unit*(sx+0.5-0.3) , grid_unit*(sy+0.5) , grid_unit*(sx+0.5+0.3) , grid_unit*(sy+0.5) , width=thickness , outline="#333" , fill="#333" , tags=tags)
    if output["value"]==1: canvas.create_oval(grid_unit*(sx+0.5-0.25) , grid_unit*(sy+0.5-0.25) , grid_unit*(sx+0.5+0.25) , grid_unit*(sy+0.5+0.25) , width=thickness , outline="#333" , fill="#CCC" , tags=tags)
    if output["value"]==2:
        canvas.create_rectangle(grid_unit*(sx+0.5-0.3) , grid_unit*(sy+0.5) , grid_unit*(sx+0.5+0.3) , grid_unit*(sy+0.5) , width=thickness , outline="#333" , fill="#333" , tags=tags)
        canvas.create_rectangle(grid_unit*(sx+0.5) , grid_unit*(sy+0.5-0.3) , grid_unit*(sx+0.5) , grid_unit*(sy+0.5+0.3) , width=thickness , outline="#333" , fill="#333" , tags=tags)

def drawTags():
    canvas.delete("tag")
    for tag,parent_id in tags.items():
        drawTag(tag,parent_id)

def drawTag(tag,parent_id):
    parent = None
    if parent_id[0]=='i':
        parent = inputs[parent_id]
        x = grid_unit*(parent['x']-view_x)
        y = grid_unit*(parent['y']-view_y+0.4)
        canvas.create_text(x-10,y,anchor='e',font=(FONT_FAMILY, FONT_SIZE), fill="black", text=tag ,tags="content tag")
    elif parent_id[0]=='o':
        parent = outputs[parent_id]
        x = grid_unit*(1+parent['x']-view_x)
        y = grid_unit*(parent['y']-view_y+0.4)
        canvas.create_text(x+10,y,anchor='w',font=(FONT_FAMILY, FONT_SIZE), fill="black", text=tag ,tags="content tag")

def drawGrid():
    canvas.delete("background")
    canvas.delete("grid")
    if zoomLevel == 0:
        canvas.create_rectangle(0,0,grid_width*grid_unit,grid_height*grid_unit,fill="#EEE",width=0, tags="background")
        return
    canvas.create_rectangle(0,0,grid_width*grid_unit,grid_height*grid_unit,fill="#CCC",width=0, tags="background")
    for yyy in range(grid_height+1):
        canvas.create_rectangle(0 , grid_unit*(yyy-0.5)+2 , grid_width*grid_unit , grid_unit*(yyy+0.5)-1 , width=0 , fill="#EEE" , tags="grid")
    for xxx in range(grid_width+1):
        canvas.create_rectangle(grid_unit*(xxx-0.5)+2 , 0 , grid_unit*(xxx+0.5)-1 , grid_height*grid_unit , width=0 , fill="#EEE" , tags="grid")

#endregion


#region [green] INTERACTION

selection = []
previousHover = [0,0]

systemModified = False
circuitModified = False

selectedTool = None
toolShortcuts = {
    'a': "g_AND",
    's': "s",
    'w': "w",
    'i': "i",
    'p': "p",
    'o': "o",
    't': "t"
}
toolNames = {
    's': "System",
    'i': "Input",
    'p': "Probe",
    'o': "Output",
    't': "Tag",
    'w': "Wire",
    'g_PNOT': "PNOT",
    'g_NOT': "NOT",
    'g_NNOT': "NNOT",
    'g_ABS': "ABS",
    'g_INC': "INC",
    'g_DEC': "DEC",
    'g_RTU': "RTU",
    'g_RTD': "RTD",
    'g_CLU': "CLU",
    'g_CLD': "CLD",
    'g_AND': "AND",
    'g_CONS': "CONS",
    'g_MUL': "MUL",
    'g_OR': "OR",
    'g_ANY': "ANY",
    'g_SUM': "SUM",
    'g_BI_AND': "BI_AND",
    'g_BI_OR': "BI_OR",
    'g_BI_NAND': "BI_NAND",
    'g_BI_NOR': "BI_NOR",
    'g_BI_XOR': "BI_XOR",
    'g_BI_XNOR': "BI_XNOR",
    'g_BI_NOT': "BI_NOT"
}

zoomLevel = 3


def setSystemModified(mod=True):
    global systemModified
    systemModified = mod

def setCircuitModified(mod=True):
    global circuitModified
    circuitModified = mod

def selectTool(tool):
    global selectedTool
    selectedTool = tool
    canvas.delete("ghost")
    if tool != 'w':
        global temp_node
        temp_node = None
        canvas.delete("w_ghost")
        canvas.delete("n_ghost")
        remove("n_ghost")
        updateScreen()
    if selectedTool: toolLabelText.set(toolNames[selectedTool])
    else: toolLabelText.set("Select")

def debug_screenMap():
    canvas.delete("debug")
    for xxx in range(grid_width):
        for yyy in range(grid_height):
            if screen[xxx][yyy]==None: continue
            elif screen[xxx][yyy][0]=='w': canvas.create_rectangle(xxx*grid_unit, yyy*grid_unit, (xxx+1)*grid_unit, (yyy+1)*grid_unit, width=0, fill="#FBB", stipple="gray50", tags="debug")
            elif screen[xxx][yyy][0]=='n': canvas.create_rectangle(xxx*grid_unit, yyy*grid_unit, (xxx+1)*grid_unit, (yyy+1)*grid_unit, width=0, fill="#FBF", stipple="gray50", tags="debug")
            elif screen[xxx][yyy][0]=='g': canvas.create_rectangle(xxx*grid_unit, yyy*grid_unit, (xxx+1)*grid_unit, (yyy+1)*grid_unit, width=0, fill="#BFB", stipple="gray50", tags="debug")
            elif screen[xxx][yyy][0]=='s': canvas.create_rectangle(xxx*grid_unit, yyy*grid_unit, (xxx+1)*grid_unit, (yyy+1)*grid_unit, width=0, fill="#BFF", stipple="gray50", tags="debug")
            elif screen[xxx][yyy][0]=='i': canvas.create_rectangle(xxx*grid_unit, yyy*grid_unit, (xxx+1)*grid_unit, (yyy+1)*grid_unit, width=0, fill="#FFB", stipple="gray50", tags="debug")
            elif screen[xxx][yyy][0]=='p': canvas.create_rectangle(xxx*grid_unit, yyy*grid_unit, (xxx+1)*grid_unit, (yyy+1)*grid_unit, width=0, fill="#FEB", stipple="gray50", tags="debug")
            elif screen[xxx][yyy][0]=='o': canvas.create_rectangle(xxx*grid_unit, yyy*grid_unit, (xxx+1)*grid_unit, (yyy+1)*grid_unit, width=0, fill="#EFB", stipple="gray50", tags="debug")

def updateScreen():
    global screen
    for xxx in range(grid_width):
        for yyy in range(grid_height):
            screen[xxx][yyy] = None
    for gate in gates.values():
        updateScreen_gate(gate)
    for system in systems.values():
        updateScreen_system(system)
    for wire in wires.values():
        updateScreen_wire(wire)
    for node in nodes.values():
        updateScreen_node(node)
    for input in inputs.values():
        updateScreen_input(input)
    for probe in probes.values():
        updateScreen_probe(probe)
    for output in outputs.values():
        updateScreen_output(output)
    # debug_screenMap()

def updateScreen_gate(gate):
    sx = gate["x"] - view_x
    sy = gate["y"] - view_y
    for xxx in range(sx-1, sx+6):
        for yyy in range(sy, sy+5):
            if xxx in range(grid_width) and yyy in range(grid_height):
                screen[xxx][yyy] = gate["id"]

def updateScreen_system(system):
    sx = system["x"] - view_x
    sy = system["y"] - view_y
    for xxx in range(sx-1, sx+6):
        for yyy in range(sy, sy+system["height"]):
            if xxx in range(grid_width) and yyy in range(grid_height):
                screen[xxx][yyy] = system["id"]

def updateScreen_wire(wire):
    sx_a = nodes[wire["node_a"]]["x"] - view_x
    sy_a = nodes[wire["node_a"]]["y"] - view_y
    sx_b = nodes[wire["node_b"]]["x"] - view_x
    sy_b = nodes[wire["node_b"]]["y"] - view_y
    for xxx in range(sx_a, sx_b+1):
        if xxx in range(grid_width) and sy_a in range(grid_height):
            screen[xxx][sy_b] = wire["id"]
    for xxx in range(sx_b, sx_a+1):
        if xxx in range(grid_width) and sy_a in range(grid_height):
            screen[xxx][sy_b] = wire["id"]
    for yyy in range(sy_a, sy_b+1):
        if yyy in range(grid_height) and sx_a in range(grid_width):
            screen[sx_a][yyy] = wire["id"]
    for yyy in range(sy_b, sy_a+1):
        if yyy in range(grid_height) and sx_a in range(grid_width):
            screen[sx_a][yyy] = wire["id"]

def updateScreen_node(node):
    sx = node["x"] - view_x
    sy = node["y"] - view_y
    if sx in range(grid_width) and sy in range(grid_height):
        screen[sx][sy] = node["id"]

def updateScreen_input(input):
    sx = input["x"] - view_x
    sy = input["y"] - view_y
    if sx in range(grid_width) and sy in range(grid_height):
        screen[sx][sy] = input["id"]
    updateScreen_node(nodes[input["node"]])

def updateScreen_probe(probe):
    sx = probe["x"] - view_x
    sy = probe["y"] - view_y
    if sx in range(grid_width) and sy in range(grid_height):
        screen[sx][sy] = probe["id"]
    updateScreen_node(nodes[probe["node"]])

def updateScreen_output(output):
    sx = output["x"] - view_x
    sy = output["y"] - view_y
    if sx in range(grid_width) and sy in range(grid_height): 
        screen[sx][sy] = output["id"]
    updateScreen_node(nodes[output["node"]])

def moveBy_gate(id,dx,dy):
    canvas.move(id, dx*grid_unit, dy*grid_unit)
    gates[id]["x"]+=dx
    gates[id]["y"]+=dy
    moveBy_node(gates[id]["output"], dx,dy)
    moveBy_node(gates[id]["input_a"], dx,dy)
    if "input_b" in gates[id]: moveBy_node(gates[id]["input_b"], dx,dy)

def moveBy_system(system_id,dx,dy):
    system = systems[system_id]
    canvas.move(system_id, dx*grid_unit, dy*grid_unit)
    system["x"]+=dx
    system["y"]+=dy
    for input_id in system["inputs"].values():
        moveBy_node(input_id, dx,dy)
    for output_id in system["outputs"].values():
        moveBy_node(output_id, dx,dy)

def moveBy_node(id,dx,dy):
    canvas.move(id, dx*grid_unit, dy*grid_unit)
    nodes[id]["x"]+=dx
    nodes[id]["y"]+=dy
    for wire in nodes[id]["wires"]:
        drawWire(wires[wire])

def moveBy_input(id,dx,dy):
    canvas.move(id, dx*grid_unit, dy*grid_unit)
    inputs[id]["x"]+=dx
    inputs[id]["y"]+=dy
    moveBy_node(inputs[id]["node"], dx,dy)

def moveBy_probe(id,dx,dy):
    canvas.move(id, dx*grid_unit, dy*grid_unit)
    probes[id]["x"]+=dx
    probes[id]["y"]+=dy
    moveBy_node(probes[id]["node"], dx,dy)

def moveBy_output(id,dx,dy):
    canvas.move(id, dx*grid_unit, dy*grid_unit)
    outputs[id]["x"]+=dx
    outputs[id]["y"]+=dy
    moveBy_node(outputs[id]["node"], dx,dy)

def moveBy(dx,dy):
    if selection==[]:
        global view_x
        global view_y
        view_x += dx
        view_y += dy
        viewPositionLabelText.set(str(view_x)+" ; "+str(view_y))
        canvas.move("content", -dx*grid_unit, -dy*grid_unit)
    else:
        for id in selection:
            if id[0]=='g' and not canMove_gate(gates[id]["x"], gates[id]["y"],dx,dy,selection): return
            elif id[0]=='s' and not canMove_system(id,dx,dy,selection): return
            elif id[0]=='n' and not canMove_node(nodes[id]["x"], nodes[id]["y"],dx,dy,selection): return
            elif id[0]=='i' and not canMove_input(inputs[id]["x"], inputs[id]["y"],dx,dy,selection): return
            elif id[0]=='p' and not canMove_probe(probes[id]["x"], probes[id]["y"],dx,dy,selection): return
            elif id[0]=='o' and not canMove_output(outputs[id]["x"], outputs[id]["y"],dx,dy,selection): return
        for id in selection:
            if id[0]=='g': moveBy_gate(id,dx,dy)
            elif id[0]=='s': moveBy_system(id,dx,dy)
            elif id[0]=='n': moveBy_node(id,dx,dy)
            elif id[0]=='i': moveBy_input(id,dx,dy)
            elif id[0]=='p': moveBy_probe(id,dx,dy)
            elif id[0]=='o': moveBy_output(id,dx,dy)
        canvas.move("selection", dx*grid_unit, dy*grid_unit)
        drawTags()
    updateScreen()
    setCircuitModified()

def zoom(dz):
    global grid_width
    global grid_height
    global grid_unit
    global thickness
    global zoomLevel
    global screen
    if not zoomLevel+dz in range(0,4): return
    zoomLevel +=dz
    if zoomLevel==3:
        grid_width = GRID_WIDTH
        grid_height = GRID_HEIGHT
        grid_unit = GRID_UNIT
        thickness = THICKNESS
        screen = [[None for yyy in range(grid_height)] for xxx in range(grid_width)]
        updateScreen()
        if dz==1: moveBy(+int(GRID_WIDTH/2),+int(GRID_HEIGHT/2))
    elif zoomLevel==2:
        grid_width = GRID_WIDTH*2
        grid_height = GRID_HEIGHT*2
        grid_unit = GRID_UNIT/2
        thickness = THICKNESS/2
        screen = [[None for yyy in range(grid_height)] for xxx in range(grid_width)]
        updateScreen()
        if dz==1: moveBy(+GRID_WIDTH,+GRID_HEIGHT)
        if dz==-1: moveBy(-int(GRID_WIDTH/2),-int(GRID_HEIGHT/2))
    elif zoomLevel==1:
        grid_width = GRID_WIDTH*4
        grid_height = GRID_HEIGHT*4
        grid_unit = GRID_UNIT/4
        thickness = THICKNESS/4
        screen = [[None for yyy in range(grid_height)] for xxx in range(grid_width)]
        updateScreen()
        if dz==1: moveBy(+GRID_WIDTH*2,+GRID_HEIGHT*2)
        if dz==-1: moveBy(-GRID_WIDTH,-GRID_HEIGHT)
    elif zoomLevel==0:
        grid_width = GRID_WIDTH*8
        grid_height = GRID_HEIGHT*8
        grid_unit = GRID_UNIT/8
        thickness = THICKNESS/4
        screen = [[None for yyy in range(grid_height)] for xxx in range(grid_width)]
        updateScreen()
        if dz==-1: moveBy(-GRID_WIDTH*2,-GRID_HEIGHT*2)
    drawGrid()
    drawAll()
    drawSelection()

def canPlace_gate(sx,sy):
    for xxx in range(sx-3, sx+5):
        for yyy in range(sy-2, sy+3):
            if sx in range(3,grid_width-3) and sy in range(2,grid_height-2):
                if screen[xxx][yyy]!=None: return False
    return True

def canPlace_system(loadedSystem_id,sx,sy):
    # for xxx in range(sx-3, sx+5):
    #     for yyy in range(sy-2, sy+3):
    #         if sx in range(3,grid_width-3) and sy in range(2,grid_height-2):
    #             if screen[xxx][yyy]!=None: return False
    return True

def canPlace_input(sx,sy):
    if sx in range(0,grid_width-1) and sy in range(0,grid_height) and screen[sx][sy]==None and screen[sx+1][sy]==None: return True
    else: return False

def canPlace_probe(sx,sy):
    if sx in range(0,grid_width) and sy in range(0,grid_height-1) and screen[sx][sy]==None and screen[sx][sy+1]==None: return True
    else: return False

def canPlace_output(sx,sy):
    if sx in range(1,grid_width) and sy in range(0,grid_height) and screen[sx][sy]==None and screen[sx-1][sy]==None: return True
    else: return False

def canMove_gate(sx,sy,dx,dy,selection):
    sx -= view_x
    sy -= view_y
    if not (sx in range(1-dx,grid_width-5-dx) and sy in range(0-dy,grid_height-4-dy)): return False
    if dx==+1:
        for yyy in range(sy, sy+5):
            if screen[sx+6][yyy]!=None and screen[sx+6][yyy][0] !='w' and not screen[sx+6][yyy] in selection: return False
    elif dx==-1:
        for yyy in range(sy, sy+5):
            if screen[sx-2][yyy]!=None and screen[sx-2][yyy][0] !='w' and not screen[sx-2][yyy] in selection: return False
    if dy==+1:
        for xxx in range(sx-1, sx+6):
            if screen[xxx][sy+5]!=None and screen[xxx][sy+5][0] !='w' and not screen[xxx][sy+5] in selection: return False
    elif dy==-1:
        for xxx in range(sx-1, sx+6):
            if screen[xxx][sy-1]!=None and screen[xxx][sy-1][0] !='w' and not screen[xxx][sy-1] in selection: return False
    return True

def canMove_system(system_id,dx,dy,selection):
    system = systems[system_id]
    sx = system["x"] - view_x
    sy = system["y"] - view_y
    s_height = system["height"]
    if not (sx in range(1-dx,grid_width-5-dx) and sy in range(0-dy,grid_height-s_height+1-dy)): return False
    if dx==+1:
        for yyy in range(sy, sy+s_height):
            if screen[sx+6][yyy]!=None and screen[sx+6][yyy][0] !='w' and not screen[sx+6][yyy] in selection: return False
    elif dx==-1:
        for yyy in range(sy, sy+s_height):
            if screen[sx-2][yyy]!=None and screen[sx-2][yyy][0] !='w' and not screen[sx-2][yyy] in selection: return False
    if dy==+1:
        for xxx in range(sx-1, sx+6):
            if screen[xxx][sy+s_height]!=None and screen[xxx][sy+s_height][0] !='w' and not screen[xxx][sy+s_height] in selection: return False
    elif dy==-1:
        for xxx in range(sx-1, sx+s_height):
            if screen[xxx][sy-1]!=None and screen[xxx][sy-1][0] !='w' and not screen[xxx][sy-1] in selection: return False
    return True

def canMove_node(sx,sy,dx,dy,selection):
    sx -= view_x
    sy -= view_y
    if not (sx in range(1-dx,grid_width-1-dx) and sy in range(0-dy,grid_height-1-dy)): return False
    if dx==+1:
        if screen[sx+1][sy]!=None and screen[sx+1][sy][0] !='w' and not screen[sx+1][sy] in selection: return False
    elif dx==-1:
        if screen[sx-1][sy]!=None and screen[sx-1][sy][0] !='w' and not screen[sx-1][sy] in selection: return False
    if dy==+1:
        if screen[sx][sy+1]!=None and screen[sx][sy+1][0] !='w' and not screen[sx][sy+1] in selection: return False
    elif dy==-1:
        if screen[sx][sy-1]!=None and screen[sx][sy-1][0] !='w' and not screen[sx][sy-1] in selection: return False
    return True

def canMove_input(sx,sy,dx,dy,selection):
    sx -= view_x
    sy -= view_y
    if not (sx in range(0-dx,grid_width-1-dx) and sy in range(0-dy,grid_height-dy)): return False
    if dx==+1:
        if screen[sx+2][sy]!=None and screen[sx+2][sy][0] !='w' and not screen[sx+2][sy] in selection: return False
    elif dx==-1:
        if screen[sx-1][sy]!=None and screen[sx-1][sy][0] !='w' and not screen[sx-1][sy] in selection: return False
    if dy==+1:
        if screen[sx][sy+1]!=None and screen[sx][sy+1][0] !='w' and not screen[sx][sy+1] in selection: return False
        if screen[sx+1][sy+1]!=None and screen[sx+1][sy+1][0] !='w' and not screen[sx+1][sy+1] in selection: return False
    elif dy==-1:
        if screen[sx][sy-1]!=None and screen[sx][sy-1][0] !='w' and not screen[sx][sy-1] in selection: return False
        if screen[sx+1][sy-1]!=None and screen[sx+1][sy-1][0] !='w' and not screen[sx+1][sy-1] in selection: return False
    return True

def canMove_probe(sx,sy,dx,dy,selection):
    sx -= view_x
    sy -= view_y
    if not (sx in range(0-dx,grid_width-dx) and sy in range(0-dy,grid_height-1-dy)): return False
    if dx==+1:
        if screen[sx+1][sy]!=None and screen[sx+1][sy][0] !='w' and not screen[sx+1][sy] in selection: return False
        if screen[sx+1][sy+1]!=None and screen[sx+1][sy+1][0] !='w' and not screen[sx+1][sy+1] in selection: return False
    elif dx==-1:
        if screen[sx-1][sy]!=None and screen[sx-1][sy][0] !='w' and not screen[sx-1][sy] in selection: return False
        if screen[sx-1][sy+1]!=None and screen[sx-1][sy+1][0] !='w' and not screen[sx-1][sy+1] in selection: return False
    if dy==+1:
        if screen[sx][sy+2]!=None and screen[sx][sy+2][0] !='w' and not screen[sx][sy+2] in selection: return False
    elif dy==-1:
        if screen[sx][sy-1]!=None and screen[sx][sy-1][0] !='w' and not screen[sx][sy-1] in selection: return False
    return True

def canMove_output(sx,sy,dx,dy,selection):
    sx -= view_x
    sy -= view_y
    if not (sx in range(1-dx,grid_width-dx) and sy in range(0-dy,grid_height-dy)): return False
    if dx==+1:
        if screen[sx+1][sy]!=None and screen[sx+1][sy][0] !='w' and not screen[sx+1][sy] in selection: return False
    elif dx==-1:
        if screen[sx-2][sy]!=None and screen[sx-2][sy][0] !='w' and not screen[sx-2][sy] in selection: return False
    if dy==+1:
        if screen[sx][sy+1]!=None and screen[sx][sy+1][0] !='w' and not screen[sx][sy+1] in selection: return False
        if screen[sx-1][sy+1]!=None and screen[sx-1][sy+1][0] !='w' and not screen[sx-1][sy+1] in selection: return False
    elif dy==-1:
        if screen[sx][sy-1]!=None and screen[sx][sy-1][0] !='w' and not screen[sx][sy-1] in selection: return False
        if screen[sx-1][sy-1]!=None and screen[sx-1][sy-1][0] !='w' and not screen[sx-1][sy-1] in selection: return False
    return True

def remove(id):
    if id[0]=='g' and id in gates:
        remove_gate(id)
    elif id[0]=='s' and id in systems:
        remove_system(id)
    elif id[0]=='n' and id in nodes and not nodes[id]["parent"]:
        remove_node(id)
    elif id[0]=='w' and id in wires:
        remove_wire(id)
    elif id[0]=='i' and id in inputs:
        remove_input(id)
    elif id[0]=='p' and id in probes:
        remove_probe(id)
    elif id[0]=='o' and id in outputs:
        remove_output(id)
    canvas.delete(id)

def remove_gate(gate_id):
    gate = gates[gate_id]
    # removing the gate mark from the input and output nodes, otherwise they wouldn't be removed
    nodes[gate["input_a"]]["parent"] = None
    if "input_b" in gate: nodes[gate["input_b"]]["parent"] = None
    nodes[gate["output"]]["parent"] = None
    # removing the input and output nodes
    remove(gate["input_a"])
    if "input_b" in gate: remove(gate["input_b"])
    remove(gate["output"])
    # removes the gate from the list of gates
    del gates[gate_id]

def remove_system(system_id):
    system = systems[system_id]
    for input_id in system["inputs"].values():
        nodes[input_id]["parent"] = None
        remove(input_id)
    for output_id in system["outputs"].values():
        nodes[output_id]["parent"] = None
        remove(output_id)
    del systems[system_id]

def remove_node(node_id):
    node = nodes[node_id]
    # removes every wire connected to this node
    for wire in node["wires"]:
        if not wire in wires: continue # to solve a bug with w_ghost
        wire = wires[wire]
        # removes the node from the wire before removing the wire, otherwise remove would be called recursively infinitely
        if wire["node_a"]==node_id: wire["node_a"]=None
        if wire["node_b"]==node_id: wire["node_b"]=None
            # remove the wire
        remove(wire["id"])
    # remove the node from the list of nodes
    del nodes[node_id]

def remove_wire(wire_id):
    wire = wires[wire_id]
    if wire["node_a"]!=None:
        nodes[wire["node_a"]]["wires"].remove(wire_id)
        if len(nodes[wire["node_a"]]["wires"])==0: remove(wire["node_a"])
    if wire["node_b"]!=None:
        nodes[wire["node_b"]]["wires"].remove(wire_id)
        if len(nodes[wire["node_b"]]["wires"])==0: remove(wire["node_b"])
    del wires[wire_id]

def remove_input(input_id):
    input = inputs[input_id]
    nodes[input["node"]]["parent"] = None
    remove(input["node"])
    del inputs[input_id]

def remove_probe(probe_id):
    probe = probes[probe_id]
    nodes[probe["node"]]["parent"] = None
    remove(probe["node"])
    del probes[probe_id]

def remove_output(output_id):
    output = outputs[output_id]
    nodes[output["node"]]["parent"] = None
    remove(output["node"])
    del outputs[output_id]

def removeSelection():
    global selection
    for id in selection: remove(id)
    selection = []
    updateScreen()
    setCircuitModified()
    setSystemModified()

def select(id=None, add=False):
    global selection
    if not add:
        canvas.delete("selection")
        selection = []
    if id!=None:
        if id[0]=='n' and nodes[id]["parent"]: id = nodes[id]["parent"]
        if not id in selection: selection.append(id)
        drawSelection()
    else: selection = []

def drawSelection():
    canvas.delete("selection")
    for id in selection:
        if id[0]=='g':
            sx = gates[id]["x"] - view_x
            sy = gates[id]["y"] - view_y
            canvas.create_rectangle((sx-1)*grid_unit , sy*grid_unit , (sx+6)*grid_unit , (sy+5)*grid_unit , width=0 , fill="#00F" , stipple="gray12" , tags="selection")
        elif id[0]=='n':
            sx = nodes[id]["x"] - view_x
            sy = nodes[id]["y"] - view_y
            canvas.create_rectangle(sx*grid_unit , sy*grid_unit , (sx+1)*grid_unit , (sy+1)*grid_unit , width=0 , fill="#00F" , stipple="gray12" , tags="selection")
        elif id[0]=='i':
            sx = inputs[id]["x"] - view_x
            sy = inputs[id]["y"] - view_y
            canvas.create_rectangle(sx*grid_unit , sy*grid_unit , (sx+2)*grid_unit , (sy+1)*grid_unit , width=0 , fill="#00F" , stipple="gray12" , tags="selection")
        elif id[0]=='p':
            sx = probes[id]["x"] - view_x
            sy = probes[id]["y"] - view_y
            canvas.create_rectangle(sx*grid_unit , sy*grid_unit , (sx+1)*grid_unit , (sy+2)*grid_unit , width=0 , fill="#00F" , stipple="gray12" , tags="selection")
        elif id[0]=='o':
            sx = outputs[id]["x"] - view_x
            sy = outputs[id]["y"] - view_y
            canvas.create_rectangle((sx-1)*grid_unit , sy*grid_unit , (sx+1)*grid_unit , (sy+1)*grid_unit , width=0 , fill="#00F" , stipple="gray12" , tags="selection")

def addTag(sx,sy):
    global tags
    global tag_idgen
    parent = screen[sx][sy]
    if parent!=None and parent[0] in ('i','o') and parent not in tags.values():
        tag = "t_"+str(tag_idgen)
        tag_idgen +=1
        tags[tag] = parent
        drawTags()
        labelPopup("Enter the tag name", changeTag, tag)

def changeTag(new_tag, old_tag):
    global tags
    tags[new_tag] = tags[old_tag]
    del tags[old_tag]
    drawTags()
    setCircuitModified()
    setSystemModified()

def labelPopup(text, func, arg):
    popup = Toplevel(root)
    text_label = Label(popup, text=text, font=(FONT_FAMILY, FONT_SIZE), width=28)
    text_label.pack()
    entryField = Entry(popup, font=(FONT_FAMILY, FONT_SIZE))
    entryField.pack()
    validateButton = Button(popup, text="Tag", font=(FONT_FAMILY, FONT_SIZE), command=lambda: func(entryField.get(), arg))
    validateButton.pack()

def hover(event):
    global previousHover
    sx = int(event.x/grid_unit)
    sy = int(event.y/grid_unit)
    if previousHover == [sx, sy]: return
    previousHover = [sx, sy]
    canvas.delete("ghost")
    if selectedTool==None: return
    if selectedTool[0]=='g':
        canvas.create_rectangle(grid_unit*(sx-3+0.5) , grid_unit*(sy-2+0.5) , grid_unit*(sx+3+0.5) , grid_unit*(sy+2+0.5) , width=0 , fill="#AAA" , stipple="gray12" , tags="ghost")
    elif selectedTool[0]=='s':
        t_height = max(loadedSystems[loadedSystemToBePlaced_id].nbrinput , loadedSystems[loadedSystemToBePlaced_id].nbroutput)+2
        canvas.create_rectangle(grid_unit*(sx-3+0.5) , grid_unit*(sy-1+0.5) , grid_unit*(sx+3+0.5) , grid_unit*(sy+t_height+0.5) , width=0 , fill="#AAA" , stipple="gray12" , tags="ghost")
    elif selectedTool[0]=='w':
        canvas.create_rectangle(grid_unit*(sx) , grid_unit*(sy) , grid_unit*(sx+1) , grid_unit*(sy+1) , width=0 , fill="#AAA" , stipple="gray12" , tags="ghost")
        if temp_node != None:
            ghost_node = {
                "id": "n_ghost",
                "x": sx + view_x,
                "y": sy + view_y,
                "gate": None,
                "parent": None,
                "wires": ["w_ghost"]
            }
            nodes["n_ghost"] = ghost_node
            ghost_wire = {
                "id": "w_ghost",
                "node_a": "n_ghost",
                "node_b": temp_node
            }
            drawWire(ghost_wire)
    elif selectedTool[0]=='i':
        canvas.create_rectangle(grid_unit*(sx) , grid_unit*(sy) , grid_unit*(sx+2) , grid_unit*(sy+1) , width=0 , fill="#AAA" , stipple="gray12" , tags="ghost")
    elif selectedTool[0]=='p':
        canvas.create_rectangle(grid_unit*(sx) , grid_unit*(sy) , grid_unit*(sx+1) , grid_unit*(sy+2) , width=0 , fill="#AAA" , stipple="gray12" , tags="ghost")
    elif selectedTool[0]=='o':
        canvas.create_rectangle(grid_unit*(sx-1) , grid_unit*(sy) , grid_unit*(sx+1) , grid_unit*(sy+1) , width=0 , fill="#AAA" , stipple="gray12" , tags="ghost")

def leftClick(event, shift=False):
    global selection
    global loadedSystemToBePlaced_id
    sx = int(event.x/grid_unit)
    sy = int(event.y/grid_unit)
    if selectedTool!=None:    
        if selectedTool[0]=='g':
            if canPlace_gate(sx,sy) and sx in range(3,grid_width-3) and sy in range(2,grid_height-2):
                createGate(selectedTool[2:], sx-2, sy-2)
        elif selectedTool[0]=='s':
            if loadedSystemToBePlaced_id and canPlace_system(loadedSystemToBePlaced_id,sx-2,sy):
                createSystem(sx-2,sy)
                loadedSystemToBePlaced_id = None
                selectTool(None)
        elif selectedTool[0]=='w':
            createWire(sx,sy)
        elif selectedTool[0]=='i':
            if canPlace_input(sx,sy):
                createInput(sx,sy)
        elif selectedTool[0]=='p':
            if canPlace_probe(sx,sy):
                createProbe(sx,sy)
        elif selectedTool[0]=='o':
            if canPlace_output(sx,sy):
                createOutput(sx,sy)
        elif selectedTool[0]=='t':
            addTag(sx,sy)
        setCircuitModified()
        setSystemModified()
    else:
        if screen[sx][sy]!=None:
            select(screen[sx][sy], shift)
            return
        else:
            select()

def rightClick(event):
    sx = int(event.x/grid_unit)
    sy = int(event.y/grid_unit)
    if screen[sx][sy]!=None and screen[sx][sy][0]=='i':
        input = inputs[screen[sx][sy]]
        input["value"]+=1
        input["value"]%=3
        drawInput(input)

def key(event):
    k = event.char.lower()
    if k in toolShortcuts:
        selectTool(toolShortcuts[k])

canvas.focus_set()
canvas.bind("<Button-1>", lambda event: leftClick(event))
canvas.bind("<Shift-Button-1>", lambda event: leftClick(event, True))
canvas.bind("<Button-3>", lambda event: rightClick(event))
canvas.bind("<Motion>", lambda event: hover(event))

canvas.bind("<Escape>", lambda event: selectTool(None))
canvas.bind("<Delete>", lambda event: removeSelection())

canvas.bind("<Return>", lambda event: simulateCc())
# canvas.bind("<Return>", lambda event: randomPrograms(50)) #debug
canvas.bind("<Control-Return>", lambda event: simulateDt())

canvas.bind("<Left>", lambda event: moveBy(-1,0))
canvas.bind("<Right>", lambda event: moveBy(+1,0))
canvas.bind("<Up>", lambda event: moveBy(0,-1))
canvas.bind("<Down>", lambda event: moveBy(0,+1))

canvas.bind("<Shift-Left>", lambda event: moveBy(-int(grid_width*SHIFT_MOVE_PERCENTAGE),0))
canvas.bind("<Shift-Right>", lambda event: moveBy(+int(grid_width*SHIFT_MOVE_PERCENTAGE),0))
canvas.bind("<Shift-Up>", lambda event: moveBy(0,-int(grid_height*SHIFT_MOVE_PERCENTAGE)))
canvas.bind("<Shift-Down>", lambda event: moveBy(0,+int(grid_height*SHIFT_MOVE_PERCENTAGE)))

canvas.bind("<Key>", key)
canvas.bind("<$>", lambda event: zoom(1))
canvas.bind("<*>", lambda event: zoom(-1))

canvas.bind("<Control-s>", lambda event: saveCircuit())
canvas.bind("<Control-o>", lambda event: loadCircuit())
canvas.bind("<Control-e>", lambda event: exportSystem())
canvas.bind("<Control-i>", lambda event: importSystem())
canvas.bind("<Control-m>", lambda event: importMemory())
canvas.bind("<Control-n>", lambda event: blankCircuit())
canvas.bind("<Control-r>", lambda event: spawnRegisterPopup())

canvas.bind("<Alt-r>", lambda event: resetSimulation())

#endregion


#region [yellow] INTERFACE

buttonFrame = Frame(root)
label_tools = Label(buttonFrame, text="Tools", height=1 , width=BUTTON_WIDTH , font=(FONT_FAMILY, FONT_SIZE) ) .grid(row=0, column=0)
button_wire = Button(buttonFrame, text="Wire", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("w") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=1, column=0)
button_input = Button(buttonFrame, text="Input", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("i") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=2, column=0)
button_probe = Button(buttonFrame, text="Probe", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("p") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=3, column=0)
button_output = Button(buttonFrame, text="Output", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("o") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=4, column=0)
button_tag = Button(buttonFrame, text="Tag", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("t") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=5, column=0)
label_gates = Label(buttonFrame, text="Gates", height=1 , width=BUTTON_WIDTH , font=(FONT_FAMILY, FONT_SIZE) ) .grid(row=6, column=0)
button_PNOT = Button(buttonFrame, text="PNOT", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("g_PNOT") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=7, column=0)
button_NOT = Button(buttonFrame, text="NOT", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("g_NOT") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=8, column=0)
button_NNOT = Button(buttonFrame, text="NNOT", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("g_NNOT") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=9, column=0)
button_ABS = Button(buttonFrame, text="ABS", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("g_ABS") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=10, column=0)
button_INC = Button(buttonFrame, text="INC", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("g_INC") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=11, column=0)
button_DEC = Button(buttonFrame, text="DEC", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("g_DEC") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=12, column=0)
button_RTU = Button(buttonFrame, text="RTU", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("g_RTU") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=13, column=0)
button_RTD = Button(buttonFrame, text="RTD", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("g_RTD") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=14, column=0)
button_CLU = Button(buttonFrame, text="CLU", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("g_CLU") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=15, column=0)
button_CLD = Button(buttonFrame, text="CLD", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("g_CLD") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=16, column=0)
label_gap1 = Label(buttonFrame, text=" ", height=1 , width=BUTTON_WIDTH , font=(FONT_FAMILY, FONT_SIZE) ) .grid(row=17, column=0)
button_AND = Button(buttonFrame, text="AND", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("g_AND") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=18, column=0)
button_OR = Button(buttonFrame, text="OR", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("g_OR") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=19, column=0)
button_CONS = Button(buttonFrame, text="CONS", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("g_CONS") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=20, column=0)
button_ANY = Button(buttonFrame, text="ANY", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("g_ANY") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=21, column=0)
button_MUL = Button(buttonFrame, text="MUL", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("g_MUL") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=22, column=0)
button_SUM = Button(buttonFrame, text="SUM", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("g_SUM") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=23, column=0)
label_bigates = Label(buttonFrame, text="BI Gates", height=1 , width=BUTTON_WIDTH , font=(FONT_FAMILY, FONT_SIZE) ) .grid(row=24, column=0)
button_BI_AND = Button(buttonFrame, text="BI_AND", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("g_BI_AND") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=25, column=0)
button_BI_OR = Button(buttonFrame, text="BI_OR", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("g_BI_OR") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=26, column=0)
button_BI_NAND = Button(buttonFrame, text="BI_NAND", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("g_BI_NAND") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=27, column=0)
button_BI_NOR = Button(buttonFrame, text="BI_NOR", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("g_BI_NOR") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=28, column=0)
button_BI_XOR = Button(buttonFrame, text="BI_XOR", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("g_BI_XOR") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=29, column=0)
button_BI_XNOR = Button(buttonFrame, text="BI_XNOR", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("g_BI_XNOR") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=30, column=0)
button_BI_NOT = Button(buttonFrame, text="BI_NOT", height=1 , width=BUTTON_WIDTH , command=lambda: selectTool("g_BI_NOT") , font=(FONT_FAMILY, FONT_SIZE) , bg="#CCC" ) .grid(row=31, column=0)
buttonFrame.columnconfigure(index=0,minsize=TKINTER_SCALING*100)

bottomFrame = Frame(root)
viewPositionLabelText = StringVar()
viewPositionLabelText.set(str(view_x)+" ; "+str(view_y))
label_view = Label(bottomFrame , width=5 , textvariable=viewPositionLabelText , font=(FONT_FAMILY, FONT_SIZE) ) .grid(row=0, column=0)
toolLabelText = StringVar()
toolLabelText.set(selectedTool)
label_tool = Label(bottomFrame , width=5 , textvariable=toolLabelText , font=(FONT_FAMILY, FONT_SIZE) ) .grid(row=0, column=1)
bottomFrame.rowconfigure(index=0,minsize=20)

chronogram_height = canvas_height
simulationPanel = Frame(root)
chronogram = Canvas(root, width=CHRONOGRAM_WIDTH, height=chronogram_height)

def drawChronogram():
    chronogram.delete("all")
    drawChronogram_grid()
    if len(recording)>0:
        gap = min(2*CHRONOGRAM_MARGIN_HORIZONTAL, (chronogram_height-40-2*CHRONOGRAM_MARGIN_VERTICAL-(len(recording)-1)*20)/len(recording))
        kkk=0
        for stream_id, stream in recording.items():
            yyy = 20 + (20+gap)*kkk
            kkk+=1
            if len(stream)>0:
                drawChronogram_stream(yyy,gap,stream_id,stream)
    drawChronogram_axis()

def drawChronogram_axis():
    chronogram.delete("axis")
    chronogram.create_rectangle(CHRONOGRAM_MARGIN_HORIZONTAL,CHRONOGRAM_MARGIN_VERTICAL , CHRONOGRAM_MARGIN_HORIZONTAL,chronogram_height-CHRONOGRAM_MARGIN_VERTICAL, fill="#777", outline="#777", width=2, tags="axis")
    chronogram.create_rectangle(CHRONOGRAM_MARGIN_HORIZONTAL,chronogram_height-CHRONOGRAM_MARGIN_VERTICAL , CHRONOGRAM_WIDTH-CHRONOGRAM_MARGIN_HORIZONTAL,chronogram_height-CHRONOGRAM_MARGIN_VERTICAL, fill="#777", outline="#777", width=2, tags="axis")

def drawChronogram_grid():
    chronogram.delete("grid")
    if clockCycle==0: return
    for kkk in range(clockCycle):
        xxx = CHRONOGRAM_MARGIN_HORIZONTAL+(1+kkk)*(CHRONOGRAM_WIDTH-2*CHRONOGRAM_MARGIN_HORIZONTAL)/clockCycle
        chronogram.create_rectangle(xxx,CHRONOGRAM_MARGIN_VERTICAL , xxx,chronogram_height-CHRONOGRAM_MARGIN_VERTICAL, fill="#DDD", width=0, tags="grid")        

def drawChronogram_stream(y,h,stream_id,stream):
    textCenter = chronogram_height-CHRONOGRAM_MARGIN_VERTICAL-y-h/2
    textID = chronogram.create_text(10,textCenter , text=stream_id, font=(FONT_FAMILY, FONT_SIZE), fill="black", angle=90, anchor="n")
    background = None
    line = None
    if stream_id[0]=='i':
        background = "#DDF"
        line = "#88F"
    elif stream_id[0]=='p':
        background = "#DFD"
        line = "#8F8"
    elif stream_id[0]=='o':
        background = "#FDD"
        line = "#F88"
    chronogram.create_rectangle(CHRONOGRAM_MARGIN_HORIZONTAL,chronogram_height-CHRONOGRAM_MARGIN_VERTICAL-y , CHRONOGRAM_WIDTH-CHRONOGRAM_MARGIN_HORIZONTAL,chronogram_height-CHRONOGRAM_MARGIN_VERTICAL-y-h, fill=background, width=0, tags="content")
    gap = (CHRONOGRAM_WIDTH-2*CHRONOGRAM_MARGIN_HORIZONTAL)/len(stream)
    for kkk in range(len(stream)):
        yyy = chronogram_height-CHRONOGRAM_MARGIN_VERTICAL-y-0.5*h*stream[kkk]-1
        if stream[kkk]<3:
            chronogram.create_rectangle(CHRONOGRAM_MARGIN_HORIZONTAL+gap*kkk , yyy , CHRONOGRAM_MARGIN_HORIZONTAL+gap*(kkk+1) , yyy , fill=line , outline=line , width=3 , tags="content")
            if kkk<len(stream)-1:
                chronogram.create_rectangle(CHRONOGRAM_MARGIN_HORIZONTAL+gap*(kkk+1) , yyy , CHRONOGRAM_MARGIN_HORIZONTAL+gap*(kkk+1) , chronogram_height-CHRONOGRAM_MARGIN_VERTICAL-y-0.5*h*stream[kkk+1]-1 , fill=line , outline=line , width=3 , tags="content")

buttonFrame.pack(side="left")
bottomFrame.pack(side="bottom")
chronogram.pack(side="right")
canvas.pack(side="right")

#endregion


#region [orange] SAVING & LOADING

def blankCircuit():
    global gates
    global systems
    global nodes
    global wires
    global inputs
    global probes
    global outputs
    global tags
    global loadedSystems
    global stream
    global gate_idgen
    global system_idgen
    global node_idgen
    global wire_idgen
    global input_idgen
    global probe_idgen
    global output_idgen
    global tag_idgen
    global loadedSystem_idgen
    gates = {}
    systems = {}
    nodes = {}
    wires = {}
    inputs = {}
    probes = {}
    outputs = {}
    tags = {}
    loadedSystems = {}
    stream = {}
    gate_idgen = 0
    system_idgen = 0
    node_idgen = 0
    wire_idgen = 0
    input_idgen = 0
    probe_idgen = 0
    output_idgen = 0
    tag_idgen = 0
    loadedSystem_idgen = 0
    clean()

def clean():
    global view_x
    global view_y
    global selection
    global selectedTool
    global loadedSystemToBePlaced_id
    view_x = 0
    view_y = 0
    selection = []
    selectedTool = None
    cleanLoadedSystem()
    updateScreen()
    drawAll()
    resetSimulation()
    drawChronogram()

def saveCircuit():
    cleanLoadedSystem()
    idgens = {
        "gate_idgen": gate_idgen,
        "system_idgen": system_idgen,
        "node_idgen": node_idgen,
        "wire_idgen": wire_idgen,
        "input_idgen": input_idgen,
        "probe_idgen": probe_idgen,
        "output_idgen": output_idgen,
        "tag_idgen": tag_idgen,
        "loadedSystem_idgen": loadedSystem_idgen,
        "view_x": view_x,
        "view_y": view_y
    }
    save = {
        "gates": gates,
        "systems": systems,
        "nodes": nodes,
        "wires": wires,
        "inputs": inputs,
        "probes": probes,
        "outputs": outputs,
        "tags": tags,
        "loadedSystems": loadedSystems,
        "idgens": idgens
    }
    saveFilename = asksaveasfilename(filetypes = (("TelociDesi circuits","*.truitec"),("all files","*.*")))
    f = open(saveFilename.replace('.truitec','')+'.truitec', 'wb')
    pickle.dump(save,f)
    f.close()
    setCircuitModified(False)

def loadCircuit():
    global gates
    global systems
    global nodes
    global wires
    global inputs
    global probes
    global outputs
    global tags
    global loadedSystems
    global gate_idgen
    global system_idgen
    global node_idgen
    global wire_idgen
    global input_idgen
    global probe_idgen
    global output_idgen
    global tag_idgen
    global loadedSystem_idgen
    global view_x
    global view_y
    circuitFileName = askopenfilename(filetypes = (("TelociDesi circuits","*.truitec"),("all files","*.*"))) # show an "Open" dialog box and return the path to the selected file
    if circuitFileName[-8:]!='.truitec': return
    f = open(circuitFileName,'rb')
    save = pickle.load(f)
    f.close()
    gates = save["gates"]
    systems = save["systems"]
    nodes = save["nodes"]
    wires = save["wires"]
    inputs = save["inputs"]
    probes = save["probes"]
    outputs = save["outputs"]
    tags = save["tags"]
    loadedSystems = save["loadedSystems"]
    idgens = save["idgens"]
    gate_idgen = idgens["gate_idgen"]
    system_idgen = idgens["system_idgen"]
    node_idgen = idgens["node_idgen"]
    wire_idgen = idgens["wire_idgen"]
    input_idgen = idgens["input_idgen"]
    probe_idgen = idgens["probe_idgen"]
    output_idgen = idgens["output_idgen"]
    tag_idgen = idgens["tag_idgen"]
    loadedSystem_idgen = idgens["loadedSystem_idgen"]
    view_x = idgens["view_x"]
    view_y = idgens["view_y"]
    clean()
    # loadProgram()

def exportSystem():
    sys = buildSystem()
    exportFilename = asksaveasfilename(filetypes = (("TelociDesi systems","*.truites"),("all files","*.*")))
    f = open(exportFilename.replace('.truites','')+'.truites', 'wb')
    pickle.dump(sys,f)
    f.close()

def importSystem():
    global loadedSystemToBePlaced_id
    global loadedSystemToBePlaced_type
    systemFileName = askopenfilename(filetypes = (("TelociDesi systems","*.truites"),("all files","*.*")))
    if systemFileName[-8:]!='.truites': return
    loadedSystemToBePlaced_id = loadSystem(systemFileName)
    loadedSystemToBePlaced_type = "standard"
    selectTool('s')

def importMemory():
    global loadedSystemToBePlaced_id
    global loadedSystemToBePlaced_type
    memoryFileName = askopenfilename(filetypes = (("TelociDesi memory","*.truitem"),("all files","*.*")))
    if memoryFileName[-8:]!='.truitem': return
    loadedSystemToBePlaced_id = loadMemory(memoryFileName)
    loadedSystemToBePlaced_type = "memory"
    selectTool('s')

def validateInteger(inStr,acttyp):
    if acttyp == '1':
        if not inStr.isdigit():
            return False
    return True

def spawnRegisterPopup():
    popup = Toplevel(root)
    text_label = Label(popup, text="Enter the size of the register", font=(FONT_FAMILY, FONT_SIZE), width=28)
    text_label.pack()
    entryField = Entry(popup, font=(FONT_FAMILY, FONT_SIZE), validate="key")
    entryField['validatecommand'] = (entryField.register(validateInteger),'%P','%d')
    entryField.pack()
    validateButton = Button(popup, text="Register", font=(FONT_FAMILY, FONT_SIZE), command=lambda: spawnRegister(int(entryField.get()),popup))
    validateButton.pack()

def spawnRegister(wordsize,popup):
    global loadedSystemToBePlaced_id
    global loadedSystemToBePlaced_type
    global loadedSystem_idgen
    global loadedSystems
    if wordsize<=0 or wordsize>100: print("Register size is invalid !"); return
    t_sys = Register(wordsize)
    loadedSystem_id = "ls_"+str(loadedSystem_idgen)
    loadedSystem_idgen +=1
    loadedSystems[loadedSystem_id] = t_sys
    loadedSystemToBePlaced_id = loadedSystem_id
    loadedSystemToBePlaced_type = "register"
    selectTool('s')
    popup.destroy()

#endregion

#region [purple] MENU
menuBar = Menu(root)
#root['menu'] = menuBar
liste_porte_inversible=["NOT","NNOT","NAND" , "AND","NCONS" ,"CONS","NMUL" , "MUL","NOR" ,"OR","NANY", "ANY", "NSUM","SUM"
,"INC","DEC","RTU","RTD","CLU","CLD"]#liste de type [id_porte1,id_inversePorte1,id_porte2,id_inversePorte2...]



def invGate(sel_id):
    global liste_porte_inversible
    if(gates[sel_id]["gate"] in liste_porte_inversible):
        index=liste_porte_inversible.index(gates[sel_id]["gate"])
        gates[sel_id]["gate"]=liste_porte_inversible[index-index%2+(index+1)%2]
    drawAll()

def invGates(sel_ids):
    for sel_id in sel_ids:
        invGate(sel_id)
    drawAll()
    


sousMenuFile = Menu(menuBar)
menuBar.add_cascade(label='File', menu=sousMenuFile)
sousMenuFile.add_command(label='Save',font=(FONT_FAMILY, FONT_SIZE_MENU),command=saveCircuit)
sousMenuFile.add_command(label='Load',font=(FONT_FAMILY, FONT_SIZE_MENU),command=loadCircuit)
sousMenuFile.add_separator()
sousMenuFile.add_command(label='Export System',font=(FONT_FAMILY, FONT_SIZE_MENU),command=exportSystem)
sousMenuFile.add_command(label='Import System',font=(FONT_FAMILY, FONT_SIZE_MENU),command=importSystem)
sousMenuFile.add_separator()
sousMenuFile.add_command(label='Import Memory',font=(FONT_FAMILY, FONT_SIZE_MENU),command=importMemory)
sousMenuFile.add_separator()
sousMenuFile.add_command(label='New',font=(FONT_FAMILY, FONT_SIZE_MENU),command=blankCircuit)
sousMenuFile.add_command(label='Exit',font=(FONT_FAMILY, FONT_SIZE_MENU),command=root.destroy)

sousMenuTools = Menu(menuBar)
menuBar.add_cascade(label='Tools', menu=sousMenuTools)
sousMenuTools.add_command(label='Delete selection',font=(FONT_FAMILY, FONT_SIZE_MENU),command=removeSelection)
sousMenuTools.add_command(label='Inverse gate',font=(FONT_FAMILY, FONT_SIZE_MENU),command=lambda : invGates(selection))
sousMenuTools.add_separator()
sousMenuTools.add_command(label='Zoom +',font=(FONT_FAMILY, FONT_SIZE_MENU),command=lambda :zoom(1))
sousMenuTools.add_command(label='Zoom -',font=(FONT_FAMILY, FONT_SIZE_MENU),command=lambda : zoom(-1))
sousMenuTools.add_separator()
sousMenuTools.add_command(label='Simulate clock cycle',font=(FONT_FAMILY, FONT_SIZE_MENU),command=simulateCc)


sousMenuOptions = Menu(menuBar)
menuBar.add_cascade(label='DevTools', menu=sousMenuOptions)
sousMenuOptions.add_command(label='Debug Mode',font=(FONT_FAMILY, FONT_SIZE_MENU),command=debug_screenMap)
sousMenuOptions.add_command(label='Redraw system',font=(FONT_FAMILY, FONT_SIZE_MENU),command=drawAll)
sousMenuOptions.add_command(label='Redraw Chronogram',font=(FONT_FAMILY, FONT_SIZE_MENU),command=drawChronogram)



root.config(menu=menuBar)
#end region


selectTool(None)
resetRecording()

drawGrid()
updateScreen()
drawAll()
drawChronogram()

root.mainloop()

# TODO
# Bugs :
#   - nodes and inputs can pass through gates if a wire hides the gate in screen
#   - tags and deleting outputs and inputs does not work well
#   - glitches with wires and nodes
#   - knot circle on nodes between only two wires (should only be with 3 or more)
# View modes :
#   - unconnected nodes map : marks with a red square the nodes connected to nothing
#   - too many output nodes map : marks with a red square output nodes connected together
#   - connection mistakes map : marks with a red square nodes on wires without connection
#   - node values
# Wires :
#   - auto-router around obstacles
#   - bridge for wires crossing without connecting
# Gates :
#   - ability to mirror gates
#   - negate output
#   - finish other unary gates
#   - basic gates with more than two inputs (AND, OR etc)
#   - inprove the canPlace_gate function (redundant condition in the leftClick function ?)
# Inputs and outputs :
#   - easy inputs and outputs for naked system and gates inoutputs
# Probes :
#   - remove probes or fix them
# Number input :
#   - input a number with keyboard, outputs the signal on a given number of trits
# Systems :
#   - change the draw function so that systems show their orientation (dark corner, rounded corner, etc)
#   - option for wide gaps between pins (1 or 2)
#   - rotate and mirror
#   - ability to display a value or information on it (register value, etc)
# Memory :
#   - double click to load new file
#   - binary version
# Register :
#   - binary version
# Simulation :
#   - check if necessary to update node if already proper value
# Logging and Visualisation :
#   - separate software to visualize chronograms and output them to csv, excel, png, etc
# User Interface :
#   - clean the whole tool selection system....
#   - replace text in buttons with icons
#   - new panel and buttons for saving and loading
#   - new panel and buttons for total cost
#   - new panel for loading and placing systems
#   - load a circuit corresponding to a system
#   - reloading all system on the circuit (if their circuit changed) -> how to tackle the issue of changing number of inputs and outputs ?
# Saving and Loading :
#   - save simulation results
# Undo Redo :
#   - keep track of all changes : created/removed/moved/rotated gate/node/wire/input/prone/output, cut wire, negated gate
#   - function to undo a change
# Copy Paste :
#   - copy the relative position, nature and relations of each item
#   - ghost the size of the thing to paste
#   - click to create each item then the relations (the wires)
# Easy navigation :
#   - panel to create, list and teleport to waypoints
# Error handeling :
#   - catch errors if save file is corrupted
#   - catch errors if memory or system files don't exist anymore
