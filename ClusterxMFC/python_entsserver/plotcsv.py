#this script plots the voltage and current readings 

import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import os
import numpy as np



# Load the CSV file
#df = pd.read_csv("c:/Users/kathe/Desktop/ClusterxSMFC/ClusterxMFC/ENTS_data_MudWattWithoutchip_RsenseOpen_04APR2025.csv")
#df = pd.read_csv("c:/Users/kathe/Desktop/ClusterxSMFC/ClusterxMFC/ENTS_data_MudWattWithChip_04APR2025.csv") #incorrect ports used V+ and V-
# Plot Voltage vs Current
plt.figure(figsize=(10, 6))
plt.plot(df['Timestamp'], df['Voltage (V)'], marker='o', linestyle='-', color='b')
plt.ylabel('Voltage (V)')
plt.xlabel('Timestamp')
plt.title('Voltage v Time')
plt.grid(True)
plt.show()