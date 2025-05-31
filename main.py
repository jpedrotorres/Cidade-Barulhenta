import tkinter as tk
from tkinter import messagebox

import sounddevice as sd
import numpy as np

class IntensidadeSom:
	def __init__(self):
		self.samplerate=44100
		self.blocksize=int(self.samplerate * 0.5)
		self.channels=1
		self.EPSILON=1e-10

	def calc_dbfs(self, indata, frames, time, status):
		self.rms=np.sqrt(np.mean(indata**2) + self.EPSILON)
		self.dbfs=20 * np.log10(self.rms)

class TelaProjeto:
	def __init__(self, root):
		self.root=root
		root.title("Som e Sustentabilidade")
#		root.geometry("300x500")

		self.som=IntensidadeSom()
		self.create_widgets()

	def create_widgets(self):
	#Criando menu
		self.menu=tk.Menu(self.root)

		self.project_menu=tk.Menu(self.menu, tearoff=0)
		self.menu.add_cascade(label="Projeto", menu=self.project_menu)
		self.project_menu.add_command(label="Novo", command=self.donothing)
		self.project_menu.add_separator()
		self.project_menu.add_command(label="Sair", command= self.root.quit)

		self.config_menu=tk.Menu(self.menu, tearoff=0)
		self.menu.add_cascade(label="Configuração", menu=self.config_menu)
		self.config_menu.add_command(label="Tempo de contagem", command=self.donothing)

		self.help_menu=tk.Menu(self.menu, tearoff=0)
		self.menu.add_cascade(label="Ajuda", menu=self.help_menu)
		self.help_menu.add_command(label="Sobre", command=self.donothing)
		self.help_menu.add_command(label="Ajuda", command=self.donothing)

		self.root.config(menu=self.menu)

	#Criando elementos do corpo
		self.title=tk.Label(self.root, text="Absorção do Som por Difentes Materiais")

	#Criando frames de controle
		self.frame_calibration=tk.Frame(self.root, bd=2, relief="groove", padx=10, pady=10)
		tk.Label(self.frame_calibration, text="Calibração do Microfone").pack()
		self.lb_calibrated_dbfs=tk.Label(self.frame_calibration, text="Calibração: Não realizada")
		self.lb_calibrated_dbfs.pack()
		tk.Button(self.frame_calibration, text="Calibrar", command=self.donothing).pack()
		self.lb_current_dbfs=tk.Label(self.frame_calibration, text="dBFS Atual: -")
		self.lb_current_dbfs.pack()

		self.frame_material=tk.Frame(self.root, bd=2, relief="groove", padx=10, pady=10)
		tk.Label(self.frame_material, text="Medição do material").pack()
		self.lb_name_material=tk.Label(self.frame_material, text="Nome do material:")
		self.lb_name_material.pack()
		self.entry_name_material=tk.Entry(self.frame_material)
		self.entry_name_material.pack()
		self.log_text=tk.Text(self.frame_material, height=5, width=20)
		self.log_text.pack()

		self.frame_list_material=tk.Frame(self.root, bd=2, relief="groove", padx=10, pady=10)

	#Layout dos Frames
		self.title.grid(row=0, columnspan=3)
		self.frame_calibration.grid(row=1, column=0)
		self.frame_material.grid(row=1, column=2)

	def donothing(self):
		pass

if __name__=="__main__":
	root=tk.Tk()

	app=TelaProjeto(root)

	root.mainloop()
