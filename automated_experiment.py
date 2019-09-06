import numpy as np
import brightfield_threaded as bt
import power_supply_current_controller_threaded as pscct
from pyfiglet import Figlet
import time
from Tkinter import *
import tkFileDialog


# read in data from input csv, and program experiments

f = Figlet(font='isometric1')
print f.renderText('Ferg')
time.sleep(1)
g = Figlet(font='isometric3')
print g.renderText('Labs')
time.sleep(1)

print('Welcome to the automated brightfield creep test tool.')
time.sleep(0.5)

print('please select the file that contains details of the experiments to be run:')

root = Tk()
root.attributes("-topmost", True)
root.filename = tkFileDialog.askopenfilename(initialdir='C:/', title='Select file',
                                             filetypes=(('csv files', '*.csv'), ('all files', '*.*')))
print('success: you have selected ' + root.filename)

file_array = np.genfromtxt(root.filename, dtype=None, skip_header=1, delimiter=',', encoding=None)
file_list = file_array.tolist()

print('please select the file that you want the raw data to be saved in:')

root.directory = tkFileDialog.askdirectory()
output_folder = root.directory + '/'
print('success: you have selected ' + output_folder)

print('success: starting experiment')

for experiment_run in file_list:
    # extract current configurations
    [filename, ca, cc, temp, dur, fon, fdur] = experiment_run
