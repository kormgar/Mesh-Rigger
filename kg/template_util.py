import kg
import pickle
import re
from os import path

r_nif_end = re.compile('.nif$', flags=re.IGNORECASE)
r_pkg_end = re.compile('.pkg$', flags=re.IGNORECASE)

#from kg.file_util import load_nif
#from kg.mesh_util import multiMesh

def loadTemplate(path_, settings = {}):

    print('Processing: ', path_)
    if re.search(r_pkg_end, path_):
        vert_dict = loadSeamTemplate(path_, settings)
        #vert_dict, bone_dict = loadTemplate(path_, settings)
        mesh_dict = dict([
          (gender, kg.mesh_util.templateMesh(template['vert'], template['bone']))
          for gender, template in vert_dict.items()
                          ])
        return mesh_dict
    else:
        test_nif = kg.file_util.load_nif(path_, settings = settings)
        if not test_nif.meshes:
            return None
        for this_mesh in test_nif.meshes:
            print(len(this_mesh.getVerts()),'found in template.  Adding to search array.')
            
        this_mesh = kg.mesh_util.multiMesh(test_nif.meshes, test_nif)
        print ('Total of ',len(this_mesh.getVerts()),'found in template.  Search array complete.')
        return this_mesh

def saveTemplate(current_settings):
    
    template_dict = dict()
    
    if current_settings.get('female'):
        template_dict['FEMALE'] = constructTemplate(current_settings, file_ = current_settings['female_template'])
    if current_settings.get('male'):
        template_dict['MALE'] = constructTemplate(current_settings, file_ = current_settings['male_template'])
    if current_settings.get('neutral'):
        template_dict['NONE'] = constructTemplate(current_settings, file_ = current_settings['template'])

    template_path, template_file = path.split(current_settings['template'])
    
    file_name = re.sub(r_nif_end, '.pkg', template_file)
    file_name = path.normpath((path.join(current_settings['destination'], file_name)))
    print('Saving Template to', file_name)
    pickle.dump(template_dict, open(file_name, "wb"))
    print('Template Saved')

def constructTemplate(current_settings, file_ = None):
    if not file_:
        file_ = current_settings['template']
        
    file_list = kg.file_util.get_files(file_, current_settings = current_settings, tri = False, morph = False)
        
    template_mesh = loadTemplate(file_list, settings = current_settings)
    template_mesh.initDoubles(mend = True)
    
    template_nmv = current_settings.get('template_mesh')
    if template_nmv == 'Edges Only':
        template_nmv = True
    elif template_nmv == 'All':
        template_nmv = False
    else:
        template_nmv = 'EXCLUDE'

    bone_prop_dict = dict()
    for m in template_mesh.m_list:
        for bone_name, bone_val in m.bone_dict.items(): 
            if bone_name in bone_prop_dict:
                continue
            bone_prop_dict[bone_name] = kg.bone_util.wrapBone(bone_val['bone'])
            continue
 
    vert_dict = dict()
    for m in template_mesh.m_list:
        m_name = m.block.name
        vert_dict[m_name] = dict()
        for i, v in m.getVerts(nmv = template_nmv, limit_doubles = True).items():
            if v.NMV:
                if v.normal:
                    vert_dict[m_name][i] = {'w_loc': v.getLoc(world_loc = True).as_list(), 'loc': v.getLoc(world_loc = False).as_list(), 'norm': v.normal.as_list(), 'wd': v.getWeight()}
                    continue
                vert_dict[m_name][i] = {'loc': v.loc.as_list(), 'norm': v.normal, 'wd': v.getWeight()}
    
    template_dict = {'vert': vert_dict, 'bone': bone_prop_dict}

    return template_dict

    
def loadSeamTemplate(file_name, current_settings):
    test_dict = pickle.load(open(file_name, "rb"))
    new_bones = {}
    for gender, template in test_dict.items():
        for bone, bone_values in template['bone'].items():
            new_bones[bone] = kg.bone_util.unWrapBone(bone_values)
        template['bone'] = new_bones

    return test_dict
    #return test_dict['vert'], new_bones