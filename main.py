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
			try:
				print("Iniciando stream de áudio")
				self.stream=sd.InputStream(
					callback=self.calc_dbfs,
					channels=self.channels,
					samplerate=self.samplerate,
					blocksize=self.blocksize,
					dtype="float32")
				self.stream.start()
				self.is_measuring= True
				print(f"Stream ativo. Captando dados do microfone a cada {self.blocksize/self.samplerate:.1f} segundos")
			except Exception as e:
				print(f"Erro ao iniciar stream: {e}")
				self.stream = None

	def stop_stream(self):
		if self.stream:
			print("Encerrando stream de áudio")
			self.is_measuring= False
			self.stream.stop()
			self.stream.close()
			self.stream= None
			print("Stream encerrado")
		elif self.stream is None:
			print("Para encerrar, o stream necessita estar ligado")

	def start_data_collection(self):
		 self.measurements_list_buffer = []
		 self.is_measuring = True
		 
	def stop_data_collection(self):
		self.is_measuring = False

	def get_avarage_dbfs(self):
		self.stop_data_collection()

		if not self.measurements_list_buffer:
			print("Aviso: Nenhuma leitura de dBFS coletada para a média.")
			return

		avg_dbfs=np.mean(self.measurements_list_buffer)
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
		self.list_frame_material= {}

		self.som=IntensidadeSom()
		self.music=PlayerSom(self.som)

		self.log_visible= False
		self.create_widgets()

		self.count_material_row=0
		self.count_material_column=0

		self.root.protocol("WM_DELETE_WINDOW", self.close_system_gui)

	def create_widgets(self):
	#Criando menu
		self.menu=tk.Menu(self.root)

		self.project_menu=tk.Menu(self.menu, tearoff=0)
		self.menu.add_cascade(label="Projeto", menu=self.project_menu)
		self.project_menu.add_command(label="Novo", command=self.confirm_new_project)
		self.project_menu.add_command(label="Iniciar Stream", command=self.init_stream_gui)
		self.project_menu.add_command(label="Encerrar Stream", command=self.stop_stream_gui)
		self.project_menu.add_command(label="Adicionar Material", command=self.screen_new_material)
		self.project_menu.add_separator()
		self.project_menu.add_command(label="Sair", command= self.close_system_gui)

		self.show_menu=tk.Menu(self.menu, tearoff=0)
		self.menu.add_cascade(label="Exibir", menu=self.show_menu)
		self.show_menu.add_command(label="Tabelas", command=self.show_result_table)
		self.show_menu.add_command(label="Gráficos", command=self.show_graph)

		self.config_menu=tk.Menu(self.menu, tearoff=0)
		self.menu.add_cascade(label="Configuração", menu=self.config_menu)
		self.config_menu.add_command(label="Tempo de contagem", command=self.screen_time_config)
		self.config_menu.add_command(label="Dispositivo de entrada", command=self.donothing)

		self.help_menu=tk.Menu(self.menu, tearoff=0)
		self.menu.add_cascade(label="Ajuda", menu=self.help_menu)
		self.help_menu.add_command(label="Ajuda", command=self.donothing)
		self.help_menu.add_command(label="Mostrar log", command=self.show_log_text)
		self.help_menu.add_command(label="Sobre", command=self.donothing)

		self.root.config(menu=self.menu)

	#Configurando tamanhos dos frames
		FRAME_WIDTH= 250
		FRAME_HEIGHT= 180

	#Criando elementos do corpo
		self.title=tk.Label(self.root, text="Absorção do Som por Difentes Materiais", font=('Arial', 10, 'bold'), pady=10)
		self.title.grid(row=0, columnspan=3, pady=10)

		#Criando frames (Microfone)
		self.frame_calibration=tk.Frame(self.root, bd=2, relief="groove", width=FRAME_WIDTH, height=FRAME_HEIGHT, padx=5, pady=5)
		self.frame_calibration.grid_propagate(False)
		self.frame_calibration.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

		tk.Label(self.frame_calibration, text="Calibração do Microfone", font=('Arial', 10, 'bold')).pack()
		self.lb_calibrated_dbfs=tk.Label(self.frame_calibration, text="Calibração: Não realizada")
		self.lb_calibrated_dbfs.pack()
		tk.Button(self.frame_calibration, text="Calibrar", command=self.start_measure_calibration).pack()
		self.lb_current_dbfs=tk.Label(self.frame_calibration, text="dBFS Atual: -")
		self.lb_current_dbfs.pack()

		#Criando frame (Espuma)
		self.frame_material_espuma=tk.Frame(self.root, bd=2, relief="groove", width=FRAME_WIDTH, height=FRAME_HEIGHT, padx=5, pady=5)
		self.frame_material_espuma.grid_propagate(False)
		self.frame_material_espuma.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

		self.create_frame_material("Espuma", is_widget_main=True, frame_reference=self.frame_material_espuma)

		#Criando frame (Jornal)
		self.frame_material_jornal=tk.Frame(self.root, bd=2, relief="groove", width=FRAME_WIDTH, height=FRAME_HEIGHT, padx=5, pady=5)
		self.frame_material_jornal.grid_propagate(False)
		self.frame_material_jornal.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")

		self.create_frame_material("Jornal", is_widget_main=True, frame_reference=self.frame_material_jornal)


		#Criando frame (Caixa de Ovo)
		self.frame_material_ovo=tk.Frame(self.root, bd=2, relief="groove", width=FRAME_WIDTH, height=FRAME_HEIGHT, padx=5, pady=5)
		self.frame_material_ovo.grid_propagate(False)
		self.frame_material_ovo.grid(row=2, column=1, padx=5, pady=5, sticky="nsew")

		self.create_frame_material("Caixa de Ovo", is_widget_main=True, frame_reference=self.frame_material_ovo)

		#Criando log_text
		self.log_text=scrolledtext.ScrolledText(self.root, height=5, width=40, state=tk.DISABLED)

		self.frame_list_material=tk.Frame(self.root, bd=2, relief="groove", padx=10, pady=10)

	#Layout do corpo principal
		self.root.grid_columnconfigure(0, weight=1)
		self.root.grid_columnconfigure(1, weight=1)
		self.root.grid_columnconfigure(2, weight=1)

		self.root.grid_rowconfigure(1, weight=1)
		self.root.grid_rowconfigure(2, weight=1)
		self.root.grid_rowconfigure(3, weight=1)
		self.root.grid_rowconfigure(4, weight=1)

	def show_log_text(self):
		if self.log_visible:
			self.log_text.grid_remove()
			self.log_visible=False
			self.root.update_idletasks()
		else:
			self.log_text.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
			self.log_visible=True
			self.root.update_idletasks()

	def init_stream_gui(self):
		if self.som.stream is None:
			self.audio_thread=threading.Thread(target=self.som.start_stream)
			self.audio_thread.daemon= True
			self.audio_thread.start()
			self.update_dbfs_display()

			self.print_log_message("Iniciando stream de áudio")
		else:
			self.print_log_message("Stream de áudio já está ativo")

	def stop_stream_gui(self):
		if self.som.stream:
			self.som.stop_stream()
			self.print_log_message("Encerrando stream de áudio")

		else:
			self.print_log_message("O stream não está ligado")

	def update_dbfs_display(self):
		if self.som.stream:
			current_dbfs=self.som.current_dbfs
			if current_dbfs!=-999:
				self.lb_current_dbfs.config(text=f"dBFS Atual: {current_dbfs:.2f} dBFS")

		else:
			self.lb_current_dbfs.config(text="dBFS Atual: -")

		self.root.after(100, self.update_dbfs_display)

	def new_project_display(self):
		if self.som.stream:
			self.som.stop_stream()

		self.som.calibrated_dbfs = None
		self.som.material_results = {}

		self.lb_calibrated_dbfs.config(text="Calibração: Não realizada")
		self.lb_current_dbfs.config(text="dBFS Atual: -")

		for material_data in self.list_frame_material.values():
			if 'frame' in material_data and material_data['frame'] is not self.frame_material_espuma and \
				material_data['frame'] is not self.frame_material_jornal and \
				material_data['frame'] is not self.frame_material_ovo:
				material_data['frame'].destroy()
		self.list_frame_material = {}

		self.create_frame_material("Espuma", is_widget_main=True, frame_reference=self.frame_material_espuma)
		self.create_frame_material("Jornal", is_widget_main=True, frame_reference=self.frame_material_jornal)
		self.create_frame_material("Caixa de Ovo", is_widget_main=True, frame_reference=self.frame_material_ovo)

		self.count_material_row = 0
		self.count_material_column = 0

		self.log_text["state"]= tk.NORMAL
		self.log_text.delete(1.0, tk.END)
		self.log_text["state"]= tk.DISABLED

	def confirm_new_project(self):
		confirm=messagebox.askokcancel("Novo Projeto", "Deseja iniciar um novo projeto?")

		if confirm:
			self.new_project_display()

	def screen_time_config(self):
		window=tk.Toplevel(self.root)
		window.title("Tempo Medida")
		window.transient(self.root)
		window.grab_set()

		self.time_history_var= self.time_count_var.get()

		tk.Label(window, text="Tempo de duração das medidas").pack(pady=10)
		tk.Scale(window, variable=self.time_count_var, from_=1, to=10, orient=tk.HORIZONTAL, resolution=1).pack(pady=5)

		tk.Button(window, text="Alterar", command= lambda: self.confirm_alter_time(window)).pack(pady=10)

	def confirm_alter_time(self, window):
		if self.time_count_var.get()==self.time_history_var:
			messagebox.showwarning("Aviso", "Valor igual ao original")
			return

		confirm=messagebox.askyesno("Confimação", f"Deseja alterar o tempo de duração da medida de {self.time_history_var} s para {self.time_count_var.get()} s?")

		if confirm:
			messagebox.showinfo("Sucesso", "Valor alterado com sucesso. Projeto será reiniciado")
			self.new_project_display()
			window.grab_release()
			window.destroy()

		else:
			self.time_count_var.set(self.time_history_var)
			messagebox.showinfo("Cancelado", "Alteração cancelada!")
			return

	def screen_new_material(self):
		window=tk.Toplevel(self.root)
		window.title("Novo Material")
		window.transient(self.root)
		window.grab_set()

		main_frame = ttk.Frame(window, padding="10 10 10 10")
		main_frame.pack(expand=True, fill="both")

		ttk.Label(main_frame, text="Adicionar Novo Material", font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)
		ttk.Label(main_frame, text="Nome do Material:").grid(row=1, column=0, sticky="w", padx=5, pady=5)

		self.entry_name_material_popup = ttk.Entry(main_frame, textvariable=self.name_material_var)
		self.entry_name_material_popup.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

		ttk.Button(main_frame, text="Adicionar Material", command=lambda: self._add_material_and_measure(window)).grid(row=2, column=0, padx=5, pady=10)
		ttk.Button(main_frame, text="Cancelar", command=window.destroy).grid(row=2, column=1, padx=5, pady=10)

	def _add_material_and_measure(self, window):
		if self.som.stream is None:
			messagebox.showwarning("Aviso", "O stream de áudio não está ativo. Por favor, inicie o stream antes de adicionar um novo material.")
			return

		material_name = self.name_material_var.get()
		if material_name.lower()=="material" or not material_name.strip():
			messagebox.showerror("Erro", "Nome de material inválido!")
			return

		if material_name in self.list_frame_material:
			confirm= messagebox.askokcancel("Aviso", "Já existe um material cadastrado com esse nome. Deseja sobrescreve-lo?")
			if not confirm:
				return
			else:
				old_frame = self.list_frame_material[material_name]
				if old_frame and 'frame' in old_material_data:
					old_material_data['frame'].destroy()
				del self.list_frame_material[material_name]

		self.start_measure_material(material_name, is_widget_main=False)

		window.destroy()
		self.name_material_var.set("Material")

	def close_system_gui(self):
		self.music.stop_sound()
		if self.som.stream:
			self.som.stop_stream()

		self.root.destroy()

	def start_measure_calibration(self):
		if self.som.stream is None:
			self.init_stream_gui()

		time.sleep(1)

		duration= self.time_count_var.get()
		self.print_log_message(f"Iniciando calibração do microfone por {duration} segundos")

		self.som.start_data_collection()
		self.music.play_sound()

		self.root.after(int(duration * 1000), self.complete_measure_mic)

	def complete_measure_mic(self):
		self.music.stop_sound()
		avg= self.som.get_avarage_dbfs()

		if avg is not None:
			self.som.calibrated_dbfs= avg
			self.lb_calibrated_dbfs.config(text=f"Calibração: {avg:.2f} dBFS")
			self.print_log_message(f"Calibração concluída. Média do valor para controle: {avg:.2f} dBFS")

		else:
			self.som.calibrated_dbfs = None
			self.print_log_message(f"Calibração não realizada")

	def start_measure_material(self, material_name, is_widget_main=False):
		if self.som.stream is None:
			self.init_stream_gui()
			return

		if self.som.calibrated_dbfs is None:
			messagebox.showwarning("Aviso", "É necessário calibrar o microfone primeiro para referência!")
			return

		time.sleep(1)

		duration=self.time_count_var.get()

		self.print_log_message(f"Iniciando medição para {material_name} por {duration:.1f} segundos.")

		self.som.start_data_collection()
		self.music.play_sound()

		if material_name in self.list_frame_material:
			if 'lb_current_dbfs' in self.list_frame_material[material_name]:
				self.list_frame_material[material_name]['lb_current_dbfs'].config(text="Medindo...")

		self.root.after(int(duration * 1000), lambda: self.complete_measure_material(material_name, is_widget_main))

	def complete_measure_material(self, material_name, is_widget_main):
		self.music.stop_sound()
		avg= self.som.get_avarage_dbfs()

		if avg is not None and self.som.calibrated_dbfs is not None:
			attenuation=self.som.calibrated_dbfs - avg
			self.som.material_results[material_name]= {"media": avg, "atenuacao": attenuation}

			self.print_log_message(f"Medição para {material_name} concluida")
			self.print_log_message(f"Valor médio: {avg:.2f} dBFS")
			self.print_log_message(f"Valor de atenuação: {attenuation:.2f} dB")

			material_data = self.list_frame_material.get(material_name)
			if material_data:
				material_data['lb_media'].config(text=f"dBFS medido do {material_name}: {avg:.2f} dBFS")
				material_data['lb_atenuacao'].config(text=f"Atenuação: {attenuation:.2f} dB")

				if 'lb_current_dbfs' in material_data:
					material_data['lb_current_dbfs'].config(text="Pronto")

			if not is_widget_main and material_name not in self.list_frame_material:
				self.create_frame_material(material_name)

		else:
			self.print_log_message(f"Não foi possível realizar a medição de {material_name}. Dados inválidos ou calibração ausente.")
			if material_name in self.list_frame_material and 'lb_current_dbfs' in self.list_frame_material[material_name]:
				self.list_frame_material[material_name]['lb_current_dbfs'].config(text="Erro!")

	def create_frame_material(self, material_name, is_widget_main=False, frame_reference=None):
		current_material_frame= None
		if is_widget_main and frame_reference is not None:
			current_material_frame= frame_reference

			for widget in current_material_frame.winfo_children():
				widget.destroy()

		else:
			if not self.frame_list_material.winfo_ismapped():
				self.frame_list_material.grid(row=4, columnspan=3, padx=5, pady=5, sticky="ew")
			current_material_frame=tk.Frame(self.frame_list_material, bd=2, relief="groove", padx=10, pady=10)

		if material_name not in self.som.material_results:
			self.som.material_results[material_name] = {'media': 0.0, 'atenuacao': 0.0}

		tk.Label(current_material_frame, text=f"Material: {material_name}", font=('Arial', 10, 'bold')).pack(pady=2)

		btn_medir_text = "Medir"
		if not is_widget_main:
			btn_medir_text = "Refazer Medida"

		btn_medir = tk.Button(current_material_frame, text=btn_medir_text, command=lambda: self.start_measure_material(material_name, is_widget_main=is_widget_main))
		btn_medir.pack()

		lb_current_dbfs_material = tk.Label(current_material_frame, text="Sem medidas!")
		lb_current_dbfs_material.pack()

		lb_media_material = tk.Label(current_material_frame, text=f"dBFS medido do {material_name}: {self.som.material_results[material_name]['media']:.2f} dBFS")
		lb_media_material.pack()

		lb_atenuacao_material = tk.Label(current_material_frame, text=f"Atenuação: {self.som.material_results[material_name]['atenuacao']:.2f} dB")
		lb_atenuacao_material.pack()

		self.list_frame_material[material_name] = {
			"frame": current_material_frame,
			"lb_current_dbfs": lb_current_dbfs_material,
			"lb_media": lb_media_material,
			"lb_atenuacao": lb_atenuacao_material
		}

		if not is_widget_main:
			if self.count_material_column > 2:
				self.count_material_column = 0
				self.count_material_row += 1

			current_material_frame.grid(row=self.count_material_row, column=self.count_material_column, padx=5, pady=5)
			self.count_material_column += 1

	def print_log_message(self, message):
		self.log_text["state"]= tk.NORMAL
		self.log_text.insert(tk.END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}\n")
		self.log_text["state"]= tk.DISABLED

		self.log_text.see(tk.END)

	#Criando TreeView
	def show_result_table(self):
		window= tk.Toplevel(self.root)
		window.title("Tabelas de Dados")
		window.transient(self.root)
		window.grab_set()

	#Criando gráfico com o Matplotlib
	def show_graph(self):
		window= tk.Toplevel(self.root)
		window.title("Tabelas de Dados")
		window.transient(self.root)
		window.grab_set()

	def donothing(self):
		pass

if __name__=="__main__":
	root=tk.Tk()
	app=TelaProjeto(root)
	root.mainloop()
