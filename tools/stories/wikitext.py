"""Wikipedia article HTML -> plain text close to the API's explaintext extract (what the bot checks against)."""
import re, sys, html as H
from html.parser import HTMLParser

class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.out=[]; s.skip=0; s.stack=[]; s.cur=None; s.buf=[]
    def handle_starttag(s, tag, a):
        a=dict(a); cls=a.get('class','') or ''
        if s.skip:
            if tag in VOID: return
            s.skip+=1; return
        if tag in ('table','style','script','sup','figure','math') or any(c in cls for c in ('reference','mw-editsection','navbox','reflist','hatnote','thumb','infobox','metadata','mw-empty-elt','noprint','shortdescription','sidebar','toc')) or a.get('role')=='note':
            if tag not in VOID: s.skip=1
            return
        if tag in ('p','li','h2','h3','h4','dd','blockquote'):
            s.cur=tag; s.buf=[]
    def handle_endtag(s, tag):
        if s.skip:
            s.skip-=1; return
        if tag==s.cur:
            t=re.sub(r'\s+',' ',''.join(s.buf)).strip()
            if t:
                if tag in ('h2','h3','h4'):
                    n={'h2':2,'h3':3,'h4':4}[tag]; s.out.append('\n'+'='*n+' '+t+' '+'='*n)
                else: s.out.append(t)
            s.cur=None
    def handle_data(s, d):
        if not s.skip and s.cur: s.buf.append(d)
VOID={'br','img','hr','meta','link','input','wbr','col','area','source'}

def text(path):
    h=open(path,encoding='utf-8').read()
    i=h.find('id="mw-content-text"'); h=h[i:] if i>0 else h
    p=P(); p.feed(h)
    t='\n'.join(p.out)
    return re.split(r"\n==\s*(?:See also|References|Notes|Further reading|External links|Bibliography|Citations|Sources)\s*==", t)[0]

if __name__=='__main__':
    t=text(sys.argv[1]); print(len(t)); 
