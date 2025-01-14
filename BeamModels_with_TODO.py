# example Beam_models
# ----------------------------------------------------------------
# PURPOSE
#  Starting point for a couple of beam models
#

import math
import numpy as np
import matplotlib.pyplot as plt
import CorotBeam_with_TODO as CorotBeam
import matplotlib.animation as anm
from copy import deepcopy
import meshio

# ----- Topology -------------------------------------------------

# This is a base class defining common functionality
class BeamModel:

    def __init__(self):
        self.inc_load = None
        self.bc = None        # List of fixed dofs, 1 based
        self.num_nodes = None
        self.coords = None    # Nodal coordinates, array (num_nodes x 2)
        self.Edofs = None     # Element dofs, 1 based    (num_elements x 6)
        self.Enods = None     # Element nodes, 1 based   (num_elements x 2)
        self.ep = None        # Element properties [E, A, I], E - Young's modulus, A - Cross section area, I - Moment of inertia
        self.num_elements = None
        self.num_dofs = None

        # Plotting related data
        self.plotDof = None   # Plotting dof for load displacment plot, 1 based
        self.plotScaleFactor = 1.0
        self.load_history = []
        self.disp_history = []

    def get_K_sys(self, disp_sys):
        # Build system stiffness matrix for the structure
        K_sys = np.zeros((self.num_dofs,self.num_dofs))

        for iel in range(self.num_elements):
            inod1 = self.Enods[iel,0]-1
            inod2 = self.Enods[iel,1]-1
            ex1 = self.coords[inod1,0]
            ex2 = self.coords[inod2,0]
            ex = np.array([ex1,ex2])
            ey = np.array([self.coords[inod1,1],self.coords[inod2,1]])
            Ke = CorotBeam.beam2e(ex, ey, self.ep) #TODO use updated routine here
            Edofs = self.Edofs[iel] - 1
            K_sys[np.ix_(Edofs,Edofs)] += Ke

        # Set boundary conditions
        for idof in range(len(self.bc)):
            idx = self.bc[idof] - 1
            K_sys[idx,:]   = 0.0
            K_sys[:,idx]   = 0.0
            K_sys[idx,idx] = 1.0

        return K_sys

    def get_num_dofs(self):
        num_dofs = self.num_nodes * 3
        return num_dofs

    def get_internal_forces(self, disp_sys):
        # Build system stiffness matrix for the structure
        f_int_sys = np.zeros(self.num_dofs)

        for iel in range(self.num_elements):
            inod1 = self.Enods[iel,0]-1
            inod2 = self.Enods[iel,1]-1
            ex1 = self.coords[inod1,0]
            ex2 = self.coords[inod2,0]
            ex = np.array([ex1,ex2])
            ey = np.array([self.coords[inod1,1],self.coords[inod2,1]])
            Ke = CorotBeam.beam2e(ex, ey, self.ep)   #TODO something better here
            Edofs = self.Edofs[iel] - 1
            disp_e = disp_sys[np.ix_(Edofs)] # ix_ picks elements with indexes in Edofs
            f_int_e = Ke * disp_e   #TODO something better here
            f_int_sys[np.ix_(Edofs)] += f_int_e

        return f_int_sys

    def get_incremental_load(self,loadFactor):
        return self.inc_load

    def get_external_load(self,loadFactor):
        return (self.inc_load * loadFactor)

    def get_residual(self,loadFactor,disp_sys):
        f_int = self.get_internal_forces(disp_sys)
        f_res = self.get_external_load(loadFactor) + self.get_internal_forces(disp_sys)
        return f_res

    def append_solution(self, loadFactor, disp_sys):
        self.load_history.append(loadFactor)
        self.disp_history.append(deepcopy(disp_sys))

    def plotDispState(self, step, limits=None, scaleFactor=1 ):
        # DOF: DOF number of displacement to be plotted
        # Scale: scale factor for displacement
        plt.close('all')  # Close all currently open figures
        # Getting deformations from all nodes:
        # deformations = self.disp_history[:,DOF]
        num_steps = len(self.load_history)
        num_nodes = self.num_nodes

        # Starting subplot:
        fig, (ax, ax_shape) = plt.subplots(nrows=1, ncols=2, figsize=(20, 10))

        # Setting up force-displacement curve:
        plottedDeformations = np.zeros(num_steps)
        for i in range(num_steps):
            plottedDeformations[i] = self.disp_history[i][self.plotDof-1]
        plottedDeformations -= plottedDeformations[0]
        plottedDeformations *= self.plotScaleFactor

        ax.plot(plottedDeformations, self.load_history, label="Node")
        ax.plot([plottedDeformations[step]], [self.load_history[step]], '.', color='red', markersize=20)
        ax.legend(loc='best', fontsize=12)
        ax.set_xlabel('Displacement', fontsize=12)
        ax.set_ylabel('Applied force', fontsize=12)
        ax.set_title('Force-displacement')

        # Animating:
        x = np.zeros(num_nodes)
        y = np.zeros(num_nodes)
        if step >= num_steps:
            step = num_steps -1

        for i in range(num_nodes):
            x[i] = self.disp_history[step][0 + i * 3] + self.coords[i, 0]
            y[i] = self.disp_history[step][1 + i * 3] + self.coords[i, 1]
        line, = ax_shape.plot(x, y)
        if limits is None:
            ax_shape.axis('equal')
        else:
            ax_shape.set_xlim(limits[0], limits[1])
            ax_shape.set_ylim(limits[2], limits[3])

        ax.plot(plottedDeformations,self.load_history)
        ax_shape.plot(x,y)

        plt.show(block=True)


    def vtu_print_state(self, step, limits=None, scaleFactor=1 ):
        # Write geomtry output to Paraview as a .vtu file
        points = []
        dispArr = []
        for ip in range(len(self.coords)):
            points.append([self.coords[ip][0], self.coords[ip][1], 0])
            dispArr.append([self.disp_history[step][0 + ip*3], self.disp_history[step][1 + ip*3], 0])

        cells = []
        for ie in range(len(self.Enods)):
            numElementNodes = len(self.Enods[ie])
            if numElementNodes == 2:
                cells.append(("line", [[self.Enods[ie][0]-1,self.Enods[ie][1]-1]]))

        point_data = {}
        point_data["displacement"] = dispArr

        mesh = meshio.Mesh(points, cells, point_data=point_data)
        #mesh = meshio.Mesh(points, cells)
        fileName = 'Results/State_{}.vtu'.format(str(step).zfill(4))
        mesh.write(fileName)
# This is an actual model
class SimplySupportedBeamModel(BeamModel):

    def __init__(self, num_nodes):
        BeamModel.__init__(self)

        self.num_nodes = num_nodes
        self.num_elements = num_nodes - 1
        self.num_dofs = self.num_nodes * 3
        self.E = 2.1e11
        self.A = 45.3e-4
        self.I = 2510e-8
        self.ep = np.array([self.E, self.A, self.I])
        self.L_total = 9.0

        L_el = self.L_total / self.num_elements

        self.coords = np.zeros((self.num_nodes,2)) # Coordinates for all the nodes
        self.dispState = np.zeros(self.num_nodes*3)
        self.Ndofs  = np.zeros((self.num_nodes,3)) # Dofs for all the nodes

        for i in range(self.num_nodes):
            self.coords[i,0] = i * L_el
            self.Ndofs[i,:] = np.array([1,2,3],dtype=int) + i*3

        self.Edofs = np.zeros((self.num_elements,6),dtype=int) # Element dofs for all the elements
        self.Enods = np.zeros((self.num_elements,2),dtype=int) # Element nodes for all the elements
        for i in range(self.num_elements):
            self.Edofs[i,:] = np.array([1,2,3,4,5,6],dtype=int) + 3*i
            self.Enods[i,:] = np.array([1,2],dtype=int) + i

        # Fix x and y at first node and y at last node
        self.bc = np.array([1,2,(self.num_nodes*3 -1)],dtype=int)

        # The external incremental load (linear scaling with lambda)
        mid_node      = (self.num_nodes +1) // 2
        mid_y_dof_idx = (mid_node-1) * 3 + 1
        self.inc_load = np.zeros(self.num_dofs)
        self.inc_load[mid_y_dof_idx] = 500.0e+4
        self.plotDof = mid_y_dof_idx + 1

# This is an actual model class
class CantileverWithEndMoment(BeamModel):

    def __init__(self, num_nodes):
        BeamModel.__init__(self)

        self.num_nodes = num_nodes
        self.num_elements = num_nodes - 1
        self.num_dofs = self.num_nodes * 3
        self.E = 2.1e11
        self.A = 45.3e-4
        self.I = 2510e-8
        self.ep = np.array([self.E, self.A, self.I])
        self.L_total = 9.0

        MomentFullCircle = 2.0 * math.pi * self.E * self.I / self.L_total

        L_el = self.L_total / self.num_elements

        self.coords = np.zeros((self.num_nodes,2))   # Coordinates for all the nodes
        self.dispState = np.zeros(self.num_nodes*3)  # Current displacement state for all dofs
        self.Ndofs  = np.zeros((self.num_nodes,3))   # Dofs for all the nodes

        for i in range(self.num_nodes):
            self.coords[i,0] = i * L_el              # Setting the x-coordinat value
            self.Ndofs[i,:] = np.array([1,2,3],dtype=int) + i*3

        self.Edofs = np.zeros((self.num_elements,6),dtype=int) # Element dofs for all the elements
        self.Enods = np.zeros((self.num_elements,2),dtype=int) # Element nodes for all the elements
        for i in range(self.num_elements):
            self.Edofs[i,:] = np.array([1,2,3,4,5,6],dtype=int) + 3*i
            self.Enods[i,:] = np.array([1,2],dtype=int) + i

        # Fix x, y and rotation at first node
        self.bc = np.array([1,2,3],dtype=int)

        # The external incremental load (linear scaling with lambda)
        self.inc_load = np.zeros(self.num_dofs)
        #self.inc_load[-1] = 1.0e6
        self.inc_load[-1] = MomentFullCircle
        self.plotDof = self.num_dofs - 1 # Setting which dof for the Load-disp curve: y disp of last node






