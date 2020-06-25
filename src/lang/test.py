import jsonpickle

f = open("./de.json", 'rb')
json_str = f.read()
objs = jsonpickle.decode(json_str)

print(objs['commands']['general']['not_in_private'])
