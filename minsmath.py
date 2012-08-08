'''How to use this script:

In the same directory as the script, you will find two files: mins.txt and 
prices.csv. Look up the current mineral prices and add them to prices.csv.

When you've finished, open mins.txt. Hit ctrl-a (or cmd-a) in the reprocessing output window, and then copy. Paste the output into mins.txt and save. Then run this script.'''

def addm(data,prices):
    ''' takes a list of minerals/amounts and adds them '''
    i = 0
    res = 0
    while(i < len(data)):
        res = res + prices[data[i]]*data[i+1]
        i = i + 2
    return(res)

def getprices():
    ''' reads in prices from a text file. TODO: replace w/eve-central'''
    f = open('prices.txt')
    raw = f.readlines()
    pricesraw = []
    for line in raw:
        foo = line.split(",")
        pricesraw.append((foo[0],float(foo[1])))
    prices = dict(pricesraw)
    return(prices)
    

def getreprocess():
    ''' reads in mineral values copy-pasted from game and saved to file '''
    f = open('mins.txt')
    raw = f.readlines()
    data = []
    for line in raw:
        foo = line.split('\t')
        data.append(foo[0])
        data.append(int(foo[1]))
    f.close()
    return(data)

if __name__ == "__main__":
    prices = getprices()
    data = getreprocess()
    sellprice = addm(data,prices)
    print(sellprice)
