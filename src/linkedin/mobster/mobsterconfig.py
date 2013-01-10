class MobsterConfigDict(dict):
  """
  A subclass of dictionary which does not allow for insertion of new keys.
  Only one instance can be created. The initial contents of the dictionary 
  are specified in CONFIG_DEFAULTS below.
  """
  
  CONFIG_DEFAULTS = {
    'WS_DEBUG_PORT': 9222, 
    'DEBUG': False
  }

  _instance = None

  def __new__(cls, *args, **kwargs):
    """Ensure that only one instance of MobsterConfigDict can be created"""
    if not cls._instance:
      cls._instance = super(MobsterConfigDict, cls)    \
                        .__new__(cls, *args, **kwargs)

      return cls._instance
    else:
      raise Exception("Attempt to create multiple instances of " \
                      "MobsterConfigDict")

  def __init__(self):
    dict.__init__(self, MobsterConfigDict.CONFIG_DEFAULTS)
  
  def __setitem__(self, key, val):
    """Do not allow assignment to key values not contained in the defaults"""
    if key not in MobsterConfigDict.CONFIG_DEFAULTS.keys():
      raise KeyError('Invalid config key {0}'.format(key))
    return dict.__setitem__(self, key, val)

config = MobsterConfigDict()
