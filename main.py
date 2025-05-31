import tkinter as tk
from tkinter import messagebox
import datetime
import time

import sounddevice as sd
import numpy as np
import threading

class IntensidadeSom:
	def __init__(self):
		self.samplerate=44100
		self.blocksize=int(self.samplerate * 0.5)
		self.channels=1
		self.EPSILON=1e-10

		self.stream= None
		self.is_measuring= False

		self.current_dbfs= -999.0
		self.measurements_list_buffer= []

	def calc_dbfs(self, indata, frames, time, status):
		rms=np.sqrt(np.mean(indata**2) + self.EPSILON)
		dbfs=20 * np.log10(rms)

		self.current_dbfs= dbfs

	def start_stream(self):
		if self.stream is None:
			print("Iniciando stream de áudio")
			self.stream=sd.InputStream(callback=self.calc_dbfs,
										channels=self.channels,
										samplerate=self.samplerate,
										blocksize=self.blocksize,
										dtype="float32")
			self.stream.start()
			self.is_measuring= True
			print(f"Stream ativo. Medindo a cada {self.blocksize/self.samplerate:.1f} segundos")

class TelaProjeto:
	def __init__(self, root):
		self.root=root
		root.title("Som e Sustentabilidade")
#		root.geometry("300x500")

		self.time_count_var=tk.DoubleVar(value=5.0)
		self.name_material_var=tk.StringVar(value="Material")

		self.som=IntensidadeSom()

		self.create_widgets()

	def create_widgets(self):
	#Criando menu
		self.menu=tk.Menu(self.root)

		self.project_menu=tk.Menu(self.menu, tearoff=0)
		self.menu.add_cascade(label="Projeto", menu=self.project_menu)
		self.project_menu.add_command(label="Novo", command=self.donothing)
		self.project_menu.add_command(label="Iniciar", command=self.init_stream_gui)
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
		self.entry_name_material=tk.Entry(self.frame_material, textvariable=self.name_material_var)
		self.entry_name_material.pack()
		tk.Button(self.frame_material, text="Adicionar", command=self.donothing).pack()
		self.log_text=tk.Text(self.frame_material, height=5, width=20)
		self.log_text.pack()

		self.frame_list_material=tk.Frame(self.root, bd=2, relief="groove", padx=10, pady=10)

	#Layout do corpo principal
		self.title.grid(row=0, columnspan=3)
		self.frame_calibration.grid(row=1, column=0)
		self.frame_material.grid(row=1, column=2)

	def init_stream_gui(self):
		self.audio_thread=threading.Thread(target=self.som.start_stream)
		self.audio_thread.daemon= True
		self.audio_thread.start()

	def update_dbfs_display(self):
		current_dbfs= self.som.current_dbfs
		if current_dbfs != -999:
			self.lb_current_dbfs.config(text=f"dBFS Atual: {current_dbfs:.2f} dBFS")

		self.root.after(100, self.update_dbfs_display)

	def donothing(self):
		pass

if __name__=="__main__":
	root=tk.Tk()

	app=TelaProjeto(root)

	root.mainloop()
