from imports import *
from functions import *

def initialize_level_set_square(xlim, ylim, center, length, dx):
    """
    Inicializa la función de nivel en forma de cuadrado.
    
    Parameters:
    xlim : tuple
        Limites en la dirección x (xmin, xmax).
    ylim : tuple
        Limites en la dirección y (ymin, ymax).
    center : tuple
        Coordenadas del centro del cuadrado (cx, cy).
    length : float
        Longitud del lado del cuadrado.
    dx : float
        Paso espacial (resolución de la malla).

    Returns:
    phi : ndarray
        Matriz que representa la función de nivel.
    X, Y : ndarray
        Matrices de coordenadas.
    """
    xmin, xmax = xlim
    ymin, ymax = ylim
    cx, cy = center
    
    # Crear una malla de puntos en el espacio 2D
    x = np.arange(xmin, xmax, dx)
    y = np.arange(ymin, ymax, dx)
    X, Y = np.meshgrid(x, y)

    # Inicializar phi en forma de cuadrado
    phi = np.ones_like(X)  # Inicializa phi a 1 (fuera del cuadrado)
    half_length = length / 2.0

    # Asignar valores dentro del cuadrado
    phi[(X >= (cx - half_length)) & (X <= (cx + half_length)) &
        (Y >= (cy - half_length)) & (Y <= (cy + half_length))] = -1

    return phi, X, Y