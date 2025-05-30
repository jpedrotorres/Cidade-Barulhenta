import tkinter as tk
from tkinter import messagebox

import sounddevice as sd
import numpy as np

class IntensidadeSom:
	def __init__(self):
		self.samplerate = 44100
		self.blocksize = int(self.samplerate * 0.5)
		self.channels = 1
		self.EPSILON = 1e-10

	def calc_dbfs(self, indata, frames, time, status):
		self.rms= np.sqrt(np.mean(indata**2) + self.EPSILON)
		self.dbfs= 20 * np.log10(self.rms)

class TelaProjeto:
	def __init__(self, root):
		self.root= root
		root.title("Som e Sustentabilidade")
#		root.geometry("300x500")

		self.som= IntensidadeSom()
		self.create_widgets()

	def create_widgets(self):
		self.title= tk.Label(self.root, text= "Absorção do Som por Difentes Materiais").pack()

		self.menu= tk.Menu(self.root)
		self.project_menu= tk.Menu(self.menu, tearoff= 0)
		self.menu.add_cascade(label="Projeto", menu= self.project_menu)
		self.project_menu.add_command(label="Novo")
		self.project_menu.add_command(label="Sair")
		self.root.config(menu=self.menu)

if __name__=="__main__":
	root= tk.Tk()

	app= TelaProjeto(root)

	root.mainloop()
