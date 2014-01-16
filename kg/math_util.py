#from itertools import imap
#from operator import add, sub
from math import sqrt #cos, sin, radians
#from tool_util import testVal

from operator import add, sub

import pyffi
from pyffi import formats
from pyffi.formats import nif
from pyffi.formats.nif import NifFormat

#from pyffi.utils import mathutils
#from pyffi.utils.mathutils import matvecMul, matMul, matscalarMul, vecNormalized, vecDotProduct, matCofactor, matDeterminant

class vector2(object):
    def __init__(self, vec):
        if type(vec) == vector2:
            coord_list = list(vec.coords)
            self.coords = coord_list
            self.length_sq = vec.length_sq
            self.length = vec.length
        else:
            self.coords = list(vec)
            self.length_sq = False
            self.length = False
        self.coord_dict = {'x': 0, 'y': 1}

    def __add__(self, other_vec):
        return vector2(map(add, self.coords, other_vec.coords))

    def __sub__(self, other_vec):
        return vector2(map(sub, self.coords, other_vec.coords))

    def __mul__(self, arg):
        return vector2([p * arg for p in self.coords])

    def __str__(self):
        return str(self.coords)

    def __getitem__(self, key):
        return self.coords[key]

    def __dict__(self, key, arg = False):
        if key in self.coord_dict:
            idx = self.coord_dict[key]
            if arg:
                self.coords[idx] = arg
                self.length_sq = False
                self.length = False
            return self.coords[idx]
    
    def as_tuple(self):
        return tuple(self.coords)

    def as_list(self):
        return list(self.coords)

    def zero(self):
        for idx in range(self.v_type):
            self.coords[idx] = 0
        return self

    def getLengthSq(self):
        if self.length_sq:
            return self.length_sq
        self.length_sq = sum([coord ** 2 for coord in self.coords])
        return self.length_sq

    def getLength(self):
        if self.length:
            return self.length
        self.length = sqrt(self.getLengthSq())
        return self.length

    def normalize(self):
        length = self.getLength()
        if length:
            mult = 1.0 / length
            self.setCoords([coord * mult for coord in self.coords])
            self.length_sq = 1.0
            self.length = 1.0
        return self
            
    def setCoords(self, coord_list):
        print(coord_list)
        for idx, coord in enumerate(coord_list):
            self.coords[idx] = coord
        self.x = coord_list[0]
        self.y = coord_list[1]
        self.length_sq = False
        self.length = False

def getVecLenSq(vec):
    return sum([coord ** 2 for coord in vec.as_list()])

def normalizeVector(vec):
    factor = getVecLenSq(vec)
    if not factor:
        s_3 = 1.0 / sqrt(3)
        return vector([s_3 for a in vec.as_list()])
    div = 1.0 / factor
    return vector([a * div for a in vec.as_list()])

def vector(coords):
    if len(coords) == 2:
        return vector2(coords)
    elif len(coords) == 3:
        return vector3(coords)
    elif len(coords) == 4:
        return vector4(coords)

def vector3(coords):
    vec = NifFormat.Vector3()
    vec.x = coords[0]
    vec.y = coords[1]
    vec.z = coords[2]
    return vec

def vector4(coords):
    vec = NifFormat.Vector4()
    vec.x = coords[0]
    vec.y = coords[1]
    vec.z = coords[2]
    vec.w = coords[3]
    return vec

def getAverageVector(vec_list, norm = False):
    """

    Take a list of vectors
    Return the mean average vector
    
    Keywords Accepted:
    norm: instead of dividing the resulting vector sum by
    the number of vectors, this is a multiplier that is applied
    to the resulting vector sum.

    """

    if not vec_list:
        return vector3((0, 0, 0))

    loc_list = [vec.as_tuple() for vec in vec_list]    

    vec_length = len(loc_list[0])
        
    if norm:
        mult = float(norm)
    else:
        this_length = len(loc_list)
        mult = 1.0 / float(this_length)
        
    return vector([sum([this_loc[x] for this_loc in loc_list]) * mult for x in range(vec_length)])

def isLocInBound(this_loc, max_coord, min_coord, true_val = True, false_val = False):
    """

    Determine whether this_loc lies between a bounding box with 
    max_coord and min_coord as the max and min corners
    
    Accepts three vectors: this_loc, max_coord, min_coord

    returns True or the true_val argument if this_loc lies within the box
    returns False or the false_val argument if this_loc lies outside the box
 
    """

    for idx, coord in enumerate(this_loc.as_list()):
        if coord > max_coord[idx] or coord < min_coord[idx]:
            return false_val
    return true_val


    
def matrix3x3(coords = False):
    if not coords:
        mat = NifFormat.Matrix33()
        mat.set_identity()
        return mat
    mat = NifFormat.Matrix33()
    mat.m_11 = coords[0][0]
    mat.m_12 = coords[0][1]
    mat.m_13 = coords[0][2]
    mat.m_21 = coords[1][0]
    mat.m_22 = coords[1][1]
    mat.m_23 = coords[1][2]
    mat.m_31 = coords[2][0]
    mat.m_32 = coords[2][1]
    mat.m_33 = coords[2][2]
    return mat

def matrix4x4(coords = False):
    if not coords:
        mat = NifFormat.Matrix44()
        mat.set_identity()
        return mat
    mat = NifFormat.Matrix44()
    mat.m_11 = coords[0][0]
    mat.m_12 = coords[0][1]
    mat.m_13 = coords[0][2]
    mat.m_14 = coords[0][3]
    mat.m_21 = coords[1][0]
    mat.m_22 = coords[1][1]
    mat.m_23 = coords[1][2]
    mat.m_24 = coords[1][3]
    mat.m_31 = coords[2][0]
    mat.m_32 = coords[2][1]
    mat.m_33 = coords[2][2]
    mat.m_34 = coords[2][3]
    mat.m_41 = coords[3][0]
    mat.m_42 = coords[3][1]
    mat.m_43 = coords[3][2]
    mat.m_44 = coords[3][3]
    return mat


def calcMinMaxVector(loc_list, form = 'list', world_loc = False):
    
    """
    
    Find the maximum and minimum composite vectors along the X, Y, and Z axes

    Accepts a list of vert objects, list of vectors, or a vertex dictionary
    keywords accepted:
    form = 'vert', 'list', 'dict'
    world_loc = True, False
 
    returns a list of min and max vectors in the follwoing format

    [min_vector, max_vector]

    """

    if form == 'vert':
        loc_list = getLocListFromVertList(loc_list, world_loc = world_loc)
    elif form == 'dict':
        loc_list = getLocListFromDictionary(loc_list, world_loc = world_loc)

    axes = len(loc_list[0])

    return [vector([fxn([vert[axis] for vert in loc_list]) for axis in range(axes)]) for fxn in [min, max]]

def getLocListFromVertList(vert_list, world_loc = False):
    """
    Accepts a list of vert objects

    keywords accepted:
    world_loc = True, False

    returns a list of locations from object.getLoc in the following format:

    [loc1, loc2, ...]
    
    """
    return [vert.getLoc(world_loc = world_loc) for vert in vert_list]

def getLocListFromDictionary(vert_dic, world_loc = False):
    """
    Accepts a dictionary of with key, value pairs of vertex index, vertex object

    keywords accepted:
    world_loc = True, False

    returns a list of locations from object.getLoc in the following format:

    [loc1, loc2, ...]
    
    """

    return [vert.getLoc(world_loc = world_loc) for vert in vert_dic.values()]

def getMinMaxCoordList(loc_list, form = 'list', world_loc = False):
    """
    
    Accepts a list of vert objects
    keywords accepted:
    form = 'vert', 'list', 'dict'
    world_loc = True, False
 
    returns a list of min and max coordinates in the following format

    [[min_x, max_x][min_y, max_y][min_z, max_z]]

    """
    #if form == 'vert':
    #    loc_list = getLocListFromVertList(loc_list, world_loc = world_loc)
    #elif form == 'dict':
    #    loc_list = getLocListFromDictionary(loc_list, world_loc = world_loc)

    return [sorted([this_vec[idx] for this_vec in calcMinMaxVector(loc_list, form = form, world_loc = world_loc)])for idx in range(3)]

