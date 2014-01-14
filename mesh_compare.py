import kg
from kg import ui_tools
from kg.template_util import loadSeamTemplate
from kg.file_util import load_nif, config
from kg.search_util import mainSearch, setWeightDictionary, compareMatches
from kg.ui_tools import uiButton, uiToggle, mainUI, uiComboSlider, uiRadio, uiFrame, uiLabel, constructMenu

import tkinter

from os import listdir, path, makedirs, walk
from re import compile, findall, IGNORECASE, split, sub


ui_tools.button_width = 20
ui_tools.entry_width = 5
ui_tools.slider_length = 100

menu = mainUI("Vertex Checker Options")
config_file = 'vertChecker.cfg'

"""
Menu Window Frames
"""

left_frame = uiFrame(menu.frame, column = 0, columnspan = 1, row = 0, rowspan = 6, relief = True)
left_frame.grid(sticky = tkinter.W + tkinter.E + tkinter.N + tkinter.S)
center_frame = uiFrame(menu.frame, column = 1, columnspan = 1, row = 0, rowspan = 6, relief = True)
center_frame.grid(sticky = tkinter.W + tkinter.E + tkinter.N + tkinter.S)
right_frame = uiFrame(menu.frame, column = 2, columnspan = 1, row = 0, rowspan = 6, relief = True)
right_frame.grid(sticky = tkinter.W + tkinter.E + tkinter.N + tkinter.S)
far_right_frame = uiFrame(menu.frame, column = 3, columnspan = 1, row = 0, rowspan = 6, relief = True)
far_right_frame.grid(sticky = tkinter.W + tkinter.E + tkinter.N + tkinter.S)
option_frame = uiFrame(menu.frame, column = 0, columnspan = 3, row = 6, rowspan = 2, relief = True)
option_frame.grid(sticky = tkinter.W + tkinter.E + tkinter.N + tkinter.S)
utility_frame = uiFrame(menu.frame, column = 0, columnspan = 3, row = 8, rowspan = 2, relief = True)
utility_frame.grid(sticky = tkinter.W + tkinter.E + tkinter.N + tkinter.S)

menu.version = 'b_07'
menu.name = 'SeamMender_Options'
menu.file = config_file

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
    {'Process Selected Files Only...' : {'command': menu.SelectTargetFile}}]},\
  ]},\
{'Help': [\
  {"About" : {'command': menu.About}}]}\
]

file_menu = constructMenu(menu, menu_structure, menu.menu_values)

menu.template_mask = mask = [("nif files","*.nif"), ("pkg files","*.pkg")]
menu.target_mask = mask = [("nif files","*.nif"), ("tri files","*.tri"), ("all", "*.*")]

menu.load_buttons({\
     'Distance' : uiComboSlider(left_frame, 'Search Distance', from_ = 0.0, to = 1.0, resolution = .0000000001, tickinterval = .0000001, arrange = 'GRID', col = 0, colspan = 1, row = 1, default = 0.00001, e_width = 20),\
     'loc': uiToggle(center_frame, 'Compare Loc', 'GRID', column = 1, columnspan = 1, row = 2, default = False),\
     'normal': uiToggle(center_frame, 'Compare Normal', 'GRID', column = 2, columnspan = 1, row = 2, default = False),\
     'report': uiToggle(center_frame, 'Report all Verts', 'GRID', column = 1, columnspan = 1, row = 3, default = False),\
     'default': uiButton(utility_frame, 'Load Defaults', 'GRID', column = 1, columnspan = 1, row = 10, buttonFunction = menu.applyDefaultSettings),\
     'cancel': uiButton(utility_frame, 'Cancel', 'GRID', column = 0, columnspan = 1, row = 10, buttonFunction = menu.cancel),\
    'ok': uiButton(utility_frame, 'OK', 'GRID', column = 2, columnspan = 1, row = 10, buttonFunction = menu.ok, sticky = 'E'),\

})

current_settings = menu.openMenu()



# 
# 
# ui_tools.button_width = 20
# ui_tools.entry_width = 5
# ui_tools.slider_length = 100
# 
# menu = mainUI("Vertex Index Tester Options")
# #vertex_frame = uiFrame(menu.frame, column = 0, columnspan = 3, row = 9, rowspan = 2, relief = True)
# menu_frame = uiFrame(menu, column = 0, columnspan = 3, row = 0, rowspan = 6, relief = True)
# menu_frame.grid(sticky = tkinter.W + tkinter.E)
# vertex_frame = uiFrame(menu, column = 0, columnspan = 3, row = 6, rowspan = 2, relief = True)
# print('Default Settings', ui_tools.svReg)
# 
# cfg = config(file = 'vert_checker_ConfigData.cfg', version = 'a_01')
# cfg.load()
# 
# print('Current Settings', ui_tools.svReg)
# 
# menu.menu_values = {\
#     'Game': (tkinter.StringVar(), 'Skyrim'),\
#     'Subfolder': (tkinter.IntVar(), 0),\
#     'template': (tkinter.StringVar(), '/test/template.nif'),\
#     'target': (tkinter.StringVar(), '/test/'),\
#     'destination': (tkinter.StringVar(), '/test/output/'),\
#     }
# 
# """
# Build a dictionary that defines the menu structure
# """
# menu_structure = [
# {'File': [\
#   {"Select Template..." : {'command': menu.OpenTemplate}},\
#   {"Target Mesh Options" : [\
#     {'Select Target Folder...' : {'command': menu.SelectTargetFolder}},\
#     {'Include Subfolders' : {'var': menu.menu_values['Subfolder'] }},\
#     {'Process Selected Meshes Only...' : {'command': menu.SelectTargetFile}}]},\
#   {"Select Destination Folder..." : {'command': menu.SelectDestinationFolder}},\
#   ]},\
# # {'Game': [\
# #   {'Skyrim': {'var': menu.menu_values['Game'][0], 'onvalue': 'Skyrim'}},\
# #   {'Fallout': {'var': menu.menu_values['Game'][0], 'onvalue': 'Fallout'}},\
# #   {'Oblivion': {'var': menu.menu_values['Game'][0], 'onvalue': 'Oblivion'}}]},\
# {'Help': [\
#   {"About" : {'command': menu.About}}]}\
# ]
# 
# file_menu = constructMenu(menu, menu_structure, menu.menu_values)
# #file_menu.newMenu(label_dict, exclusive = True)
# 
# menu.load_buttons({\
# #     'Targets' : uiComboSlider(menu_frame, 'Vertex Targets', from_ = 1, to = 100, resolution = 1, tickinterval = 1, arrange = 'GRID', col = 0, colspan = 1, row = 1, default = 10),\
#      'Distance' : uiComboSlider(menu_frame, 'Search Distance', from_ = 0.0, to = 1.0, resolution = .0000000001, tickinterval = .0000001, arrange = 'GRID', col = 0, colspan = 1, row = 1, default = 0.00001, e_width = 20),\
# #     'override': uiToggle(menu_frame, 'Override Search Distance', 'GRID', column = 0, columnspan = 1, row = 5, default = True),\
# #     #'LEFT': uiToggle(menu.frame, 'Mirror Left to Right', 'GRID', column = 2, columnspan = 1, row = 2, default = False, category = ['LR'], control_E_key = ['LR']),\
# #     #'RIGHT': uiToggle(menu.frame, 'Mirror Right to Left', 'GRID', column = 2, columnspan = 1, row = 3, default = False, category = ['LR'], control_E_key = ['LR']),\
# #     #'NONE': uiToggle(menu.frame, 'No Mirroring', 'GRID', column = 2, columnspan = 1, row = 4, default = True, category = ['LR'], control_E_key = ['LR']),\
# #     'select_bones': uiToggle(menu_frame, 'Select Bones to Copy', 'GRID', column = 1, columnspan = 1, row = 2, default = True),\
# #     'copy_havok': uiToggle(menu_frame, 'Copy Havok node', 'GRID', column = 1, columnspan = 1, row = 3, default = False),\
#      'loc': uiToggle(menu_frame, 'Compare Loc', 'GRID', column = 1, columnspan = 1, row = 2, default = False),\
#      'normal': uiToggle(menu_frame, 'Compare Normal', 'GRID', column = 2, columnspan = 1, row = 2, default = False),\
#      'report': uiToggle(menu_frame, 'Report all Verts', 'GRID', column = 1, columnspan = 1, row = 3, default = False),\
# #     #'mirror' : uiRadio(vertex_frame, 'Mirroring Options',['Mirror Left to Right','Mirror Right to Left','No Mirroring'], column = 0, columnspan = 1, row = 0, rowspan = 8, default = 'No Mirroring'),\
# # 
# #     'save': uiButton(vertex_frame, 'Save Current Settings', 'GRID', column = 0, columnspan = 1, row = 9, buttonFunction = menu.save),\
# #     'load': uiButton(vertex_frame, 'Load Settings', 'GRID', column = 2, columnspan = 1, row = 9, buttonFunction = menu.load),\
#      'default': uiButton(vertex_frame, 'Load Defaults', 'GRID', column = 1, columnspan = 1, row = 10, buttonFunction = menu.applyDefaultSettings),\
#      'cancel': uiButton(vertex_frame, 'Cancel', 'GRID', column = 0, columnspan = 1, row = 10, buttonFunction = menu.cancel),\
#     'ok': uiButton(vertex_frame, 'OK', 'GRID', column = 2, columnspan = 1, row = 10, buttonFunction = menu.ok, sticky = 'E'),\
# })
# 
# current_settings = menu.openMenu()
"""
Short distance search, set targets high to ensure that all verts within search are returned
"""
current_settings['Targets'] = 100
current_settings['res'] = 100
"""
Force script to copy boneweights
"""
current_settings['bone'] = False

try: menu.destroy()
except: menu.end = True

def Main():

    def process_nif(this_path, test_file):
        #return
        if findall(r_nif, test_file) and test_file != current_settings['template']:
            print('Processing', test_file)
            target_nif = load_nif(path.join(this_path, test_file), template = template_mesh, settings = current_settings)
            #target_nif = load_nif(path.join(path, test_file))
            
            targets_found = 0
            for this_mesh in target_nif.meshes:
                mainSearch(current_settings, template_mesh, this_mesh, search_resolution = current_settings['res'], vertFunction = compareMatches)
                print('Displaying Results for', this_mesh.block.name)
                if current_settings.get('report'):
                    for v in this_mesh.verts.values():
                        print(v.idx, 'Exact Match: ', v.exact_match)
                        print('Detail View', v.match_results)
                else:
                    for v in this_mesh.verts.values():
                        if not v.exact_match:
                            print(v.idx, 'Exact Match: ', v.exact_match)
                            print('Detail View', v.match_results)
                            


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
    
    dirpath = current_settings['target']

    r_parse_file_bracket = compile('\}\s\{', flags=IGNORECASE)
    r_parse_file_spacer = compile('\.nif\s', flags=IGNORECASE)
    r_parse_file_spacer2 = compile('\.nif\',\s\'', flags=IGNORECASE)
    r_parse_bracket = compile('[\{\}]', flags=IGNORECASE)

    """Check for .nif in dirpath"""
    print ('dirpath', dirpath)
    if not findall(r_nif, dirpath):
        if current_settings['subfolder']:
            for this_path, dirnames, filenames in walk(dirpath):
                for this_file in filenames:
                    process_nif(this_path, this_file)
        else:
            for test_file in listdir(dirpath):

                process_nif(dirpath, test_file)
    else:
        if findall(r_parse_file_spacer2, dirpath):
            for this_file in eval(dirpath):
                this_path, test_file = path.split(sub(r_parse_bracket, '', this_file))
                process_nif(this_path, this_file)
        else:
            
            dir_files = sub(r_parse_file_spacer, '.nif} {', dirpath)
            dir_files = split(r_parse_file_bracket, dir_files)
            for this_file in dir_files:
                this_path, test_file = path.split(sub(r_parse_bracket, '', this_file))
                process_nif(this_path, test_file)
  

if not menu.end:
    print (ui_tools.svReg)
    menu.save(file = config_file)
    Main()
