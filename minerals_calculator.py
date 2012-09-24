"""usage: 
    minerals_calculator.py
    minerals_calculator.py <location> <net_refine_yield> <refinery_tax> [--file <assets>]
    minerals_calculator.py --file <assets>

--file: indicate the location on disk of a file containing your assets, copied from the EVE client."""

import evelink.api
import evelink.eve
import evelink.char
import evecentral
import sys
from database import database
from docopt import docopt

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

    def get_file_refine_list(self,assets_file):
        refine_assets = parse_assets(assets_file)
        return(refine_assets)

    def get_prices(self,system):
        ''' reads in prices from a text file. TODO: replace w/eve-central'''
        minerals = ['Isogen','Megacyte','Mexallon','Nocxium','Pyerite','Tritanium','Zydrine']
        pricesraw = []
        for item in minerals:
            typeid = self.get_value('type_id','inv_types','type_name',item)[0]
            pricesraw.append((typeid,evecentral.find_sys_price(typeid,system)))
        prices = dict(pricesraw)
        return(prices)
    
    def print_refine(self,refine_assets,region):
        res = []
        total = 0.0;
        for item in refine_assets:
            itemid = item['item_type_id']
            repro = self.get_value('material_id,quantity','item_materials','type_id',itemid)
            refine_price = addm(repro,prices,refinery*0.01,standings*0.01)*item['quantity']
            sell_price = evecentral.find_best_price(item['item_type_id'],region)*item['quantity']
            if(refine_price > sell_price):
                verdict = "refine"
                delta = refine_price - sell_price
                total = total + refine_price
            else:
                verdict = "sell"
                delta = sell_price - refine_price
                total = total + sell_price
            res.append([self.get_value('type_name','inv_types','type_id',itemid)[0],verdict,str(refine_price/item['quantity']),str(delta)])
        res.sort()
        colsize = biggest_name(res)
        pattern = '{0:'+str(colsize+3)+'s} {1:6s} {2:7s} {3:5s}'
        for item in res:
            print(pattern.format(item[0],item[1],item[2],item[3]))
        print("-------------- \n Total: "+str(total))

    def print_file_refine(self,refine_assets,region):
        res = []
        total = 0.0;
        for item in refine_assets:
            itemid = self.get_value('type_id','inv_types','type_name',item[0])[0]
            repro = self.get_value('material_id,quantity','item_materials','type_id',itemid)
            refine_price = addm(repro,prices,refinery*0.01,standings*0.01)*item[1]
            sell_price = evecentral.find_best_price(itemid,region)*item[1]
            if(refine_price > sell_price):
                verdict = "refine"
                delta = refine_price - sell_price
                total = total + refine_price
            else:
                verdict = "sell"
                delta = sell_price - refine_price
                total = total + sell_price
            res.append([self.get_value('type_name','inv_types','type_id',itemid)[0],verdict,str(refine_price/item[1]),str(delta)])
        res.sort()
        colsize = biggest_name(res)
        pattern = '{0:'+str(colsize+3)+'s} {1:6s} {2:7s} {3:5s}'
        for item in res:
            print(pattern.format(item[0],item[1],item[2],item[3]))
        print("-------------- \n Total: "+str(total))

def addm(data,prices,refine,tax):
    ''' takes a list of tuples of (minerals,amount) and adds them, taking into account tax etc '''
    res = 0
    for item in data:
        try:
            res = res + prices[item[0]]*int(item[1]*refine*(1-tax))
        except KeyError: #this error for items which refine into t2 stuff
            return 0
    return(res)

def biggest_name(results):
    biggest = 0
    for item in results:
        if biggest < len(item[0]):
            biggest = len(item[0])
    return biggest

def parse_assets(path_to_file):
    f = open(path_to_file)
    assets = [[y[0],get_qty(y[1])] for y in [x.split('\t') for x in f.readlines()]]
    return assets

def get_qty(ins):
    try:
        qty = int(ins)
    except ValueError:
        qty = 1
    return qty

if __name__ == '__main__':
    
    arguments = docopt(__doc__, argv=sys.argv[1:])
    calc = minerals_calculator()
    
    if arguments['<location>'] == False:
        location = raw_input('Where are you located?\n')
        refinery = float(raw_input('What is your net refining yield in percent? \n'))
        standings = float(raw_input('And what is the refinery tax in percent? \n'))
    else:
        location = arguments['<location>']
        refinery = arguments['<net_refine_yield>']
        standings = arguments['<refinery_tax>']
    if(type(refinery) == str and type(standings) == str):
        refinery = float(refinery)
        standings = float(standings)

    system = calc.get_value('system_id','solar_systems','system_name',location)[0]
    region = calc.get_value('region_id','solar_systems','system_name',location)[0]
    prices = calc.get_prices(system)

    if arguments['--file'] == False:
        refine_assets = calc.get_refine_list(location)
        if(refine_assets != KEY_ERROR):
            calc.print_refine(refine_assets,region)
    else:
        assetfile = arguments['<assets>']
        refine_assets = calc.get_file_refine_list(assetfile)
        if(refine_assets != KEY_ERROR):
            calc.print_file_refine(refine_assets,region)

