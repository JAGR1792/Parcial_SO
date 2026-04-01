import csv # para manejo de archivos CSV
import random # para generar variaciones aleatorias entre los datos
import threading # Hilos
import time # para control de tiempos y pausas entre lecturas
from collections import deque # para facilitarme la vida
from dataclasses import dataclass, field # decoradores para no tener que escribir código repetitivo
from datetime import datetime # Para reportes por si time no funciona bien el timestamp del sistema operativo
from pathlib import Path # para manejo de rutas de archivos
from typing import Any # para anotaciones de tipos en caso de que Tkinter no esté disponible

from matplotlib.figure import Figure

# ========== INTENTO DE CARGA DE TK PARA GUI ==========
try:
    import tkinter as tk
    from tkinter import ttk
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    TK_DISPONIBLE = True
except ImportError:
    TK_DISPONIBLE = False
    tk: Any = None
    ttk: Any = None
    FigureCanvasTkAgg: Any = None


# ========== ESTRUCTURA DE DATOS ==========

@dataclass
class DatosClimaticos:
    """Almacena una muestra de datos climáticos con timestamp."""
    timestamp: datetime
    temperatura: float
    humedad: float
    presion: float


@dataclass
class EstacionMeteorologica:
    """Almacena estado compartido entre hilos."""
    archivo_salida: Path = field(default_factory=lambda: Path("registro_meteorologico.csv"))
    
    # Control de hilos
    evento_parada: threading.Event = field(default_factory=threading.Event)
    bloqueo_datos: threading.Lock = field(default_factory=threading.Lock)
    
    # Datos compartidos
    datos_actuales: DatosClimaticos | None = None
    datos_pendientes: list[DatosClimaticos] = field(default_factory=list)
    historial: deque = field(default_factory=lambda: deque(maxlen=120))
    
    # Variables de simulación
    temperatura_actual: float = field(default_factory=lambda: random.uniform(18.0, 30.0))
    humedad_actual: float = field(default_factory=lambda: random.uniform(40.0, 80.0))
    presion_actual: float = field(default_factory=lambda: random.uniform(1005.0, 1020.0))
    
    def __post_init__(self):
        """Inicializa el archivo CSV con encabezados."""
        if not self.archivo_salida.exists() or self.archivo_salida.stat().st_size == 0:
            with self.archivo_salida.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["fecha", "hora", "temperatura_c", "humedad_pct", "presion_hpa"])


# ==================== HILO 1: ADQUISICION DE DATOS ====================
# Genera datos climáticos cada 1 segundo con variaciones realistas.
# Simula sensores que leen temperatura, humedad y presión.

def limitar_rango(valor: float, minimo: float, maximo: float) -> float:
    """Limita un valor al rango especificado."""
    return max(minimo, min(maximo, valor))


def obtener_temperatura_siguiente(estacion: EstacionMeteorologica) -> float:
    """Simula variación realista de temperatura."""
    variacion = random.uniform(-0.35, 0.35)
    estacion.temperatura_actual = limitar_rango(
        estacion.temperatura_actual + variacion, 10.0, 40.0
    )
    return round(estacion.temperatura_actual, 2)


def obtener_humedad_siguiente(estacion: EstacionMeteorologica) -> float:
    """Simula variación realista de humedad."""
    variacion = random.uniform(-1.2, 1.2)
    estacion.humedad_actual = limitar_rango(
        estacion.humedad_actual + variacion, 15.0, 100.0
    )
    return round(estacion.humedad_actual, 2)


def obtener_presion_siguiente(estacion: EstacionMeteorologica) -> float:
    """Simula variación realista de presión."""
    variacion = random.uniform(-0.55, 0.55)
    estacion.presion_actual = limitar_rango(
        estacion.presion_actual + variacion, 980.0, 1040.0
    )
    return round(estacion.presion_actual, 2)


def hilo_adquisicion_datos(estacion: EstacionMeteorologica) -> None:
    """
    HILO 1: Adquisición de datos climáticos.
    
    Corre en loop infinito, cada 1 segundo:
    - Genera temperatura, humedad, presión con pequeñas variaciones
    - Almacena los datos en variables compartidas (thread-safe con lock)
    - Los datos quedan disponibles para otros hilos
    """
    print("Hilo 1 Funciona")
    
    while not estacion.evento_parada.is_set():
        # Genera nuevos datos climáticos
        muestra = DatosClimaticos(
            timestamp=datetime.now(),
            temperatura=obtener_temperatura_siguiente(estacion),
            humedad=obtener_humedad_siguiente(estacion),
            presion=obtener_presion_siguiente(estacion),
        )
        
        # Guarda en datos compartidos (protegido con lock)
        with estacion.bloqueo_datos:
            estacion.datos_actuales = muestra
            estacion.datos_pendientes.append(muestra)
            estacion.historial.append(muestra)
        
        # Espera 1 segundo antes de siguiente lectura
        time.sleep(1)


# ==================== HILO 2: REGISTRO EN ARCHIVO CSV ====================
# Guarda datos en archivo CSV cada 5 segundos de forma thread-safe.
# Lee desde la cola de datos pendientes y escribe en el archivo.

def hilo_registro_archivo(estacion: EstacionMeteorologica) -> None:
    """
    HILO 2: Registro de datos en archivo CSV.
    
    Corre en loop infinito, cada 5 segundos:
    - Lee datos pendientes sin bloquear el Hilo 1
    - Escribe los datos en archivo CSV con fecha, hora y valores
    - Mantiene un registro continuo del estado meteorológico
    """
    print("Hilo 2 Funciona")
    
    while not estacion.evento_parada.is_set():
        # Espera 5 segundos entre grabaciones
        time.sleep(5)
        
        # Obtiene datos pendientes de forma thread-safe
        with estacion.bloqueo_datos:
            if not estacion.datos_pendientes:
                continue
            lote = estacion.datos_pendientes.copy()
            estacion.datos_pendientes.clear()
        
        # Escribe el lote en el archivo CSV
        with estacion.archivo_salida.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for item in lote:
                writer.writerow(
                    [
                        item.timestamp.strftime("%Y-%m-%d"),
                        item.timestamp.strftime("%H:%M:%S"),
                        f"{item.temperatura:.2f}",
                        f"{item.humedad:.2f}",
                        f"{item.presion:.2f}",
                    ]
                )


# ==================== HILO 3: VISUALIZACION EN GUI / CONSOLA ====================
# Muestra datos en tiempo real: interfaz gráfica si está disponible, consola alternativa.

def construir_descripcion_clima(datos: DatosClimaticos, tendencia_temp: float | None) -> str:
    """Genera una descripción textual del estado del clima."""
    # Descripción de temperatura
    if datos.temperatura >= 30:
        estado_temp = "ambiente caluroso"
    elif datos.temperatura <= 15:
        estado_temp = "ambiente frío"
    else:
        estado_temp = "temperatura confortable"
    
    # Descripción de humedad
    if datos.humedad >= 75:
        estado_humedad = "humedad alta"
    elif datos.humedad <= 35:
        estado_humedad = "ambiente seco"
    else:
        estado_humedad = "humedad moderada"
    
    # Descripción de presión
    if datos.presion <= 1000:
        estado_presion = "presión baja"
    elif datos.presion >= 1020:
        estado_presion = "presión alta"
    else:
        estado_presion = "presión estable"
    
    # Descripción de tendencia
    if tendencia_temp is None:
        texto_tendencia = "sin tendencia suficiente"
    elif tendencia_temp > 0.2:
        texto_tendencia = "la temperatura va en aumento"
    elif tendencia_temp < -0.2:
        texto_tendencia = "la temperatura va en descenso"
    else:
        texto_tendencia = "la temperatura se mantiene estable"
    
    return (
        f"Se registra {estado_temp}, {estado_humedad} y {estado_presion}; "
        f"además, {texto_tendencia}."
    )


class InterfazGrafica:
    """GUI con gráficas y datos en tiempo real (si Tkinter está disponible)."""
    
    def __init__(self, estacion: EstacionMeteorologica) -> None:
        self.estacion = estacion
        self.raiz: Any = tk.Tk()
        self.raiz.title("Estación Meteorológica - Simulador")
        self.raiz.geometry("1000x700")
        self.raiz.minsize(900, 600)
        
        # Variables de interfaz
        self.var_temperatura = tk.StringVar(value="Temperatura: -- °C")
        self.var_humedad = tk.StringVar(value="Humedad: -- %")
        self.var_presion = tk.StringVar(value="Presión: -- hPa")
        self.var_descripcion = tk.StringVar(value="Esperando datos...")
        
        self._construir_interfaz()
        self.raiz.protocol("WM_DELETE_WINDOW", self._al_cerrar)
    
    def _construir_interfaz(self) -> None:
        """Crea la estructura visual de la interfaz."""
        marco_principal = ttk.Frame(self.raiz, padding=12)
        marco_principal.pack(fill=tk.BOTH, expand=True)
        
        # Encabezado
        encabezado = ttk.Label(
            marco_principal,
            text="Estación Meteorológica Multihilo",
            font=("Helvetica", 16, "bold"),
        )
        encabezado.pack(anchor=tk.W, pady=(0, 10))
        
        # Métricas
        marco_metricas = ttk.Frame(marco_principal)
        marco_metricas.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(marco_metricas, textvariable=self.var_temperatura, font=("Helvetica", 11)).pack(
            side=tk.LEFT, padx=(0, 20)
        )
        ttk.Label(marco_metricas, textvariable=self.var_humedad, font=("Helvetica", 11)).pack(
            side=tk.LEFT, padx=(0, 20)
        )
        ttk.Label(marco_metricas, textvariable=self.var_presion, font=("Helvetica", 11)).pack(
            side=tk.LEFT
        )
        
        # Descripción
        ttk.Label(marco_principal, text="Descripción del clima:", font=("Helvetica", 11, "bold")).pack(anchor=tk.W)
        ttk.Label(
            marco_principal,
            textvariable=self.var_descripcion,
            wraplength=920,
            justify=tk.LEFT,
            font=("Helvetica", 10),
        ).pack(fill=tk.X, pady=(2, 10))
        
        # Gráficas
        figura = Figure(figsize=(10, 4.8), dpi=100)
        self.eje_temp = figura.add_subplot(311)
        self.eje_humedad = figura.add_subplot(312)
        self.eje_presion = figura.add_subplot(313)
        figura.tight_layout(pad=2.0)
        
        self.lienzo = FigureCanvasTkAgg(figura, master=marco_principal)
        self.lienzo.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _actualizar_visualizacion(self) -> None:
        """Refresca gráficas y métricas cada 1 segundo."""
        with self.estacion.bloqueo_datos:
            datos_actuales = self.estacion.datos_actuales
            puntos = list(self.estacion.historial)
        
        if datos_actuales:
            self.var_temperatura.set(f"Temperatura: {datos_actuales.temperatura:.2f} °C")
            self.var_humedad.set(f"Humedad: {datos_actuales.humedad:.2f} %")
            self.var_presion.set(f"Presión: {datos_actuales.presion:.2f} hPa")
            
            tendencia_temp = None
            if len(puntos) >= 6:
                tendencia_temp = puntos[-1].temperatura - puntos[-6].temperatura
            self.var_descripcion.set(construir_descripcion_clima(datos_actuales, tendencia_temp))
        
        # Dibuja gráficas
        if puntos:
            etiquetas = [item.timestamp.strftime("%H:%M:%S") for item in puntos]
            temperaturas = [item.temperatura for item in puntos]
            humedades = [item.humedad for item in puntos]
            presiones = [item.presion for item in puntos]
            
            self.eje_temp.clear()
            self.eje_humedad.clear()
            self.eje_presion.clear()
            
            self.eje_temp.plot(etiquetas, temperaturas, color="#d1495b", linewidth=1.8)
            self.eje_humedad.plot(etiquetas, humedades, color="#00798c", linewidth=1.8)
            self.eje_presion.plot(etiquetas, presiones, color="#3066be", linewidth=1.8)
            
            self.eje_temp.set_ylabel("Temp (°C)")
            self.eje_humedad.set_ylabel("Hum (%)")
            self.eje_presion.set_ylabel("Pres (hPa)")
            self.eje_presion.set_xlabel("Hora")
            
            self.eje_temp.grid(alpha=0.25)
            self.eje_humedad.grid(alpha=0.25)
            self.eje_presion.grid(alpha=0.25)
            
            paso = max(1, len(etiquetas) // 8)
            idx_visibles = list(range(0, len(etiquetas), paso))
            etiquetas_visibles = [etiquetas[i] for i in idx_visibles]
            
            self.eje_temp.set_xticks(idx_visibles)
            self.eje_temp.set_xticklabels([])
            self.eje_humedad.set_xticks(idx_visibles)
            self.eje_humedad.set_xticklabels([])
            self.eje_presion.set_xticks(idx_visibles)
            self.eje_presion.set_xticklabels(etiquetas_visibles, rotation=30, ha="right")
            
            self.lienzo.draw_idle()
        
        self.raiz.after(1000, self._actualizar_visualizacion)
    
    def ejecutar(self) -> None:
        """Inicia la interfaz gráfica."""
        print("✓ Hilo 3 iniciado: Visualización gráfica")
        self._actualizar_visualizacion()
        self.raiz.mainloop()
    
    def _al_cerrar(self) -> None:
        """Ejecutado al cerrar la ventana."""
        self.estacion.evento_parada.set()
        self.raiz.destroy()


def hilo_visualizacion_consola(estacion: EstacionMeteorologica) -> None:
    """
    HILO 3 (Alternativa sin GUI): Visualización en consola.
    
    Se ejecuta si Tkinter no está disponible.
    Muestra en terminal:
    - Datos actuales de temperatura, humedad, presión
    - Descripción textual del estado del clima
    """
    print("Hilo 3 Funciona, pero no muestra GUI.")
    print("=" * 70)
    
    try:
        while not estacion.evento_parada.is_set():
            with estacion.bloqueo_datos:
                datos_actuales = estacion.datos_actuales
                puntos = list(estacion.historial)
            
            if datos_actuales:
                tendencia_temp = None
                if len(puntos) >= 6:
                    tendencia_temp = puntos[-1].temperatura - puntos[-6].temperatura
                descripcion = construir_descripcion_clima(datos_actuales, tendencia_temp)
                
                print(
                    f"\n[{datos_actuales.timestamp.strftime('%H:%M:%S')}] "
                    f"T={datos_actuales.temperatura:.2f}°C | "
                    f"H={datos_actuales.humedad:.2f}% | "
                    f"P={datos_actuales.presion:.2f}hPa"
                )
                print(f"→ {descripcion}")
            
            time.sleep(1)
    except KeyboardInterrupt:
        estacion.evento_parada.set()
        print("\n" + "=" * 70)
        print("Simulación finalizada por usuario.")


# ==================== FUNCION PRINCIPAL ====================

def main() -> None:
    """
    Función principal que:
    1. Crea la estación meteorológica con estado compartido
    2. Inicia los 3 hilos en paralelo
    3. Inicia visualización (GUI o consola)
    """
    print("\n" + "=" * 70)
    print("ESTACION METEOROLOGICA - SIMULADOR MULTIHILO")
    print("=" * 70 + "\n")
    
    # Crea estructura compartida
    estacion = EstacionMeteorologica(archivo_salida=Path("registro_meteorologico.csv"))
    
    # Inicia Hilo 1 y Hilo 2 en background
    hilo_1 = threading.Thread(
        target=hilo_adquisicion_datos,
        args=(estacion,),
        name="Hilo-Adquisicion",
        daemon=True,
    )
    hilo_2 = threading.Thread(
        target=hilo_registro_archivo,
        args=(estacion,),
        name="Hilo-Registro",
        daemon=True,
    )
    
    hilo_1.start()
    hilo_2.start()
    
    # Inicia Hilo 3: visualización (GUI o consola)
    if TK_DISPONIBLE:
        interfaz = InterfazGrafica(estacion)
        interfaz.ejecutar()
    else:
        hilo_3 = threading.Thread(
            target=hilo_visualizacion_consola,
            args=(estacion,),
            name="Hilo-Visualizacion-Consola",
            daemon=False,
        )
        hilo_3.start()
        hilo_3.join()


if __name__ == "__main__":
    main()
