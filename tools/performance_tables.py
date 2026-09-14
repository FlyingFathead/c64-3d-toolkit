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
        # Short presentation names only: keep raw method IDs and file links stable.
        for row in rows:
            for j,value in enumerate(row):
                if ']( ' in value or '](' in value:continue
                for old,new in [('hors-renderer-v4-gmod3','hors-v4-gmod3'),
                    ('hors-renderer-v3-easyflash','hors-v3'),('hors-renderer-v3','hors-v3'),
                    ('hors-render-v2','hors-v2'),('hors-render-v1','hors-v1')]:
                    value=value.replace(old,new)
                row[j]=value
        columns=[j for j,h in enumerate(header) if ('fps' in h.lower() and not any(word in h.lower() for word in ('change','preference','method')))
                 or h.lower() == 'average' or h.lower().startswith('samples/s')]
        columns=[j for j in columns if not any(word in header[j].lower().split() for word in ('high','low','peak','min','max','minimum','maximum'))]
        if header[0]=='Entry':columns=[] # inventory of different workloads, one method
        for row in rows:
            for j,value in enumerate(row):
                if number(value) is not None:
                    row[j]=value.replace('**','').replace(' (tie)','')
        if rows and columns:
            # A/B columns compare within a row. Average columns rank sustained throughput.
            # High and low rates remain unbolded interval diagnostics.
            horizontal=len(columns)>1
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
        model_names=list(dict.fromkeys(row[0] for row in rows))
        if header[0].lower()=='model' and len(model_names)>1 and all(name.startswith("Sande's") for name in model_names):
            for name in model_names:
                result+=['', '#### '+name, '', '| '+' | '.join(header[1:])+' |','| '+' | '.join(['---']*(len(header)-1))+' |']
                result+=['| '+' | '.join(row[1:])+' |' for row in rows if row[0]==name]
            result.append('')
        else:
            result+=['| '+' | '.join(header)+' |',separator]
            result+=['| '+' | '.join(row)+' |' for row in rows]
    return result
