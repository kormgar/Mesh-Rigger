import kg

def latticeToDictionary(this_lattice):
    #a_lattice = Lattice.Get(this_lattice.name)
    this_dict = dict()
    #this_dict['name'] = a_lattice.getName()
    #this_dict['keyTypes'] = a_lattice.getKeyTypes() 
    #this_dict['partitions'] = a_lattice.getPartitions() 
    #this_dict['mode'] = a_lattice.getMode() 
    #this_dict['nodes'] = dict([(this_idx, a_lattice.getPoint(this_idx)) for this_idx in range(a_lattice.latSize)])
    this_dict['matrix'] = list(list(i) for i in this_lattice.getMatrix('worldspace'))
    this_dict['size'] = this_lattice.getSize('worldspace')
    this_dict['location'] = this_lattice.getLocation('worldspace')

    return this_dict

class latticeType(object):

    '''
    LatticeType objects store data and calculations related to latice modifiers
    '''

    def __init__(self, size, x_part, y_part, z_part, location, node_dict = {}):
        self.x, self.y, self.z = size
        
        return
                 
# class nodeType(object):
#     def __init__(self, lattice, loc, d_vec = kg.math_util.vector([0,0,0])):
#         self.lattice = lattice
#         self.loc = loc
#         self.x, self.y, self.z = self.loc
#         self.d_vec = d_vec
        
        