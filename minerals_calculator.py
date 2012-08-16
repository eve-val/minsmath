import evelink.api
import evelink.eve
import evelink.char
import yaml
from yaml import load
import evecentral

KEY_ERROR = -1

class minerals_calculator(object):

    def __init__(self):
        try:
            charinfo = open('char_info.txt')
            keyid, vcode, charname = charinfo.read().split(',')
            keyid = int(keyid)
        except IOError:
            keyid, vcode, charname = get_charinfo()
        self.get_character(charname,(keyid,vcode))
        self.get_tables()



    def get_character(self, charname, apikey):
        self.api = evelink.api.API(api_key=apikey)
        self.eve = evelink.eve.EVE()
        charid = self.eve.character_id_from_name(charname)
        self.char = evelink.char.Char(char_id = charid, api= self.api)
        self.assets = self.char.assets()

    def refresh_assets(self):
        self.assets = self.char.assets()

    def get_tables(self):
        print('please wait. This program will now suck ALL the memory.')
        ins = self.load_yaml('invTypes.yaml')
        self.item_types = ins['data']
        print('load 1/5 complete.')
        ins = self.load_yaml('mapSolarSystems.yaml')
        self.solar_systems = ins['data']
        print('load 2/5 complete.')
        ins = self.load_yaml('invTypeMaterials.yaml')
        self.item_materials = ins['data'] 
        print('load 3/5 complete.')
        ins = self.load_yaml('staStations.yaml')
        self.highsec_stations = ins['data']
        print('load 4/5 complete.')
        self.nullsec_stations = self.eve.conquerable_stations()
        print('loading complete.')

    def load_yaml(self,filename):
        f = open(filename)
        return(yaml.load(f))    

    def get_charinfo(self):
        keyid = int(raw_input('What is your api key id? \n'))
        vcode = raw_input('What is your api vcode? \n')
        charname = raw_input('What is your character name? \n')
        out = file('char_info.txt','w')
        out.write(str(keyid) + ',' + vcode + ',' + charname)
        out.close()
        return([keyid,vcode,charname])

    def get_itemid_by_name(self,name):
        for item in self.item_types:
            if(item['typeName'] == name):
                return(item['typeID'])
        print('Name not found')

    def get_sysid_by_name(self,name):
        for elem in self.solar_systems:
            if elem['solarSystemName'] == name:
                return(elem['solarSystemID'])

    def get_regionid_by_sysname(self,sysname):
        for elem in self.solar_systems:
            if elem['solarSystemName'] == sysname:
                return(elem['regionID'])

    def get_staids_by_sysid(self,sysid):
        for key in self.nullsec_stations:
            if self.nullsec_stations[key]['system_id'] == sysid:
                return([key])
        results = []
        for elem in self.highsec_stations:
            if elem['solarSystemID'] == sysid:
                results.append(elem['stationID'])
        return(results)

    def get_staname_by_staid(self, staid):
        for key in self.nullsec_stations:
            if key == staid:
                return(self.nullsec_stations[key]['name'])
        for elem in self.highsec_stations:
            if elem['stationID'] == staid:
                return(elem['stationName'])

    def get_assets_at_station(self,name):
        sysid = self.get_sysid_by_name(name)
        staids = self.get_staids_by_sysid(sysid)
        system_assets = []
        asset_ids = []
        for station in staids:
            try:
                system_assets.append(self.assets[station]['contents'])
                asset_ids.append(station)
            except KeyError:
                pass
        if len(system_assets) == 0:
            print('you appear not to have anything there!')
            return(KEY_ERROR)
        elif len(system_assets) == 1:
            return(system_assets[0])
        else:
            for sta in assets_ids:
                print('[' + str(iter) + '] \t' + self.get_staname_by_staid(sta))
            result = raw_input('Which station did you mean?')
            return(system_assets[result])

    def offer_containers(self,assets):
        i = 1
        has_containsers = False
        containers = {}
        for elem in assets:
            try:
                contents = elem['contents']
                containers[i] = elem
                has_containers = True
            except KeyError:
                pass
        if has_containers == False:
            return(None)
        return(containers)

    def get_refine_list(self,location):
        refine_assets = self.get_assets_at_station(location)  
        if(refine_assets == KEY_ERROR): return KEY_ERROR
        containers = self.offer_containers(refine_assets)
        if(containers != None):
            print('Here are the available containers:')
            print('[0]\tHangar')
            for key in containers:
                print('['+str(key)+']' + '\t' + self.get_item_name_by_type(containers[key]['item_type_id']))
            selection = int(raw_input('Which container would you like to look in? \n'))
            if(selection != 0):
                refine_assets = containers[selection]['contents']
        return(refine_assets)

    def get_repro_results(self,itemid):
        results = []
        for item in self.item_materials:
            if item['typeID'] == itemid:
                results.append((item['materialTypeID'],int(item['quantity'])))
        return(results)

    def get_item_name_by_type(self,typeid):
        for item in self.item_types:
            if item['typeID'] == typeid:
                return(item['typeName'])
        print('Item ID not found')

    def getprices(self):
        ''' reads in prices from a text file. TODO: replace w/eve-central'''
        f = open('prices.csv')
        raw = f.readlines()
        pricesraw = []
        for line in raw:
            foo = line.split(',')
            pricesraw.append((self.get_itemid_by_name(foo[0]),float(foo[1])))
        prices = dict(pricesraw)
        return(prices)
     
    def print_refine(self,refine_assets):
        res = []
        for item in refine_assets:
            repro = self.get_repro_results(item['item_type_id'])
            refine_price = addm(repro,prices,refinery*0.01,standings*0.01)*item['quantity']
            sell_price = evecentral.find_best_price(item['item_type_id'],region)*item['quantity']
            if(refine_price > sell_price):
                verdict = "refine"
                delta = refine_price - sell_price
            else:
                verdict = "sell"
                delta = sell_price - refine_price
            res.append(str(self.get_item_name_by_type(item['item_type_id'])) + '\t' + verdict + '\t' + str(delta))
        res.sort()
        for item in res:
            print(item)
        
def addm(data,prices,refine,tax):
    ''' takes a list of tuples of (minerals,amount) and adds them, taking into account tax etc '''
    res = 0
    for item in data:
        res = res + prices[item[0]]*int(item[1]*refine*(1-tax))
    return(res)


if __name__ == '__main__':
    calc = minerals_calculator()
    while True:
        prices = calc.getprices()
        location = raw_input('Which system are your assets in? Please type the full name. \n')
        region = calc.get_regionid_by_sysname(location)
        calc.refresh_assets()
        refinery = float(raw_input('What is your net refining yield in percent? \n'))
        standings = float(raw_input('And what is the refinery tax in percent? \n'))
        refine_assets = calc.get_refine_list(location)
        if(refine_assets != KEY_ERROR):
            calc.print_refine(refine_assets)
