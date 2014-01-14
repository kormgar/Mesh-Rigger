#import tkinter
#from tkinter import ttk
from math import ceil, sqrt
import re

import tkinter
from tkinter import ttk, W, N, S, E
from tkinter import filedialog

from os import path

import kg
#from tkinter.filedialog import askopenfilename

cmpCancel = re.compile('cancel',flags = re.IGNORECASE)
cmpOK = re.compile('ok',flags = re.IGNORECASE)
cmpDefault = re.compile('default',flags = re.IGNORECASE)

global svReg
svReg = dict()

#default_paths = {'template': '/test/template.nif','target': '/test/', 'destination': '/test/output/', 'subfolder': 0}

global button_width
global entry_width
global slider_length
global control_dictionary

button_width = 20
entry_width = 3
slider_length  = 20
control_dictionary = dict()

class boneMenu(tkinter.Tk):
    def __init__(self, bone_list, title = "Select Bones To Copy", style = "classic", side = False):
        tkinter.Tk.__init__(self)

        self.title = title
        self.style = ttk.Style()
        self.style.theme_use(style)
        self.style.configure('button_on.TButton', relief = tkinter.SUNKEN)
        self.style.configure('button_off.TButton', relief = tkinter.RAISED)        
        #bone_list = list(template_mesh.bone_dict.keys())
        num_bones = len(bone_list)
        sqrt_bones = sqrt(num_bones)
        c = 0
        c_max = int(ceil(sqrt_bones * .8))
        r = 0
        r_max = int(ceil(sqrt_bones * 1.25))
        self.frame_1 = ttk.Frame(self, relief = tkinter.GROOVE, padding = 1.3)
        self.frame_1.grid(column = 0, columnspan = c_max, row = 0, rowspan = r_max)
        
        self.buttons = {}
        get_side = kg.bone_util.getBoneSide
        for this_bone in bone_list:
            if side:
                bone_side = get_side(this_bone.decode("utf-8"))
                #print (bone_side)
                if bone_side and bone_side not in side:
                    continue
            self.buttons[this_bone] = uiToggle(self.frame_1, this_bone.decode("utf-8"), 'PACK', default = True)
            self.buttons[this_bone].grid(column = c, row = r)
            r += 1
            if r >= r_max:
                r = 0
                c += 1
            
        self.frame_2 = ttk.Frame(self, relief = tkinter.GROOVE, padding = 1.3)
        self.frame_2.grid(column = 0, columnspan = c_max, row = r_max + 1)
        
        uiButton(self.frame_2, 'OK', 'GRID', column = 2, columnspan = 1, row = 8, buttonFunction = self.ok, sticky = 'E')

    def ok(self):
        self.quit()      
 
    def bone_list(self):
        return [this_bone for this_bone, button in self.buttons.items() if button.getVal(this_bone)]
               
    def openMenu(self):
        self.mainloop()
        return self.bone_list()

class mainUI(tkinter.Tk):
    
    def __init__(self, title, style = "classic"):
        tkinter.Tk.__init__(self)
        
        self.version = None
        self.name = 'Main Menu'       
        self.title(title)
        self.style = ttk.Style()
        self.style.theme_use(style)
        self.style.configure('button_on.TButton', relief = tkinter.SUNKEN)
        self.style.configure('button_off.TButton', relief = tkinter.RAISED)
        self.style.configure('slider.Horizontal.TScale', length = slider_length)
        self.frame = uiFrame(self, arrange = 'GRID')
        self.menu_values = {}
        self.file = 'default.cfg'
        self.cfg = False
        self.buttons = {}
        self.end = False
        self.reg = {}
        self.template_mask = [('all files', '.*')]
        self.target_mask = [('all files', '.*')]
         
    def openMenu(self):
        if not self.load(file = self.file):
            self.applyDefaultSettings()
        self.mainloop()
        return self.getReg()

    def load(self, save_dir = False, file = False):

        r_parse_file_number = re.compile('[0-9]', flags=re.IGNORECASE)
        r_parse_file_float = re.compile('[0-9]\.[0-9]', flags=re.IGNORECASE)
        r_parse_file_text = re.compile('[a-z]', flags=re.IGNORECASE)
        r_parse_file_delimiter = re.compile('=', flags=re.IGNORECASE)
        r_parse_file_space = re.compile('^\s|$\s', flags=re.IGNORECASE)

        if not save_dir:
            save_dir = kg.file_util.dir_

        if file:
            file_path = path.normpath(path.join(save_dir, file))
            if not path.exists(file_path):
                return False
            save_file = open(file_path, 'r')
        else:
            mask = [("config files","*.ini")]
            
            save_file = tkinter.filedialog.askopenfile(
            initialdir = save_dir,
            defaultextension = ".ini",
            filetypes = mask)
        if not save_file:
            return False
        print('loading settings from', save_file.name)
        test_reg = {}
        try:
            test_reg = dict(list(re.sub(r_parse_file_space, '', val) for val in list(re.split(r_parse_file_delimiter, line)))[0:2] for line in save_file)
        except:
            print('Invalid save file detected, aborting')
            save_file.close()
            return False
        """
        Identify type of save variables and convert from string as needed
        """
        for key, val in list(test_reg.items()):
            if not re.search(r_parse_file_text, val):
                if re.search(r_parse_file_float, val):
                    #print ('float', key, val)
                    test_reg[key] = float(val)
                elif re.search(r_parse_file_number, val):
                    #print('int', key, val)
                    test_reg[key] = int(val)
            else:
                if val == str(True) or val == str(False) or val == str(None):
                    test_reg[key] = eval(val)
        _version = test_reg.get('version', False)
        _name = test_reg.get('name', False)

        if _version is False or _name is False:
            print('Invalid save file detected, aborting')
            
        if _version != self.version:
            print('Version mismatch in save file detected, aborting')
            return False
        if _name != self.name:
            print('Tool Name mismatch in save file detected, aborting')
            return False

        key_list = ['template', 'destination']
        for key in key_list:
            tplt = test_reg.get(key)
            #print(tplt)
            #if tplt and not path.isabs(tplt):
            #    test_reg[key] = path.normpath(path.join(kg.file_util.i_dir_, tplt))

        global svReg
        svReg = test_reg
        self.applySavedSettings(test_reg)
        save_file.close()
        return True
        
    def save(self, save_dir = False, file = False):
        
        if not save_dir:
            save_dir = kg.file_util.dir_
        else:
            save_dir = kg.file_util.checkPath(save_dir)
            
        if file:
            save_file = open(path.normpath(path.join(save_dir, file)), 'w')
        else:
            mask = [("config files","*.ini")]
            
            save_file = tkinter.filedialog.asksaveasfile(
            initialdir = save_dir,
            defaultextension = ".ini",
            filetypes = mask)
            if not save_file:
                return

        file_string = str('version'+'='+str(self.version)+'\n'+'name'+'='+str(self.name)+'\n')
        for key, val in sorted(list(self.getReg().items())):
            file_string += (str(key)+'='+str(val) + '\n')
        save_file.write(file_string)
        #print (file_string)
        save_file.close()

        return
    
    def applyDefaultSettings(self):
        #self.reg = default_paths
        for key, button in self.buttons.items():
            button.setDefault(key)

    def applySavedSettings(self, test_reg = {}):
        if test_reg:
            self.reg = test_reg
        else:
            self.reg = {}
        #print(self.buttons)
        for key, button in self.buttons.items():
            #print(key)
            button.setSavedValue(key)
        for key, val in self.menu_values.items():
            if self.reg.get(key) is not None:
                val[0].set(self.reg.get(key))

    def load_buttons(self, button_dictionary):
        for key, button in button_dictionary.items():
            self.buttons[key] = button
         
    def getVal(self, key = None):
        return self.buttons[key].getVal(key)
     
    def getReg(self):
        #print('before', self.reg)
        for key, button in self.buttons.items():
            button_type = type(button)
            if button_type is uiButton or button_type is uiLabel:
                continue
            if button_type is constructMenu:
                for key, val in button.getVal():
                    self.reg[key] = val
                continue
            self.reg[key] = self.getVal(key)

        #print('after', self.reg)
        return self.reg
        
    def setEnd(self, val):
        self.end = val

    def cancel(self):
        self.setEnd(True)
        self.quit()
 
    def ok(self):
        self.quit()

    def OpenFemaleTemplate(self):
        self.OpenFile(self.menu_values.get('female_template')[0])

    def OpenMaleTemplate(self):
        self.OpenFile(self.menu_values.get('male_template')[0])

    def OpenTemplate(self):
        self.OpenFile(self.menu_values.get('template')[0])

    def OpenFile(self, var_):
        file_path, file = path.split(var_.get())
        template = kg.file_util.checkPath(file_path)
        if path.exists(template):
            template_file = tkinter.filedialog.askopenfilename(initialdir = template, filetypes = self.template_mask)
        else:
            template_file = tkinter.filedialog.askopenfilename(filetypes = self.template_mask)
        if template_file:
            var_.set(template_file)
 
    def SelectTargetFile(self):
        
        dirpath = self.menu_values.get('target')[0].get()
        file_path, file_ = kg.file_util.parse_target_files(dirpath)
        
        #path_ = kg.file_util.get_files(self.menu_values.get('target')[0].get(), current_settings = {}, tri = False, morph = False)[0]
        #file_path, file_ = path.split(path_)
        target = kg.file_util.checkPath(file_path)
        #target = self.menu_values.get('target')[0].get()
        print('initialdir', target)
        if path.exists(target):
            target_files = tkinter.filedialog.askopenfilenames(initialdir = target)
        else:
            target_files = tkinter.filedialog.askopenfilenames()
        #target_files = tkinter.filedialog.askopenfilenames(initialdir = target, filetypes = self.target_mask)
        if target_files:
            self.menu_values['target'][0].set(target_files)
            #self.reg['target'] = target_files

    def SelectTargetFolder(self):
        dirpath = self.menu_values.get('target')[0].get()
        file_path, file_ = kg.file_util.parse_target_files(dirpath)
        
        
        #path_ = kg.file_util.get_files(self.menu_values.get('target')[0].get(), current_settings = {}, tri = False, morph = False)[0]
        #file_path, file = path.split(path_)
        target = kg.file_util.checkPath(file_path)
        if path.exists(target):
            target_folder = tkinter.filedialog.askdirectory(initialdir = target)
        else:
            target_folder = tkinter.filedialog.askdirectory()

        print('initialdir', target)
        if target_folder:
            self.menu_values['target'][0].set(target_folder)
            #self.reg['target'] = target_folder

    def SelectDestinationFolder(self):
        file_path, file = path.split(self.menu_values.get('destination')[0].get())
        destination = path.normpath(file_path)
        print('initialdir', destination)
        if path.exists(destination):
            destination_folder = tkinter.filedialog.askdirectory(initialdir = destination)
        else:
            destination_folder = tkinter.filedialog.askdirectory()
            
        #destination = self.menu_values.get('destination')[0].get()
        if destination_folder:
            self.menu_values['destination'][0].set(destination_folder)
            #self.reg['destination'] = destination_folder
    
    def About(self):
        print ("Menu Test Response")

    def searchSubFolder(self):
        if self.reg.get('subfolder', tkinter.IntVar()).get():
            self.reg['subfolder'].set(0)
        else:
            self.reg['subfolder'].set(1)


class constructMenu(tkinter.Menu):
    def __init__(\
    self,\
    master,\
    menu_structure = {},\
    menu_values = {}\
    ):  
        tkinter.Menu.__init__(self, master)
        self.master= master
        self.master.config(menu = self)
        self.menu_dict = {}
        self.var_dict = {}
        self.menu_values = menu_values
        self.master.buttons['menu'] = self
        self.processMenu(menu_structure)
        self.setDefault()

    def setSavedValue(self, key = None):
        for k, val in self.menu_values.items():
            reg_val = self.master.reg.get(k)
            #print(reg_val)
            if reg_val is not None:
                val[0].set(reg_val)
                continue
            val[0].set(val[1])        

    def getVal(self, key = None):
        if key is not None:
            if key not in self.menu_values:
                yield None
            yield self.menu_values.get(key)[0].get()
        for key, item in self.menu_values.items():
            val = item[0].get()
            yield (key, val)

    def setDefault(self, key = None):
        if key != 'menu':
            item = self.menu_values.get(key)
            if item:
                item[0].set(item[1])
            return
        for val in self.menu_values.values():
            val[0].set(val[1])
        return
    
    def processMenu(self, menu_structure, parent_menu = None):
        #print (parent_menu)
        #print (menu_structure)
        if isinstance(menu_structure, list):
            for menu_item in menu_structure:
                for menu_label, menu_contents in menu_item.items():
                    #print (menu_label)
                    #print (menu_item)
                    if not parent_menu:
                        #print('Adding New Menu')
                        self.menu_dict[menu_label] = tkinter.Menu(self, tearoff=0)
                        self.add_cascade(label = menu_label, 
                        menu = self.menu_dict[menu_label])
                        self.processMenu(menu_contents, self.menu_dict[menu_label])
                    elif isinstance(menu_contents, list):
                        self.menu_dict[menu_label] = tkinter.Menu(self, tearoff=0)
                        parent_menu.add_cascade(label = menu_label,
                        menu = self.menu_dict[menu_label]) 
                        self.processMenu(menu_contents, self.menu_dict[menu_label])
                    elif 'command' in menu_contents:
                        #print ('command')
                        parent_menu.add_command(label = menu_label,
                        command = menu_contents['command'])
                    elif 'var' in menu_contents:
                        onvalue = menu_contents.get('onvalue', 1)
                        #print('onvalue', onvalue)
                        parent_menu.add_checkbutton(label = menu_label,
                        variable = menu_contents['var'][0],
                        onvalue = onvalue)
                        #print('var')
        return

class uiMenu(tkinter.Menu):    
    def __init__(\
        self,\
        master,\
        var_dict = {},\
        default_dict = {}\
    ):
        tkinter.Menu.__init__(self, master)
        master.config(menu = self)
        self.root = master
        if var_dict:
            self.var_dict = var_dict
        else:
            self.var_dict = {'subfolder' : tkinter.IntVar()}
        if default_dict:
            self.default_dict = default_dict
        else:
            self.default_dict = {'subfolder' : 0}

        for key in self.var_dict:
            master.buttons[key] = self
        #$menu_dict = {'File': tkinter.Menu(self, tearoff=0), 'About': tkinter.Menu(self, tearoff=1)}
        filemenu = tkinter.Menu(self, tearoff=0)
        self.add_cascade(label="File", menu=filemenu)
        #filemenu.add_command(label="New", command=self.NewFile)
        filemenu.add_command(label="Select Template...", command=self.root.OpenTemplate)
        target_folder = tkinter.Menu(self, tearoff=0)
        #sourceFolder.add_command(label="Source Mesh Options")
        target_folder.add_command(label="Select Target Folder...", command=self.root.SelectTargetFolder)
        target_folder.add_checkbutton(label = "Include Subfolders", variable = self.var_dict['subfolder'])
        target_folder.add_command(label="Process Selected Meshes Only", command=self.root.SelectTargetFile)
        filemenu.add_cascade(label="Target Mesh Options", menu=target_folder)        
        #filemenu.add_command(label="Select Source Folder...", command=self.root.SelectSourceFolder)
        filemenu.add_command(label="Select Destination Folder...", command=self.root.SelectDestinationFolder)
        filemenu.add_separator()
        filemenu.add_command(label="Quit", command=self.root.cancel)

        helpmenu = tkinter.Menu(self)
        self.add_cascade(label="Help", menu=helpmenu)
        helpmenu.add_command(label="About", command=self.root.About)

    def newMenu(self, label_dict, exclusive):
        return


    def setSavedValue(self, key):
        if key not in self.var_dict:
            return
        default_setting = self.default_dict.get(key, None)
        #print (default_setting)
        if default_setting is not None:
            
            #if key in svReg:
            #    print (svReg[key])
            self.var_dict[key].set(svReg.get(key, default_setting))
        elif key in svReg:
            self.var_dict[key].set(svReg[key])            

    def setDefault(self, key):
        if key in self.default_dict and key in self.var_dict:
            self.var_dict[key].set(self.default_dict[key])

    def getVal(self, key):
        if key in self.var_dict:
            return self.var_dict[key].get()
        return None

class uiRadio(ttk.Frame):
    
    def __init__(\
        self,\
        master,\
        label,\
        button_list = [],\
        column = 0,\
        columnspan = 1,\
        row = 0,\
        rowspan = 1,\
        default = None,\
        pack = False
    ):
        ttk.Frame.__init__(self, master)  
        self.button_dict = {}
        self.val = tkinter.StringVar()
        self.default = default
        self.root = master
        if pack:
            self.pack()
        else:
            self.grid(column = column, columnspan = columnspan, row = row, rowspan = rowspan)
        x = 0
        
        self.lbl = uiLabel(\
            self,\
            label,\
            arrange = 'GRID',\
            column = 0,\
            columnspan = 1,\
            row = 0,\
            width = len(label)
        )
           
        self.lbl.grid(column = 0, row = 0, columnspan = len(button_list), sticky = W + E + N + S)
        
        for key in button_list:
            x += 1
            #print (key)
            self.button_dict[key] = tkinter.Radiobutton(self, text = key, variable = self.val, value = key, indicatoron = False, width = 15, height = 1)
            self.button_dict[key].grid(column = 0, row = x, sticky = W + E + N + S)
            
    
    def setSavedValue(self, key):
        #print('Radio', key, svReg.get(key))
        if self.default is not None:
            self.setVal(svReg.get(key, self.default))
        elif key in svReg:
            self.setVal(svReg[key])
    
    def getVal(self, key):
        #print ('radio', self.val.get())
        return self.val.get()

    def setVal(self, val):
        self.val.set(val)
 
    def setDefault(self, key = None):
        if self.default is not None:
            self.setVal(self.default)
     
class uiFrame(ttk.Frame):
    
    def __init__(self, master, arrange = False, column = 0, columnspan = 1, row = 0, rowspan = 1, relief = False):
        if relief:
            ttk.Frame.__init__(self, master, relief = tkinter.GROOVE, padding = 1.3)  
        else:
            ttk.Frame.__init__(self, master)  
        self.grid(column = column, columnspan = columnspan, row = row, rowspan = rowspan)

    def setEnd(self, val):
        self.master.setEnd(val)
 
class uiToggle(ttk.Button):
    
    def __init__(self,\
        master,\
        label,\
        arrange,\
        column = 0,\
        columnspan = 1,\
        row = 0,\
        default = None,\
        width = False,\
        function = False,\
        category = [],\
        control_key = [],\
        control_A_key = [],\
        control_E_key = []\
    ):
        if not width:
            width = button_width
            
        self.function = function
        self.root = master
        """
        Build the control dictionary
        """
        self.control = {'control': control_key, 'active': control_A_key, 'exclusive':control_E_key}
        self.control = dict([(control_key, control_list)
                         for control_key, control_list 
                         in list(self.control.items())
                         if control_list])
        for category_key in category:
            if category_key in control_dictionary:
                control_dictionary[category_key].append(self)
                continue
            control_dictionary[category_key] = [self]

        #for control_key, control_list in self.control.items()
        #control_dictionary[control_key]
        #Button.__init__(self, master,text = label, relief = GROOVE, command = lambda: self.toggle_button())
        ttk.Button.__init__(self, master, text = label, command = lambda: self.toggle_button(), width = width)
        if arrange == 'GRID':
            self.grid(column = column, columnspan = columnspan, row = row, sticky = 'W', ipadx = 2, ipady = 2, padx = 4, pady = 2)
        else:
            self.pack()
        #self.pack()

        self.val = False
        self.default = default

    def toggle_button(self):
        #print('button Toggle')
        if self.getVal():
            self.configure(style='button_off.TButton')
            self.val = False
        else:
            self.configure(style='button_on.TButton')
            for c_key in self.control.get('exclusive', list()):
                for UI_Obj in control_dictionary.get(c_key, list()):
                    if UI_Obj is not self:
                        UI_Obj.setVal(False)
            self.val = True
            if self.function:
                self.function()

    def getVal(self, key = False):
        return self.val
            
    def setVal(self, val):
        if val != self.getVal():
            self.toggle_button()

    def setDefault(self, key = None):
        if self.default is not None:
            self.setVal(self.default)
            
    def setSavedValue(self, key):
        if self.default is not None:
            self.setVal(svReg.get(key, self.default))
        elif key in svReg:
            self.setVal(svReg[key])
        
class uiButton(ttk.Button):
    
    def __init__(self,\
        master,\
        label,\
        arrange,\
        column = 0,\
        columnspan = 1,\
        row = 0,\
        buttonFunction = False,\
        sticky = 'W',\
        width = button_width\
    ):
        
  
        ttk.Button.__init__(self, master, text = label, command = buttonFunction, width = width)        
        
        if arrange == 'GRID':
            self.grid(column = column, columnspan = columnspan, row = row, sticky = sticky, ipadx = 2, ipady = 2, padx = 4, pady = 2)
        else:
            self.pack()
 
    def end(self):
        self.master.setEnd(True)
        self.quit()
 
    def ok(self):
        self.quit()
   
    def setDefault(self, key = None):
        return

    def setSavedValue(self, key):
        return
 
class uiFooter(uiFrame):
    def __init__(self,\
        master,\
        label = None,\
        from_ = 0,\
        to = 100,\
        arrange = 'GRID',\
        col = 0,\
        colspan = 0,\
        row = 0,\
        stk = 's',\
    ):
    
        ttk.Frame.__init__(self, master)
        if arrange == 'GRID':
            self.grid(column = col, columnspan = colspan, row = row, sticky = stk)
        else:    
            self.pack(expand=True, fill='both')


class uiComboSlider(uiFrame):

    def __init__(self,\
        master,\
        label = None,\
        from_ = 0,\
        to = 100,\
        orient = tkinter.HORIZONTAL,\
        resolution = 1,\
        tickinterval = 1,\
        arrange = 'GRID',\
        col = 0,\
        colspan = 0,\
        row = 0,\
        stk = 'e',\
        var = False,\
        default = 1,\
        width = button_width,\
        e_width = entry_width,\
    ):
        self.entry_width = e_width
        ttk.Frame.__init__(self, master, borderwidth = 3, relief = tkinter.GROOVE)
        self.root = master
        if arrange == 'GRID':
            self.grid(column = col, columnspan = colspan, row = row, pady = 10, padx = 10, rowspan = 2, sticky = tkinter.W + tkinter.E + tkinter.N + tkinter.S)
        else:    
            self.pack(expand=True, fill='both')
            
        if var:
            self.var = var
        elif type(from_) is int:
            self.var = tkinter.IntVar()
            #print ('Integer', type(self.var))
        else:
            self.var = tkinter.DoubleVar()
            #print ('Float', type(self.var))

        self.default = default
        #print (label)
        self.lbl = uiLabel(\
            self,\
            label,\
            arrange = 'GRID',\
            column = 0,\
            columnspan = 2,\
            row = 0,\
            width = width,\
        )

        self.entry = uiEntry(\
            self,\
            self.var,\
            arrange = 'GRID',\
            column = 1,\
            columnspan = 1,\
            row = 1,\
            to = to,\
            from_ = from_,\
            width = entry_width\
        )

        self.slider = uiSlider(\
           self,\
           'Search Distance',\
            from_ = from_,\
            to = to,\
            orient = tkinter.HORIZONTAL,\
            resolution = resolution,\
            tickinterval = tickinterval,\
            variable = self.var,\
            arrange = 'GRID',\
            column = 0,\
            columnspan = 1,\
            row = 1,\
            default = default,\
            command = self.entry.valid,\
        )

    def setEnd(self, val):
        self.master.setEnd(val)

    def setDefault(self, key = None):
        self.var.set(self.default)

    def setSavedValue(self, key):
        if self.default is not None:
            self.var.set(svReg.get(key, self.default))
        elif key in svReg:
            self.var.set(svReg[key])
        
    def getVal(self, key = False):
        return self.var.get()

class uiLabel(ttk.Label):
    
    def __init__(\
        self,\
        master,\
        text,\
        arrange = 'GRID',\
        column = 0,\
        columnspan = 1,\
        row = 0,\
        width = button_width\
    ):
        ttk.Label.__init__(self, master, text = text, width = width)
        if arrange == 'GRID':
            self.grid(column = column, columnspan = columnspan, row = row, sticky = E)
        else:
            self.pack()
        
    def setDefault(self, key = None):
        return
 
    def setSavedValue(self, key):
        return
    
class uiEntry(ttk.Entry):
    
    def __init__(\
        self,\
        master,\
        var,\
        arrange = 'GRID',\
        column = 1,\
        columnspan = 1,\
        row = 0,\
        to = None,\
        from_ = None,\
        width = entry_width\
    ):
        #vcmd = master.register(self.valid)
        ttk.Entry.__init__(self, master, textvariable = var, validate  = 'focusout', validatecommand = self.valid, width = width)
        if arrange == 'GRID':
            self.grid(column = column, columnspan = columnspan, row = row, sticky = 'E', ipadx = 2, ipady = 2, padx = 4, pady = 2)
        else:
            self.pack()
        self.var = var
        self.to = to
        self.from_ = from_

    def valid(self, value = None):
        #print (value)
        val = self.var.get()
         
        if val > self.to:
            self.var.set(self.to)
            return True
        elif val < self.from_:
            self.var.set(self.self.from_)
            return True
 
        self.var.set(val)
        
        return True

class uiSlider(ttk.Scale):

    def __init__(\
        self,\
        master,\
        label,\
        from_ = 1,\
        to = 100,\
        orient = tkinter.HORIZONTAL ,\
        resolution = 1,\
        tickinterval = 1,\
        variable = None,\
        arrange = 'GRID',\
        column = 0,\
        columnspan = 1,\
        row = 0,\
        default = None,\
        command = None,\
        length = None\
    ):
    
        self.root = master
        if not length:
            length = slider_length
        if variable:
            self.var = variable
            #print (self.var)
        elif type(from_) is int:
            self.var = tkinter.IntVar()
        else:
            self.var = tkinter.DoubleVar()
        #Scale.__init__(self, master, variable = self.var, label = label, from_ = from_, to = to, orient = orient, relief = relief, resolution = resolution)
        ttk.Scale.__init__(self, master, variable = self.var, from_ = from_, to = to, orient = orient, command = command, length = slider_length)
        
        self.configure( style = 'slider.Horizontal.TScale')
        
        if arrange == 'GRID':
            self.grid(column = column, columnspan = columnspan, row = row, sticky = 'E', ipadx = 2, ipady = 2, padx = 4, pady = 2)
        else:
            self.pack()
        #self.pack()
        self.default = default

    def setDefault(self, key = None):
        #print('SETTING DEFAULTS')
        if self.default is not None:
            self.setVal(self.default)
        return

    def setSavedValue(self, key):
        if self.default is not None:
            self.setVal(svReg.get(key, self.default))
        elif key in svReg:
            self.setVal(svReg[key])
    
    def getVal(self, key = False):
        return self.var.get()
    
    def setVal(self, val):
        self.var.set(val)


