import numpy as np
import scipy.ndimage
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.colors as mcolors

# Parámetros
tube_radius = 10  # Radio exterior del tubo
inner_radius = 3   # Radio interior (cavidad)
resolution = 1000  # Resolución de la malla
burn_rate = 0.05  # Velocidad base de quemado
time_steps = 1000  # Número de pasos de tiempo
h = 20  # Altura del cartucho, constante

# Constantes para el modelo de presión
a = 1.0  # Constante de proporcionalidad para la velocidad de regresión
n = 0.5  # Exponente de la ley de regresión
initial_area = 2 * np.pi * inner_radius * h  # Área inicial de la pared de la cavidad

# Crear la malla 2D
x = np.linspace(-tube_radius, tube_radius, resolution)
y = np.linspace(-tube_radius, tube_radius, resolution)
X, Y = np.meshgrid(x, y)

# Crear la geometría del tubo (tubo hueco)
tube = np.sqrt(X**2 + Y**2)

# Inicializar el frente de quemado: quemado solo en la mitad superior de la cavidad
front = np.ones_like(tube)

# Establecer la condición de contorno para quemar solo la mitad superior de la cavidad
front[(tube <= inner_radius) & (Y >= 0)] = 0  # Quemado en la mitad superior de la cavidad
front[(tube > tube_radius)] = 0  # Fuera del tubo también se considera quemado

# Crear una función de velocidad de regresión (velocidad de quemado del propelente)
def fast_marching(front, speed, dx, steps):
    # Inicializar matriz de tiempos
    T = np.full_like(front, np.inf)
    T[front == 0] = 0  # Inicializar las celdas quemadas
    speed_inv = 1 / speed
    
    # Propagar el frente con el algoritmo de Fast Marching
    scipy.ndimage.distance_transform_edt(front == 1, sampling=dx, return_distances=True, distances=T)
    return T * speed_inv / steps

# Función para calcular el área no quemada de la pared de la cavidad (longitud de la circunferencia no quemada multiplicada por la altura)
def area_no_quemada_pared(radio_quemado):
    # Área no quemada de la pared = longitud de la circunferencia no quemada * altura
    return 2 * np.pi * radio_quemado * h

# Función para obtener la velocidad de regresión basada en la presión, que depende del área no quemada de la pared
def get_burn_rate(area_no_quemada):
    # Presión inversamente proporcional al área no quemada de la pared
    P = initial_area / area_no_quemada
    burn_rate = a * (P**n)  # Ley de regresión de la velocidad con presión
    return burn_rate, P  # Devolver también la presión

# Crear la figura con dos gráficos: uno para la combustión y otro para la presión
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

# Gráfico de la combustión (izquierda)
ax1.set_title('Regresión del frente de quemado en tubo hueco')
ax1.set_xlabel('X (mm)')
ax1.set_ylabel('Y (mm)')
ax1.set_xlim(-tube_radius, tube_radius)
ax1.set_ylim(-tube_radius, tube_radius)

# Gráfico de la presión (derecha)
ax2.set_title('Variación de la presión en la cámara')
ax2.set_xlabel('Tiempo (frames)')
ax2.set_ylabel('Presión relativa (P)')
ax2.set_xlim(0, time_steps)
ax2.set_ylim(0, 5)  # Definir el límite de la presión, ajustable según resultados
pressure_data = []  # Lista para almacenar los valores de presión
time_data = []  # Lista para almacenar el tiempo (frames)
pressure_line, = ax2.plot([], [], color='blue')  # Línea que mostrará la presión

# Definir la distancia de cada paso
dx = (2 * tube_radius) / resolution
time_field = fast_marching(front, burn_rate, dx, time_steps)

# Crear un mapa de color binario: rojo para quemado y blanco para no quemado
cmap = mcolors.ListedColormap(['white', 'red'])  # Blanco para no quemado, rojo para quemado
bounds = [0, 1, 2]  # Definir los límites de los valores
norm = mcolors.BoundaryNorm(bounds, cmap.N)

# Función de inicialización
img = ax1.imshow(np.zeros_like(time_field), extent=(-tube_radius, tube_radius, -tube_radius, tube_radius), origin='lower', cmap=cmap, norm=norm, interpolation='bilinear')

def update(frame):
    # Calcular el radio quemado actual (progresión del frente de quemado)
    radio_quemado = inner_radius + burn_rate * frame

    # Detener la animación cuando se alcanza el radio máximo del tubo
    if radio_quemado >= tube_radius:
        print("Todo el combustible ha sido quemado.")
        ani.event_source.stop()  # Detener la animación
        return

    # Calcular el área no quemada restante de la pared
    area_restante = area_no_quemada_pared(radio_quemado)

    # Obtener la velocidad de quemado y la presión basada en el área no quemada
    current_burn_rate, current_pressure = get_burn_rate(area_restante)

    # Actualizar el frente según los pasos de tiempo
    updated_front = np.ones_like(tube)
    updated_front[(tube <= inner_radius + current_burn_rate * frame)] = 0  # Quemado desde el interior hacia el exterior
    updated_front[(tube > tube_radius)] = 0  # Mantener el quemado fuera del tubo
    
    # Crear una imagen binaria: 1 para quemado (rojo), 0 para no quemado (blanco)
    binary_field = np.zeros_like(tube)
    binary_field[updated_front == 0] = 1  # Área quemada en rojo
    
    # Actualizar el gráfico de combustión
    img.set_data(binary_field)
    
    # Actualizar el gráfico de presión
    pressure_data.append(current_pressure)
    time_data.append(frame)
    pressure_line.set_data(time_data, pressure_data)
    
    return [img, pressure_line]

# Crear la animación con una pausa de 100 ms entre fotogramas
ani = FuncAnimation(fig, update, frames=time_steps, blit=True, repeat=False, interval=1/60)

# Mostrar la animación
plt.tight_layout()
plt.show()
