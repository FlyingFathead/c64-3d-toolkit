"""Consistent FPS maxima in generated Markdown, grouped by comparable workload."""
import re


def highlight_fps(lines):
    result=[];i=0
    def cells(line):return [v.strip() for v in line.strip().strip('|').split('|')]
    def number(text):
        clean=text.replace('**','').replace(' (tie)','').replace(',','')
        return float(clean) if re.fullmatch(r'[-+]?\d+(?:\.\d+)?',clean) else None
    while i<len(lines):
        if not (lines[i].startswith('|') and i+1<len(lines) and re.fullmatch(r'[| :\-]+',lines[i+1])):
            result.append(lines[i]);i+=1;continue
        header=cells(lines[i]);separator=lines[i+1];i+=2;rows=[]
        while i<len(lines) and lines[i].startswith('|'):
            rows.append(cells(lines[i]));i+=1
        columns=[j for j,h in enumerate(header) if ('fps' in h.lower() and not any(word in h.lower() for word in ('change','preference','method')))
                 or h.lower() in ('high','average','low') or h.lower().startswith('samples/s')]
        if rows and columns:
            extrema=any(any(word in header[j].lower() for word in ('high','low','average')) for j in columns)
            # A/B columns compare within a row. High/average/low columns
            # represent different statistics and are ranked independently.
            horizontal=len(columns)>1 and not extrema
            if horizontal:
                groups=[[(r,c) for c in columns] for r in range(len(rows))]
            else:
                workload=header[0].lower() in ('model','scene','animation')
                names=list(dict.fromkeys(row[0] if workload else '' for row in rows))
                groups=[[(r,c) for r,row in enumerate(rows) if (row[0] if workload else '')==name]
                        for name in names for c in columns]
            for group in groups:
                values=[(r,c,number(rows[r][c])) for r,c in group if c<len(rows[r])]
                valid=[v for r,c,v in values if v is not None]
                if not valid:continue
                best=max(valid);ties=sum(v==best for v in valid)>1
                for r,c,v in values:
                    if v is None:continue
                    text=rows[r][c].replace('**','').replace(' (tie)','')
                    rows[r][c]='**'+text+(' (tie)' if ties else '')+'**' if v==best else text
        result+=['| '+' | '.join(header)+' |',separator]
        result+=['| '+' | '.join(row)+' |' for row in rows]
    return result
