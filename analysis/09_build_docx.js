const fs=require('fs');
const {Document,Packer,Paragraph,TextRun,HeadingLevel,AlignmentType,Table,TableRow,TableCell,
       WidthType,ShadingType,BorderStyle,ImageRun,PageBreak}=require('docx');

const md=fs.readFileSync('/home/user/brainmets-POP/docs/manuscript-draft.md','utf8').split('\n');
const PAGE_W=12240, MARGIN=1440, CONTENT=PAGE_W-2*MARGIN;   // US Letter

// inline *italic* / **bold** -> TextRun[]
function runs(t, base={}){
  const out=[]; const re=/(\*\*[^*]+\*\*|\*[^*]+\*)/g; let last=0,m;
  while((m=re.exec(t))!==null){
    if(m.index>last) out.push(new TextRun({...base,text:t.slice(last,m.index)}));
    const s=m[0];
    if(s.startsWith('**')) out.push(new TextRun({...base,text:s.slice(2,-2),bold:true}));
    else out.push(new TextRun({...base,text:s.slice(1,-1),italics:true}));
    last=re.lastIndex;
  }
  if(last<t.length) out.push(new TextRun({...base,text:t.slice(last)}));
  return out.length?out:[new TextRun({...base,text:t})];
}
const cell=(t,{head=false,w})=>new TableCell({
  width:{size:w,type:WidthType.DXA},
  shading:head?{type:ShadingType.CLEAR,fill:'EDF1F4'}:undefined,
  margins:{top:60,bottom:60,left:110,right:110},
  children:[new Paragraph({spacing:{before:0,after:0},
    children:runs(t,{size:18,bold:head,font:'Calibri'})})]});

const kids=[];
let i=0;
while(i<md.length){
  let ln=md[i];

  if(/^\s*\|/.test(ln) && i+1<md.length && /^\s*\|[\s:|-]+\|\s*$/.test(md[i+1])){
    const rows=[]; 
    while(i<md.length && /^\s*\|/.test(md[i])){ rows.push(md[i]); i++; }
    const parse=r=>r.trim().replace(/^\||\|$/g,'').split('|').map(c=>c.trim());
    const header=parse(rows[0]); const body=rows.slice(2).map(parse);
    const n=header.length; const w=Math.floor(CONTENT/n);
    const widths=Array(n).fill(w); widths[n-1]=CONTENT-w*(n-1);
    kids.push(new Table({
      columnWidths:widths, width:{size:CONTENT,type:WidthType.DXA},
      rows:[new TableRow({tableHeader:true,children:header.map((h,k)=>cell(h,{head:true,w:widths[k]}))}),
            ...body.map(r=>new TableRow({children:r.map((c,k)=>cell(c,{w:widths[k]}))}))]}));
    kids.push(new Paragraph({spacing:{after:200},children:[]}));
    continue;
  }

  if(/^---+\s*$/.test(ln)){
    kids.push(new Paragraph({spacing:{before:120,after:240},
      border:{bottom:{style:BorderStyle.SINGLE,size:6,color:'C7CDD2'}},children:[]}));
    i++; continue;
  }
  const h=ln.match(/^(#{1,4})\s+(.*)$/);
  if(h){
    const lvl=[HeadingLevel.TITLE,HeadingLevel.HEADING_1,HeadingLevel.HEADING_2,HeadingLevel.HEADING_3][h[1].length-1];
    kids.push(new Paragraph({heading:lvl,spacing:{before:h[1].length===1?0:280,after:140},
      children:runs(h[2],{font:'Calibri'})}));
    i++; continue;
  }
  if(/^\s*$/.test(ln)){ i++; continue; }
  const li=ln.match(/^[*-]\s+(.*)$/);
  if(li){
    kids.push(new Paragraph({bullet:{level:0},spacing:{after:80},
      children:runs(li[1],{size:21,font:'Calibri'})}));
    i++; continue;
  }
  // paragraph: join wrapped lines
  const buf=[ln]; i++;
  while(i<md.length && md[i].trim()!=='' && !/^[#|*-]/.test(md[i]) && !/^---+$/.test(md[i])){ buf.push(md[i]); i++; }
  kids.push(new Paragraph({spacing:{after:160,line:300},alignment:AlignmentType.LEFT,
    children:runs(buf.join(' '),{size:21,font:'Calibri'})}));
}

// Figure 1 image on its own page
kids.push(new Paragraph({children:[new PageBreak()]}));
kids.push(new Paragraph({heading:HeadingLevel.HEADING_2,spacing:{after:160},
  children:runs('Figure 1',{font:'Calibri'})}));
kids.push(new Paragraph({spacing:{after:160},children:[new ImageRun({
  type:'png',
  data:fs.readFileSync('/home/user/brainmets-POP/figures/figure1_survival_both_clocks.png'),
  transformation:{width:660,height:319}})]}));
kids.push(new Paragraph({spacing:{after:160},children:runs(
  'Overall survival in synchronous and metachronous brain metastases under two time origins. (A) From primary lung cancer diagnosis; (B) from brain-metastasis diagnosis. Kaplan-Meier estimates with censoring marks and numbers at risk. The same 116 patients and 89 deaths underlie both panels. Curves are shown over the full observation period (to 129 months); fewer than five patients per group remain at risk beyond 48 months.',
  {size:19,font:'Calibri'})}));

kids.push(new Paragraph({children:[new PageBreak()]}));
kids.push(new Paragraph({heading:HeadingLevel.HEADING_2,spacing:{after:160},
  children:runs('Figure 2',{font:'Calibri'})}));
kids.push(new Paragraph({spacing:{after:160},children:[new ImageRun({
  type:'png',
  data:fs.readFileSync('/home/user/brainmets-POP/figures/figure2_oncoplot.png'),
  transformation:{width:660,height:422}})]}));
kids.push(new Paragraph({spacing:{after:160},children:runs(
  'Oncoplot of the 20 most frequently altered genes, synchronous beside metachronous brain metastases. Each column is one patient, ordered within group by alteration pattern; each row is one gene, ordered by cohort-wide frequency except that the three 9p21.3 genes are held adjacent because they are contiguous on the chromosome and lost in a single event. Copy-number events fill the whole cell and short variants are drawn as an inset bar, so alteration class is carried by geometry as well as colour. The bar above shows the number of altered genes per patient; percentages at right are within-group frequencies. No alteration differed significantly between groups after Benjamini-Hochberg correction.',
  {size:19,font:'Calibri'})}));

const doc=new Document({
  styles:{default:{
    document:{run:{font:'Calibri',size:21},paragraph:{spacing:{line:300}}},
    title:{run:{font:'Calibri',size:34,bold:true,color:'12303A'},paragraph:{spacing:{after:240}}},
    heading1:{run:{font:'Calibri',size:28,bold:true,color:'12303A'}},
    heading2:{run:{font:'Calibri',size:24,bold:true,color:'1D4B57'}},
    heading3:{run:{font:'Calibri',size:22,bold:true,color:'333333'}}}},
  sections:[{properties:{page:{size:{width:12240,height:15840},
    margin:{top:MARGIN,bottom:MARGIN,left:MARGIN,right:MARGIN}}}, children:kids}]});

Packer.toBuffer(doc).then(b=>{fs.writeFileSync('/home/user/brainmets-POP/docs/manuscript-draft.docx',b);
  console.log('wrote manuscript-draft.docx',b.length,'bytes');});
