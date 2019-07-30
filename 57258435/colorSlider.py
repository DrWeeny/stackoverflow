import maya.cmds as cmds
import maya.OpenMaya as om
import maya.mel as mel
import sys
import math
from functools import partial


def create(rigType, sideColor, isStretch, *args):

    # DW : refreshed every time by property that is executing before being passed
    if rigType == 0:
        print('IK/FK mode')
    elif rigType == 1:
        print('IK mode')
    elif rigType == 2:
        print('FK mode')

    # DW : in this state of the script, it will return always 7 because there is no refresh query
    #      so you can see to pass outside your class some arguments
    #      below an example for an alternative of property
    print('color picked is {}'.format(sideColor))

    # DW : in this example the function for getting the status is passed
    #      it is different from property because we still use to execute the command
    if isStretch():
        print('rig is stretchy')
    else:
        print('no stretch')

    # Dw : note that if you create an instance of your window inside a variable :
    # ui = rigCreator()
    # ui.ikfkPick is something you can print at any moment to debug
    # any variable with 'self' would be replaced by 'ui' in this case


class rigCreator:

    # DW : default colour, self don't need to be specify but it is like so
    #      personally I put the important parameters or parameters that set default values on top
    #      it is easier when parsing the code few month later
    sideColor = 7  #: DW : don't hesitate to do inline comment to say this is RED color (im followng google doctstring https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)
    isStretch = 0
    ikfkPick = 0  #: pick IK/FK option,  1 for IK, 2 for FK

    def __init__(self, *args):

       #self.startFunction()
        self.window = "uiWindow"
        self.title = "Rigging Tool Bipeds"
        self.winSize = (150, 200)
        self.createUI()

    def createUI(self):
        # DW : only put *args if you are using maya command flags, otherwise no need
        #check if window and prefs exist. If yes, delete


        if cmds.window(self.window, ex=True):
            cmds.deleteUI(self.window, wnd=True)
        elif cmds.windowPref(self.window, ex=True):
            cmds.windowPref(self.window, r=True)

        self.window = cmds.window(self.window, t=self.title, wh = self.winSize, s=1, mnb=1, mxb=1)
        self.mainForm = cmds.formLayout(nd=100)
        self.tagLine= cmds.text(label = "Rig Tool")
        cmds.frameLayout(label="1. Choose the root joint")
        self.Layout = cmds.columnLayout(adj=1)

        #Add a saparator to the window
        cmds.separator()

        # button to select the first joint
        cmds.rowColumnLayout (nc = 2, cs=[(1,6), (2,6)])
        self.tf_rootBt = cmds.textField ('rootJnt', tx = 'First joint of your Arm chain', w = 250)
        #cmds.textFieldButtonGrp('rootJnt', width=380, cal=(8, "center"), cw3=(100, 200, 75), h=40, pht="First joint of your Arm chain", l="First Joint", bl="Select", bc = lambda x: findJnt(), p=self.Layout)
        # DW : use lambda only to parse arguments, the better way to not make confusion is to use partial module
        cmds.button(l = 'Select', c = self.findJnt)

        cmds.setParent(self.Layout)
        frame = cmds.frameLayout("2. Name options", lv=1, li=1, w=250)

        #cmds.text(label="", align = "left")
        cmds.rowColumnLayout(nc=4, cs=[(1,6), (2,6), (3,6), (4,6)])
        #cmds.text('Side', l='Side:')
        # DW : string naming can be dangerous, if another script create this type of name, it will conflict
        #      put your ctrl name into a variable or a class variable if you are using it somewhere else
        #      Same don't use lambda if you are not parsing arguments
        self.om_partside = cmds.optionMenu('Part_Side', l='Side:', cc=self.colorChange, acc=1, ni=1)
        cmds.menuItem(label='L_')
        cmds.menuItem(label='R_')
        cmds.menuItem(label='_')
        cmds.text('Part', l='Part:')
        cmds.optionMenu('part_Body')
        cmds.menuItem(label='Arm')
        cmds.menuItem(label='Leg')
        cmds.menuItem(label='Spine')


        cmds.setParent(self.Layout)
        frame2 = cmds.frameLayout("3. Type of rig", lv=True, li=1, w=250)
        cmds.rowColumnLayout(nc=3, cs=[(1,6), (2,6), (3,6)])
        # DW :conforming to the default user settings on top of the class
        # demonstrate property in class
        self.rc_ikfk = cmds.radioCollection("limb side")
        for x, lb in enumerate(['IK/FK', 'IK', 'FK']):
            if x == self.ikfkPick:
                defvalue = True
            else:
                defvalue = False
            cmds.radioButton(label=lb, select=defvalue)

        cmds.setParent(self.Layout)
        frame3 = cmds.frameLayout("4. Thick if you want to apply stretch", lv=True, li=1, w=250)
        cmds.rowColumnLayout(nc=1, cs=[(1,6)])
        # DW : adding default value, class variable naming
        self.ckb_stretch = cmds.checkBox( label='Stretchy limb', align='center', value=self.isStretch, cc=self.getStretch)

        cmds.setParent(self.Layout)


        cmds.setParent(self.Layout)
        frame4 = cmds.frameLayout("5. Pick icon color", lv=True, li=1, w=250)
        cmds.gridLayout(nr=1, nc=5, cwh=[62,20])
        cmds.iconTextButton('darkBlue_Btn', bgc=[.000,.016,.373])
        cmds.iconTextButton('lightBlue_Btn', bgc=[0,0,1])
        cmds.iconTextButton('Brown_Btn', bgc=[.537,.278,.2])
        cmds.iconTextButton('red_Btn', bgc=[1,0,0])
        cmds.iconTextButton('Yellow_Btn', bgc=[1,1,0])
        cmds.setParent(self.Layout)

        self.sl_colorBt = cmds.colorIndexSliderGrp('rigColor', w=250, h=50, cw2=(150,0), min=0, max=31, v= self.sideColor)
        # This button will creat the chain of joins with streatch and squach
        # DW : never use comma for executing some function, if you use this script as a module afterward,
        #      you will have problems dealing with python namespacing
        #      maya is always passing a default argument True, so put *args in any command that is used by your ui controls
        cmds.button('b_create', label='Create', h=30, c=partial(create, self.rigType, self.sideColor, self.getStretch))

        #show the window
        cmds.showWindow(self.window)


    def findJnt(self, *args):

        self.root = cmds.ls(sl=True, type='joint', l=True)
        # DW : just becaue I was toying around the concept of root, sorry... ignor below
        rootAbove = [i for i in self.root[0].split('|')[1:] if cmds.nodeType(i) == 'joint']
        if rootAbove[0] != self.root[0].split('|')[-1]:
            cmds.warning('you didn\'t choose the top joint !')

        if len(self.root) == 1:
            selRoot = self.root[0]
            # DW : you dont have to store your edit, use class variable instead of string name
            cmds.textField (self.tf_rootBt, e=1, tx=selRoot.split('|')[-1])
        else:
            cmds.warning ('Please select only the first joint!')

    def colorChange(self, *args):

        # DW : you don't need to put self on limbSide has you are not using it anywhere else
        limbSide = cmds.optionMenu(self.om_partside, q=1, sl=1)
        # DW : putting some elif
        if limbSide == 1:
            self.sideColor = 7
        elif limbSide == 2:
            self.sideColor = 14
        elif limbSide ==3:
            self.sideColor = 18
        # DW : conforming editing controls
        cmds.colorIndexSliderGrp(self.sl_colorBt, e=1, v=self.sideColor)


    def partBody(self, *args):
        pass

    @property
    def rigType(self):
        '''Returns:
               int: option selected in ui'''
        # DW : demonstrating property usage and partial
        rb = cmds.radioCollection(self.rc_ikfk, q=True, select=True)
        cia = [i.split('|')[-1] for i in cmds.radioCollection(self.rc_ikfk, q=True, cia=True)]
        return cia.index(rb)


    def getStretch(self, *args):
        """function to get if the user need stretchy things

        Note:
            *args is just here to bypass maya default added True argument

        Returns:
            bool: use stretch or not

        """
        # dw making some example function with some docstring
        self.isStretch = cmds.checkBox(self.ckb_stretch, q=True, value=True)
        return self.isStretch

rigCreator()