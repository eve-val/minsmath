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

    def get_refine_list(self,assets_file):
        refine_assets = parse_assets(assets_file)
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
        print('we got here, and refine_assets has a length of '+str(len(refine_assets)))
        res = []
        for item in refine_assets:
            itemid = self.get_value('type_id','inv_types','type_name',item[0])[0]
            repro = self.get_value('material_id,quantity','item_materials','type_id',itemid)
            refine_price = addm(repro,prices,refinery*0.01,standings*0.01)*item[1]
            sell_price = evecentral.find_best_price(itemid,region)*item[1]
            if(refine_price > sell_price):
                verdict = "refine"
                delta = refine_price - sell_price
            else:
                verdict = "sell"
                delta = sell_price - refine_price
            res.append([self.get_value('type_name','inv_types','type_id',itemid)[0],verdict,str(refine_price/item[1]),str(delta)])
        res.sort()
        colsize = biggest_name(res)
        pattern = '{0:'+str(colsize+3)+'s} {1:6s} {2:7s} {3:5s}'
        for item in res:
            print(pattern.format(item[0],item[1],item[2],item[3]))
        
def addm(data,prices,refine,tax):
    ''' takes a list of tuples of (minerals,amount) and adds them, taking into account tax etc '''
    res = 0
    for item in data:
        res = res + prices[item[0]]*int(item[1]*refine*(1-tax))
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
    calc = minerals_calculator()
    while True:
        prices = calc.getprices()
        assetfile = raw_input('Please select your assets and copy, then paste the results into a text file. What is its name?\n')
        location = raw_input('and where are you located?')
        region = calc.get_value('region_id','solar_systems','system_name',location)[0]
        refinery = float(raw_input('What is your net refining yield in percent? \n'))
        standings = float(raw_input('And what is the refinery tax in percent? \n'))
        refine_assets = calc.get_refine_list(assetfile)
        if(refine_assets != KEY_ERROR):
            calc.print_refine(refine_assets,region)
