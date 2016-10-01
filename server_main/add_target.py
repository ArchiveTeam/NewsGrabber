import json
import os
import sys

def main():
    targets = {}
    if os.path.isfile('targets.json'):
        targets = json.load(open('targets.json', 'r'))
        os.rename('targets.json', 'targets.json_old')

    newname = raw_input('name: ')[:9]
    newrsync = ''
    newsort = ''
    newquantity = ''

    if newname in targets:
        print 'Target already exists, details:'
        print 'name = ' + newname
        print 'rsync = ' + targets[newname]['rsync']
        print 'sort = ' + targets[newname]['sort']
        print 'quantity = ' + str(targets[newname]['quantity'])
        newrsync = targets[newname]['rsync']
        newsort = targets[newname]['sort']
        newquantity = targets[newname]['quantity']
        if raw_input('remove target? (y/n)') == 'y' and raw_input('SURE YOU WANT TO REMOVE? (Y/N)') == 'Y':
            del targets[newname]
            json.dump(targets, open('targets.json', 'w'), indent = 4)
            return 0
        if raw_input('change name? (y/n)') == 'y':
            del targets[newname]
            newname = raw_input('name: ')
        if raw_input('change rsync? (y/n)') == 'y':
            newrsync = raw_input('rsync: ')
        if raw_input('change sort? (y/n)') == 'y':
            newsort = raw_input('sort: (g/d)')
        if raw_input('change quantity? (y/n)') == 'y':
            newquantity = raw_input('quantity: ')
    else:
        newrsync = raw_input('rsync: ')
        newsort = raw_input('sort: (g/d)')
        newquantity = raw_input('quantity: ')

    if 'g' in newsort:
        newsort = 'grabber'
    else:
        newsort = 'discoverer'

    if not newname in targets:
        targets[newname] = {}
    targets[newname]['rsync'] = newrsync
    targets[newname]['sort'] = newsort
    targets[newname]['quantity'] = int(newquantity)

    json.dump(targets, open('targets.json', 'w'), indent = 4)

    if os.path.isfile('targets.json_old'):
        os.remove('targets.json_old')

    return 0

if __name__ == '__main__':
    sys.exit(main())
