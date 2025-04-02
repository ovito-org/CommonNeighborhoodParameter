#### Common Neighborhood Parameter ####
# This modifier computes the common neighborhood parameter (CNP) for each particle in a simulation. 
# 
# The CNP is a measure used for the structural characterization of atomic configurations.
# See http://doi.org/10.1016/j.cpc.2007.05.018 for details.

from ovito.pipeline import ModifierInterface
from ovito.data import CutoffNeighborFinder, DataCollection
from traits.api import Float
import numpy as np

class CommonNeighborhoodParameterModifier(ModifierInterface):

    cutoff = Float(3.2, label="Cutoff radius")

    def modify(self, data: DataCollection, **kwargs):
        if self.cutoff <= 0.0:
            raise ValueError("Cutoff must be positive.")
        n_particles = data.particles.count

        # Build neighbor dictionaries: list of Python dicts, one for each particle, where each dict contains the neighbors of the particle.
        # The keys are the global indices of the neighbors, and the values are the vectors from the particle to its neighbors.
        yield "Building neighbor list dictionary"
        finder = CutoffNeighborFinder(self.cutoff, data)
        neighbor_dicts = [
            { neigh.index : neigh.delta for neigh in finder.find(i) }
                for i in range(n_particles)
        ]
        # Precompute neighbor sets, which allows for faster intersection operations to determine common neighbors.
        neighbor_sets = [set(d.keys()) for d in neighbor_dicts]

        # CNP calculation.
        yield "Calculating common neighborhood parameter"
        cnp_values = np.zeros(n_particles)
        for i in range(n_particles):
            yield i / n_particles # Progress reporting
            neighbors_i = neighbor_dicts[i]
            if len(neighbors_i) == 0:
                continue
            total_sum = 0.0
            for j in neighbors_i:
                neighbors_j = neighbor_dicts[j]
                common_neighbors = neighbor_sets[i] & neighbor_sets[j]
                sum_k = np.zeros(3)
                for k in common_neighbors:
                    R_ik = neighbors_i[k]
                    R_jk = neighbors_j[k]
                    sum_k += (R_ik + R_jk)
                total_sum += sum_k[0]**2 + sum_k[1]**2 + sum_k[2]**2
            cnp_values[i] = total_sum / len(neighbors_i)

        # Output CNP values as a new particle property.
        data.particles_.create_property("CNP", data=cnp_values)