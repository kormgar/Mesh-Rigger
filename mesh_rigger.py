import kg
from kg import ui_tools
from kg.template_util import loadTemplate
from kg.file_util import load_nif, config, i_dir_, save_file
from kg.search_util import mainSearch, setWeightDictionary
from kg.ui_tools import uiButton, uiToggle, mainUI, uiComboSlider, uiRadio, uiFrame, uiLabel, constructMenu

import tkinter

from os import listdir, path, makedirs, walk
from re import compile, findall, IGNORECASE, split, sub

config_file = 'MeshRigger.cfg'

ui_tools.button_width = 20
ui_tools.entry_width = 5
ui_tools.slider_length = 100

menu = mainUI("Mesh Rigger Options")
#utility_frame = uiFrame(menu.frame, column = 0, columnspan = 3, row = 9, rowspan = 2, relief = True)
vertex_frame = uiFrame(menu, column = 0, columnspan = 1, row = 0, rowspan = 6, relief = True)
vertex_frame.grid(sticky = tkinter.W + tkinter.E + tkinter.N + tkinter.S)
menu_frame = uiFrame(menu, column = 1, columnspan = 2, row = 0, rowspan = 6, relief = True)
menu_frame.grid(sticky = tkinter.W + tkinter.E + tkinter.N + tkinter.S)
utility_frame = uiFrame(menu, column = 0, columnspan = 3, row = 6, rowspan = 2, relief = True)
utility_frame.grid(sticky = tkinter.W + tkinter.E + tkinter.N + tkinter.S)

#print('Default Settings', ui_tools.svReg)

menu.version = 'b_14'
menu.name = 'MeshRigger_Options'
menu.file = config_file

menu.menu_values = {\
    'Game': (tkinter.StringVar(), 'Skyrim'),\
    'subfolder': (tkinter.IntVar(), 0),\
    'template': (tkinter.StringVar(), 'Mesh Rigger/template.nif'),\
    'template_s': (tkinter.StringVar(), ''),\
    'target': (tkinter.StringVar(), 'Mesh Rigger/'),\
    'destination': (tkinter.StringVar(), 'Mesh Rigger/output/'),\
    'skeleton_links': (tkinter.IntVar(), 1),\
    }

"""
Build a dictionary that defines the menu structure
"""

menu_structure = [
{'File': [\
  {"Template Options" : [\
    {'Select Template Mesh...' : {'command': menu.OpenTemplate}},\
    {'Select Template Skeleton...' : {'command': menu.OpenSkeletonTemplate}},\
    {'Preserve Skeleton Structure' : {'var': menu.menu_values['skeleton_links']}}]},\
  {"Target Options" : [\
    {'Select Target Folder...' : {'command': menu.SelectTargetFolder}},\
    {'Include Subfolders' : {'var': menu.menu_values['subfolder'] }},\
    {'Process Selected Meshes Only...' : {'command': menu.SelectTargetFile}}]},\
  {"Select Destination Folder..." : {'command': menu.SelectDestinationFolder}},\
  ]},\
{'Game': [\
  {'Skyrim': {'var': menu.menu_values['Game'], 'onvalue': 'Skyrim'}},\
  {'Fallout': {'var': menu.menu_values['Game'], 'onvalue': 'Fallout'}},\
  {'Oblivion': {'var': menu.menu_values['Game'], 'onvalue': 'Oblivion'}}]},\
{'Help': [\
  {"About" : {'command': menu.About}}]}\
]

file_menu = constructMenu(menu, menu_structure, menu.menu_values)
menu.template_mask = mask = [("nif files","*.nif")]
menu.target_mask = mask = [("nif files","*.nif")]

menu.load_buttons({\
    'override': uiToggle(vertex_frame, 'Override Distance', 'GRID', column = 0, columnspan = 1, row = 0, default = True),\
    'Distance' : uiComboSlider(vertex_frame, 'Search Distance', from_ = 0.0, to = 100.0, resolution = .1, tickinterval = .1, arrange = 'GRID', col = 0, colspan = 1, row = 1, default = 3),\
    'Targets' : uiComboSlider(vertex_frame, 'Vertex Targets', from_ = 1, to = 100, resolution = 1, tickinterval = 1, arrange = 'GRID', col = 0, colspan = 1, row = 3, default = 5),\
    #'LEFT': uiToggle(menu.frame, 'Mirror Left to Right', 'GRID', column = 2, columnspan = 1, row = 2, default = False, category = ['LR'], control_E_key = ['LR']),\
    #'RIGHT': uiToggle(menu.frame, 'Mirror Right to Left', 'GRID', column = 2, columnspan = 1, row = 3, default = False, category = ['LR'], control_E_key = ['LR']),\
    #'NONE': uiToggle(menu.frame, 'No Mirroring', 'GRID', column = 2, columnspan = 1, row = 4, default = True, category = ['LR'], control_E_key = ['LR']),\
    'select_bones': uiToggle(menu_frame, 'Select Bones to Copy', 'GRID', column =0, columnspan = 1, row = 2, default = True),\
    'copy_havok': uiToggle(menu_frame, 'Copy Havok node', 'GRID', column = 0, columnspan = 1, row = 3, default = False),\
    'delete': uiToggle(menu_frame, 'Overwrite Existing Bones', 'GRID', column = 1, columnspan = 1, row = 2, default = False),\
    'delete_rigging': uiToggle(menu_frame, 'Delete Existing Rigging', 'GRID', column = 1, columnspan = 1, row = 3, default = False),\
    'delete_partitions': uiToggle(menu_frame, 'Delete Existing Partitions', 'GRID', column = 1, columnspan = 1, row = 4, default = False),\
    #'mirror' : uiRadio(utility_frame, 'Mirroring Options',['Mirror Left to Right','Mirror Right to Left','No Mirroring'], column = 0, columnspan = 1, row = 0, rowspan = 8, default = 'No Mirroring'),\

    'save': uiButton(utility_frame, 'Save Current Settings', 'GRID', column = 0, columnspan = 1, row = 9, buttonFunction = menu.save),\
    'load': uiButton(utility_frame, 'Load Settings', 'GRID', column = 2, columnspan = 1, row = 9, buttonFunction = menu.load),\
    'default': uiButton(utility_frame, 'Load Defaults', 'GRID', column = 1, columnspan = 1, row = 9, buttonFunction = menu.applyDefaultSettings),\
    'cancel': uiButton(utility_frame, 'Cancel', 'GRID', column = 0, columnspan = 1, row = 10, buttonFunction = menu.cancel),\
    'ok': uiButton(utility_frame, 'OK', 'GRID', column = 2, columnspan = 1, row = 10, buttonFunction = menu.ok, sticky = 'E'),\
})

current_settings = menu.openMenu()
"""
Force script to copy boneweights
"""
current_settings['bone'] = True

try: menu.destroy()
except: menu.end = True

side = current_settings.get('mirror')
if side == 'Mirror Left to Right':
    side = 'LEFT'
elif side == 'Mirror Right to Left':
    side = 'RIGHT'
else:
    side = False
#print('side', side)


def Main():
    print (current_settings.get('Game'))
    def process_morph(test_file, bone_list, morph_dict):
        print('Processing', test_file)
        target_nif = load_nif(test_file, template = template_mesh, settings = current_settings)
        if not target_nif.valid:
            print(test_file,'Could Not Be Processed')
            return
        
        targets_found = 0
        for this_mesh in target_nif.meshes:
            targets_found += mainSearch(current_settings, template_mesh, this_mesh, search_resolution = 1, vertFunction = setWeightDictionary, side = side)
            
        save_file(target_nif, test_file, targets_found, current_settings, morph_dict = morph_dict)
            
    def process_nif(test_file, bone_list):
        print('Processing', test_file)
        target_nif = load_nif(test_file, template = template_mesh, settings = current_settings)
        if not target_nif.valid:
            print(test_file,'Could Not Be Processed')
        
        targets_found = 0
        for this_mesh in target_nif.meshes:
            targets_found += mainSearch(current_settings, template_mesh, this_mesh, search_resolution = 1, vertFunction = setWeightDictionary, side = side)

        save_file(target_nif, test_file, targets_found, current_settings)
    
    if not path.exists(current_settings['destination']):
        makedirs(current_settings['destination'])
        
    template_mesh = None
    
    if path.exists(current_settings['template']):
        template_mesh = loadTemplate(current_settings['template'], settings = current_settings)
        if not template_mesh:
            print('No Valid Blocks found on Template Mesh, Exiting')
            return
        skeleton = current_settings.get('template_s')
        template_mesh.loadSkeleton(skeleton)
    
        bone_list = current_settings['bone_list'] = sorted(list(template_mesh.bone_dict.keys()))
        #print(bone_list)
        if current_settings['select_bones']:
            bone_menu = ui_tools.boneMenu(bone_list, side = side)
            current_settings['bone_list'] = bone_menu.openMenu()
            #print (bone_list)
            try: bone_menu.destroy()
            except: pass

    if not template_mesh:
        print('Template Not Found, Exiting')
        return

    if current_settings.get('template_s'):
        print('Generating Bone Dictionary from Skeleton')
        skeleton = kg.file_util.load_nif(current_settings['template_s'], settings = current_settings, skeleton_only = True)
        for b_data in skeleton.bone_dict.values():
            if b_data.get('is_skel_root'):
                root = b_data
                break
                
        for bone_name, bone_data in template_mesh.lno.bone_dict.items():
            if bone_name not in skeleton.bone_dict and not bone_data.get('is_skel_root'):
                skeleton.bone_dict[bone_name] = bone_data
                root['children'].append(bone_name)
        template_mesh.lno.bone_dict = skeleton.bone_dict

        print('Skeleton Dictionary Generation Complete')

    nif_list, morph_set = kg.file_util.get_files(current_settings['target'], current_settings, tri = False)
    for test_file in nif_list:
        #print('test_file, test_file')
        process_nif(test_file, bone_list)
    if morph_set:
        morph_key = kg.file_util.getMorphType(current_settings.get('template'))
        if morph_key == 0:
            base = '_0.nif'
            morph = '_1.nif'
        else:
            base = '_1.nif'
            morph = '_0.nif'
        for this_morph in morph_set:
            base_file = this_morph + base
            morph_file = this_morph + morph
            #print(morph_file)
            morph_dict = {}
            print(morph_file)
            if path.exists(morph_file):
                morph_nif = load_nif(morph_file, template = False, settings = current_settings, init_skin = False, init_mesh = False)
                morph_dict = {}
                for mesh_ in morph_nif.meshes:
                    #print(mesh_.block.name)
                    morph_dict[mesh_.block.name] = dict([(v_idx, (vert_.getLoc(world_loc = False), vert_.getNormal(world_loc = False))) for v_idx, vert_ in mesh_.verts.items()])
                morph_nif.nif_file.close()    
            #print(morph_dict)
            process_morph(base_file, bone_list, morph_dict)

if not menu.end:
    menu.save(file = config_file)
    Main()
