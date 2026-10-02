#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Real LibreOffice smoke: metadata-stamped tables, multiline text and negative chart labels."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import hashlib
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches, Pt
from stamp_pptx_metadata import stamp


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    office=shutil.which('libreoffice') or shutil.which('soffice')
    if not office or not shutil.which('pdftotext'):
        raise RuntimeError('real smoke requires LibreOffice Impress and Poppler pdftotext')
    with tempfile.TemporaryDirectory(prefix='clayz-smoke-') as td:
        root=Path(td);p=Presentation()
        s=p.slides.add_slide(p.slide_layouts[6]);t=s.shapes.add_table(2,2,0,0,Inches(8),Inches(3))
        for i,text in enumerate(['2025','Line one\nLine two','2025','Complete table']):t.table.cell(i//2,i%2).text=text
        s=p.slides.add_slide(p.slide_layouts[6]);d=CategoryChartData();d.categories=['Negative','Positive'];d.add_series('Values',[-11.09,24.01])
        chart=s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED,0,0,Inches(8),Inches(5),d).chart
        chart.plots[0].has_data_labels=True
        chart.plots[0].data_labels.show_value=True
        chart.plots[0].data_labels.number_format='0.00'
        src=root/'source.pptx';pptx=root/'stamped.pptx';p.save(src);stamp(src,pptx,{'ClayzVersion':'runtime-smoke'})
        cmd=[office,'-env:UserInstallation='+ (root/'office-profile').as_uri(),'--headless','--convert-to','pdf','--outdir',str(root),str(pptx)]
        proc=subprocess.run(cmd,check=True,capture_output=True,text=True,timeout=90)
        pdf=root/'stamped.pdf'
        if not pdf.is_file():raise RuntimeError('Office returned without an actual PDF: '+proc.stdout+proc.stderr)
        text=subprocess.run(['pdftotext',str(pdf),'-'],check=True,capture_output=True,text=True,timeout=30).stdout
        for value in ['Line one','Line two','Complete table','-11.09','24.01']:
            if value not in text:raise RuntimeError('rendered text/negative label missing: '+value)
        result={'status':'passed','office_version':subprocess.run([office,'--version'],capture_output=True,text=True,check=True).stdout.strip(),
                'pptx_sha256':hashlib.sha256(pptx.read_bytes()).hexdigest(),'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),
                'checks':['metadata-stamped package opens','integrated table and multiline text render','negative chart label retains sign'],
                'limitations':['Not a pixel geometry verdict.','Not STKaiti or PowerPoint/WPS native acceptance.']}
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result))

if __name__=='__main__':main()
