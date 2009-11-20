from django.conf import settings
from ..models import TransitAppFormProgress

def add_progress_uuid_to_session(request, progress_uuid):
    """Add a UUID to the session's progress UUID list"""
    uuids = request.get_session("progress_uuids", [])
    if progress_uuid not in uuids:
        uuids.append(progress_uuid)
        request.set_session("progress_uuids", uuids)
    
def remove_progress_uuid_from_session(request, progress_uuid):
    uuids = request.get_session("progress_uuids", [])
    if progress_uuid in uuids:
        uuids.remove(progress_uuid)
        if len(uuids) > 0:
            request.set_session("progress_uuids", uuids)
        else:
            request.del_session("progress_uuids")

def is_progress_uuid_in_session(request, progress_uuid):
    uuids = request.get_session("progress_uuids", [])
    return progress_uuid in uuids
    
def is_progress_uuid_in_datastore(progress_uuid):
    return TransitAppFormProgress.all().filter('progress_uuid =', progress_uuid).get() is not None
    
def is_progress_uuid_valid(request, progress_uuid):
    # Basic sanity check
    if progress_uuid is None:
        return False
        
    # Support accessing via /DEBUG/ if DEBUG is turned on
    if progress_uuid == settings.PROGRESS_DEBUG_MAGIC:
        return True
    
    # Another basic sanity check (these first three checks MUST happen in this order.)
    if len(progress_uuid) != 32:
        return False
        
    # IF this is part of a form post, AND the form post contains a progress_uuid,
    # make sure that the form post's UUID matches everything else...
    if request.method == "POST":
        posted_uuid = request.POST.get("progress_uuid", None)
        if posted_uuid and (posted_uuid != progress_uuid):
            return False
            
    # Make sure the UUID is in the user's session AND there is progress stored in the data store
    return is_progress_uuid_in_session(request, progress_uuid) and is_progress_uuid_in_datastore(progress_uuid)


