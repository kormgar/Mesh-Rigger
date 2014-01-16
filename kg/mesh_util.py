from itertools import combinations
import pyffi
from pyffi import formats
from pyffi.formats import nif
from pyffi.formats.nif import NifFormat
#from pyffi.formats.nif.NifFormat import Matrix33, Vector3
from kg.vert_util import vertex, mendSeamDoubles
from kg.face_util import face
from kg.search_util import BuildVertexDictionary, NormalizeInfluence
from kg.bone_util import getBoneSide, wrapBone, unWrapBone, extractTransform
from kg.math_util import matrix3x3, vector
from kg.data_sets import part_settings

#from collections import Counter
from operator import itemgetter
import re

r_female = re.compile('female', flags=re.IGNORECASE)
r_male = re.compile('male', flags=re.IGNORECASE)


class mesh(object):

    def __init__(\
        self,\
        load_obj,\
        block,\
        full_init = True,\
        tri = False,\
        egm = False\
    ):
        self.lno = load_obj
        self.data = self.lno.data
        self.tri = tri
        self.egm = egm
        self.nmv_doubles = set()
        self.bone_update_dict = {}
    
        if tri:
            self.niData = self.data
            self.verts = dict([(idx, vertex(idx, vert, self)) for idx, vert in enumerate(self.data.vertices)])
            self.init_faces()
            self.mat = matrix3x3()
            self.mat_i = matrix3x3()
            #print(self.verts)
            return
        if egm:
            return
        
        self.root_blocks = load_obj.root_blocks
        self.block = block
        self.textures = self.getTextures()
        self.material = self.getMaterial()
        self.niData = block.data
        self.verts = dict([(idx, vertex(idx, vert, self)) for idx, vert in enumerate(self.niData.vertices)])
        self.mat = self.block.get_transform()
        self.mat_i = self.mat.get_inverse()
        self.nmv_verts = {}
        self.init = full_init

        self.partition_map_ = None
        self.triangles_ = None
        self.skin = self.block.skin_instance
        if self.skin:
            if isinstance(self.skin, NifFormat.BSDismemberSkinInstance):
                self.triangles_, self.partition_map_ = (self.skin.get_dismember_partitions())
                #print(self.triangles_)
                #print(self.partition_map_)
        if self.skin.data:
            self.skin_transform = extractTransform(self.skin.data.skin_transform)
            self.skin_type = type(self.skin)
        """initialize UV Information"""
        self.uv_sets = self.niData.uv_sets
            
        if self.init:
            self.initDoubles()
            self.init_faces()
            if self.uv_sets:
                self.initUV()
            print ('initializing bones')
            self.initBones()
        else:
            """initialize Faces and Find NMV Vertices"""
            self.init_faces()
        #print('len(self.nmv_verts)',len(self.nmv_verts))
        #print('validating skin')
        #self.block._validate_skin()

    def getGender(self):
        if self.tri:
            return 'NONE'
        #print(self.textures)
        if not self.textures:
            return 'NONE'
        if re.search(r_female, self.textures):
            return 'FEMALE' 
        if re.search(r_male, self.textures):
            return 'MALE' 
        return 'NONE'

    def getTextures(self):
        for block in self.block.properties:
            if isinstance(block, NifFormat.NiTexturingProperty):
                try:
                    filename = getattr(block, 'base_texture').source.file_name.decode("utf-8")
                except:
                    filename = False
                return filename

            #if isinstance(block, NifFormat.BSShaderTextureSet):
            #    print(block)
                
                
#             if isinstance(block, NifFormat.NiMaterialProperty):
#             if isinstance(block, NifFormat.BSLightingShaderProperty):                
#             if isinstance(block, NifFormat.NiAVObject):
            
    def getMaterial(self):           
        for block in self.block.properties:
            return
        

    def getNormalDict(self, res = 10000):
        normal_loc_list = [v.normal for v in self.verts.values()]
        BuildVertexDictionary(self.verts.values(), res = res)
        return

    def getVertDict(self, res = 10000):
        vert_dictionary = BuildVertexDictionary(self.verts.values(), res = res)
        return

    def initBones(self):
        
        self.skininst = self.block.skin_instance
        #print (self.skininst)
        if self.skininst:
            
            #print ('Test A')
            #print (skininst.get_vertex_weights())
            
            #print(NifFormat.NiSkinData().get_vertex_weights())
            self.skindata = self.skininst.data
            bones = self.skininst.bones
            boneWeights = self.skindata.bone_list
            
            self.bone_dict = dict([(bone.name, {'idx': idx, 'bone': bone, 'weight' : boneWeights[idx].vertex_weights}) for idx, bone in enumerate(bones) if bone])
            #self.bone_dict2 = dict([(bone.name, {'idx': idx, 'bone': bone, 'weight' : dict([(skinweight.index, skinweight.weight) for skinweight in boneWeights[idx].vertex_weights])}) for idx, bone in enumerate(bones) if bone])
            vert_dict = self.verts
            for bone_name, this_bone in self.bone_dict.items():
                for skinWeight in this_bone['weight']:
                    this_vert = vert_dict[skinWeight.index]
                    this_vert.addWeight(bone_name, skinWeight.weight)
            return
        else:
            self.bone_dict = {}
            
    def processWeightDictionary(self, settings = {}):


        if self.lno.settings.get('delete_rigging'):
            delete_rig = True
        else:
            delete_rig = False
        
        #if not self.lno.settings.get('copy_havok'):
        self.cleanBUDict()
        try:
            max_vert_bone = part_settings[self.lno.game]['maxbonespervertex']
        except:
            max_vert_bone = 4

        """
        Cycle through vertices and purge excess 
        """
        if delete_rig:
            bone_set = set(list(self.bone_update_dict.keys()))
        else:
            bone_set = set(list(self.bone_update_dict.keys()) + list(self.bone_dict.keys()))
        
        weight_dict = dict([(bone_, {}) for bone_ in bone_set])
                
        for vert_ in self.getVerts().values():
            vert_bones = list(vert_.getWeight().items())
                
            if len(vert_bones) > max_vert_bone:
                """
                purge excess bones
                """
                vert_bones = sorted(vert_bones, reverse = True, key = itemgetter(1))[0:4]
            """
            normalize bone-weights
            """
            vert_bones = NormalizeInfluence(vert_bones)
                
            for bone_, weight_ in vert_bones:
                try:
                    weight_dict[bone_][vert_.idx] = weight_
                except:
                    weight_dict[bone_] = {vert_.idx: weight_}

        return weight_dict

    def addBone2(self, bone, weight_dict, settings = {}, side = False, ignore_existing_bones = False):
        #bone = self.lno.bone_dict.get(bone.name)
        #self.block._validate_skin() 
        #print(self.block)
        skininst = self.block.skin_instance 
        skindata = skininst.data 
        bone_index = skininst.num_bones 
        skininst.num_bones = bone_index+1 
        skininst.bones.update_size() 
        skininst.bones[bone_index] = bone 
        skindata.num_bones = bone_index+1 
        skindata.bone_list.update_size() 
        skinbonedata = skindata.bone_list[bone_index] 
        # set vertex weights 
        skinbonedata.num_vertices = len(weight_dict) 
        skinbonedata.vertex_weights.update_size() 
        for i, (vert_index, vert_weight) in enumerate(sorted(weight_dict.items())): 
            skinbonedata.vertex_weights[i].index = vert_index 
            skinbonedata.vertex_weights[i].weight = vert_weight      
        return
            
    def addBone(self, bone, weight_dict, settings = {}, side = False, ignore_existing_bones = False):
        """
        Add a bone and boneweights to a nif that is missing the bone
        bone should be a bone from a block.skin_instance.bones call
        weight_dict should be the format {v_idx: weight}
        """
        #print('validating skin ')
        #self.block._validate_skin()
        #print('***TESTING***')
        #print ('processing', bone.name)
        #print (dir(bone))
        #print ('processing', bone.name)
        bone_info = self.bone_dict.get(bone.name)
        if bone_info and not ignore_existing_bones:
            """
            Merge weight dictionaries
            """
            bone_index = bone_info['idx']
            skinbonedata = self.skindata.bone_list[bone_index]    
            self.skininst.bones
            #print ('bone found updating weight table on mesh')
#             if not settings.get('delete', False):
#                 for skinWeight in bone_info['weight']:
#                     v_idx = skinWeight.index
#                     if v_idx not in weight_dict:
#                         weight_dict[v_idx] = skinWeight.weight
                     
            skinbonedata.num_vertices = len(weight_dict)                           
            skinbonedata.vertex_weights.update_size()   
                                            
            for i, (vert_index, vert_weight) in enumerate(sorted(weight_dict.items(), key = itemgetter(0))):
                skinbonedata.vertex_weights[i].index = vert_index                   
                skinbonedata.vertex_weights[i].weight = vert_weight    
            return
        elif self.lno.bone_dict.get(bone.name):
            bone = self.lno.bone_dict.get(bone.name)
            #self.block._validate_skin() 
            skininst = self.block.skin_instance 
            skindata = skininst.data 
            bone_index = skininst.num_bones 
            skininst.num_bones = bone_index+1 
            skininst.bones.update_size() 
            skininst.bones[bone_index] = bone 
            skindata.num_bones = bone_index+1 
            skindata.bone_list.update_size() 
            skinbonedata = skindata.bone_list[bone_index] 
            # set vertex weights 
            skinbonedata.num_vertices = len(weight_dict) 
            skinbonedata.vertex_weights.update_size() 
            for i, (vert_index, vert_weight) in enumerate(sorted(weight_dict.items())): 
                skinbonedata.vertex_weights[i].index = vert_index 
                skinbonedata.vertex_weights[i].weight = vert_weight         
        else:
#             print ('processing', bone.name)
#             print('bone not found, adding to mesh')
#             print('rotation', bone.rotation)
#             print('translation', bone.translation)
#             print('scale', bone.scale)
            
            bone_dict = wrapBone(bone)
            bone = unWrapBone(bone_dict)
            #bone.update_bind_position()
            #self.block._validate_skin() 
            skininst = self.block.skin_instance 
            skindata = skininst.data 
            skelroot = skininst.skeleton_root 
            skelroot.num_children += 1
            skelroot.children.update_size()
            skelroot.add_child(bone) 
            bone_index = skininst.num_bones 
            skininst.num_bones = bone_index+1 
            skininst.bones.update_size() 
            skininst.bones[bone_index] = bone
            skindata.num_bones = bone_index+1 
            skindata.bone_list.update_size() 
            skinbonedata = skindata.bone_list[bone_index] 
            # set vertex weights 
            skinbonedata.num_vertices = len(weight_dict) 
            skinbonedata.vertex_weights.update_size() 
            for i, (vert_index, vert_weight) in enumerate(sorted(weight_dict.items())): 
                skinbonedata.vertex_weights[i].index = vert_index 
                skinbonedata.vertex_weights[i].weight = vert_weight 
                
            self.lno.bone_dict[bone.name] = bone
            #self.skindata = self.skininst.data
            #bones = self.skininst.bones
            #boneWeights = self.skindata.bone_list
            #self.bone_dict = dict([(bone.name, {'idx': idx, 'bone': bone, 'weight' : boneWeights[idx].vertex_weights}) for idx, bone in enumerate(bones) if bone])
            #self.block.update_bind_position()
            if side and side == getBoneSide(bone.name.decode("utf-8")):
                self.mirrorBone(bone)
                
#             print('rotation', bone.rotation)
#             print('translation', bone.translation)
#             print('scale', bone.scale)                
                
        return
  
    def mirrorBone(self, bone):
        #print(dir(bone))
        return
  
    def initBUDict(self, template_bone_dict, settings = {}):
        """
        initialize the bone_update_dict with all of the bones in the template mesh
        """
        bone_list = settings.get('bone_list', [])
        for bone_name, bone_info in template_bone_dict.items():
            if bone_name in bone_list:
                #print('Good Bone Name', bone_name)
                self.bone_update_dict[bone_name] = {'bone': bone_info['bone'], 'verts': {}}
            #else:
                #print('Bad Bone Name', bone_name)
  
    def cleanBUDict(self):
        """
        Purge empty groups from the bone_update_dict
        """
        delete_list = [bone_name for bone_name, bone_info in self.bone_update_dict.items() if not bone_info['verts']]
        for bone_name in delete_list:
            del self.bone_update_dict[bone_name]
        #print(self.bone_update_dict)
                        
    def initUV(self):
        #First, convert UV map information into a dictionary that uses vertex index as a key
        self.uv_dict = dict([\
            (\
             uv_idx, dict(zip([int(a[1:-1])\
             for a in uv_map.get_detail_child_names()], uv_map))\
            )\
            for uv_idx, uv_map in enumerate(self.uv_sets)\
        ])
        
        for uv_set_idx, uvs in self.uv_dict.items():
            for v_idx, uv in uvs.items():
                self.verts[v_idx].uv = uv
                self.verts[v_idx].uv_set = uv_set_idx
                #print v_idx, self.verts[v_idx].uv
        
    def generatePartitionMap(self):
        
        faces = self.faces
        verts = self.verts
        partition_map = list()
        invalid_list = list()
        triangles = list()
        for idx, face_idx in enumerate(self.niData.get_triangles()):
            bd_partition_dict = {}
            
            for v_idx in face_idx:
                this_vert = verts[v_idx]
                for vert, influence in this_vert.influence_list:
                    part_key_list = vert.BDPartition
                    for key in part_key_list:
                        new_val = bd_partition_dict.get(key, 0) + influence
                        bd_partition_dict[key] = new_val
            if not bd_partition_dict:
                partition_map.append(0)
                triangles.append(face_idx)
                invalid_list.append(idx)
                continue
            partition_map.append(max(list(
            bd_partition_dict.items()), key = itemgetter(1))[0])
            triangles.append(face_idx)

        return triangles, partition_map
        
    def init_faces(self):
        print('initializing faces')
        verts = self.verts
        self.faces = dict()
        self.edges = dict()
        self.edge_count = dict()
        
        if self.tri:
            triangles = [tuple([tri.v_1, tri.v_2, tri.v_3]) for tri in self.niData.tri_faces]
            #print(dir(triangles))
            
            self.partition_map = None
        elif self.egm:
            self.partition_map = None
        
        elif isinstance(self.block.skin_instance, NifFormat.BSDismemberSkinInstance):
            triangles = self.niData.get_triangles()
            triangles, trianglepartmap = (self.block.skin_instance.get_dismember_partitions())
            self.partition_map = dict(zip(triangles, trianglepartmap))
            for this_face, d_idx in self.partition_map.items():
                for v_idx in this_face:
                    verts[v_idx].addBDPartition(d_idx)
        else:
            triangles = self.niData.get_triangles()
            self.partition_map = None
            
        for idx, tri in enumerate(triangles):
            
            face_verts = dict([(v_idx, verts[v_idx]) for v_idx in tri])
            
            this_face = self.faces[tri] = face(idx, face_verts)
            
            tri_edge_key = sorted(tri)
            
            edge_idx_list = list(combinations(tri_edge_key, 2))
            #print(edge_idx_list)
            this_face.edges = edge_idx_list

            for edge_key in edge_idx_list:
                #if edge_key in self.edges:
                #    print(edge_key)
                if edge_key not in self.edges:
                    self.edges[edge_key] = list()
                    self.edge_count[edge_key] = 0
                    """
                    Update each vert in this edge with neighboring vertex information
                    This is the foundation of any edge connectivity maps
                    """
                    for x in range(2):
                        face_verts[edge_key[x]].addEdges([face_verts[edge_key[x - 1]]])
                self.edges[edge_key].append(this_face)
                self.edge_count[edge_key] += 1
                
        self.nmv_edges = [edge_key for edge_key, ct in self.edge_count.items() if ct == 1]
        self.nmv_faces = [self.edges[edge_key] for edge_key in self.nmv_edges]
        self.nmv_verts = dict([(v_idx, self.verts[v_idx].setNMV()) for vert_tup in self.nmv_edges for v_idx in vert_tup])
        #print (len(self.nmv_verts))
        delete_list = list()
        "Purge true doubles from nmv verts list"            
        for idx, vert in self.nmv_verts.items():
            if vert.getDoubles():

                list_1 = list(edge_vert.getDoubles() for edge_vert in vert.getEdges() if edge_vert.getNMV() and edge_vert.getDoubles())
                if len(list_1) > 1:
                    vert_double_tup = tuple(sorted([vert] + list(vert.getDoubles().values()), key = lambda v:v.idx))
                    self.nmv_doubles.update([vert_double_tup])
                    delete_list.append(idx)
        for idx in delete_list:
            del self.nmv_verts[idx]
        for vert in self.nmv_verts.values():
            vert.NMV = True
        #print (len(self.nmv_verts))
        return
            
    def getNMVVerts(self, nmv = False):
        if not self.nmv_verts:
            self.init_faces()
        if nmv == 'EXCLUDE':
            try:
                return self.non_nmv_verts
            except:
                """Build a dictionary of non nmv verts"""
                vert_set = set(list(self.verts.items()))
                nmv_set = set(list(self.nmv_verts.items()))
                self.non_nmv_verts = dict(vert_set.difference(nmv_set))
                return self.non_nmv_verts
        #print('returning nmv verts')
        return self.nmv_verts

            
    def getVerts(self, side = False, nmv = False):
        include_set = set(list(self.verts.items()))
        #print('include_set', include_set)
        if side:
            include_set.intersection_update(list((v_idx, this_vert)
            for v_idx, this_vert in self.verts.items()
            if this_vert.getSide(side)))
        if nmv:
            include_set.intersection_update(set(list(self.getNMVVerts(nmv = nmv).items())))
                          
        return dict(include_set)
          
    
    def initDoubles(self, res = 10000):
        """
        
        Attempt to find one or more vertex doubles.

        Builds a vertex location dictionary to index the locations for fast access.

        keywards accepted:

        res: integer value.  Default 10000.  1 / res (default .0001) gives the length of each side 
        of the box checked for the mirror of a given vertex

        """
        main_dictionary = BuildVertexDictionary(self.getVerts().values(), res = res, world_loc = False)
        for y_entry in main_dictionary.values():
            for x_entry in y_entry.values():
                for vert_list in x_entry.values():
                    if len(vert_list) > 1:
                        for this_vert in vert_list:
                            this_vert.setDouble(dict([(v1.idx, v1) for v1 in vert_list if v1 is not this_vert]))
                    else:
                        vert_list[0].setDouble({})


class multiMesh(object):
    def __init__(
        self,\
        mesh_list,\
        load_nif_obj\
    ):
        self.lno = load_nif_obj
        self.m_list = mesh_list
        self.block = mesh_list[0].block
        self.v_list = [vert for mesh in self.m_list for vert in mesh.getVerts().values()]
        self.verts = dict([(i, vert) for i, vert in enumerate(self.v_list)])
        self.verts_v = dict([(vert, i) for i, vert in enumerate(self.v_list)])
        self.bone_dict = dict([(bone_name, {'bone': bone}) for bone_name, bone in set([(bone_name, bone_info['bone']) for mesh in self.m_list for bone_name, bone_info in mesh.bone_dict.items()])])
        self.nmv_verts = dict([(idx, vert) for idx, vert in self.verts.items() if vert.NMV])
        self.data = self.lno.data

    def __iter__(self):
        for mesh_ in self.m_list:
            yield mesh_
            
    def loadSkeleton(self, skeleton):
        if not skeleton:
            return
        return
    
    def initDoubles(self, res = 1000, mend = False):
        """
        
        Attempt to find one or more vertex doubles.

        Builds a vertex location dictionary to index the locations for fast access.

        keywards accepted:

        res: integer value.  Default 10000.  1 / res (default .0001) gives the length of each side 
        of the box checked for the mirror of a given vertex

        """
        main_dictionary = BuildVertexDictionary(self.getVerts().values(), res = res, world_loc = False)
        for y_entry in main_dictionary.values():
            for x_entry in y_entry.values():
                for vert_list in x_entry.values():
                    if len(vert_list) > 1:
                        for this_vert in vert_list:
                            this_vert.setDouble(dict([(v1.idx, v1) for v1 in vert_list if v1 is not this_vert]))
                        mendSeamDoubles(vert_list)    
                    else:
                        vert_list[0].setDouble({})

    
    def getblocks(self):
        return [this_mesh.block for this_mesh in self.m_list]
                   
    def getNMVVerts(self, nmv = False):
        if nmv == 'EXCLUDE':
            try:
                return self.non_nmv_verts
            except:
                """Build a dictionary of non nmv verts"""
                self.non_nmv_list = [vert for mesh in self.m_list for vert in mesh.getNMVVerts(nmv = nmv)]
                self.non_nmv_verts = dict([(self.verts_v[vert], vert) for vert in self.v_list])
                return self.non_nmv_verts
        return self.nmv_verts

           
    def getVerts(self, side = False, nmv = False, limit_doubles = False):
        
        include_set = set(list(self.verts.items()))
        if side:
            include_set.intersection_update(list((v_idx, this_vert)
            for v_idx, this_vert in self.verts.items()
            if this_vert.getSide(side)))
        if nmv:
            include_set.intersection_update(set(list(self.getNMVVerts(nmv = nmv).items())))
        if limit_doubles:
            double_set = set()
            for vert in include_set:
                if vert.getDoubles() and vert not in double_set:
                    double_set.update(set(vert.getDoubles()))
            include_set.difference_update(double_set)
                           
        return dict(include_set)

class templateMesh(object):
    def __init__(
        self,\
        vert_dict,\
        bone_dict\
    ):
    
        mesh_vert_dict = {}
        for mesh_name, v_dict in vert_dict.items():
            mesh_vert_dict[mesh_name] = {}
            for v_idx, v_data in v_dict.items():
                this_vert = vertex(v_idx, init = False)
                this_vert.loc = vector(v_data['loc'])
                if 'w_loc' in v_data:
                    this_vert.w_loc = vector(v_data['w_loc'])
                else:
                    this_vert.loc = vector(v_data['loc'])
                this_vert.normal = vector(v_data['norm'])
                this_vert.weight_dict = v_data['wd']
                this_vert.NMV = True
                mesh_vert_dict[mesh_name] = this_vert   
        self.mesh_vert_dict = mesh_vert_dict
        self.v_list = [v for v in self.mesh_vert_dict.values()]
        self.verts = dict([(i, vert) for i, vert in enumerate(self.v_list)])
        self.non_nmv_verts = {}
        self.nmv_verts = self.verts
        self.bone_dict = dict([(bone_name, {'bone': bone}) for bone_name, bone in bone_dict.items()])

           
    def getNMVVerts(self, nmv = False):
        return self.nmv_verts
           
    def getVerts(self, side = False, nmv = False):
        
        include_set = set(list(self.verts.items()))
        if side:
            include_set.intersection_update(list((v_idx, this_vert)
            for v_idx, this_vert in self.verts.items()
            if this_vert.getSide(side)))
        if nmv:
            include_set.intersection_update(set(list(self.getNMVVerts(nmv = nmv).items())))
                           
        return dict(include_set)
        
        