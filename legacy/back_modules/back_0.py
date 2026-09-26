from imports import *
from functions import *


class PolynomialCp:
    def __init__(self, component: str):
        """
        Initializes the PolynomialCp object for a given chemical component.

        Args:
        component (str): The name of the chemical component to retrieve properties for.
        """
        self.R: float = 8.31446261815324  # Universal gas constant in J/(mol*K)
        
        # Connect to the SQLite database and retrieve thermodynamic properties
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute(''' 
            SELECT  a1_cold, a2_cold, a3_cold, a4_cold, a5_cold,
                    a1_hot, a2_hot, a3_hot, a4_hot, a5_hot,
                    minColdTemp, maxColdTemp, minHotTemp, maxHotTemp,
                    MolWeight, Hf0
            FROM termoquimica
            WHERE Component = ? 
        ''', (component,))

        data: Optional[Tuple] = cursor.fetchone()  # Retrieve data as a tuple
        conn.close()

        if data is None:
            raise ValueError(f"No data found for component: {component}")

        # Extract coefficients and temperature limits from the data
        coefs: List[Tuple[float, float]] = [(float(data[i]), float(data[i + 5])) for i in range(5)]
        temps: List[Tuple[float, float]] = [(float(data[i]), float(data[i + 2])) for i in range(10, 12)]
        props: List[float] = list(map(float, data[14:]))

        # Assign coefficients and properties to instance variables
        self.a1_cold, self.a1_hot = coefs[0]
        self.a2_cold, self.a2_hot = coefs[1]
        self.a3_cold, self.a3_hot = coefs[2]
        self.a4_cold, self.a4_hot = coefs[3]
        self.a5_cold, self.a5_hot = coefs[4]

        self.minColdTemp, self.maxColdTemp = temps[0]
        self.minHotTemp, self.maxHotTemp = temps[1]

        self.MolWeight, self.Hf0 = props

    def cp(self, T: float) -> float:
        """
        Calculates the specific heat capacity at constant pressure (cp) for the component at temperature T.

        Args:
        T (float): The temperature at which to calculate cp.

        Returns:
        float: The specific heat capacity at temperature T in J/(mol*K). Returns 0 if T is outside the valid range.
        """
        if self.minColdTemp <= T < self.maxColdTemp:
            value = self.R * (
                self.a1_cold +
                self.a2_cold * T +
                self.a3_cold * T**2 +
                self.a4_cold * T**3 +
                self.a5_cold * T**4
            )
        elif self.minHotTemp <= T < self.maxHotTemp:
            value = self.R * (
                self.a1_hot +
                self.a2_hot * T +
                self.a3_hot * T**2 +
                self.a4_hot * T**3 +
                self.a5_hot * T**4
            )
        else:
            value = 0  # Return 0 if temperature is outside the valid range

        return value
    
    
def adiabaticTemp_calc(reac: list[tuple[float, Any]], prod: list[tuple[float, Any]], t0: float, tGuess: float, hStep: float):
    """
    Calculate adiabatic temperature for a given reaction.

    Parameters:
    - reac (list[tuple[float, Any]]): List of tuples containing reactant moles and their heat capacities.
    - prod (list[tuple[float, Any]]): List of tuples containing product moles and their heat capacities.
    - t0 (float): Initial temperature (K).
    - tGuess (float): Initial guess for the adiabatic temperature (K).
    - hStep (float): Integration step size.

    Returns:
    - tSol (float): Adiabatic flame temperature (K).
    - molWeight_prod (float): Molecular weight of products (kg/mol).
    - cp_Mass (float): Specific heat capacity of products (J/kg·K).
    - cv_Mass (float): Specific heat capacity at constant volume (J/kg·K).
    - R_prod (float): Gas constant of products (J/(mol·K)).
    - gamma (float): Ratio of specific heats (dimensionless).
    - cChar (float): Characteristic speed of sound (m/s).
    """

    # Check if the integration step size is valid
    if hStep <= 0:
        messagebox.showinfo("Error", "Invalid integration step value.")
        return

    # Extract moles of reactants and products from input lists
    reac_moles = [item[0] for item in reac]
    prod_moles = [item[0] for item in prod]
    # Create PolynomialCp objects for reactants and products
    reac_comps = [PolynomialCp(item[1]) for item in reac]
    prod_comps = [PolynomialCp(item[1]) for item in prod]

    # Calculate the initial enthalpy of formation for reactants and products
    hf0_reac = sum([n * r.Hf0 for n, r in zip(reac_moles, reac_comps)])
    hf0_prod = sum([n * p.Hf0 for n, p in zip(prod_moles, prod_comps)])

    # Calculate molecular weight of products
    molWeight_prod = sum([n * r.MolWeight for n, r in zip(prod_moles, prod_comps)]) / sum(prod_moles)

    def heat_balance(t: float) -> float:
        """
        Calculate heat balance equation for given temperature t.

        Parameters:
        - t (float): Temperature (K).

        Returns:
        - delta (float): Heat balance difference.
        """
        # Calculate enthalpy contributions from reactants
        hCp_reac = sum([n * integration(r.cp, 298, t0, hStep) for n, r in zip(reac_moles, reac_comps)])
        # Calculate enthalpy contributions from products
        hCp_prod = sum([n * integration(p.cp, 298, t, hStep) for n, p in zip(prod_moles, prod_comps)])

        # Calculate the heat contributions
        Q_Disp = hf0_reac + hCp_reac
        Q_Req  = hf0_prod + hCp_prod

        # Calculate the difference in heat
        delta = (Q_Disp - Q_Req)
        return delta
    
    # Calculate total moles of products
    prodMol = sum([n for n in prod_moles])

    # Solve for adiabatic temperature using the Newton-Raphson method
    tSol = newtonRaph(heat_balance, tGuess, tol=hStep, max_iter=10000, h=hStep)

    # Calculate additional properties based on the calculated temperature
    molWeight_prod = (sum([n * r.MolWeight for n, r in zip(prod_moles, prod_comps)]) / prodMol) * 1e-3
    cp_Mass = (sum([n * r.cp(tSol) for n, r in zip(prod_moles, prod_comps)]) / prodMol) / molWeight_prod

    # Universal gas constant adjusted for molecular weight
    R_prod = 8.31446261815324 / molWeight_prod  

    # Calculate specific heat at constant volume
    cv_Mass = cp_Mass - R_prod  

    # Calculate ratio of specific heats
    gamma = cp_Mass / cv_Mass  

    # Calculate characteristic speed of sound
    cChar = np.sqrt(gamma * R_prod * tSol) / (gamma * np.sqrt((2 / (gamma + 1))**((gamma + 1) / (gamma - 1))))  

    return tSol, molWeight_prod, cp_Mass, cv_Mass, R_prod, gamma, cChar

    
