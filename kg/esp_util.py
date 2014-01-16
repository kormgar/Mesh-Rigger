from pyffi.formats.esp import EspFormat
import re
import os
item_split = re.compile('EDID')
field_split = re.compile(r'\\' + 'x00')
name_field = re.compile(r"\\"+"x00" + "(.*?)"+r"\\"+"x00")
r_nif_end = re.compile('.nif', flags=re.IGNORECASE)
female_nif = re.compile("MOD3"+".*?"+"x00"+"(.*?NIF)" + r"\\"+"x00", flags=re.IGNORECASE)
male_nif = re.compile("MODL"+".*?"+"x00"+"(.*?NIF)" + r"\\"+"x00", flags=re.IGNORECASE)
biped_flag = re.compile("BMDT")
armor_flag = re.compile("ARMO")
race_flag = re.compile("Saint", flags=re.IGNORECASE)
#race_flag = re.compile("RACE")
clothing_flag = re.compile("CLOT")

file_path = 'C:\\Steam\\steamapps\\common\\Oblivion_old\\Data\\femaleArmor.esp'

from struct import *

def getArmorPaths(file_path):
    file_ = open(os.path.normpath(file_path), 'rb')
    a = True
    b = 'b\'\''
    while a!=b:
        a = unpack('h', file_.readline())
        print(a)
        #for c in re.split(item_split, a):           
           
    #EspFormat
    #data = EspFormat.Data()
    #data.read(file_)
    #print(file_.name)
    
def getArmorPathsa(file_path):
    file_ = open(os.path.normpath(file_path), 'rb')    
    armor_dictionary = {}
    a = True
    b = 'b\'\''
    while a!=b:
        a = str(file_.readline())
        print(a)
        for c in re.split(item_split, a):
            #print(c)
            #if not re.search(race_flag, c):
            #    continue
            #print(c)
            #if not re.search(armor_flag, c) and not re.search(clothing_flag, c):
            #    continue
            nm = re.search(name_field, c)
            m = re.search(male_nif, c)
            f = re.search(female_nif, c)
            if not nm:
                continue
            this_name = nm.group(1)
            if not this_name:
                continue
            if not m and not f:
                continue
            armor_dictionary[this_name] = {}
            if m and not f:
                m_path = m.group(1)
                armor_dictionary[this_name]['UNKNOWN'] = os.path.normpath(m_path)
            elif m:
                m_path = m.group(1)
                armor_dictionary[this_name]['MALE'] = os.path.normpath(m_path)
                    
            if f:
                f_path = f.group(1)
                armor_dictionary[this_name]['FEMALE'] = os.path.normpath(f_path)
            #print(c)
    #for key, val in armor_dictionary.items():
    #    print (key, ':', val)    

