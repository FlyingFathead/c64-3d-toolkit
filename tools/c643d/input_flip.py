"""Host-only, pixel-exact artwork reflections; overlay/effect data is untouched."""
from dataclasses import replace


def options(args):
    return dict(flip_horizontal=bool(getattr(args,'flip_input_horizontal',False)),
                flip_vertical=bool(getattr(args,'flip_input_vertical',False)))


def _runs(values, stride=1, limit=255):
    """Compress sorted offset/value cells into existing span records."""
    result=[];items=sorted(values.items());i=0
    while i<len(items):
        start,value=items[i];count=1;i+=1
        while i<len(items) and items[i]==(start+count*stride,value) and count<limit:
            count+=1;i+=1
        result.append((start&255,start>>8,count,value))
    return result


def frame(frame, *, width=256, height=192, flip_horizontal=False, flip_vertical=False):
    """Reflect native vector records and colour/clear cells inside the viewport.

    Reflect exact decoded pixels instead of re-rasterizing endpoints, preserving
    DDA tie decisions. Called before optimization/selective-byte-clear planning.
    """
    if not flip_horizontal and not flip_vertical:return frame
    if width%8 or height%8 or not 8<=width<=320 or not 8<=height<=200:
        raise ValueError('Flip viewport must use 8-pixel cells within 320x200')
    from .pipeline import decode_record_points, make_step_chunks
    records=[]
    for rec in frame.records:
        points=[(width-1-x if flip_horizontal else x,height-1-y if flip_vertical else y)
                for x,y in decode_record_points(rec)]
        axis=(rec[3]>>6)&1
        if (flip_horizontal and axis==0) or (flip_vertical and axis==1):points.reverse()
        x,y=points[0];minor=1-axis
        negative=points[-1][minor]<points[0][minor]
        offset=(y//8)*320+(x//8)*8
        control=(x&7)|((y&7)<<3)|(axis<<6)|(int(negative)<<7)
        records.append((offset&255,offset>>8,len(points),control,
                        *make_step_chunks(dict(points=points,axis=axis),0,len(points)-1)))
    def cell(index):
        y,x=divmod(index,40)
        if x<width//8 and y<height//8:
            if flip_horizontal:x=width//8-1-x
            if flip_vertical:y=height//8-1-y
        return y*40+x
    clear={}
    for lo,hi,count in frame.clear_spans:
        start=(lo|(hi<<8))//8
        for i in range(start,start+count):clear[cell(i)*8]=0
    # Do not let clear records cross a physical character row.
    clears=[]
    for y in range(height//8):
        row={k:v for k,v in clear.items() if k//320==y}
        clears.extend((lo,hi,count) for lo,hi,count,_ in _runs(row,8,32))
    colors={}
    for lo,hi,count,value in frame.color_spans:
        start=lo|(hi<<8)
        for i in range(start,start+count):colors[cell(i)]=value
    return replace(frame,records=records,clear_spans=clears,color_spans=_runs(colors))


def surface(bits, screen, *, width=256, flip_horizontal=False, flip_vertical=False):
    """Reflect already quantized pixels/colours, preserving the right HUD area."""
    if not flip_horizontal and not flip_vertical:return bits,screen
    bits=bits.copy();screen=screen.copy()
    if flip_horizontal:
        bits[:,:width]=bits[:,:width][:,::-1]
        screen[:,:width//8]=screen[:,:width//8][:,::-1]
    if flip_vertical:
        bits[:,:width]=bits[:,:width][::-1,:]
        screen[:,:width//8]=screen[:,:width//8][::-1,:]
    return bits,screen


def bounds(box, *, width=256, height=192, flip_horizontal=False, flip_vertical=False):
    if box is None:return None
    x0,x1,y0,y1=box
    if flip_horizontal:x0,x1=width-1-x1,width-1-x0
    if flip_vertical:y0,y1=height-1-y1,height-1-y0
    return [x0,x1,y0,y1]
