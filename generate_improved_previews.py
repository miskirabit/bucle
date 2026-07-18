#!/usr/bin/env python3
"""
BUCLE - Generador de previews v2 FIX
Fixes del agente anterior:
- Eliminado fondo rect + 2 strokes falsos con opacity 0.75 / 0.9 (línea inferior)
- Añadido clipPath real para dientes dentro de boca
- Soporte upper + lower teeth
- Cupid bow, corner sharp, wavy, skew
- Estilos sólidos (fill only)
"""

import os, math

CX, CY = 310, 235

def clamp(v, mn, mx): return max(mn, min(mx, v))

def generate_mouth_paths(p):
    halfW = p['mouthWidth']/2
    leftX = CX - halfW
    rightX = CX + halfW
    leftY = CY + p['smile']
    rightY = CY + p['smile'] + p['skew']*0.25
    topHalf = p['mouthHeight']*p['upperCurve']*0.86
    bottomHalf = p['mouthHeight']*p['lowerCurve']*0.86
    topY = CY - topHalf
    bottomY = CY + bottomHalf
    cupid = p['cupidBow']
    peakY = topY - 2
    dipY = topY + cupid
    leftPeakX = CX - p['mouthWidth']*0.20 + p['skew']*0.05
    rightPeakX = CX + p['mouthWidth']*0.20 + p['skew']*0.08
    dipX = CX + p['skew']*0.22
    corner = p['cornerSharp']
    wavy = p['wavy']

    outer = (
        f"M {leftX:.2f} {leftY:.2f} "
        f"C {(leftX+p['mouthWidth']*0.13*(1-corner*0.5)):.2f} {(topY-p['mouthHeight']*0.08):.2f} {(leftPeakX-p['mouthWidth']*0.07):.2f} {peakY:.2f} {leftPeakX:.2f} {peakY:.2f} "
        f"C {(leftPeakX+18):.2f} {peakY:.2f} {(dipX-26):.2f} {dipY:.2f} {dipX:.2f} {dipY:.2f} "
        f"C {(dipX+26):.2f} {dipY:.2f} {(rightPeakX-18):.2f} {peakY:.2f} {rightPeakX:.2f} {peakY:.2f} "
        f"C {(rightPeakX+p['mouthWidth']*0.07):.2f} {peakY:.2f} {(rightX-p['mouthWidth']*0.13*(1-corner*0.5)):.2f} {(topY-p['mouthHeight']*0.08):.2f} {rightX:.2f} {rightY:.2f} "
        f"C {(rightX-p['mouthWidth']*0.14):.2f} {(bottomY+wavy*0.22):.2f} {(CX+p['mouthWidth']*0.22+wavy*0.45+p['skew']*0.2):.2f} {(bottomY+wavy*0.32):.2f} {(CX+wavy*0.18+p['skew']*0.12):.2f} {bottomY:.2f} "
        f"C {(CX-p['mouthWidth']*0.22+wavy*0.14-p['skew']*0.1):.2f} {(bottomY-wavy*0.18):.2f} {(leftX+p['mouthWidth']*0.14):.2f} {(bottomY-wavy*0.08):.2f} {leftX:.2f} {leftY:.2f} Z"
    )

    innerW = max(40, p['mouthWidth']-p['lipThickness']*2.2)
    innerHalf = innerW/2
    innerTopHalf = max(6, p['mouthHeight']*p['upperCurve']*0.46 - p['lipThickness']*0.18)
    innerBottomHalf = max(6, p['mouthHeight']*p['lowerCurve']*0.46 - p['lipThickness']*0.12)
    innerLeftX = CX-innerHalf
    innerRightX = CX+innerHalf
    innerLeftY = CY+p['smile']*0.35
    innerRightY = CY+p['smile']*0.35+p['skew']*0.12
    innerTopY = CY-innerTopHalf+p['smile']*0.12
    innerBottomY = CY+innerBottomHalf+p['smile']*-0.10

    minOpening = 3 if p['mouthHeight']<28 else 8
    if innerBottomY-innerTopY < minOpening:
        mid = (innerBottomY+innerTopY)/2
        innerTopY = mid-minOpening/2
        innerBottomY = mid+minOpening/2

    innerCupid = cupid*0.42
    innerPeakY = innerTopY-1
    innerDipY = innerTopY+innerCupid
    innerLeftPeakX = CX-innerW*0.20+p['skew']*0.03
    innerRightPeakX = CX+innerW*0.20+p['skew']*0.05
    innerDipX = CX+p['skew']*0.14
    innerWavy = wavy*0.45

    if p['mouthHeight']<52:
        inner = (
            f"M {innerLeftX:.2f} {((innerLeftY+innerRightY)/2):.2f} "
            f"Q {(CX-innerW*0.1):.2f} {innerTopY:.2f} {CX:.2f} {innerTopY:.2f} "
            f"Q {(CX+innerW*0.1):.2f} {innerTopY:.2f} {innerRightX:.2f} {((innerLeftY+innerRightY)/2):.2f} "
            f"Q {(CX+innerW*0.1):.2f} {innerBottomY:.2f} {CX:.2f} {innerBottomY:.2f} "
            f"Q {(CX-innerW*0.1):.2f} {innerBottomY:.2f} {innerLeftX:.2f} {((innerLeftY+innerRightY)/2):.2f} Z"
        )
    else:
        inner = (
            f"M {innerLeftX:.2f} {innerLeftY:.2f} "
            f"C {(innerLeftX+innerW*0.15):.2f} {innerTopY:.2f} {(innerLeftPeakX-innerW*0.05):.2f} {innerPeakY:.2f} {innerLeftPeakX:.2f} {innerPeakY:.2f} "
            f"C {(innerLeftPeakX+12):.2f} {innerPeakY:.2f} {(innerDipX-16):.2f} {innerDipY:.2f} {innerDipX:.2f} {innerDipY:.2f} "
            f"C {(innerDipX+16):.2f} {innerDipY:.2f} {(innerRightPeakX-12):.2f} {innerPeakY:.2f} {innerRightPeakX:.2f} {innerPeakY:.2f} "
            f"C {(innerRightPeakX+innerW*0.05):.2f} {innerPeakY:.2f} {(innerRightX-innerW*0.15):.2f} {innerTopY:.2f} {innerRightX:.2f} {innerRightY:.2f} "
            f"C {(innerRightX-innerW*0.14):.2f} {(innerBottomY+innerWavy*0.2):.2f} {(CX+innerW*0.18):.2f} {innerBottomY:.2f} {CX:.2f} {innerBottomY:.2f} "
            f"C {(CX-innerW*0.18):.2f} {innerBottomY:.2f} {(innerLeftX+innerW*0.14):.2f} {(innerBottomY+innerWavy*0.12):.2f} {innerLeftX:.2f} {innerLeftY:.2f} Z"
        )

    bounds = {'left':innerLeftX,'right':innerRightX,'top':innerTopY,'bottom':innerBottomY,
              'centerY':(innerTopY+innerBottomY)/2,'height':innerBottomY-innerTopY,'width':innerW,'cx':CX,'cy':CY}
    return outer, inner, bounds

def top_arch_y(x,b):
    t=(x-b['cx'])/(b['width']/2); ct=clamp(t,-1,1)
    cornerY=b['centerY']-b['height']*0.10
    return b['top'] + (cornerY-b['top'])*ct*ct

def bottom_arch_y(x,b):
    t=(x-b['cx'])/(b['width']/2); ct=clamp(t,-1,1)
    cornerY=b['centerY']+b['height']*0.10
    return b['bottom'] - (b['bottom']-cornerY)*ct*ct

def tooth_path(x,baseY,w,h,style,is_lower,rnd=0.5):
    r=min(7,w*0.26,abs(h)*0.28); hw=w/2
    tipY=baseY-abs(h) if is_lower else baseY+abs(h)
    tipX=x+(rnd-0.5)*w*0.08
    if style=='square':
        return f"M {x-hw:.1f} {baseY:.1f} L {x+hw:.1f} {baseY:.1f} L {x+hw:.1f} {tipY:.1f} L {x-hw:.1f} {tipY:.1f} Z"
    if style=='pointed':
        return f"M {x-hw:.1f} {baseY:.1f} L {x+hw:.1f} {baseY:.1f} L {tipX:.1f} {tipY:.1f} Z"
    if style=='fangs':
        side=hw*0.78
        return f"M {x-side:.1f} {baseY:.1f} Q {x:.1f} {(baseY+tipY)/2 + (-6 if is_lower else 6)} {tipX:.1f} {tipY:.1f} Q {x:.1f} {(baseY+tipY)/2 + (-6 if is_lower else 6)} {x+side:.1f} {baseY:.1f} Z"
    # rounded default
    return f"M {x-hw:.1f} {baseY:.1f} L {x+hw:.1f} {baseY:.1f} L {x+hw:.1f} {tipY-r:.1f} Q {x+hw:.1f} {tipY:.1f} {x+hw-r:.1f} {tipY:.1f} L {x-hw+r:.1f} {tipY:.1f} Q {x-hw:.1f} {tipY:.1f} {x-hw:.1f} {tipY-r:.1f} Z"

def gen_teeth(bounds,count,w,h,spacing,offY,style,gap,irreg,fangBoost,is_lower):
    if count<=0 or not bounds or bounds['height']<4: return []
    total=count*w+(count-1)*spacing+(gap or 0)
    start=bounds['cx']-total/2+w/2
    out=[]
    for i in range(count):
        x=start+i*(w+spacing)
        if gap>0:
            if count%2==0:
                if i>=count//2: x+=gap
            else:
                mid=count//2
                if i==mid: x+=gap/2
                elif i>mid: x+=gap
        arch = bottom_arch_y(x,bounds) if is_lower else top_arch_y(x,bounds)
        base = arch-2+offY if is_lower else arch+2+offY
        rnd=0.5+math.sin(i*1.7+count*0.4)*0.5
        finalH=h
        if fangBoost>0 and (i in (0,count-1,1,count-2)):
            is_edge=i in (0,count-1)
            finalH*=1+fangBoost*(0.9 if is_edge else 0.6)
        if irreg>0:
            finalH*=1+(rnd-0.5)*irreg*0.7
        out.append(tooth_path(x,base,w,finalH,style,is_lower,rnd))
    return out

def build_svg(p, typ='ambos'):
    outer, inner, bounds = generate_mouth_paths(p)
    upper = gen_teeth(bounds, p['upperCount'], p['upperToothWidth'], p['upperToothHeight'], p['upperSpacing'], p['upperY'], p['upperStyle'], p['upperGap'], p['upperIrregular'], p['upperFangBoost'], False)
    lower = gen_teeth(bounds, p['lowerCount'], p['lowerToothWidth'], p['lowerToothHeight'], p['lowerSpacing'], p['lowerY'], p['lowerStyle'], 0, p['upperIrregular']*0.5, 0, True) if p['showLower'] else []
    inner_svg=''
    if typ in ('boca','ambos'):
        inner_svg+=f'<path d="{outer}" fill="{p["mouthColor"]}"/>\n  <path d="{inner}" fill="{p["innerColor"]}"/>\n'
    if typ in ('dientes','ambos'):
        if typ=='ambos':
            inner_svg+=f'  <clipPath id="c"><path d="{inner}"/></clipPath>\n  <g clip-path="url(#c)">\n'
        else:
            inner_svg+='  <g>\n'
        for t in upper+lower:
            inner_svg+=f'  <path d="{t}" fill="{p["teethColor"]}"/>\n'
        inner_svg+='  </g>\n'
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<svg width="620" height="460" viewBox="0 0 620 460" xmlns="http://www.w3.org/2000/svg">\n  {inner_svg}</svg>'

if __name__=='__main__':
    os.makedirs('previews', exist_ok=True)
    defaults=dict(mouthWidth=400,mouthHeight=138,lipThickness=32,upperCurve=0.86,lowerCurve=1.08,cupidBow=14,cornerSharp=0.46,smile=2,wavy=12,skew=0,mouthColor='#ff234e',innerColor='#0b0b0c',upperCount=8,upperToothWidth=34,upperToothHeight=52,upperSpacing=6,upperY=0,upperGap=0,upperIrregular=0.06,upperFangBoost=0,upperStyle='rounded',showLower=True,lowerCount=6,lowerToothWidth=30,lowerToothHeight=36,lowerSpacing=5,lowerY=0,lowerStyle='rounded',teethColor='#ffffff')
    configs=[
        ("default", defaults),
        ("smile", {**defaults, "smile":38, "mouthWidth":460, "mouthHeight":100, "upperStyle":"pointed", "upperCount":9}),
        ("open", {**defaults, "mouthHeight":200, "mouthWidth":350, "lipThickness":22}),
        ("fangs", {**defaults, "upperCount":7, "upperStyle":"fangs", "upperFangBoost":0.85}),
        ("bat", {**defaults, "mouthWidth":480, "mouthHeight":164, "cupidBow":18, "upperCount":6, "upperToothWidth":42, "upperStyle":"bat", "lowerCount":7, "lowerStyle":"bat"}),
        ("closed", {**defaults, "mouthHeight":42, "lipThickness":36, "upperCount":6, "showLower":False}),
    ]
    for name,p in configs:
        svg=build_svg(p,'ambos')
        open(f'previews/{name}.svg','w').write(svg)
        open(f'preview-{name}.svg','w').write(svg)
        print(f'✓ {name}')
    # separate boca/dientes for default
    open('preview-boca.svg','w').write(build_svg(defaults,'boca'))
    open('preview-dientes.svg','w').write(build_svg(defaults,'dientes'))
    open('preview-default.svg','w').write(build_svg(defaults,'ambos'))
    print("done - sólidos, sin fake línea")
