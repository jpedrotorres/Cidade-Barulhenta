import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import scrolledtext
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

	def stop_stream(self):
		if self.stream:
			print("Encerrando stream de áudio")
			self.is_measuring= False
			self.stream.stop()
			self.stream.close()
			self.stream= None
			print("Stream encerrado")
		else:
			print("Para encerrar, o stream necessita estar ligado")

	def get_avarage_dbfs(self):
		if not self.measurements_list_buffer:
			return

		avg_dbfs=np.mean(self.self.measurements_list_buffer)
		self.measurements_list_buffer=[]
		return avg_dbfs

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
		self.project_menu.add_command(label="Novo", command=self.confirm_new_project)
		self.project_menu.add_command(label="Iniciar", command=self.init_stream_gui)
		self.project_menu.add_command(label="Encerrar", command=self.stop_stream_gui)
		self.project_menu.add_separator()
		self.project_menu.add_command(label="Sair", command= self.root.quit)

		self.config_menu=tk.Menu(self.menu, tearoff=0)
		self.menu.add_cascade(label="Configuração", menu=self.config_menu)
		self.config_menu.add_command(label="Tempo de contagem", command=self.screen_time_config)

		self.help_menu=tk.Menu(self.menu, tearoff=0)
		self.menu.add_cascade(label="Ajuda", menu=self.help_menu)
		self.help_menu.add_command(label="Ajuda", command=self.donothing)
		self.help_menu.add_command(label="Sobre", command=self.donothing)

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
		self.log_text=tk.scrolledtext.ScrolledText(self.frame_material, height=5, width=20, state=tk.DISABLED)
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
		self.update_dbfs_display()

		self.log_text["state"]= tk.NORMAL
		self.log_text.insert(tk.END, "Iniciando stream de áudio...\n")
		self.log_text["state"]= tk.DISABLED

	def stop_stream_gui(self):
		if self.som.is_measuring:
			self.som.stop_stream()
			self.log_text["state"]= tk.NORMAL
			self.log_text.insert(tk.END, "Encerrando stream de áudio...\n")
			self.log_text["state"]= tk.DISABLED

		else:
			self.log_text["state"]= tk.NORMAL
			self.log_text.insert(tk.END, "O stream não está ligado...\n")
			self.log_text["state"]= tk.DISABLED

	def update_dbfs_display(self):
		if self.som.is_measuring:
			current_dbfs=self.som.current_dbfs
			if current_dbfs!=-999:
				self.lb_current_dbfs.config(text=f"dBFS Atual: {current_dbfs:.2f} dBFS")

		self.root.after(100, self.update_dbfs_display)

	def new_project_display(self):
		if self.som.stream:
			self.som.stop_stream()
		self.lb_current_dbfs.config(text="dBFS Atual: -")

		self.log_text["state"]= tk.NORMAL
		self.log_text.delete(1.0, tk.END)
		self.log_text["state"]= tk.DISABLED

	def confirm_new_project(self):
		confirm=tk.messagebox.askokcancel("Novo Projeto", "Deseja iniciar um novo projeto?")

		if confirm:
			self.new_project_display()

	def screen_time_config(self):
		window=tk.Toplevel(self.root)
		window.title("Tempo Medida")
		window.transient(self.root)
		window.grab_set()

		self.time_history_var= self.time_count_var.get()

		tk.Label(window, text="Tempo de duração das medidas").pack()
		tk.Scale(window, variable=self.time_count_var, from_=1, to=10, orient=tk.HORIZONTAL).pack()

		tk.Button(window, text="Alterar", command= lambda: self.confirm_alter_time(window)).pack()

	def confirm_alter_time(self, window):
		if self.time_count_var.get()==self.time_history_var:
			tk.messagebox.showwarning("Aviso", "Valor igual ao original")
			return

		confirm=tk.messagebox.askyesno("Confimação", f"Deseja alterar o tempo de duração da medida de {self.time_history_var} s para {self.time_count_var.get()} s?")

		if confirm:
			tk.messagebox.showinfo("Sucesso", "Valor alterado com sucesso. Projeto será reiniciado")
			self.new_project_display()

		else:
			self.time_count_var.set(self.time_history_var)
			tk.messagebox.showinfo("Cancelado", "Alteração cancelada!")
			return

		window.grab_release()
		window.destroy()

	def donothing(self):
		pass

if __name__=="__main__":
	root=tk.Tk()

	app=TelaProjeto(root)

	root.mainloop()
