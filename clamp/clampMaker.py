import OCC
from OCC.TopoDS import TopoDS_Compound, TopoDS_Shape
from OCC.BRep import BRep_Builder
from OCC.BRepTools import breptools_Write
from OCC.Geom import Geom_Ellipse
from math import pi, ceil, floor
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

class BallCurve:

  def __init__(self,wire):

    self.wire = wire
    self.balls = []
    self.ballParams = []
    self.adaptor = BRepAdaptor_CompCurve(self.wire)

  def transform(trsf):
    mt = BRepBuilerAPI_Transform()
    self.wire

  def insertBall(self,index,ball,paramOnCurve):

    ball.ballCurve = self
    self.balls.insert(index,ball)
    self.ballParams.insert(index,paramOnCurve)
    for i in range(len(self.balls)):
      self.balls[i].index = i

  def popBall(self,index):
    ball = self.balls.pop(index)
    param = self.ballParams.pop(index)
    for i in range(len(balls)):
      ball[i].index = i
    return (ball,param)

  def spaceBalls(self,firstBallIndex,lastBallIndex):
    # spaces the balls between firstBallIndex and lastBallIndex evenly on the curve
    # get the distance on the curve from the first ball to the last ball

    if firstBallIndex == lastBallIndex:
      raise Warning("firstBallIndex and lastBallIndex are the same!")

    u0 = self.ballParams[firstBallIndex]
    u1 = self.ballParams[lastBallIndex]

    nSegmentsToQuery = ceil(u1) - floor(u0)
    firstSegmentToQuery = floor(u0)
    d = {}
    print("segments to query: {}".format(nSegmentsToQuery))
    for i in range(nSegmentsToQuery):
      segment = firstSegmentToQuery + i
      print(segment)
      p = gp_Pnt()
      v = gp_Vec()
      self.adaptor.D1(segment+0.5,p,v)
      d[segment] = v.Magnitude()
    print(d)

    l = 0.0
    if floor(u0) != floor(u1): # u0 and u1 are in different edges
      print("different edges")
      l += (ceil(u0)-u0) * d[int(floor(u0))]
      print("l = {}".format(l))
      l += (u1 - floor(u1)) * d[int(floor(u1))]
      print("l = {}".format(l))
    else: # same edge
      l += (u1 - u0) * d[int(floor(u0))]

    if nSegmentsToQuery >= 3:
      for i in range(nSegmentsToQuery-2):
        l += d[firstSegmentToQuery+1+i]
    print("l = {}".format(l))

    nBallsToMove = lastBallIndex - firstBallIndex - 1
    deltaL = l/(nBallsToMove+1)
    print("deltaL {}".format(deltaL))

    for i in range(nBallsToMove):
      ballIndex = i + firstBallIndex + 1
      print("ballIndex {}".format(ballIndex))
      u_base = self.ballParams[ballIndex - 1]
      converged = False
      l_from_past_segments = 0.0
      while not converged:
        u = ( deltaL - l_from_past_segments ) / d[int(floor(u_base))] + u_base
        if (u - floor(u_base)) > 1.0:
          print("not converged. u_base={}  u={}".format(u_base,u))
          l_from_past_segments += d[int(floor(u_base))] * (floor(u_base+1) - u_base)
          u_base = floor(u_base + 1)
        else:
          print("converged. u_base={} u={}".format(u_base,u))
          self.ballParams[ballIndex] = u
          converged = True

  def getPnt(self,i):
    return self.adaptor.Value(self.ballParams[i])


class Ball:

  def __init__(self,r):
    self.index = None
    self.ballCurve = None
    self.r = r

  def Shape(self):
    p = self.ballCurve.getPnt(self.index)
    ax = gp_Ax2(p,gp_Dir(0,0,1),gp_Dir(0,1,0))
    ms = BRepPrimAPI_MakeSphere(ax,self.r)
    return ms.Shape()

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
#profile = loadBRep("inputGeom/circ.brep")

for i in Topo(profile).wires():
  wire = i

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

output = [profile]

ms = MakeSlotShapedSolid()
ms.ax2 = gp_Ax2(gp_Pnt(0,0,150),gp_Dir(0,0,1),gp_Dir(0,1,0))
slot = ms.Solid()
output.append(slot)


ballCurve = BallCurve(wire)
for i in range(32):
  ball = Ball(5)
  ballCurve.insertBall(i+1,ball,0.5)

ballCurve.ballParams[0] = 0.25 * 5.0 
ballCurve.ballParams[15] = 0.5 * 5.0
ballCurve.spaceBalls(0,15)

ballCurve.ballParams[16] = 0.75 * 5.0
ballCurve.ballParams[31] = 0.99 * 5.0
ballCurve.spaceBalls(16,31)

for ball in ballCurve.balls:
  output.append(ball.Shape())

writeBRep("./out.brep",output)
