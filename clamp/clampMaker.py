import OCC
from OCC.TopoDS import TopoDS_Compound, TopoDS_Shape
from OCC.BRep import BRep_Builder
from OCC.BRepTools import breptools_Write
from OCC.Geom import Geom_Ellipse
from math import pi
from OCC.gp import *
from OCC.BRepBuilderAPI import BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeFace, BRepBuilderAPI_Transform
from OCC.BRepPrimAPI import BRepPrimAPI_MakePrism, BRepPrimAPI_MakeSphere
from OCC.BRepAlgoAPI import BRepAlgoAPI_Cut
from math import cos, sin
from OCC.TopTools import TopTools_ListOfShape
from OCC.BRepTools import breptools_Read
from OCC.BRepAdaptor import BRepAdaptor_CompCurve
from OCCUtils import Topo

def writeBRep(filename, shapeList):
    aRes = TopoDS_Compound()
    aBuilder = BRep_Builder()
    aBuilder.MakeCompound(aRes)
    for shape in shapeList:
        aBuilder.Add(aRes, shape)
    breptools_Write(aRes, filename)

def makeEllipticalAnnularSolid(rx_outer,ry_outer,rx_inner,ry_inner,z_min,z_max):

    # Make the outer part of the clamp
    ax = gp_Ax2(gp_Pnt(0,0,z_min),gp_Dir(0,0,1),gp_Dir(1,0,0))
    ge = Geom_Ellipse(ax,rx_outer,ry_outer)
    elip = ge.Elips()
    me = BRepBuilderAPI_MakeEdge(elip,0,2*pi)
    edge = me.Edge()
    mw = BRepBuilderAPI_MakeWire(edge)
    wire = mw.Wire()
    pln = gp_Pln(gp_Pnt(0,0,z_min),gp_Dir(0,0,1))
    mf = BRepBuilderAPI_MakeFace(pln,wire)
    face = mf.Face()
    mp = BRepPrimAPI_MakePrism(face,gp_Vec(0,0,z_max-z_min))
    body = mp.Shape()

    # Make the cutter for the inner hole body
    ax = gp_Ax2(gp_Pnt(0,0,z_min-1),gp_Dir(0,0,1),gp_Dir(1,0,0))
    ge = Geom_Ellipse(ax,rx_inner,ry_inner)
    elip = ge.Elips()
    me = BRepBuilderAPI_MakeEdge(elip,0,2*pi)
    edge = me.Edge()
    mw = BRepBuilderAPI_MakeWire(edge)
    wire = mw.Wire()
    pln = gp_Pln(gp_Pnt(0,0,z_min-1),gp_Dir(0,0,1))
    mf = BRepBuilderAPI_MakeFace(pln,wire)
    face = mf.Face()
    mp = BRepPrimAPI_MakePrism(face,gp_Vec(0,0,z_max+1))
    innerHoleCutter = mp.Shape()

    # Cut out the middle
    mc = BRepAlgoAPI_Cut(body,innerHoleCutter)
    return mc.Shape()

def makeEllipticalAnnularSolidSlice(rx_outer,ry_outer,rx_inner,ry_inner,z_min,z_max,theta0,theta1,bias=0.5):
    # bias: 0.5 means the
    # theta is the radius where the pie sliced ends coinside with theta1 and theta0
    full = makeEllipticalAnnularSolid(rx_outer,ry_outer,rx_inner,ry_inner,z_min,z_max)
    ax = gp_Ax2(gp_Pnt(0,0,z_min),gp_Dir(0,0,1),gp_Dir(1,0,0))
    rx = (rx_outer-rx_inner)*bias + rx_inner
    ry = (ry_outer-ry_inner)*bias + ry_inner
    ge = Geom_Ellipse(ax,rx,ry)
    elip = ge.Elips()
    me = BRepBuilderAPI_MakeEdge(elip,0,2*pi)
    edge = me.Edge()

def makePieSlice(r,theta0,theta1,z_min,z_max):
    p0 = gp_Pnt(0,0,z_min)
    p1 = gp_Pnt(r*cos(theta0),r*sin(theta0),z_min)
    p2 = gp_Pnt(r*cos(theta1),r*sin(theta1),z_min)
    edges = []
    los = TopTools_ListOfShape()
    me = BRepBuilderAPI_MakeEdge(p0,p1)
    edges.append(me.Edge())
    los.Append(me.Edge())
    ax = gp_Ax2(gp_Pnt(0,0,z_min),gp_Dir(0,0,1),gp_Dir(1,0,0))
    circ = gp_Circ(ax,r)
    me = BRepBuilderAPI_MakeEdge(circ,theta0,theta1)
    edges.append(me.Edge())
    los.Append(me.Edge())
    me = BRepBuilderAPI_MakeEdge(p2,p0)
    edges.append(me.Edge())
    los.Append(me.Edge())

    """
    mw = BRepBuilderAPI_MakeWire()
    for i in edges:
      mw.Add(i)
    """
    mw = BRepBuilderAPI_MakeWire()
    mw.Add(los)
    
    pln = gp_Pln(gp_Pnt(0,0,z_min),gp_Dir(0,0,1))
    mf = BRepBuilderAPI_MakeFace(pln,mw.Wire())
    face = mf.Face()
    mp = BRepPrimAPI_MakePrism(face,gp_Vec(0,0,z_max-z_min))
    return mp.Shape()

def makeBall(r):
    ax = gp_Ax2(gp_Pnt(0,0,0),gp_Dir(0,0,1),gp_Dir(0,1,0))
    ms = BRepPrimAPI_MakeSphere(ax,r)
    return ms.Shape()

def makeStringerWithContinuousSlot():
    thickness = 5.0
    width = 25.0
    slot_width = 5.0
    slot_depth = thickness/4.0
    length = 150.0

    points = []

    x = 0
    y = 0
    z = 0

    x = thickness/2.0
    y = -width/2.0
    points.append(gp_Pnt(x,y,z)) # bottom right corner

    y = -slot_width /2.0
    points.append(gp_Pnt(x,y,z)) 

    x = x - slot_depth
    points.append(gp_Pnt(x,y,z)) 

    y = slot_width /2.0
    points.append(gp_Pnt(x,y,z)) 

    x = x + slot_depth
    points.append(gp_Pnt(x,y,z)) 

    y = width / 2.0  # top right corner
    points.append(gp_Pnt(x,y,z)) 

    x = -thickness / 2.0 # top left corner
    points.append(gp_Pnt(x,y,z))

    y = slot_width / 2.0
    points.append(gp_Pnt(x,y,z))

    x = x + slot_depth
    points.append(gp_Pnt(x,y,z))

    y = -slot_width / 2.0
    points.append(gp_Pnt(x,y,z))

    x = x - slot_depth
    points.append(gp_Pnt(x,y,z))

    y = -width / 2.0
    points.append(gp_Pnt(x,y,z)) # bottom left corner

    x = thickness / 2.0 
    points.append(gp_Pnt(x,y,z)) # back to the bottom right corner

    mw = BRepBuilderAPI_MakeWire()
    for i in range(len(points)-1):
      me = BRepBuilderAPI_MakeEdge(points[i],points[i+1])
      edge = me.Edge()
      mw.Add(edge)

    mf = BRepBuilderAPI_MakeFace(mw.Wire())
    mp = BRepPrimAPI_MakePrism(mf.Face(),gp_Vec(0,0,length))
    return mp.Shape()

class Clamp:

    def __init__(self):
        pass

class BallRetainer:

    def __init__(self):
        pass

class MakeSlotShapedSolid:

    def __init__(self):
      """
      ax2 is in the middle of the slot on the back face
      The first direction of the ax2 is the extrusion direction.
      The second direction is the slot direction.
      """
      self.ax2 = gp_Ax2(gp_Pnt(0,0,0),gp_Dir(0,0,1),gp_Dir(1,0,0))
      self.thickness = 5.0
      self.width = 20.0
      self.length = 150.0

    def Solid(self):

      mw = BRepBuilderAPI_MakeWire()
      points = []

      x = -self.length/2.0
      y = -self.width/2.0
      z = 0.0
      points.append(gp_Pnt(x,y,z))

      x = self.length/2.0
      points.append(gp_Pnt(x,y,z))

      me = BRepBuilderAPI_MakeEdge(points[0],points[1])
      mw.Add(me.Edge()) # bottom edge

      ax = gp_Ax2(gp_Pnt(x,0,0),gp_Dir(0,0,1),gp_Dir(0,-1,0))
      circ = gp_Circ(ax,self.width/2.0)
      me = BRepBuilderAPI_MakeEdge(circ,0,pi)
      mw.Add(me.Edge())

      points = []
      y = self.width/2.0
      points.append(gp_Pnt(x,y,z))

      x = -self.length/2.0
      points.append(gp_Pnt(x,y,z))
      me = BRepBuilderAPI_MakeEdge(points[0],points[1])
      mw.Add(me.Edge()) # top edge

      ax = gp_Ax2(gp_Pnt(x,0,0),gp_Dir(0,0,1),gp_Dir(0,1,0))
      circ = gp_Circ(ax,self.width/2.0)
      me = BRepBuilderAPI_MakeEdge(circ,0,pi)
      mw.Add(me.Edge())

      mf = BRepBuilderAPI_MakeFace(mw.Wire())
      mp = BRepPrimAPI_MakePrism(mf.Face(),gp_Vec(0,0,self.thickness))

      shape = mp.Shape()

      #v_trans = gp_Vec(self.ax2.Location().XYZ())
      ax = gp_Ax2(gp_Pnt(0,0,0),gp_Dir(0,0,1),gp_Dir(1,0,0))
      #mainRotationAngle = ax.Angle(self.ax2)

      trsf = gp_Trsf()
      trsf.SetTransformation(gp_Ax3(self.ax2),gp_Ax3(ax))

      mt = BRepBuilderAPI_Transform(shape,trsf)
      return mt.Shape()

class StringerBallAssy:

  def __init__(self):

      self.l_min = 50.0
      self.l_max = 150.0
      self.thickness = 5.0
      self.width = 25.0
      self.r = 20.0
      self.groove_depth = self.thickness / 4.0
      self.groove_width = 5.0

  def buildStringer(self):
    x = 0
    y = 0

def loadBRep(filename):
  builder = BRep_Builder()
  shape = TopoDS_Shape()
  breptools_Read(shape, filename, builder)
  return shape


profile = loadBRep("inputGeom/5_segment_wire.brep")

for i in Topo(profile).wires():
  wire = i

adaptor = BRepAdaptor_CompCurve(wire)
print(adaptor.FirstParameter())
print(adaptor.LastParameter())

body         = makeEllipticalAnnularSolid(70,55,40,25,0,30)
cavityCutter = makeEllipticalAnnularSolid(65,50,45,30,5,31)
mc = BRepAlgoAPI_Cut(body,cavityCutter)
part = mc.Shape()

pieSlice = makePieSlice(100,0,pi/4.0,-1,31)

ball = makeBall(10)
stringer = makeStringerWithContinuousSlot()
trsf = gp_Trsf()
trsf.SetTranslation(gp_Vec(0,0,-75))
mt = BRepBuilderAPI_Transform(stringer,trsf)

mc = BRepAlgoAPI_Cut(ball,mt.Shape())
keyedBalls = mc.Shape()

balls = []
for i in range (5):
  #p = adaptor.Value(i+0.5)
  p = gp_Pnt()
  v = gp_Vec()
  adaptor.D1(i+0.6,p,v)
  print("magnitude:{}".format(v.Magnitude()))
  trsf = gp_Trsf()
  trsf.SetTranslation(gp_Vec(p.XYZ()))
  mt = BRepBuilderAPI_Transform(keyedBalls,trsf)
  balls.append(mt.Shape())

output = [profile]
output.extend(balls)

ms = MakeSlotShapedSolid()
ms.ax2 = gp_Ax2(gp_Pnt(0,0,150),gp_Dir(0,0,1),gp_Dir(0,1,0))
slot = ms.Solid()
output.append(slot)

#profile = loadBRep("inputGeom/circ.brep")

#writeBRep("./out.brep",[part,pieSlice,ball,stringer])
#writeBRep("./out.brep",[keyedBalls,stringer,profile])
writeBRep("./out.brep",output)
