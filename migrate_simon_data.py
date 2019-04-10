import json
import requests
import csv
import time
import argparse
from datetime import datetime
import secrets

startTime = time.time()

baseURL = secrets.baseURL
user = secrets.user
password = secrets.password
repo_id = secrets.repo_id
resource_id = secrets.resource_id

FNAME = "simon_data_cache.json"

try:
    auth = requests.post(baseURL+'/users/'+user+'/login?password='+password).json()
except requests.exceptions.RequestException as e:
    print("Invalid URL, try again")
    exit()
#test authentication
if auth.get("session") == None:
    print("Wrong user or password! Try Again")
    exit()
else:
#print authentication confirmation
    print("Hello " + auth["user"]["name"])

SESSION = auth["session"]
HEADERS = {'X-ArchivesSpace-Session':SESSION}

def parse_simon_data(fname):
    #input: json filename
    with open(fname) as cache:
        cache_dict = json.loads(cache.read())
    test = cache_dict["http://doi.library.cmu.edu/10.1184/pmc/simon/box00017/fld01179/bdl0002/doc0001"]
    print(test)
    print("Cache load successful.")

    return cache_dict #tested!

def create_series_obj(aw_dict): #tested!
    #input: one dictionary from DICT_OF_DICTS
    series_name = aw_dict["Series"]
    if series_name in SERIES_DICTS.keys():
        return SERIES_DICTS[series_name]['ref_id']
    else:
        #create ao record
        new_ao = {}
        new_ao["jsonmodel_type"] = "archival_object"
        new_ao['title'] = series_name
        new_ao['level'] = 'series'
        new_ao['resource'] = {"ref":"/repositories/"+repo_id+"/resources/"+resource_id}
        new_ao_data = json.dumps(new_ao)
        #post
        new_ao_post = requests.post(baseURL+'/repositories/'+ repo_id +'/archival_objects', headers=HEADERS,data=new_ao_data).json()
        print(new_ao_post)
        #add that data to SERIES_DICTS
        SERIES_DICTS[series_name] = {}
        SERIES_DICTS[series_name]['ref_id'] = new_ao_post['uri']
        return SERIES_DICTS[series_name]['ref_id']

def make_file_identifier(link):
    split_link = link.split("/")
    box_ind = split_link.index("simon") + 1
    identifier = "Simon_" + "_".join(split_link[box_ind:]) + ".pdf"
    return identifier

def create_digital_object(aw_dict): #tested!
    #input: one dict for DICT_OF_DICTS
    #parse dict for info
    new_do = {}
    new_do['title'] = aw_dict['Title']
    new_do['jsonmodel_type'] = 'digital_object'
    new_do['digital_object_id'] = make_file_identifier(aw_dict["Persistent Link"])
    if 'Date Created' in list(aw_dict.keys()):
        new_do['dates'] = [{"expression": aw_dict['Date Created'],"date_type": "single", "label": "creation", "jsonmodel_type": "date"}]
    new_do['file_versions'] = [{ "jsonmodel_type":"file_version", 'file_uri': make_file_identifier(aw_dict["Persistent Link"]), "is_representative":False, "file_format_name":aw_dict['Type'], "publish":True}]
    new_do_data = json.dumps(new_do)
    #post to archivesspace, make ref url
    new_do_post = requests.post(baseURL+'/repositories/'+ repo_id +'/digital_objects', headers=HEADERS,data=new_do_data).json()
    print(new_do_post)
    #make instance object
    try:
        dig_obj_uri = new_do_post['uri']
        instance = {'instance_type':'digital_object', 'digital_object':{'ref': '/repositories/'+ repo_id + '/digital_objects/' + dig_obj_uri}}
        #return instance
        return instance
    except:
        print('Error!')
        exit()

def make_container_indicator(link):
    split_link = link.split("/")
    simon_ind = split_link.index("simon")
    indicator = split_link[simon_ind] + "_" + split_link[simon_ind + 1]
    return indicator

def create_top_container(aw_dict):
    #input: one dictionary from DICT_OF_DICTS
    indicator = make_container_indicator(aw_dict['Persistent Link'])
    if indicator in TOP_CONTAINERS.keys():
        return TOP_CONTAINERS[indicator]
    else:
        #create instance container w/ ref id
        new_co = {}
        new_co['type'] = 'box'
        new_co['jsonmodel_type'] = 'top_container'
        new_co['indicator'] = make_container_indicator(aw_dict["Persistent Link"])
        new_con_data = json.dumps(new_co)
        new_con_post = requests.post(baseURL+'/repositories/'+ repo_id +'/top_containers', headers=HEADERS,data=new_con_data).json()
        print(new_con_post)
        try:
            con_obj_uri = new_con_post['uri']
        except:
            print('Error!')
            exit()
        #create instance object
        top_container = {}
        top_container['ref'] = con_obj_uri
        sub_container = {}
        sub_container['top_container'] = top_container
        instance = {}
        instance['sub_container'] = sub_container
        instance['instance_type'] = 'mixed_materials'
        #add that data to TOP_CONTAINERS
        TOP_CONTAINERS[indicator] = instance
        #return instance
        print(instance)
        return instance

def create_archival_object(aw_dict, box_instance, do_instance, repo_id, resource_id): #tested with instances!
    #input: one dict from DICT_OF_DICTS, repo, resource
    #parse dict for info
    new_ao = {}
    new_ao['title'] = aw_dict['Title']
    new_ao['level'] = 'item'
    new_ao['resource'] = {"ref":"/repositories/"+repo_id+"/resources/"+resource_id}
    if 'Date Created' in list(aw_dict.keys()):
        new_ao['dates'] = [{"expression": aw_dict['Date Created'],"date_type": "single", "label": "creation", "jsonmodel_type": "date"}]
    new_ao['instances'] = []
    new_ao['instances'].append(do_instance)
    new_ao['instances'].append(box_instance)
    new_ao['parent'] ={"ref":aw_dict['series_id']}
    #post to Aspace AS CHILD OF RESOURCE
    new_ao_data = json.dumps(new_ao)
    #post
    # print(new_ao_data)
    new_ao_post = requests.post(baseURL+'/repositories/'+ repo_id +'/archival_objects', headers=HEADERS,data=new_ao_data).json()
    print(new_ao_post)
    return new_ao_post

def add_records_to_series(series_kids, repo_id, resource_id): #make AOs children of others
    #
    for key in list(series_kids.keys()):
        kid_list = series_kids[key]
        kids_dict = {'children':[]}
        kids_dict['position'] = 1
        for kid in kid_list:
            kid_obj = {}
            kid_obj['ref_id']= '/repositories/'+ repo_id +'/archival_objects/' + kid
            kids_dict['children'].append(kid_obj)
        kids_json = json.dumps(kids_dict)
        ao_post = requests.post(baseURL+'/repositories/' + repo_id + '/archival_objects/' + key + '/accept_children',headers=HEADERS,data=kids_json)
        print('Added children to AO! ', ao_post.text)


def whole_thang(DICT_OF_DICTS, repo_id, resource_id):
    #input: repo_id, resource_id
    #returns: nothing
    #creates ASpace records based on ArchivalWare records
    series_kids = {}
    for aw_dict in DICT_OF_DICTS:
        aw_dict = DICT_OF_DICTS[aw_dict]
        #create AO series
        series_ref = create_series_obj(aw_dict) #create series level AOs
        series_name = aw_dict["Series"]
        aw_dict['series_id'] = series_ref #add series AO ref_id to the AW dictionary for later
        #create DO individual record
        do_instance = create_digital_object(aw_dict)
        #create box instance
        box_instance = create_top_container(aw_dict)
        #create AO record and post
        new_ao_id = create_archival_object(aw_dict, box_instance, do_instance, repo_id, resource_id)

def delete_ao(ao_id, repo_id):
    delete = requests.delete(baseURL + '/repositories/' + repo_id + '/archival_objects/' + str(ao_id), headers=HEADERS)
    print(delete.text) #tested!

def delete_do(do_id, repo_id):
    delete = requests.delete(baseURL + '/repositories/' + repo_id + '/digital_objects/' + str(do_id), headers=HEADERS)
    print(delete.text)

def delete_con(con_id, repo_id):
    delete = requests.delete(baseURL + '/repositories/' + repo_id + '/top_containers/' + str(con_id), headers=HEADERS)
    print(delete.text)

def delete_stuff(endpoint, repo_id):
    data = {}
    data["all_ids"]='true'
    resp = requests.get(baseURL + '/repositories/' + repo_id + endpoint, headers=HEADERS, params = data)
    for id in resp.json():
        if endpoint == '/top_containers':
            delete_con(id, repo_id)
        elif endpoint == '/digital_objects':
            delete_do(id, repo_id)
        elif endpoint == '/archival_objects':
            delete_ao(id, repo_id)

def delete_all_stuff():
    endpoints = ['/top_containers','/digital_objects', '/archival_objects']
    inp = input("delete all records?")
    if inp == 'yes' or inp == 'y':
        for endpoint in endpoints:
            print(endpoint)
            delete_stuff(endpoint, repo_id)

if __name__=='__main__':
    DICT_OF_DICTS = parse_simon_data(FNAME)
    # delete_all_stuff()
    SERIES_DICTS = {}
    TOP_CONTAINERS = {}
    inp = input("add data? ")
    if inp == 'no':
        exit()
    else:
        but_kitchen_sink = whole_thang(DICT_OF_DICTS, repo_id, resource_id)
