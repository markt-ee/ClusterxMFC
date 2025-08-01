import tkinter as tk
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure 


class CSVPlotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV Plot Viewer")
        self.root.geometry("800x600")

        self.file_path = ""

        self.select_button = tk.Button(root, text="Select CSV File", command=self.select_file)
        self.select_button.pack(pady=10)

        self.path_label = tk.Label(root, text="", wraplength=700)
        self.path_label.pack(pady=5)

        self.canvas = None

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.file_path = file_path
            self.path_label.config(text=f"Selected file: {self.file_path}")
            self.plot_csv(file_path)

    def plot_csv(self, path):
        try:
            df = pd.read_csv(path)

            if self.canvas:
                self.canvas.get_tk_widget().destroy()

            # Use Matplotlib's Figure directly (no plt.show())
            # fig = Figure(figsize=(8, 5), dpi=100)
            # ax = fig.add_subplot(111)
            # ax.plot(df['Timestamp'], df['Voltage (V)'], marker='o', linestyle='-', color='b')
            # ax.set_ylabel('Voltage (V)')
            # ax.set_xlabel('Timestamp')
            # ax.set_title('Voltage vs Time')
            # ax.grid(True)

            plt.figure(figsize=(10, 6))
            plt.plot(df['Timestamp'], df['Voltage (V)'], marker='o', linestyle='-', color='b')
            plt.ylabel('Voltage (V)')
            plt.xlabel('Timestamp')
            plt.title('Voltage v Time')
            plt.grid(True)
            plt.show()




            self.canvas = FigureCanvasTkAgg(fig, master=self.root)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(pady=20)

        except Exception as e:
            self.path_label.config(text=f"Error reading file: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CSVPlotApp(root)
    root.mainloop()
