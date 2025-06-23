import tkinter as tk
from controlador import ZooInventarioApp # Keep ZooInventarioApp in interfaz.py

# Configura tu API Key de Gemini (usada dentro de interfaz.py)
API_KEY = "AIzaSyAz-PDOis1eJrF5pgWkZ_3dkPvqGW-tY-w"

if __name__ == "__main__":
    # Se lanza primero la ventana principal
    root = tk.Tk()
    app = ZooInventarioApp(root, api_key=API_KEY) 
    root.mainloop()