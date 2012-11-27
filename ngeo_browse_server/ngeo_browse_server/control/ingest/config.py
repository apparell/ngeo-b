from os.path import isabs, join, basename, splitext
from ConfigParser import NoSectionError, NoOptionError

from django.conf import settings

from ngeo_browse_server.config import get_ngeo_config, safe_get


INGEST_SECTION = "control.ingest"
MAPCACHE_SECTION = "control.ingest.mapcache"

def get_project_relative_path(path):
    """ Returns a path, relative to the defined `PROJECT_DIR` directory. """
    
    if isabs(path):
        return path
    
    return join(settings.PROJECT_DIR, path)


def get_storage_path(file_name, storage_dir=None, config=None):
    """ Returns an absolute path to a filename within the intermediary storage
    directory for uploaded but unprocessed files. 
    """
    
    config = config or get_ngeo_config()
    
    if not storage_dir:
        storage_dir = config.get(INGEST_SECTION, "storage_dir")
    
    return get_project_relative_path(join(storage_dir, file_name))


def get_optimized_path(file_name, directory=None, config=None):
    """ Returns an absolute path to a filename within the storage directory for
    optimized raster files. Uses the 'control.ingest.optimized_files_dir' 
    setting from the ngEO configuration.
    
    Also tries to get the postfix for optimized files from the 
    'control.ingest.optimized_files_postfix' setting from the ngEO configuration.
    
    All relative paths are treated relative to the PROJECT_DIR directory setting.
    """
    
    config = config or get_ngeo_config()
    
    file_name = basename(file_name)
    if directory:
        file_name = join(directory, file_name)
    
    optimized_dir = get_project_relative_path(
        config.get(INGEST_SECTION, "optimized_files_dir")
    )
    
    postfix = safe_get(config, INGEST_SECTION, "optimized_files_postfix", "")
    root, ext = splitext(file_name)
    return join(optimized_dir, root + postfix + ext)


def get_format_config(config=None):
    """ Returns a dictionary with all preprocessing format specific
    configuration settings.
    """
    
    values = {}
    config = config or get_ngeo_config()
    
    values["compression"] = safe_get(config, INGEST_SECTION, "compression")
    
    if values["compression"] == "JPEG":
        value = safe_get(config, INGEST_SECTION, "jpeg_quality")
        values["jpeg_quality"] = int(value) if value is not None else None
    
    elif values["compression"] == "DEFLATE":
        value = safe_get(config, INGEST_SECTION, "zlevel")
        values["zlevel"] = int(value) if value is not None else None
        
    try:
        values["tiling"] = config.getboolean(INGEST_SECTION, "tiling")
    except: pass
    
    return values


def get_optimization_config(config=None):
    """ Returns a dictionary with all optimization specific config settings. """
    
    values = {}
    config = config or get_ngeo_config()
    
    try:
        values["overviews"] = config.getboolean(INGEST_SECTION, "overviews")
    except: pass
    
    try:
        values["color_index"] = config.getboolean(INGEST_SECTION, "color_index")
    except: pass
    
    try:
        values["footprint_alpha"] = config.getboolean(INGEST_SECTION, "footprint_alpha")
    except: pass
    
    return values


def get_mapcache_config(config=None):
    """ Returns a dicitonary with all mapcache related config settings. """
    
    values = {}
    config = config or get_ngeo_config()
    
    values["seed_command"] = config.get(MAPCACHE_SECTION, "seed_command")
    values["config_file"] = config.get(MAPCACHE_SECTION, "config_file")
    values["threads"] = int(safe_get(config, MAPCACHE_SECTION, "threads", 1))
    
    return values