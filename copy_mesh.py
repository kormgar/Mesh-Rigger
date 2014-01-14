import kg
from kg import ui_tools
from kg.template_util import loadSeamTemplate
from kg.file_util import load_nif
from kg.ui_tools import uiButton, uiToggle, mainUI, uiFrame, constructMenu

from pyffi.spells.nif.optimize import SpellMergeDuplicates
from pyffi.spells.nif import NifToaster

import tkinter

from os import listdir, path, makedirs, walk
from re import compile, findall, IGNORECASE, split, sub

config_file = 'MeshCopy.cfg'

ui_tools.button_width = 20
ui_tools.entry_width = 5
ui_tools.slider_length = 100

menu = mainUI("Mesh Copy Tool Options")
left_frame = uiFrame(menu, column = 0, columnspan = 3, row = 0, rowspan = 6, relief = True)
left_frame.grid(sticky = tkinter.W + tkinter.E)
utility_frame = uiFrame(menu, column = 0, columnspan = 3, row = 6, rowspan = 6, relief = True)
utility_frame.grid(sticky = tkinter.W + tkinter.E)

menu.version = 'b_13'
menu.name = 'MeshCopy_Options'
menu.file = config_file
#menu.load(file = config_file)

menu.menu_values = {\
    'subfolder': (tkinter.IntVar(), 0),\
    'template': (tkinter.StringVar(), '/test/template.nif'),\
    'target': (tkinter.StringVar(), '/test/'),\
    'destination': (tkinter.StringVar(), '/test/output/'),\
    }

"""
Build a dictionary that defines the menu structure
"""
menu_structure = [
{'File': [\
  {"Select Template..." : {'command': menu.OpenTemplate}},\
  {"Target Mesh Options" : [\
    {'Select Target Folder...' : {'command': menu.SelectTargetFolder}},\
    {'Include Subfolders' : {'var': menu.menu_values['subfolder']}},\
    {'Process Selected Meshes Only...' : {'command': menu.SelectTargetFile}}]},\
  {"Select Destination Folder..." : {'command': menu.SelectDestinationFolder}},\
  ]},\
{'Help': [\
  {"About" : {'command': menu.About}}]}\
]

file_menu = constructMenu(menu, menu_structure, menu.menu_values)
menu.template_mask = mask = [("nif files","*.nif")]
menu.target_mask = mask = [("nif files","*.nif")]

menu.load_buttons({\
    'combine_name': uiToggle(left_frame, 'Combine Names', 'GRID', column = 0, columnspan = 1, row = 1, default = True),\
    'combine_material': uiToggle(left_frame, 'Combine Materials', 'GRID', column = 2, columnspan = 1, row = 1, default = True),\

    'save': uiButton(utility_frame, 'Save Current Settings', 'GRID', column = 0, columnspan = 1, row = 9, buttonFunction = menu.save),\
    'load': uiButton(utility_frame, 'Load Settings', 'GRID', column = 2, columnspan = 1, row = 9, buttonFunction = menu.load),\
    'default': uiButton(utility_frame, 'Load Defaults', 'GRID', column = 1, columnspan = 1, row = 9, buttonFunction = menu.applyDefaultSettings),\
    'cancel': uiButton(utility_frame, 'Cancel', 'GRID', column = 0, columnspan = 1, row = 10, buttonFunction = menu.cancel),\
    'ok': uiButton(utility_frame, 'OK', 'GRID', column = 2, columnspan = 1, row = 10, buttonFunction = menu.ok, sticky = 'E'),\
})

current_settings = menu.openMenu()
print('current_settings',current_settings)

try: menu.destroy()
except: menu.end = True

print('current_settings',current_settings)

def Main():

    def process_nif(this_file):
        #return
        print('Processing', test_file)
        target_nif = load_nif(this_file, template = template_mesh, settings = current_settings, init_skin = True)
        #target_nif = load_nif(path.join(path, test_file))
        target_bone_dict = dict([(bone_name, val['bone'])for this_mesh in target_nif.meshes
        for bone_name, val in this_mesh.bone_dict.items()])
                
        targets_found = 0
        for this_mesh in template_mesh.m_list:
            target_nif.copy_skin_instance(this_mesh.block)
            #list(target_nif.skeleton_root)[0].add_child(this_mesh.block)
            new_mesh = kg.mesh_util.mesh(target_nif, this_mesh.block)
            for bone_name, b in this_mesh.bone_dict.items():
                this_bone = target_bone_dict.get(bone_name, b['bone'])

                new_mesh.addBone( this_bone, dict([(v.index, v.weight) for v in b['weight' ]]))

        if current_settings['subfolder']:
            """Preserve the relative file structure in the output folder"""
            rel_path = path.relpath(this_path, start=current_settings['target'])
            output_folder = path.join(current_settings['destination'], rel_path)
            if not path.exists(output_folder):
                makedirs(output_folder)
                print ('Folder not found.  Adding ' + output_folder)
        else:
            output_folder = current_settings['destination']
            
        if current_settings.get('combine_material'):
            print('Merging Duplicate Blocks')
            toaster = NifToaster()
            SpellMergeDuplicates(data=target_nif.data, toaster=toaster).recurse()
            
        if current_settings.get('combine_name'):
            template_path, template_filename = path.split(current_settings['template'])
            test_file = sub(r_nif, '_', test_file) + template_filename
        target_nif.save(output_folder,test_file)

    r_nif = compile('.ni[f$\}]', flags=IGNORECASE)
    
    if not path.exists(current_settings['destination']):
        print ('destination', current_settings['destination'])
        makedirs(current_settings['destination'])
        
    template_mesh = None
    
    if path.exists(current_settings['template']):
        template_mesh = loadSeamTemplate(current_settings['template'], settings = current_settings)
        if not template_mesh:
            print('No Valid Blocks found on Template Mesh, Exiting')
            return
        """Build a dictionary of all manifold vertices on the mesh"""
        

        #current_settings['bone_list'] = template_mesh.getVerts(side = side)
        #print('Template Found')

    if not template_mesh:
        print('Template Not Found, Exiting')
        return
    
    nif_list = kg.file_util.get_files(current_settings['target'], current_settings, tri = False)
    print(nif_list)
    for this_path, test_file in nif_list:
        print('Processing Files')
        print (this_path, test_file)
        process_nif(this_path, test_file)  

#     dirpath = current_settings['target']
#     
#     print (dirpath)
#     r_parse_file_bracket = compile('\}\s\{', flags=IGNORECASE)
#     r_parse_file_spacer = compile('\.nif\sC', flags=IGNORECASE)
#     r_parse_bracket = compile('[\{\}]', flags=IGNORECASE)
#     
# 
#     """Check for .nif in dirpath"""
#     print ('dirpath', dirpath)
#     if not findall(r_nif, dirpath):
#         #print(dirpath)
#         if current_settings.get('subfolder'):
#             for this_path, dirnames, filenames in walk(dirpath):
#                 for this_file in filenames:
#                     process_nif(this_path, this_file)
#         else:
#             for test_file in listdir(dirpath):
# 
#                 process_nif(dirpath, test_file)
#     else:
#         #dir_files = split(r_parse_file, dirpath)
#         dir_files = sub(r_parse_file_spacer, '.nif} {C', dirpath)
#         dir_files = split(r_parse_file_bracket, dir_files)
#         for this_file in dir_files:
#             print ('this_file', this_file)
#             this_path, test_file = path.split(sub(r_parse_bracket, '', this_file))
#             process_nif(this_path, test_file)
  

if not menu.end:
    menu.save(file = config_file)
    print(current_settings)
    Main()