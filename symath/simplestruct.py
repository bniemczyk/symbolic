class SimpleStruct(object):

  def __init__(self, **kargs):

    for k in kargs:
      setattr(self,k,kargs[k])
