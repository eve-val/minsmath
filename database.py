import sqlite3
import yaml

def db_setup():
    conn = sqlite3.connect('eve.db')
    c = conn.cursor()

    #these are all the relevant fields from invTypes; if more are required they can be added
    c.execute('CREATE TABLE inv_types (type_id int, group_id int, type_name text, portion_size int)') 
    temp = load_yaml('invTypes.yaml')['data']
    ins = [(x['typeID'],x['groupID'],x['typeName'],x['portionSize']) for x in temp]
    c.executemany('INSERT INTO inv_types VALUES (?,?,?,?)', ins)
    
    #solar systems table
    c.execute('CREATE TABLE solar_systems (region_id int, system_id int, system_name text)')
    temp = load_yaml('mapSolarSystems.yaml')['data']
    ins = [(x['regionID'],x['solarSystemID'],x['solarSystemName']) for x in temp]
    c.executemany('INSERT INTO solar_systems VALUES (?,?,?)', ins)
    
    #high sec stations table: can get refinery efficiency here, which means could compute from char sheet
    c.execute('CREATE TABLE stations (id int, system_id int, region_id int, name text)')
    temp = load_yaml('staStations.yaml')['data']
    ins = [(x['stationID'],x['solarSystemID'],x['regionID'],x['stationName']) for x in temp]
    c.executemany('INSERT INTO stations VALUES (?,?,?,?)', ins)
    
    #refining results table
    c.execute('CREATE TABLE item_materials (type_id int, material_id int, quantity int)')
    temp = load_yaml('invTypeMaterials.yaml')['data']
    ins = [(x['typeID'],x['materialTypeID'],x['quantity']) for x in temp]
    c.executemany('INSERT INTO item_materials VALUES (?,?,?)', ins)

    conn.commit()
    
    
def load_yaml(filename):
    f = open(filename)
    return yaml.load(f)

class database(object):

    def __init__(self):
    
        self.conn = sqlite3.connect('eve.db')
        self.c = self.conn.cursor()

    def add_temp_table(self,table,fields):
        self.c.execute('CREATE TABLE '+table+' '+str(fields))

    def add_temp_values(self,table,pattern,data):
        self.c.executemany('INSERT INTO '+table+' VALUES '+pattern,data)

    def query(self,query,inputs):

        '''A wrapper for database queries. Expects an SQL query, with ?s for inputs that require sanitization. inputs is a tuple containing the inputs that should replace the ?s. Returns a list of all matching rows.'''

        self.c.execute(query,inputs)
        return self.c.fetchall()

if __name__ == '__main__':

    db_setup()
