#! /usr/bin/env python
'''
Generates Inkscape SVG file containing box components needed to 
laser cut a tabbed construction box taking kerf and clearance into account

Copyright (C) 2011 elliot white   elliot@twot.eu
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
__version__ = "0.8" ### please report bugs, suggestions etc to bugs@twot.eu ###

from ink_helper import *

_ = gettext.gettext

def drill(center, diameter, n_pt):
  from math import sin, cos, pi
  center = Vec2(center)
  radius = diameter / 2.
  out = Vec2([1, 0])
  up = Vec2([0, 1])
  path = Path([center + out * radius])
  dtheta = (2 * pi) / n_pt
  for i in range(n_pt + 1):
    path.append(center + out * radius * cos(i * dtheta) + up * radius * sin(i * dtheta))
  return path
  
def t_slot(center, orient, screw_diameter, nut_diameter):
  '''
  make one t-slot starting 
              __
             |  |
  -----------+  +-----+      ------
                      |        ^
  x center            |   screw_diameter  x----------------------> orient
                      |        v
  -----------+  +-----+      ------
             |  |
              --
  '''
  orient = Vec2(orient)
  out = orient / orient.norm()
  up = Vec2([out[1], -out[0]])
  center = Vec2(center)
  screw_r = screw_diameter / 2.
  nut_r = nut_diameter / 2.
  nut_w = screw_diameter
  path = Path([center + up * screw_r])
  path.append_from_last(orient)
  path.append_from_last(up * (nut_r - screw_r))
  path.append_from_last(out * (nut_w))
  path.append_from_last(-up * (nut_r - screw_r))
  path.append_from_last(out * (screw_length - thickness - orient.norm() - nut_w))
  path.append_from_last(-up * screw_r)
  path.extend(path.reflect(center, up).reverse())
  return path

def t_slots((rx,ry),(sox,soy),(eox,eoy),tabVec,length,(dirx,diry),isTab, do_holes):
  #       root startOffset endOffset tabVec length  direction  isTab

  divs=int(length/nomTab)  # divisions
  if not divs%2: divs-=1   # make divs odd
  divs=float(divs)
  tabs=(divs-1)/2          # tabs for side
  
  if equalTabs:
    gapWidth=tabWidth=length/divs
  else:
    tabWidth=nomTab
    gapWidth=(length-tabs*nomTab)/(divs-tabs)
    
  if isTab:                 # kerf correction
    gapWidth-=correction
    tabWidth+=correction
    first=correction/2
  else:
    gapWidth+=correction
    tabWidth-=correction
    first=-correction/2
    
  s=[] 
  firstVec=0; secondVec=tabVec
  dirxN=0 if dirx else 1 # used to select operation on x or y
  diryN=0 if diry else 1
  (Vx,Vy)=(rx+sox*thickness,ry+soy*thickness)
  nut_diameter = 2 * screw_diameter
  
  step = Vec2([dirx * (tabWidth + gapWidth + firstVec * 2), diry * (tabWidth + gapWidth + firstVec * 2)])
  orient = Vec2([-diry * (screw_length - thickness - screw_diameter), dirx * (screw_length - thickness - screw_diameter)])
  center = Vec2(Vx + dirx* (gapWidth + tabWidth/2.), Vy + diry* (gapWidth + tabWidth/2.)) + (orient / orient.norm()) * thickness
  slot = t_slot(center, orient, screw_diameter, nut_diameter)
  hole = drill(center - (orient / orient.norm()) * (thickness * 1.5 + spacing), 
               screw_diameter, 360)
  
  slots = []
  holes = []
  for i in range(0,(int(divs)) / 2, 1):
    slots.append(slot.translate(step * i))
    if do_holes:
      holes.append(hole.translate(step * i))
      holes.append(hole.translate(step * i - orient / orient.norm() * (Z - thickness) ))

  out = [s.drawXY() for s in slots]
  out.extend([h.drawXY() for h in holes])
  return out
  
def side((rx,ry),(sox,soy),(eox,eoy),tabVec,length,(dirx,diry),isTab):
  #       root startOffset endOffset tabVec length  direction  isTab

  divs=int(length/nomTab)  # divisions
  if not divs%2: divs-=1   # make divs odd
  divs=float(divs)
  tabs=(divs-1)/2          # tabs for side
  
  if equalTabs:
    gapWidth=tabWidth=length/divs
  else:
    tabWidth=nomTab
    gapWidth=(length-tabs*nomTab)/(divs-tabs)
    
  if isTab:                 # kerf correction
    gapWidth-=correction
    tabWidth+=correction
    first=correction/2
  else:
    gapWidth+=correction
    tabWidth-=correction
    first=-correction/2
    
  firstVec=0; secondVec=tabVec
  dirxN=0 if dirx else 1 # used to select operation on x or y
  diryN=0 if diry else 1
  (Vx,Vy)=(rx+sox*thickness,ry+soy*thickness)
  s='M '+str(Vx)+','+str(Vy)+' '

  if dirxN: Vy=ry # set correct line start
  if diryN: Vx=rx

  # generate line as tab or hole using:
  #   last co-ord:Vx,Vy ; tab dir:tabVec  ; direction:dirx,diry ; thickness:thickness
  #   divisions:divs ; gap width:gapWidth ; tab width:tabWidth

  for n in range(1,int(divs)):
    if n%2:
      Vx=Vx+dirx*gapWidth+dirxN*firstVec+first*dirx
      Vy=Vy+diry*gapWidth+diryN*firstVec+first*diry
      s+='L '+str(Vx)+','+str(Vy)+' '
      Vx=Vx+dirxN*secondVec
      Vy=Vy+diryN*secondVec
      s+='L '+str(Vx)+','+str(Vy)+' '
    else:
      Vx=Vx+dirx*tabWidth+dirxN*firstVec
      Vy=Vy+diry*tabWidth+diryN*firstVec
      s+='L '+str(Vx)+','+str(Vy)+' '
      Vx=Vx+dirxN*secondVec
      Vy=Vy+diryN*secondVec
      s+='L '+str(Vx)+','+str(Vy)+' '

    (secondVec,firstVec)=(-secondVec,-firstVec) # swap tab direction
    first=0
  s+='L '+str(rx+eox*thickness+dirx*length)+','+str(ry+eoy*thickness+diry*length)+' '
  return s

  
class TSlotBoxMaker(inkex.Effect):
  def __init__(self):
      # Call the base class constructor.
      inkex.Effect.__init__(self)
      # Define options
      self.OptionParser.add_option('--unit',action='store',type='string',
        dest='unit',default='mm',help='Measure Units')
      self.OptionParser.add_option('--inside',action='store',type='int',
        dest='inside',default=0,help='Int/Ext Dimension')
      self.OptionParser.add_option('--length',action='store',type='float',
        dest='length',default=100,help='Length of Box')
      self.OptionParser.add_option('--width',action='store',type='float',
        dest='width',default=100,help='Width of Box')
      self.OptionParser.add_option('--depth',action='store',type='float',
        dest='height',default=100,help='Height of Box')
      self.OptionParser.add_option('--tab',action='store',type='float',
        dest='tab',default=25,help='Nominal Tab Width')
      self.OptionParser.add_option('--equal',action='store',type='int',
        dest='equal',default=0,help='Equal/Prop Tabs')
      self.OptionParser.add_option('--thickness',action='store',type='float',
        dest='thickness',default=10,help='Thickness of Material')
      self.OptionParser.add_option('--kerf',action='store',type='float',
        dest='kerf',default=0.5,help='Kerf (width) of cut')
      self.OptionParser.add_option('--clearance',action='store',type='float',
        dest='clearance',default=0.01,help='Clearance of joints')
      self.OptionParser.add_option('--style',action='store',type='int',
        dest='style',default=25,help='Layout/Style')
      self.OptionParser.add_option('--spacing',action='store',type='float',
        dest='spacing',default=25,help='Part Spacing')
      self.OptionParser.add_option('--screw_length',action='store',type='float',
        dest='screw_length',default=25,help='Screw Length')
      self.OptionParser.add_option('--screw_diameter',action='store',type='float',
        dest='screw_diameter',default=25,help='Screw Diameter')
      
  def effect(self):
    global parent,nomTab,equalTabs,thickness,correction, screw_length, screw_diameter, spacing, Z
    
        # Get access to main SVG document element and get its dimensions.
    svg = self.document.getroot()
    
        # Get the attibutes:
    widthDoc  = inkex.unittouu(svg.get('width'))
    heightDoc = inkex.unittouu(svg.get('height'))

        # Create a new layer.
    layer = inkex.etree.SubElement(svg, 'g')
    layer.set(inkex.addNS('label', 'inkscape'), 'newlayer')
    layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
    
    parent=self.current_layer
    
        # Get script's option values.
    unit=self.options.unit
    inside=self.options.inside
    X = inkex.unittouu( str(self.options.length)  + unit )
    Y = inkex.unittouu( str(self.options.width) + unit )
    Z = inkex.unittouu( str(self.options.height)  + unit )
    thickness = inkex.unittouu( str(self.options.thickness)  + unit )
    nomTab = inkex.unittouu( str(self.options.tab) + unit )
    equalTabs=self.options.equal
    kerf = inkex.unittouu( str(self.options.kerf)  + unit )
    clearance = inkex.unittouu( str(self.options.clearance)  + unit )
    layout=self.options.style
    spacing = inkex.unittouu( str(self.options.spacing)  + unit )
    screw_length = inkex.unittouu( str(self.options.screw_length)  + unit )
    screw_diameter = inkex.unittouu( str(self.options.screw_diameter)  + unit )

    if inside: # if inside dimension selected correct values to outside dimension
      X+=thickness*2
      Y+=thickness*2
      Z+=thickness*2

    correction=kerf-clearance

    # check input values mainly to avoid python errors
    # TODO restrict values to *correct* solutions
    error=0
    
    if min(X,Y,Z)==0:
      inkex.errormsg(_('Error: Dimensions must be non zero'))
      error=1
    if max(X,Y,Z)>max(widthDoc,heightDoc)*10: # crude test
      inkex.errormsg(_('Error: Dimensions Too Large'))
      error=1
    if min(X,Y,Z)<3*nomTab:
      inkex.errormsg(_('Error: Tab size too large'))
      error=1
    if nomTab<thickness:
      inkex.errormsg(_('Error: Tab size too small'))
      error=1	  
    if thickness==0:
      inkex.errormsg(_('Error: Thickness is zero'))
      error=1	  
    if thickness>min(X,Y,Z)/3: # crude test
      inkex.errormsg(_('Error: Material too thick'))
      error=1	  
    if correction>min(X,Y,Z)/3: # crude test
      inkex.errormsg(_('Error: Kerf/Clearence too large'))
      error=1	  
    if spacing>max(X,Y,Z)*10: # crude test
      inkex.errormsg(_('Error: Spacing too large'))
      error=1	  
    if spacing<kerf:
      inkex.errormsg(_('Error: Spacing too small'))
      error=1	  

    if error: exit()
   
    # layout format:(rootx),(rooty),Xlength,Ylength,tabInfo
    # root= (spacing,X,Y,Z) * values in tuple
    # tabInfo= <abcd> 0=holes 1=tabs
    if   layout==1: # Diagramatic Layout
      pieces=[[(2,0,0,1),(3,0,1,1),X,Z,0b1010, False, False],
              [(1,0,0,0),(2,0,0,1),Z,Y,0b1111, False, False],
              [(2,0,0,1),(2,0,0,1),X,Y,0b0000,  True,  True],
              [(3,1,0,1),(2,0,0,1),Z,Y,0b1111, False, False],
              [(4,1,0,2),(2,0,0,1),X,Y,0b0000,  True, False],
              [(2,0,0,1),(1,0,0,0),X,Z,0b1010, False, False]]
    elif layout==2: # 3 Piece Layout
      pieces=[[(2,0,0,1),(2,0,1,0),X,Z,0b1010, False, False],
              [(1,0,0,0),(1,0,0,0),Z,Y,0b1111, False, False],
              [(2,0,0,1),(1,0,0,0),X,Y,0b0000,  True, False]]
    elif layout==3: # Inline(compact) Layout
      pieces=[[(1,0,0,0),(1,0,0,0),X,Y,0b0000, False, False],
              [(2,1,0,0),(1,0,0,0),X,Y,0b0000, False, False],
              [(3,2,0,0),(1,0,0,0),Z,Y,0b0101,  True,  True],
              [(4,2,0,1),(1,0,0,0),Z,Y,0b0101, False, False],
              [(5,2,0,2),(1,0,0,0),X,Z,0b1111,  True, False],
              [(6,3,0,2),(1,0,0,0),X,Z,0b1111, False, False]]
    elif layout==4: # Diagramatic Layout with Alternate Tab Arrangement
      pieces=[[(2,0,0,1),(3,0,1,1),X,Z,0b1001, False, False],
              [(1,0,0,0),(2,0,0,1),Z,Y,0b1100, False, False],
              [(2,0,0,1),(2,0,0,1),X,Y,0b1100,  True, False],
              [(3,1,0,1),(2,0,0,1),Z,Y,0b0110, False,  True],
              [(4,1,0,2),(2,0,0,1),X,Y,0b0110,  True, False],
              [(2,0,0,1),(1,0,0,0),X,Z,0b1100, False, False]]

    for piece in pieces: # generate and draw each piece of the box
      (xs,xx,xy,xz)=piece[0]
      (ys,yx,yy,yz)=piece[1]
      x=xs*spacing+xx*X+xy*Y+xz*Z  # root x co-ord for piece
      y=ys*spacing+yx*X+yy*Y+yz*Z  # root y co-ord for piece
      dx=piece[2]
      dy=piece[3]
      tabs=piece[4]
      slots = piece[5]
      holes = piece[6]
      a=tabs>>3&1; b=tabs>>2&1; c=tabs>>1&1; d=tabs&1 # extract tab status for each side
      # generate and draw the sides of each piece
      drawS(side((x,y),(d,a),(-b,a),-thickness if a else thickness,dx,(1,0),a), parent)          # side a
      drawS(side((x+dx,y),(-b,a),(-b,-c),thickness if b else -thickness,dy,(0,1),b), parent)     # side b
      drawS(side((x+dx,y+dy),(-b,-c),(d,-c),thickness if c else -thickness,dx,(-1,0),c), parent) # side c
      drawS(side((x,y+dy),(d,-c),(d,a),-thickness if d else thickness,dy,(0,-1),d), parent)      # side d
      
    # side((rx,ry),(sox,soy),(eox,eoy),tabVec,length,(dirx,diry),isTab):
    #       root startOffset endOffset tabVec length  direction  isTab

      if slots:
        [drawS(slot, parent) for slot in t_slots((x,y),(d,a),(-b,a),-thickness if a else thickness,dx,(1,0),a, holes)]          # slot a
        [drawS(slot, parent) for slot in t_slots((x+dx,y),(-b,a),(-b,-c), thickness if b else -thickness,dy,(0,1),b, holes)]    # slot b
        [drawS(slot, parent) for slot in t_slots((x+dx,y+dy),(-b,-c),(d,-c),thickness if c else -thickness,dx,(-1,0),c, holes)] # slot c
        [drawS(slot, parent) for slot in t_slots((x,y+dy),(d,-c),(d,a),-thickness if d else thickness,dy,(0,-1),d, holes)]      # slot d

# Create effect instance and apply it.
effect = TSlotBoxMaker()
effect.affect()
