# Parcial SO - Estación Meteorológica Multihilo

Simulador de estación meteorológica con 3 hilos independientes.

## Descripción de Hilos

- **Hilo 1**: Adquisición de datos climáticos cada 1 segundo (temperatura, humedad, presión con variaciones realistas)
- **Hilo 2**: Registro en archivo CSV cada 5 segundos (mantiene histórico con fecha y hora)
- **Hilo 3**: Visualización en tiempo real con gráficas e interfaz

## Instalación Rápida

```bash
git clone https://github.com/JAGR1792/Parcial_SO.git
cd Parcial_SO
pip install -r requirements.txt
python estacion_meteorologica.py
```

## Requisitos

- Python 3.10+
- matplotlib
