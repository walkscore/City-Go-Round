def uniquify(seq): 
    # not order preserving 
    set = {} 
    map(set.__setitem__, seq, []) 
    return set.keys()

def chunk_sequence(sequence, chunk_size):
    chunk = []
    for item in sequence:
        chunk.append(item)
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk

def key_for_value(dictionary, value):
    for k, v in dictionary.iteritems():
        if v == value:
            return k
    return None

def pad_list(list, length, pad_with = None):
    if len(list) < length:
        list.extend([pad_with] * (length - len(list)))

def collapse_list(list, collapse_item = None):
    while collapse_item in list:
        list.remove(collapse_item)
    