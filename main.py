#!/usr/bin/env python
#
# Copyright 2019 the original author or authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# TODO: Create viz that displays generated Qiskit code for circuit
# TODO: Prevent error from occurring when circuit is empty
#
"""Create quantum circuits with Qiskit and Pygame"""

from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit import execute
# import pygame, pygame.midi
from pygame.midi import time
from pygame.locals import *

from model.circuit_grid_model import *
from model import circuit_node_types as node_types
from containers.vbox import VBox
from utils.colors import WHITE
from utils.navigation import *
from utils.gamepad import *
from viz.circuit_diagram import CircuitDiagram
from viz.measurements_histogram import MeasurementsHistogram
from viz.qsphere import QSphere
from viz.statevector_grid import StatevectorGrid
from viz.unitary_grid import UnitaryGrid
from controls.circuit_grid import *

WINDOW_SIZE = 1500, 1000
NUM_QUBITS = 4

if not pygame.font: print('Warning, fonts disabled')
if not pygame.mixer: print('Warning, sound disabled')

pygame.init()

pygame.joystick.init()
num_joysticks = pygame.joystick.get_count()

joystick = False
if num_joysticks > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()

screen = pygame.display.set_mode(WINDOW_SIZE)

background = pygame.Surface(screen.get_size())
background = background.convert()
background.fill(WHITE)

pygame.font.init()


def main():
    pygame.display.set_caption('Unitary Fingerboard')

    screen.blit(background, (0, 0))
    pygame.display.flip()

    # Prepare objects
    clock = pygame.time.Clock()

    circuit_grid_model = CircuitGridModel(NUM_QUBITS, 18)

    # circuit_grid_model.set_node(0, 0, CircuitGridNode(node_types.IDEN))

    circuit = circuit_grid_model.compute_circuit()

    unitary_grid = UnitaryGrid(circuit)

    statevector_grid = StatevectorGrid(circuit)

    middle_sprites = VBox(400, 10, unitary_grid)
    right_sprites = VBox(1300, 0, statevector_grid)

    circuit_grid = CircuitGrid(10, 600, circuit_grid_model)
    screen.blit(background, (0, 0))

    middle_sprites.draw(screen)
    right_sprites.draw(screen)
    circuit_grid.draw(screen)
    pygame.display.flip()

    gamepad_repeat_delay = 100
    gamepad_neutral = True
    gamepad_pressed_timer = 0
    gamepad_last_update = pygame.time.get_ticks()

    # MIDI setup
    # TODO: Put in functions or class/methods
    pygame.midi.init()

    print_midi_device_info()

    device_id = 0
    if device_id is None:
        input_id = pygame.midi.get_default_input_id()
    else:
        input_id = device_id

    # input_id = 0
    print("using input_id :%s:" % input_id)
    i = pygame.midi.Input(input_id)

    # sending midi to the output
    output_id = pygame.midi.get_default_output_id()
    ## output_id = 1
    print("using output_id :%s:" % output_id)
    midi_output = pygame.midi.Output(output_id)
    midi_output.set_instrument(0)

    # end of sending midi to output

    bit_str_meas = '0000'

    beg_time = time()
    recent_note_time = beg_time


    # Main Loop
    going = True
    while going:
        clock.tick(30)

        pygame.time.wait(10)

        if time() > recent_note_time:
            melody_circ = circuit_grid_model.compute_circuit()
            bit_str_meas = measure_circuit(melody_circ, bit_str_meas)

            # pitch_meas = int(bit_str_meas, 2)
            pitch_meas = compute_pitch_by_bitstr(bit_str_meas)

            recent_note_time += 500
            # midi_output.write([[[0x90, pitch_meas, 127], recent_note_time + 0],
            #                    [[0x90, pitch_meas, 0], recent_note_time + 500]])
            midi_output.write([[[0x90, pitch_meas, 127], recent_note_time + 0]])
            # melody_circ = createTransitionCircuit(cur_mel_midi_vals)

        if joystick:
            gamepad_move = False
            joystick_hat = joystick.get_hat(0)

            if joystick_hat == (0, 0):
                gamepad_neutral = True
                gamepad_pressed_timer = 0
            else:
                if gamepad_neutral:
                    gamepad_move = True
                    gamepad_neutral = False
                else:
                    gamepad_pressed_timer += pygame.time.get_ticks() - gamepad_last_update
            if gamepad_pressed_timer > gamepad_repeat_delay:
                gamepad_move = True
                gamepad_pressed_timer -= gamepad_repeat_delay
            if gamepad_move:
                if joystick_hat == (-1, 0):
                    move_update_circuit_grid_display(circuit_grid, MOVE_LEFT)
                elif joystick_hat == (1, 0):
                    move_update_circuit_grid_display(circuit_grid, MOVE_RIGHT)
                elif joystick_hat == (0, 1):
                    move_update_circuit_grid_display(circuit_grid, MOVE_UP)
                elif joystick_hat == (0, -1):
                    move_update_circuit_grid_display(circuit_grid, MOVE_DOWN)
            gamepad_last_update = pygame.time.get_ticks()

            # Check left thumbstick position
            # left_thumb_x = joystick.get_axis(0)
            # left_thumb_y = joystick.get_axis(1)

        # Handle Input Events
        for event in pygame.event.get():
            pygame.event.pump()

            # if event.type != MOUSEMOTION:
            #     print("event: ", event)
            if event.type == QUIT:
                going = False

            elif event.type == JOYBUTTONDOWN:
                if event.button == BTN_A:
                    # Place X gate
                    circuit_grid.handle_input_x()
                    update_viz(circuit, circuit_grid_model, circuit_grid, middle_sprites,
                               right_sprites, unitary_grid, statevector_grid)
                    pygame.display.flip()
                elif event.button == BTN_X:
                    # Place Y gate
                    circuit_grid.handle_input_y()
                    update_viz(circuit, circuit_grid_model, circuit_grid, middle_sprites,
                               right_sprites, unitary_grid, statevector_grid)
                    pygame.display.flip()
                elif event.button == BTN_B:
                    # Place Z gate
                    circuit_grid.handle_input_z()
                    update_viz(circuit, circuit_grid_model, circuit_grid, middle_sprites,
                               right_sprites, unitary_grid, statevector_grid)
                    pygame.display.flip()
                elif event.button == BTN_Y:
                    # Place Hadamard gate
                    circuit_grid.handle_input_h()
                    update_viz(circuit, circuit_grid_model, circuit_grid, middle_sprites,
                               right_sprites, unitary_grid, statevector_grid)
                    pygame.display.flip()
                elif event.button == BTN_RIGHT_TRIGGER:
                    # Delete gate
                    circuit_grid.handle_input_delete()
                    update_viz(circuit, circuit_grid_model, circuit_grid, middle_sprites,
                               right_sprites, unitary_grid, statevector_grid)
                    pygame.display.flip()
                elif event.button == BTN_RIGHT_THUMB:
                    # Add or remove a control
                    circuit_grid.handle_input_ctrl()
                    update_viz(circuit, circuit_grid_model, circuit_grid, middle_sprites,
                               right_sprites, unitary_grid, statevector_grid)
                    pygame.display.flip()
                # elif event.button == BTN_LEFT_BUMPER:
                #     # Update visualizations
                #     # TODO: Refactor following code into methods, etc.
                #     screen.blit(background, (0, 0))
                #     circuit = circuit_grid_model.compute_circuit()
                #     unitary_grid.set_circuit(circuit)
                #     statevector_grid.set_circuit(circuit)
                #     middle_sprites.arrange()
                #     right_sprites.arrange()
                #     middle_sprites.draw(screen)
                #     right_sprites.draw(screen)
                #     circuit_grid.draw(screen)
                #     pygame.display.flip()

            elif event.type == JOYAXISMOTION:
                # print("event: ", event)
                if event.axis == AXIS_RIGHT_THUMB_X and joystick.get_axis(AXIS_RIGHT_THUMB_X) >= 0.95:
                    circuit_grid.handle_input_rotate(np.pi / 8)
                    update_viz(circuit, circuit_grid_model, circuit_grid, middle_sprites,
                               right_sprites, unitary_grid, statevector_grid)
                    pygame.display.flip()
                if event.axis == AXIS_RIGHT_THUMB_X and joystick.get_axis(AXIS_RIGHT_THUMB_X) <= -0.95:
                    circuit_grid.handle_input_rotate(-np.pi / 8)
                    update_viz(circuit, circuit_grid_model, circuit_grid, middle_sprites,
                               right_sprites, unitary_grid, statevector_grid)
                    pygame.display.flip()
                if event.axis == AXIS_RIGHT_THUMB_Y and joystick.get_axis(AXIS_RIGHT_THUMB_Y) <= -0.95:
                    circuit_grid.handle_input_move_ctrl(MOVE_UP)
                    update_viz(circuit, circuit_grid_model, circuit_grid, middle_sprites,
                               right_sprites, unitary_grid, statevector_grid)
                    pygame.display.flip()
                if event.axis == AXIS_RIGHT_THUMB_Y and joystick.get_axis(AXIS_RIGHT_THUMB_Y) >= 0.95:
                    circuit_grid.handle_input_move_ctrl(MOVE_DOWN)
                    update_viz(circuit, circuit_grid_model, circuit_grid, middle_sprites,
                               right_sprites, unitary_grid, statevector_grid)
                    pygame.display.flip()

            elif event.type == KEYDOWN:
                index_increment = 0
                if event.key == K_ESCAPE:
                    going = False
                elif event.key == K_a:
                    circuit_grid.move_to_adjacent_node(MOVE_LEFT)
                    circuit_grid.draw(screen)
                    pygame.display.flip()
                elif event.key == K_d:
                    circuit_grid.move_to_adjacent_node(MOVE_RIGHT)
                    circuit_grid.draw(screen)
                    pygame.display.flip()
                elif event.key == K_w:
                    circuit_grid.move_to_adjacent_node(MOVE_UP)
                    circuit_grid.draw(screen)
                    pygame.display.flip()
                elif event.key == K_s:
                    circuit_grid.move_to_adjacent_node(MOVE_DOWN)
                    circuit_grid.draw(screen)
                    pygame.display.flip()
                elif event.key == K_x:
                    circuit_grid.handle_input_x()
                    update_viz(circuit, circuit_grid_model, circuit_grid, middle_sprites,
                               right_sprites, unitary_grid, statevector_grid)
                    pygame.display.flip()
                elif event.key == K_y:
                    circuit_grid.handle_input_y()
                    update_viz(circuit, circuit_grid_model, circuit_grid, middle_sprites,
                               right_sprites, unitary_grid, statevector_grid)
                    pygame.display.flip()
                elif event.key == K_z:
                    circuit_grid.handle_input_z()
                    update_viz(circuit, circuit_grid_model, circuit_grid, middle_sprites,
                               right_sprites, unitary_grid, statevector_grid)
                    pygame.display.flip()
                elif event.key == K_h:
                    circuit_grid.handle_input_h()
                    update_viz(circuit, circuit_grid_model, circuit_grid, middle_sprites,
                               right_sprites, unitary_grid, statevector_grid)
                    pygame.display.flip()
                elif event.key == K_BACKSLASH:
                    circuit_grid.handle_input_delete()
                    update_viz(circuit, circuit_grid_model, circuit_grid, middle_sprites,
                               right_sprites, unitary_grid, statevector_grid)
                    pygame.display.flip()
                elif event.key == K_c:
                    # Add or remove a control
                    circuit_grid.handle_input_ctrl()
                    update_viz(circuit, circuit_grid_model, circuit_grid, middle_sprites,
                               right_sprites, unitary_grid, statevector_grid)
                    pygame.display.flip()
                elif event.key == K_UP:
                    # Move a control qubit up
                    circuit_grid.handle_input_move_ctrl(MOVE_UP)
                    update_viz(circuit, circuit_grid_model, circuit_grid, middle_sprites,
                               right_sprites, unitary_grid, statevector_grid)
                    pygame.display.flip()
                elif event.key == K_DOWN:
                    # Move a control qubit down
                    circuit_grid.handle_input_move_ctrl(MOVE_DOWN)
                    update_viz(circuit, circuit_grid_model, circuit_grid, middle_sprites,
                               right_sprites, unitary_grid, statevector_grid)
                    pygame.display.flip()
                elif event.key == K_LEFT:
                    # Rotate a gate
                    circuit_grid.handle_input_rotate(-np.pi/8)
                    update_viz(circuit, circuit_grid_model, circuit_grid, middle_sprites,
                               right_sprites, unitary_grid, statevector_grid)
                    pygame.display.flip()
                elif event.key == K_RIGHT:
                    # Rotate a gate
                    circuit_grid.handle_input_rotate(np.pi / 8)
                    update_viz(circuit, circuit_grid_model, circuit_grid, middle_sprites,
                               right_sprites, unitary_grid, statevector_grid)
                    pygame.display.flip()
                # elif event.key == K_SPACE:
                #     # Update visualizations
                #     # TODO: Refactor following code into methods, etc.
                #     screen.blit(background, (0, 0))
                #     circuit = circuit_grid_model.compute_circuit()
                #     unitary_grid.set_circuit(circuit)
                #     statevector_grid.set_circuit(circuit)
                #     middle_sprites.arrange()
                #     right_sprites.arrange()
                #     middle_sprites.draw(screen)
                #     right_sprites.draw(screen)
                #     circuit_grid.draw(screen)
                #     pygame.display.flip()

            # else:
            #     print("event: ", event)

    pygame.quit()


def update_viz(circuit, circuit_grid_model, circuit_grid, middle_sprites, right_sprites,
                            unitary_grid, statevector_grid):
    # Update visualizations
    # TODO: Refactor following code into methods, etc.
    screen.blit(background, (0, 0))
    circuit = circuit_grid_model.compute_circuit()
    unitary_grid.set_circuit(circuit)
    statevector_grid.set_circuit(circuit)
    middle_sprites.arrange()
    right_sprites.arrange()
    middle_sprites.draw(screen)
    right_sprites.draw(screen)
    circuit_grid.draw(screen)
    pygame.display.flip()

def move_update_circuit_grid_display(circuit_grid, direction):
    circuit_grid.move_to_adjacent_node(direction)
    circuit_grid.draw(screen)
    pygame.display.flip()

def print_midi_device_info():
    for i in range(pygame.midi.get_count()):
        r = pygame.midi.get_device_info(i)
        (interf, name, input, output, opened) = r

        in_out = ""
        if input:
            in_out = "(input)"
        if output:
            in_out = "(output)"

        print("%2i: interface :%s:, name :%s:, opened :%s:  %s" %
              (i, interf, name, opened, in_out))

def compute_pitch_by_bitstr(bitstr):
    pitches = [60,62,64,65,67,69,71,72,74,76,77,79,81,83,84,86]
    # pitches = [60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75]
    # pitches = [60,63,65,67,70,72,75,77,79,82,84,86,89,91,93,96]
    # pitches = [36,40,43,48,52,55,60,64,67,72,76,79,84,88,91,96]
    return pitches[int(bitstr, 2)]

def measure_circuit(circ, initial_bit_str):
    # Use the BasicAer qasm_simulator backend
    from qiskit import BasicAer
    backend_sim = BasicAer.get_backend('qasm_simulator')

    # Initialize each wire
    init_qr = QuantumRegister(NUM_QUBITS, 'q')

    init_circ = QuantumCircuit(init_qr)

    for bit_idx in range(0, NUM_QUBITS):
        if int(initial_bit_str[bit_idx]) == 1:
            init_circ.x(init_qr[NUM_QUBITS - bit_idx - 1])
        else:
            init_circ.iden(init_qr[NUM_QUBITS - bit_idx - 1])

    init_circ.barrier(init_qr)

    # Create a Quantum Register with 4 qubits
    qr = QuantumRegister(NUM_QUBITS, 'q')

    # Create a Classical Register with 4 bits
    cr = ClassicalRegister(NUM_QUBITS, 'c')

    # Create the measurement portion of a quantum circuit
    meas_circ = QuantumCircuit(qr, cr)

    # Create a barrier that separates the gates from the measurements
    meas_circ.barrier(qr)

    # Measure the qubits into the classical registers
    meas_circ.measure(qr, cr)

    # Add the measurement circuit to the original circuit
    complete_circuit = init_circ + circ + meas_circ

    # mel_circ_drawing = (init_circ + circ).draw(output='mpl')
    # mel_circ_drawing.savefig("utils/data/mel_circ.png")
    # mel_circ_img, mel_circ_img_rect = load_image('mel_circ.png', -1)
    # mel_circ_img.convert()
    # mel_circ_img_rect.topleft = (0, 0)
    # screen.blit(mel_circ_img, mel_circ_img_rect)
    # pygame.display.flip()

    # Execute the circuit on the qasm simulator, running it 1000 times.
    job_sim = execute(complete_circuit, backend_sim, shots=1)

    # Grab the results from the job.
    result_sim = job_sim.result()

    # Print the counts, which are contained in a Python dictionary
    counts = result_sim.get_counts(complete_circuit)
    print(counts)
    basis_state_str = list(counts.keys())[0]
    # print ("basis_state_str: ", basis_state_str)

    # highlight_measured_state(initial_bit_str, basis_state_str)
    return basis_state_str

if __name__ == '__main__':
    main()