from google.appengine.ext import db

def iter_uniquify(entities, seen_set, uniquify = True):
    """Return an iterator that walks over the given entities, by default removing duplicates."""
    if uniquify:
        for entity in entities:
            if entity.key() not in seen_set:
                seen_set.add(entity.key())
                yield entity
    else:
        for entity in entities:
            yield entity

def key_and_entity(entity_or_key, entity_class):
    """Given an entity or key, return both the entity and its key."""
    if isinstance(entity_or_key, db.Model):
        return (entity_or_key.key(), entity_or_key)
    else:
        return (entity_or_key, entity_class.get([entity_or_key]))

def normalize_to_key(entity_or_key):
    """Given an entity or key, return the key."""
    return entity_or_key.key() if isinstance(entity_or_key, db.Model) else entity_or_key

def normalize_to_keys(entities_or_keys):
    """Given a list of entities or keys, return a list of keys."""
    return [eok.key() if isinstance(eok, db.Model) else eok for eok in entities_or_keys]

def serialize_entities(entities):
    """Given a list of datastore entities, or a single entity, return a string (or list of strings) 
       that represents that entity. Using protobuf is substantially faster than pickling and leads to
       much more compact representations when storing in memcache."""
    if entities is None:
        return None
    elif isinstance(entities, db.Model):
        # Just one instance
        return db.model_to_protobuf(entities).Encode()
    else:
        # A list
        return [db.model_to_protobuf(x).Encode() for x in entities]

def deserialize_entities(data):
    """Given the representation of a serialized entity, or entities, return the
       deserialized form."""
    if data is None:
        return None
    elif isinstance(data, str):
        # Just one instance
        return db.model_from_protobuf(entity_pb.EntityProto(data))
    else:
        return [db.model_from_protobuf(entity_pb.EntityProto(x)) for x in data]

def unique_keys(keys):
    unique = {}
    for key in keys:
        unique[key] = True
    return unique.values()
    
def unique_entities(entities):
    unique = {}
    for entity in entities:
        unique[entity.key()] = entity
    return unique.values()

class QueryException(Exception):
    pass

class AppendedQuery(object):
    """
    AppendedQuery allows you to "append" the results of multiple distinct AppEngine
    queries into a single large query. The primary advantage is that it keeps queries
    unevaluated until absolutely necessary. It must be used cautiously, because it can be
    computationally expensive. It is the "end" of a query chain and does not support
    filter(), order(), or ancestor().
    
    It is most efficient to iterate over an AppendedQuery.
    """
    def __init__(self, queries):
        self._queries = queries

    def filter(self, *args, **kwargs):
        raise QueryException("AppendedQuery does not support filter().")
        
    def order(self, *args, **kwargs):
        raise QueryException("AppendedQuery does not support order().")
        
    def ancestor(self, *args, **kwargs):
        raise QueryException("AppendedQuery does not support ancestor().")
        
    def get(self):
        for query in self._queries:
            got = query.get()
            if got is not None:
                return got
        return None
        
    def fetch(self, limit, offset = None):
        if offset is not None:
            raise QueryException("AppendedQuery does not support fetch() with an offset.")            
        fetched = []
        for query in self._queries:
            query_fetched = query.fetch(limit)
            fetched.extend(query_fetched)
            limit -= len(query_fetched)
            if limit <= 0:
                return fetched
        return fetched
    
    def count(self, limit = 1000):
        count = 0
        for query in self._queries:
            count += query.count(remaining_limit)
            limit -= count
            if limit <= 0:
                return count
        return count
        
    def __iter__(self):
        for query in self._queries:
            for entity in query:
                yield entity
    