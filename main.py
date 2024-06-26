from fastapi import FastAPI,Form,Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import re
import os
import httpx
import html
class StudentInfo(BaseModel):
    stnum: str
    name: str
    grade: int
    ph: str
    notes: Optional[str]

    @classmethod
    def as_form(cls, stnum: str = Form(...), name: str = Form(...), grade: int = Form(...), ph: str = Form(...), notes: Optional[str] = Form(None)):
        return cls(stnum=stnum, name=name, grade=grade, ph=ph, notes=notes)
pattern='^2(3|4)5(5|7)\d{3}$'
sheet=os.getenv('KGCmember')
programe=os.getenv('KGCPrograme')
templates = Jinja2Templates(directory="template")

app=FastAPI()
app.mount("/mount", StaticFiles(directory="mount"))
@app.get("/")
def index():
    return FileResponse('index.html')
@app.get("/insertform")
def insertform():
    return FileResponse('insert.html')
@app.get("/insert")
def getinsert(request: Request):
    return templates.TemplateResponse('warning.html',{'request':request,'msg':'정보를 입력해주세요'})
@app.post("/insert")
async def insert(request: Request,student : StudentInfo=Depends(StudentInfo.as_form)):
    if not student.notes:
        student.notes=""
    form = {'mode': 'insert', 'stnum': student.stnum, "name": student.name, "grade": student.grade, "ph": student.ph, "notes": student.notes}
    if not re.match(pattern,student.stnum):
        return templates.TemplateResponse('warning.html',{'request':request,'msg':'빅데이터과나 영상미디어콘텐츠과만 가입이 가능합니다'})
    df=pd.read_excel(sheet)
    df=df[(df['학번']==student.stnum)|(df['연락처']==student.ph)]
    if len(df)>0:
        return templates.TemplateResponse('warning.html',{'request':request,'msg':'이미 가입되었습니다'})
    try:   
        async with httpx.AsyncClient() as client:
            response = await client.post(programe, data=form, follow_redirects=True)
            response.raise_for_status()
            msg = response.text
            msg = html.unescape(msg)
            path="success.html"
    except httpx.RequestError as e:
        msg = f'{e}'
        path="warning.html"
    except httpx.HTTPStatusError as e:
        msg = f'HTTP 오류 발생: {e.response.status_code} {html.unescape(e.response.text)}'
        path="warning.html"
    return templates.TemplateResponse(path, {'request': request, 'msg': msg,'insert':True})
@app.get("/deleteform")
def delete():
    return FileResponse('delete.html')
@app.get("/delete")
def getinsert(request: Request):
    return templates.TemplateResponse('warning.html',{'request':request,'msg':'정보를 입력해주세요'})
@app.post("/delete")
async def delete(request: Request,stnum:str=Form(...)):
    df=pd.read_excel(sheet)
    df=df[(df['학번']==int(stnum))]
    if len(df)==0:
        return templates.TemplateResponse('warning.html',{'request':request,'msg':'해당 학번이 존재하지 않습니다'})
    if 2355009 in df['학번'].values:
        return templates.TemplateResponse('warning.html',{'request':request,'msg':'대표학생은 삭제할수 없습니다'})
    if 2357040 in df['학번'].values:
        return templates.TemplateResponse('warning.html',{'request':request,'msg':'부대표학생은 삭제할수 없습니다'})
    form = {'mode': 'delete', 'stnum': stnum}
    try:   
        async with httpx.AsyncClient() as client:
            response = await client.post(programe, data=form, follow_redirects=True)
            response.raise_for_status()
            msg = response.text
            msg = html.unescape(msg)
            path="success.html"
    except httpx.RequestError as e:
        msg = f'Google Sheets에 데이터 추가 중 오류 발생: {e}'
        path="warning.html"
    except httpx.HTTPStatusError as e:
        msg = f'HTTP 오류 발생: {e.response.status_code} {html.unescape(e.response.text)}'
        path="warning.html"
    return templates.TemplateResponse(path, {'request': request, 'msg': msg,'insert':False})
@app.get("/updateform")
def update():
    return FileResponse('update.html')
@app.post("/updateinput")
async def updateinput(request: Request,stnum:str=Form(...)):
    stnum=int(stnum)
    df=pd.read_excel(sheet)
    df=df[df['학번']==stnum]
    df.fillna("",inplace=True)
    if 2355009 in df['학번'].values:
        return templates.TemplateResponse('warning.html',{'request':request,'msg':'대표학생의 정보는 수정할수 없습니다'})
    if 2357040 in df['학번'].values:
        return templates.TemplateResponse('warning.html',{'request':request,'msg':'부대표학생의 정보는 수정할수 없습니다'})
    if len(df)<1:
        return templates.TemplateResponse('warning.html',{'request':request,'msg':'해당 학번이 존재하지 않습니다'})
    df.set_index('학번',inplace=True)
    return templates.TemplateResponse('updateform.html',{'request':request,'stnum':stnum,'grade':df['학년'][stnum],'ph':df['연락처'][stnum],'name':df['성명'][stnum],'notes':df['비고'][stnum] })
@app.get("/update")
def getinsert(request: Request):
    return templates.TemplateResponse('warning.html',{'request':request,'msg':'정보를 입력해주세요'})
@app.post("/update")
async def update(request: Request,student : StudentInfo=Depends(StudentInfo.as_form)):
    form = {'mode': 'update', 'stnum': student.stnum, "name": student.name, "grade": student.grade, "ph": student.ph, "notes": student.notes}
    path=""
    try:   
        async with httpx.AsyncClient() as client:
            response = await client.post(programe, data=form, follow_redirects=True)
            response.raise_for_status()
            msg = response.text
            msg = html.unescape(msg)
            path="success.html"
    except httpx.RequestError as e:
        msg = f'Google Sheets에 데이터 추가 중 오류 발생: {e}'
        path="warning.html"
    except httpx.HTTPStatusError as e:
        msg = f'HTTP 오류 발생: {e.response.status_code} {html.unescape(e.response.text)}'
        path="warning.html"
    return templates.TemplateResponse(path,{'request':request,'msg':msg,'insert':False})
@app.get("/admincheck")
def admincheck():
    return FileResponse('admincheck.html')
@app.get("/admin")
def admin(request: Request):
    return templates.TemplateResponse('warning.html',{'request':request,'msg':'암호를 입력헤주세요'})
@app.post("/admin")
def admin(request: Request,pw:str=Form(...)):
    df=pd.read_excel(sheet)
    dept={
    55:'빅데이터과',
    57:'영상미디어콘텐츠과'
    }
    df['학과']=df['학번'].apply(lambda x:dept[x%100000//1000])
    df['비고'] = df.apply(lambda row: ", ".join(filter(None, [str(row['역할']).strip() if pd.notna(row['역할']) else None,
        str(row['비고']).strip() if pd.notna(row['비고']) else None])), axis=1)
    df=df[['학과']+'학번	학년	성명	연락처	비고'.split()]
    df.reset_index(inplace=True)
    df.rename(columns={'index':'연번'},inplace=True)
    df['연번']=df['연번'].apply(lambda x:x+1)
    return templates.TemplateResponse('member.html',{'request':request,'table':df.to_html(index=False).replace("th","td").replace('class="dataframe"',"align='center'").replace('NaN',"")}) if pw==os.getenv("pw") else templates.TemplateResponse('warning.html',{'request':request,'msg':'암호를 틀렸습니다'})