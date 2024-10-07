from imports import *


def get_data(type, file):
    """
    Fetches JSON data from a specified file and directory.

    Parameters:
    - type (str): The folder name where the file is located.
    - file (str): The name of the file from which to load the data.

    Returns:
    - data (dict): The data loaded from the specified JSON file.
    """
    
    # Open the temp_dir.txt file to get the directory path where data is stored
    with open('temp_dir.txt', 'r') as txt:
        dir = txt.readline().strip()  # Read the directory path and remove extra spaces/newlines
    
    # Construct the full path to the JSON file based on the provided type and file
    file_path = dir + f'\\{type}\\' + file
    
    # Open the specified JSON file and load its content
    with open(file_path, 'r') as file:
        data = json.load(file)  # Load the JSON content into a Python dictionary
    
    return data  # Return the loaded data


def get_entry_value(entry):
    """
    Retrieves the value from a given entry widget.

    Parameters:
    - entry (tk.Entry or ctk.CTkEntry): The entry widget from which to retrieve the value.

    Returns:
    - str: The value of the entry widget. If the entry is empty, returns '0'.
    """
    
    # Get the value from the entry widget.
    # If the entry is empty, return '0' as a default value.
    return entry.get() if entry.get() else '0'


def validate_scientific_notation(value):
    """
    Validates if a given string follows scientific notation format.

    Parameters:
    - value (str): The string to be validated.

    Returns:
    - bool: True if the string is in valid scientific notation, otherwise False.
    """
    
    # Regular expression pattern for matching scientific notation.
    pattern = r'^-?\d*\.?\d+(?:[eE][-+]?\d+)?$'
    
    # Use the 're.match' function to check if the value matches the pattern.
    # If it matches, return True; otherwise, return False.
    return re.match(pattern, value) is not None


def get_database_components():
    """
    Retrieves distinct components from the 'termoquimica' table in a SQLite database and returns them
    along with their LaTeX representations.

    Returns:
    - list: A list containing two elements:
        1. A list of distinct component names from the database.
        2. A dictionary mapping component names to their LaTeX representations.
    """
    
    # Connect to the SQLite database 'database.db'.
    conn = sqlite3.connect('database.db')
    
    # Create a cursor object to execute SQL queries.
    cursor = conn.cursor()
    
    # Execute an SQL query to retrieve distinct component names from the 'termoquimica' table.
    cursor.execute("SELECT DISTINCT Component FROM termoquimica")
    
    # Fetch all results from the query and extract the first column (component names).
    components = [row[0] for row in cursor.fetchall()]
    
    # Close the database connection.
    conn.close()
    
    # Convert each component name to its LaTeX representation using 'convert_to_latex' function.
    latex_components = [convert_to_latex(component) for component in components]
    
    # Create a dictionary that maps component names to their LaTeX representations.
    latex_map = dict(zip(components, latex_components))
    
    # Return both the list of components and the dictionary mapping components to LaTeX.
    return [components, latex_map]


def get_propellant_value(column_name, cell_value):
    """
    Retrieves distinct values from a specified column in the 'propelente' table where
    the 'Propelente' column matches a given value.

    Args:
    - column_name (str): The name of the column from which to retrieve values.
    - cell_value (str): The value to search for in the 'Propelente' column.

    Returns:
    - list: A list of distinct values from the specified column where the 'Propelente'
            column matches the given value.
    """
    
    # Connect to the SQLite database 'database.db'.
    conn = sqlite3.connect('database.db')
    
    # Create a cursor object to execute SQL queries.
    cursor = conn.cursor()
    
    # Define the SQL query to fetch distinct values from the specified column where 'Propelente' matches cell_value.
    query = f"""
    SELECT DISTINCT {column_name}
    FROM propelente
    WHERE propelente.Propelente = ?"""
    
    # Execute the query, passing the 'cell_value' to replace the placeholder (?) in the query.
    cursor.execute(query, (cell_value,))
    
    # Fetch all results and store them in a list.
    components = [row[0] for row in cursor.fetchall()]
    
    # Close the database connection.
    conn.close()
    
    # Return the list of distinct values from the specified column.
    return components


def convert_to_latex(component):
    """
    Converts a chemical component string into LaTeX format by:
    1. Removing any text within parentheses.
    2. Converting numbers into subscript format for chemical notations.

    Args:
    - component (str): The chemical component string (e.g., "H2O", "C6H12O6").

    Returns:
    - str: A LaTeX-formatted string where numbers are subscripted.
    """
    
    # Step 1: Remove any text inside parentheses along with the parentheses themselves.
    component = re.sub(r'\(.*?\)', '', component).strip()
    
    # Step 2: Replace any numeric characters in the string with LaTeX subscript notation.
    component = re.sub(r'(\d+)', r'_{\1}', component)
    
    # Return the LaTeX-formatted component string.
    return component


def save_dir_path(dir_path):
    """
    Saves the given directory path to a temporary file.

    Args:
    - dir_path (str): The directory path to be saved.

    This function writes the provided directory path into a file named 
    'temp_dir.txt' for temporary use in the application.
    """
    
    # Open the file "temp_dir.txt" in write mode. If it doesn't exist, it will be created.
    with open("temp_dir.txt", "w") as file:
        # Write the directory path to the file.
        file.write(dir_path)


def get_dir_path():
    """
    Retrieves the directory path from a temporary file.

    Returns:
    - str or None: The directory path if it exists; otherwise, None.

    This function checks for the existence of the 'temp_dir.txt' file. If the file exists,
    it reads the content and returns the directory path. If the file does not exist, it returns None.
    """
    
    # Check if the temporary file "temp_dir.txt" exists.
    if os.path.exists("temp_dir.txt"):
        # Open the file in read mode.
        with open("temp_dir.txt", "r") as file:
            # Read the contents of the file, stripping any leading/trailing whitespace.
            return file.read().strip()
    
    # Return None if the file does not exist.
    return None


def clear_dir_path():
    """
    Deletes the temporary directory path file.

    This function checks for the existence of the 'temp_dir.txt' file. 
    If the file exists, it deletes the file from the filesystem.
    """

    # Check if the temporary file "temp_dir.txt" exists.
    if os.path.exists("temp_dir.txt"):
        # Remove the file from the filesystem.
        os.remove("temp_dir.txt")


def newtonRaph(f: Callable[[float], float], x0: float, tol: float, max_iter: int, h: float) -> Union[float, None]:
    """
    Newton-Raphson method for finding the roots of a function.

    Parameters:
    f : Callable[[float], float]
        The objective function for which the root is to be found.
    x0 : float
        Initial guess for the root.
    tol : float
        Tolerance level for convergence.
    max_iter : int
        Maximum number of iterations to perform.
    h : float
        Small step size for numerical derivative approximation.

    Returns:
    float
        The approximate root of the function if found, otherwise returns None and displays an error message.
    """
    
    def fp(f: Callable[[float], float], x: float, h: float) -> float:
        """
        Computes the numerical derivative of the function at a given point.

        Parameters:
        f : Callable[[float], float]
            The function for which the derivative is calculated.
        x : float
            The point at which the derivative is evaluated.
        h : float
            Small step size for derivative approximation.

        Returns:
        float
            The numerical derivative at point x.
        """
        return (f(x + h) - f(x - h)) / (2 * h)

    x = x0  # Start with the initial guess
    for i in range(max_iter):
        fx = f(x)  # Evaluate the function at the current x
        dfx = fp(f, x, h)  # Calculate the numerical derivative

        if dfx == 0:  # Check for zero derivative to avoid division by zero
            messagebox.showinfo("Error", "Zero derivative. Newton-Raphson method cannot proceed.")
            return None

        x_new = x - fx / dfx  # Update the root estimate using the Newton-Raphson formula

        if abs(x_new - x) < tol:  # Check for convergence
            return x_new  # Return the approximated root if within tolerance

        x = x_new  # Update x for the next iteration

    messagebox.showinfo("Error", "Newton-Raphson method did not converge within the maximum number of iterations.")
    return None


def integration(f: Callable[[float], float], a: float, b: float, h: float) -> float:
    """
    Calculates the approximate definite integral of a function f over the interval [a, b]
    using the trapezoidal rule with a step size of h.

    Parameters:
    f : Callable[[float], float]
        The function to integrate. It takes a float as input and returns a float.
    a : float
        The lower limit of integration.
    b : float
        The upper limit of integration.
    h : float
        The step size for integration.

    Returns:
    float
        The approximate value of the definite integral of f over [a, b].
    """
    
    # Calculate the integral using the trapezoidal rule
    return h * ( (f(a) + f(b)) / 2 + sum(f(a + k * h) for k in range(1, int((b - a) / h))) )


def discreteIntegration(fs: List[float], xs: List[float]) -> float:
    """
    Calculates the approximate integral of discrete data points using the trapezoidal rule.

    Parameters:
    fs : List[float]
        The function values at discrete points.
    xs : List[float]
        The discrete points corresponding to the function values.

    Returns:
    float
        The approximate value of the integral computed using the trapezoidal rule.
    """
    # Calculate the integral using the trapezoidal rule
    return sum([(xs[i + 1] - xs[i]) * (fs[i + 1] + fs[i]) / 2 for i in range(len(fs) - 1)])


def initialize_database() -> None:
    """
    Initializes the SQLite database and creates the necessary tables if they do not exist.

    This function creates two tables:
    1. termoquimica: Stores thermochemical data for various components.
    2. propelente: Stores data for propellants.

    Returns:
    None
    """
    db_filename = 'database.db'  # Database filename
    conn = sqlite3.connect(db_filename)  # Connect to the SQLite database
    c = conn.cursor()  # Create a cursor object to execute SQL commands

    # Create the termoquimica table if it does not exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS termoquimica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Component TEXT,
            MolWeight NUMERIC,
            Hf0 NUMERIC,
            minColdTemp NUMERIC,
            maxColdTemp NUMERIC,
            minHotTemp NUMERIC,
            maxHotTemp NUMERIC,
            a1_cold NUMERIC,
            a2_cold NUMERIC,
            a3_cold NUMERIC,
            a4_cold NUMERIC,
            a5_cold NUMERIC,
            a1_hot NUMERIC,
            a2_hot NUMERIC,
            a3_hot NUMERIC,
            a4_hot NUMERIC,
            a5_hot NUMERIC
        )
    ''')

    # Create the propelente table if it does not exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS propelente (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Propelente TEXT,
            T_ad NUMERIC,
            MolWeight NUMERIC,
            Cp NUMERIC,
            Cv NUMERIC,
            R NUMERIC,
            gamma NUMERIC,
            cChar NUMERIC,
            Density NUMERIC,
            P1_min NUMERIC,
            P1_max NUMERIC,
            a NUMERIC,
            n NUMERIC
        )
    ''')

    conn.commit()  # Commit the changes to the database
    conn.close()   # Close the connection to the database


def insert_fig(
    fig: plt.Figure, 
    frame: ctk.CTk, 
    resize: str = 'Manual', 
    l: float = 0.1, 
    r: float = 0.9, 
    t: float = 0.9, 
    b: float = 0.2
    ) -> None:
    """
    Inserts a Matplotlib figure into a given Tkinter frame and manages resizing.

    Parameters:
    fig : plt.Figure
        The Matplotlib figure to be inserted.
    frame : ctk.CTk
        The Tkinter frame where the figure will be displayed.
    resize : str
        Specifies how to resize the figure. Options are 'Manual' or 'Auto'.
    l : float
        The left margin of the figure.
    r : float
        The right margin of the figure.
    t : float
        The top margin of the figure.
    b : float
        The bottom margin of the figure.

    Returns:
    None
    """
    # Create a new canvas for the figure but do not display it yet
    new_canvas = FigureCanvasTkAgg(fig, master=frame)
    new_widget = new_canvas.get_tk_widget()

    # Resize the figure to fit the size of the frame
    def on_resize(event=None, canvas=new_canvas, widget=new_widget, force_resize=False):
        if event is None:
            width, height = frame.winfo_width(), frame.winfo_height()
        else:
            width, height = event.width, event.height

        # Set the figure size based on the frame size
        fig.set_size_inches(width / fig.dpi, height / fig.dpi)
        if resize != 'Auto':
            fig.subplots_adjust(left=l, right=r, top=t, bottom=b)
        canvas.draw()

        if force_resize:
            # Display the new canvas
            widget.pack(side=ctk.TOP, fill=ctk.BOTH, expand=1)
            widget.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
            frame.grid_rowconfigure(0, weight=1)
            frame.grid_columnconfigure(0, weight=1)

            # Remove the old canvas if it exists
            if hasattr(frame, 'canvas'):
                old_canvas = frame.canvas
                old_widget = old_canvas.get_tk_widget()
                old_widget.destroy()

            # Assign the new canvas to the frame
            frame.canvas = canvas

            # Close the figure to free memory
            plt.close(fig)

    # If the frame does not have the resize bind, add it
    if not hasattr(frame, 'resize_bound'):
        frame.bind("<Configure>", on_resize)
        frame.resize_bound = True

    # Call on_resize manually to resize immediately
    frame.update_idletasks()
    on_resize(force_resize=True)
    plt.close(fig)


class TempSchemes:
    """
    A collection of numerical integration schemes for solving ordinary differential equations (ODEs).

    Methods:
    - Euler: Implements the Euler method for ODEs.
    - Heun: Implements the Heun method (a type of Runge-Kutta method) for ODEs.
    - RK4: Implements the fourth-order Runge-Kutta method for ODEs.
    """

    @staticmethod
    def Euler(f: List[Callable[[np.ndarray], float]], u: np.ndarray, h: float) -> np.ndarray:
        """
        Performs a single step of the Euler method.

        Parameters:
        f : List[Callable[[np.ndarray], float]]
            A list of functions representing the derivatives of the system.
        u : np.ndarray
            The current state vector.
        h : float
            The time step for the integration.

        Returns:
        np.ndarray
            The updated state vector after one step of the Euler method.
        """
        k1 = np.array([fi(u) for fi in f])  # Evaluate the derivatives
        return u + h * k1  # Update the state vector

    @staticmethod
    def Heun(f: List[Callable[[np.ndarray], float]], u: np.ndarray, h: float) -> np.ndarray:
        """
        Performs a single step of the Heun method (Improved Euler method).

        Parameters:
        f : List[Callable[[np.ndarray], float]]
            A list of functions representing the derivatives of the system.
        u : np.ndarray
            The current state vector.
        h : float
            The time step for the integration.

        Returns:
        np.ndarray
            The updated state vector after one step of the Heun method.
        """
        k1 = np.array([fi(u) for fi in f])  # Evaluate the derivatives at the current state
        k2 = np.array([fi(u + k1 * h) for fi in f])  # Evaluate the derivatives at the predicted state
        return u + h * (k1 + k2) / 2  # Update the state vector

    @staticmethod
    def RK4(f: List[Callable[[np.ndarray], float]], u: np.ndarray, h: float) -> np.ndarray:
        """
        Performs a single step of the fourth-order Runge-Kutta method.

        Parameters:
        f : List[Callable[[np.ndarray], float]]
            A list of functions representing the derivatives of the system.
        u : np.ndarray
            The current state vector.
        h : float
            The time step for the integration.

        Returns:
        np.ndarray
            The updated state vector after one step of the RK4 method.
        """
        k1 = np.array([fi(u) for fi in f])  # Evaluate the derivatives at the current state
        k2 = np.array([fi(u + 0.5 * k1 * h) for fi in f])  # Evaluate the derivatives at the midpoint
        k3 = np.array([fi(u + 0.5 * k2 * h) for fi in f])  # Evaluate the derivatives at the next midpoint
        k4 = np.array([fi(u + k3 * h) for fi in f])  # Evaluate the derivatives at the next state
        return u + h * (k1 + 2 * k2 + 2 * k3 + k4) / 6  # Update the state vector


def numerical_derivative(x: np.ndarray, f: np.ndarray) -> np.ndarray:
    """
    Computes the numerical derivative of a function given by arrays of x and f values.

    Parameters:
    - x: np.ndarray
        An array of x values (independent variable).
    - f: np.ndarray
        An array of f values (dependent variable).

    Returns:
    - np.ndarray
        An array of the numerical derivative df/dx.
    
    Raises:
    - ValueError: If the lengths of x and f are not the same.
    """
    if len(x) != len(f):
        raise ValueError("The length of x and f must be the same")
    
    df_dx = np.zeros_like(f)  # Initialize the derivative array with zeros
    
    # Central difference for the interior points
    df_dx[1:-1] = (f[2:] - f[:-2]) / (x[2:] - x[:-2])
    
    # Forward difference for the first point
    df_dx[0] = (f[1] - f[0]) / (x[1] - x[0])
    
    # Backward difference for the last point
    df_dx[-1] = (f[-1] - f[-2]) / (x[-1] - x[-2])
    
    return df_dx  # Return the computed derivative


def solve_ode_system(
    f_system: list,
    u0: np.ndarray,
    h: float,
    method: str,
    t_max: float,
    divergence_threshold: float = 1e6,
    stop_conditions: list = None,
    indefinite: bool = False
    ) -> tuple[np.ndarray, np.ndarray]:
    """
    General solver for a system of differential equations.
    
    Parameters:
    - f_system: list
        A list of functions defining the system of ODEs.
    - u0: np.ndarray
        Initial conditions as a list or numpy array.
    - h: float
        Step size for the integration.
    - method: str
        The integration method to use: "Euler", "Heun", or "RK4".
    - t_max: float
        Maximum time for the simulation.
    - divergence_threshold: float, optional
        Threshold for divergence detection (default is 1e6).
    - stop_conditions: list of functions, optional
        Each function takes the current state as input and returns a boolean indicating if the simulation should stop.
    - indefinite: bool, optional
        If True, the simulation will run indefinitely until a stop condition is met (default is False).
    
    Returns:
    - sol: np.ndarray
        A numpy array with the solution for each variable over time.
    - t: np.ndarray
        A numpy array with the time points.
    
    Raises:
    - RuntimeError: If there is an error during computation.
    """
    # Dictionary to map method names to corresponding functions
    schemes = {
        "Euler": TempSchemes.Euler,
        "Heun": TempSchemes.Heun,
        "RK4": TempSchemes.RK4
    }
    
    if method not in schemes:
        messagebox.showinfo("Error", "Method should be 'Euler', 'Heun', or 'RK4'")
        return
    
    try:
        # Determine the initial number of steps based on t_max
        num_steps = int(t_max / h) + 1 if t_max else 1000  # Allocate space for results
        sol = np.zeros((num_steps, len(u0)))  # Solution array
        sol[0] = u0  # Set initial conditions

        t = np.zeros(num_steps)  # Time array
        
        i = 1  # Current step index
        while True:
            if not indefinite and i >= num_steps:
                break  # Stop if not indefinite and reached maximum steps
            
            if indefinite and i >= num_steps:
                # Expand arrays if running indefinitely
                sol = np.vstack([sol, np.zeros((1000, len(u0)))])
                t = np.hstack([t, np.zeros(1000)])
                num_steps += 1000  # Increase the number of steps allocated

            sol[i] = schemes[method](f_system, sol[i-1], h)  # Calculate the next step
            t[i] = t[i-1] + h  # Update time
            
            # Check for divergence
            if np.any(np.abs(sol[i] - sol[i-1]) > divergence_threshold):
                messagebox.showinfo("Divergence stop", "Simulation stopped due to divergence.")
                break
            
            # Check for custom stop conditions
            if stop_conditions:
                if any(condition(sol[i]) for condition in stop_conditions):
                    messagebox.showinfo("Conditional stop", "Simulation stopped due to custom stop condition.")
                    break
            
            i += 1  # Move to the next step
        
        # Trim the arrays to the actual size
        sol = sol[:i]
        t = t[:i]
    except (Exception, RuntimeError) as e:
        messagebox.showinfo("Error", f"Calculation error:\n{traceback.format_exc()}")
        return 
    
    return sol, t  # Return the solution and time arrays


def getSerialValues(line: str) -> Optional[Tuple[float, float, float]]:
    """
    Extracts time, force, and temperature values from a text line 
    in the format "t(s): <value>\t F(kg): <value>\t T(K): <value>".

    Args:
    - line (str): A string containing the values.

    Returns:
    - tuple: A tuple containing the time, force, and temperature as floats.
             Returns None if the values are not found in the expected format.
    """
    # Regular expression to capture the three specific values in the correct format
    match = re.match(r"t\(s\):\s*([-+]?\d*\.\d+|\d+)\s*F\(kg\):\s*([-+]?\d*\.\d+|\d+)\s*T\(K\):\s*([-+]?\d*\.\d+|\d+)", line)

    if match:  # If the line matches the expected format
        # Extract the three values and convert them to floats
        return tuple(map(float, match.groups()))
    else:
        # Return None if the expected format is not found
        return None


def importLibraries(lib: str) -> Dict[str, Type[Any]]:
    """
    Imports all classes from Python files in a specified directory that have a 'nozzle_type' attribute.
    
    Args:
    lib (str): The name of the directory containing the Python library files.

    Returns:
    Dict[str, Type[Any]]: A dictionary where the keys are nozzle types and the values are the corresponding class types.
    An empty dictionary is returned if the directory does not exist or if no valid classes are found.
    """
    # Get the current working directory
    root = os.getcwd()
    libraryDir = os.path.join(root, lib)  # Construct the full path to the library directory

    # Check if the directory exists
    if not os.path.isdir(libraryDir):
        print(f"La ruta {libraryDir} no existe.")
        return {}

    # Add the library directory to the system path if not already present
    if libraryDir not in sys.path:
        sys.path.append(libraryDir)

    nozzleClasses = {}  # Dictionary to store nozzle classes

    # Iterate over each file in the directory
    for fileName in os.listdir(libraryDir):
        # Process only Python files (excluding __init__.py)
        if fileName.endswith('.py') and fileName != '__init__.py':
            modName = fileName[:-3]  # Remove .py extension to get the module name
            try:
                modulo = importlib.import_module(modName)  # Import the module
                
                # Get all classes defined in the module
                classes = [
                    obj for name, obj in inspect.getmembers(modulo, inspect.isclass)
                    if obj.__module__ == modulo.__name__
                ]
                
                for classs in classes:
                    # Check if the class has the 'nozzle_type' attribute
                    if hasattr(classs, 'nozzle_type'):
                        nozzle_type = getattr(classs, 'nozzle_type')  # Get the nozzle type
                        nozzleClasses[nozzle_type] = classs  # Store the class in the dictionary
            except ImportError as e:
                print(f"No se pudo importar el módulo {modName}: {e}")

    return nozzleClasses  # Return the dictionary of nozzle classes


def get_circle_points(r: float, center: Tuple[float, float] = (0, 0), num_points: int = 100) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate points that define a circle.

    Args:
    r (float): The radius of the circle.
    center (Tuple[float, float], optional): The coordinates of the center of the circle. Defaults to (0, 0).
    num_points (int, optional): The number of points to generate around the circle. Defaults to 100.

    Returns:
    Tuple[np.ndarray, np.ndarray]: Two arrays containing the x and y coordinates of the points on the circle.
    """
    # Create a vector of angles from 0 to 2*pi
    t = np.linspace(0, 2 * np.pi, num_points)
    
    # Parametrize the circle and add the offset of the center
    x = center[0] + r * np.cos(t)  # x coordinates of the circle
    y = center[1] + r * np.sin(t)  # y coordinates of the circle
    
    return x, y  # Return the x and y coordinates




