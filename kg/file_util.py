import kg
# import pyffi
# from pyffi.formats.nif import NifFormat
# from pyffi.spells.nif import NifSpell
# import pyffi.spells.nif
# import pyffi.spells.nif.check # recycle checking spells for update spells
#from kg.mesh_util import mesh
#from kg import ui_tools
from os import listdir, path, makedirs, getcwd, walk
from re import compile, split, sub, search, IGNORECASE
from pyffi.formats.nif import NifFormat
from pyffi.formats.tri import TriFormat
from pyffi.formats.egm import EgmFormat

import pickle

progCFG = compile('\.ini$', flags=IGNORECASE)
r_parse_file_bracket = compile('\}\s\{', flags=IGNORECASE)
r_parse_nif_file_spacer = compile('\.nif\s', flags=IGNORECASE)
r_parse_tri_file_spacer = compile('\.tri\s', flags=IGNORECASE)
r_parse_file_spacer2 = compile('\.(nif)\',\s\'|\.(tri)\',\s\'', flags=IGNORECASE)
r_parse_bracket = compile('^{|}$', flags=IGNORECASE)
r_nif = compile('\.nif', flags=IGNORECASE)
r_nif_end = compile('\.nif$', flags=IGNORECASE)
r_tri = compile('\.tri', flags=IGNORECASE)
r_tri_end = compile('\.tri$', flags=IGNORECASE)
r_skin = compile('skin', flags=IGNORECASE)
r_male = compile('male', flags=IGNORECASE)
r_female = compile('female', flags=IGNORECASE)
r_flag_male = compile('_m\.nif$', flags=IGNORECASE)
r_flag_female = compile('_f\.nif$', flags=IGNORECASE)
r_morph_0 = compile('_0\.nif$', flags=IGNORECASE)
r_morph_1 = compile('_1\.nif$', flags=IGNORECASE)
r_morph_01 = compile('^'+'(.*)'+'_[01]\.nif$', flags=IGNORECASE)

"""
Determine the configuration directory.  Create directory if not found
"""

global dir_
dir_ = path.normpath(path.join(getcwd(), 'save'))
if not path.exists(dir_):
    makedirs(dir_)
#print(dir_)
    
global i_dir_
i_dir_ = path.normpath((getcwd()))
if not path.exists(i_dir_):
    makedirs(i_dir_)
#print(i_dir_)
#print(dir_)
#print(i_dir_)



def checkPath(path_, dir_ = i_dir_):
    #print('Checking Path', path_)
    #print('Test Results:', path.isabs(path_))
    if not path.isabs(path_):
        path_ = path.normpath(path.join(i_dir_, path_))
    return path_

def save_file(target_mesh, this_file, targets_found, current_settings, morph_dict = {}): 
    #print(this_file)

    destination_path = checkPath(current_settings['destination'])
    
    this_file =  checkPath(this_file)
    this_path, this_file = path.split(this_file)


    if targets_found:
        print(str(targets_found) +' vertices Modified.  Saving File')
        if current_settings['subfolder'] and not search(r_nif, current_settings['target']) and not search(r_tri, current_settings['target']):
            target_path = checkPath(current_settings['target'])
            """Preserve the relative file structure in the output folder"""
            rel_path = path.relpath(this_path, start=target_path)
            if rel_path != '.':
                output_folder = path.join(destination_path, rel_path)
            else:
                output_folder = destination_path
        else:
            output_folder = destination_path
        if not path.exists(output_folder):
            print ('Folder not found.  Adding ' + output_folder)
            makedirs(output_folder)
            
        print(str(targets_found) +' vertices modified.  Saving '+ this_file + ' to ' + output_folder)
        
        file_name = path.normpath(path.join(output_folder, this_file))
        target_mesh.save(file_name, current_settings, morph_dict = morph_dict)
    else:
        print(str(targets_found) +' vertices modified.  File not Saved')

def swapMorphType(file_):
    if search(r_morph_0, file_):
        return sub(r_morph_0, '_1.nif', file_)
    return sub(r_morph_1, '_0.nif', file_)

def getMorphType(file_):
    if file_:
        if search(r_morph_0, file_):
            return 0
        if search(r_morph_1, file_):
            return 1
    return None

def getGenderFlag(file_):
    if search(r_flag_male, file_):
        return 'MALE'
    if search(r_flag_female, file_):
        return 'FEMALE'
    return 'NONE'

def checkFileType(file_, tri = False):
    if tri:
        if search(r_tri_end, file_) or search(r_nif_end, file_):
            return True
    if search(r_nif_end, file_):
        return True
    return False

def parse_target_files(dirpath):
    if search(r_nif, dirpath) or search(r_tri, dirpath):
        dir_files = sub(r_parse_bracket, '', dirpath)
        dir_files = sub(r_parse_nif_file_spacer, '.nif} {', dir_files)
        dir_files = sub(r_parse_tri_file_spacer, '.tri} {', dir_files)
        dir_files = split(r_parse_file_bracket, dir_files)
        return path.split([path.normpath(sub(r_parse_bracket, '', this_file)) for this_file in dir_files][0])
    else:
        return path.split(dirpath)

def get_files(dirpath, current_settings = {}, tri = False, morph = True):

    """Check for .nif in dirpath"""
    #print(current_settings['target'])
    morph_key = getMorphType(current_settings.get('template'))
    
    if not search(r_nif, dirpath) and not search(r_tri, dirpath):
        if not path.isabs(dirpath):
            dirpath = path.normpath(path.join(i_dir_, dirpath))
        if current_settings.get('subfolder'):
            file_list = [path.normpath(path.join(this_path, this_file)) for this_path, dirnames, filenames in walk(dirpath) for this_file in filenames if checkFileType(this_file, tri)]
        else:
            file_list = [path.normpath(path.join(dirpath, this_file)) for this_file in listdir(dirpath) if checkFileType(this_file, tri)]
    else:
        if search(r_parse_file_spacer2, dirpath):
            file_list = [path.split(sub(r_parse_bracket, '', this_file)) for this_file in eval(dirpath)]
        else:
            #Compensate for multiple TKinter delimiter conventions
            dir_files = sub(r_parse_bracket, '', dirpath)
            dir_files = sub(r_parse_nif_file_spacer, '.nif} {', dir_files)
            dir_files = sub(r_parse_tri_file_spacer, '.tri} {', dir_files)
            dir_files = split(r_parse_file_bracket, dir_files)
            file_list = [path.normpath(sub(r_parse_bracket, '', this_file)) for this_file in dir_files if checkFileType(this_file, tri)]

    if morph:

        morph_set = set()
        
        if morph_key is not None:
            morph_set = set()
            delete_list = list()
            for idx, file_ in enumerate(file_list):
                key_ = search(r_morph_01, file_)
                if not key_:
                    continue
                morph_set.update([key_.group(1)])
                delete_list.append(idx)
            for idx in sorted(delete_list, reverse = True):
                del file_list[idx]
    
        nif_list = [this_file for this_file in file_list if search(r_nif, this_file)]
        if not tri:
            return nif_list, list(morph_set)
        
        tri_list = [this_file for this_file in file_list if search(r_tri, this_file)]
        return nif_list, tri_list, list(morph_set)

    nif_list = [this_file for this_file in file_list if search(r_nif, this_file)]
    if not tri:
        return nif_list
    
    tri_list = [this_file for this_file in file_list if search(r_tri, this_file)]
    return nif_list, tri_list

def createPath(_path):
    _path = path.normpath(_path)
    if not path.exists(_path):
        makedirs(_path)

class load_egm(object):
    def __init__(self, _path, template = None, settings = {}):
        _path = checkPath(_path)
        self.egm_file = open(path.normpath(_path), 'rb')
        self.data = EgmFormat.Data()
        self.data.inspect(self.egm_file)
        self.data.read(self.egm_file)
        self.node_list = list(self.egm_file.data.get_global_child_nodes())

    def save(self, dir_path, file_name, settings = {}):
        self.egm_file.close()
        print('Saving Tri FIle')   
        egm_file = open(path.normpath(path.join(dir_path, file_name)), 'wb')
        self.data.write(egm_file)
        egm_file.close()

class load_tri(object):
    def __init__(self, _path, template = None, settings = {}):
        _path = checkPath(_path)
        self.tri_file = open(path.normpath(_path), 'rb')
        self.data = TriFormat.Data()
        self.data.inspect(self.tri_file)
        self.data.read(self.tri_file)
        self.mesh = kg.mesh_util.mesh(self, False, tri = True)   
        #print(self.data)  

    def save(self, file_name, current_settings = {}, morph_dict = {}):
        #dir_path = checkPath(dir_path)
        self.tri_file.close()
        print('Saving Tri FIle')   
        tri_file = open(file_name, 'wb')
        self.data.write(tri_file)
        tri_file.close()
        
        return

class load_nif(object):
    def __init__(self, _path, template = None, settings = {}, init_skin = True, init_mesh = True):
        _path = checkPath(_path)
        if not path.exists(_path):
            return None

        #print('Path exist', path.exists(_path))
        #print(_path)
        self.path = _path
        self.nif_file = open(path.normpath(_path), 'rb')
        self.data = NifFormat.Data()
        self.data.inspect(self.nif_file)
        try:
            self.data.read(self.nif_file)
            self.valid = True
        except:
            self.valid = False
            return
        self.gender = False
        self.version = {'version': self.data.version, 'user_version': self.data.user_version, 'user_version_2': self.data.user_version_2}
        self.template = template

        #print(self.data.version)
        #print(self.data.user_version)
        #print(self.data.user_version_2)
        
        if settings.get('Game'):
            self.game = settings.get('Game')
            print(self.game)
        else:
            """
            Attempt to determine game from data versions
            If that fails, attempt to determine from template data versions
            if that fails, default to Skyrim
            """
            self.game = kg.data_sets.game_lookup.get((self.data.version, self.data.user_version, self.data.user_version_2))
            if not self.game and self.template:
                self.game = kg.data_sets.game_lookup.get((template.data.version, template.data.user_version, template.data.user_version_2))
            if not self.game:
                self.game = 'Skyrim'                                        
            
        self.root_blocks = self.data.roots
        self.skeleton_root = self.getSkeletonRoots()
        #self.main_root = self.skeleton_root[0]
        for root in self.skeleton_root:
            root.send_geometries_to_bind_position()
            root.send_bones_to_bind_position()
        
        self.meshes = list()
        self.settings = settings
        
        self.bone_struct, self.bone_name_struct = self.getBoneStructure()
    
        self.bone_dict = self.initBones()
        self.skin_dictionary = {}
        
        self.skinned_blocks = []
        self.unskinned_blocks = []
        self.new_skinned_meshes = []
        self.havok_blocks = []
        
        self.nif_type = settings.get('Game')
        
        #self.initBones()
        #self.initSkinDictionary()
        #return        
        #if settings.get('copy_havok'):
        
        if init_skin:
            self.initSkin()
        else:
            self.initMeshes(init_mesh)
 
        if settings.get('bone'):
            self.mend_skin()
             
        if self.settings.get('copy_havok'):
            self.copy_havok()
            
        self.block_dict = {}
        for branch in self.data.get_global_iterator():
            try:
                self.block_dict[branch.name] = branch
            except:
                pass
        self.mesh_dict = dict([(mesh_.block.name, mesh_) for mesh_ in self.meshes])
        
    def __iter__(self):
        for branch in self.data.get_global_iterator():
            yield branch
            
    def rebuildSkinInstance(self):

        bone_set = set()

        delete_rigging = self.settings.get('delete_rigging')
        #print('**********delete_rigging',delete_rigging,'**********')
            
        template_bone_dict = self.template.lno.bone_dict
        """
        Are we copying the rigging from the template or using the existing rigging
        """
        if delete_rigging:
            bone_dict = dict([(bone_name, kg.bone_util.unWrapBone(bone_data)) for bone_name, bone_data in template_bone_dict.items()])
            bone_data = template_bone_dict
            #print('bone_dict', bone_dict)
        else:
            bone_dict = dict([(bone_name, kg.bone_util.unWrapBone(bone_data)) for bone_name, bone_data in self.bone_dict.items()])
            bone_data = self.bone_dict
            for mesh_ in self.meshes:
                mesh_.cleanBUDict() 
                bone_set.update(set(list(mesh_.bone_update_dict.keys())))
            for bone_name in bone_set:
                if bone_name not in bone_dict:
                    bone_dict[bone_name] = kg.bone_util.unWrapBone(template_bone_dict[bone_name])
                    bone_data[bone_name] = template_bone_dict[bone_name]

        self.data = NifFormat.Data()

        self.data.version = self.version['version']
        self.data.user_version = self.version['user_version']
        self.data.user_version_2 = self.version['user_version_2']

#         if self.template:
#             self.data.version = self.template.data.version
#             self.data.user_version = self.template.data.user_version
#             self.data.user_version_2 = self.template.data.user_version_2
#         elif self.game in kg.data_sets.version_data:
#             self.data.version = kg.data_sets.version_data[self.game]['version']
#             self.data.user_version = kg.data_sets.version_data[self.game]['user_version']
#             self.data.user_version_2 = kg.data_sets.version_data[self.game]['user_version_2']
#         else:
#             self.data.version = self.version['version']
#             self.data.user_version = self.version['user_version']
#             self.data.user_version_2 = self.version['user_version_2']

        self.data.roots = [bone_dict[bone_name] for bone_name, b_data in bone_data.items() if b_data.get('is_skel_root')]
    
        
        for ids, bone in enumerate(self.data.roots):
            #print(bone.name)
            child_list = bone_data[bone.name].get('children')
            #print(child_list)
            if not child_list:
                child_list = []
            #print(child_list)
            if not delete_rigging:
                for item in bone_set:
                    if item not in child_list:
                        child_list.append(item)
                #child_list.extend(sorted(list(bone_set)))
            #print(child_list)
            
    
            child_bone_list = [bone_dict.get(child_name) for child_name in child_list if child_name in bone_dict]
            if not delete_rigging:
                other_child_list = [self.block_dict.get(child_name) for child_name in child_list if child_name not in bone_dict and child_name in self.block_dict]
            else:
                other_child_list = [mesh_.block for mesh_ in self.meshes]
            
            for child_block in other_child_list:
                print('Adding Child Block', child_block.name, 'to', bone.name)
                bone.add_child(child_block)
                mesh_ = self.mesh_dict[child_block.name]
                skin_instance = mesh_.skin_type()
                child_block.skin_instance = skin_instance
                skin_instance.data = NifFormat.NiSkinData()
                skin_instance.data.scale = 1.0
                skin_instance.data.rotation = kg.math_util.matrix3x3()
                skin_instance.data.translation = kg.math_util.vector([0,0,0])
#                 skin_instance.data.scale = mesh_.skin_transform['scale']
#                 skin_instance.data.rotation = kg.math_util.matrix3x3(mesh_.skin_transform['rotation'])
#                 skin_instance.data.translation = kg.math_util.vector(mesh_.skin_transform['translation'])
                skin_instance.skeleton_root = bone
                skin_instance.num_bones = 0
                skin_instance.bones.update_size()
                   
            for child_block in child_bone_list:
                print('Adding Child Bone', child_block.name, 'to', bone.name)
                bone.add_child(child_block)
    
        for bone_name, bone_data in bone_data.items():

            child_list = bone_data.get('children')
            if bone_data.get('is_skel_root') or not child_list:
                continue
    
            parent_bone = bone_dict[bone_name]
    
            if child_list:

                child_bone_list = [bone_dict.get(child_name) for child_name in child_list if child_name in bone_dict]
                other_child_list = [self.block_dict.get(child_name) for child_name in child_list if child_name not in bone_dict and child_name in self.block_dict]
                    
                for child_block in child_bone_list:
                    print('Adding Child Block', child_block.name, 'to', parent_bone.name)
                    parent_bone.add_child(child_block)    
                    mesh_ = self.mesh_dict[child_block.name]            
                    skin_instance = mesh_.skin_type()
                    child_block.skin_instance = skin_instance  
                    skin_instance.data = NifFormat.NiSkinData()
#                     skin_instance.data.scale = 1.0
#                     skin_instance.data.rotation = kg.math_util.matrix3x3()
#                     skin_instance.data.translation = kg.math_util.vector([0,0,0])
                    skin_instance.data.scale = mesh_.skin_transform['scale']
                    skin_instance.data.rotation = kg.math_util.matrix3x3(mesh_.skin_transform['rotation'])
                    skin_instance.data.translation = kg.math_util.vector(mesh_.skin_transform['translation'])
                    skin_instance.skeleton_root = parent_bone
                    skin_instance.num_bones = 0
                    skin_instance.bones.update_size() 
                    
    
                    #child_block.update_bind_position()
                for child_block in other_child_list:
                    print('Adding Child Bone', child_block.name, 'to', parent_bone.name)
                    parent_bone.add_child(child_block)            
        
    
        for idx, block in enumerate(self.data.get_global_iterator()):

            if isinstance(block, NifFormat.NiGeometry):
                mesh_ = self.mesh_dict[block.name]
                weight_dict = mesh_.processWeightDictionary()

                for bone_name, wd_ in weight_dict.items():
                    if bone_name not in bone_dict:
                        bone = kg.bone_util.unWrapBone(self.template.lno.bone_dict[bone_name])
                    else:
                        bone = bone_dict[bone_name]
                        
                    block.add_bone(bone, wd_)
                
                if not isinstance(block.skin_instance, NifFormat.BSDismemberSkinInstance):
                    triangles = None
                    trianglepartmap = None
                elif delete_rigging:
                    triangles, trianglepartmap = mesh_.generatePartitionMap()
                else:
                    triangles = mesh_.triangles_
                    trianglepartmap = mesh_.partition_map_
                
                block.update_skin_partition(
                                    maxbonesperpartition=kg.data_sets.part_settings[self.game]['maxbonesperpartition'],
                                    maxbonespervertex=kg.data_sets.part_settings[self.game]['maxbonespervertex'],
                                    padbones=False,
                                    triangles = triangles,
                                    trianglepartmap = trianglepartmap,
                                    stripify = True,
                                    stitchstrips = True, 
                                    maximize_bone_sharing=kg.data_sets.part_settings[self.game]['maximize_bone_sharing']
                                    ) 
                if isinstance(block.skin_instance, NifFormat.BSDismemberSkinInstance):
                    for this_part in block.skin_instance.partitions:
                        if isinstance(block.skin_instance, NifFormat.BSDismemberSkinInstance):
                            for this_part in block.skin_instance.partitions:
                                this_part.part_flag.pf_editor_visible = kg.data_sets.partition_dict[self.game][this_part.body_part]['pf_editor_visible']
                                this_part.part_flag.reserved_bits_1 = kg.data_sets.partition_dict[self.game][this_part.body_part]['reserved_bits_1']
                                this_part.part_flag.pf_start_net_boneset = kg.data_sets.partition_dict[self.game][this_part.body_part]['pf_start_net_boneset']
                            #print(this_part)
                #for i, bone in enumerate(block.skin_instance.bones):
                #    print(i, bone)        
                #print(block.skin_instance.data.bone_list)
                block.update_bind_position()
         
        for root in self.data.roots:
            root.send_geometries_to_bind_position()
            root.send_bones_to_bind_position()

  
    def getGender(self):
        if self.gender is not False:
            return self.gender
        
        if search(r_female, self.path) or search(r_flag_female, self.path):
            self.gender = 'FEMALE'
            return self.gender
        elif search(r_male, self.path) or search(r_flag_male, self.path):
            self.gender = 'MALE'
            return self.gender
        
        for texture in self.getTexturePaths(simple_list = True):
            if search(r_female, self.path):
                self.gender = 'FEMALE'
                return self.gender
            if search(r_male, self.path):
                self.gender = 'MALE'
                return self.gender          
 
        self.gender = 'NONE' 
        return self.gender              
        
        
    def getTexturePaths(self, simple_list = False):
        for branch in self.data.get_global_iterator():
            texture_dict = dict()
            if isinstance(branch, NifFormat.NiGeometry):
                texture_dict[branch.name] = list()
                for block in branch.properties:
                    if isinstance(block, NifFormat.NiTexturingProperty):
                        texture_dict[branch.name].append(getattr(block, 'base_texture').source.file_name.decode("utf-8"))
        if simple_list:
            return [texture for tex_list in self.getTexturePaths().values() for texture in tex_list]
 
        return texture_dict
                        #print(branch.name)
                        #print(getattr(block, 'base_texture').source.file_name.decode("utf-8"))
#                 try:
#                     filename = getattr(block, 'base_texture').source.file_name.decode("utf-8")
#                 except:
#                     filename = False
#                 return filename
# 
#             if isinstance(block, NifFormat.BSShaderTextureSet):
#                 print(block)
                 


    def applyMorphDictionary(self, morph_dictionary):
        for mesh_ in self.meshes:
            v_dict = mesh_.verts
            loc_dict = morph_dictionary.get(mesh_.block.name)
            if not loc_dict:
                continue
            for v_idx, loc_tuple in loc_dict.items():
                #print(v_idx, loc_tuple)
                vert_ = v_dict[v_idx]
                vert_.setLoc(loc_tuple[0], world_loc = False)
                if loc_tuple[1]:
                    vert_.setNormal(loc_tuple[1], world_loc = False)
            mesh_.block.update_tangent_space()
            
    def reBuildBones(self):
        skel_root = self.skeleton_root[0]
        do_once = False
        self.bone_prop_dict = dict()
        for m in self.meshes:
            for bone_name, bone_val in m.bone_dict.items(): 
                if bone_name in self.bone_prop_dict:
                    continue
                self.bone_prop_dict[bone_name] = kg.bone_util.wrapBone(bone_val['bone'])
                continue
        
        for this_mesh in self.meshes:
            if isinstance(this_mesh.block.skin_instance, NifFormat.BSDismemberSkinInstance):
                triangles, this_mesh.partition_map = (this_mesh.block.skin_instance.get_dismember_partitions())
                if not do_once:
                    self.copy_skin_instance(this_mesh.block, skel_root = skel_root)
                    do_once = True
                else:
                    self.copy_skin_instance(this_mesh.block)

    def getDictElements(self, d):
        for key, val in d.items():
            yield key
            if isinstance(val, dict):
                for item in self.getDictElements(val):
                    yield item
            else:
                yield val                    

    def initBones(self):
        struct_dict = self.bone_struct
        print(self.skeleton_root)
        #for bone in self.getDictElements(struct_dict):
        #    print(bone.name)
        #    print(bone)
            
        return dict([(bone.name, kg.bone_util.wrapBone(bone, skel_root = bone in self.skeleton_root)) for bone in self.getDictElements(struct_dict)])
        #$print(self.bone_dict)
    
    def getChildBones(self, bone_struct, bone_name_struct, bone_key_set):
        
        for bone, child_struct in bone_struct.items():
            #Prevent recursion
            if bone in bone_key_set:
                continue
            for child in bone.get_refs():
                if not isinstance(child, NifFormat.NiNode):
                    continue
                bone_key_set.update(bone_key_set)
                child_struct[child] = {}
            #bone_struct[bone.name] = {}
            bone_struct[bone], bone_name_struct[bone.name] = self.getChildBones(child_struct, {} , bone_key_set)
            #bone_name_struct[bone.name] = self.getChildBones(child_name_struct, bone_key_set)
        return bone_struct, bone_name_struct
    
    def getBoneStructure(self):
        r_set = set(self.skeleton_root)
        #print('r_set', r_set)
        bad_roots = set([
             r_1 for r_1 in r_set for r_2 in r_set
             if r_1 is not r_2 and r_1.find_chain(r_2)
             ])
        true_roots = r_set.difference(bad_roots)
        bone_struct = dict([(root, {}) for root in true_roots])
        bone_name_struct = dict([(root.name, {}) for root in true_roots])
        #bone_key_set = set(bone_struct.keys())
        b_dict, b_n_dict = self.getChildBones(bone_struct, bone_name_struct, set())
#         for bone in bone_struct.keys():
#             for child in bone.get_refs():
#                 if not isinstance(child, NifFormat.NiNode):
#                     continue
#                 print(child)
                
                

        #print('bone_key_set', bone_key_set)
        #print('true_roots', true_roots)
        return b_dict, b_n_dict
            
        
    def getSkeletonRoots(self):
        s_roots = set()
        for branch in self.data.get_global_iterator():
            if isinstance(branch, NifFormat.NiGeometry) and branch.skin_instance:
                skelroot = branch.skin_instance.skeleton_root
                if skelroot:
                    s_roots.update([skelroot])
                    #print(s_roots)
        return list(s_roots)
            
    def close(self):
        self.nif_file.close()

    def initMeshes(self, init_mesh):
        for block in self.root_blocks:
            for this_block in [this_block for this_block in block.tree()
            if isinstance(this_block, NifFormat.NiGeometry)]:
                self.meshes.append(kg.mesh_util.mesh(self, this_block, full_init = init_mesh))      
        return
    
    def initSkin(self):
        print('initializing skin')
        for branch in self.data.get_global_iterator():
            if isinstance(branch, NifFormat.NiGeometry) and branch.is_skin():
                if not branch.skin_instance or not branch.skin_instance.data:
                    self.unskinned_blocks.append(branch)
                    print('incomplete skinning detected')
                    continue           
                if self.settings.get('delete_rigging') and self.template:
                    self.unskinned_blocks.append(branch)
                    continue
                try: 
                    branch._validate_skin()
                    self.skinned_blocks.append(branch)
                except: 
                    print('skin failed validation check')
                    
                    if branch.skin_instance == None:
                        print('No Skin Instance')
                        self.unskinned_blocks.append(branch)
                        continue
                    if branch.skin_instance.data == None:
                        print('NiGeometry has NiSkinInstance without NiSkinData')
                        self.unskinned_blocks.append(branch)
                        continue
                        #raise NifFormat.NifError('NiGeometry has NiSkinInstance without NiSkinData')
                    if branch.skin_instance.skeleton_root == None:
                        print('NiGeometry has NiSkinInstance without skeleton root')
                        
                        s_root = self.getSkeletonRoots()
                        if s_root:
                            skelroot = s_root[0]
                            branch.skin_instance.skeleton_root = skelroot
#                             skelroot = s_root[0]
#                             idx = skelroot.num_children
#                             skelroot.num_children += 1
#                             skelroot.children.update_size()
#                             skelroot.children[idx] = branch
                            
                            print(branch.skin_instance.skeleton_root)
                        self.skinned_blocks.append(branch)
                        #raise NifFormat.NifError('NiGeometry has NiSkinInstance without skeleton root')
                    if branch.skin_instance.num_bones != branch.skin_instance.data.num_bones:
                        print('NiSkinInstance and NiSkinData have different number of bones')
                        #raise NifFormat.NifError('NiSkinInstance and NiSkinData have different number of bones')
                    
                    #self.unskinned_blocks.append(branch)
                    #continue
                """
                Check for materials named 'skin'
                """
                if self.settings.get('skin'):

                    material_block = False
                    for prop in branch.properties:
                        if type(prop) == NifFormat.NiMaterialProperty:
                            material_block = prop
                            break
                    if not material_block:
                        print('Block with no Material found, skipping Block')
                        continue
                    mat_name = material_block.name.decode("utf-8")
                    if not search(r_skin, mat_name):
                        
                    #elif material_block.name != bytes('skin', "utf-8"):
                        print('Block with material named ' + material_block.name.decode("utf-8") + ' found, skipping Block')
                        continue
                print('Block Found')
                self.meshes.append(kg.mesh_util.mesh(self, branch)) 

    def mend_skin(self):

        for branch in self.unskinned_blocks:
            
            if not self.template: 
                self.meshes.append(kg.mesh_util.mesh(self, branch, full_init = False))
                continue
            
            self.copy_skin_instance(branch)
            self.skinned_blocks.append(branch) 
            temp_mesh = kg.mesh_util.mesh(self, branch)
            
            self.new_skinned_meshes.append(temp_mesh)
            self.meshes.append(temp_mesh)
            
                
        return
    
    def copy_havok(self):
        
        for block in self.root_blocks:
            for this_block in block.tree():
                if isinstance(this_block, NifFormat.NiStringExtraData):
                    if bytes('Havok', "utf-8") in this_block.name:
                        self.havok_blocks.append(this_block)
                        
        if not self.template:
            return
                
        if self.template.lno.havok_blocks and not self.havok_blocks:
            self.data.roots.add_extra_data(self.template.lno.havok_blocks[0])   

#     def rebuild_skin(self, this_block):
# 
#             block = self.meshes[0].block
#             block._validate_skin()
#             t_skininst = block.skin_instance
#             t_skelroot = t_skininst.skeleton_root
#             skelroot = NifFormat.NiNode()
#             self.data.roots = [skelroot]
#             skelroot.name = t_skelroot.name
#             skelroot.flags = t_skelroot.flags
                
    def copy_skin_instance(self, this_block, skel_root = False):
        
        if skel_root:
            print('Rbuilding Root')
            #block = self.template.block
            #block._validate_skin()
            #t_skininst = block.skin_instance
            t_skelroot = skel_root
            skelroot = NifFormat.NiNode()
            self.data.roots = [skelroot]
            skelroot.name = t_skelroot.name
            skelroot.flags = t_skelroot.flags
                    
        elif not self.skinned_blocks:
            print('Create new root')
            """
            No pre-existing skeleton root.  Create new root
            Grab root data from the template mesh
            """
            block = self.template.block
            block._validate_skin()
            t_skininst = block.skin_instance
            t_skelroot = t_skininst.skeleton_root
            skelroot = NifFormat.NiNode()
            self.data.roots = [skelroot]
            skelroot.name = t_skelroot.name
            skelroot.flags = t_skelroot.flags
            
        else:
            """
            Skeleton Root already exists.  Use existing root
            """
            print('Use Existing Root')
            skelroot = self.skinned_blocks[0].skin_instance.skeleton_root    

#             
#         if isinstance(self.template.block.skin_instance, NifFormat.BSDismemberSkinInstance):
#             skininst = getattr(NifFormat, "BSDismemberSkinInstance")()
#         else:
#             skininst = getattr(NifFormat, "NiSkinInstance")()            

        """
        Now add skeleton root
        """
        print('******adding skeleton root******')
        idx = skelroot.num_children
        skelroot.num_children += 1
        skelroot.children.update_size()
        skelroot.children[idx] = this_block
    
        """
        Now add skin
        """
        if isinstance(self.template.block.skin_instance, NifFormat.BSDismemberSkinInstance):
            skininst = getattr(NifFormat, "BSDismemberSkinInstance")()
        else:
            skininst = getattr(NifFormat, "NiSkinInstance")()
        
        this_block.skin_instance = skininst 
        skininst.data = NifFormat.NiSkinData()
        skininst.skin_partition = getattr(NifFormat, "NiSkinPartition")()
        #skininst.skin_partition = NifFormat.NiSkinPartition()
        skininst.skeleton_root = skelroot
        skininst.num_bones = 0
        skininst.bones.update_size()


    def stripExcessWeights(self):
        for this_mesh in self.meshes:
            #this_mesh.skindata
            #this_mesh.skininst.bones
            boneWeights = this_mesh.skindata.bone_list
            #print(boneWeights)
                
    def save(self, file_name, current_settings = {}, morph_dict = {}):

        """
        Apply Weights and Rebuild skin if needed
        """

        if any([mesh_.bone_update_dict for mesh_ in self.meshes]):
            print('Rebuilding Skin Instances')
            self.rebuildSkinInstance()
            print('Skin Instances Rebuilt')

        """
        Save Main Mesh
        """
        self.nif_file.close()
        print('Saving ', file_name)   
        niffile = open(file_name, 'wb')
        self.data.write(niffile)
        if not morph_dict:
            niffile.close()  
            print('Save Complete') 
            return
        """
        Generate Morph Mesh
        """
        self.applyMorphDictionary(morph_dict)
        morph_file = swapMorphType(file_name)
        print('Saving ', morph_file)   
        niffile = open(morph_file, 'wb')
        self.data.write(niffile)
        niffile.close()
        print('Save Complete')
        
        return

        
#         current_settings['destination'] = checkPath(current_settings['destination'])
#         print(current_settings['destination'])
#         dir_path, file_name = path.split(file_name)
#         print('test_1',dir_path)
#         #for branch in self.data.get_global_iterator():
#         #    if isinstance(branch, NifFormat.NiGeometry) and branch.skin_instance:
#         #        branch.update_bind_position()
# #         skel_root = self.root_blocks[0]
# #         #skel_root.send_geometries_to_bind_position()
# #         skel_root.send_bones_to_bind_position()
#         #update_bind_position
#         if current_settings.get('subfolder'):
#             """Preserve the relative file structure in the output folder"""
#             rel_path = path.relpath(dir_path, start=current_settings['target'])
#             dir_path = path.join(current_settings['destination'], rel_path)
#             
#         else:   
#             dir_path = path.join(current_settings['destination'])
#         print('test_2',dir_path)
#             
#         if not path.exists(dir_path):
#             makedirs(dir_path)
#             print ('Folder not found.  Adding ' + dir_path)
        
#         if self.nif_type == 'Skyrim':
#             max_part_bones = 63
#             max_vert_bones = 4
#             maximize_bone_sharing = False
#         elif self.nif_type == 'Fallout':
#             max_part_bones = 18
#             max_vert_bones = 4
#             maximize_bone_sharing = True
#         else:
#             max_part_bones = 18
#             max_vert_bones = 4
#             maximize_bone_sharing = False
        """
        Check for newly skinned blocks and generate partitions as needed
        """
        #part_dict = {}
        #part_props = {}
        
#         
#         
#         if self.new_skinned_meshes:
#             print('Applying Partitions')
#         for this_mesh in self.meshes:
# 
#             if this_mesh in self.new_skinned_meshes and isinstance(self.template.block.skin_instance, NifFormat.BSDismemberSkinInstance):
#                 partition_map = this_mesh.generatePartitionMap()
#                 part_dict ={}
#                 if current_settings.get('def_partitions'):
#                     part_dict = kg.data_sets.partition_dict.get(self.nif_type)
#                 if not part_dict:
#                     part_props = dict([(this_part.body_part, this_part) for block in self.template.getblocks() for this_part in block.skin_instance.partitions])
# 
#             elif isinstance(this_mesh.block.skin_instance, NifFormat.BSDismemberSkinInstance):
#                 if this_mesh.partition_map:
#                     partition_map = list(this_mesh.partition_map.values())
#                 else:
#                     triangles, partition_map = (this_mesh.block.skin_instance.get_dismember_partitions())
#                 part_dict = kg.data_sets.partition_dict.get(self.nif_type)
# 
#             else:
#                 partition_map = None
#             print('Rebuilding Skin Partition')
#                     #SpellSendBonesToBindPosition
#                     #SpellSendGeometriesToBindPosition    
#             this_mesh.block.update_skin_partition(
#                                 maxbonesperpartition=max_part_bones,
#                                 maxbonespervertex=max_vert_bones,
#                                 padbones=False,
#                                 trianglepartmap=partition_map,
#                                 stripify = False,
#                                 stitchstrips = True,
#                                 maximize_bone_sharing = maximize_bone_sharing) 
#             if part_dict:
#                 for this_part in this_mesh.block.skin_instance.partitions:
#                     t_p_f = part_dict[this_part.body_part]
#                     p_f = this_part.part_flag
#                     p_f.pf_editor_visible = t_p_f['pf_editor_visible']
#                     p_f.reserved_bits_1 = t_p_f['reserved_bits_1']
#                     p_f.pf_start_net_boneset = t_p_f['pf_start_net_boneset']
#             elif part_props:
#                 for this_part in this_mesh.block.skin_instance.partitions:
#                     print (part_dict)
#                     #33: {'pf_editor_visible' : 1, 'reserved_bits_1' : 0, 'pf_start_net_boneset' : 1, 'body_part' : 'SBP_33_HANDS'},\
#                     t_p_f = part_props[this_part.body_part].part_flag
#                     p_f = this_part.part_flag
#                     p_f.pf_editor_visible = t_p_f.pf_editor_visible
#                     p_f.reserved_bits_1 = t_p_f.reserved_bits_1
#                     p_f.pf_start_net_boneset = t_p_f.pf_start_net_boneset
                    #print (t_p_f.pf_start_net_boneset)
                    #print (p_f.pf_start_net_boneset)
                #print(this_mesh.block.skin_instance.partitions)
#             this_mesh.block.update_skin_partition(
#                             maxbonesperpartition = max_part_bones, 
#                             maxbonespervertex = max_vert_bones, 
#                             trianglepartmap = partition_map,
#                             maximize_bone_sharing = True)

#         if self.settings.get('skin'):
# 
#             material_block = False
#             for prop in branch.properties:
#                 if type(prop) == NifFormat.NiMaterialProperty:
#                     material_block = prop
#                     break
#             if not material_block:
#                 print('Block with no Material found, skipping Block')
#                 continue
#             elif material_block.name != bytes('skin', "utf-8"):
#                 print('Block with material named ' + material_block.name.decode("utf-8") + ' found, skipping Block')
#                 continue
#         print('Block Found')
            


        #from pyffi.spells.nif.fix import SpellSendGeometriesToBindPosition, SpellSendDetachedGeometriesToNodePosition, SpellSendBonesToBindPosition
        #from pyffi.spells.nif import NifToaster
        #toaster = NifToaster()
        #toaster.exclude_types = (NifFormat.NiSkinInstance, NifFormat.NiSkinData, NifFormat.NiSkinPartition, NifFormat.BSDismemberSkinInstance)
        #print(test_nif.bone_name_struct)
        #SpellSendGeometriesToBindPosition(data=self.data, toaster=toaster).recurse()
        #SpellSendDetachedGeometriesToNodePosition(data=self.data, toaster=toaster).recurse()
        #SpellSendBonesToBindPosition(data=self.data, toaster=toaster).recurse()
        #SpellSendGeometriesToBindPosition
        #SpellSendDetachedGeometriesToNodePosition

        """
        Apply Weights and Rebuild skin if needed
        """

        if any([mesh_.bone_update_dict for mesh_ in self.meshes]):
            print('Rebuilding Skin Instances')
            self.rebuildSkinInstance()
            print('Skin Instances Rebuilt')

        """
        Save Main Mesh
        """
        self.nif_file.close()
        print('Saving ', file_name)   
        niffile = open(path.normpath(path.join(dir_path, file_name)), 'wb')
        self.data.write(niffile)
        if not morph_dict:
            niffile.close()  
            print('Save Complete') 
            return
        """
        Generate Morph Mesh
        """
        self.applyMorphDictionary(morph_dict)
        morph_file = swapMorphType(file_name)
        print('Saving ', morph_file)   
        niffile = open(path.normpath(path.join(dir_path, morph_file)), 'wb')
        self.data.write(niffile)
        niffile.close()
        print('Save Complete')
        


class config(object):
    def __init__(self, savedir = False, file = 'setings.cfg', version = None):
        global dir_
        if not savedir:
            self.dir_ = dir_
        else:
            self.dir_ = savedir
                
        dir_ = checkPath(dir_)
            
        if not path.exists(self.dir_):
            makedirs(self.dir_)
            
        self.file = path.join(dir_, file)
        #print(self.file)
        self.version = version

    def getSaveSlots(self, rKey = False):
        regKeys = listdir(self.dir_)
        if rKey:
            saveFiles = list(key for key in regKeys if rKey in key and search(progCFG, key) is not None)
        else:
            saveFiles = list(key for key in regKeys if search(progCFG, key) is not None)
        saveSlot = list(sub(progCFG, '', key) for key in saveFiles)
        return saveFiles, saveSlot
    
    def save(self, svReg = False, file = False):
        if not file:
            file = self.file
        if not svReg:
            svReg = kg.ui_tools.svReg
        svReg['VERSION'] = self.version
        pickle.dump(svReg, open(self.file, "wb"))
    
    def load(self, configFile = False, Version = False):
        if not configFile:
            configFile = self.file
        if not Version:
            Version = self.version
        #Check version against registry version.  
        #If they do not match, discard existing configuration information
        try:
            kg.ui_tools.svReg = pickle.load(open(configFile, "rb"))
            if Version:
                if 'VERSION' not in kg.ui_tools.svReg:
                    kg.ui_tools.svReg = dict()
                    kg.ui_tools.svReg['VERSION'] = Version
                elif kg.ui_tools.svReg['VERSION'] != Version:
                    kg.ui_tools.svReg = dict()
                    kg.ui_tools.svReg['VERSION'] = Version
        except:
            kg.ui_tools.svReg = dict()
            if Version:
                kg.ui_tools.svReg['VERSION'] = Version        