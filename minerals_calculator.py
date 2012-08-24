import evelink.api
import evelink.eve
import evelink.char
import evecentral
from database import database

KEY_ERROR = -1

class minerals_calculator(object):

    def __init__(self):
        try:
            charinfo = open('char_info.txt')
            keyid, vcode, charname = charinfo.read().split(',')
            keyid = int(keyid)
        except IOError:
            keyid, vcode, charname = self.get_charinfo()
        self.get_character(charname,(keyid,vcode))
        self.database = database()
        self.get_tables()


    def get_character(self, charname, apikey):
        self.api = evelink.api.API(api_key=apikey)
        self.eve = evelink.eve.EVE()
        charid = self.eve.character_id_from_name(charname)
        self.char = evelink.char.Char(char_id = charid, api= self.api)
        self.assets = self.char.assets()

    def get_charinfo(self):
        keyid = int(raw_input('What is your api key id? \n'))
        vcode = raw_input('What is your api vcode? \n')
        charname = raw_input('What is your character name? \n')
        out = file('char_info.txt','w')
        out.write(str(keyid) + ',' + vcode + ',' + charname)
        out.close()
        return [keyid,vcode,charname]


    def refresh_assets(self):
        self.assets = self.char.assets()

    def get_tables(self):
        self.nullsec_stations = self.eve.conquerable_stations()
        inserts = []
        for key in self.nullsec_stations:
            temp = self.nullsec_stations[key]
            inserts.append((temp['id'],temp['system_id'],self.get_value('region_id','solar_systems','system_id',temp['system_id'])[0],temp['name']))
        self.database.add_temp_values('stations','(?,?,?,?)',inserts)
        print('loading complete.')

    def get_charinfo(self):
        keyid = int(raw_input('What is your api key id? \n'))
        vcode = raw_input('What is your api vcode? \n')
        charname = raw_input('What is your character name? \n')
        out = file('char_info.txt','w')
        out.write(str(keyid) + ',' + vcode + ',' + charname)
        out.close()
        return [keyid,vcode,charname]

    def get_value(self,field,table,key,value):
        result = self.database.query('select '+field+' from '+table+' where '+key+'=?',(value,))
        if len(result) == 0:
            return result
        #database returns a tuple. If the tuple has only one element, flatten it.
        elif len(result[0]) == 1:
            result = [x[0] for x in result]
        return result

    def get_assets_at_station(self,name):
        sysid = self.get_value('system_id','solar_systems','system_name',name)[0]
        staids = self.get_value('id','stations','system_id',sysid)
        system_assets = [] #list of assets at stations.
        asset_ids = [] #ids of stations with assets at them
        for station in staids:
            try:
                system_assets.append(self.assets[station]['contents'])
                asset_ids.append(station)
            except KeyError: #KeyError means no assets were found at that station.
                pass
        if len(system_assets) == 0:
            print('you appear not to have anything there!')
            return(KEY_ERROR)
        elif len(system_assets) == 1:
            return(system_assets[0])
        else:
            i = 0
            for sta in asset_ids:
                print('[' + str(i) + '] \t' + self.get_value('name','stations','id',sta)[0])
                i = i+1
            result = int(raw_input('Which station did you mean?'))
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
                print('['+str(key)+']' + '\t' + self.get_value('type_name','inv_types','type_id',containers[key]['item_type_id'])[0])
            selection = int(raw_input('Which container would you like to look in? \n'))
            if(selection != 0):
                refine_assets = containers[selection]['contents']
        return(refine_assets)

    def getprices(self):
        ''' reads in prices from a text file. TODO: replace w/eve-central'''
        f = open('prices.csv')
        raw = f.readlines()
        pricesraw = []
        for line in raw:
            foo = line.split(',')
            pricesraw.append((self.get_value('type_id','inv_types','type_name',foo[0])[0],float(foo[1])))
        prices = dict(pricesraw)
        return(prices)
     
    def print_refine(self,refine_assets,region):
        res = []
        for item in refine_assets:
            repro = self.get_value('material_id,quantity','item_materials','type_id',item['item_type_id'])
            refine_price = addm(repro,prices,refinery*0.01,standings*0.01)*item['quantity']
            sell_price = evecentral.find_best_price(item['item_type_id'],region)*item['quantity']
            if(refine_price > sell_price):
                verdict = "refine"
                delta = refine_price - sell_price
            else:
                verdict = "sell"
                delta = sell_price - refine_price
            res.append(str(self.get_value('type_name','inv_types','type_id',item['item_type_id'])[0]) + '\t' + verdict + '\t Refine price per: '+str(refine_price/item['quantity']) +'\t Difference: ' + str(delta))
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
        region = calc.get_value('region_id','solar_systems','system_name',location)[0]
        calc.refresh_assets()
        refinery = float(raw_input('What is your net refining yield in percent? \n'))
        standings = float(raw_input('And what is the refinery tax in percent? \n'))
        refine_assets = calc.get_refine_list(location)
        if(refine_assets != KEY_ERROR):
            calc.print_refine(refine_assets,region)
