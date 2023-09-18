import json
import random

with open("message.txt") as file:
    json_data = json.load(file)

id = 0
device_list = []
for node in json_data['nodes']:
    device = dict()
    device['id'] = id
    device['name'] = node['id']
    device['position'] = dict()
    device['position']['x'] = node['latitude']
    device['position']['y'] = node['longitude']
    device['position']['z'] = node['altitude']

    try:
        device['model'] = node['model']
    except:
        pass

    for link in json_data['links']:
        if link['source'] == device['name']:
            link['source'] = id
        if link['target'] == device['name']:
            link['target'] = id

    device_list.append(device)
    id +=1

    # Lets add in some resources

    if random.getrandbits(1):
        #NDC
        device['resource'] = {"cpu": 16, "gpu": 0, "mem": 32768, "disk": 1024000}
    else:
        # Nvidia Orin Nano
        device['resource'] = {"cpu": 8, "gpu": 8, "mem": 8192, "disk": 1024000}

output_data = {"devices" : device_list, "links" : json_data['links']}
json_string = json.dumps(output_data, indent=4)
with open("devices.json", 'w') as file:
    file.write(json_string)

