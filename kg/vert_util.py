'''\
__author__ = "Kormgar"
__url__ = ["kormgar@yahoo.com"]
__version__= '1.0'

the vert_util module is a collection of utilities intended to be used by other scripts
the vertType class is a wrapper for Blender obj.mesh.verts objects, used to aid vertex search, categorization, and connectivity scripts
'''
#from pyffi.formats.nif.NifFormat import Matrix33, Vector3
from kg.math_util import vector, getAverageVector, normalizeVector

class vertex(object):
    '''
    This is a container that stores state information related to an individual vertex
    this includes the location, the worldspace location, group flags (similar to vertex groups)
    the mirror of this vertex (equivalent vertex on the other side of the x-axis)
    '''

    def __init__(
        self,\
        idx,\
        vert = False,\
        mesh = False,\
        init = True
    ):
        self.idx = idx
        if init:
            self.mesh = mesh
            self.data = mesh.niData
            self.vert = vert
            self.loc = vector([vert.x, vert.y, vert.z])
            #print(self.loc)
            self.w_loc = False
            try: self.normal = self.data.normals[idx]
            except: self.normal = False
        self.uv = False
        self.influence_list = []
        self.travel_mod = False
        self.searchModifiers = []
        self.search_mod = False
        self.doubles = None
        self.edges = set()
        self.NMV = None
        self.weight_dict = {}
        self.side = False
        self.BDPartition = []
        self.exact_match = False
        self.match_results = {}
        #self.uv = self.data.uv_sets[idx]

    def addBDPartition(self, part_idx):
        self.BDPartition.append(part_idx)

    def updateBUDict(self, weight_dict):
        #print('before', self.weight_dict)
        bu_dict = self.mesh.bone_update_dict
        #print('bu_dict', bu_dict)
        v_idx = self.idx
        for bone_key, weight in weight_dict.items():
            if bone_key in bu_dict:
                bu_dict[bone_key]['verts'][v_idx] = weight
                self.addWeight(bone_key, weight)
        #print('after', self.weight_dict)

        
    def addWeight(self, bone_key, weight):
        self.weight_dict[bone_key] = weight
       
    def getWeight(self, bone = None):
        if not bone:
            return self.weight_dict
        return self.weight_dict.get(bone, False)
    
    def delWeight(self, bone_list = []):
        if not bone_list:
            self.weight_dict = {}
            return
        for bone_ in bone_list:
            if bone_ in self.weight_dict:
                del self.weight_dict[bone_]
        
    def getLoc(self, world_loc = True, search_loc = False, travel_mod = False, flip_x_axis = False):
        
        if world_loc and not self.w_loc:
            self.w_loc = self.loc * self.mesh.mat
            
        if world_loc:
            temp_loc = self.w_loc
        else:
            temp_loc = self.loc

        if search_loc:
            temp_loc = temp_loc + self.getSearchLoc(world_loc = world_loc)
        elif travel_mod:
            temp_loc = temp_loc +  self.getTravelMod()

        if flip_x_axis:
            temp_loc = vector(temp_loc.as_list())
            temp_loc.x = -1 * temp_loc.x

        return temp_loc

    def getTravelMod(self):
        if self.travel_mod:
            return self.travel_mod
        self.travel_mod = vector([0,0,0])
        return self.travel_mod
    
    def getSearchMod(self):
        return getAverageVector(self.searchModifiers)    
    
    def getSearchLoc(self, world_loc = True):
        if not self.search_mod:
            if self.searchModifiers:
                self.search_mod = getAverageVector(self.searchModifiers)
            else:
                return vector([0,0,0])
        if world_loc:
            return self.search_mod + self.getLoc(world_loc = True)
        return self.search_mod * self.mesh.mat_i + self.getLoc(world_loc = False)

    def setLoc(self, loc, world_loc = True):
        if world_loc:
            """
            convert world_loc coordinates to local space coordinates
            """
            loc = loc * self.mesh.mat_i
        temp_loc = loc.as_list()
        self.vert.x = temp_loc[0]
        self.vert.y = temp_loc[1]
        self.vert.z = temp_loc[2]
  
    def getNormal(self, world_loc = False):
        return self.normal
    
    def getUV(self):
        if self.uv:
            return self.uv
        self.mesh.initUV()
        return self.uv
    
    def setNormal(self, loc, world_loc = False, normalize = False):
        if self.normal:
            if world_loc:
                loc = loc #* self.mesh.mat_i
            if normalize:
                loc = normalizeVector(loc)
            temp_loc = loc.as_list()
            self.normal.x = temp_loc[0]
            self.normal.y = temp_loc[1]
            self.normal.z = temp_loc[2]
            self.nloc = [self.normal.x, self.normal.y, self.normal.z]
        
    def getDoubles(self):
        if self.doubles is None:
            self.mesh.initDoubles()
        return self.doubles
            
    def setDouble(self, vert_dict):
        self.doubles = vert_dict

    def addEdges(self, vert_list):
        self.edges.update(set(vert_list))
        
    def getEdges(self):
        return self.edges
            
    def setNMV(self, state = True):
        self.NMV = state
        return self
    
    def getNMV(self):
        return self.NMV
    
    def setInfluence(self, influence_list):
        self.influence_list.extend(influence_list)
        
    def getInfluence(self):
        return self.influence_list
    
    def getSide(self, this_test = False, lxor = False):
        if not self.side:
            self.groupVertex()
        if not this_test:
            return self.side
        if this_test == 'LEFT':
            side_flip = 'RIGHT'
        else:
            side_flip = 'LEFT'
        if this_test in self.side:
            return not lxor or side_flip not in self.side
        return False
    
    def groupVertex(self):
        '''
        Categorize vertices as either LEFT, RIGHT, or middle (LEFT and RIGHT)
        '''
        this_loc = self.getLoc()
        if not this_loc:
            self.side = set()
        if this_loc.x >= 0.01:
            self.side = set(['RIGHT'])
        elif this_loc.x <= -0.01:
            self.side = set(['LEFT'])
        else:
            self.side = set(['LEFT', 'RIGHT'])
            