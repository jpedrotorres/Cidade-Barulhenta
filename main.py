import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import scrolledtext
import datetime
import time
import os

import sounddevice as sd
import soundfile as sf
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

		self.calibrated_dbfs= None
		self.material_results= {}

	def calc_dbfs(self, indata, frames, time, status):
		rms=np.sqrt(np.mean(indata**2) + self.EPSILON)
		dbfs=20 * np.log10(rms)

		self.current_dbfs= dbfs
		if self.is_measuring:
			self.measurements_list_buffer.append(dbfs)

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
			print(f"Stream ativo. Captando dados do microfone a cada {self.blocksize/self.samplerate:.1f} segundos")

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

		avg_dbfs=np.mean(self.measurements_list_buffer)
		self.measurements_list_buffer=[]
		return avg_dbfs

class PlayerSom:
	def __init__(self, som_instance):
		BASE_DIR=os.path.dirname(os.path.abspath(__file__))
		self.reference_sound_file=os.path.join(BASE_DIR, "sons", "ruido_rosa.wav")

		self.som=som_instance

		if not os.path.exists(self.reference_sound_file):
			messagebox.showerror("Erro de Arquivo", f"Arquivo de áudio não encontrado em: {self.reference_sound_file}")


	def play_sound(self):
		try:
			data, fs = sf.read(self.reference_sound_file, dtype='float32')

			sd.play(data, fs, device=self.som.output_device_id if hasattr(self.som, 'output_device_id') else None)

		except FileNotFoundError:
			tk.messagebox.showerror("Erro de Arquivo", f"Arquivo de áudio '{filename}' não encontrado. Verifique o caminho.")

		except Exception as e:
			tk.messagebox.showerror("Erro de Reprodução", f"Não foi possível reproduzir o áudio: {e}")

	def stop_sound(self):
		sd.stop()

class TelaProjeto:
	def __init__(self, root):
		self.root=root
		root.title("Som e Sustentabilidade")
		root.resizable(False, False)

		self.time_count_var=tk.DoubleVar(value=5.0)
		self.name_material_var=tk.StringVar(value="Material")

		self.som=IntensidadeSom()
		self.music=PlayerSom(self.som)

		self.create_widgets()

		self.count_material_row=0
		self.count_material_column=0
		self.list_frame_material= {}

	def create_widgets(self):
	#Criando menu
		self.menu=tk.Menu(self.root)

		self.project_menu=tk.Menu(self.menu, tearoff=0)
		self.menu.add_cascade(label="Projeto", menu=self.project_menu)
		self.project_menu.add_command(label="Novo", command=self.confirm_new_project)
		self.project_menu.add_command(label="Iniciar", command=self.init_stream_gui)
		self.project_menu.add_command(label="Encerrar", command=self.stop_stream_gui)
		self.project_menu.add_separator()
		self.project_menu.add_command(label="Sair", command= self.close_system_gui)

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

		#Criando frames (Microfone)
		self.frame_calibration=tk.Frame(self.root, bd=2, relief="groove", padx=10, pady=10)
		tk.Label(self.frame_calibration, text="Calibração do Microfone").pack()
		self.lb_calibrated_dbfs=tk.Label(self.frame_calibration, text="Calibração: Não realizada")
		self.lb_calibrated_dbfs.pack()
		tk.Button(self.frame_calibration, text="Calibrar", command=self.start_measure_calibration).pack()
		self.lb_current_dbfs=tk.Label(self.frame_calibration, text="dBFS Atual: -")
		self.lb_current_dbfs.pack()

		self.frame_material=tk.Frame(self.root, bd=2, relief="groove", padx=10, pady=10)
		tk.Label(self.frame_material, text="Medição do material").pack()
		self.lb_name_material=tk.Label(self.frame_material, text="Nome do material:")
		self.lb_name_material.pack()
		self.entry_name_material=tk.Entry(self.frame_material, textvariable=self.name_material_var)
		self.entry_name_material.pack()
		tk.Button(self.frame_material, text="Adicionar", command=self.start_measure_material).pack()
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

		self.print_log_message(f"Iniciando stream de áudio")

	def stop_stream_gui(self):
		if self.som.is_measuring:
			self.som.stop_stream()
			self.print_log_message(f"Encerrando stream de áudio")

		else:
			self.print_log_message(f"O stream não está ligado")

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

	def close_system_gui(self):
		if self.som.stream:
			self.som.stop_stream()

		self.root.destroy()

	def start_measure_calibration(self):
		if self.som.stream is None:
			self.init_stream_gui()

		duration= self.time_count_var.get()
		self.print_log_message(f"Iniciando calibração do microfone por {duration} segundos")

		self.music.play_sound()
		self.som.measurements_list_buffer= []
		self.root.after(int(duration * 1000), self.complete_measure_mic)

	def complete_measure_mic(self):
		self.music.stop_sound()
		avg= self.som.get_avarage_dbfs()

		if avg is not None:
			self.som.calibrated_dbfs= avg
			self.lb_calibrated_dbfs.config(text=f"Calibração: {avg:.2f} dBFS")
			self.print_log_message(f"Calibração concluída. Média do valor para controle: {avg:.2f} dBFS")

		else:
			self.print_log_message(f"Calibração não realizada")

	def start_measure_material(self):
		if self.som.stream is None:
			self.init_stream_gui()

		if self.som.calibrated_dbfs is None:
			tk.messagebox.showwarning("Aviso", "É necessário calibrar o microfone primeiro para referência!")
			return

		material_name= self.name_material_var.get()
		if material_name.lower()=="material":
			tk.messagebox.showerror("Erro", "Nome de material inválido!")
			return

		duration=self.time_count_var.get()

		self.print_log_message(f"Iniciando calibração do {material_name}")

		self.som.measurements_list_buffer= []

		self.music.play_sound()
		self.root.after(int(duration * 1000), lambda: self.complete_measure_material(material_name))

	def complete_measure_material(self, material_name):
		self.music.stop_sound()
		avg= self.som.get_avarage_dbfs()

		if avg is not None and self.som.calibrated_dbfs is not None:
			attenuation=self.som.calibrated_dbfs - avg
			self.som.material_results[material_name]= {"media": avg, "atenuacao": attenuation}

			self.print_log_message(f"Medição para {material_name} concluida")
			self.print_log_message(f"Valor médio: {avg:.2f} dBFS")
			self.print_log_message(f"Valor de atenuação: {attenuation:.2f} dB")

			self.create_frame_material(material_name)

		else:
			self.print_log_message(f"Não foi possível realizar a medição de {material_name}")

	def create_frame_material(self, material_name):
		if material_name in self.list_frame_material:
			confirm= tk.messagebox.askokcancel("Aviso", "Já existe um material cadastrado com esse nome. Deseja sobrescreve-lo?")

			if not confirm:
				return

		frame_material=tk.Frame(self.frame_list_material, bd=2, relief="groove", padx=10, pady=10)
		tk.Label(frame_material, text=f"{material_name}").pack()
		tk.Label(frame_material, text=f"Média {material_name}: {self.som.material_results[material_name]['media']:.2f} dBFS").pack()
		tk.Label(frame_material, text=f"Atenuação: {self.som.material_results[material_name]['atenuacao']:.2f} dB").pack()

		self.list_frame_material[material_name]=frame_material

		self.frame_list_material.grid(row=3, columnspan=3)
		frame_material.grid(row=self.count_material_row, column=self.count_material_column)
		#self.count_material_row+=1
		self.count_material_column+=1

		#CRIAR BOTÂO PARA EXCLUIR MEDIDA

	def print_log_message(self, message):
		self.log_text["state"]= tk.NORMAL
		self.log_text.insert(tk.END, f"{message}...\n")
		self.log_text["state"]= tk.DISABLED

		self.log_text.see(tk.END)

	def donothing(self):
		pass

if __name__=="__main__":
	root=tk.Tk()

	app=TelaProjeto(root)

	root.mainloop()
