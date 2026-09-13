#!/usr/bin/env python3
"""Extract the supplied SAKU 2026 vector paths; PyMuPDF is needed only here."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent


def main():
    import fitz
    source = HERE / 'source/Saku_2026_logo.pdf'
    with fitz.open(source) as doc:
        page = doc[0]
        tree = ET.fromstring(page.get_svg_image(text_as_path=True))
        ns = '{http://www.w3.org/2000/svg}'
        href = '{http://www.w3.org/1999/xlink}href'
        ids = {node.get('id'): node for node in tree.iter() if node.get('id')}
        # The four logo letter outlines, kept separate from the page artwork.
        letters = [node for node in tree.iter(ns+'path')
                   if node.get('transform', '').startswith('matrix(1,0,0,-1,')
                   and node.get('d', '').startswith('M0 0')]
        # Some letters begin at another local point. The PDF drawing records
        # identify the four contiguous glyph paths; locate their parent group.
        groups = [node for node in tree.iter(ns+'g') if len(node.findall(ns+'path')) == 4]
        if len(groups) != 1:
            raise ValueError('The source PDF logo structure changed')
        letters = groups[0].findall(ns+'path')
        uses = [node for node in tree.iter(ns+'use') if node.get('data-text')]
        if ''.join(node.get('data-text') for node in uses) != '2026':
            raise ValueError('The source year changed')
        crop = fitz.Rect(199.4211, 18.6317, 406.4158, 55.7758)
        svg = ET.Element(ns+'svg', {'version':'1.1', 'width':f'{crop.width:.4f}',
            'height':f'{crop.height:.4f}', 'viewBox':f'{crop.x0:.4f} {crop.y0:.4f} {crop.width:.4f} {crop.height:.4f}'})
        ET.SubElement(svg, ns+'title').text = 'SAKU 2026'
        ET.SubElement(svg, ns+'desc').text = 'Suomen Amiga-käyttäjät ry (Saku). Vector logo extracted from the supplied 2026 PDF; transparent background.'
        for node in letters:
            copy = deepcopy(node)
            copy.set('fill', '#000000')
            svg.append(copy)
        for use in uses:
            node = deepcopy(ids[use.get(href).lstrip('#')])
            node.attrib.pop('id', None)
            node.set('transform', use.get('transform'))
            node.set('fill', use.get('fill'))
            svg.append(node)
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    target = HERE / 'saku_2026.svg'
    ET.ElementTree(svg).write(target, encoding='utf-8', xml_declaration=True)
    outlined=deepcopy(svg)
    outlined.find(ns+'title').text='SAKU 2026 — white outline variant'
    outlined.find(ns+'desc').text='Derived from the supplied SAKU 2026 PDF. Original black SAKU paths with white strokes; red year unchanged; transparent background.'
    for node in outlined.findall(ns+'path')[:4]:
        node.set('stroke','#ffffff')
        node.set('stroke-width','1.2')
        node.set('stroke-linejoin','round')
        node.set('stroke-linecap','round')
        # The PDF uses implicit fill closure. Explicit Z also closes the stroke.
        if not node.get('d','').rstrip().lower().endswith('z'):
            node.set('d',node.get('d')+'Z')
    # Original crop already has a half-point margin; allow the 0.6-point
    # outside half of the stroke plus a little transparent breathing room.
    outlined.set('viewBox',f'{crop.x0-0.75:.4f} {crop.y0-0.75:.4f} {crop.width+1.5:.4f} {crop.height+1.5:.4f}')
    outlined.set('width',f'{crop.width+1.5:.4f}');outlined.set('height',f'{crop.height+1.5:.4f}')
    variant=HERE/'saku_2026-white-outline.svg'
    ET.ElementTree(outlined).write(variant,encoding='utf-8',xml_declaration=True)
    white=deepcopy(svg)
    white.find(ns+'title').text='SAKU 2026 — white background reference'
    white.find(ns+'desc').text='Original SAKU 2026 vectors with an explicit white canvas rectangle, for reference and rotating-card presentations.'
    white.insert(2,ET.Element(ns+'rect',{'x':f'{crop.x0:.4f}','y':f'{crop.y0:.4f}',
        'width':f'{crop.width:.4f}','height':f'{crop.height:.4f}','fill':'#ffffff'}))
    white_target=HERE/'saku_2026-white-background.svg'
    ET.ElementTree(white).write(white_target,encoding='utf-8',xml_declaration=True)
    card=deepcopy(white)
    card.find(ns+'title').text='SAKU 2026 — padded rounded white card'
    card.find(ns+'desc').text='Original logo colours on a white card with 8-point horizontal and 6-point vertical padding, and 5-point rounded corners.'
    card_box=(crop.x0-8,crop.y0-6,crop.width+16,crop.height+12)
    card.set('viewBox',' '.join(f'{v:.4f}' for v in card_box))
    card.set('width',f'{card_box[2]:.4f}');card.set('height',f'{card_box[3]:.4f}')
    rect=card.find(ns+'rect')
    for name,value in zip(('x','y','width','height'),card_box):rect.set(name,f'{value:.4f}')
    rect.set('rx','5');rect.set('ry','5')
    card_target=HERE/'saku_2026-rounded-card.svg'
    ET.ElementTree(card).write(card_target,encoding='utf-8',xml_declaration=True)
    report = dict(source_pdf='source/Saku_2026_logo.pdf',
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), page=1,
        crop_points=list(crop), output=target.name,
        svg_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        vector_paths=8, raster_images=0, font_dependencies=0,
        colours=['#000000', '#fe0000'], background='transparent; page artwork omitted',
        credit='Suomen Amiga-käyttäjät ry (Saku); supplied for this example')
    report['variants']=[dict(output=variant.name,sha256=hashlib.sha256(variant.read_bytes()).hexdigest(),
        modification='White 1.2-point rounded stroke on the four original black letter paths; original red year retained',
        traced_from_raster=False,background='transparent')]
    report['variants'].append(dict(output=white_target.name,sha256=hashlib.sha256(white_target.read_bytes()).hexdigest(),
        modification='Explicit white canvas rectangle behind the original eight logo/year paths',background='#ffffff'))
    report['variants'].append(dict(output=card_target.name,sha256=hashlib.sha256(card_target.read_bytes()).hexdigest(),
        modification='Padded rounded white card for Shift+B; original rectangular reference retained',background='#ffffff',
        padding_points=[8,6],corner_radius_points=5))
    (HERE/'source/provenance.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Extracted eight original vector paths, including outlined year glyphs.')


if __name__ == '__main__':
    main()
