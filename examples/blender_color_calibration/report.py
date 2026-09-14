"""Generate a numeric and visual calibration from the real palette mapper."""
from pathlib import Path
import hashlib
import json
import sys
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from tools.c643d.colors import nearest_c64_color_index, c64_color_name


def main():
    palettes = json.loads((HERE/'palettes.json').read_text())
    reference = palettes[0]['rgb']
    rows = []
    for palette in palettes:
        for index, rgb in enumerate(palette['rgb']):
            mapped = nearest_c64_color_index(rgb)
            rows.append(dict(palette=palette['name'], expected_index=index, source_rgb=rgb,
                             mapped_index=mapped, mapped_name=c64_color_name(mapped), matches=mapped==index))
    assert all(r['matches'] for r in rows if r['palette']=='toolkit')
    result = dict(mapper_sha256=hashlib.sha256((ROOT/'tools/c643d/colors.py').read_bytes()).hexdigest(),
                  rows=rows, note='Cross-palette nearest-RGB mapping is not palette-index preservation.')
    (HERE/'mapping-results.json').write_text(json.dumps(result, indent=2)+'\n')
    lines=['# Calibration mapping results','','RGB swatches use the exact values in `palettes.json`; names are native VIC-II indices.','','| Source palette | Intended index/name | Source RGB | Nearest mapped index/name | Same index |','| --- | --- | --- | --- | --- |']
    for r in rows:
        lines.append(f'| {r["palette"]} | {r["expected_index"]}: {c64_color_name(r["expected_index"])} | {r["source_rgb"]} | {r["mapped_index"]}: {r["mapped_name"]} | {"yes" if r["matches"] else "no"} |')
    (HERE/'MAPPING_RESULTS.md').write_text('\n'.join(lines)+'\n')
    image=Image.new('RGB',(1370,540),'#171b25');draw=ImageDraw.Draw(image)
    font=ImageFont.load_default(size=17);small=ImageFont.load_default(size=13)
    draw.text((20,15),'C64 palette calibration: source swatch above / mapped toolkit swatch below',font=font,fill='white')
    for y,palette in enumerate(palettes):
        top=60+y*150;draw.text((20,top),palette['name'],font=font,fill='white')
        for index,rgb in enumerate(palette['rgb']):
            x=190+index*72; mapped=nearest_c64_color_index(rgb)
            draw.rectangle((x,top,x+64,top+44),fill=tuple(rgb),outline='#555555')
            draw.rectangle((x,top+48,x+64,top+92),fill=tuple(reference[mapped]),outline='#555555')
            draw.text((x,top+99),f'{index} -> {mapped}',font=small,fill='#99e0b0' if mapped==index else '#ffbb77')
    draw.text((20,510),'Exact native indices: set material["c643d_color"] = 0..15 in Blender. This bypasses RGB ambiguity.',font=small,fill='white')
    image.save(HERE/'color-calibration.png')
    print('Reference palette: 16/16 exact. Cross-palette results:',[(p['name'],sum(r['matches'] for r in rows if r['palette']==p['name'])) for p in palettes])


if __name__=='__main__': main()
