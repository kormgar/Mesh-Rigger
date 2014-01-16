

def deepListPermutations(deep_list, idx = False, temp_list = []):
    """

    This is a self-recursive function that is a variation of the 
    itertools permutation function

    Takes a list of iterables of form [[],[],[],[],...]

    Returns a list of lists containing all possible permutations of the
    top level items in each iterables with each other sublist
    where only a single item may be added from each sublist at a time.

    Example:
    deepListPermutations([['a','b'],['c', [1,2,3]],['e','f','g']])
    will return:
    [['a', 'c', 'e'], ['a', 'c', 'f'], ['a', 'c', 'g'], ['a', [1, 2, 3], 'e'], ['a',
    [1, 2, 3], 'f'], ['a', [1, 2, 3], 'g'], ['b', 'c', 'e'], ['b', 'c', 'f'], ['b',
    'c', 'g'], ['b', [1, 2, 3], 'e'], ['b', [1, 2, 3], 'f'], ['b', [1, 2, 3], 'g']]

    """

    if idx >= len(deep_list):
        return temp_list
    if temp_list:
        temp_list[:] = [this_list + [this_vert] for this_list in temp_list for this_vert in deep_list[idx]]
    else:
        temp_list = [[this_vert] for this_vert in deep_list[idx]]
    if idx is False and not temp_list:
        return deepListPermutations(deep_list)
    return deepListPermutations(deep_list, idx + 1, temp_list)

def testVal(test1, test2, t_val, f_val):
    if test1 == test2:
        return t_val
    return f_val