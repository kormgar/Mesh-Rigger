import kg
from kg import ui_tools
#kg.template_util.loadTemplate('')
from kg.template_util import loadTemplate
from kg.file_util import load_nif, load_tri, get_files, save_file, getGenderFlag
from kg.search_util import mainSearch, setSeams, setTriSeams
from kg.ui_tools import uiButton, uiToggle, mainUI, uiComboSlider, uiRadio, uiFrame, uiLabel, constructMenu
from operator import itemgetter

import re
import tkinter

from os import path, makedirs

r_nif_end = re.compile('\.nif$', flags=re.IGNORECASE)
r_tri_end = re.compile('\.tri$', flags=re.IGNORECASE)

ui_tools.button_width = 20
ui_tools.entry_width = 5
ui_tools.slider_length = 100

menu = mainUI("Seam Mender Options")
config_file = 'SeamMender.cfg'

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

menu.version = 'b_13'
menu.name = 'SeamMender_Options'
menu.file = config_file

menu.menu_values = {\
    'Game': (tkinter.StringVar(), 'Oblivion'),\
    'subfolder': (tkinter.IntVar(), 0),\
    'template': (tkinter.StringVar(), 'Seam Mender/template.nif'),\
    'target': (tkinter.StringVar(), 'Seam Mender/'),\
    'destination': (tkinter.StringVar(), 'Seam Mender/output/'),\
    }

"""
Build a dictionary that defines the menu structure
"""
menu_structure = [
{'File': [\
  {"Select Template..." : {'command': menu.OpenTemplate}},\
  {"Target Mesh Options" : [\
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

menu.template_mask = mask = [("nif files","*.nif"), ("pkg files","*.pkg")]
menu.target_mask = mask = [("nif files","*.nif"), ("tri files","*.tri"), ("all", "*.*")]

menu.load_buttons({\
    'loc': uiToggle(left_frame, 'Location', 'GRID', column = 0, columnspan = 1, row = 0, default = True),\
    'norm': uiToggle(left_frame, 'Normal Vector', 'GRID', column = 0, columnspan = 1, row = 1, default = True),\
    'bone': uiToggle(left_frame, 'Bone Weights', 'GRID', column = 0, columnspan = 1, row = 2, default = True),\
    #'skin': uiToggle(menu, 'Copy Skin Only', 'GRID', column = 0, columnspan = 1, row = 2, default = True),\
#     'uv': uiToggle(menu, 'UV Coordinates', 'GRID', column = 0, columnspan = 1, row = 3, default = False),\
    'Targets' : uiComboSlider(center_frame, 'Vertex Targets', from_ = 1, to = 100, resolution = 1, tickinterval = 1, arrange = 'GRID', col = 0, colspan = 1, row = 1, default = 1),\
    'Distance' : uiComboSlider(center_frame, 'Search Distance', from_ = 0.0, to = 100.0, resolution = .1, tickinterval = .1, arrange = 'GRID', col = 0, colspan = 1, row = 4, default = 0.1),\
    #'template mesh' : uiRadio(menu.frame, 'Template Mesh\nVertex Options',['Edges Only','Exclude Edges','All'], column = 2, columnspan = 1, row = 0, default = 'Exclude Edges'),\
    'label': uiLabel(right_frame, 'Vertex Options', 'GRID', column = 0, columnspan = 1, row = 0),\
    'template_mesh' : uiRadio(right_frame, 'Template Mesh',['Edges Only','Exclude Edges','All'], column = 0, columnspan = 1, row = 1, rowspan = 4, default = 'Edges Only'),\
    'target_mesh' : uiRadio(right_frame, 'Target Mesh',['Edges Only','Exclude Edges','All'], column = 0, columnspan = 1, row = 5, rowspan = 4, default = 'Edges Only'),\
    'gender' : uiRadio(far_right_frame, 'gender',['Female Only','Male Only','Both'], column = 1, columnspan = 1, row = 1, rowspan = 4, default = 'Both', pack = True),\


    'skin': uiToggle(option_frame, 'Copy Skin Only', 'GRID', column = 0, columnspan = 1, row = 0, default = False),\
    'doubles': uiToggle(option_frame, 'Mend Doubles', 'GRID', column = 1, columnspan = 1, row = 0, default = True),\
    'pseudo_doubles': uiToggle(option_frame, 'Mend Pseudo-Doubles', 'GRID', column = 1, columnspan = 1, row = 1, default = False),\
    'tri': uiToggle(option_frame, 'Mend Tri Files', 'GRID', column = 2, columnspan = 1, row = 0, default = True),\
    
    'save': uiButton(utility_frame, 'Save Current Settings', 'GRID', column = 0, columnspan = 1, row = 9, buttonFunction = menu.save),\
    'load': uiButton(utility_frame, 'Load Settings', 'GRID', column = 2, columnspan = 1, row = 9, buttonFunction = menu.load),\
    'default': uiButton(utility_frame, 'Load Defaults', 'GRID', column = 1, columnspan = 1, row = 9, buttonFunction = menu.applyDefaultSettings),\
    'cancel': uiButton(utility_frame, 'Cancel', 'GRID', column = 0, columnspan = 1, row = 10, buttonFunction = menu.cancel),\
    'ok': uiButton(utility_frame, 'OK', 'GRID', column = 2, columnspan = 1, row = 10, buttonFunction = menu.ok, sticky = 'E'),\

})

current_settings = menu.openMenu()

try: menu.destroy()
except: menu.end = True

def Main():

    Female = False
    Male = False
    NoGender = True

    def process_tri(this_file):
        if template_verts:
            print('******TRI******')
            
            mesh_ = template_mesh                         
            verts_ = template_verts
            
            if gender_list or current_settings['gender']:
                """
                Determine Gender of Tri File
                """

                root_nif_path = re.sub(r_tri_end, '.nif', this_file)
                tri_gender = getGenderFlag(root_nif_path)
                if tri_gender is 'NONE' and path.exists(root_nif_path):
                    target_nif = load_nif(root_nif_path, template = False, settings = {})
                    if not target_nif.valid:
                        tri_gender = 'NONE'
                    else:
                        tri_gender = target_nif.getGender()
                if gender_list:
                    mesh_ = template_mesh.get(tri_gender)
                    verts_ = template_verts.get(tri_gender)
                    if not mesh_ or not verts_:
                        print('Incorrect Gender:', this_file )
                        print('Closing', this_file )
                        return
                    
                elif tri_gender != current_settings['gender']:
                    print('Incorrect Gender:', this_file )
                    print('Closing', this_file )
                    return
        
            print('Processing', this_file)

            target_tri = load_tri(this_file, template = template_mesh, settings = current_settings)

            tri_mesh = target_tri.mesh
#             for a in zip(sorted([(vert.idx, vert.getLoc(world_loc = True).as_list()) for vert in tri_mesh.getVerts(nmv = True).values()], key = itemgetter(0)),
#             sorted([(vert.idx, vert.getLoc(world_loc = False).as_list()) for vert in template_mesh.getVerts(nmv = True).values()], key = itemgetter(0))):
#                 print (a)
            
            
            targets_found = mainSearch(current_settings, mesh_, tri_mesh, search_resolution = 1, vertFunction = setTriSeams, nmv = target_nmv, act_verts = verts_, tri = True, world_loc = True)

            save_file(target_tri, this_file, targets_found, current_settings)   

    def process_nif(this_file, repair_doubles = False):
#         if findall(r_nif, test_file) and test_file != current_settings['template']:
        print('******NIF******')
        print('Processing', this_file)

        target_nif = load_nif(this_file, template = template_mesh, settings = current_settings)
        if not target_nif.valid:
            print(target_nif,'Could Not Be Processed')
            return
        nif_gender = target_nif.getGender()
        if gender_list:
            if nif_gender not in gender_list:
                print('Incorrect Gender:', this_file )
                print('Closing', this_file )
                return
            mesh_ = template_mesh.get(nif_gender)
            verts_ = template_verts.get(nif_gender)
        elif nif_gender != current_settings['gender']:
            print('Incorrect Gender:', this_file )
            print('Closing', this_file )
            return
                    
        
        targets_found = 0
        for this_mesh in target_nif.meshes:
            if gender_list:
                targets_found += mainSearch(current_settings, mesh_, this_mesh, search_resolution = 1, vertFunction = setSeams, nmv = target_nmv, act_verts = verts_)
            else:   
                targets_found += mainSearch(current_settings, template_mesh, this_mesh, search_resolution = 1, vertFunction = setSeams, nmv = target_nmv, act_verts = template_verts)       
        if repair_doubles:
            for this_mesh in target_nif.meshes:
                if current_settings.get('doubles'):
                    for tup in this_mesh.nmv_doubles:
                        average_normal = kg.math_util.vector3([0,0,0])
                        bad_normal = 0
                        for v in tup:
                            if v.normal:
                                average_normal += v.normal
                            else:
                                bad_normal += 1
                        if bad_normal == len(tup):
                            continue
                        for v in tup:
                            v.setNormal(kg.math_util.normalizeVector(average_normal))
                            targets_found += 1
        save_file(target_nif, this_file, targets_found, current_settings)
        #target_nif.save(this_file, current_settings)
        #save_file(target_nif, this_file, targets_found, current_settings)           


    
    if not path.exists(current_settings['destination']):
        print ('destination', current_settings['destination'])
        makedirs(current_settings['destination'])
        
    template_mesh = False
    template_verts = {}
    gender_list = []
    
    if path.exists(current_settings['template']):
        template_mesh = loadTemplate(current_settings['template'], settings = current_settings)
        if not template_mesh:
            print('Invalid Template, Exiting')
            return
        print('TEMPLATE MESH', template_mesh)
        gender = False
        if not isinstance(dict, kg.mesh_util.multiMesh):
            print(template_mesh)
            if 'FEMALE' in template_mesh:
                Female = True
                gender_list.append('FEMALE')
            if 'MALE' in template_mesh:
                Male = True
                gender_list.append('MALE')
            if 'NONE' in template_mesh:
                Neutral = True
                gender_list.append('NONE')
                
        """Build a dictionary of all manifold vertices on the mesh"""
        template_nmv = current_settings.get('template_mesh')
        if template_nmv == 'Edges Only':
            template_nmv = True
        elif template_nmv == 'All':
            template_nmv = False
        else:
            template_nmv = 'EXCLUDE'
        print(template_nmv)
        if gender_list:
            template_verts = dict([(gender, template_mesh[gender].getVerts(nmv = template_nmv)) for gender in gender_list])
        else:
            template_verts = template_mesh.getVerts(nmv = template_nmv)
        print('Template Found')

    if not template_mesh and not current_settings.get('doubles'):
        print('Template Not Found, Exiting')
        return
    
    target_nmv = current_settings.get('target_mesh')
    if target_nmv == 'Exclude Edges':
        target_nmv = 'EXCLUDE'
    elif target_nmv == 'All':
        target_nmv = False
    else:
        target_nmv = True

    if current_settings.get('gender') == 'Female Only':
        current_settings['gender'] = 'FEMALE'
    elif current_settings.get('gender') == 'Male Only':
        current_settings['gender'] = 'MALE'
    else:
        current_settings['gender'] = None


    if current_settings['tri']:
        nif_list, tri_list = get_files(current_settings['target'], current_settings, tri = True, morph = False)
        for this_file in nif_list:
            process_nif(this_file, repair_doubles = current_settings.get('doubles'))
        if template_mesh:
            for this_file in tri_list:
                process_tri(this_file)
    else:
        nif_list = get_files(current_settings['target'], current_settings, morph = False)
        for this_file in nif_list:
            process_nif(this_file, repair_doubles = current_settings.get('doubles'))
        
if not menu.end:
    menu.save(file = config_file)
    Main()