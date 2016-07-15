def splitlist(list_, number):
    lists = []
    last_number = 0.
    while last_number < len(list_):
        new_list = list_[int(last_number):int(last_number + (len(list_)/float(number)))]
        lists.append(new_list)
        last_number += len(list_)/float(number)
    return lists
