import maya.cmds as mc
import pymel.all as pma
from functools import partial

BOOLEANMODE_ADD = 1
BOOLEANMODE_SUBTRACT = 2
PRIMITIVE_CUBE = 0
PRIMITIVE_CYLINDER = 1
PRIMITIVE_SPHERE = 2
PRIMITIVE_CUSTOM = 3


def cleanUp ():
    mc.delete(constructionHistory=True)
    mc.delete("*_ctrl*")

def hider(option, *args):
    if option == 0:
        mc.hide()
    elif option == 1:
        mc.select ("*_ctrl*")
        mc.hide()
    elif option == 2:
        mc.select ("*_ctrl*")
        mc.showHidden()
        mc.select (clear=True)

def fixMaterial():
    # pma.hyperShade( assign="lambert1" )
    # works better with the command sets, jut put the SG you need
    sel = mc.ls(sl = True)
    if not mc.objExists('grey20'):
        shaLambert = mc.shadingNode('lambert', asShader = True, name = 'grey20')
        shaLambertSG = mc.sets(name = 'grey20SG', empty = True, renderable = True, noSurfaceShader = True)
        mc.connectAttr('grey20.outColor', 'grey20SG.surfaceShader')
    mc.sets(sel, edit = True, fe = shaLambertSG)

def triangulate():
    mc.polyTriangulate()

def creator(primitives, *args):
    selection = mc.ls(sl=True)
    for x in selection:
        if primitives == PRIMITIVE_CUBE:
            a = makeCube() #Create cube
        if primitives == PRIMITIVE_CYLINDER:
            a = makeCyl() #Create cyl 
        if primitives == PRIMITIVE_SPHERE:
            a = makeSphere() #Create sphere 
        if primitives == PRIMITIVE_CUSTOM:
            a = selection[1]  
            x = selection[0]
            mc.select(a)
        b = createController(a)
        meshConstrainer (b,a)
        operator(x,a) 
        mc.select(b)

def operator(meshA, meshB):
   booleanmode = get_boolean_mode()
   # is there a way to replace this pymel ?
   pma.polyBoolOp( meshA, meshB, op=booleanmode, n="basemesh" )
   fixMaterial()  #REMINDER: Need to be replaced with the actual assigned material and not with a lambert1 so for who is working with other materials can easyly keep using that


def get_boolean_mode(addRadioB=None, subRadioB=None):
    # should not be implemented as string.....
    if mc.radioButton('addRadio', query = True, select = True) :
        return BOOLEANMODE_ADD
    if mc.radioButton('subRadio', query = True, select = True) :
        return BOOLEANMODE_SUBTRACT
    return None

def makeCube():
    cubeTransform = mc.polyCube(n="cubetobool", w=1, h=1, d=1, sx=1, sy=1, sz=1)[0]
    return cubeTransform       

def makeCyl():
    cylTransform = mc.polyCylinder(n="cubetobool", r=1, h=2, sx=20)[0]
    return cylTransform   

def makeSphere():
    sphereTransform = mc.polySphere(n="cubetobool", r=1, sx=20, sy=20, cuv=2)[0]
    return sphereTransform    


def meshConstrainer(constrainer, constrained):   
    mc.scaleConstraint( constrainer, constrained, maintainOffset=True)
    mc.parentConstraint( constrainer, constrained, maintainOffset=True)


def createController(object):
    #object = pma.ls(sl=True) 
    pivotObj = mc.xform(object,query=True,t=True,worldSpace=True)
    edges = mc.filterExpand(mc.polyListComponentConversion(te=1),sm=32,ex=1) # convert edges to curve ancd create one object
    for edge in edges:
        vtx = mc.ls(mc.polyListComponentConversion(edge,fe=1,tv=1),fl=1)
        p1 = mc.pointPosition(vtx[0])
        p2 = mc.pointPosition(vtx[1])
        curves = mc.curve(n="line_ctrl_curve", d=1,p=(p1,p2))

    ctrl = mc.curve (n="bool_ctrl", d=1,ws=True, p=pivotObj)
    mc.xform (centerPivots=True)
    for curveEdge in mc.ls ("line_ctrl*"):
        mc.parent(curveEdge,ctrl, s=1, r=1)
        mc.rename(curveEdge, "shapeunused")


    transforms =  mc.ls(type='transform')
    deleteList = []
    for tran in transforms:
        if mc.nodeType(tran) == 'transform':
            children = mc.listRelatives(tran, c=True)
            if children is None:
                #print '%s, has no childred' %(tran)
                deleteList.append(tran)

    if not deleteList:           
       mc.delete(deleteList)
    return ctrl


def deleteUI(name, *args):
    mc.deleteUI(name)


#################TUTORIAL
def super_bool_tut():
    windowNameTut = "Tutorial"
    if mc.window(windowNameTut , exists=True):
        mc.deleteUI(windowNameTut)
    windowTutorial = mc.window(windowNameTut, title = windowNameTut, width = 400, height = 300, backgroundColor = [0.2, 0.2, 0.2])
    mainSubLayout = mc.columnLayout( "testColumn", adjustableColumn = True)
    lb_txt = "This tool is a super tool to make booleans wrote by Leonardo Iezzi. To make it works correctly, you need to have your base mesh already even if just a cube. "
    lb_txt += "With your base mesh selected just press one of the three buttons on the windows to subtract or add those primitives. "
    lb_txt += "If you want to use a custom mesh for the operation: select your base mesh then the custom one "
    lb_txt += "(it's important to pick your base mesh first) and then press the 'Use custom mesh' button. After you have done, select your base mesh and press 'Clean Up.'"
    mc.text("intro", label = lb_txt ,wordWrap= True, height = 100, backgroundColor = [0.2, 0.2, 0.2], align='left', parent = mainSubLayout)

    mc.separator(parent = "testColumn", height=20)
    mc.button("goit", label = "Got it", width = 120, height = 40, backgroundColor = [0.5, 0.5, 0.5], parent = mainSubLayout, command = partial(deleteUI, windowNameTut))

    mc.showWindow()

################################################################################################UI################################################# 
# @@@@@@@    THIS IS POLYSHIFTER!! I HAVE ADDED THIS AS A FUNCTION INSTEAD OF LEAVING IT UNINDENTED
def super_bool_ui():
    windowName = "SuperBool"
    w, h = (120, 200)
    if mc.window(windowName , exists=True):
        mc.deleteUI(windowName)
    window = mc.window( windowName, title= windowName, width = w, height = h)
    mainLayout = mc.columnLayout( "mainColumn", adjustableColumn = True)

    ################################################################################################UI#################################################
    gridl_01 = mc.gridLayout("nameGridLayout01", numberOfRowsColumns = (1,4), cellWidthHeight = (40,40), parent = mainLayout)
    btn_symb = mc.symbolButton("nameButton1", image = "polyCube.png", width = 40, height = 40, backgroundColor = [0.2, 0.2, 0.2], parent = gridl_01, command = partial(creator, PRIMITIVE_CUBE))
    mc.symbolButton("nameButton2", image = "polyCylinder.png", width = 40, height = 40, backgroundColor = [0.2, 0.2, 0.2], parent = gridl_01, command = partial(creator, PRIMITIVE_CYLINDER))
    mc.symbolButton("nameButton3", image = "polySphere.png", width = 40, height = 40, backgroundColor = [0.2, 0.2, 0.2], parent = gridl_01, command = partial(creator, PRIMITIVE_SPHERE))
    vl_column01 = mc.columnLayout("columnLayoutName01", adjustableColumn = True, backgroundColor = [0.2, 0.2, 0.2], p=mainLayout)
    mc.radioCollection("collection10", parent = vl_column01)
    subRadioB = mc.radioButton("subRadio", select = True, label = "Sub")
    addRadioB = mc.radioButton("addRadio", label = "Add")
    ################################################################################################UI#################################################
    mc.separator(parent = mainLayout, height=20)

    mc.button("customMeshB", label = "Use Custom Mesh", width = 120, height = 40, backgroundColor = [0.2, 0.2, 0.2], parent = mainLayout, command = partial(creator, PRIMITIVE_CUSTOM))

    mc.separator(parent = mainLayout, height=20)
    ################################################################################################UI#################################################
    gridl_02 = mc.gridLayout("nameGridLayout03", numberOfRowsColumns = (1,3), cellWidthHeight = (53,40), parent = mainLayout)
    mc.button("hidSelB", label = "Hide Sel",  height = 40, backgroundColor = [0.2, 0.2, 0.2], parent = gridl_02, command = partial(hider, 0))
    mc.button("hidAllB", label = "Hide All",  height = 40, backgroundColor = [0.2, 0.2, 0.2], parent = gridl_02, command = partial(hider, 1))
    mc.button("showAll", label = "Show All",  height = 40, backgroundColor = [0.2, 0.2, 0.2], parent = gridl_02, command = partial(hider, 2))

    mc.separator(parent = mainLayout, height=20)

    mc.button("clean", label = "Clean Up", width = 120, height = 40, backgroundColor = [0.2, 0.2, 0.2], parent = mainLayout, command = cleanUp)

    mc.separator(parent = mainLayout, height=20)
    ################################################################################################UI#################################################
    ################################################################################################UI#################################################
    gridl_03 = mc.gridLayout("nameGridLayout02", numberOfRowsColumns = (1,2), cellWidthHeight = (80,40), parent = mainLayout)
    mc.button("triangB", label = "Triangulate", width = 120, height = 40, backgroundColor = [0.2, 0.2, 0.2], parent = gridl_03, command = triangulate)
    mc.button("fixMatB", label = "FixMaterial", width = 120, height = 40, backgroundColor = [0.2, 0.2, 0.2], parent = gridl_03, command = fixMaterial)
    ################################################################################################UI#################################################
    mc.showWindow()


###################################################################
##################                              ###################
##################    END OF SUPER BOOL TOOL    ###################
##################                              ###################
###################################################################
###################################################################
##################                              ###################
##################   BEGINNING OF MY UI SCRIPT  ###################
##################                              ###################
###################################################################

#### My custom script ####
def my_custom_script_com(*args):
    super_bool_ui()
    super_bool_tut()

# Create a custom floating window with 
if mc.window('ToolsWindow', q=True, exists=True):
    mc.deleteUI('ToolsWindow')
if mc.workspaceControl('ToolsWorkspaceControl', q=True, exists=True):
    mc.deleteUI('ToolsWorkspaceControl')
mc.window('ToolsWindow')
mainL = mc.columnLayout()
tabLayout = mc.tabLayout('ToolsTabs', p=mainL)

#########################################################
##################    IMPORTING PANEL    ################
#########################################################
tabMenu = mc.columnLayout("Menu", adj=True, p=tabLayout)
separator_long = mc.separator(
                         height=10,
                         style='in', p=tabMenu)

mc.button(label="MyCustomScript", command = my_custom_script_com, p=tabMenu)
mc.showWindow()

