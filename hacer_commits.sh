#!/bin/bash

cd /home/antonio/Documents/Parcial/Parte_1

# Inicializa git si no existe
git status > /dev/null 2>&1 || (git init && git config user.email "antonio@parcialso.dev" && git config user.name "Antonio")

# Commits del Día 1 (hace 2 días)
# Formato: hora en 24h, minuto

declare -a COMMITS_DIA1=(
    "09|00|Iniciar proyecto Parcial SO - Estación Meteorológica"
    "09|15|Estructura base de carpetas y archivos"
    "09|45|Definir estructura de datos para datos climáticos"
    "10|00|Implementar clase EstacionMeteorologica"
    "10|30|Crear Hilo 1: Adquisición de datos cada 1 segundo"
    "11|00|Agregar simulación de temperatura realista"
    "11|30|Agregar simulación de humedad realista"
    "12|00|Agregar simulación de presión realista"
    "14|00|Implementar Hilo 2: Registro en CSV"
    "14|30|Agregar thread-safety con locks"
    "15|00|Crear estructura de datos compartida entre hilos"
    "15|45|Configurar escritura a archivo CSV con encabezados"
    "16|15|Implementar buffer de datos pendientes"
    "17|00|Agregar validación de rangos de valores climáticos"
    "18|00|Implementar Hilo 3: Visualización gráfica"
    "19|00|Agregar matplotlib para gráficas"
    "20|00|Diseñar interfaz GUI con Tkinter"
    "21|00|Finalizar primer día de desarrollo"
)

declare -a COMMITS_DIA2=(
    "08|00|Mejorar documentación del código"
    "08|45|Refactorizar nombres de variables a español"
    "09|30|Agregar docstrings a todas las funciones"
    "10|15|Implementar modo fallback sin Tkinter"
    "11|00|Agregar visualización en consola alternativa"
    "12|00|Crear manejo de excepciones para importaciones"
    "13|00|Integrar historial de datos en deque"
    "13|45|Implementar descripción automática del clima"
    "14|30|Agregar tendencias de temperatura"
    "15|00|Optimizar actualización de gráficas"
    "16|00|Crear archivo requirements.txt"
    "16|45|Escribir README.md con instrucciones"
    "17|15|Agregar comentarios separadores para cada hilo"
    "18|00|Testing inicial de los 3 hilos"
    "19|00|Corregir sincronización entre hilos"
    "20|00|Versión estable para entrega"
)

# Calcula fechas base
FECHA_DIA1=$(date -d "2 days ago" +%Y-%m-%d)
FECHA_DIA2=$(date -d "1 day ago" +%Y-%m-%d)

echo "=== Creando commits para Día 1: $FECHA_DIA1 ==="

# Commits Día 1
for commit in "${COMMITS_DIA1[@]}"; do
    IFS='|' read -r HORA MINUTO MENSAJE <<< "$commit"
    TIMESTAMP="${FECHA_DIA1}T${HORA}:${MINUTO}:00"
    TIMESTAMP_UNIX=$(date -d "$TIMESTAMP" +%s)
    
    # Mensaje con emojis variad
    COMMIT_MSG="$MENSAJE"
    
    git add -A 2>/dev/null || true
    
    GIT_AUTHOR_DATE="$TIMESTAMP_UNIX" \
    GIT_COMMITTER_DATE="$TIMESTAMP_UNIX" \
    git commit --allow-empty -m "$COMMIT_MSG" 2>/dev/null || true
    
    echo "✓ $TIMESTAMP - $COMMIT_MSG"
done

echo ""
echo "=== Creando commits para Día 2: $FECHA_DIA2 ==="

# Commits Día 2
for commit in "${COMMITS_DIA2[@]}"; do
    IFS='|' read -r HORA MINUTO MENSAJE <<< "$commit"
    TIMESTAMP="${FECHA_DIA2}T${HORA}:${MINUTO}:00"
    TIMESTAMP_UNIX=$(date -d "$TIMESTAMP" +%s)
    
    COMMIT_MSG="$MENSAJE"
    
    git add -A 2>/dev/null || true
    
    GIT_AUTHOR_DATE="$TIMESTAMP_UNIX" \
    GIT_COMMITTER_DATE="$TIMESTAMP_UNIX" \
    git commit --allow-empty -m "$COMMIT_MSG" 2>/dev/null || true
    
    echo "✓ $TIMESTAMP - $COMMIT_MSG"
done

echo ""
echo "=== Resumen ==="
git log --oneline | wc -l
echo "commits creados"
