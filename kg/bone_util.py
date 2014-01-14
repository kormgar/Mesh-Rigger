from re import compile, sub, findall, IGNORECASE
import kg
from pyffi.formats.nif import NifFormat
#import cPickle as pickle

#Compile any regular expressions that we will be using
prog_R = compile('(\\b)R(\\b)')
prog_RIGHT = compile('(\\b)RIGHT(\\b)')
prog_r = compile('(\\b)r(\\b)')
prog_L = compile('(\\b)L(\\b)')
prog_LEFT = compile('(\\b)LEFT(\\b)')
prog_l = compile('(\\b)l(\\b)')
prog_R_IC = compile('\\bR\\b', flags=IGNORECASE)
prog_L_IC = compile('\\bL\\b', flags=IGNORECASE)
prog_LR_End = compile('\\b[lr]$', flags=IGNORECASE)
prog_Splt = compile('\W')
prog_1 = compile('[0-9]+[. ][lr]$', flags=IGNORECASE)
prog_2 = compile('[0-9]+$')

def swapBoneSide(strng):
    '''
    Takes a string as input, Parses the side, and returns the corresponding opposite side
    Examples: 
        for string 'boneName.L' , script will return 'boneName.R'
        for string 'Bone r Name', script will return 'Bone l Name'
        for string 'Bone Name Red', script will return 'Bone Name Red'
    '''
    if findall(prog_R, strng):
        return sub(prog_R,'\\1L\\2', strng)
    elif findall(prog_r, strng):
        return sub(prog_r,'\\1l\\2', strng)
    elif findall(prog_L, strng):
        return sub(prog_L,'\\1R\\2', strng)
    elif findall(prog_l, strng):
        return sub(prog_l,'\\1r\\2', strng)
    else:
        return strng

def swapSide(strng):
    '''
    Takes a string as input, Parses the side, and returns the corresponding opposite side
    Examples: 
        for string 'boneName.L' , script will return 'boneName.R'
        for string 'Bone r Name', script will return 'Bone l Name'
        for string 'Bone Name Red', script will return 'Bone Name Red'
    '''
    if findall(prog_RIGHT, strng):
        return sub(prog_RIGHT,'\\1LEFT\\2', strng)
    elif findall(prog_LEFT, strng):
        return sub(prog_LEFT,'\\1RIGHT\\2', strng)
    else:
        return strng

def getBoneSide(strng):
    '''
    Takes a string as input, Parses the side, and returns either 'RIGHT', 'LEFT', or None
    Examples: 
        for string 'boneName.L' , script will return 'LEFT'
        for string 'Bone r Name', script will return 'RIGHT'
        for string 'Bone Name Red', script will return None
    '''
    if findall(prog_R_IC, strng):
        return 'RIGHT'
    elif findall(prog_L_IC, strng):
        return 'LEFT'
    else:
        return None

def getLeftRight(strng):
    '''
    Takes a string as input, returns the start and end index of the L or R part of the string
    '''
    b = prog_LR_End.search(strng)
    if b:
        return b.start(), b.end()
    else:
        return False, False

def parseTrailingNumbers(strng):
    '''Just a simple parsing function.  Takes a string as input, returns trailing integers and number of digits
    '''
    a, b, c = strng,(0,1),''

    res = prog_1.search(strng)

    if res:
        a = strng[0:res.start()]
        b = strng[res.start():res.end() - 2]
        c = strng[res.end() - 2:res.end()]
        return a, b, res.end() - res.start() - 2 , c

    res = prog_2.search(strng)
    if res:
        a = strng[0:res.start()]
        b = strng[res.start():res.end()]
        c = ''
        return a, b, res.end() - res.start() , c

    return a, b[0], b[1], c

    a = len(strng)
    d = 0
    for i in range(0, a):
        b = strng[-1 - i]
        c = findall(prog_2, b)
        if not c:
            idx = i - 1
            break
        else:
            d += int(c[0]) * 10 ** i 
    if idx >= 0:
        idx += 1

    return d, idx
    
def wrapBone(bone, skel_root = False):
    #print(bone.name)
    
    #print(list(child.name for child in bone.children))
    return {
    'is_skel_root': skel_root,\
    'bounding_box': extractBoundingBox(bone.bounding_box),\
    'children': list(child.name for child in bone.children if child),\
    'collision_object': bone.collision_object,\
    'controller': bone.controller,\
    'effects': list(bone.effects),\
    'extra_data': bone.extra_data,\
    'extra_data_list': list(bone.extra_data_list),\
    'flags': bone.flags,\
    'has_bounding_box': bone.has_bounding_box,\
    'has_old_extra_data': bone.has_old_extra_data,\
    'name': bone.name,\
    'num_children': bone.num_children,\
    'num_effects': bone.num_effects,\
    'num_extra_data_list': bone.num_extra_data_list,\
    'num_properties': bone.num_properties,\
    'old_extra_internal_id': bone.old_extra_internal_id,\
    'old_extra_prop_name': bone.old_extra_prop_name,\
    'old_extra_string': bone.old_extra_string,\
    'properties': list(bone.properties),\
    'rotation': bone.rotation.as_list(),\
    'scale': bone.scale,\
    'translation': bone.translation.as_list(),\
    'unknown_1': list(bone.unknown_1),\
    'unknown_2': bone.unknown_2,\
    'unknown_byte': bone.unknown_byte,\
    'unknown_short_1': bone.unknown_short_1,\
    'velocity': bone.velocity.as_list(),\
    }


def unWrapBone(bone_values):

    this_bone = NifFormat.NiNode()
    this_bone.collision_object = bone_values['collision_object']
    this_bone.controller = bone_values['controller']
    this_bone.extra_data = bone_values['extra_data']
    this_bone.flags = bone_values['flags']
    this_bone.has_bounding_box = bone_values['has_bounding_box']
    this_bone.has_old_extra_data = bone_values['has_old_extra_data']
    this_bone.name = bone_values['name']
    #this_bone.num_children = bone_values['num_children']
    this_bone.num_effects = bone_values['num_effects']
    this_bone.num_extra_data_list = bone_values['num_extra_data_list']
    this_bone.num_properties = bone_values['num_properties']
    this_bone.old_extra_internal_id = bone_values['old_extra_internal_id']
    this_bone.old_extra_prop_name = bone_values['old_extra_prop_name']
    this_bone.old_extra_string = bone_values['old_extra_string']
    this_bone.scale = bone_values['scale']
    this_bone.unknown_2 = bone_values['unknown_2']
    this_bone.unknown_byte = bone_values['unknown_byte']
    this_bone.unknown_short_1 = bone_values['unknown_short_1']
    this_bone.rotation = kg.math_util.matrix3x3(bone_values['rotation'])
    this_bone.translation = kg.math_util.vector(bone_values['translation'])
    this_bone.velocity = kg.math_util.vector(bone_values['velocity'])
    update_array(this_bone.properties, bone_values['properties'])
    update_array(this_bone.unknown_1, bone_values['unknown_1'])
    update_array(this_bone.extra_data_list, bone_values['extra_data_list'])
    update_array(this_bone.effects, bone_values['effects'])
    update_array(this_bone.properties, bone_values['properties'])
    b_box_data = bone_values['bounding_box']
    b_box = NifFormat.BoundingBox()
    b_box.radius = kg.math_util.vector(b_box_data['radius'])
    b_box.rotation = kg.math_util.matrix3x3(b_box_data['rotation'])
    b_box.translation = kg.math_util.vector(b_box_data['translation'])
    b_box.unknown_int = b_box_data['unknown_int']
    
    return this_bone

def extractTransform(data_set):
    return {
    'scale': data_set.scale,
    'rotation': data_set.rotation.as_list(),
    'translation': data_set.translation.as_list(),
    }

def extractBoundingBox(BoundingBox_):
    return {
        'radius': BoundingBox_.radius.as_list(),
        'rotation': BoundingBox_.rotation.as_list(),
        'translation': BoundingBox_.translation.as_list(),
        'unknown_int': BoundingBox_.unknown_int,
        }


def update_array(this_array, val_list):
    if not val_list:
        return
    #idx = this_array.get_size()
    for val in val_list:
        this_array.append(val)
    this_array.update_size()
    
    return