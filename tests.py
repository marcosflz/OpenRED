import numpy as np
import pyvista as pv

# Crear un cubo como modelo sólido
cube = pv.Cube()

# Crear un gráfico 3D y visualizar el cubo
plotter = pv.Plotter()
plotter.add_mesh(cube, color='lightblue', show_edges=True)
plotter.add_title('Modelo 3D: Cubo')

# Mostrar el modelo
plotter.show()

# Crear un plano de corte
# Definir un plano en el eje Z
normal_vector = (0, 0, 1)  # Dirección del plano (normal)
origin_point = (0, 0, 0)    # Punto de origen del plano

# Realizar el corte
slice = cube.slice(normal=normal_vector, origin=origin_point)

# Mostrar el corte
plotter = pv.Plotter()
plotter.add_mesh(slice, color='orange', show_edges=True)
plotter.add_title('Corte Transversal del Cubo')

# Mostrar el corte
plotter.show()
