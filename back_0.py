from imports import *
from functions import *


def adiabaticTemp_calc(reac, prod, t0, tGuess, hStep):
    if hStep <= 0:
        return messagebox.showinfo("Error", "Valor de paso de integración no válido.")
    

    reac_moles = [item[0] for item in reac]
    prod_moles = [item[0] for item in prod]

    reac_comps = [polynomialCp(item[1]) for item in reac]
    prod_comps = [polynomialCp(item[1]) for item in prod]

    hf0_reac = sum([n * r.Hf0 for n,r in zip(reac_moles,reac_comps)])
    hf0_prod = sum([n * p.Hf0 for n,p in zip(prod_moles,prod_comps)])

    molWeight_prod = sum([n * r.MolWeight for n,r in zip(prod_moles,prod_comps)]) / sum([n for n in prod_moles])

    def heat_balance(t):

        hCp_reac = sum([n * integration(r.cp, 298, t0, hStep) for n,r in zip(reac_moles,reac_comps)])
        hCp_prod = sum([n * integration(p.cp, 298, t,  hStep) for n,p in zip(prod_moles,prod_comps)])

        Q_Disp = hf0_reac + hCp_reac
        Q_Req  = hf0_prod + hCp_prod

        delta = (Q_Disp - Q_Req)
        return delta
    
    prodMol         = sum([n for n in prod_moles])
    tSol            = newtonRaph(heat_balance, tGuess, tol=hStep, max_iter=10000, h=hStep)
    molWeight_prod  = (sum([n * r.MolWeight for n,r in zip(prod_moles,prod_comps)]) / prodMol)*1e-3
    cp_Mass         =  (sum([n * r.cp(tSol) for n,r in zip(prod_moles,prod_comps)]) / prodMol) / molWeight_prod
    R_prod          = 8.31446261815324/molWeight_prod
    cv_Mass         = cp_Mass - R_prod
    gamma           = cp_Mass/cv_Mass
    cChar           = np.sqrt(gamma * R_prod * tSol) / (gamma * np.sqrt((2 / (gamma + 1))**((gamma + 1)/(gamma - 1))))
    return tSol, molWeight_prod, cp_Mass, cv_Mass, R_prod, gamma, cChar



class polynomialCp:
    def __init__(self, component):
        self.R = 8.31446261815324
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

        data = cursor.fetchone()
        conn.close()

        coefs = [(float(data[i]),  float(data[i+5])) for i in range(5)]
        temps = [(float(data[i]),  float(data[i+2])) for i in range(10,12)]
        props = list(map(float, data[14:]))

        self.a1_cold, self.a1_hot =  coefs[0]
        self.a2_cold, self.a2_hot =  coefs[1]
        self.a3_cold, self.a3_hot =  coefs[2]
        self.a4_cold, self.a4_hot =  coefs[3]
        self.a5_cold, self.a5_hot =  coefs[4]

        self.minColdTemp, self.maxColdTemp = temps[0]
        self.minHotTemp, self.maxHotTemp = temps[1]

        self.MolWeight, self.Hf0 = props

    def cp(self,T):
        if self.minColdTemp <= T < self.maxColdTemp:
            value = self.R*(
                self.a1_cold +
                self.a2_cold * T +
                self.a3_cold * T**2 +
                self.a4_cold * T**3 +
                self.a5_cold * T**4
            )
        elif self.minHotTemp <= T < self.maxHotTemp:
            value = self.R*(
                self.a1_hot +
                self.a2_hot * T +
                self.a3_hot * T**2 +
                self.a4_hot * T**3 +
                self.a5_hot * T**4
            )
        else:
            value = 0
        return value
    
