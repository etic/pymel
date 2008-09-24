"""
A wrap of Maya's MVector, MPoint, MColor, MMatrix, MTransformationMatrix, MQuaternion, MEulerRotation types
"""

import inspect
import math, copy
import itertools, operator, colorsys
import warnings

import pymel.util as util
import pymel.api as _api
from pymel.util.arrays import *
from pymel.util.arrays import _toCompOrArrayInstance
import factories as _factories

# patch some Maya api classes that miss __iter__ to make them iterable / convertible to list
def _patchMVector() :
    def __len__(self):
        """ Number of components in the Maya api MVector, ie 3 """
        return 3
    type.__setattr__(_api.MVector, '__len__', __len__)
    def __iter__(self):
        """ Iterates on all components of a Maya api MVector """
        for i in xrange(len(self)) :
            yield _api.MVector.__getitem__(self, i)
    type.__setattr__(_api.MVector, '__iter__', __iter__)

def _patchMFloatVector() :
    def __len__(self):
        """ Number of components in the Maya api MFloatVector, ie 3 """
        return 3
    type.__setattr__(_api.MFloatVector, '__len__', __len__)
    def __iter__(self):
        """ Iterates on all components of a Maya api MFloatVector """
        for i in xrange(len(self)) :
            yield _api.MFloatVector.__getitem__(self, i)
    type.__setattr__(_api.MFloatVector, '__iter__', __iter__)

def _patchMPoint() :
    def __len__(self):
        """ Number of components in the Maya api MPoint, ie 4 """
        return 4
    type.__setattr__(_api.MPoint, '__len__', __len__)    
    def __iter__(self):
        """ Iterates on all components of a Maya api MPoint """
        for i in xrange(len(self)) :
            yield _api.MPoint.__getitem__(self, i)
    type.__setattr__(_api.MPoint, '__iter__', __iter__)
 
def _patchMFloatPoint() :
    def __len__(self):
        """ Number of components in the Maya api MFloatPoint, ie 4 """
        return 4
    type.__setattr__(_api.MFloatPoint, '__len__', __len__)    
    def __iter__(self):
        """ Iterates on all components of a Maya api MFloatPoint """
        for i in xrange(len(self)) :
            yield _api.MFloatPoint.__getitem__(self, i)
    type.__setattr__(_api.MFloatPoint, '__iter__', __iter__) 
  
def _patchMColor() :
    def __len__(self):
        """ Number of components in the Maya api MColor, ie 4 """
        return 4
    type.__setattr__(_api.MColor, '__len__', __len__)    
    def __iter__(self):
        """ Iterates on all components of a Maya api MColor """
        for i in xrange(len(self)) :
            yield _api.MColor.__getitem__(self, i)
    type.__setattr__(_api.MColor, '__iter__', __iter__)  
    
def _patchMMatrix() :
    def __len__(self):
        """ Number of rows in the Maya api MMatrix, ie 4.
            Not to be confused with the number of components (16) given by the size method """
        return 4
    type.__setattr__(_api.MMatrix, '__len__', __len__)       
    def __iter__(self):
        """ Iterates on all 4 rows of a Maya api MMatrix """
        for r in xrange(4) :
            yield Array([_api.MScriptUtil.getDoubleArrayItem(_api.MMatrix.__getitem__(self, r), c) for c in xrange(4)])
    type.__setattr__(_api.MMatrix, '__iter__', __iter__)

def _patchMFloatMatrix() :
    def __len__(self):
        """ Number of rows in the Maya api MFloatMatrix, ie 4.
            Not to be confused with the number of components (16) given by the size method """
        return 4
    type.__setattr__(_api.MFloatMatrix, '__len__', __len__)       
    def __iter__(self):
        """ Iterates on all 4 rows of a Maya api MFloatMatrix """
        for r in xrange(4) :
            yield Array([_api.MScriptUtil.getDoubleArrayItem(_api.MMatrix.__getitem__(self, r), c) for c in xrange(4)])
    type.__setattr__(_api.MFloatMatrix, '__iter__', __iter__)

def _patchMTransformationMatrix() :
    def __len__(self):
        """ Number of rows in the Maya api MMatrix, ie 4.
            Not to be confused with the number of components (16) given by the size method """
        return 4
    type.__setattr__(_api.MTransformationMatrix, '__len__', __len__)       
    def __iter__(self):
        """ Iterates on all 4 rows of a Maya api MTransformationMatrix """
        return self.asMatrix().__iter__()
    type.__setattr__(_api.MTransformationMatrix, '__iter__', __iter__)

def _patchMQuaternion() :
    def __len__(self):
        """ Number of components in the Maya api MQuaternion, ie 4 """
        return 4
    type.__setattr__(_api.MQuaternion, '__len__', __len__)       
    def __iter__(self):
        """ Iterates on all components of a Maya api MQuaternion """
        for i in xrange(len(self)) :
            yield _api.MQuaternion.__getitem__(self, i)
    type.__setattr__(_api.MQuaternion, '__iter__', __iter__)  

def _patchMEulerRotation() :
    def __len__(self):
        """ Number of components in the Maya api MEulerRotation, ie 4 """
        return 4
    type.__setattr__(_api.MEulerRotation, '__len__', __len__)       
    def __iter__(self):
        """ Iterates on all components of a Maya api MEulerRotation """
        for i in xrange(len(self)) :
            yield _api.MEulerRotation.__getitem__(self, i)
    type.__setattr__(_api.MEulerRotation, '__iter__', __iter__)  

_patchMVector()
_patchMFloatVector()
_patchMPoint()
_patchMFloatPoint()
_patchMColor()
_patchMMatrix()
_patchMFloatMatrix()
_patchMTransformationMatrix()
_patchMQuaternion()
_patchMEulerRotation()

# the meta class of metaMayaWrapper
class MetaMayaArrayTypeWrapper(_factories.MetaMayaTypeWrapper) :
    """ A metaclass to wrap Maya array type classes such as MVector, MMatrix """ 
             
    def __new__(mcl, classname, bases, classdict):
        """ Create a new wrapping class for a Maya api type, such as MVector or MMatrix """
            
        if 'shape' in classdict :
            # fixed shape means also fixed ndim and size
            shape = classdict['shape']
            ndim = len(shape)
            size = reduce(operator.mul, shape, 1)
            if 'ndim' not in classdict :
                classdict['ndim'] = ndim
            elif classdict['ndim'] != ndim :
                raise ValueError, "class %s shape definition %s and number of dimensions definition %s do not match" % (classname, shape, ndim)
            if 'size' not in classdict :
                classdict['size'] = size
            elif classdict['size'] != size :
                raise ValueError, "class %s shape definition %s and size definition %s do not match" % (classname, shape, size)
                                          
        # create the new class   
        newcls = super(MetaMayaArrayTypeWrapper, mcl).__new__(mcl, classname, bases, classdict)

        try :
            apicls = newcls.apicls 
        except :
            apicls = None        
        try :
            shape = newcls.shape 
        except :
            shape = None
        try :
            cnames = newcls.cnames
        except :
            cnames = ()
            
        if shape is not None :
            # fixed shape means also fixed ndim and size
            ndim = len(shape)
            size = reduce(operator.mul, shape, 1)
            
            if cnames :
                # definition for component names
                type.__setattr__(newcls, 'cnames', cnames ) 
                subsizes = [reduce(operator.mul, shape[i+1:], 1) for i in xrange(ndim)]
                for index, compname in enumerate(cnames) :
                    coords = []
                    for i in xrange(ndim) :
                        c = index//subsizes[i]
                        index -= c*subsizes[i]
                        coords.append(c)
                    if len(coords) == 1 :
                        coords = coords[0]
                    else :
                        coords = tuple(coords)
                    p = eval("property( lambda self: self.__getitem__(%s) ,  lambda self, val: self.__setitem__(%s,val) )" % (coords, coords))
                    if compname not in classdict :
                        type.__setattr__(newcls, compname, p)
                    else :
                        raise AttributeError, "component name %s clashes with class method %r" % (compname, classdict[compname])                 
        elif cnames :
            raise ValueError, "can only define component names for classes with a fixed shape/size"
         
        # constants for shape, ndim, size
        if shape is not None :
            type.__setattr__(newcls, 'shape', shape)
        if ndim is not None :
            type.__setattr__(newcls, 'ndim', ndim)
        if size is not None :
            type.__setattr__(newcls, 'size', size)                        
        #__slots__ = ['_data', '_shape', '_size']    
        # add component names to read-only list
        readonly = newcls.__readonly__
        if hasattr(newcls, 'shape') :
            readonly['shape'] = None 
        if hasattr(newcls, 'ndim') :
            readonly['ndim'] = None  
        if hasattr(newcls, 'size') :
            readonly['size'] = None                                 
        if 'cnames' not in readonly :
            readonly['cnames'] = None
        type.__setattr__(newcls, '__readonly__', readonly)      

#        print "created class", newcls
#        print "bases", newcls.__bases__
#        print "readonly", newcls.__readonly__
#        print "slots", newcls.__slots__
        return newcls  

# generic math function that can operate on Arrays herited from arrays
# (min, max, sum, prod...)

# Functions that work on vectors will now be inherited from Array and properly defer
# to the class methods
               
class MVector(Vector) :
    """ A 3 dimensional vector class that wraps Maya's api MVector class,
        >>> v = MVector(1, 2, 3)
        >>> w = MVector(x=1, z=2)
        >>> z = MVector(MVector.xAxis, z=1)
        """
    __metaclass__ = MetaMayaArrayTypeWrapper
    __slots__ = ()
    # class specific info
    apicls = _api.MVector
    cnames = ('x', 'y', 'z')
    shape = (3,)

    def __new__(cls, *args, **kwargs):
        shape = kwargs.get('shape', None)
        ndim = kwargs.get('ndim', None)
        size = kwargs.get('size', None)
        # will default to class constant shape = (3,), so it's just an error check to catch invalid shapes,
        # as no other option is actually possible on MVector, but this method could be used to allow wrapping
        # of Maya array classes that can have a variable number of elements
        shape, ndim, size = cls._expandshape(shape, ndim, size)        
        
        new = cls.apicls.__new__(cls)
        cls.apicls.__init__(new)
        return new
        
    def __init__(self, *args, **kwargs):
        """ __init__ method, valid for MVector, MPoint and MColor classes """
        cls = self.__class__
        
        if args :
            # allow both forms for arguments
            if len(args)==1 and hasattr(args[0], '__iter__') :
                args = args[0]
            # shortcut when a direct api init is possible     
            try :
                self.assign(args)
            except :
                # special exception to the rule that you cannot drop data in Arrays __init__
                # to allow all conversion from MVector derived classes (MPoint, MColor) to a base class 
                # special case for MPoint to cartesianize if necessary
                # note : we may want to premultiply MColor by the alpha in a similar way
                if isinstance(args, _api.MPoint) and args.w != 1.0 :
                    args = copy.deepcopy(args).cartesianize()  
                if isinstance(args, _api.MColor) and args.a != 1.0 :
                    # note : we may want to premultiply MColor by the alpha in a similar way
                    pass
                if isinstance(args, _api.MVector) or isinstance(args, _api.MPoint) or isinstance(args, _api.MColor) :
                    args = tuple(args)
                    if len(args) > len(self) :
                        args = args[slice(self.shape[0])]
                super(Vector, self).__init__(*args)
            
        if hasattr(cls, 'cnames') and len(set(cls.cnames) & set(kwargs)) :  
            # can also use the form <componentname>=<number>
            l = list(self.flat)
            setcomp = False
            for i, c in enumerate(cls.cnames) :
                if c in kwargs :
                    if float(l[i]) != float(kwargs[c]) :
                        l[i] = float(kwargs[c])
                        setcomp = True
            if setcomp :
                try :
                    self.assign(l)
                except :
                    msg = ", ".join(map(lambda x,y:x+"=<"+util.clsname(y)+">", cls.cnames, l))
                    raise TypeError, "in %s(%s), at least one of the components is of an invalid type, check help(%s) " % (cls.__name__, msg, cls.__name__) 

    # for compatibility with base classes Array that actually hold a nested list in their _data attribute
    # here, there is no _data attribute as we subclass api.MVector directly, thus v.data is v
    # for wraps 
                          
    def _getdata(self):
        return self.apicls(self)
    def _setdata(self, value):
        self.assign(value) 
    def _deldata(self):
        if hasattr(self.apicls, 'clear') :
            self.apicls.clear(self)  
        else :
            raise TypeError, "cannot clear stored elements of %s" % (self.__class__.__name__)
          
    data = property(_getdata, _setdata, _deldata, "The MVector/MFloatVector/MPoint/MFloatPoint/MColor data")                           
                          
    # overloads for assign and get though standard way should be to use the data property
    # to access stored values                   
                                                 
    def assign(self, value):
        """ Wrap the MVector api assign method """
        # don't accept instances as assign works on exact types
        if type(value) != self.apicls and type(value) != type(self) :
            if not hasattr(value, '__iter__') :
                value = (value,)
            value = self.apicls(*value) 
        self.apicls.assign(self, value)
        return self
   
    # API get, actually not faster than pulling self[i] for such a short structure
    def get(self):
        """ Wrap the MVector api get method """
        ms = _api.MScriptUtil()
        l = (0,)*self.size
        ms.createFromDouble ( *l )
        p = ms.asDoublePtr ()
        self.apicls.get(self, p)
        return tuple([ms.getDoubleArrayItem ( p, i ) for i in xrange(self.size)])

    def __len__(self):
        """ Number of components in the MVector instance, 3 for MVector, 4 for MPoint and MColor """
        return self.apicls.__len__(self)
    
    # __getitem__ / __setitem__ override
    
    # faster to override __getitem__ cause we know MVector only has one dimension
    def __getitem__(self, i):
        """ Get component i value from self """
        if hasattr(i, '__iter__') :
            i = list(i)
            if len(i) == 1 :
                i = i[0]
            else :
                raise IndexError, "class %s instance %s has only %s dimension(s), index %s is out of bounds" % (util.clsname(self), self, self.ndim, i)
        if isinstance(i, slice) :
            return _toCompOrArrayInstance(list(self)[i], Vector)
            try :
                return _toCompOrArrayInstance(list(self)[i], Vector)
            except :
                raise IndexError, "class %s instance %s is of size %s, index %s is out of bounds" % (util.clsname(self), self, self.size, i)
        else :
            if i < 0 :
                i = self.size + i
            if i<self.size and not i<0 :
                if hasattr(self.apicls, '__getitem__') :
                    return self.apicls.__getitem__(self, i)
                else :
                    return list(self)[i]
            else :
                raise IndexError, "class %s instance %s is of size %s, index %s is out of bounds" % (util.clsname(self), self, self.size, i)

    # as api.MVector has no __setitem__ method, so need to reassign the whole MVector
    def __setitem__(self, i, a):
        """ Set component i value on self """
        v = Vector(self)
        v.__setitem__(i, a)
        self.assign(v) 
   
    # iterator override
     
    # TODO : support for optional __iter__ arguments           
    def __iter__(self, *args, **kwargs):
        """ Iterate on the api components """
        return self.apicls.__iter__(self.data)   
    def __contains__(self, value):
        """ True if at least one of the vector components is equal to the argument """
        return value in self.__iter__()  
    
    # common operators without an api equivalent are herited from Vector
    
    # operators using the Maya API when applicable, but that can delegate to Vector
    
    def __eq__(self, other):
        """ u.__eq__(v) <==> u == v
            Equivalence test """
        try :
            return bool(self.apicls.__eq__(self, other))
        except :
            return bool(super(MVector, self).__eq__(other))        
    def __ne__(self, other):
        """ u.__ne__(v) <==> u != v
            Equivalence test """
        return (not self.__eq__(other))      
    def __neg__(self):
        """ u.__neg__() <==> -u
            The unary minus operator. Negates the value of each of the components of u """        
        return self.__class__(self.apicls.__neg__(self)) 
    def __add__(self, other) :
        """ u.__add__(v) <==> u+v
            Returns the result of the addition of u and v if v is convertible to a Vector (element-wise addition),
            adds v to every component of u if v is a scalar """ 
        try :
            return self.__class__._convert(self.apicls.__add__(self, other))
        except :
            # return self.__class__._convert(super(MVector, self).__add__(other)) 
            return self.__class__._convert(super(MVector, self).__add__(other)) 
    def __radd__(self, other) :
        """ u.__radd__(v) <==> v+u
            Returns the result of the addition of u and v if v is convertible to a Vector (element-wise addition),
            adds v to every component of u if v is a scalar """
        try :
            return self.__class__._convert(self.apicls.__radd__(self, other))
        except :
            return self.__class__._convert(super(MVector, self).__radd__(other))  
    def __iadd__(self, other):
        """ u.__iadd__(v) <==> u += v
            In place addition of u and v, see __add__ """
        try :
            return self.__class__(self.__add__(other))
        except :
            return NotImplemented   
    def __sub__(self, other) :
        """ u.__sub__(v) <==> u-v
            Returns the result of the substraction of v from u if v is convertible to a Vector (element-wise substration),
            substract v to every component of u if v is a scalar """        
        try :
            return self.__class__._convert(self.apicls.__sub__(self, other))
        except :
            return self.__class__._convert(super(MVector, self).__sub__(other))   
    def __rsub__(self, other) :
        """ u.__rsub__(v) <==> v-u
            Returns the result of the substraction of u from v if v is convertible to a Vector (element-wise substration),
            replace every component c of u by v-c if v is a scalar """        
        try :
            return self.__class__._convert(self.apicls.__rsub__(self, other))
        except :
            return self.__class__._convert(super(MVector, self).__rsub__(other))      
    def __isub__(self, other):
        """ u.__isub__(v) <==> u -= v
            In place substraction of u and v, see __sub__ """
        try :
            return self.__class__(self.__sub__(other))
        except :
            return NotImplemented     
    def __div__(self, other):
        """ u.__div__(v) <==> u/v
            Returns the result of the division of u by v if v is convertible to a Vector (element-wise division),
            divide every component of u by v if v is a scalar """  
        try :
            return self.__class__._convert(self.apicls.__div__(self, other))
        except :
            return self.__class__._convert(super(MVector, self).__div__(other))    
    def __rdiv__(self, other):
        """ u.__rdiv__(v) <==> v/u
            Returns the result of of the division of v by u if v is convertible to a Vector (element-wise division),
            invert every component of u and multiply it by v if v is a scalar """
        try :
            return self.__class__._convert(self.apicls.__rdiv__(self, other))
        except :
            return self.__class__._convert(super(MVector, self).__rdiv__(other))    
    def __idiv__(self, other):
        """ u.__idiv__(v) <==> u /= v
            In place division of u by v, see __div__ """        
        try :
            return self.__class__(self.__div__(other))
        except :
            return NotImplemented           
    # action depends on second object type
    def __mul__(self, other) :
        """ u.__mul__(v) <==> u*v
            The multiply '*' operator is mapped to the dot product when both objects are Vectors,
            to the transformation of u by matrix v when v is a Matrix,
            to element wise multiplication when v is a sequence,
            and multiplies each component of u by v when v is a numeric type. """
        try :
            res = self.apicls.__mul__(self, other)
        except :
            res = super(MVector, self).__mul__(other)
        if util.isNumeric(res) :
            return res
        else :
            return self.__class__._convert(res)          
    def __rmul__(self, other):
        """ u.__rmul__(v) <==> v*u
            The multiply '*' operator is mapped to the dot product when both objects are Vectors,
            to the left side multiplication (pre-multiplication) of u by matrix v when v is a Matrix,
            to element wise multiplication when v is a sequence,
            and multiplies each component of u by v when v is a numeric type. """
        try :
            res = self.apicls.__rmul__(self, other)
        except :
            res = super(MVector, self).__rmul__(other)
        if util.isNumeric(res) :
            return res
        else :
            return self.__class__._convert(res)
    def __imul__(self, other):
        """ u.__imul__(v) <==> u *= v
            Valid for MVector * MMatrix multiplication, in place transformation of u by MMatrix v
            or MVector by scalar multiplication only """
        try :
            return self.__class__(self.__mul__(other))
        except :
            return NotImplemented         
    # special operators
    def __xor__(self, other):
        """ u.__xor__(v) <==> u^v
            Defines the cross product operator between two 3D vectors,
            if v is a Matrix, u^v is equivalent to u.transformAsNormal(v) """
        if isinstance(other, Vector) :
            return self.cross(other)
        elif isinstance(other, Matrix) :
            return self.transformAsNormal(other)
        else :
            return NotImplemented
    def __ixor__(self, other):
        """ u.__xor__(v) <==> u^=v
            Inplace cross product or transformation by inverse transpose of v is v is a Matrix """
        try :        
            return self.__class__(self.__xor__(other))
        except :
            return NotImplemented        
         
    # wrap of other API MVector methods, we use the api method if possible and delegate to Vector else   
    
    def isEquivalent(self, other, tol=None):
        """ Returns true if both arguments considered as MVector are equal within the specified tolerance """
        if tol is None :
            tol = _api.MVector_kTol
        try :
            nself, nother = coerce(self, other)
        except :
            return False                 
        if isinstance(nself, MVector) :
            return bool(nself.apicls.isEquivalent(nself, nother, tol))
        else :
            return bool(super(MVector, nself).isEquivalent(nother, tol))            
    def isParallel(self, other, tol=None):
        """ Returns true if both arguments considered as MVector are parallel within the specified tolerance """
        if tol is None :
            tol = _api.MVector_kTol        
        try :
            return bool(self.apicls.isParallel(MVector(self), MVector(other), tol))
        except :
            return super(MVector, self).isParallel(other, tol)
    def distanceTo(self, other):
        try :
            return MPoint.apicls.distanceTo(MPoint(self), MPoint(other))
        except :
            return super(MVector, self).dist(other)
    def length(self):
        """ Return the length of the vector """
        return MVector.apicls.length(MVector(self))
    def sqlength(self):
        """ Return the square length of the vector """
        return self.dot(self)          
    def normal(self): 
        """ Return a normalized copy of self """ 
        return self.__class__(MVector.apicls.normal(MVector(self)))
    def normalize(self):
        """ Performs an in place normalization of self """
        if type(self) is MVector :
            MVector.apicls.normalize(self)
        else :
            self.assign(v.normal())
        
    # additional api methods that work on MVector only, and don't have an equivalent on Vector

    def rotateTo(self, other):
        """ u.rotateTo(v) --> MQuaternion
            Returns the MQuaternion that represents the rotation of the MVector u into the MVector v
            around their mutually perpendicular axis. It amounts to rotate u by angle(u, v) around axis(u, v) """
        if isinstance(other, MVector) :
            return MQuaternion(MVector.apicls.rotateTo(MVector(self), MVector(other)))
        else :
            raise TypeError, "%r is not a MVector instance" % other
    def rotateBy(self, *args):
        """ u.rotateBy(*args) --> MVector
            Returns the result of rotating u by the specified arguments.
            There are several ways the rotation can be specified:
            args is a tuple of one MMatrix, MTransformationMatrix, MQuaternion, MEulerRotation
            arg is tuple of 4 arguments, 3 rotation value and an optionnal rotation order
            args is a tuple of one MVector, the axis and one float, the angle to rotate around that axis """
        if args :
            if len(args) == 2 and isinstance(args[0], MVector) :
                return self.__class__(self.apicls.rotateBy(self, MQuaternion(MVector(args[0]), float(args[1]))))
            elif len(args) == 1 and isinstance(args[0], MMatrix) :
                return self.__class__(self.apicls.rotateBy(self, args[0].rotate))         
            else :
                return self.__class__(self.apicls.rotateBy(self, MEulerRotation(*args)))
        else :
            return self
    
    # additional api methods that work on MVector only, but can also be delegated to Vector
      
    def transformAsNormal(self, other):
        """ Returns the vector transformed by the matrix as a normal
            Normal vectors are not transformed in the same way as position vectors or points.
            If this vector is treated as a normal vector then it needs to be transformed by
            post multiplying it by the inverse transpose of the transformation matrix.
            This method will apply the proper transformation to the vector as if it were a normal. """
        if isinstance(other, MMatrix) :
            return self.__class__._convert(MVector.apicls.transformAsNormal(MVector(self), MMatrix(other)))
        else :
            return self.__class__._convert(super(MVector, self).transformAsNormal(other))
    def dot(self, other):
        """ dot product of two vectors """
        if isinstance(other, MVector) :
            return MVector.apicls.__mul__(MVector(self), MVector(other))
        else :
            return super(MVector, self).dot(other)       
    def cross(self, other):
        """ cross product, only defined for two 3D vectors """
        if isinstance(other, MVector) :
            return self.__class__._convert(MVector.apicls.__xor__(MVector(self), MVector(other)))
        else :
            return self.__class__._convert(super(MVector, self).cross(other))              
    def axis(self, other, normalize=False):
        """ u.axis(v) <==> angle(u, v) --> MVector
            Returns the axis of rotation from u to v as the vector n = u ^ v
            if the normalize keyword argument is set to True, n is also normalized """
        if isinstance(other, MVector) :
            if normalize :
                return self.__class__._convert(MVector.apicls.__xor__(MVector(self), MVector(other)).normal())
            else :
                return self.__class__._convert(MVector.apicls.__xor__(MVector(self), MVector(other)))
        else :
            return self.__class__._convert(super(MVector, self).axis(other, normalize)) 
    def angle(self, other):
        """ u.angle(v) <==> angle(u, v) --> float
            Returns the angle (in radians) between the two vectors u and v
            Note that this angle is not signed, use axis to know the direction of the rotation """
        if isinstance(other, MVector) :
            return MVector.apicls.angle(MVector(self), MVector(other))
        else :
            return super(MVector, self).angle(other)  
        
    # methods without an api equivalent    
        
    # cotan on MVectors only takes 2 arguments          
    def cotan(self, other):
        """ u.cotan(v) <==> cotan(u, v) --> float :
            cotangent of the a, b angle, a and b should be MVectors"""
        return Vector.cotan(self, other)
                                   
    # rest derived from Vector class

class MFloatVector(MVector) :
    """ A 3 dimensional vector class that wraps Maya's api MFloatVector class,
        It behaves identically to MVector, but it also derives from api's MFloatVector
        to keep api methods happy
        """
    apicls = _api.MFloatVector
 
# MPoint specific functions

def planar(p, *args, **kwargs): 
    """ planar(p[, q, r, s (...), tol=tolerance]) --> bool
        Returns True if all provided MPoints are planar within given tolerance """
    if not isinstance(p, MPoint) :
        try :
            p = MPoint(p)
        except :
            raise TypeError, "%s is not convertible to type MPoint, planar is only defined for n MPoints" % (util.clsname(p))           
    return p.planar(*args, **kwargs)
def center(p, *args): 
    """ center(p[, q, r, s (...)]) --> MPoint
        Returns the MPoint that is the center of p, q, r, s (...) """
    if not isinstance(p, MPoint) :
        try :
            p = MPoint(p)
        except :
            raise TypeError, "%s is not convertible to type MPoint, center is only defined for n MPoints" % (util.clsname(p))           
    return p.center(*args)
def bWeights(p, *args):  
    """ bWeights(p[, p0, p1, (...), pn]) --> tuple
        Returns a tuple of (n0, n1, ...) normalized barycentric weights so that n0*p0 + n1*p1 + ... = p  """
    if not isinstance(p, MPoint) :
        try :
            p = MPoint(p)
        except :
            raise TypeError, "%s is not convertible to type MPoint, bWeights is only defined for n MPoints" % (util.clsname(p))           
    return p.bWeights(*args)

               
class MPoint(MVector):
    """ A 4 dimensional vector class that wraps Maya's api MPoint class,
        """    
    apicls = _api.MPoint
    cnames = ('x', 'y', 'z', 'w')
    shape = (4,)

    def __melobject__(self):
        """Special method for returning a mel-friendly representation. In this case, a cartesian 3D point """
        return self.cartesian()
    
#    # base methods are inherited from MVector

    # we only show the x, y, z components on an iter
    def __len__(self):
        l = len(self.data)
        if self.w == 1.0 :
            l -= 1
        return l
    def __iter__(self, *args, **kwargs):
        """ Iterate on the api components """
        l = len(self)
        for c in list(self.apicls.__iter__(self.data))[:l] :
            yield c
               
    # modified operators, when adding 2 MPoint consider second as MVector
    def __add__(self, other) :
        """ u.__add__(v) <==> u+v
            Returns the result of the addition of u and v if v is convertible to a Vector (element-wise addition),
            adds v to every component of u if v is a scalar """ 
        # prb with coerce when delegating to Vector, either redefine coerce for MPoint or other fix
        # if isinstance(other, MPoint) :
        #    other = MVector(other)   
        try :
             other = MVector(other) 
        except :
            pass   
        try :
            return self.__class__._convert(self.apicls.__add__(self, other))
        except :
            return self.__class__._convert(super(Vector, self).__add__(other)) 
    def __radd__(self, other) :
        """ u.__radd__(v) <==> v+u
            Returns the result of the addition of u and v if v is convertible to a Vector (element-wise addition),
            adds v to every component of u if v is a scalar """ 
        if isinstance(other, MPoint) :
            other = MVector(other)                       
        try :
            return self.__class__._convert(self.apicls.__radd__(self, other))
        except :
            return self.__class__._convert(super(MPoint, self).__radd__(other))  
    def __iadd__(self, other):
        """ u.__iadd__(v) <==> u += v
            In place addition of u and v, see __add__ """
        try :
            return self.__class__(self.__add__(other))
        except :
            return NotImplemented     
  
          
    # specific api methods
    def cartesianize (self) :
        """ p.cartesianize() --> MPoint
            If the point instance p is of the form P(W*x, W*y, W*z, W), for some scale factor W != 0,
            then it is reset to be P(x, y, z, 1).
            This will only work correctly if the point is in homogenous form or cartesian form.
            If the point is in rational form, the results are not defined. """
        return self.__class__(self.apicls.cartesianize(self))
    def cartesian (self) :
        """ p.cartesian() --> MPoint
            Returns the cartesianized version of p, without changing p. """
        t = copy.deepcopy(self)
        self.apicls.cartesianize(t)
        return t   
    def rationalize (self) :
        """ p.rationalize() --> MPoint
            If the point instance p is of the form P(W*x, W*y, W*z, W) (ie. is in homogenous or (for W==1) cartesian form),
            for some scale factor W != 0, then it is reset to be P(x, y, z, W).
            This will only work correctly if the point is in homogenous or cartesian form.
            If the point is already in rational form, the results are not defined. """
        return self.__class__(self.apicls.rationalize(self))
    def rational (self) :
        """ p.rational() --> MPoint
            Returns the rationalized version of p, without changing p. """
        t = copy.deepcopy(self)
        self.apicls.rationalize(t)
        return t
    def homogenize (self) :
        """ p.homogenize() --> MPoint
            If the point instance p is of the form P(x, y, z, W) (ie. is in rational or (for W==1) cartesian form),
            for some scale factor W != 0, then it is reset to be P(W*x, W*y, W*z, W). """
        return self.__class__(self.apicls.homogenize(self))
    def homogen (self) :
        """ p.homogen() --> MPoint
            Returns the homogenized version of p, without changing p. """
        t = copy.deepcopy(self)
        self.apicls.homogenize(t)
        return t    
    
    # additionnal methods
    
    def isEquivalent(self, other, tol=None):
        """ Returns true if both arguments considered as MPoint are equal within the specified tolerance """
        if tol is None :
            tol = _api.MPoint_kTol
        try :
            nself, nother = coerce(self, other)
        except :
            return False                 
        if isinstance(nself, MPoint) :
            return bool(nself.apicls.isEquivalent(nself, nother, tol))
        else :
            return bool(super(MPoint, nself).isEquivalent(nother, tol))  
    def axis(self, start, end, normalize=False):
        """ a.axis(b, c) --> MVector
            Returns the axis of rotation from point b to c around a as the vector n = (b-a)^(c-a)
            if the normalize keyword argument is set to True, n is also normalized """
        return MVector.axis(start-self, end-self, normalize=normalize)
    def angle(self, start, end):
        """ a.angle(b, c) --> float
            Returns the angle (in radians) of rotation from point b to c around a.
            Note that this angle is not signed, use axis to know the direction of the rotation """
        return MVector.angle(start-self, end-self)               
    def cotan(self, start, end):
        """ a.cotan(b, c) --> float :
            cotangent of the (b-a), (c-a) angle, a, b, and c should be MPoints representing points a, b, c"""        
        return Vector.cotan(start-self, end-self)        
    def planar(self, *args, **kwargs): 
        """ p.planar(q, r, s (...), tol=tolerance) --> bool
            Returns True if all provided points are planar within given tolerance """
        if len(args) > 2 :
            tol = kwargs.get('tol', None)
            n = (args[0]-self)^(args[1]-self)
            return reduce(operator.and_, map(lambda x:n.isParallel(x, tol), [(args[0]-self)^(a-self) for a in args[2:]]), True)
        else :
            return True
    def center(self, *args): 
        """ p.center(q, r, s (...)) --> MPoint
            Returns the MPoint that is the center of p, q, r, s (...) """
        return sum((self,)+args) / float(len(args) + 1)
    def bWeights(self, *args): 
        """ p.bWeights(p0, p1, (...), pn) --> tuple
            Returns a tuple of (n0, n1, ...) normalized barycentric weights so that n0*p0 + n1*p1 + ... = p.
            This method works for n points defining a concave or convex n sided face,
            always returns positive normalized weights, and is continuous on the face limits (on the edges),
            but the n points must be coplanar, and p must be inside the face delimited by (p0, ..., pn) """
        if args :
            p = self
            q = list(args)
            np = len(q)            
            w = Vector(0.0, size=np)
            weightSum = 0.0
            pOnEdge = False;
            tol = _api.MPoint_kTol
            # all args should be MPoints
            for i in xrange(np) :
                if not isinstance(q[i], MPoint) :
                    try :
                        q[i] = MPoint(q[i])
                    except :
                        raise TypeError, "cannot convert %s to MPoint, bWeights is defined for n MPoints" % (util.clsname(q[i]))
            # if p sits on an edge, it' a limit case and there is an easy solution,
            # all weights are 0 but for the 2 edge end points
            for i in xrange(np) :
                next = (i+1) % np
                   
                e = ((q[next]-q[i]) ^ (p-q[i])).sqlength()
                l = (q[next]-q[i]).sqlength()
                if e <= (tol * l) :
                    if l < tol :
                        # p is on a 0 length edge, point and next point are on top of each other, as is p then
                        w[i] = 0.5
                        w[next] = 0.5
                    else :
                        # p is somewhere on that edge between point and next point
                        di = (p-q[i]).length()
                        w[next] = float(di / sqrt(l))
                        w[i] = 1.0 - w[next]
                    # in both case update the weights sum and mark p as being on an edge,
                    # problem is solved
                    weightSum += 1.0
                    pOnEdge = True
                    break         
            # If p not on edge, use the cotangents method
            if not pOnEdge :
                for i in xrange(np) :
                    prev = (i+np-1) % np
                    next = (i+1) % np
        
                    lenSq = (p - q[i]).sqlength()
                    w[i] = ( q[i].cotan(p, q[prev]) + q[i].cotan(p, q[next]) ) / lenSq
                    weightSum += w[i]
    
            # then normalize result
            if abs(weightSum) :
                w /= weightSum
            else :
                raise ValueError, "failed to compute bWeights for %s and %s.\nThe point bWeights are computed for must be inside the planar face delimited by the n argument points" % (self, args)
        
            return tuple(w)               
        else :
            return ()  


class MFloatPoint(MPoint) :
    """ A 4 dimensional vector class that wraps Maya's api MFloatPoint class,
        It behaves identically to MPoint, but it also derives from api's MFloatPoint
        to keep api methods happy
        """    
    apicls = _api.MFloatPoint    
    
    
class MColor(MVector):
    """ A 4 dimensional vector class that wraps Maya's api MColor class,
        It stores the r, g, b, a components of the color, as normalized (Python) floats
        """        
    apicls = _api.MColor
    cnames = ('r', 'g', 'b', 'a')
    shape = (4,)
    # modes = ('rgb', 'hsv', 'cmy', 'cmyk')
    modes = ('rgb', 'hsv')
    
    # constants
    red = _api.MColor(1.0, 0.0, 0.0)
    green = _api.MColor(0.0, 1.0, 0.0)
    blue = _api.MColor(0.0, 0.0, 1.0)
    white = _api.MColor(1.0, 1.0, 1.0)
    black = _api.MColor(0.0, 0.0, 0.0)
    opaque = _api.MColor(0.0, 0.0, 0.0, 1.0)
    clear = _api.MColor(0.0, 0.0, 0.0, 0.0)

    # static methods
    @staticmethod
    def rgbtohsv(c):
        c = tuple(c)
        return tuple(colorsys.rgb_to_hsv(*clamp(c[:3]))+c[3:4])
    @staticmethod
    def hsvtorgb(c):
        c = tuple(c)
        # return colorsys.hsv_to_rgb(clamp(c[0]), clamp(c[1]), clamp(c[2]))
        return tuple(colorsys.hsv_to_rgb(*clamp(c[:3]))+c[3:4])
    
    # TODO : could define rgb and hsv iterators and allow __setitem__ and __getitem__ on these iterators
    # like (it's more simple) it's done in ArrayIter  
    def _getrgba(self):
        return tuple(self)
    def _setrgba(self, value):
        if not hasattr(value, '__iter__') :
            # the way api interprets a single value
            # value = (None, None, None, value)
            value = (value,)*4
        l = list(self)
        for i, v in enumerate(value[:4]) :
            if v is not None :
                l[i] = float(v)
        self.assign(*l)
    rgba = property(_getrgba, _setrgba, None, "The r,g,b,a MColor components""")       
    def _getrgb(self):
        return self.rgba[:3]
    def _setrgb(self, value):
        if not hasattr(value, '__iter__') :
            value = (value,)*3
        self.rgba = value[:3]
    rgb = property(_getrgb, _setrgb, None, "The r,g,b MColor components""")
    
    def _gethsva(self):
        return tuple(MColor.rgbtohsv(self))
    def _sethsva(self, value):
        if not hasattr(value, '__iter__') :
            # the way api interprets a single value
            # value = (None, None, None, value)
            value = (value,)*4
        l = list(MColor.rgbtohsv(self))
        for i, v in enumerate(value[:4]) :
            if v is not None :
                l[i] = float(v)
        self.assign(*MColor.hsvtorgb(self))   
    hsva = property(_gethsva, _sethsva, None, "The h,s,v,a MColor components""") 
    def _gethsv(self):
        return tuple(MColor.rgbtohsv(self))[:3]
    def _sethsv(self, value):
        if not hasattr(value, '__iter__') :
            value = (value,)*3
        self.hsva = value[:3]  
    hsv = property(_gethsv, _sethsv, None, "The h,s,v,a MColor components""")
    def _geth(self):
        return self.hsva[0]
    def _seth(self, value):
        self.hsva = (value, None, None, None)  
    h = property(_geth, _seth, None, "The h MColor component""")            
    def _gets(self):
        return self.hsva[1]
    def _sets(self, value):
        self.hsva = (None, value, None, None)  
    s = property(_gets, _sets, None, "The s MColor component""") 
    def _getv(self):
        return self.hsva[2]
    def _setv(self, value):
        self.hsva = (None, None, value, None)  
    v = property(_getv, _setv, None, "The v MColor component""") 
        
    # __new__ is herited from MPoint/MVector, need to override __init__ to accept hsv mode though    
                           
    def __init__(self, *args, **kwargs):
        """ Init a MColor instance
            Can pass one argument being another MColor instance , or the color components """
        cls = self.__class__
        mode = kwargs.get('mode', None)
        if mode is not None and mode not in cls.modes :
            raise ValueError, "unknown mode %s for %s" % (mode, util.clsname(self))
        # can also use the form <componentname>=<number>
        # for now supports only rgb and hsv flags
        hsvflag = {}
        rgbflag = {}
        for a in 'hsv' :
            if a in kwargs :
                hsvflag[a] = kwargs[a]
        for a in 'rgb' :
            if a in kwargs :
                rgbflag[a] = kwargs[a]
        # can't mix them
        if hsvflag and rgbflag :
            raise ValueError, "can not mix r,g,b and h,s,v keyword arguments in a %s declaration" % util.clsname(self)
        # if no mode specified, guess from what keyword arguments where used, else use 'rgb' as default
        if mode is None :
            if hsvflag :
                mode = 'hsv'
            else :
                mode = 'rgb'
        # can't specify a mode and use keywords of other modes
        if mode is not 'hsv' and hsvflag :
            raise ValueError, "Can not use h,s,v keyword arguments while specifying %s mode in %s" % (mode, util.clsname(self))
        elif mode is not 'rgb' and rgbflag :
            raise ValueError, "Can not use r,g,b keyword arguments while specifying %s mode in %s" % (mode, util.clsname(self))
        # NOTE: do not try to use mode with _api.MColor, it seems bugged as of 2008
            #import colorsys
            #colorsys.rgb_to_hsv(0.0, 0.0, 1.0)
            ## Result: (0.66666666666666663, 1.0, 1.0) # 
            #c = _api.MColor(_api.MColor.kHSV, 0.66666666666666663, 1.0, 1.0)
            #print "# Result: ",c[0], c[1], c[2], c[3]," #"
            ## Result:  1.0 0.666666686535 1.0 1.0  #
            #c = _api.MColor(_api.MColor.kHSV, 0.66666666666666663*360, 1.0, 1.0)
            #print "# Result: ",c[0], c[1], c[2], c[3]," #"
            ## Result:  1.0 240.0 1.0 1.0  #
            #colorsys.hsv_to_rgb(0.66666666666666663, 1.0, 1.0)
            ## Result: (0.0, 0.0, 1.0) #  
        # we'll use MColor only to store RGB values internally and do the conversion a read/write if desired
        # which I think make more sense anyway       
        # quantize (255, 65535, no quantize means colors are 0.0-1.0 float values)
        # Initializing api's MColor with int values seems also not to always behave so we quantize first and 
        # use a float init always
        quantize = kwargs.get('quantize', None)
        if quantize is not None :
            try :
                quantize = float(quantize)
            except :
                raise ValueError, "quantize must be a numeric value, not %s" % (util.clsname(quantize)) 
        # can be initilized with a single argument (other MColor, MVector, Vector)
        if len(args)==1 :
            args = args[0]              
        # we dont rely much on MColor api as it doesn't seem totally finished, and do some things directly here               
        if isinstance(args, self.__class__) or isinstance(args, self.apicls) :
            # alternatively could be just ignored / output as warning
            if quantize :
                raise ValueError, "Can not quantize a MColor argument, a MColor is always stored internally as float color" % (mode, util.clsname(self))
            if mode == 'rgb' :
                args = Vector(args)
            elif mode == 'hsv' :
                args = Vector(cls.rgbtohsv(args))
        else :
            # single alpha value, as understood by api will break coerce behavior in operations
            # where other operand is a scalar
            #if not hasattr(args, '__iter__') :
            #    args = Vector(0.0, 0.0, 0.0, args)
            if hasattr(args, '__len__') :
                shape = (min(len(args), cls.size),)
            else :
                shape = cls.shape
            args = Vector(args, shape=shape)
            # quantize if needed
            if quantize :
                args /= quantize
            # pad to a full MColor size
            args.stack(self[len(args):]) 
                     
        # apply keywords arguments, and convert if mode is not rgb   
        if mode == 'rgb' :
            if rgbflag :
                for i, a in enumerate('rgb') :
                    if a in rgbflag :  
                        if quantize :
                            args[i] = float(rgbflag[a]) / quantize
                        else :                                                   
                            args[i] = float(rgbflag[a])                          
        elif mode == 'hsv' :
            if hsvflag :
                for i, a in enumerate('hsv') :
                    if a in hsvflag : 
                        if quantize :
                            args[i] = float(hsvflag[a]) / quantize
                        else :                                                   
                            args[i] = float(hsvflag[a])   
            args = Vector(cls.hsvtorgb(args))
        # finally alpha keyword
        a = kwargs.get('a', None)
        if a is not None :
            if quantize :
                args[-1] = float(a) / quantize
            else :
                args[-1] = float(a)
                                      
        try :
            self.assign(args)
        except :
            msg = ", ".join(map(lambda x,y:x+"=<"+util.clsname(y)+">", mode, args))
            raise TypeError, "in %s(%s), at least one of the components is of an invalid type, check help(%s) " % (util.clsname(self), msg, util.clsname(self))                                 

    def __melobject__(self):
        """Special method for returning a mel-friendly representation. In this case, a 3-component color (RGB) """
        return [self.r, self.g, self.b]
            
    # overriden operators
    
    # defined for two MColors only
    def __add__(self, other) :
        """ c.__add__(d) <==> c+d
            Returns the result of the addition of MColors c and d if d is convertible to a MColor,
            adds d to every component of c if d is a scalar """ 
        # prb with coerce when delegating to Vector, either redefine coerce for MPoint or other fix
        # if isinstance(other, MPoint) :
        #    other = MVector(other)   
        try :
            other = MColor(other) 
        except :
            pass   
        try :
            return self.__class__._convert(self.apicls.__add__(self, other))
        except :
            return self.__class__._convert(super(Vector, self).__add__(other)) 
    def __radd__(self, other) :
        """ c.__radd__(d) <==> d+c
            Returns the result of the addition of MColors c and d if d is convertible to a MColor,
            adds d to every component of c if d is a scalar """ 
        try :
            other = MColor(other) 
        except :
            pass                        
        try :
            return self.__class__._convert(self.apicls.__radd__(self, other))
        except :
            return self.__class__._convert(super(MPoint, self).__radd__(other))  
    def __iadd__(self, other):
        """ c.__iadd__(d) <==> c += d
            In place addition of c and d, see __add__ """
        try :
            return self.__class__(self.__add__(other))
        except :
            return NotImplemented   
    def __sub__(self, other) :
        """ c.__add__(d) <==> c+d
            Returns the result of the substraction of MColor d from c if d is convertible to a MColor,
            substract d from every component of c if d is a scalar """  
        try :
            other = MColor(other) 
        except :
            pass   
        try :
            return self.__class__._convert(self.apicls.__sub__(self, other))
        except :
            return self.__class__._convert(super(Vector, self).__sub__(other)) 
    def __rsub__(self, other) :
        """ c.__rsub__(d) <==> d-c
            Returns the result of the substraction of MColor c from d if d is convertible to a MColor,
            replace every component c[i] of c by d-c[i] if d is a scalar """  
        try :
            other = MColor(other) 
        except :
            pass                        
        try :
            return self.__class__._convert(self.apicls.__rsub__(self, other))
        except :
            return self.__class__._convert(super(MPoint, self).__rsub__(other))  
    def __isub__(self, other):
        """ c.__isub__(d) <==> c -= d
            In place substraction of d from c, see __sub__ """
        try :
            return self.__class__(self.__sub__(other))
        except :
            return NotImplemented             
    # action depends on second object type
    # TODO : would be nice to define LUT classes and allow MColor * LUT transform
    # overloaded operators
    def __mul__(self, other):
        """ a.__mul__(b) <==> a*b
            If b is a 1D sequence (Array, Vector, MColor), __mul__ is mapped to element-wise multiplication,
            If b is a Matrix, __mul__ is similar to Point a by Matrix b multiplication (post multiplication or transformation of a by b),
            multiplies every component of a by b if b is a single numeric value """
        if isinstance(other, Matrix) :
            # will defer to Matrix rmul
            return NotImplemented
        else :
            # will defer to Array.__mul__
            return Array.__mul__(self, other)
    def __rmul__(self, other):
        """ a.__rmul__(b) <==> b*a
            If b is a 1D sequence (Array, Vector, MColor), __mul__ is mapped to element-wise multiplication,
            If b is a Matrix, __mul__ is similar to Matrix b by Point a matrix multiplication,
            multiplies every component of a by b if b is a single numeric value """     
        if isinstance(other, Matrix) :
            # will defer to Matrix mul
            return NotImplemented
        else :
            # will defer to Array.__rmul__
            return Array.__rmul__(self, other)
    def __imul__(self, other):
        """ a.__imul__(b) <==> a *= b
            In place multiplication of Vector a and b, see __mul__, result must fit a's type """      
        res = self*other
        if isinstance(res, self.__class__) :
            return self.__class__(res)        
        else :
            raise TypeError, "result of in place multiplication of %s by %s is not a %s" % (clsname(self), clsname(other), clsname(self))      
 
             
    # additionnal methods, to be extended
    def over(self, other):
        """ c1.over(c2): Composites c1 over other c2 using c1's alpha, the resulting color has the alpha of c2 """
        if isinstance(other, MColor) :
            a = self.a
            return MColor(MVector(other).blend(MVector(self), self.a), a=other.a)            
        else :
            raise TypeError, "over is defined for MColor instances, not %s" % (util.clsname(other))
    # return MVector instead ? Keeping alpha doesn't make much sense
    def premult(self):
        """ Premultiply MColor r, g and b by it's alpha and resets alpha to 1.0 """
        return self.__class__(MVector(self)*self.a)                       
    def gamma(self, g):
        """ c.gamma(g) applies gamma correction g to MColor c, g can be a scalar and then will be applied to r, g, b
            or an iterable of up to 3 (r, g, b) independant gamma correction values """ 
        if not hasattr(g, '__iter__') :
            g = (g,)*3+(1.0,)
        else :
            g = g[:3]+(1.0,)*(4-len(g[:3]))        
        return gamma(self, g)
    def hsvblend(self, other, weight=0.5):
        """ c1.hsvblend(c2) --> MColor
            Returns the result of blending c1 with c2 in hsv space, using the given weight """
        c1 = list(self.hsva)
        c2 = list(other.hsva)
        if abs(c2[0]-c1[0]) >= 0.5 :
            if abs(c2[0]-c1[0]) == 0.5 :
                c1[1], c2[1] = 0.0, 0.0
            if c1[0] > 0.5 :
                c1[0] -= 1.0
            if c2[0] > 0.5 :
                c2[0] -= 1.0
        c = blend(c1, c2, weight=weight)
        if c[0] < 0.0 :
            c[0] += 1.0      
        return self.__class__(c, mode='hsv')
  

# to specify space of transforms

class MSpace(_api.MSpace):
    apicls = _api.MSpace
    __metaclass__ = _factories.MetaMayaTypeWrapper
    pass

#kInvalid
#    kTransform
#Transform matrix (relative) space
#    kPreTransform
#Pre-transform matrix (geometry)
#    kPostTransform
#Post-transform matrix (world) space
#    kWorld
#transform in world space
#    kObject
#Same as pre-transform space
#    kLast 

# sadly MTransformationMatrix.RotationOrder and MEulerRotation.RotationOrder don't match

#class MRotationOrder(int):
#    pass

#kInvalid
#    kXYZ
#    kYZX
#    kZXY
#    kXZY
#    kYXZ
#    kZYX
#    kLast 


#    kXYZ
#    kYZX
#    kZXY
#    kXZY
#    kYXZ
#    kZYX 

# functions that work on Matrix (det(), inv(), ...) herited from arrays
# and properly defer to the class methods

# For row, column order, see the definition of a MTransformationMatrix in docs :
# T  = |  1    0    0    0 |
#      |  0    1    0    0 |
#      |  0    0    1    0 |
#      |  tx   ty   tz   1 |
# and m(r, c) should return value of cell at r row and c column :
# t = _api.MTransformationMatrix()
# t.setTranslation(_api.MVector(1, 2, 3), _api.MSpace.kWorld)
# m = t.asMatrix()
# mm(3,0)
# 1.0
# mm(3,1)
# 2.0
# mm(3,2)
# 3.0  

class MMatrix(Matrix):
    """ A 4x4 transformation matrix based on api MMatrix 
        >>> v = self.__class__(1, 2, 3)
        >>> w = self.__class__(x=1, z=2)
        >>> z = self.__class__(_api.Mself.__class__.xAxis, z=1)
        """    
    __metaclass__ = MetaMayaArrayTypeWrapper
    apicls = _api.MMatrix
    shape = (4, 4)
    cnames = ('a00', 'a01', 'a02', 'a03',
               'a10', 'a11', 'a12', 'a13',
               'a20', 'a21', 'a22', 'a23',
               'a30', 'a31', 'a32', 'a33' ) 
    
    # constants
    
    identity = _api.MMatrix()

    def __new__(cls, *args, **kwargs):
        shape = kwargs.get('shape', None)
        ndim = kwargs.get('ndim', None)
        size = kwargs.get('size', None)
        # will default to class constant shape = (4, 4), so it's just an error check to catch invalid shapes,
        # as no other option is actually possible on MMatrix, but this method could be used to allow wrapping
        # of Maya array classes that can have a variable number of elements
        shape, ndim, size = cls._expandshape(shape, ndim, size)        
        
        new = cls.apicls.__new__(cls)
        cls.apicls.__init__(new)
        return new
        
    def __init__(self, *args, **kwargs):
        """ __init__ method, valid for MVector, MPoint and MColor classes """
        cls = self.__class__
                
        if args :
            # allow both forms for arguments
            if len(args)==1 and hasattr(args[0], '__iter__') :
                args = args[0]
#            shape = kwargs.get('shape', None)
#            ndim = kwargs.get('ndim', None)
#            size = kwargs.get('size', None)
#            if shape is not None or ndim is not None or size is not None :
#                shape, ndim, size = cls._expandshape(shape, ndim, size) 
#                args = Matrix(args, shape=shape, ndim=ndim, size=size)                         
            # shortcut when a direct api init is possible     
            try :
                self.assign(args)
            except :
                super(Matrix, self).__init__(*args)
                # value = list(Matrix(value, shape=self.shape).flat)
                # data = self.apicls()
                # _api.MScriptUtil.createMatrixFromList ( value, data ) 
            
        if hasattr(cls, 'cnames') and len(set(cls.cnames) & set(kwargs)) :  
            # can also use the form <componentname>=<number>
            l = list(self.flat)
            setcomp = False
            for i, c in enumerate(cls.cnames) :
                if c in kwargs :
                    if float(l[i]) != float(kwargs[c]) :
                        l[i] = float(kwargs[c])
                        setcomp = True
            if setcomp :
                try :
                    self.assign(l)
                except :
                    msg = ", ".join(map(lambda x,y:x+"=<"+util.clsname(y)+">", cls.cnames, l))
                    raise TypeError, "in %s(%s), at least one of the components is of an invalid type, check help(%s) " % (cls.__name__, msg, cls.__name__) 

    # for compatibility with base classes Array that actually hold a nested list in their _data attribute
    # here, there is no _data attribute as we subclass api.MVector directly, thus v.data is v
    # for wraps 

    def _getdata(self):
        return self
    def _setdata(self, value):
        self.assign(value) 
    def _deldata(self):
        if hasattr(self.apicls, 'clear') :
            self.apicls.clear(self)  
        else :
            raise TypeError, "cannot clear stored elements of %s" % (self.__class__.__name__)
                                
    data = property(_getdata, _setdata, _deldata, "The MMatrix/MFloatMatrix/MTransformationMatrix/MQuaternion/MEulerRotation data") 
    
    # set properties for easy acces to translation / rotation / scale of a MMatrix or derived class
    # some of these will only yield dependable results if MMatrix is a MTransformationMatrix and some
    # will always be zero for some classes (ie only rotation has a value on a MQuaternion
    
    def _getTranslate(self):
        t = MTransformationMatrix(self)
        return MVector(t.getTranslation(MSpace.kTransform))     
    def _setTranslate(self, value):
        t = MTransformationMatrix(self)
        t.setTranslation ( MVector(value), MSpace.kTransform )
        self.assign(t.asMatrix())
    translate = property(_getTranslate, _setTranslate, None, "The translation expressed in this MMatrix, in transform space") 
    def _getRotate(self):
        t = MTransformationMatrix(self)
        return MQuaternion(t.rotation())  
    def _setRotate(self, value):
        t = MTransformationMatrix(self)
        q = MQuaternion(value)
        t.rotateTo(q)
        # values = (q.x, q.y, q.z, q.w)
        # t.setRotationQuaternion(q.x, q.y, q.z, q.w)
        self.assign(t.asMatrix())
    rotate = property(_getRotate, _setRotate, None, "The rotation expressed in this MMatrix, in transform space") 
    def _getScale(self):
        t = MTransformationMatrix(self)
        ms = _api.MScriptUtil()
        ms.createFromDouble ( 1.0, 1.0, 1.0 )
        p = ms.asDoublePtr ()
        t.getScale (p, MSpace.kTransform);
        return MVector([ms.getDoubleArrayItem (p, i) for i in range(3)])        
    def _setScale(self, value):
        t = MTransformationMatrix(self)
        ms = _api.MScriptUtil()
        ms.createFromDouble (*MVector(value))
        p = ms.asDoublePtr ()
        t.setScale ( p, MSpace.kTransform)        
        self.assign(t.asMatrix())
    scale = property(_getScale, _setScale, None, "The scale expressed in this MMatrix, in transform space")  

    def __melobject__(self):
        """Special method for returning a mel-friendly representation. In this case, a flat list of 16 values """
        return [ x for x in self.flat ]
           
    # some MMatrix derived classes can actually be represented as matrix but not stored
    # internally as such by the API
    
    def asMatrix(self, percent=None):
        "The matrix representation for this MMatrix/MTransformationMatrix/MQuaternion/MEulerRotation instance"
        if percent is not None and percent != 1.0 :
            if type(self) is not MTransformationMatrix :
                self = MTransformationMatrix(self)
            return MMatrix(self.apicls.asMatrix(self, percent))
        else :
            if type(self) is MMatrix :
                return self
            else :
                return MMatrix(self.apicls.asMatrix(self))  
                  
    matrix = property(asMatrix, None, None, "The MMatrix representation for this MMatrix/MTransformationMatrix/MQuaternion/MEulerRotation instance")                 
                          
    # overloads for assign and get though standard way should be to use the data property
    # to access stored values                                                                    
    def assign(self, value):
        # don't accept instances as assign works on exact api.MMatrix type
        data = None
        if type(value) == self.apicls or type(value) == type(self) :
            data = value
        elif hasattr(value, 'asMatrix') :
            data = value.asMatrix()
        else :
            value = list(Matrix(value).flat)
            if len(value) == self.size :
                data = self.apicls()
                _api.MScriptUtil.createMatrixFromList ( value, data ) 
            else :
                raise TypeError, "cannot assign %s to a %s" % (value, util.clsname(self))
        
        self.apicls.assign(self, data)
        return self
   
    # API get, actually not faster than pulling self[i] for such a short structure
    def get(self):
        """ Wrap the MMatrix api get method """
        mat = self.matrix
        return tuple(tuple(_api.MScriptUtil.getDoubleArrayItem ( _api.MMatrix.__getitem__(mat, r), c) for c in xrange(MMatrix.shape[1])) for r in xrange(MMatrix.shape[0]))
        # ptr = _api.MMatrix(self.matrix).matrix
        # return tuple(tuple(_api.MScriptUtil.getDouble2ArrayItem ( ptr, r, c) for c in xrange(MMatrix.shape[1])) for r in xrange(MMatrix.shape[0]))

    def __len__(self):
        """ Number of components in the MMatrix instance """
        return self.apicls.__len__(self)

    # iterator override     
    # TODO : support for optionnal __iter__ arguments           
    def __iter__(self, *args, **kwargs):
        """ Iterate on the MMatrix rows """
        return self.apicls.__iter__(self.data)   
    # contains is herited from Array contains
    
    # __getitem__ / __setitem__ override
    def __getitem__(self, index):
        """ m.__getitem__(index) <==> m[index]
            Get component index value from self.
            index can be a single numeric value or slice, thus one or more rows will be returned,
            or a row,column tuple of numeric values / slices """
        m = Matrix(self)
        # print list(m)
        return m.__getitem__(index)
        # return super(Matrix, self).__getitem__(index)

    # deprecated and __getitem__ should accept slices anyway
    def __getslice__(self, start, end):
        return self.__getitem__(slice(start, end))

    # as api.MMatrix has no __setitem__ method
    def __setitem__(self, index, value):
        """ m.__setitem__(index, value) <==> m[index] = value
            Set value of component index on self
            index can be a single numeric value or slice, thus one or more rows will be returned,
            or a row,column tuple of numeric values / slices """
        m = Matrix(self)
        m.__setitem__(index, value)
        self.assign(m) 

    # deprecated and __setitem__ should accept slices anyway
    def __setslice__(self, start, end, value):
        self.__setitem__(slice(start, end), value)
        
    def __delitem__(self, index) :
        """ Cannot delete from a class with a fixed shape """
        raise TypeError, "deleting %s from an instance of class %s will make it incompatible with class shape" % (index, clsname(self))

    def __delslice__(self, start):
        self.__delitem__(slice(start, end))           
    
    # TODO : wrap double MMatrix:: operator() (unsigned int row, unsigned int col ) const 

    # common operators herited from Matrix
    
    # operators using the Maya API when applicable   
    def __eq__(self, other):
        """ m.__eq__(v) <==> m == v
            Equivalence test """
        try :
            return bool(self.apicls.__eq__(self, other))
        except :
            return bool(super(MMatrix, self).__eq__(other))        
    def __ne__(self, other):
        """ m.__ne__(v) <==> m != v
            Equivalence test """
        return (not self.__eq__(other))             
    def __neg__(self):
        """ m.__neg__() <==> -m
            The unary minus operator. Negates the value of each of the components of m """        
        return self.__class__(self.apicls.__neg__(self)) 
    def __add__(self, other) :
        """ m.__add__(v) <==> m+v
            Returns the result of the addition of m and v if v is convertible to a Matrix (element-wise addition),
            adds v to every component of m if v is a scalar """ 
        try :
            return self.__class__._convert(self.apicls.__add__(self, other))
        except :
            return self.__class__._convert(super(MMatrix, self).__add__(other)) 
    def __radd__(self, other) :
        """ m.__radd__(v) <==> v+m
            Returns the result of the addition of m and v if v is convertible to a Matrix (element-wise addition),
            adds v to every component of m if v is a scalar """
        try :
            return self.__class__._convert(self.apicls.__radd__(self, other))
        except :
            return self.__class__._convert(super(MMatrix, self).__radd__(other))  
    def __iadd__(self, other):
        """ m.__iadd__(v) <==> m += v
            In place addition of m and v, see __add__ """
        try :
            return self.__class__(self.__add__(other))
        except :
            return NotImplemented   
    def __sub__(self, other) :
        """ m.__sub__(v) <==> m-v
            Returns the result of the substraction of v from m if v is convertible to a Matrix (element-wise substration),
            substract v to every component of m if v is a scalar """        
        try :
            return self.__class__._convert(self.apicls.__sub__(self, other))
        except :
            return self.__class__._convert(super(MMatrix, self).__sub__(other))   
    def __rsub__(self, other) :
        """ m.__rsub__(v) <==> v-m
            Returns the result of the substraction of m from v if v is convertible to a Matrix (element-wise substration),
            replace every component c of m by v-c if v is a scalar """        
        try :
            return self.__class__._convert(self.apicls.__rsub__(self, other))
        except :
            return self.__class__._convert(super(MMatrix, self).__rsub__(other))      
    def __isub__(self, other):
        """ m.__isub__(v) <==> m -= v
            In place substraction of m and v, see __sub__ """
        try :
            return self.__class__(self.__sub__(other))
        except :
            return NotImplemented             
    # action depends on second object type
    def __mul__(self, other) :
        """ m.__mul__(x) <==> m*x
            If x is a Matrix, __mul__ is mapped to matrix multiplication m*x, if x is a Vector, to Matrix by Vector multiplication.
            Otherwise, returns the result of the element wise multiplication of m and x if x is convertible to Array,
            multiplies every component of b by x if x is a single numeric value """
        try :
            return self.__class__._convert(self.apicls.__mul__(self, other))
        except :
            return self.__class__._convert(super(MMatrix, self).__mul__(other))       
    def __rmul__(self, other):
        """ m.__rmul__(x) <==> x*m
            If x is a Matrix, __rmul__ is mapped to matrix multiplication x*m, if x is a Vector (or MVector or MPoint or MColor),
            to transformation, ie Vector by Matrix multiplication.
            Otherwise, returns the result of the element wise multiplication of m and x if x is convertible to Array,
            multiplies every component of m by x if x is a single numeric value """
        try :
            return self.__class__._convert(self.apicls.__rmul__(self, other))
        except :
            return self.__class__._convert(super(MMatrix, self).__rmul__(other))
    def __imul__(self, other):
        """ m.__imul__(n) <==> m *= n
            Valid for MMatrix * MMatrix multiplication, in place multiplication of Matrix m by Matrix n """
        try :
            return self.__class__(self.__mul__(other))
        except :
            return NotImplemented  
    # __xor__ will defer to MVector __xor__ 

    # API added methods

    def setToIdentity (self) :
        """ m.setToIdentity() <==> m = a * b
            Sets Matrix to the identity matrix """
        try :        
            self.apicls.setToIdentity(self)
        except :
            self.assign(self.__class__())
        return self   
    def setToProduct ( self, left, right ) :
        """ m.setToProduct(a, b) <==> m = a * b
            Sets Matrix to the result of the product of Matrix a and Matrix b """
        try :        
            self.apicls.setToProduct(self.__class__(left), self.__class__(right))
        except :
            self.assign(self.__class__(self.__class__(left) * self.__class__(right)))
        return self   
    def transpose(self):
        """ Returns the transposed MMatrix """
        try :
            return self.__class__._convert(self.apicls.transpose(self))
        except :
            return self.__class__._convert(super(MMatrix, self).transpose())    
    def inverse(self):
        """ Returns the inverse MMatrix """
        try :
            return self.__class__._convert(self.apicls.inverse(self))
        except :
            return self.__class__._convert(super(MMatrix, self).inverse())    
    def adjoint(self):
        """ Returns the adjoint (adjugate) MMatrix """
        try :
            return self.__class__._convert(self.apicls.adjoint(self))
        except :
            return self.__class__._convert(super(MMatrix, self).adjugate())   
    def homogenize(self):
        """ Returns a homogenized version of the MMatrix """
        try :
            return self.__class__._convert(self.apicls.homogenize(self))
        except :
            return self.__class__._convert(super(MMatrix, self).homogenize())   
    def det(self):
        """ Returns the determinant of this MMatrix instance """
        try :
            return self.apicls.det4x4(self)
        except :
            return super(MMatrix, self).det()           
    def det4x4(self):
        """ Returns the 4x4 determinant of this MMatrix instance """
        try :
            return self.apicls.det4x4(self)
        except :
            return super(MMatrix, self[:4,:4]).det()    
    def det3x3(self):
        """ Returns the determinant of the upper left 3x3 submatrix of this MMatrix instance,
            it's the same as doing det(m[0:3, 0:3]) """
        try :
            return self.apicls.det3x3(self)
        except :
            return super(MMatrix, self[:3,:3]).det()          
    def isEquivalent(self, other, tol=_api.MVector_kTol):
        """ Returns true if both arguments considered as MMatrix are equal within the specified tolerance """
        try :
            nself, nother = coerce(self, other)
        except :
            return False                 
        if isinstance(nself, MMatrix) :
            return bool(nself.apicls.isEquivalent(nself, nother, tol))
        else :
            return bool(super(Matrix, nself).isEquivalent(nother, tol))      
    def isSingular(self) : 
        """ Returns True if the given MMatrix is singular """
        try :
            return bool(self.apicls.isSingular(self))
        except :
            return super(Matrix, self).isSingular()     
 
    # additionnal methods
 
    def blend(self, other, weight=0.5):
        """ Returns a 0.0-1.0 scalar weight blend between self and other MMatrix,
            blend mixes MMatrix as transformation matrices """
        if isinstance(other, MMatrix) :
            return self.__class__(self.weighted(1.0-weight)*other.weighted(weight))
        else :
            return blend(self, other, weight=weight)   
    def weighted(self, weight):
        """ Returns a 0.0-1.0 scalar weighted blend between identity and self """
        if type(self) is not MTransformationMatrix :
            self = MTransformationMatrix(self)
        return self.__class__._convert(self.asMatrix(weight))

class MFloatMatrix(MMatrix) :
    """ A 4x4 matrix class that wraps Maya's api MFloatMatrix class,
        It behaves identically to MMatrix, but it also derives from api's MFloatMatrix
        to keep api methods happy
        """    
    apicls = _api.MFloatMatrix   

class MTransformationMatrix(MMatrix):
    apicls = _api.MTransformationMatrix 

    def _getTranslate(self):
        return MVector(self.getTranslation(MSpace.kTransform))     
    def _setTranslate(self, value):
        self.setTranslation ( MVector(value), MSpace.kTransform )
    translate = property(_getTranslate, _setTranslate, None, "The translation expressed in this MTransformationMatrix, in transform space") 
    def _getRotate(self):
        return MQuaternion(self.rotation())  
    def _setRotate(self, value):
        q = MQuaternion(value)
        self.setRotationQuaternion(q.x, q.y, q.z, q.w)
    rotate = property(_getRotate, _setRotate, None, "The rotation expressed in this MTransformationMatrix, in transform space") 
    def _getScale(self):
        ms = _api.MScriptUtil()
        ms.createFromDouble ( 1.0, 1.0, 1.0 )
        p = ms.asDoublePtr ()
        self.getScale (p, MSpace.kTransform);
        return MVector([ms.getDoubleArrayItem (p, i) for i in range(3)])        
    def _setScale(self, value):
        ms = _api.MScriptUtil()
        ms.createFromDouble (*MVector(value))
        p = ms.asDoublePtr ()
        self.setScale ( p, MSpace.kTransform)        
    scale = property(_getScale, _setScale, None, "The scale expressed in this MTransformationMatrix, in transform space")  
        
    def rotation(self) :
        return self.apicls.rotation(self)
 
    def rotation(self) :
        return self.apicls.rotation(self) 
    
class MQuaternion(MMatrix):
    apicls = _api.MQuaternion
    shape = (4,)
    cnames = ('x', 'y', 'z', 'w')      

    def __new__(cls, *args, **kwargs):
        shape = kwargs.get('shape', None)
        ndim = kwargs.get('ndim', None)
        size = kwargs.get('size', None)
        # will default to class constant shape = (4,), so it's just an error check to catch invalid shapes,
        # as no other option is actually possible on MQuaternion, but this method could be used to allow wrapping
        # of Maya array classes that can have a variable number of elements
        shape, ndim, size = cls._expandshape(shape, ndim, size)        
        
        new = cls.apicls.__new__(cls)
        cls.apicls.__init__(new)
        return new
        
    def __init__(self, *args, **kwargs):
        """ __init__ method for MQuaternion """
        cls = self.__class__
        
        if args :
            # allow both forms for arguments
            if len(args)==1 and hasattr(args[0], '__iter__') :
                args = args[0]
            # MTransformationMatrix, MQuaternion, MEulerRotation api classes can convert to a rotation MQuaternion
            if hasattr(args, 'rotate') :
                args = args.rotate
            elif len(args) == 4 and ( isinstance(args[3], basestring) or isinstance(args[3], MEulerRotation.RotationOrder) ) :
                quat = _api.MQuaternion()
                quat.assign(MEulerRotation(args))
                args = quat
                # allow to initialize directly from 3 rotations and a rotation order
            elif len(args) == 2 and isinstance(args[0], Vector) and isinstance(args[1], float) :
                # some special init cases are allowed by the api class, want to authorize
                # MQuaternion(MVector axis, float angle) as well as MQuaternion(float angle, MVector axis)
                args = (float(args[1]), MVector(args[0]))        
            # shortcut when a direct api init is possible     
            try :
                self.assign(args)
            except :
                super(Array, self).__init__(*args)
            
        if hasattr(cls, 'cnames') and len(set(cls.cnames) & set(kwargs)) :  
            # can also use the form <componentname>=<number>
            l = list(self.flat)
            setcomp = False
            for i, c in enumerate(cls.cnames) :
                if c in kwargs :
                    if float(l[i]) != float(kwargs[c]) :
                        l[i] = float(kwargs[c])
                        setcomp = True
            if setcomp :
                try :
                    self.assign(l)
                except :
                    msg = ", ".join(map(lambda x,y:x+"=<"+util.clsname(y)+">", cls.cnames, l))
                    raise TypeError, "in %s(%s), at least one of the components is of an invalid type, check help(%s) " % (cls.__name__, msg, cls.__name__)                          

   # set properties for easy acces to translation / rotation / scale of a MMatrix or derived class
    # some of these will only yield dependable results if MMatrix is a MTransformationMatrix and some
    # will always be zero for some classes (ie only rotation has a value on a MQuaternion
    
    def _getTranslate(self):
        return MVector(0.0, 0.0, 0.0)     
    translate = property(_getTranslate, None, None, "The translation expressed in this MMQuaternion, which is always (0.0, 0.0, 0.0)") 
    def _getRotate(self):
        return self 
    def _setRotate(self, value):
        self.assign(MQuaternion(value))
    rotate = property(_getRotate, _setRotate, None, "The rotation expressed in this MQuaternion, in transform space") 
    def _getScale(self):
        return MVector(1.0, 1.0, 1.0)       
    scale = property(_getScale, None, None, "The scale expressed in this MQuaternion, which is always (1.0, 1.0, 1.0")  
                                           
    # overloads for assign and get though standard way should be to use the data property
    # to access stored values                   
                                                 
    def assign(self, value):
        """ Wrap the MQuaternion api assign method """
        # api MQuaternion assign accepts MMatrix, MQuaternion and MEulerRotation
        if isinstance(value, MMatrix) :
            value = value.rotate
        else :
            if not hasattr(value, '__iter__') :
                value = (value,)
            value = self.apicls(*value) 
        self.apicls.assign(self, value)
        return self
   
    # API get, actually not faster than pulling self[i] for such a short structure
    def get(self):
        """ Wrap the MQuaternion api get method """
        ms = _api.MScriptUtil()
        l = (0,)*self.size
        ms.createFromDouble ( *l )
        p = ms.asDoublePtr ()
        self.apicls.get(self, p)
        return tuple([ms.getDoubleArrayItem ( p, i ) for i in xrange(self.size)])

    # faster to override __getitem__ cause we know MQuaternion only has one dimension
    def __getitem__(self, i):
        """ Get component i value from self """
        if hasattr(i, '__iter__') :
            i = list(i)
            if len(i) == 1 :
                i = i[0]
            else :
                raise IndexError, "class %s instance %s has only %s dimension(s), index %s is out of bounds" % (util.clsname(self), self, self.ndim, i)
        if isinstance(i, slice) :
            try :
                return list(self)[i]
            except :
                raise IndexError, "class %s instance %s is of size %s, index %s is out of bounds" % (util.clsname(self), self, self.size, i)
        else :
            if i < 0 :
                i = self.size + i
            if i<self.size and not i<0 :
                if hasattr(self.apicls, '__getitem__') :
                    return self.apicls.__getitem__(self, i)
                else :
                    return list(self)[i]
            else :
                raise IndexError, "class %s instance %s is of size %s, index %s is out of bounds" % (util.clsname(self), self, self.size, i)

    # as api.MVector has no __setitem__ method, so need to reassign the whole MVector
    def __setitem__(self, i, a):
        """ Set component i value on self """
        v = Vector(self)
        v.__setitem__(i, a)
        self.assign(v) 
   
    # iterator override
     
    # TODO : support for optional __iter__ arguments           
    def __iter__(self, *args, **kwargs):
        """ Iterate on the api components """
        return self.apicls.__iter__(self.data)   
    def __contains__(self, value):
        """ True if at least one of the vector components is equal to the argument """
        return value in self.__iter__()  

class MEulerRotation(MMatrix):
    apicls = _api.MEulerRotation
    shape = (4,)   
    cnames = ('x', 'y', 'z', 'o') 
    
    class RotationOrder(dict):
        pass
    rotationOrder = RotationOrder({"xyz": _api.MEulerRotation.kXYZ,
                                   "yzx": _api.MEulerRotation.kYZX,
                                   "zxy": _api.MEulerRotation.kZXY,
                                   "xzy": _api.MEulerRotation.kXZY,
                                   "yxz": _api.MEulerRotation.kYXZ,
                                   "zyx": _api.MEulerRotation.kZYX,
                                   })  
    
    def __new__(cls, *args, **kwargs):
        shape = kwargs.get('shape', None)
        ndim = kwargs.get('ndim', None)
        size = kwargs.get('size', None)
        # will default to class constant shape = (4,), so it's just an error check to catch invalid shapes,
        # as no other option is actually possible on MEulerRotation, but this method could be used to allow wrapping
        # of Maya array classes that can have a variable number of elements
        shape, ndim, size = cls._expandshape(shape, ndim, size)        
        
        new = cls.apicls.__new__(cls)
        cls.apicls.__init__(new)
        return new
        
    def __init__(self, *args, **kwargs):
        """ __init__ method for MEulerRotation """
        cls = self.__class__
        
        if args :
            # allow both forms for arguments
            if len(args)==1 and hasattr(args[0], '__iter__') :
                args = args[0]
            # MTransformationMatrix, MQuaternion, MEulerRotation api classes can convert to a rotation MQuaternion
            if hasattr(args, 'rotate') :
                euler = _api.MEulerRotation()
                euler.assign(args.rotate)
                args = euler
            elif len(args) == 4 and isinstance(args[3], basestring) :
                # allow to initialize directly from 3 rotations and a rotation order as string
                args = (args[0], args[1], args[2], cls.rotationOrder[args[3]])           
            elif len(args) == 2 and isinstance(args[0], Vector) and isinstance(args[1], float) :
                # some special init cases are allowed by the api class, want to authorize
                # MQuaternion(MVector axis, float angle) as well as MQuaternion(float angle, MVector axis)
                args = (float(args[1]), MVector(args[0]))        
            # shortcut when a direct api init is possible     
            try :
                self.assign(args)
            except :
                super(Array, self).__init__(*args)
            
        if hasattr(cls, 'cnames') and len(set(cls.cnames) & set(kwargs)) :  
            # can also use the form <componentname>=<number>
            l = list(self.flat)
            setcomp = False
            for i, c in enumerate(cls.cnames) :
                if c in kwargs :
                    if float(l[i]) != float(kwargs[c]) :
                        l[i] = float(kwargs[c])
                        setcomp = True
            if setcomp :
                try :
                    self.assign(l)
                except :
                    msg = ", ".join(map(lambda x,y:x+"=<"+util.clsname(y)+">", cls.cnames, l))
                    raise TypeError, "in %s(%s), at least one of the components is of an invalid type, check help(%s) " % (cls.__name__, msg, cls.__name__)  
                
    def assign(self, value):
        """ Wrap the MQuaternion api assign method """
        # api MQuaternion assign accepts MMatrix, MQuaternion and MEulerRotation
        if isinstance(value, MTransformationMatrix) :     
            value = value.asMatrix()
        else :
            if not hasattr(value, '__iter__') :
                value = (value,)
            value = self.apicls(*value) 
        self.apicls.assign(self, value)
        return self
   
    # API get, actually not faster than pulling self[i] for such a short structure
    def get(self):
        """ Wrap the MQuaternion api get method """
        ms = _api.MScriptUtil()
        l = (0,)*self.size
        ms.createFromDouble ( *l )
        p = ms.asDoublePtr ()
        self.apicls.get(self, p)
        return tuple([ms.getDoubleArrayItem ( p, i ) for i in xrange(self.size)])

class MTime( _api.MTime ) :
    apicls = _api.MTime
    __metaclass__ = _factories.MetaMayaTypeWrapper
    def __str__( self ): return str(float(self))
    def __int__( self ): return int(float(self))
    def __float__( self ): return self.as(self.apicls.uiUnit())
    def __repr__(self): return '%s(%s)' % ( self.__class__.__name__, float(self) )

class MDistance( _api.MDistance ) :
    apicls = _api.MDistance
    __metaclass__ = _factories.MetaMayaTypeWrapper
    def __str__( self ): return str(float(self))
    def __int__( self ): return int(float(self))
    def __float__( self ): return self.as(self.apicls.uiUnit())
    def __repr__(self): return '%s(%s)' % ( self.__class__.__name__, float(self) )

class MAngle( _api.MAngle ) :
    apicls = _api.MAngle
    __metaclass__ = _factories.MetaMayaTypeWrapper
    def __str__( self ): return str(float(self))
    def __int__( self ): return int(float(self))
    def __float__( self ): return self.as(self.apicls.uiUnit())
    def __repr__(self): return '%s(%s)' % ( self.__class__.__name__, float(self) )
   

#class MItMeshEdge( _api.MItMeshEdge ):
#    apicls = _api.MItMeshEdge
#    __metaclass__ = _factories.MetaMayaTypeWrapper
#    def __init__(self, *args):
#        _api.MItMeshEdge.__init__(self, *args)
#        self._node = args[0]
#    def __iter__(self): return self
#    def next(self):
#        if self.isDone(): raise StopIteration
#        _api.MItMeshEdge.next(self)
#        return api.MItMeshEdge.index(self)
#    def __len__(self): return self.count()
#    def __getitem__(self, item):
#        su = _api.MScriptUtil()
#        if isinstance( item, slice):
#            self.__iter__()
#            rargs = [item.start, item.stop+1]
#            if item.step is not None: rargs.append( item.step)
#            for i in range(  *rargs ):
#                #print i
#                #self._iter.next()
#                _api.MItMeshEdge.setIndex( self, i, su.asIntPtr() )  # bug workaround
#                #print self._iter.getIndex()
#                yield self
#        elif isinstance( item, tuple):
#            for slc in item:
#                for cmp in self.__getitem__(slc): 
#                    yield cmp
#        else:
#            self.__iter__()
#            _api.MItMeshEdge.setIndex( self, i, su.asIntPtr() )  # bug workaround
#            yield self

class MItMeshEdge( _api.MItMeshEdge ):
    apicls = _api.MItMeshEdge
    __metaclass__ = _factories.MetaMayaTypeWrapper
    def __init__(self, node, component=None ):
        args = [node]
        self._range = None
        if _api.isValidMObject( component ): 
            args.append(component)   

        _api.MItMeshEdge.__init__(self, *args)
        
        if _api.isValidMObject( component ): 
            pass 
        elif isinstance(component, int):
            self._range = [component]
            su = _api.MScriptUtil()
            _api.MItMeshEdge.setIndex( self, component, su.asIntPtr() )  # bug workaround
            
        elif isinstance(component, slice):
            self._range = range( component.start, component.stop+1)
            su = _api.MScriptUtil()
            _api.MItMeshEdge.setIndex( self, component.start, su.asIntPtr() )  # bug workaround
            
        elif component is not None:
            raise TypeError, "component must be a valid MObject representing a component, an integer, or a slice"
        
        self._node = node
        self._comp = component
        self._index = 0
        
    def __str__(self): 
        if isinstance( self._comp, int ):
            return 'dummy.e[%s]' % ( self._comp )
        elif isinstance( self._comp, slice ):
            return 'dummy.e[%s:%s]' % ( self._comp.start, self._comp.stop )
        
        return 'dummy.e[0:%s]' % self.count()-1
                                       
    
    def __iter__(self): 
        print "ITER"
        #su = _api.MScriptUtil()
        #_api.MItMeshEdge.setIndex( self, component.start, su.asIntPtr() )  # bug workaround
        return self
    
    def next(self):
        if self.isDone(): raise StopIteration
        if self._range is not None:
            try:
                nextIndex = self._range[self._index]
                su = _api.MScriptUtil()
                _api.MItMeshEdge.setIndex( self, nextIndex, su.asIntPtr() )  # bug workaround
                self._index += 1
                return MItMeshEdge(self._node, nextIndex)
            except IndexError:
                raise StopIteration

        else:
            _api.MItMeshEdge.next(self)
        return MItMeshEdge(self._node, _api.MItMeshEdge.index(self) )
#        if isinstance( self._comp, int ):
#            _api.MItMeshEdge.setIndex( self, self._comp, su.asIntPtr() )  # bug workaround
#        elif isinstance( self._comp, slice):
#            _api.MItMeshEdge.setIndex( self, i, su.asIntPtr() )  # bug workaround
    
    def count(self):
        if self._range is not None:
            return len(self._range)
        else:
            return _api.MItMeshEdge.count( self )
    def __len__(self): 
        return self.count()
            
    def __getitem__(self, item):
        return MItMeshEdge(self._node, item)
        
#        su = _api.MScriptUtil()
#        if isinstance( item, slice):
#            self.__iter__()
#            rargs = [item.start, item.stop+1]
#            if item.step is not None: rargs.append( item.step)
#            for i in range(  *rargs ):
#                #print i
#                #self._iter.next()
#                _api.MItMeshEdge.setIndex( self, i, su.asIntPtr() )  # bug workaround
#                #print self._iter.getIndex()
#                yield self
#        elif isinstance( item, tuple):
#            for slc in item:
#                for cmp in self.__getitem__(slc): 
#                    yield cmp
#        else:
#            self.__iter__()
#            _api.MItMeshEdge.setIndex( self, i, su.asIntPtr() )  # bug workaround
#            yield self

#class PolyEdge(object):
#    def __init__(self, dagNode ):
#        self._node = dagNode
#        self._iter = None
#    def __iter__(self):
#        if self._iter is None:
#            self._iter = MItMeshEdge( self._node )
#        return self._iter
#    def next(self):
#        if self._iter.isDone(): raise StopIteration
#        _api.MItMeshEdge.next(self._iter)
#        return api.MItMeshEdge.index(self._iter)
#    def __getitem__(self, item):
#        if isinstance( item, slice):
#            self.__iter__()
#            for i in range( item.start, item.stop+1, item.step ):
#                #print i
#                #self._iter.next()
#                _api.MItMeshEdge.setIndex( self._iter, i, su.asIntPtr() )  # bug workaround
#                print self._iter.getIndex()
#                yield self._iter
#        elif isinstance( item, tuple):
#            for slc in item:
#                for cmp in self.__getitem__(slc): 
#                    yield cmp
#        else:
#            self.__iter__()
#            _api.MItMeshEdge.setIndex( self._iter, i, su.asIntPtr() )  # bug workaround
#            yield self._iter

class MBoundingBox( _api.MBoundingBox):
    apicls = _api.MBoundingBox
    __metaclass__ = _factories.MetaMayaTypeWrapper
    def __init__(self, *args):
        if len(args) == 2:
            args = list(args)
            if not isinstance( args[0], _api.MPoint ): 
                args[0] = MPoint( args[0] )
            if not isinstance( args[1], _api.MPoint ): 
                args[1] = MPoint( args[1] )    
        _api.MBoundingBox.__init__(self, *args)
    def __str__(self):
        return '%s(%s,%s)' % (self.__class__.__name__, self.min(), self.max())
    repr = __str__
    w = property( _factories.wrapApiMethod( _api.MBoundingBox, 'width'  ) )
    h = property( _factories.wrapApiMethod( _api.MBoundingBox, 'height'  ) )
    d = property( _factories.wrapApiMethod( _api.MBoundingBox, 'depth'  ) )

#_factories.ApiTypeRegister.register( 'MVector', MVector )
#_factories.ApiTypeRegister.register( 'MMatrix', MMatrix )
#_factories.ApiTypeRegister.register( 'MPoint', MPoint )
#_factories.ApiTypeRegister.register( 'MColor', MColor )
#_factories.ApiTypeRegister.register( 'MQuaternion', MQuaternion )
#_factories.ApiTypeRegister.register( 'MEulerRotation', MEulerRotation )
                    
def _testMVector() :
    
    print "MVector class:", dir(MVector)
    u = MVector()
    print u
    print "MVector instance:", dir(u)
    print repr(u)
    print MVector.__readonly__
    print MVector.__slots__
    print MVector.shape
    print MVector.ndim
    print MVector.size
    print u.shape
    print u.ndim
    print u.size    
    # should fail
    u.shape = 2
    
    u.assign(MVector(4, 5, 6))
    print repr(u)
    #MVector([4.0, 5.0, 6.0])    
    u = MVector(1, 2, 3)
    print repr(u)
    # MVector([1.0, 2.0, 3.0])
    print len(u)
    # 3
    # inherits from Vector --> Array
    print isinstance(u, Vector)
    # True
    print isinstance(u, Array)
    # True
    # as well as _api.MVector
    print isinstance(u, _api.MVector)
    # True
    # accepted directly by API methods
    M = _api.MTransformationMatrix()
    M.setTranslation ( u, _api.MSpace.kWorld )
    # need conversion on the way back though
    u = MVector(M.getTranslation ( _api.MSpace.kWorld ))
    print repr(u)
    # MVector([1.0, 2.0, 3.0])
    
    u = MVector(x=1, y=2, z=3)
    print repr(u)
    # MVector([1.0, 2.0, 3.0])
    u = MVector([1, 2], z=3)
    print repr(u)
    # MVector([1.0, 2.0, 3.0])
    u = MVector(_api.MPoint(1, 2, 3))
    print repr(u)  
    # MVector([1.0, 2.0, 3.0])
    print "u = MVector(Vector(1, 2, 3))"
    u = MVector(Vector(1, 2, 3))
    print repr(u)
    # MVector([1.0, 2.0, 3.0])
    u = MVector(1)
    print repr(u)   
    # MVector([1.0, 1.0, 1.0])  
    u = MVector(1,2)
    print repr(u)    
    # MVector([1.0, 2.0, 0.0])              
    u = MVector(Vector(1, shape=(2,)))
    print repr(u)  
    # MVector([1.0, 1.0, 0.0])  
    u = MVector(MPoint(1, 2, 3))
    print repr(u) 
    # MVector([1.0, 2.0, 3.0])
    u = MVector(MPoint(1, 2, 3, 1), y=20, z=30)
    print repr(u) 
    # MVector([1.0, 20.0, 30.0])                           
    # should fail
    print "MVector(Vector(1, 2, 3, 4))"
    try :     
        u = MVector(Vector(1, 2, 3, 4))
    except :
        print "will raise ValueError: could not cast [1, 2, 3, 4] to MVector of size 3, some data would be lost"
           
    
            
    print u.get()
    # (1.0, 20.0, 30.0)
    print u[0]
    1.0
    u[0] = 10
    print repr(u)
    # MVector([10.0, 20.0, 30.0])   
    print (10 in u)
    # True
    print list(u)
    # [10.0, 20.0, 30.0]
    
    u = MVector.xAxis
    v = MVector.yAxis
    print MVector.xAxis
    print str(MVector.xAxis)
    print unicode(MVector.xAxis)
    print repr(MVector.xAxis)

    print "u = MVector.xAxis:"
    print repr(u)
    # MVector([1.0, 0.0, 0.0])
    print "v = MVector.yAxis:"
    print repr(v)
    # MVector([0.0, 1.0, 0.0])
    n = u ^ v
    print "n = u ^ v:"
    print repr(n)
    # MVector([0.0, 0.0, 1.0])
    print "n.x=%s, n.y=%s, n.z=%s" % (n.x, n.y, n.z)
    # n.x=0.0, n.y=0.0, n.z=1.0
    n = u ^ Vector(v)
    print "n = u ^ Vector(v):"
    print repr(n)
    # MVector([0.0, 0.0, 1.0])
    n = u ^ [0, 1, 0]
    print "n = u ^ [0, 1, 0]:"
    print repr(n)
    # MVector([0.0, 0.0, 1.0])       
    n[0:2] = [1, 1]
    print "n[0:2] = [1, 1]:"
    print repr(n)
    # MVector([1.0, 1.0, 1.0]) 
    print "n = n * 2 :"
    n = n*2
    print repr(n)
    # MVector([2.0, 2.0, 2.0])
    print "n = n * [0.5, 1.0, 2.0]:"
    n = n*[0.5, 1.0, 2.0]    
    print repr(n) 
    # MVector([1.0, 2.0, 4.0])  
    print "n * n :"
    print n * n
    # 21.0
    print repr(n.clamp(1.0, 2.0))
    # MVector([1.0, 2.0, 2.0])
    print repr(-n)
    # MVector([-1.0, -2.0, -4.0])
    w = u + v
    print repr(w)
    # MVector([1.0, 1.0, 0.0])
    p = MPoint(1, 2, 3)
    q = u + p
    print repr(q)
    # MPoint([2.0, 2.0, 3.0, 1.0])
    q = p + u
    print repr(q)
    # MPoint([2.0, 2.0, 3.0, 1.0])    
    print repr(p+q)
    # MPoint([3.0, 4.0, 6.0, 1.0])    
    w = u + Vector(1, 2, 3, 4)
    print repr(w)
    # Vector([2.0, 2.0, 3.0, 4])
    print repr(u+2)
    # MVector([3.0, 2.0, 2.0])
    print repr(2+u)
    # MVector([3.0, 2.0, 2.0])
    print repr(p+2)
    # MPoint([3.0, 4.0, 5.0, 1.0])
    print repr(2+p)
    # MPoint([3.0, 4.0, 5.0, 1.0])
    print repr(p + u)
    # MPoint([2.0, 2.0, 3.0, 1.0])
    print repr(Vector(1, 2, 3, 4) + u)
    # Vector([2.0, 2.0, 3.0, 4])
    print repr([1, 2, 3] + u)
    # MVector([2.0, 2.0, 3.0])

      
    u = MVector(1, 2, 3)
    print repr(u)
    # MVector([1.0, 2.0, 3.0])
    print u.length()
    # 3.74165738677
    print length(u)
    # 3.74165738677
    print length([1, 2, 3])
    # 3.74165738677
    print length(Vector(1, 2, 3))
    # 3.74165738677
    print Vector(1, 2, 3).length()
    # 3.74165738677
    print length(Vector(1, 2, 3, 4))
    # 5.47722557505
    print Vector(1, 2, 3, 4).length() 
    # 5.47722557505
    print length(1)
    # 1.0
    print length([1, 2])
    # 2.2360679775
    print length([1, 2, 3])
    # 3.74165738677
    print length([1, 2, 3, 4])
    # 5.47722557505
    print length([1, 2, 3, 4], 0)
    # 5.47722557505
    print length([1, 2, 3, 4], (0,))
    # 5.47722557505
    print length([[1, 2], [3, 4]], 1)
    # [3.16227766017, 4.472135955]
    # should fail
    try :
        print length([1, 2, 3, 4], 1)
    except :
        print "Will raise ValueError, \"axis 0 is the only valid axis for a MVector, 1 invalid\""

    u = MVector(1, 2, 3)
    print repr(u)
    # MVector([1.0, 2.0, 3.0])    
    print u.sqlength()
    # 14
    print repr(u.normal())
    # MVector([0.267261241912, 0.534522483825, 0.801783725737])
    u.normalize()
    print repr(u)
    # MVector([0.267261241912, 0.534522483825, 0.801783725737])

    u = MVector(1, 2, 3)
    print repr(u)  
    # MVector([1.0, 2.0, 3.0])  
    w = u + [0.01, 0.01, 0.01]
    print repr(w)
    # MVector([1.01, 2.01, 3.01])
    print (u == u)
    # True
    print (u == w)
    # False
    print (u == MVector(1.0, 2.0, 3.0))
    # True
    print (u == [1.0, 2.0, 3.0])
    # False    
    print (u == MPoint(1.0, 2.0, 3.0))
    # False
    print u.isEquivalent([1.0, 2.0, 3.0])
    # True
    print u.isEquivalent(MVector(1.0, 2.0, 3.0))
    # True
    print u.isEquivalent(MPoint(1.0, 2.0, 3.0))   
    # True
    print u.isEquivalent(w)
    # False     
    print u.isEquivalent(w, 0.1)
    # True
    
    u = MVector(1, 0, 0)
    print repr(u)
    # MVector([1.0, 0.0, 0.0]) 
    v = MVector(0.707, 0, -0.707)
    print repr(v)
    # MVector([0.707, 0.0, -0.707])              
    print repr(axis(u, v))
    # MVector([-0.0, 0.707, 0.0])
    print repr(u.axis(v))
    # MVector([-0.0, 0.707, 0.0])   
    print repr(axis(Vector(u), Vector(v)))
    # Vector([-0.0, 0.707, 0.0])
    print repr(axis(u, v, normalize=True))
    # MVector([-0.0, 1.0, 0.0])
    print repr(v.axis(u, normalize=True))
    # MVector([-0.0, -1.0, 0.0])    
    print repr(axis(Vector(u), Vector(v), normalize=True))
    # Vector([-0.0, 1.0, 0.0])    
    print angle(u,v)    
    # 0.785398163397
    print v.angle(u)
    # 0.785398163397
    print angle(Vector(u), Vector(v))
    # 0.785398163397
    print cotan(u, v)
    # 1.0
    print repr(u.rotateTo(v))
    # MQuaternion([-0.0, 0.382683432365, 0.0, 0.923879532511])
    print repr(u.rotateBy(u.axis(v), u.angle(v)))
    # MVector([0.707106781187, 0.0, -0.707106781187])
    q = MQuaternion([-0.0, 0.382683432365, 0.0, 0.923879532511])
    print repr(u.rotateBy(q))
    # MVector([0.707106781187, 0.0, -0.707106781187])
    print u.distanceTo(v)
    # 0.765309087885
    print u.isParallel(v)
    # False
    print u.isParallel(2*u)
    # True
    print repr(u.blend(v))
    # MVector([0.8535, 0.0, -0.3535])
        
    print "end tests MVector"

def _testMPoint() :
    
    print "MPoint class", dir(MPoint)
    print hasattr(MPoint, 'data')
    p = MPoint()
    print repr(p)
    # MPoint([0.0, 0.0, 0.0])
    print "MPoint instance", dir(p)
    print hasattr(p, 'data')
    print repr(p.data)
    # <maya.OpenMaya.MPoint; proxy of <Swig Object of type 'MPoint *' at 0x84a1270> >
    
    p = MPoint(1, 2, 3)
    print repr(p)
    # MPoint([1.0, 2.0, 3.0])
    v = MVector(p)
    print repr(v)
    # MVector([1.0, 2.0, 3.0])
    V = Vector(p)
    print repr(V)
    # Vector([1.0, 2.0, 3.0, 1.0])
    print list(p)
    # [1.0, 2.0, 3.0]
    print len(p)
    # 3
    print p.size
    # 4
    print p.x, p.y, p.z, p.w
    # 1.0 2.0 3.0 1.0
    print p[0], p[1], p[2], p[3] 
    # 1.0 2.0 3.0 1.0     
    p.get()
    # 1.0 2.0 3.0 1.0
    
    # accepted by api
    q = _api.MPoint()
    print q.distanceTo(p)
    # 3.74165738677
 
    # support for non cartesian points still there
    
    p = MPoint(1, 2, 3, 2)
    print repr(p)
    # MPoint([1.0, 2.0, 3.0, 2.0])
    v = MVector(p)
    print repr(v)
    # MVector([0.5, 1.0, 1.5])
    V = Vector(p)
    print repr(V)
    # Vector([1.0, 2.0, 3.0, 2.0])
    print list(p)
    # [1.0, 2.0, 3.0, 2.0]
    print len(p)
    # 4
    print p.size
    # 4
    print p.x, p.y, p.z, p.w
    # 1.0 2.0 3.0 2.0
    print p[0], p[1], p[2], p[3] 
    # 1.0 2.0 3.0 2.0     
    p.get()
    # 1.0 2.0 3.0 2.0
    
    # accepted by api
    q = _api.MPoint()
    print q.distanceTo(p)
    # 1.87082869339    
    
    p = MPoint(_api.MPoint())
    print repr(p) 
    # MPoint([0.0, 0.0, 0.0])
    p = MPoint(1)
    print repr(p)
    # MPoint([1.0, 1.0, 1.0])
    p = MPoint(1, 2)
    print repr(p)     
    # MPoint([1.0, 2.0, 0.0])      
    p = MPoint(1, 2, 3)
    print repr(p)
    # MPoint([1.0, 2.0, 3.0])
    p = MPoint(_api.MPoint(1, 2, 3))
    print repr(p) 
    # MPoint([1.0, 2.0, 3.0])
    p = MPoint(Vector(1, 2))
    print repr(p) 
    # MPoint([1.0, 2.0, 0.0])       
    p = MPoint(MVector(1, 2, 3))
    print repr(p) 
    # MPoint([1.0, 2.0, 3.0])      
    p = MPoint(_api.MVector(1, 2, 3))
    print repr(p) 
    # MPoint([1.0, 2.0, 3.0])    
    p = MPoint(Vector(1, 2, 3, 4))
    print repr(p) 
    # MPoint([1.0, 2.0, 3.0, 4.0]) 
    print repr(MVector(p))
    # MVector([0.25, 0.5, 0.75])
    print repr(Vector(p))
    # Vector([1.0, 2.0, 3.0, 4.0])
    p = MPoint(p, w=1)
    print repr(p) 
    # MPoint([1.0, 2.0, 3.0])    
    print repr(MVector(p))
    # MVector([1.0, 2.0, 3.0])
    print repr(Vector(p))
    # Vector([1.0, 2.0, 3.0, 1.0])
            
    p = MPoint.origin
    print repr(p)
    # MPoint([0.0, 0.0, 0.0])
    p = MPoint.xAxis
    print repr(p) 
    # MPoint([1.0, 0.0, 0.0])

    p = MPoint(1, 2, 3)
    print repr(p)
    # MPoint([1.0, 2.0, 3.0])
    print repr(p + MVector([1, 2, 3]))
    # MPoint([2.0, 4.0, 6.0])
    print repr(p + MPoint([1, 2, 3]))
    # MPoint([2.0, 4.0, 6.0])    
    print repr(p + [1, 2, 3])
    # MPoint([2.0, 4.0, 6.0])
    print repr(p + [1, 2, 3, 1])
    # MPoint([2.0, 4.0, 6.0])
    print repr(p + MPoint([1, 2, 3, 1]))
    # MPoint([2.0, 4.0, 6.0])
    print repr(p + [1, 2, 3, 2])
    # MPoint([2.0, 4.0, 6.0, 3.0])    TODO : convert to MPoint always?
    print repr(p + MPoint([1, 2, 3, 2]))
    # MPoint([1.5, 3.0, 4.5])
        
    print repr(MVector([1, 2, 3]) + p)
    # MPoint([2.0, 4.0, 6.0])
    print repr(MPoint([1, 2, 3]) + p)
    # MPoint([2.0, 4.0, 6.0])    
    print repr([1, 2, 3] + p)
    # MPoint([2.0, 4.0, 6.0])
    print repr([1, 2, 3, 1] + p)
    # MPoint([2.0, 4.0, 6.0])
    print repr(MPoint([1, 2, 3, 1]) + p)
    # MPoint([2.0, 4.0, 6.0])
    print repr([1, 2, 3, 2] + p)
    # MPoint([2.0, 4.0, 6.0, 3.0])
    print repr(MPoint([1, 2, 3, 2]) + p)
    # MPoint([1.5, 3.0, 4.5])
        
    # various operation, on cartesian and non cartesian points
    
    print "p = MPoint(1, 2, 3)"        
    p = MPoint(1, 2, 3)
    print repr(p)  
    # MPoint([1.0, 2.0, 3.0])
    print "p/2"
    print repr(p/2)
    # MPoint([0.5, 1.0, 1.5])
    print "p*2"
    print repr(p*2)
    # MPoint([2.0, 4.0, 6.0])  
    print "q = MPoint(0.25, 0.5, 1.0)"        
    q = MPoint(0.25, 0.5, 1.0)
    print repr(q)  
    # MPoint([0.25, 0.5, 1.0])
    print repr(q+2)
    # MPoint([2.25, 2.5, 3.0])
    print repr(q/2)
    # MPoint([0.125, 0.25, 0.5])
    print repr(p+q)
    # MPoint([1.25, 2.5, 4.0])
    print repr(p-q)
    # MVector([0.75, 1.5, 2.0])
    print repr(q-p)
    # MVector([-0.75, -1.5, -2.0])
    print repr(p-(p-q))
    # MPoint([0.25, 0.5, 1.0])
    print repr(MVector(p)*MVector(q))
    # 4.25
    print repr(p*q)
    # 4.25
    print repr(p/q)
    # MPoint([4.0, 4.0, 3.0])
    
    print "p = MPoint(1, 2, 3)"        
    p = MPoint(1, 2, 3)
    print repr(p)  
    # MPoint([1.0, 2.0, 3.0])
    print "p/2"
    print repr(p/2)
    # MPoint([0.5, 1.0, 1.5])
    print "p*2"
    print repr(p*2) 
    # MPoint([2.0, 4.0, 6.0])       
    print "q = MPoint(0.25, 0.5, 1.0, 0.5)"        
    q = MPoint(0.25, 0.5, 1.0, 0.5)
    print repr(q)  
    # MPoint([0.25, 0.5, 1.0, 0.5])
    r = q.deepcopy()
    print repr(r)
    # MPoint([0.25, 0.5, 1.0, 0.5])
    print repr(r.cartesianize())
    # MPoint([0.5, 1.0, 2.0])
    print repr(r)
    # MPoint([0.5, 1.0, 2.0])
    print repr(q)
    # MPoint([0.25, 0.5, 1.0, 0.5])
    print repr(q.cartesian())
    # MPoint([0.5, 1.0, 2.0])
    r = q.deepcopy()
    print repr(r)
    # MPoint([0.25, 0.5, 1.0, 0.5])
    print repr(r.rationalize())
    # MPoint([0.5, 1.0, 2.0, 0.5])
    print repr(r)
    # MPoint([0.5, 1.0, 2.0, 0.5])
    print repr(q.rational())
    # MPoint([0.5, 1.0, 2.0, 0.5])
    r = q.deepcopy()
    print repr(r.homogenize())
    # MPoint([0.125, 0.25, 0.5, 0.5])
    print repr(r)
    # MPoint([0.125, 0.25, 0.5, 0.5]) 
    print repr(q.homogen())
    # MPoint([0.125, 0.25, 0.5, 0.5])
    print repr(q)
    # MPoint([0.25, 0.5, 1.0, 0.5])      
    print MVector(q)
    # [0.5, 1.0, 2.0]
    print MVector(q.cartesian())
    # [0.5, 1.0, 2.0]     
    # ignore w
    print "q/2"
    print repr(q/2)
    # MPoint([0.125, 0.25, 0.5, 0.5])
    print "q*2"
    print repr(q*2) 
    # MPoint([0.5, 1.0, 2.0, 0.5])
    print repr(q+2)             # cartesianize is done by MVector add
    # MPoint([2.5, 3.0, 4.0])

    print repr(q)
    # MPoint([0.25, 0.5, 1.0, 0.5])     
    print repr(p+MVector(1, 2, 3))
    # MPoint([2.0, 4.0, 6.0])
    print repr(q+MVector(1, 2, 3))       
    # MPoint([1.5, 3.0, 5.0])
    print repr(q.cartesian()+MVector(1, 2, 3))       
    # MPoint([1.5, 3.0, 5.0])

    print repr(p-q)
    # MVector([0.5, 1.0, 1.0])
    print repr(p-q.cartesian())
    # MVector([0.5, 1.0, 1.0])    
    print repr(q-p)
    # MVector([-0.5, -1.0, -1.0])
    print repr(p-(p-q))
    # MPoint([0.5, 1.0, 2.0])
    print repr(MVector(p)*MVector(q))
    # 4.25    
    print repr(p*q)
    # 4.25
    print repr(p/q)             # need explicit homogenize as division not handled by api
    # MPoint([4.0, 4.0, 3.0, 2.0])    TODO : what do we want here ?
    # MVector([2.0, 2.0, 1.5])
    # additionnal methods
       
    print "p = MPoint(x=1, y=2, z=3)"        
    p = MPoint(x=1, y=2, z=3)
    print p.length()
    # 3.74165738677
    print p[:1].length()
    # 1.0
    print p[:2].length()
    # 2.2360679775
    print p[:3].length()
    # 3.74165738677
    
    p = MPoint(1.0, 0.0, 0.0)
    q = MPoint(0.707, 0.0, -0.707)
    print repr(p)
    # MPoint([1.0, 0.0, 0.0, 1.0])
    print repr(q)
    # MPoint([0.707, 0.0, -0.707, 1.0])
    print repr(q-p)
    # MVector([-0.293, 0.0, -0.707])
    print repr(axis(MPoint.origin, p, q))
    # MVector([-0.0, 0.707, 0.0])
    print repr(MPoint.origin.axis(p, q))
    # MVector([-0.0, 0.707, 0.0]) 
    print repr(MPoint.origin.axis(q, p))
    # MVector([0.0, -0.707, 0.0])         
    print angle(MPoint.origin, p, q)    
    # 0.785398163397
    print angle(MPoint.origin, q, p)    
    # 0.785398163397    
    print MPoint.origin.angle(p, q)
    # 0.785398163397    
    print p.distanceTo(q)  
    # 0.765309087885
    print (q-p).length()
    # 0.765309087885    
    print cotan(MPoint.origin, p, q)
    # 1.0
    # obviously True
    print planar(MPoint.origin, p, q)
    # True
    r = center(MPoint.origin, p, q)
    print repr(r)
    # MPoint([0.569, 0.0, -0.235666666667, 1.0])
    print planar(MPoint.origin, p, q, r)
    # True
    print planar(MPoint.origin, p, q, r+MVector(0.0, 0.1, 0.0))
    # False 
    print bWeights(r, MPoint.origin, p, q)
    # (0.33333333333333337, 0.33333333333333331, 0.33333333333333343)
      
    p = MPoint([0.33333, 0.66666, 1.333333, 0.33333])
    print repr(round(p, 3))
    # MPoint([0.333, 0.667, 1.333, 0.333])
    
    print "end tests MPoint"
 
def _testMColor() :
    
    print "MColor class", dir(MColor)
    print hasattr(MColor, 'data')
    c = MColor()
    print repr(c)
    # MColor([0.0, 0.0, 0.0, 1.0])
    print "MColor instance", dir(c)
    print hasattr(c, 'data')
    print repr(c.data)
    # MColor([0.0, 0.0, 0.0, 1.0])
    c = MColor(_api.MColor())
    print repr(c)     
    # MColor([0.0, 0.0, 0.0, 1.0])
    # using api convetion of single value would mean alpha
    # instead of Vector convention of filling all with value
    # which would yield # MColor([0.5, 0.5, 0.5, 0.5]) instead
    # This would break coerce behavior for MColor  
    print "c = MColor(0.5)"
    c = MColor(0.5)
    print repr(c)   
    # MColor([0.5, 0.5, 0.5, 0.5])
    print "c = round(MColor(128, quantize=255), 2)"
    c = MColor(128, quantize=255)
    print repr(c) 
    # MColor([0.501999974251, 0.501999974251, 0.501999974251, 0.501999974251])
    c = MColor(255, 128, b=64, a=32, quantize=255)
    print repr(c) 
    # MColor([1.0 0.501999974251 0.250999987125 0.125490196078])
          
    print "c = MColor(1, 1, 1)"
    c = MColor(1, 1, 1)
    print repr(c)
    # MColor([1.0, 1.0, 1.0, 1.0])
    print "c = round(MColor(255, 0, 255, g=128, quantize=255, mode='rgb'), 2)"
    c = round(MColor(255, 0, 255, g=128, quantize=255, mode='rgb'), 2)
    print repr(c)
    # MColor([1.0, 0.5, 1.0, 1.0])
    
    print "c = round(MColor(255, b=128, quantize=255, mode='rgb'), 2)"
    c = round(MColor(255, b=128, quantize=255, mode='rgb'), 2)
    print repr(c)
    # MColor([1.0, 1.0, 0.5, 1.0])
    print "c = MColor(1, 0.5, 2, 0.5)"
    c = MColor(1, 0.5, 2, 0.5)
    print repr(c)
    # MColor([1.0, 0.5, 2.0, 0.5])
    print "c = MColor(0, 65535, 65535, quantize=65535, mode='hsv')"
    c = MColor(0, 65535, 65535, quantize=65535, mode='hsv')
    print repr(c)
    # MColor([1.0, 0.0, 0.0, 1.0])
    print "c.rgb"
    print repr(c.rgb)
    # (1.0, 0.0, 0.0)   
    print "c.hsv"
    print repr(c.hsv)
    # (0.0, 1.0, 1.0)
    d = MColor(c, v=0.5, mode='hsv')
    print repr(d)
    # MColor([0.5, 0.0, 0.0, 1.0])
    print repr(d.hsv)
    # (0.0, 1.0, 0.5) 
    print "c = MColor(MColor.blue, v=0.5)"
    c = MColor(MColor.blue, v=0.5)
    print repr(c)
    # MColor([0.0, 0.0, 0.5, 1.0])
    print "c.hsv"
    print c.hsv
    # (0.66666666666666663, 1.0, 0.5)
    c.r = 1.0
    print repr(c)
    # MColor([1.0, 0.0, 0.5, 1.0])
    print "c.hsv"
    print c.hsv
    # (0.91666666666666663, 1.0, 1.0)
            
    print "c = MColor(1, 0.5, 2, 0.5).clamp()"
    c = MColor(1, 0.5, 2, 0.5).clamp()
    print repr(c)
    # MColor([1.0, 0.5, 1.0, 0.5])
    print c.hsv
    # (0.83333333333333337, 0.5, 1.0)
        
    print "MColor(c, v=0.5)"
    d = MColor(c, v=0.5)
    print repr(d)
    # MColor([0.5, 0.25, 0.5, 0.5])
    print "d.hsv"
    print d.hsv
    # (0.83333333333333337, 0.5, 0.5)
    
    print "c = MColor(0.0, 0.5, 1.0, 0.5)"
    c = MColor(0.0, 0.5, 1.0, 0.5)
    print repr(c)
    # MColor(0.0, 0.5, 1.0, 0.5)
    print "d = c.gamma(2.0)"
    d = c.gamma(2.0)
    print repr(d)
    # MColor([0.0, 0.25, 1.0, 0.5])
    
    print "c = MColor.red.blend(MColor.blue, 0.5)"
    c = MColor.red.blend(MColor.blue, 0.5)
    print repr(c)
    # MColor([0.5, 0.0, 0.5, 1.0])
    print c.hsv
    # (0.83333333333333337, 1.0, 0.5)
    c = MColor.red.hsvblend(MColor.blue, 0.5)
    print repr(c)
    # MColor([1.0, 0.0, 1.0, 1.0])
    print c.hsv
    # (0.83333333333333337, 1.0, 1.0)

    print "c = MColor(0.25, 0.5, 0.75, 0.5)"
    c = MColor(0.25, 0.5, 0.75, 0.5)
    print repr(c)
    # MColor([0.25, 0.5, 0.75, 0.5])
    print "d = MColor.black"
    d = MColor.black
    print repr(d)
    # MColor([0.0, 0.0, 0.0, 1.0])                  
    print "c.over(d)"
    print repr(c.over(d))
    # MColor([0.125, 0.25, 0.375, 1.0])
    print "d.over(c)"
    print repr(d.over(c))
    # MColor([0.0, 0.0, 0.0, 0.5])
    print "c.premult()"
    print repr(c.premult())
    # MColor([0.125, 0.25, 0.375, 1.0])
    
    # herited from MVector
    
    print "c = MColor(0.25, 0.5, 1.0, 1.0)"
    c = MColor(0.25, 0.5, 1.0, 1.0)
    print repr(c)
    # MColor([0.25, 0.5, 1.0, 1.0])
    print "d = MColor(2.0, 1.0, 0.5, 0.25)"
    d = MColor(2.0, 1.0, 0.5, 0.25)
    print repr(d)
    # MColor([2.0, 1.0, 0.5, 0.25])
    print "-c"
    print repr(-c)
    # MColor([-0.25, -0.5, -1.0, 1.0]) 
    print "e = c*d"
    e = c*d
    print repr(e)
    # MColor([0.5, 0.5, 0.5, 0.25])
    print "e + 2"
    print repr(e+2)
    # MColor([2.5, 2.5, 2.5, 0.25])
    print "e * 2.0"               # mult by scalar float is defined in api for colors and also multiplies alpha
    print repr(e*2.0)
    # MColor([1.0, 1.0, 1.0, 0.5])    
    print "e / 2.0"               # as is divide, that ignores alpha now for some reason
    print repr(e/2.0)
    # MColor([0.25, 0.25, 0.25, 0.25])
    print "e+MVector(1, 2, 3)"
    print repr(e+MVector(1, 2, 3))
    # MColor([1.5, 2.5, 3.5, 0.25])
    # how to handle operations on colors ?
    # here behaves like api but does it make any sense
    # for colors as it is now ?
    print "c+c"
    print repr(c+c)
    # MColor([0.5, 1.0, 2.0, 1.0])
    print "c+d"
    print repr(c+d)
    # MColor([2.25, 1.5, 1.5, 1.0])       
    print "d-c"
    print repr(d-c)
    # MColor([1.75, 0.5, -0.5, 0.25])
            
    print "end tests MColor"
    
def _testMMatrix() :

    print "MMatrix class", dir(MMatrix)
    m = MMatrix()
    print m.formated()
    #[[1.0, 0.0, 0.0, 0.0],
    # [0.0, 1.0, 0.0, 0.0],
    # [0.0, 0.0, 1.0, 0.0],
    # [0.0, 0.0, 0.0, 1.0]]    
    print m[0, 0]
    # 1.0
    print repr(m[0:2, 0:3])
    # [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    print m(0, 0)
    # 1.0
    print "MMatrix instance:", dir(m)
    print MMatrix.__readonly__
    print MMatrix.__slots__
    print MMatrix.shape
    print MMatrix.ndim
    print MMatrix.size
    print m.shape
    print m.ndim
    print m.size    
    # should fail
    m.shape = (4, 4)
    m.shape = 2
    
    print dir(MSpace)
       
    m = MMatrix.identity    
    # inherits from Matrix --> Array
    print isinstance(m, Matrix)
    # True
    print isinstance(m, Array)
    # True
    # as well as _api.MMatrix
    print isinstance(m, _api.MMatrix)
    # True
    # accepted directly by API methods     
    n = _api.MMatrix()
    m = n.setToProduct(m, m)
    print repr(m)
    print repr(n)
    
    # inits
    m = MMatrix(range(16)) 
    print m.formated()
    #[[0.0, 1.0, 2.0, 3.0],
    # [4.0, 5.0, 6.0, 7.0],
    # [8.0, 9.0, 10.0, 11.0],
    # [12.0, 13.0, 14.0, 15.0]]     
    M = Array(range(16), shape=(8, 2))
    m = MMatrix(M)
    print m.formated() 
    #[[0.0, 1.0, 2.0, 3.0],
    # [4.0, 5.0, 6.0, 7.0],
    # [8.0, 9.0, 10.0, 11.0],
    # [12.0, 13.0, 14.0, 15.0]]    
    M = Matrix(range(9), shape=(3, 3))
    m = MMatrix(M)
    print m.formated()   
    #[[0.0, 1.0, 2.0, 0.0],
    # [3.0, 4.0, 5.0, 0.0],
    # [6.0, 7.0, 8.0, 0.0],
    # [0.0, 0.0, 0.0, 1.0]]
    # inherits from Matrix --> Array
    print isinstance(m, Matrix)
    # True
    print isinstance(m, Array)
    # True
    # as well as _api.MMatrix
    print isinstance(m, _api.MMatrix)
    # True
    # accepted directly by API methods     
    n = _api.MMatrix()
    m = n.setToProduct(m, m)
    print repr(m)
    print repr(n)    
    t = _api.MTransformationMatrix()
    t.setTranslation ( MVector(1, 2, 3), _api.MSpace.kWorld ) 
    m = MMatrix(t)
    print m.formated() 
    #[[1.0, 0.0, 0.0, 0.0],
    # [0.0, 1.0, 0.0, 0.0],
    # [0.0, 0.0, 1.0, 0.0],
    # [1.0, 2.0, 3.0, 1.0]]
    m = MMatrix(m, a30=10)   
    print m.formated() 
    #[[1.0, 0.0, 0.0, 0.0],
    # [0.0, 1.0, 0.0, 0.0],
    # [0.0, 0.0, 1.0, 0.0],
    # [10.0, 2.0, 3.0, 1.0]]                   
    # should fail
    print "MMatrix(range(20)"
    try :     
        m = MMatrix(range(20))
        print m.formated()
    except :
        print "will raise ValueError: cannot initialize a MMatrix of shape (4, 4) from (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19), some information would be lost, use an explicit resize or trim"     

    m = MMatrix.identity
    M = m.trimmed(shape=(3, 3))
    print repr(M)
    # Matrix([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    print M.formated()
    #[[1.0, 0.0, 0.0],
    # [0.0, 1.0, 0.0],
    # [0.0, 0.0, 1.0]]    
    try: 
        m.trim(shape=(3, 3))
    except :
        print "will raise TypeError: new shape (3, 3) is not compatible with class MMatrix"
           
    print m.nrow
    # 4
    print m.ncol
    # 4
    # should fail
    try :
        m.nrow = 3
    except :
        print "will raise TypeError: new shape (3, 4) is not compatible with class MMatrix"
    print list(m.row)
    # [Array([1.0, 0.0, 0.0, 0.0]), Array([0.0, 1.0, 0.0, 0.0]), Array([0.0, 0.0, 1.0, 0.0]), Array([0.0, 0.0, 0.0, 1.0])]
    print list(m.col)
    # [Array([1.0, 0.0, 0.0, 0.0]), Array([0.0, 1.0, 0.0, 0.0]), Array([0.0, 0.0, 1.0, 0.0]), Array([0.0, 0.0, 0.0, 1.0])]
    
    m = MMatrix( Matrix(range(9), shape=(3, 3)).trimmed(shape=(4, 4), value=10) )
    print m.formated()   
    #[[0.0, 1.0, 2.0, 10.0],
    # [3.0, 4.0, 5.0, 10.0],
    # [6.0, 7.0, 8.0, 10.0],
    # [10.0, 10.0, 10.0, 10.0]]    
    
    print m.get()
    # ((0.0, 1.0, 2.0, 10.0), (3.0, 4.0, 5.0, 10.0), (6.0, 7.0, 8.0, 10.0), (10.0, 10.0, 10.0, 10.0))
    print repr(m[0])
    # [0.0, 1.0, 2.0, 10.0]
    m[0] = 10
    print m.formated()
    #[[10.0, 10.0, 10.0, 10.0],
    # [3.0, 4.0, 5.0, 10.0],
    # [6.0, 7.0, 8.0, 10.0],
    # [10.0, 10.0, 10.0, 10.0]]   
    print (10 in m)
    # True
    print list(m)
    # [Array([10.0, 10.0, 10.0, 10.0]), Array([3.0, 4.0, 5.0, 10.0]), Array([6.0, 7.0, 8.0, 10.0]), Array([10.0, 10.0, 10.0, 10.0])]
    print list(m.flat)
    # [10.0, 10.0, 10.0, 10.0, 3.0, 4.0, 5.0, 10.0, 6.0, 7.0, 8.0, 10.0, 10.0, 10.0, 10.0, 10.0]
    
    u = MVector.xAxis
    v = MVector.yAxis
    print MVector.xAxis
    print str(MVector.xAxis)
    print unicode(MVector.xAxis)
    print repr(MVector.xAxis)

    print "u = MVector.xAxis:"
    print repr(u)

    # trans matrix : t: 1, 2, 3, r: 45, 90, 30, s: 0.5, 1.0, 2.0
    m = MMatrix([0.0, 4.1633363423443383e-17, -0.5, 0.0, 0.25881904510252079, 0.96592582628906831, 1.3877787807814459e-16, 0.0, 1.9318516525781366, -0.51763809020504159, 0.0, 0.0, 1.0, 2.0, 3.0, 1.0])
    print "m:"
    print round(m, 2).formated()
    #[[0.0, 0.0, -0.5, 0.0],
    # [0.26, 0.97, 0.0, 0.0],
    # [1.93, -0.52, 0.0, 0.0],
    # [1.0, 2.0, 3.0, 1.0]]

    x = MVector.xAxis
    y = MVector.yAxis   
    z = MVector.zAxis 
    u = MVector(1, 2, 3)   
    print "u:"
    print repr(u)
    # MVector([1, 2, 3])
    print "u*m"
    print repr(u*m)
    # MVector([6.31319304794, 0.378937381963, -0.5])   
    print "m*u"
    print repr(m*u)
    # MVector([-1.5, 2.19067069768, 0.896575472168])    
    
    p=MPoint(1, 10, 100, 1)   
    print "p:"
    print repr(p)
    # MPoint([1.0, 10.0, 100.0, 1.0])
    print "p*m"
    print repr(p*m)
    # MPoint([196.773355709, -40.1045507576, 2.5, 1.0])
    print "m*p"
    print repr(m*p)
    # MPoint([-50.0, 9.91807730799, -3.24452924947, 322.0])
    
    print "v = [1, 2, 3]*m"
    v = Vector([1, 2, 3])*m
    print repr(v)
    # Vector([6.31319304794, 0.378937381963, -0.5])
    print "v = [1, 2, 3, 1]*m"
    v = Vector([1, 2, 3, 1])*m
    print repr(v)       
    # Vector([7.31319304794, 2.37893738196, 2.5, 1.0])   
    # should fail
    print "Vector([1, 2, 3, 4, 5])*m"
    try :
        v = Vector([1, 2, 3, 4, 5])*m
    except :
        print "Will raise ValueError: vector of size 5 and matrix of shape (4, 4) are not conformable for a Vector * Matrix multiplication"        

    # herited

    print "m = MMatrix(range(1, 17))"
    m = MMatrix(range(1, 17))
    print m.formated()
    #[[1.0, 2.0, 3.0, 4.0],
    # [5.0, 6.0, 7.0, 8.0],
    # [9.0, 10.0, 11.0, 12.0],
    # [13.0, 14.0, 15.0, 16.0]]    
    # element wise
    print "[1, 10, 100]*m"
    print repr([1, 10, 100]*m)
    # MMatrix([[1.0, 20.0, 300.0, 0.0], [5.0, 60.0, 700.0, 0.0], [9.0, 100.0, 1100.0, 0.0], [13.0, 140.0, 1500.0, 0.0]])
    print "M = Matrix(range(20), shape=(4, 5))"
    M = Matrix(range(1, 21), shape=(4, 5))
    print M.formated()
    #[[1, 2, 3, 4, 5],
    # [6, 7, 8, 9, 10],
    # [11, 12, 13, 14, 15],
    # [16, 17, 18, 19, 20]]    
    print "m*M"
    n = m*M
    print (n).formated()
    #[[110.0, 120.0, 130.0, 140.0, 150.0],
    # [246.0, 272.0, 298.0, 324.0, 350.0],
    # [382.0, 424.0, 466.0, 508.0, 550.0],
    # [518.0, 576.0, 634.0, 692.0, 750.0]]    
    print util.clsname(n)
    # Matrix
    print "m*2"
    n = m*2
    print (n).formated()
    #[[2.0, 4.0, 6.0, 8.0],
    # [10.0, 12.0, 14.0, 16.0],
    # [18.0, 20.0, 22.0, 24.0],
    # [26.0, 28.0, 30.0, 32.0]]  
    print util.clsname(n)  
    # MMatrix
    print "2*m"
    n = 2*m
    print (n).formated()
    #[[2.0, 4.0, 6.0, 8.0],
    # [10.0, 12.0, 14.0, 16.0],
    # [18.0, 20.0, 22.0, 24.0],
    # [26.0, 28.0, 30.0, 32.0]]      
    print util.clsname(n) 
    # MMatrix
    print "m+2"
    n=m+2
    print (n).formated()
    #[[3.0, 4.0, 5.0, 6.0],
    # [7.0, 8.0, 9.0, 10.0],
    # [11.0, 12.0, 13.0, 14.0],
    # [15.0, 16.0, 17.0, 18.0]]    
    print util.clsname(n) 
    # MMatrix
    print "2+m"
    n=2+m
    print (n).formated()
    #[[3.0, 4.0, 5.0, 6.0],
    # [7.0, 8.0, 9.0, 10.0],
    # [11.0, 12.0, 13.0, 14.0],
    # [15.0, 16.0, 17.0, 18.0]]       
    print util.clsname(n)
    # MMatrix
    try :
        m.setToProduct(m, M)
    except :
        print """Will raise TypeError:  cannot initialize a MMatrix of shape (4, 4) from (Array([0, 1, 2, 3, 4]), Array([5, 6, 7, 8, 9]), Array([10, 11, 12, 13, 14]), Array([15, 16, 17, 18, 19])) of shape (4, 5),
                                        as it would truncate data or reduce the number of dimensions"""
    
    
    
    print m.isEquivalent(m*M)
    # False
    
    # trans matrix : t: 1, 2, 3, r: 45, 90, 30, s: 0.5, 1.0, 2.0
    m = MMatrix([0.0, 4.1633363423443383e-17, -0.5, 0.0, 0.25881904510252079, 0.96592582628906831, 1.3877787807814459e-16, 0.0, 1.9318516525781366, -0.51763809020504159, 0.0, 0.0, 1.0, 2.0, 3.0, 1.0])
    print "m:"
    print round(m, 2).formated()
    #[[0.0, 0.0, -0.5, 0.0],
    # [0.26, 0.97, 0.0, 0.0],
    # [1.93, -0.52, 0.0, 0.0],
    # [1.0, 2.0, 3.0, 1.0]]    
    print "m.transpose():"
    print round(m.transpose(),2).formated()
    #[[0.0, 0.26, 1.93, 1.0],
    # [0.0, 0.97, -0.52, 2.0],
    # [-0.5, 0.0, 0.0, 3.0],
    # [0.0, 0.0, 0.0, 1.0]]  
    print "m.isSingular():"     
    print m.isSingular()
    # False
    print "m.inverse():"
    print round(m.inverse(),2).formated()
    #[[0.0, 0.26, 0.48, 0.0],
    # [0.0, 0.97, -0.13, 0.0],
    # [-2.0, 0.0, 0.0, 0.0],
    # [6.0, -2.19, -0.22, 1.0]]   
    print "m.adjoint():" 
    print round(m.adjoint(),2).formated()
    #[[0.0, 0.26, 0.48, 0.0],
    # [0.0, 0.97, -0.13, 0.0],
    # [-2.0, 0.0, -0.0, 0.0],
    # [6.0, -2.19, -0.22, 1.0]]    
    print "m.adjugate():"
    print round(m.adjugate(),2).formated()
    #[[0.0, 0.26, 0.48, 0.0],
    # [0.0, 0.97, -0.13, 0.0],
    # [-2.0, 0.0, -0.0, 0.0],
    # [6.0, -2.19, -0.22, 1.0]]    
    print "m.homogenize():"
    print round(m.homogenize(),2).formated()
    #[[0.0, 0.0, -1.0, 0.0],
    # [0.26, 0.97, 0.0, 0.0],
    # [0.97, -0.26, -0.0, 0.0],
    # [1.0, 2.0, 3.0, 1.0]]    
    print "m.det():"
    print m.det()
    # 1.0
    print "m.det4x4():"
    print m.det4x4()
    # 1.0
    print "m.det3x3():"
    print m.det3x3()
    # 1.0
    print "m.weighted(0.5):"
    print round(m.weighted(0.5),2).formated()
    #[[0.53, 0.0, -0.53, 0.0],
    # [0.09, 0.99, 0.09, 0.0],
    # [1.05, -0.2, 1.05, 0.0],
    # [0.5, 1.0, 1.5, 1.0]]    
    print "m.blend(MMatrix.identity, 0.5):"
    print round(m.blend(MMatrix.identity, 0.5),2).formated()
    #[[0.53, 0.0, -0.53, 0.0],
    # [0.09, 0.99, 0.09, 0.0],
    # [1.05, -0.2, 1.05, 0.0],
    # [0.5, 1.0, 1.5, 1.0]]
      
    print "end tests MMatrix"

def _testMTransformationMatrix() :

    q = MQuaternion()
    print repr(q)
    # MQuaternion([0.0, 0.0, 0.0, 1.0])
    q = MQuaternion(1, 2, 3, 0.5)
    print repr(q)
    # MQuaternion([1.0, 2.0, 3.0, 0.5])
    q = MQuaternion(0.785, 0.785, 0.785, "xyz")
    print repr(q)
    # MQuaternion([0.191357439088, 0.461717715523, 0.191357439088, 0.844737481223])
    
    m = MMatrix()
    m.rotate = q
    print repr(m)
    # MMatrix([[0.500398163355, 0.499999841466, -0.706825181105, 0.0], [-0.146587362969, 0.853529322022, 0.499999841466, 0.0], [0.853295859083, -0.146587362969, 0.500398163355, 0.0], [0.0, 0.0, 0.0, 1.0]])

    
    print "MTransformationMatrix class", dir(MTransformationMatrix)
    m = MTransformationMatrix()
    print m.formated()
    #[[1.0, 0.0, 0.0, 0.0],
    # [0.0, 1.0, 0.0, 0.0],
    # [0.0, 0.0, 1.0, 0.0],
    # [0.0, 0.0, 0.0, 1.0]]    
    print m[0, 0]
    # 1.0
    print m[0:2, 0:3]
    # [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    print "MTransformationMatrix instance:", dir(m)
    print MTransformationMatrix.__readonly__
    print MTransformationMatrix.__slots__
    print MTransformationMatrix.shape
    print MTransformationMatrix.ndim
    print MTransformationMatrix.size
    print m.shape
    print m.ndim
    print m.size    
    # should fail
    m.shape = (4, 4)
    m.shape = 2
    
    print dir(MSpace)
       
    m = MTransformationMatrix.identity    
    # inherits from Matrix --> Array
    print isinstance(m, Matrix)
    # True
    print isinstance(m, Array)
    # True
    # as well as _api.MTransformationMatrix and _api.MMatrix
    print isinstance(m, _api.MTransformationMatrix)
    # True
    print isinstance(m, _api.MMatrix)
    # True    
    
    # accepted directly by API methods     
    n = _api.MMatrix()
    n = n.setToProduct(m, m)
    print repr(n)

    n = _api.MTransformationMatrix()
    n = n.assign(m)
    print repr(n)
    
    m = MTransformationMatrix.identity
    m.rotation = MQuaternion()
    print repr(m)
    print m.formated()
    
    
    n = MTransformationMatrix.identity 
    n.translation = MVector(1, 2, 3)
    print n.formated()
    print repr(n)
    
    o = m*n
    print repr(o)
    print o.formated()
    
    print "end tests MTransformationMatrix"
    
if __name__ == '__main__' :
    _testMVector()   
    _testMPoint()
    _testMColor()
    _testMMatrix()
    _testMTransformationMatrix()


    