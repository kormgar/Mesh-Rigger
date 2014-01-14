import kg

#kg.esp_util.f

#import kg
from kg import ui_tools
#kg.template_util.loadSeamTemplate('')
from kg.template_util import loadSeamTemplate, loadTemplate
#from kg.file_util import load_nif, load_tri, get_files, save_file
#from kg.search_util import mainSearch, setSeams, setTriSeams
from kg.ui_tools import uiButton, uiToggle, mainUI, uiComboSlider, uiRadio, uiFrame, uiLabel, constructMenu
#from operator import itemgetter

from pyffi.formats.nif import NifFormat

import tkinter
import re
from os import path, makedirs

ui_tools.button_width = 20
ui_tools.entry_width = 5
ui_tools.slider_length = 100

menu = mainUI("ESP Reader Options")
config_file = 'esp_reader.cfg'

r_nif_end = re.compile('.nif$', flags=re.IGNORECASE)


"""
Menu Window Frames
"""

# left_frame = uiFrame(menu.frame, column = 0, columnspan = 1, row = 0, rowspan = 6, relief = True)
# left_frame.grid(sticky = tkinter.W + tkinter.E + tkinter.N + tkinter.S)
# right_frame = uiFrame(menu.frame, column = 1, columnspan = 2, row = 0, rowspan = 6, relief = True)
# right_frame.grid(sticky = tkinter.W + tkinter.E + tkinter.N + tkinter.S)
option_frame = uiFrame(menu.frame, column = 0, columnspan = 3, row = 6, rowspan = 2, relief = True)
option_frame.grid(sticky = tkinter.W + tkinter.E + tkinter.N + tkinter.S)
utility_frame = uiFrame(menu.frame, column = 0, columnspan = 3, row = 8, rowspan = 2, relief = True)
utility_frame.grid(sticky = tkinter.W + tkinter.E + tkinter.N + tkinter.S)

menu.version = 'a_01'
menu.name = 'exp_reader_Options'
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
  {"Select esp/esm..." : {'command': menu.OpenTemplate}},\
  #{"Select Destination Folder..." : {'command': menu.SelectDestinationFolder}},\
  ]},\
{'Help': [\
  {"About" : {'command': menu.About}}]}\
]

file_menu = constructMenu(menu, menu_structure, menu.menu_values)

menu.template_mask = mask = [("Oblivion Files","*.esm"), ("Oblivion Files","*.esp")]
#menu.target_mask = mask = [("nif files","*.nif"), ("tri files","*.tri")]

menu.load_buttons({\
# #     'loc': uiToggle(left_frame, 'Location', 'GRID', column = 0, columnspan = 1, row = 0, default = True),\
# #     'norm': uiToggle(left_frame, 'Normal Vector', 'GRID', column = 0, columnspan = 1, row = 1, default = True),\
# #     'bone': uiToggle(left_frame, 'Bone Weights', 'GRID', column = 0, columnspan = 1, row = 2, default = True),\
# 
#     'template_mesh' : uiRadio(option_frame, 'Template Mesh',['Edges Only','Exclude Edges','All'], column = 0, columnspan = 1, row = 1, rowspan = 4, default = 'Exclude Edges', pack = True),\
#     #'target_mesh' : uiRadio(right_frame, 'Target Mesh',['Edges Only','Exclude Edges','All'], column = 0, columnspan = 1, row = 5, rowspan = 4, default = 'Edges Only'),\
#     
#     'save': uiButton(utility_frame, 'Save Current Settings', 'GRID', column = 0, columnspan = 1, row = 9, buttonFunction = menu.save),\
#     'load': uiButton(utility_frame, 'Load Settings', 'GRID', column = 2, columnspan = 1, row = 9, buttonFunction = menu.load),\
#     'default': uiButton(utility_frame, 'Load Defaults', 'GRID', column = 1, columnspan = 1, row = 9, buttonFunction = menu.applyDefaultSettings),\
    'cancel': uiButton(utility_frame, 'Cancel', 'GRID', column = 0, columnspan = 1, row = 10, buttonFunction = menu.cancel),\
    'ok': uiButton(utility_frame, 'OK', 'GRID', column = 2, columnspan = 1, row = 10, buttonFunction = menu.ok, sticky = 'E'),\

})

current_settings = menu.openMenu()
print(current_settings)

try: menu.destroy()
except: menu.end = True

def Main():
    
#     if not path.exists(current_settings['destination']):
#         print ('destination', current_settings['destination'])
#         makedirs(current_settings['destination'])
    kg.esp_util.getArmorPaths(current_settings['template'])
    #kg.template_util.saveTemplate(current_settings)
    
    return
        
if not menu.end:
    menu.save(file = config_file)
    Main()