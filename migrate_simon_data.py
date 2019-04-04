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
    #return: a dictionary containing dictionaries of the ArchivalWare records

def create_series_obj(aw_dict): #tested!
    #input: one dictionary from DICT_OF_DICTS
    series_name = aw_dict["Series"]
    if series_name in SERIES_DICTS.keys():
        return SERIES_DICTS[series_name]['id']
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
        # SERIES_DICTS[series_name] = {}
        # SERIES_DICTS[series_name]['id'] = new_ao_post['id']
        return new_ao_post

def create_digital_object(aw_dict):
    #input: one dict for DICT_OF_DICTS
    #parse dict for info
    #return do instance
    pass

def make_container_indicator(link):
    split_link = link.split("/")
    simon_ind = split_link.index("simon")
    indicator = split_link(simon_ind) + "_" + split_link(simon_ind + 1)
    return indicator

def parse_top_container_info(aw_dict):
    #input: one dictionary from DICT_OF_DICTS
    indicator = make_container_indicator(aw_dict['Persistent Link'])
    if indicator in TOP_CONTAINERS.keys():
        return TOP_CONTAINERS[indicator]
    else:
        #create instance container w/ ref id
        #add that data to TOP_CONTAINERS
        #return TOP_CONTAINERS[indicator]
        pass

def create_archival_object(aw_dict, box_instance, do_instance, repo_id, resource_id):
    #input: one dict from DICT_OF_DICTS, repo, resource
    #parse dict for info
    new_ao = {}
    new_ao['title'] = aw_dict['Title']
    new_ao['level'] = 'item'
    new_ao['resource'] = {"ref":"/repositories/"+repo_id+"/resources/"+resource_id}
    new_ao['dates'] = [{"expression": aw_dict['Date Created'],"date_type": "single", "label": "creation", "jsonmodel_type": "date"}]
    #post to Aspace AS CHILD OF RESOURCE
    new_ao_data = json.dumps(new_ao)
    #post
    new_ao_post = requests.post(baseURL+'/repositories/'+ repo_id +'/archival_objects', headers=HEADERS,data=new_ao_data).json()
    print(new_ao_post)
    return new_ao_post


def add_records_to_series(series_kids, repo_id, resource_id): #make AOs children of others
    for key in list(series_kids.keys()):
        kid_list = series_kids[key]
        kids_dict = {'children':[]}
        for kid in kid_list:
            kid_obj = {}
            kid_obj['ref_id']= kid
            kids_dict['children'].append(kid_obj)
        kids_json = json.dumps(kids_dict)
        ao_post = requests.post(baseURL+'/repositories/' + repo_id + '/archival_objects/' + key + '/children',headers=HEADERS,data=kids_json).json()
        print('Added children to AO: ', ao_post['id'])
    pass

def whole_thang(DICT_OF_DICTS, repo_id, resource_id):
    #input: repo_id, resource_id
    #returns: nothing
    #creates ASpace records based on ArchivalWare records
    series_kids = {}
    for aw_dict in DICT_OF_DICTS:
        #create AO series
        series_id = create_series_obj(aw_dict) #create series level AOs
        aw_dict['series_id'] = series_id #add series AO ref_id to the AW dictionary for later
        #create DO individual record
        do_instance = create_digital_object(aw_dict)
        #create box instance
        box_instance = parse_top_container_info(aw_dict)

        #create AO record and post
        new_ao_id = create_archival_object(aw_dict, box_instance, do_instance, repo_id, resource_id)
        if series_id in series_kids.keys():
            series_kids[series_id].append(new_ao_id)
        else:
            series_kids[series_id] = [new_ao_id]
    pass

def delete_ao(ao_id, repo_id):
    delete = requests.delete(baseURL + '/repositories/' + repo_id + '/archival_objects/' + str(ao_id), headers=HEADERS)
    print(delete.text) #tested!

if __name__=='__main__':
    DICT_OF_DICTS = parse_simon_data(FNAME)
    SERIES_DICTS = {}
    TOP_CONTAINERS = {}
    # data = {}
    # data["all_ids"]="true"
    # resp = requests.get(baseURL + '/repositories/' + repo_id + '/archival_objects', headers=HEADERS, data = data)
    # print(resp.text
    ids_to_del = []
    ao_post_series= create_series_obj(DICT_OF_DICTS["http://doi.library.cmu.edu/10.1184/pmc/simon/box00017/fld01179/bdl0002/doc0001"])
    ids_to_del.append(ao_post_series['id'])
    ao_post = create_archival_object(DICT_OF_DICTS["http://doi.library.cmu.edu/10.1184/pmc/simon/box00017/fld01179/bdl0002/doc0001"], None, None, repo_id, resource_id)
    ids_to_del.append(ao_post['id'])
    inp = input("Delete archival objects? type yes or no: ")
    if inp == 'yes':
        for ao_post_id in ids_to_del:
            delete_ao(ao_post_id, repo_id)
