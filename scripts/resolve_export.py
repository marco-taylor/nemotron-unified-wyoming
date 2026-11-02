#!/usr/bin/env python3
"""Resolve using PEP658 metadata. Reject wheel bodies before any large transfer."""
import sys,os
sys.path.insert(0,'/work/export/bootstrap/pip')
from pip._vendor.requests.adapters import HTTPAdapter
old=HTTPAdapter.send
def guarded(self,request,*args,**kwargs):
    r=old(self,request,*args,**kwargs)
    if '.whl' in request.url and not request.url.split('?',1)[0].endswith('.metadata'):
        r.close()
        raise RuntimeError('Metadata-only resolver refuses wheel body: '+request.url)
    return r
HTTPAdapter.send=guarded
from pip._internal.cli.main import main
raise SystemExit(main(['install','--dry-run','--ignore-installed','--break-system-packages',
    '--only-binary=:all:','--find-links','export/downloads','--report',os.environ.get('EXPORT_PLAN','export/reports/pip-plan.json'),
    '--find-links','export/cpu-wheels.html',
    '-c','export/constraints-cpu.txt','-r','export/requirements.in']))
