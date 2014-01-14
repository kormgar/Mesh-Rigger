from math import sqrt, ceil
from operator import itemgetter, add, sub
#import numpy
#length = numpy.linalg.norm
#from pyffi.utils.mathutils import vecDistance

from kg.tool_util import deepListPermutations
from kg.math_util import matrix3x3, getVecLenSq, vector, vector2
from kg.bone_util import swapSide, unWrapBone

from time import clock

global sphereKeyDict
global sphereValues
global sphereBloomValues
global circleValues
global circleKeyDict
global circleBloomValues

sphereKeyDict = {}
sphereValues = {}
sphereBloomValues = {}
circleValues = {}
circleKeyDict = {}
circleBloomValues = {}

identity_matrix = matrix3x3()

def NormalizeInfluence(influence_list):

    if not influence_list:
        return influence_list

    influence_sum = sum([influence for vert, influence in influence_list])

    if not influence_sum:
        norm_factor = 1.0 / float(len(influence_list))
        influence_list = [(vert, norm_factor) for vert, influence in list(influence_list)]

    else:
        norm_factor = 1.0 / float(influence_sum)
        influence_list = [(vert, influence * norm_factor) for vert, influence in list(influence_list)]

    return influence_list

def setTriSeams(ctx_vert, influence_list, settings = {}):
    #print('influence_list', influence_list)

    if settings.get('loc', True):
        ctx_vert.setLoc(combine_influences(influence_list, world_loc = False), world_loc = True)
    ctx_vert.setInfluence(NormalizeInfluence(influence_list))

def setSeams(ctx_vert, influence_list, settings = {}):
    #print('setting Seams')
    #if settings.get('Loc', True):
    if settings.get('loc', True):
        #print(combine_influences(influence_list))
        #print('loc')
        ctx_vert.setLoc(combine_influences(influence_list))
    if settings.get('norm', True):        
    #if settings.get('Normal', True):
        ctx_vert.setNormal(combine_influences(influence_list, Normal = True))
        #print(combine_influences(influence_list, Normal = True))
    if settings.get('bone', False):
        ctx_vert.updateBUDict(combine_influences(influence_list, BoneWeight = True))

    ctx_vert.setInfluence(NormalizeInfluence(influence_list))
    #fix_UV_Map = settings.get('UV Map', False)

def combine_influences(influence_list, world_loc = True, travel_mod = False, Normal = False, BoneWeight = False, loc_list = False):

    #global time1
    #global time2
    #global time3
    #global time4
    if type(influence_list[0][0]) == vector2:
        average_vector = vector([0,0])
    else:   
        average_vector = vector([0,0,0])
    
    if not influence_list:
        if BoneWeight:
            return {}
        return average_vector

    influence_list = NormalizeInfluence(list(influence_list))

#     if loc_list:
#         for loc, influence in influence_list:
#             average_vector = average_vector + (loc * influence)
#         return average_vector

    if Normal:
        #Combine the Normal vectors from the vertexes on the influence list
        for vert, influence in influence_list:
            average_vector = average_vector + (vert.getNormal(world_loc = world_loc) * influence)
        return average_vector

    if BoneWeight:

        #print 'BoneWeight True'

        #Combine the weights from the vertexes on the influence list
        #timeA = time()
        """
        Build the skeleton of the dictionary
        """
        weightDictionary = dict([(this_group, 0.0)
            for this_group in set(
            this_group for inf_vert, influence in influence_list
            for this_group in inf_vert.getWeight().keys())
        ])
        #time1 += timeA - time()
        #timeA = time()
        """
        Add the weight values to the dictionary
        """
        for inf_vert, influence in influence_list:
            for this_group, weight in inf_vert.getWeight().items():
                weightDictionary[this_group] += weight * influence
        #time2 += timeA - time()

        return weightDictionary

    for vert, influence in influence_list:
        average_vector = average_vector + (vert.getLoc(world_loc = world_loc, travel_mod = travel_mod) * influence)

    return average_vector

def setWeightDictionary(ctx_vert, influence_list, settings = {}):

    #Combine the weights from the vertexes on the influence list
    #timeA = time()
    setInfluences(ctx_vert, influence_list, settings = settings)
    ctx_vert.updateBUDict(combine_influences(influence_list, BoneWeight = True))

def setInfluences(ctx_vert, influence_list, settings = {}):
    """
    This function is intended to be called by the mainSearch function if 
    vertFunction = setInfluences is passed as the a keyword

    Converts an influence list to a property of the passed vert object
    that can later be accessed by the getInfluence vertType method
    """
    ctx_vert.setInfluence(NormalizeInfluence(influence_list))

def compareMatches(ctx_vert, influence_list, settings = {}):
    test_idx = ctx_vert.idx
    norm = ctx_vert.normal
    for v, influence in influence_list:
        if test_idx == v.idx:
            if not settings.get('normal'):
                ctx_vert.match_results = {'Loc Match' : True, 'Index Match' : True}
                ctx_vert.exact_match = True
            v_norm = v.normal
            if not norm and not v_norm:
                ctx_vert.match_results = {'Loc Match' : True, 'Index Match' : True, 'Normal Match': 'No Normals'}
                return
            elif not norm:
                ctx_vert.match_results = {'Loc Match' : True, 'Index Match' : True, 'Normal Match': 'Template Norm Missing'}
                return
            elif not v_norm:
                ctx_vert.match_results = {'Loc Match' : True, 'Index Match' : True, 'Normal Match': 'Target Norm Missing'}
                return
            norm_dist = sqrt(getVecLenSq(v.normal - norm))
            ctx_vert.match_results = {'Loc Match' : True, 'Normal Match': norm_dist}
            if norm_dist < .0000000000001:
                ctx_vert.exact_match = True
            return
    if not settings.get('normal'):
        ctx_vert.match_results = {'Loc Match' : True, 'Index Match' : False, 'Indices': [v.idx for v, influence in influence_list]}
        return
    norm_dist_list = []
    for v, influence in influence_list:
        v_norm = v.normal
        if not v_norm and not norm:
            norm_dist_list.append('No Normals')
        elif not norm:
            norm_dist_list.append('Template Norm Missing')
        elif not v_norm:
            norm_dist_list.append('Target Norm Missing')
        else:
            norm_dist_list.append(sqrt(getVecLenSq(v.normal - norm)))
            
    ctx_vert.match_results = {\
        'Loc Match' : True,\
        'Index Match' : False,\
        'Indices': [v.idx for v, influence in influence_list],\
        'normal_distances':  norm_dist_list}    

def mainSearch(\
    settings,\
    act_mesh,\
    ctx_mesh,\
    side = False,\
    search_weight = identity_matrix,\
    search_resolution = 1,\
    nmv = False,\
    vertFunction = setInfluences,\
    bb = False,\
    max_radius = False,\
    act_verts = False,\
    ctx_verts = False,\
    Distance = None,\
    OverrideDistance = None,\
    search_targets = None,\
    xAxisNoCross = None,\
    progress_msg = 'Processing Vertices',\
    complete_msg = '**Vertices searched in',\
    mirror_search = False,\
    inf_type = 'VERT',\
    res_alt = 1000,\
    tri = False,\
    world_loc = True\
):

    """
    This is the primary generic vertex/node search module

    Inputs:

    Settings: this should be a dictionary generated by the menu module
        that includes relevant search options. Additional dictionary 
        keys may be required depending on the called vert function.):
        'Cross X Axis' (Bool), Default: False
        'Vertex Search Targets' (int), Default: 1
        'Vertex Search Distance' (float), Default: 1.0
        'Override Distance' (bool), Default: False
        Note, if a particular value is not found in the settings dictionary
        the default value will be used.

    act_mesh: the meshType (or other object that accepts any keywords accepted
        by meshType.getVerts()) that will be searched.  Note: the objects
        returned by getVerts()can be any object that accepts any keywords
        accepted by vertType.getLoc()

    ctx_mesh: the meshType (or other object that accepts any keywords accepted
        by meshType.getVerts()) that will do the searching.  Note: the objects
        returned by getVerts()can be any object that accepts any keywords
        accepted by vertType.getLoc()

    Keyword Arguments:

    search_resolution (int): 1 / resolution gives the size of the boxes to be searched for vertex targets

    nmv (bool): Limits the search to non-manifold vertices only.  These are defined as vertices
        belonging to an edge that itself belongs to only a single face.

    side ('LEFT', 'RIGHT', False): If set to 'LEFT' or 'RIGHT' this defines
        the side of both the Active and the Context mesh that will be searched

    mirror_search ('LEFT, 'RIGHT', False): If set to 'LEFT or 'RIGHT', this
        causes the context mesh to search the opposite side of the active mesh

    vertFunction (function): the function that will be used to process the
        search results for an individual vertex (or node, etc)
        function must accept three arguments: vert, influence_list, settings = settings

    search_weight (Matrix): A matrix that should be used to transform the
        apparent loc for a given context mesh vertex when searching for
        nearest neighbors.  The net effect on the search results is analagous
        to applying the search weight matrix to the context mesh and then 
        running the search.

    """

    #print ('validating skin - mainsearch 1')
    #ctx_mesh.block._validate_skin()
    targets_found = 0
    #print ('*****Bone Setting***', settings.get('bone'))
    if settings.get('bone', False) and not tri:
        """
        Initialize the BU update dictionary
        """
        ctx_mesh.initBUDict(act_mesh.bone_dict, settings = settings)
        if settings.get('delete_rigging', False):
            for vert_ in ctx_mesh.getVerts().values():
                vert_.delWeight()            
        elif settings.get('delete', False):
            bu_list = list(ctx_mesh.bone_update_dict.keys())
            print('Bone Weight Override List', bu_list)
            for vert_ in ctx_mesh.getVerts().values():
                vert_.delWeight(bu_list)

    print('Main Search')
    #print 'selected vertices'
    #print settings.get('Selected Vertices', False)
    if not act_verts:
        act_vert_count = len(act_mesh.getVerts(nmv = nmv))
    else:
        act_vert_count = len(act_verts)
    #print(act_vert_count)

    if xAxisNoCross == None:
        xAxisNoCross = settings.get('Cross X Axis', False)
    if search_targets == None:
        search_targets = settings.get('Targets', 1)
    if Distance == None:
        Distance = settings.get('Distance', 1.0)
    if OverrideDistance == None:
        OverrideDistance = settings.get('override', False)

    print ('Distance', Distance)
    print ('search_targets', search_targets)

    if search_targets > act_vert_count:
        search_targets = act_vert_count

    if xAxisNoCross and not side or mirror_search:
        vert_count = len(ctx_mesh.getVerts(nmv = nmv))
        side = ['LEFT', 'RIGHT']
    else:
        vert_count = len(ctx_mesh.getVerts(side = side, nmv = nmv))
        side = [side]

    msg_index = int(vert_count / 8)

    if not vert_count:
        return 0

    int_dist_sq = int(ceil(pow(Distance * res_alt, 2)))
    if not tri:
        act_world_loc = world_loc
        ctx_world_loc = world_loc
    else:
        act_world_loc = False
        ctx_world_loc = True

    #DistanceSq = Distance

    for this_side in side:

        if mirror_search and mirror_search == this_side or mirror_search == True:
            flip_x_axis = True
            act_side = swapSide(this_side)
        else:
            flip_x_axis = False
            act_side = this_side

        if not act_verts:
            a_verts = act_mesh.getVerts(side = act_side, nmv = nmv)
            #print (a_verts)
            #print (act_mesh.verts)
        else:
            a_verts = act_verts

        print('Template Vertices:', len(a_verts))


        if not ctx_verts:
            c_verts = ctx_mesh.getVerts(side = this_side, nmv = nmv)
        else:
            c_verts = ctx_verts
            
        #search_resolution = 3
            
        #act_loc_dictionary, act_set_a, act_set_b, act_set_c = BuildVertexDictionary(\
        act_loc_dictionary = BuildVertexDictionary(\
            a_verts.values(),\
            search_weight = search_weight,\
            res = search_resolution,\
            #get_key_set = True,\
            res_alt = res_alt,\
            world_loc = act_world_loc\
        )
        #print(act_loc_dictionary)
        print('Target Mesh Vertices', len(c_verts))
        
        ctx_loc_dictionary = BuildVertexDictionary(\
            c_verts.values(),\
            search_weight = search_weight,\
            res = search_resolution,\
            useSearchMod = True,\
            flip_x_axis = flip_x_axis,\
            res_alt = res_alt,\
            world_loc = ctx_world_loc\
        )
        #print(ctx_loc_dictionary)
        #a_verts = act_mesh.getVerts(selected_vertices = settings.get('Selected Vertices', False), side = act_side, nmv = nmv).values()
        b = 0
        c = 0
        print('searching for Targets')
        target_count = 0
        temp_count = 0
        for a_val in ctx_loc_dictionary.values():
            for b_val in a_val.values():
                for ctx_vert_list in b_val.values():
                    a = clock()
                    act_targets = GetNearVert(\
                        ctx_vert_list[0].getLoc(world_loc = ctx_world_loc, search_loc = True, flip_x_axis = flip_x_axis),\
                        search_targets,\
                        act_loc_dictionary,\
                        Distance = Distance,\
                        #Distance = DistanceSq,\
                        OverrideDistance = OverrideDistance,\
                        res = search_resolution,\
#                         set_a = act_set_a,\
#                         set_b = act_set_b,\
#                         set_c = act_set_c,\
                        res_alt = res_alt,\
                        int_dist_sq = int_dist_sq
                        #bb = bb\
                        #max_radius = max_radius
                    )
                    b += clock() - a
                   
                    for ctx_vert in ctx_vert_list:
                        target_count += 1
                        temp_count += 1
                        a = clock()
                        ctx_loc = ctx_vert.getLoc(world_loc = ctx_world_loc, search_loc = True, flip_x_axis = flip_x_axis)

                        influence_list = getVertexInfluence(\
                            ctx_loc,\
                            act_targets,\
                            search_targets = search_targets,\
                            Distance = Distance,\
                            #Distance = DistanceSq,\
                            OverrideDistance = OverrideDistance,\
                            search_weight = search_weight,\
                            near_vert_weight = 3,\
                            far_vert_weight = 3,\
                            return_type = inf_type,\
                            int_dist_sq = int_dist_sq,\
                            res_alt = res_alt\
                        )
                        if not influence_list:
                            continue
                        influence_list = sorted(list(influence_list.items()), reverse = True, key = itemgetter(1))
                        c += clock() - a
                        vertFunction(ctx_vert, influence_list, settings = settings)
                        targets_found += 1
                        #print('Targets Found for vertex ' + str(ctx_vert.idx) + ' at ', ctx_loc.as_list())
                        #print([('Template Vertex: ' + str(v.idx), 'Influence: ' + str(inf)) for v, inf in influence_list])
                        """
                        #This commented out blosk block was used to test the fidelity
                        #of the fast search compared to a simple search
                        #It is retained to test the fidelity of any future
                        #modifications of the fast search algorithm 

                        influence_list_2 = sorted(getVertexInfluence(\
                                                    ctx_loc,\
                                                    a_verts,\
                                                    search_targets = search_targets,\
                                                    Distance = Distance,\
                                                    OverrideDistance = OverrideDistance,\
                                                    search_weight = search_weight,\
                                                    near_vert_weight = 3,\
                                                    far_vert_weight = 3\
                                                ).items(), reverse = True, key = itemgetter(1))
                        cmp_list = [item for item in merge_list(influence_list, influence_list_2)]
                        if cmp_list:
                            discrepancy_count += 1
                            print [item for item in cmp_list if item[0] is not 'l2']
                            print [item for item in cmp_list if item[0] is not 'l1']
                        
                            print 'Influence List'
                            print [(vert, (vert.getLoc(world_loc = True) - ctx_loc).length) for vert, inf in influence_list]
                            print [(vert, (vert.getLoc(world_loc = True) - ctx_loc).length) for vert, inf in influence_list_2]
                        """

 
                    if temp_count >= msg_index:
                        print(str(target_count) + ' of ' + str(vert_count) + 'verts searched')
                        temp_count = 0
                            

#     if settings.get('bone', False) and not tri:
#         
#         ctx_mesh.cleanBUDict()        
#         
#         #ctx_mesh.cleanBUDict()
#         
#         """
#         Cycle through vertices and purge excess 
#         """
#         max_vert_bone = settings.get('bones_per_vert', 4)
#         new_bones = list(ctx_mesh.bone_update_dict.keys())
#         bone_set = set(list(ctx_mesh.bone_update_dict.keys()) + list(ctx_mesh.bone_dict.keys()))
#         print('bone_set', bone_set)
#         weight_dict = dict([(bone_, {}) for bone_ in bone_set])
#         print(weight_dict)
#                 
#         for vert_ in ctx_mesh.getVerts().values():
#             vert_bones = list(vert_.getWeight().items())
# #             while len(vert_bones) > max_vert_bone:
# #                 print(vert_bones)
# #                 for x in range(1, len(vert_bones) + 1):
# #                     test_bone = vert_bones[-x]
# #                     if test_bone not in new_bones:
# #                         del vert_bones[-x]
# #                         break
# #                     if x == len(vert_bones):
# #                         del vert_bones[-1]
#                 
#             if len(vert_bones) > max_vert_bone:
#                 """
#                 purge excess bones
#                 """
#                 vert_bones = sorted(vert_bones, reverse = True, key = itemgetter(1))[0:4]
#             """
#             normalize bone-weights
#             """
#             vert_bones = NormalizeInfluence(vert_bones)
#                 
#             for bone_, weight_ in vert_bones:
#                 weight_dict[bone_][vert_.idx] = weight_
# 
#         
#         for bone_name_, wd_ in weight_dict.items():
#             try:
#                 niBone = ctx_mesh.bone_update_dict[bone_name_]['bone']
#             except:
#                 niBone = ctx_mesh.bone_dict[bone_name_]['bone']
#             
#             ctx_mesh.addBone(niBone, wd_, settings)
# #             
# #         bone_list = settings.get('bone_list', [])
# # 
# # 
# #         for bone_name, bone_info in ctx_mesh.bone_update_dict.items():
# #             if bone_list:
# # 
# #                 if bone_name not in bone_list:
# #                     continue
# #             
# #             niBone = bone_info['bone']
# #             weight_dict = bone_info['verts']
# # 
# #             ctx_mesh.addBone(niBone, weight_dict, settings)
#         print('Bone Update Complete')

                  
#     if settings.get('bone', False) and not tri:
#         bone_package = ctx_mesh.lno.bone_prop_dict
#         bone_list = settings.get('bone_list', [])
#         #print (bone_list)
#         #if not bone_list:
#         #    bone_list = list(act_mesh.bone_dict.keys())
#         ctx_mesh.cleanBUDict()
#         bone_key_list = []
#         for bone_name, bone_info in ctx_mesh.bone_update_dict.items():
# #             print('fucking fuckity fuck')
# #             print(bone_name)
# #             print('fucking fuckity fuck')
#             niBone = bone_package.get(bone_name)
#             if niBone:
#                 niBone = unWrapBone(niBone)
#             else:
#                 niBone = bone_info['bone']
#                 
#                 
#             weight_dict = {}
#             ctx_bone_info = ctx_mesh.bone_dict2.get(bone_name)
# #             print(ctx_bone_info)
#             if ctx_bone_info:
#                 if not settings.get('delete', False):
#                     for idx, weight in ctx_bone_info['weight'].items():
#                         weight_dict[idx] = weight
#                     
#             if bone_list:
#                 if bone_name in bone_list:
#                     for v_idx, val in bone_info['verts'].items():
#                         weight_dict[v_idx] = val
#                         
#             if ctx_bone_info:
#                 if not weight_dict:
#                     for idx, weight in ctx_bone_info['weight'].items():
#                         weight_dict[idx] = weight
#             
#             bone_key_list.append(niBone.name)
#             ctx_mesh.addBone(niBone, weight_dict, settings)
            
#         for bone_name, bone_info in ctx_mesh.bone_dict2.items():
#             niBone = bone_package.get(bone_name)
#             if niBone:
#                 niBone = unWrapBone(niBone)
#             else:
#                 niBone = bone_info['bone']
# 
#             weight_dict = {}
#             for idx, weight in bone_info['weight'].items():
#                 weight_dict[idx] = weight
# 
#             ctx_mesh.addBone(niBone, weight_dict, settings, ignore_existing_bones = True)
#             print('********')
            
        #print('Bone Update Complete')

#     if settings.get('Weight', False):
#         #Time to remove any newly added empty groups
#         for this_group in group_set:
#             if not ctx_mesh.mesh.getVertsFromGroup(this_group):
#                 ctx_mesh.mesh.removeVertGroup(this_group)
 
    #print('Dictionary Check Took', b)
    #print('Vertex Search Took', c)
 
    return targets_found


def GetCircleKeys(radius):
    #This function generates a dictionary of circular index keys that cover the volume between integer radius r - 1 and r.
    #Format of returned keys will be circleDict[y] = list(x values)
    #circleValues is a dictionary containing all currently stored radii values

    global circleValues
    global circleKeyDict

    try:
        return circleKeyDict[radius]
    except:
        pass

    circle_Dict = circleKeyDict[radius] = dict()

    radius_Squared_Max = (radius + 1) ** 2
    radius_Squared_Min = radius ** 2

    for x in range(0, radius + 1):

        x_set = set([x, -x])
        x_squared = x ** 2

        for idx in x_set:
            circle_Dict[idx] = set()

        for z in range(0, radius + 1):

            z_squared = z ** 2
            radius_squared_xz = x_squared + z_squared

            if radius_squared_xz < radius_Squared_Min:
                continue

            if radius_squared_xz >= radius_Squared_Max:
                break

            z_set = set([z, -z])

            for i_x in x_set:
                circle_Dict[i_x].update(z_set)

    return circleKeyDict[radius]

def getCircleBloom(radius):

    #This function returns a dictionary of x, and z indices in a nested dictionary and set format
    #dictionary[x coordinate] = set of z integer values for respective integer values
    #this is used as a lookup table when searching for candidates for nearest neighbor searches

    global circleBloomValues

    try:
        return circleBloomValues[radius]
    except:
        pass

    sphereKeys = GetCircleKeys(radius)
    bloomDict = circleBloomValues[radius] = dict()

    small_set = ([0, 1])

    def getValSet(a):
        if a > 0:
            a_set = set([1])
        elif a < 0:
            a_set = set([-1])
        else:
            a_set = set([-1, 1])

        return set(a + (i1 * i2) for i1 in small_set for i2 in a_set)

    for x, z_list in sphereKeys.items():

        x_val_set = getValSet(x)

        for x_val in x_val_set:
            if x_val not in bloomDict:
                bloomDict[x_val] = set()

        for z in z_list:

            z_val_set = getValSet(z)

            combolist = deepListPermutations([x_val_set, z_val_set])
            combolist.remove([x, z])

            for x_val, z_val in combolist:
                bloomDict[x_val].update([z_val])

    return circleBloomValues[radius]


def GetSphereKeys(radius):
    #This function generates a dictionary of spherical index keys that cover the volume between integer radius r and r + 1.
    #Format of returned keys will be circleDict[y][x] = list(Z Values)

    global sphereKeyDict

    try:
        return sphereKeyDict[radius]
    except:
        pass

    circle_Dict = sphereKeyDict[radius] = dict()

    #Define the inner and outer radii for this search sphere

    radius_Squared_Max = (radius + 1) ** 2
    radius_Squared_Min = radius ** 2
    #max_Y = radius

    #Now iterate through every valid value along the y axis and determine the valid range of x values for a given slice
    for x in range(0, radius + 1):

        x_set = set([x, -x])
        x_squared = x ** 2

        for idx in x_set:
            circle_Dict[idx] = dict()

        for y in range(0, radius + 1):

            y_squared = y ** 2
            radius_squared_xy = x_squared + y_squared

            if radius_squared_xy >= radius_Squared_Max:
                break

            y_set = set([y, -y])

            x_y_permutation_list = deepListPermutations([x_set, y_set])

            for i_x, i_y in x_y_permutation_list:
                circle_Dict[i_x][i_y] = set()

            for z in range(0, radius + 1):

                z_squared = z ** 2
                radius_squared_xyz = radius_squared_xy + z_squared

                if radius_squared_xyz < radius_Squared_Min:
                    continue

                if radius_squared_xyz >= radius_Squared_Max:
                    break

                z_set = set([z, -z])
                #print z_set

                for i_x, i_y in x_y_permutation_list:
                    circle_Dict[i_x][i_y].update(z_set)

                continue

    #key_list_A = set(circle_Dict.keys())
    #key_dict_B = dict([(keyA, set(valA.keys())) for keyA, valA in circle_Dict.items()])

    #for keyA, valB in circle_Dict.items():
    #    for keyB, listC in valB.items():
    #        this_list = sorted(list(listC))
    #        valB[keyB] = this_list

    #sphereKeyDict[(radius, 'KEY_A')] = key_list_A
    #sphereKeyDict[(radius, 'KEY_B')] = key_dict_B

    return sphereKeyDict[radius]

def getSphereBloom(radius):

    #This function returns a dictionary of x, y, and z indices in a nested dictionary and list format
    #dictionary[y coordinate][x coordinate] = list of z integer values for respective x and y integer values
    #this is used as a lookup table when searching for candidates for nearest neighbor searches

    global sphereBloomValues

    try:
        return sphereBloomValues[radius]
    except:
        pass

    sphereKeys = GetSphereKeys(radius)
    sphereBloomValues[radius] = dict()
    bloomDict = sphereBloomValues[radius]
    small_set = ([0, 1])

    def getValSet(a):
        if a > 0:
            a_set = set([1])
        elif a < 0:
            a_set = set([-1])
        else:
            a_set = set([-1, 1])

        return set(a + (i1 * i2) for i1 in small_set for i2 in a_set)

    for x, y_dict in sphereKeys.items():

        x_val_set = getValSet(x)

        for x_val in x_val_set:
            if x_val not in bloomDict:
                bloomDict[x_val] = dict()

        for y, z_list in y_dict.items():

            y_val_set = getValSet(y)

            for x_val in x_val_set:
                for y_val in y_val_set:
                    if y_val not in bloomDict[x_val]:
                        bloomDict[x_val][y_val] = set()

            for z in z_list:

                z_val_set = getValSet(z)

                combolist = deepListPermutations([x_val_set, y_val_set, z_val_set])
                combolist.remove([x, y, z])

                for x_val, y_val, z_val in combolist:
                    bloomDict[x_val][y_val].update([z_val])

    return sphereBloomValues[radius]


def getIntegerKeys(coord, keyList = [0, 2, 1], res = 1):
    """
    
    This function takes set of points as an argument
    It returns a set of integer keys suitable for packing and unpacking
    vertices in vertex loc dictionaries

    Arguments accepted:
    coord: the set of coordinates that will be transformed
    keyList: an optional argument that will reorder the resulting keys
    res: an optional argument that determines the size of the box slices.
    The lengh of a side of the box is 1 / res.  The volume is 1 / res ** 3
    
    """
    #print(coord)
    #print(res)
    #for idx in keyList:
    #    print(coord[idx] * res)
    return [int(ceil(coord[idx] * res)) for idx in keyList]
    #coord_list = []
    #for idx in keyList:
    #    coord = this_vec[idx]
    #    coord_list.append(int(ceil(this_vec[idx]  * res)))
    #return coord_list

def BuildVertexDictionary(vertex_list, res = 2, search_weight = identity_matrix, world_loc = True, keyList = [0, 2, 1], search_type = False, useSearchMod = False, flip_x_axis = False, get_key_set = False, res_alt = None):
    '''
    Receives a list of vertices.  Returns a dictionary that uses locations as keys.
    search_weight is a matrix that will be applied to stretch the indexed space in the specified manner
    useVertType uses the vertType vertex object wrapper.  If set to false, the Blender object.mesh.vertex objects will be used instead
    world_loc should be set to true for searches to find matches between two mesh objects
    world_loc should be set to false for searches to find matches within a single mesh object (find mirrored vertex, etc)
    '''
    #print 'Test 1'
    vertexIndex = dict()
    print ('Building Vertex Dictionary')

    if search_type == 'UV':
        print('UV Search is probably erroring out right about now')
        keyList = [1, 0]
        for uv in vertex_list:
            idx_a, idx_b = getIntegerKeys(uv.getLoc(), keyList = keyList, res = res)
            if res_alt:
                uv.altLoc = getIntegerKeys(uv.getLoc(), keyList = [0,1], res = res_alt)
            #loc = uv.getLoc() * res
            #idx_a, idx_b = [int(loc[x]) for x in keyList]
            if idx_a not in vertexIndex:
                vertexIndex[idx_a] = {idx_b: [uv]}
                continue
            if idx_b not in vertexIndex[idx_a]:
                vertexIndex[idx_a][idx_b] = [uv]
                continue
            if uv not in vertexIndex[idx_a][idx_b]:
                vertexIndex[idx_a][idx_b].append(uv)
    elif search_type == 'LOC_LIST':
        for loc in vertex_list:
            idx_a, idx_b, idx_c = getIntegerKeys(loc, keyList = keyList, res = res)

            if idx_a not in vertexIndex:
                vertexIndex[idx_a] = {idx_b: {idx_c: [loc]}}
                continue
            if idx_b not in vertexIndex[idx_a]:
                vertexIndex[idx_a][idx_b] = {idx_c: [loc]}
                continue
            if idx_c not in vertexIndex[idx_a][idx_b]:
                vertexIndex[idx_a][idx_b][idx_c] = [loc]
                continue

            vertexIndex[idx_a][idx_b][idx_c].append(loc)

    else:            
        for this_vert in vertex_list:
            #print(this_vert.getLoc(world_loc = world_loc, search_loc = useSearchMod, flip_x_axis = flip_x_axis))
            loc = this_vert.getLoc(world_loc = world_loc, search_loc = useSearchMod, flip_x_axis = flip_x_axis) * search_weight
            #print(loc)
            idx_a, idx_b, idx_c = getIntegerKeys(loc.as_list(), keyList = keyList, res = res)
            if res_alt:
                this_vert.altLoc = getIntegerKeys(loc.as_list(), keyList = [0,1,2], res = res_alt)
            #print(idx_a, idx_b, idx_c)
            if idx_a not in vertexIndex:
                vertexIndex[idx_a] = {idx_b: {idx_c: [this_vert]}}
                continue
            if idx_b not in vertexIndex[idx_a]:
                vertexIndex[idx_a][idx_b] = {idx_c: [this_vert]}
                continue
            if idx_c not in vertexIndex[idx_a][idx_b]:
                vertexIndex[idx_a][idx_b][idx_c] = [this_vert]
                continue

            vertexIndex[idx_a][idx_b][idx_c].append(this_vert)

#     if get_key_set:
#         set_a = set(vertexIndex.keys())
#         set_b = dict([(key_a, set(val_a.keys())) for key_a, val_a in vertexIndex.items()])
#         set_c = dict([(key_a, dict([(key_b, set(val_b.keys()))])) for key_a, val_a in vertexIndex.items() for key_b, val_b in val_a.items()])
#         return vertexIndex, set_a, set_b, set_c

    return vertexIndex

def GetNearVert(vertloc, vNumberPref, vertLocDictionary, xAxisNoCross = False, Distance = False, OverrideDistance = False, res = 1, keyList = [0, 2, 1], uv_search = False, bb = False, max_radius = False, set_a = set(), set_b = set(), set_c = set(), res_alt = None, search_weight = identity_matrix, int_dist_sq = None):
    """
    This function identifies candidate vertices for nearest neighbor searches.

    vertloc. three coordinates representing a vector (x,y,z)
    vNumberPref. number of target vertices sought
    vertLocDictionary. This is a dictionary containing vertex indices.  The key is a n x,y,z tuple, following the format. (int(10 * v.co[0],int(10 * v.co[1],int(10 * v.c0[2]) where v is a given vertex
    minKey, maxKey A list containing three items (x,y,z) that define the minimum and maximum boundaries of the search space
    xAxisNoCross.  value of 1 treats the x = 0 plane as a search boundary for verts.co[0] > 0 and verts.co[0] < 0
    Distance. he maximum allowed search distance.  This limits the maximum allowed iterations (Distance = r / 10)
    res combined gives the relative size of each dictionary space that will be searched.
    UV search is a 2D vector search.  When UV is false, the standard 3D vector search will be used
    """
    vertKey = dict()
    VertList = list()
    this_radius = -1

    doOnce = False

    if uv_search:
        keyList = [1, 0]
        keyA, keyB = getIntegerKeys(vertloc.as_list(), keyList = keyList, res = res)
        #keyA, keyB = [int(res * vertloc[x]) for x in keyList]
        key_dictionary = circleKeyDict
        key_function = GetCircleKeys
        bloom_function = getCircleBloom
    else:
        tempKeys = keyA, keyB, keyC = getIntegerKeys(vertloc.as_list(), keyList = keyList, res = res)
        #keyA, keyB, keyC = [int(res * vertloc[x]) for x in keyList]
        key_dictionary = sphereKeyDict
        key_function = GetSphereKeys
        bloom_function = getSphereBloom

    if not OverrideDistance or not max_radius:
        max_radius = int(ceil(Distance * res)) + 1

    VertList = list()

    #print(set_a)
    #print(vertLocDictionary.keys())
    def checkUVDictionary(keyDict):
        temp_uv_vert_list = list()
        for a, keyDictA in keyDict.items():
            aKey = keyA + a
            aDict = vertLocDictionary.get(aKey)
            if aDict:
                for b in keyDictA:
                    bKey = keyB + b
                    bDict = aDict.get(bKey)
                    if bDict:
                        temp_uv_vert_list.extend(bDict)
        return temp_uv_vert_list

    def checkVertDictionary(keyDict):
#         valid_keys = key_set_A.intersection(set_b)
#         if not valid_keys:
#             return []
        temp_vert_list = list()
        #for a in valid_keys:
        for a, keyDictA in keyDict.items():
            keyDictA = keyDict[a]
            aKey = keyA + a
            aDict = vertLocDictionary.get(aKey)
            if aDict:
                for b, keyDictB in keyDictA.items():
                    bKey = keyB + b
                    bDict = aDict.get(bKey)
                    if bDict:
                        for c in keyDictB:
                            cKey = keyC + c
                            cDict = bDict.get(cKey)
                            if cDict:
                                temp_vert_list.extend(cDict)
        return temp_vert_list


    def checkVertDictionarySet(keyDict, key_set_A):
        valid_keys = key_set_A.intersection(set(keyDict.keys()))
        if not valid_keys:
            return []
        temp_vert_list = list()
        #print(valid_keys)
        #print(keyDict.keys())
        for a in valid_keys:
        #for a, keyDictA in keyDict.items():
            keyDictA = keyDict[a]
            aKey = keyA + a
            aDict = vertLocDictionary.get(aKey)
            if aDict:
                for b, keyDictB in keyDictA.items():
                    bKey = keyB + b
                    bDict = aDict.get(bKey)
                    if bDict:
                        for c in keyDictB:
                            cKey = keyC + c
                            cDict = bDict.get(cKey)
                            if cDict:
                                temp_vert_list.extend(cDict)
        return temp_vert_list


    if uv_search:
        check_function = checkUVDictionary
    else:
        check_function = checkVertDictionary

    endCounter = 0

    def sub_a(itm):
        return sub(itm, keyA)

    while endCounter < 2 :
        this_radius += 1
        if this_radius not in key_dictionary:
            key_dictionary[this_radius] = key_function(this_radius)
        keyDict = key_dictionary.get(this_radius)
        #key_set_A = set(map(sub_a, set_a))
#         if bb:
        #key_set_A = set(map(add_a, sphereKeyDict.get(this_radius, 'KEY_A')))
#             key_dict_B = sphereKeyDict.get((this_radius, 'KEY_B'))
            #key_list_A = set(val for val in key_list_Main if val > minA and val < maxA)
            #key_list_B = list(a)
            #key_dict_B = sphereKeyDict[(radius, 'KEY_B')]
        VertList.extend(checkVertDictionary(keyDict))
        #VertList.extend(checkVertDictionarySet(keyDict, key_set_A))

        if Distance:
            if this_radius > max_radius:
                if OverrideDistance and not len(VertList):
                    continue
                break
        if len(VertList) >= vNumberPref:
            endCounter += 1

    keyDict = bloom_function(this_radius)
    VertList.extend(check_function(keyDict))
            
    #print ('after', len(VertList))
            


    #purge Duplicates
    #print this_radius
    return list(set(VertList))

def getSQDist(coord_1, coord_2):
    return pow(sub(coord_1, coord_2),2)

def getVertexInfluence(target_loc, passed_vert_list, search_targets = 1, Distance = False, OverrideDistance = False, search_weight = identity_matrix, uv_search = False, match = True, near_vert_weight = 3, far_vert_weight = 3, return_type = 'VERT', int_dist_sq = None, res_alt = 1000):
    """
    This function takes a list of candidate vertices and returns a dictionary of vertex : relative influence based on proximity to the passed target location , target_loc
    keywords accepted:

    search_targets: Maximum number of entries in the returned influence dictionary
    Distance: Maximum allowed distance between target_loc and a vertex position
    OverrideDistance: If every vertex fails the distance test, determines if the shortest distance vertes should be returned.
    search_weight: Transformation matrix that modifies the distance calculation
    uv_search: Is this search in 2D UV space or 3D object space
    match: If set to true, exact matches purge the list down to exact matches only
    near_vert_weight: Increases the relative influence of near vertices
    far_vert_weight: Increases the relative influence of distant vertices

    Note: This the passed vert list must be free of duplicates.

    """
    if not passed_vert_list:
        return {}

    #purge Duplicates
    #passed_vert_list = list(set(passed_vert_list))

    

    if uv_search:
        print('Reminder UV Search is Currently Non Functional')
        vert_list = [((uv.getLoc() - target_loc).length, uv.getVert()) for uv in passed_vert_list]

    else:
        #vert_list = [(sqrt(getVecLenSq((the_vert.getLoc(world_loc = True) - target_loc) * search_weight)), the_vert) for the_vert in passed_vert_list]
        v_loc = getIntegerKeys((target_loc * search_weight).as_list(), keyList = [0,1,2], res = res_alt)
        vert_list =  [(sum(list(map(getSQDist, v_loc, v.altLoc))), v) for v in passed_vert_list]


        #vert_list = [(((the_vert.getLoc(world_loc = True) - target_loc) * search_weight).length, the_vert) for the_vert in passed_vert_list]
        #vert_list = [(getVecLenSq((the_vert.getLoc(world_loc = True) - target_loc) * search_weight) ** .5, the_vert) for the_vert in passed_vert_list]
        #vert_list = [(length(the_vert.getLoc(world_loc = True) - target_loc), the_vert) for the_vert in passed_vert_list]


    #print (vert_list)
    if Distance or int_dist_sq:
        if not int_dist_sq:
            int_dist_sq = int(ceil(pow(Distance * res_alt, 2)))
        

        culled_list = [(this_length, vert) for this_length, vert in vert_list if this_length <= int_dist_sq]
        if not culled_list and OverrideDistance:
            culled_list = [(min(vert_list, key = itemgetter(0)))]

        if not culled_list:
            return {}

        vert_list = culled_list

    #vert_list = [(loc, v) for loc, v in sorted(vert_list, key = itemgetter(0))[0:search_targets]]
    vert_list = [(sqrt(loc), v) for loc, v in sorted(vert_list, key = itemgetter(0))[0:search_targets]]
    #vert_list = vert_list[0:search_targets]
    #if len(vert_list):
    #    print('Culled Target List', vert_list)
    return calc_distance_weights(vert_list, near_vert_weight = near_vert_weight, far_vert_weight = near_vert_weight, return_type = return_type)

def calc_distance_weights(vert_list, near_vert_weight = 3, far_vert_weight = 3, return_type = 'VERT'):
    """
    Accepts a list of distance, vert tuples.
    Returns a dictionary with vert keys and relative influence values
    The sum of all influences in the dictionary will be 1.0

    Keywords Accepted
    vert_number: Maximum number of vertices to be processed in the list
    """
    if not vert_list:
        return {}

    #Purge duplicate entries
    #vert_list = list(set(vert_list))

    list_length = len(vert_list)

    if list_length == 1:
        if return_type == 'LENGTH':
            return {vert_list[0][0] : 1.0}
        return {vert_list[0][1] : 1.0}

    max_length = max(vert_list, key = itemgetter(0))[0]

    if not max_length:
        influence = 1.0 / float(len(vert_list))
        if return_type == 'LENGTH':
            return dict([(this_length, influence) for this_length, vert in vert_list])
        return dict([(vert, influence) for this_length, vert in vert_list])

    length_ratio = 1.0 / max_length

    if return_type == 'LENGTH':
        vertex_influence_dict = dict([\
            (this_length, ((1 - (float(this_length) * length_ratio) ** near_vert_weight) ** far_vert_weight))\
            for this_length, vert in vert_list\
        ])

    else:
        vertex_influence_dict = dict([\
            (vert, ((1 - (float(this_length) * length_ratio) ** near_vert_weight) ** far_vert_weight))\
            for this_length, vert in vert_list\
        ])

    influence_sum = float(sum(vertex_influence_dict.values()))

    if influence_sum:
        influence_ratio = 1.0 / float(influence_sum)
        return dict([(vert, influence * influence_ratio) for vert, influence in vertex_influence_dict.items()])

    influence = 1.0 / float(len(vertex_influence_dict))
    return dict([(vert, influence) for vert, influence in vertex_influence_dict.items()])