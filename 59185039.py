import maya.cmds as cmds
import dw_maya_utils as dwu
import dw_presets_io as dwpreset
import dw_decorators as dwdeco
import dw_json as dwjson
import re

class MAttr(object):
    """Represent a maya attribute

    Args:
        node (str): a string for the maya node affected
        attr (str): a string that represent the attribute
    Attributes:
        attr_bypass (str): regex to bypass the compound attributes, because i need to connect and getattr
    """
    attr_bypass = re.compile('\[(\d+)?:(\d+)?\]')

    def __init__(self, node, attr='result'):
        self.__dict__['node'] = node  #: str: current priority node evaluated
        self.__dict__['attribute'] = attr  #: str: current priority node evaluated
        self.__dict__['idx'] = 0  #: str: current priority node evaluated

    def __getitem__(self, item):
        """
        getitem has been overrided so you can select the compound attributes
        ``mn = MayaNode('cluster1')``
        ``mn.node.weightList[0]``
        ``mn.node.weightList[1].weights[0:100]``

        Notes:
            the notations with list[0:0:0] is class slice whereas list[0] is just and int

        Args:
            item (Any): should be slice class or an int

        Returns:
            cls : MAttr is updated with the chosen index/slice
        """
        if isinstance(item, int):
            self.__dict__['attribute'] = '{}[{}]'.format(self.attr, item)
        else:
            if not item.start and not item.stop and not item.step:
                item = ':'
            else:
                item = ':'.join([str(i) for i in [item.start, item.stop, item.step] if i != None])
            self.__dict__['attribute'] = '{}[{}]'.format(self.attr, item)
        return self

    def __getattr__(self, attr):
        """
        __getattr__ is overriden in order to select attributes
        Args:
            attr (str): name of the attribute, even if we loop throught,

        Returns:
            str: it join all the attributes that has been chained : weightList[0].weight

        """
        myattr = '{}.{}'.format(self.attr, attr)
        if myattr in self.listAttr(myattr):
            return MAttr(self._node, '{}.{}'.format(self.attr, attr))
        else:
            return self.__getattribute__(attr)

    def __iter__(self):
        """
        To loop throught attributes values if needed (for example if we have an enum)
        Returns:
        """
        return self

    def next(self):
        """
        To loop throught attributes values if needed (for example if we have an enum)
        Returns:
        """
        mylist = self.get()
        if not isinstance(mylist, (list, tuple)):
            mylist = [mylist]
        else:
            if isinstance(mylist[0], (list, tuple)):
                if len(mylist) == 1:
                    mylist = mylist[0]
        try:
            item = mylist[self.__dict__['idx']]
        except IndexError:
            raise StopIteration()
        self.__dict__['idx'] += 1
        return item

    def __repr__(self):
        """
        Represent the data when you execute the class
        Returns:
            str: type attribute + value
        """
        try:
            space = ' '*16
            mess = '<<{}>>\n{}{}'.format(str(self._type),
                                         space,
                                             str(self.get()))
        except:
            mess = 'Warning Compound Attribute'
        return mess

    def __str__(self):
        """
        Returns:
            str: return the get() as a string
        """
        return str(self.get())

    def set(self, *args, **kwargs):
        """
        This is the cmds.setAttr but with string type supported with no flags requirement
        Args:
            *args (Any): maya arguments for the commands
            **kwargs (Any): all the flag you would try to parse
        """
        if not isinstance(args[0], basestring) and len(args) == 1:
            cmds.setAttr('{}.{}'.format(self._node, self.attr), args[0], **kwargs)
        elif isinstance(args[0], basestring) and len(args) == 1:
            cmds.setAttr('{}.{}'.format(self._node, self.attr), args[0], type = 'string', **kwargs)
        elif args or kwargs:
            cmds.setAttr('{}.{}'.format(self._node, self.attr), *args, **kwargs)

    def get(self):
        """
        this is the cmds.getAttr
        Returns:
            Any: cmds.getAttr()
        """
        if self.attr in self.listAttr(self.attr) or self.attr_bypass.search(self.attr):
            return cmds.getAttr('{}.{}'.format(self._node, self.attr))

    @dwdeco.acceptString('destination')
    def connect(self, destination, force=True):
        """
        This is the cmds.connectAttr
        Args:
            destination (bool): another attribute should be plugged
            force (bool):  by default True

        Returns:

        """
        _isConnec = [True if '.' in i and cmds.ls(i) else False for i in destination]
        if not all(_isConnec):
            invalid_input = ', '.join([i for x, i in zip(_isConnec, destination) if not x])
            cmds.error('please provide good attributes :``` {} ```are invalid'.format(invalid_input))

        if self.attr in self.listAttr(self.attr) or self.attr_bypass.search(self.attr):
            for d in destination:
                cmds.connectAttr('{}.{}'.format(self._node, self.attr), d, force=force)

    def listAttr(self, attr=None):
        """
        used to check if the attribute exist in his short or long form
        Args:
            attr (str): check if the attribute exist
        Returns:
            list: all the attributes available or the attribute
        """
        if attr:
            return cmds.listAttr('{}.{}'.format(self._node, attr)) + cmds.listAttr('{}.{}'.format(self._node, attr),
                                                                                   shortNames = True)
        return cmds.listAttr(self._node) + cmds.listAttr(self._node, shortNames = True)

    @property
    def _node(self):
        """
        This is the node inherated
        Returns:
            str: node from MayaNode
        """
        return self.__dict__['node']

    @property
    def attr(self):
        """
        Current Attribute
        Returns:
            str: attribute name
        """
        return self.__dict__['attribute']

    @property
    def _type(self):
        """
        Returns:
            str: type of the current attribute
        """
        o = cmds.getAttr('{}.{}'.format(self._node, self.attr), type = True)
        if isinstance(o, (list, tuple)):
            return list(set(o))
        return o

class MayaNode(object):
    """Represent a maya node as a class like pymel

    Only provide the name as a string, if you use preset, you can create a new node

    Note:
        Should use maya api for getting the node

    Args:
        name (str): a string for the maya node you want to encapsulate
        preset (:obj:`dict`, optional): Used for creating a new node from 'attrPreset'
            you can also just specify the nodeType with a string instead

    Attributes:
        maya_attr_name (maya_data): Any attribute from the name will look for actual maya attribute

    """

    def __init__(self, name, preset={}, blendValue=1):

        # this dict method is used to avoid calling __getattr__
        self.__dict__['node'] = name  #: str: current priority node evaluated
        self.__dict__['item'] = 1  #: int: can be either 0 or 1 and should be exented with Mesh or Cluster
        if preset:
            targ_ns = name.rsplit(':', 1)[0]
            self.loadNode(preset, blendValue, targ_ns)

    def __getitem__(self, item):
        """
        getitem has been overrided so you can select the main nodes sh or tr so when you do:
        ``mn = MayaNode('pCube1')``
        ``mn[0].node`` result as the transform
        ``mn[1].node`` result as the shape

        Note:
            By default ``mn.node`` is the transform
        """
        return self.setNode(item)

    def __getattr__(self, attr):
        """
        getattr has been overrided so you can select maya attributes and set them
        if you type an attribute, it will try to find if it exists in either shape or transform
        if it exists in both, it will always warn you that it returns shape in priority
        ``mn = MayaNode('pCube1')``
        ``mn.translateX = 10`` result in doing a cmds.setAttr
        ``mn.translateX.set(10)``
        ``mn.translateX.get()`` note that you to use get in order to do getAttr otherwise it __repr__ or __str__

        ``mn = MayaNode('cluster1')``
        ``mn.weightList[1].weights.get()`` is equivalent of cmds.getAttr('cluster1.weightList[1].weights[:]')

        Note:
            You cant have the value without .get()
        """
        if attr in self.listAttr(attr):
            return MAttr(self.node, attr)
        elif attr in self.__dict__:
            return self.__dict__[attr]
        else:
            try:
                return self.__getattribute__(attr)
            except AttributeError:
                cmds.warning('{} doesn\'t exists, return None instead')
                return None

    def __setattr__(self, key, value):
        """
        setattr has been overrided so you can set the value also with `=`
        ``mn = MayaNode('pCube1')``
        ``mn.translateX = 10`` result in doing a cmds.setAttr

        Note:
            it support maya kwargs/flags, the method is support string type
        """
        if key in self.listAttr(key) or key:
            try:
                if not isinstance(value, basestring):
                    MAttr(self.node, key).set(value)
            except AttributeError:
                if not isinstance(value, basestring):
                    cmds.setAttr('{}.{}'.format(self.node, self.attr), value)
                elif isinstance(value, basestring):
                    cmds.setAttr('{}.{}'.format(self.node, self.attr), value, type = 'string')

    @property
    def __node(self):
        """
        This one is used to get the actual node from __dict__
        """
        return self.__dict__['node']

    def setNode(self, index):
        """
        set the current node by __dict__, it is used with __getitem__
        Args:
            index (int): 0 and 1 available by default, might need more index for cluster for example
        Returns:
            cls: return itself

        """
        self.__dict__['item'] = index
        return self

    @property
    def node(self):
        """str: return the current node"""
        id = self.__dict__['item']
        if id == 0:
            return self.tr or self.sh
        else:
            return self.sh

    @property
    def nodeType(self):
        """str: return the current node type, by default it always return the shape"""
        if not self.sh:
            return cmds.nodeType(self.__node)
        else:
            return cmds.nodeType(self.sh)

    @property
    def sh(self):
        """str: return the main node (everything but not transform)"""
        if cmds.nodeType(self.__node) != 'transform':
            return self.__node
        else:
            _sh = cmds.listRelatives(self.__node, type='shape', ni=True)
            if _sh:
                return _sh[0]
            return
    @property
    def tr(self):
        """str: return the transform if there is one, otherwise return the shape too"""
        if cmds.nodeType(self.__node) == 'transform':
            return self.__node
        else:
            _tr = cmds.listRelatives(self.__node, p=True)
            if _tr:
                _sh = cmds.listRelatives(_tr, type='shape', ni=True)
                if _sh:
                    return _tr[0]
        return self.sh

    def listAttr(self, attr=None):

        """ list all the attr of the node or if the attr exist

        Args:
            attr (str, optional): name of an attribute

        Returns:
            list: it gives the list of attributes existing

        """

        current = self.node
        tr = self.tr
        sh = self.sh

        attr_list_tr = []
        if tr:
            attr_list_tr += cmds.listAttr(tr)
            attr_list_tr += cmds.listAttr(tr, shortNames = True)

        attr_list_sh = []
        if sh:
            attr_list_sh += cmds.listAttr(sh)
            attr_list_sh += cmds.listAttr(sh, shortNames = True)

        if current == tr:
            if attr:
                if attr in attr_list_tr and attr in attr_list_sh:
                    if sh != tr:
                        cmds.warning('attribute `{}` exists in shape and transform, result from : {}.{}'.format(attr,
                                                                                                                current,
                                                                                                                attr))
                elif attr not in attr_list_tr:
                    if attr in attr_list_sh:
                        self.__dict__['item'] = 1
                        return attr_list_sh
            return attr_list_tr
        elif current == sh:
            if attr:
                if attr in attr_list_tr and attr in attr_list_sh:
                    if sh != tr:
                        cmds.warning('attribute `{}` exists in shape and transform, result from : {}.{}'.format(attr,
                                                                                                                current,
                                                                                                                attr))
                elif attr not in attr_list_sh:
                    if attr in attr_list_tr:
                        self.__dict__['item'] = 0
                        return attr_list_tr
            return attr_list_sh

    def attrPreset(self, node=None):
        """
        common method to create a preset of the node
        if nothing is specified it will try to make a dictionnary with both tr and sh

        Args:
            node (str, optional): name of the node

        Returns:
            dict: it gives the list of attributes existing

        """

        if node is not None:
            if node == 0:
                return dwpreset.createAttrPreset(self.tr)
            else:
                return dwpreset.createAttrPreset(self.sh)
        else:
            if self.tr == self.sh:
                return dwpreset.createAttrPreset(self.node)
            else:
                tr_dic = dwpreset.createAttrPreset(self.tr)
                sh_dic = dwpreset.createAttrPreset(self.sh)
                combine_dic = dwu.merge_two_dicts(tr_dic, sh_dic)

                out_dic = {}
                key = self.tr.split(':')[-1]
                out_dic[key] = combine_dic
                out_dic['{}_nodeType'.format(key)] = self.nodeType

                return out_dic

    def rename(self, name):
        """
        Rename the transform and the shape and update the class with the new name
        It keeps the maya way of renaming where, renaming the shape will rename trnsform
        and if you rename the transform will rename the shape
        Also it will try to keep the Shape with Shape at the end
        If there is no transform, it will make a straight rename

        Args:
            node (str, optional): name of the node

        Returns:
            cls: the class self is returned so you can keep playing with the node
        """
        sh_p = '[Ss]hape(\d+)?$'
        p = re.compile(sh_p)

        if self.tr == self.sh:
            cmds.rename(self.tr, name)
        else:
            if self.sh == name:
                # if shape, was set on creation
                _tmp = cmds.rename(self.sh, 'dwTmpRename')
                # if name has maya Shape pattern, do the replace
                if p.search(name):
                    id = p.search(name).group(1) or ''
                    _sh = cmds.rename(self.sh, name)
                    self.__dict__['node'] = name
                    _tr_name = p.sub(id, name)
                    self.__dict__['node'] = name
                    _tr = cmds.rename(self.tr, _tr_name, ignoreShape=True)
                else:
                    _sh = cmds.rename(self.sh, name)
                    self.__dict__['node'] = name
                    cmds.rename(self.tr, name, ignoreShape=True)
                    self.__dict__['node'] = name
                    cmds.rename(self.sh, name + 'Shape')
            else:
                cmds.rename(self.tr, name, ignoreShape=True)
                self.__dict__['node'] = name
                cmds.rename(self.sh, name+'Shape')
        self.__dict__['node'] = name
        return self.tr

    def createNode(self, preset, targ_ns=':'):
        """
        Like maya cmds.createNode() but work with preset dictionnary or single string
        One of the good thing, it is giving a constant name. IE :

        `cmds.createNode('mesh', name='toto')` result into a polysurface1 transform and a shape mesh called toto
        `mn = MayaNode('toto', 'mesh')` result creating toto transform and a shape called totoShape

        Also if the preset is a dictionnary it must contain a key:nodeType, value:mesh and it will set all the other
        attributes.

        Args:
            preset (Any):

        Returns:
            str: new node name

        """

        if isinstance(preset, basestring):
            # If we give some string, it will conform the dictionnary
            _type = preset[:]
            if _type not in cmds.ls(nt=True):
                cmds.error('Please provide a valid : string nodeType or a key `nodeType`')
            preset = {self.__dict__['node'] + '_nodeType': _type}

        # we try to determine if we create a node from scratch or if we load it
        # in case of loading, we need to remap the dictionnary keys with the correct namespace
        if targ_ns == ':'  or targ_ns == '':
            # in this case we have created the node with a basestring type so we need to add the namespace
            _type = self.__dict__['node'] + '_nodeType'
            if _type not in preset:
                _type = targ_ns + ':' + self.__dict__['node'] + '_nodeType'
        else:
            # In this case we create a node with a namespace but the preset is namespace agnostic
            _type = self.__dict__['node'] + '_nodeType'
            if _type not in preset:
                _type = self.__dict__['node'].rsplit(':', 1)[-1] + '_nodeType'

        # this part is for creating a good node name, at the end of the proc it will rename
        flags = dwu.Flags(preset, self.__dict__['node'], 'name', 'n', dic={})

        new_node = cmds.createNode(preset[_type])
        self.__dict__['node'] = new_node
        if flags:
            new_name = self.rename(**flags)
            return new_name

    def saveNode(self, path=str, file=str):
        """
        save the node as json
        Args:
            path (str): /path/gneh/
            file (str): myfile

        Returns:
            /path/gneh/myfile.json
        """
        if path.startswith('/'):
            if not path.endswith('/'):
                path += '/'
            if '.' not in file:
                file += '.json'
            fullpath = path + file

            print('node saved as json to {}'.format(fullpath))
            return dwjson.saveJson(fullpath, self.attrPreset())

    def loadNode(self, preset=dict, blend=1, targ_ns=':'):
        """

        Args:
            preset ():

        Returns:

        """
        if isinstance(preset, basestring):
            self.createNode(preset)

        if not isinstance(preset, basestring):
            for k in preset:
                if not k.endswith('_nodeType'):
                    if targ_ns not in [':', '']:
                        nodename = targ_ns + ':' + k
                    else:
                        nodename = k
                    ntype = preset[k + '_nodeType']
                    if nodename == self.__dict__['node']:
                        if not cmds.objExists(nodename):
                            new_name = self.createNode(preset, targ_ns)
                        else:
                            new_name = k

                        dwpreset.blendAttrDic(k, new_name, preset[k], blend)
                        mainType = preset[k][k]['nodeType']
                        if mainType != ntype:
                            for sh in preset[k]:
                                if 'nodeType' in preset[k][sh]:
                                    if preset[k][sh]['nodeType'] == ntype:
                                        dwpreset.blendAttrDic(sh, self.sh, preset[k], blend)
                                        break
                        break
