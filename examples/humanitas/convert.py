import json


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


output_data = {"devices" : device_list, "links" : json_data['links']}
json_string = json.dumps(output_data, indent=4)
with open("devices.json", 'w') as file:
    file.write(json_string)

