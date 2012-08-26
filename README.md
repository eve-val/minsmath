minsmath
========

A quick python script to make reprocessing decisions easier

To use:
* Clone the repository to your computer
* Obtain a copy the invTypes, invTypeMaterals, mapSolarSystems, and staStations static data dump tables as .yaml files (this step is non-trivial and means this program is difficult to use for non-VN folks). Place these in the minsmath directory.
* Update prices.csv with the correct mineral prices from the market. As much as I would love to automate this step, eve-central doesn't quite have the tools.
* Run database.py. This will set up an sqlite database named eve.db to store the information from the yaml files
* Run minerals\_calculator.py with any of the following options:

        usage: 
        minerals_calculator.py    
        minerals_calculator.py <location> <net_refine_yield> <refinery_tax> [--file <assets>]    
        minerals_calculator.py --file <assets>

        --file: indicate the location on disk of a file containing your assets, copied from the EVE client.    
