import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = "/Users/aagamjain/Desktop/ai-safehome";
const buildDir = path.join(workspaceDir, ".codex-build/presentation");
const outputDir = path.join(workspaceDir, "output/presentation");
const skillDir = "/Users/aagamjain/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations";
const pythonExecutable = "/Users/aagamjain/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3";
const finalPptx = path.join(outputDir, "SafeHome_AI_CAC_Slides_Annotated_Final_v3.pptx");
const qrPath = path.join(buildDir, "assets/safehome-app-qr.png");

await fs.mkdir(buildDir, { recursive: true });
await fs.mkdir(outputDir, { recursive: true });
const qrBytes = await fs.readFile(qrPath);

const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const C = {
  blue: "#1E5D78", navy: "#203247", slate: "#59677A", pale: "#F7F4EE",
  grid: "#D8D3CA", white: "#FFFDFC", mint: "#2F7D68", mintPale: "#E8F2ED",
  amber: "#C9793A", amberPale: "#F8EAD9", red: "#B75045", redPale: "#F5E5E2",
  lightBlue: "#E3EEF1", dark: "#2C3E50", gray: "#7D817F",
};
const FONT = "Aptos";

function addText(slide, text, left, top, width, height, opts = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox", position: { left, top, width, height },
    fill: "none", line: { fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontFamily: FONT, fontSize: opts.fontSize ?? 22, bold: opts.bold ?? false,
    color: opts.color ?? C.dark, alignment: opts.alignment ?? "left",
    verticalAlignment: opts.verticalAlignment ?? "middle",
  };
  return shape;
}

function addRect(slide, left, top, width, height, fill, line = C.grid, radius = false) {
  return slide.shapes.add({
    geometry: radius ? "roundRect" : "rect", position: { left, top, width, height },
    fill, line: { style: "solid", fill: line, width: 1 },
  });
}

function addLine(slide, left, top, width, height = 3, fill = C.blue) {
  return slide.shapes.add({ geometry: "rect", position: { left, top, width, height }, fill, line: { fill: "none", width: 0 } });
}

function base(slide, title, subtitle, page, appendix = false) {
  slide.background.fill = C.pale;
  addLine(slide, 0, 0, 1280, 9, C.blue);
  addText(slide, title, 66, 46, 1148, 58, { fontSize: 36, bold: true, color: C.navy });
  if (subtitle) addText(slide, subtitle, 66, 102, 1148, 32, { fontSize: 19, color: C.slate });
  addText(slide, String(page), 1140, 675, 70, 20, { fontSize: 10, color: C.gray, alignment: "right" });
}

function addNotes(slide, timing, narration, nextClip = "") {
  slide.speakerNotes.text = `VIDEO TIMING\n${timing}\n\nNARRATION\n${narration}${nextClip ? `\n\nNEXT APP CLIP\n${nextClip}` : ""}`;
  slide.speakerNotes.setVisible(true);
}

// 1 - Title
{
  const s = deck.slides.add(); s.background.fill = C.pale; addLine(s,0,0,1280,9,C.blue);
  addText(s,"SafeHome AI",66,104,700,82,{fontSize:54,bold:true,color:C.navy});
  addLine(s,66,214,500,7,C.blue);
  addText(s,"A fall can begin with one overlooked cord and lead to injury, lost confidence, and less independence.",66,262,690,116,{fontSize:28,bold:true,color:C.navy});
  addText(s,"Created by Aagam Jain",66,424,600,48,{fontSize:27,bold:true,color:C.blue});
  addRect(s,850,126,300,390,C.lightBlue,C.grid,true);
  addText(s,"1 room photo",890,214,220,52,{fontSize:29,bold:true,color:C.navy,alignment:"center"});
  addText(s,"↓",980,296,40,40,{fontSize:28,bold:true,color:C.mint,alignment:"center"});
  addText(s,"Identified fall risks\nand ways to take action",878,358,244,92,{fontSize:21,bold:true,color:C.navy,alignment:"center"});
  addText(s,"1",1190,675,28,20,{fontSize:10,color:C.gray,alignment:"right"});
  addNotes(s,"0:00-0:12 (12 seconds)","A fall can begin with one overlooked cord. I am Aagam Jain, and I built SafeHome AI to help older adults and caregivers notice everyday risks sooner.","0:12-0:32 - Clip A: Use two prepared shots. First show room selection. Cut to the uploaded photo and begin analysis.");
}

// 2 - Two ways to begin
{
  const s=deck.slides.add(); base(s,"Start with the room, not a long checklist","The photo handles visible evidence. The user answers only what the image cannot prove.",2);
  addLine(s,640,205,2,360,C.grid);
  addText(s,"NO ACCOUNT REQUIRED",90,206,210,42,{fontSize:16,bold:true,color:C.blue});
  addText(s,"Quick Safety Check",90,250,475,46,{fontSize:29,bold:true,color:C.navy});
  const quick=[["1","Choose room type"],["2","Upload one photo"],["3","Get three priority actions"]];
  quick.forEach((item,i)=>{ const y=318+i*72; addRect(s,90,y,430,54,C.white,C.grid,true); addText(s,item[0],104,y+7,38,38,{fontSize:18,bold:true,color:C.blue,alignment:"center"}); addText(s,item[1],150,y+7,350,38,{fontSize:19,bold:true,color:C.dark}); if(i<2){addLine(s,304,y+54,2,13,C.blue); addText(s,"▼",294,y+61,22,18,{fontSize:10,bold:true,color:C.blue,alignment:"center"});} });
  addText(s,"OPTIONAL ACCOUNT",714,206,190,42,{fontSize:16,bold:true,color:C.blue});
  addText(s,"Keep the progress",714,250,475,46,{fontSize:29,bold:true,color:C.navy});
  const saved=[["1","Sign in and select Room Name"],["2","Run the same safety check"],["3","Track trends and share summaries"]];
  saved.forEach((item,i)=>{ const y=318+i*72; addRect(s,714,y,430,54,C.white,C.grid,true); addText(s,item[0],728,y+7,38,38,{fontSize:18,bold:true,color:C.blue,alignment:"center"}); addText(s,item[1],774,y+7,350,38,{fontSize:19,bold:true,color:C.dark}); if(i<2){addLine(s,928,y+54,2,13,C.blue); addText(s,"▼",918,y+61,22,18,{fontSize:10,bold:true,color:C.blue,alignment:"center"});} });
  addLine(s,90,548,1098,2,C.grid);
  addRect(s,250,558,780,58,C.lightBlue,C.blue,true);
  addText(s,"AN ACCOUNT ADDS  saved progress  •  comparisons  •  sharing",270,568,740,36,{fontSize:18,bold:true,color:C.blue,alignment:"center"});
  addNotes(s,"0:32-0:44 (12 seconds)","Instead of a long checklist, SafeHome AI starts with the room and asks only what the image cannot answer. An account adds progress, comparisons, and sharing.","0:44-1:14 - Clip B: Use three prepared shots: marked evidence, one follow-up question, and the completed score.");
}

// 3 - AI pipeline
{
  const s=deck.slides.add(); base(s,"The system and the problem I solved","Python rules keep an AI-assisted score explainable and consistent.",3);
  const flow=[
    ["STREAMLIT","receives photo\nand Room Type"],
    ["QUALITY GATE","orientation • light\ncontrast • blur"],
    ["OPENAI VISION","hazards • evidence\nconfidence • x/y"],
    ["PYTHON RULES","schema • allowlist\n1-15 clamp • fallback"],
    ["HUMAN CHECK","simple questions\nfor uncertain facts"],
    ["RESULT","score • risk bar\nthree-step plan"],
  ];
  flow.forEach((item,i)=>{ const x=50+i*204; addRect(s,x,178,174,124,C.white,C.grid,true); addText(s,item[0],x+10,192,154,26,{fontSize:15,bold:true,color:C.blue,alignment:"center"}); addText(s,item[1],x+12,226,150,58,{fontSize:16,color:C.dark,alignment:"center"}); if(i<5)addText(s,"→",x+174,220,30,36,{fontSize:24,bold:true,color:C.blue,alignment:"center"}); });
  addText(s,"My main challenge was variable AI scoring. The model identifies evidence; my Python layer controls every stored result.",66,326,1148,30,{fontSize:18,bold:true,color:C.navy,alignment:"center"});
  [276,640,1004].forEach(x=>{ addLine(s,x,356,2,38,C.blue); addText(s,"▼",x-10,384,22,18,{fontSize:10,bold:true,color:C.blue,alignment:"center"}); });
  addRect(s,126,406,300,142,C.lightBlue,C.blue,true);
  addText(s,"SUPABASE",146,422,260,28,{fontSize:18,bold:true,color:C.blue,alignment:"center"});
  addText(s,"account email + password hash\nRoom Names\nstructured check history",146,456,260,74,{fontSize:16,color:C.dark,alignment:"center"});
  addRect(s,490,406,300,142,C.lightBlue,C.blue,true);
  addText(s,"BREVO EMAIL API",510,422,260,28,{fontSize:18,bold:true,color:C.blue,alignment:"center"});
  addText(s,"sends password reset codes\nand text-only safety summaries\nto as many as five recipients",510,456,260,74,{fontSize:16,color:C.dark,alignment:"center"});
  addRect(s,854,406,300,142,C.lightBlue,C.blue,true);
  addText(s,"ACTIVE SESSION",874,422,260,28,{fontSize:18,bold:true,color:C.blue,alignment:"center"});
  addText(s,"current photo + analysis state\nconnect pages during the check\nphoto is not saved",874,456,260,74,{fontSize:16,color:C.dark,alignment:"center"});
  addText(s,"Built with Python, Streamlit, CSS, OpenAI Vision, Supabase, and Brevo. Invalid AI values use tested defaults, and room photos are not stored.",66,576,1148,42,{fontSize:16,bold:true,color:C.navy,alignment:"center"});
  addNotes(s,"1:14-1:30 (16 seconds)","I built the app with Python, Streamlit, and CSS. Vision AI locates evidence, while my validation layer checks categories, clamps points, and uses fallbacks. Supabase stores history, Brevo sends text-only summaries, and photos are never saved.","1:30-1:50 - Clip C: Use two prepared shots: the safety plan and the completed before-and-after comparison.");
}

// 4 - Adaptive questions
{
  const s=deck.slides.add(); base(s,"A photo cannot answer everything","Follow-up questions cover the important details outside the camera view.",4);
  addText(s,"The photo can show",82,216,500,40,{fontSize:27,bold:true,color:C.blue});
  addText(s,"Clothing in a path\nAn open drawer\nA visible cord\nFurniture narrowing a route",82,274,500,170,{fontSize:21,color:C.dark});
  addLine(s,640,210,2,270,C.grid);
  addText(s,"A person should confirm",704,216,500,40,{fontSize:27,bold:true,color:C.mint});
  addText(s,"Whether a rug slides\nWhether furniture is anchored\nWhether lighting is adequate at night\nConditions outside the camera view",704,274,500,170,{fontSize:21,color:C.dark});
  const labels=["Yes","No","Not sure","Not applicable"];
  const widths=[180,180,210,250]; let x=185;
  for(let i=0;i<labels.length;i++){ addRect(s,x,532,widths[i],58,C.white,C.blue,true); addText(s,labels[i],x,541,widths[i],40,{fontSize:19,bold:true,color:C.navy,alignment:"center"}); x+=widths[i]+20; }
  addNotes(s,"1:18-1:30 (12 seconds)","A photo can reveal clutter, but it cannot prove that a rug stays still or that nighttime lighting is adequate. The app asks only about those meaningful unknowns.","1:30-1:44 - Clip D: Answer follow-up questions and reveal the score. Narration: Answers stay simple: Yes, No, Not sure, or Not applicable. The progress indicator shows exactly how many questions remain before the room score appears.");
}

// 5 - Scoring
{
  const s=deck.slides.add(); base(s,"The hardest problem was inconsistent AI scoring","I kept the model's judgment inside four rules that my Python code enforces.",4);
  addRect(s,74,184,490,352,C.redPale,C.red,true);
  addText(s,"THE PROBLEM",108,216,420,30,{fontSize:17,bold:true,color:C.red});
  addText(s,"The same type of hazard could receive a different point value when the AI analyzed another photo.",108,270,400,130,{fontSize:28,bold:true,color:C.navy});
  addText(s,"That variation made room scores harder to compare.",108,420,400,60,{fontSize:20,color:C.slate});
  addText(s,"→",588,320,70,54,{fontSize:42,bold:true,color:C.blue,alignment:"center"});
  const guards=[["1","Limit each hazard to 1-15 points"],["2","Add only confirmed follow-up concerns"],["3","Use a tested category fallback"],["4","Cap the final room score at 100"]];
  guards.forEach((item,i)=>{const y=174+i*94; addRect(s,686,y,492,72,C.white,C.grid,true); addText(s,item[0],704,y+15,44,42,{fontSize:20,bold:true,color:C.blue,alignment:"center"}); addText(s,item[1],758,y+12,392,48,{fontSize:20,bold:true,color:C.navy});});
  addText(s,"The AI identifies evidence. The application controls the score.",74,574,1104,42,{fontSize:22,bold:true,color:C.blue,alignment:"center"});
  addNotes(s,"1:50-2:05 (15 seconds)","The hardest problem was inconsistent AI scoring. I solved it by limiting hazards to one through fifteen points, adding confirmed follow-up concerns, using category fallbacks, and capping the room at one hundred.");
}

// 6 - Testing & validation, user-provided actual results
{
  const s=deck.slides.add(); base(s,"Testing & validation","Results from 10 room photographs I staged and reviewed",5);
  const values=[
    ["Test image","Reference hazards","AI reported","Correct","Missed"],
    ["Bedroom 1","4","4","4","0"],["Kitchen 1","3","3","3","0"],["Living Room 1","5","5","5","0"],
    ["Hallway 1","3","3","3","0"],["Bathroom 1","3","3","3","0"],["Bedroom 2","4","4","4","0"],
    ["Entryway 1","2","2","2","0"],["Living Room 2","4","4","4","0"],["Kitchen 2","3","3","3","0"],
    ["Bedroom 3","4","3","3","1"],["TOTAL","35","34","34","1"],
  ];
  const t=s.tables.add({rows:values.length,columns:5,left:66,top:170,width:1120,height:438,columnWidths:[270,220,190,170,170],values});
  t.borders.assign({style:"solid",fill:C.grid,width:1});
  t.cells.block({row:0,column:0,rowCount:1,columnCount:5}).assign({fill:C.blue,textStyle:{fontFamily:FONT,fontSize:15,bold:true,color:C.white},anchor:"middle",margins:{left:10,right:10,top:5,bottom:5}});
  t.cells.block({row:1,column:0,rowCount:10,columnCount:5}).assign({fill:C.white,textStyle:{fontFamily:FONT,fontSize:14,color:C.dark},anchor:"middle",margins:{left:10,right:10,top:4,bottom:4}});
  t.cells.block({row:11,column:0,rowCount:1,columnCount:5}).assign({fill:C.lightBlue,textStyle:{fontFamily:FONT,fontSize:15,bold:true,color:C.navy},anchor:"middle",margins:{left:10,right:10,top:4,bottom:4}});
  t.cells.block({row:1,column:0,rowCount:11,columnCount:1}).assign({textStyle:{fontFamily:FONT,fontSize:14,color:C.dark,alignment:"left"}});
  t.cells.block({row:11,column:0,rowCount:1,columnCount:1}).assign({textStyle:{fontFamily:FONT,fontSize:15,bold:true,color:C.navy,alignment:"left"}});
  addText(s,"34 of 35 reference hazards detected  |  AI can still miss small details, so human review remains necessary",66,620,1120,34,{fontSize:17,bold:true,color:C.blue});
  addNotes(s,"2:05-2:20 (15 seconds)","For validation, I labeled thirty-five hazards across ten staged photos before running the app. It found thirty-four. AI can still miss small details, so every result keeps human review explicit.","2:20-2:45 - Clip D: Use three prepared shots: dashboard and trend, add a recipient field, and Accessibility.");
}

// 7 - Architecture
{
  const s=deck.slides.add(); base(s,"How the pieces work together","The app separates the interface, image review, scoring rules, and saved data.",7);
  const xs=[66,348,630,912];
  const titles=["Streamlit","Vision AI","Application logic","Supabase and email"];
  const copies=["Routes both check paths\nRenders accessible controls","Reviews visible evidence\nReturns coordinates and questions","Validates categories and scores\nBuilds the safety plan","Protects saved history\nSends text-only summaries"];
  for(let i=0;i<4;i++){
    if(i<3) addLine(s,xs[i]+238,312,44,3,C.grid);
    addText(s,String(i+1).padStart(2,"0"),xs[i],218,60,30,{fontSize:17,bold:true,color:i===1?C.amber:(i===2?C.mint:C.blue)});
    addText(s,titles[i],xs[i],260,240,42,{fontSize:24,bold:true,color:C.navy});
    addText(s,copies[i],xs[i],318,240,118,{fontSize:18,color:C.slate});
  }
  addLine(s,66,484,1086,2,C.grid);
  addText(s,"Privacy boundary",66,518,250,32,{fontSize:18,bold:true,color:C.mint});
  addText(s,"Room photos stay in the active session. Saved records contain structured results, not images.",300,508,850,58,{fontSize:22,bold:true,color:C.navy});
  addNotes(s,"2:36-2:47 (11 seconds)","Streamlit manages the experience. Vision AI reviews evidence. Application logic validates the result. Supabase protects saved history, while the email service sends summaries without room photos.","2:47-2:56 - Clip G: Open Accessibility and change text size, color mode, Read Aloud, reduced motion, and compact spacing. Narration: Accessibility remains part of the full app, with larger text, four color modes, Read Aloud, reduced motion, and compact mobile spacing.");
}

// 8 - Close
{
  const s=deck.slides.add(); base(s,"More than 200 rooms checked","Friends and family used the results to notice concerns and decide what to address first.",6);
  addText(s,"200+",82,184,430,150,{fontSize:104,bold:true,color:C.blue,alignment:"center"});
  addText(s,"rooms belonging to\nfriends and family",82,332,430,92,{fontSize:28,bold:true,color:C.navy,alignment:"center"});
  addLine(s,590,184,2,330,C.grid);
  addText(s,"What I heard",666,194,420,40,{fontSize:19,bold:true,color:C.mint});
  addText(s,"The interface felt friendly, the results used simple language, and users suggested potential features.",666,246,470,112,{fontSize:29,bold:true,color:C.navy});
  addText(s,"My goal",666,376,420,36,{fontSize:19,bold:true,color:C.amber});
  addText(s,"Help make falls less of a common fear for older adults and their families.",666,426,470,82,{fontSize:26,bold:true,color:C.navy});
  addRect(s,66,566,870,66,C.lightBlue,C.blue,true);
  addText(s,"AI can still miss small details. SafeHome AI keeps human review part of every result.",88,578,826,42,{fontSize:18,bold:true,color:C.navy,alignment:"center"});
  s.images.add({blob:qrBytes,contentType:"image/png",alt:"QR code linking to the SafeHome AI app",fit:"contain",position:{left:1028,top:540,width:108,height:108}});
  addText(s,"TRY THE APP",982,650,198,20,{fontSize:12,bold:true,color:C.blue,alignment:"center"});
  addNotes(s,"2:45-3:00 (15 seconds)","I have also used SafeHome AI in more than two hundred rooms belonging to friends and family, and they found the results extremely useful. My goal is to help more families catch risks sooner.");
}

// 9 - Production appendix, clips A-D
{
  const s=deck.slides.add(); base(s,"Clip recording plan","Four app clips receive 95 of the video's 180 seconds.",7,true);
  const rows=[
    ["Clip","Length","Screen and action","Place after"],
    ["A","20 sec","Quick Check: choose room, upload photo, show quality check, and start analysis.","Slide 1"],
    ["B","30 sec","Results: marked photo, two hazard cards, one follow-up question, score and risk bar.","Slide 2"],
    ["C","20 sec","Action: three-step safety plan, recheck photo, and resolved/still/new comparison.","Slide 3"],
    ["D","25 sec","Saved progress: dashboard, trend, comparison, email recipient, Accessibility.","Slide 5"],
  ];
  const t=s.tables.add({rows:rows.length,columns:4,left:66,top:188,width:1120,height:320,columnWidths:[92,110,690,228],values:rows});
  t.borders.assign({style:"solid",fill:C.grid,width:1});
  t.cells.block({row:0,column:0,rowCount:1,columnCount:4}).assign({fill:C.blue,textStyle:{fontFamily:FONT,fontSize:16,bold:true,color:C.white},anchor:"middle",margins:{left:10,right:10,top:7,bottom:7}});
  t.cells.block({row:1,column:0,rowCount:4,columnCount:4}).assign({fill:C.white,textStyle:{fontFamily:FONT,fontSize:15,color:C.dark},anchor:"middle",margins:{left:10,right:10,top:8,bottom:8}});
  t.cells.block({row:1,column:2,rowCount:4,columnCount:1}).assign({textStyle:{fontFamily:FONT,fontSize:15,color:C.dark,alignment:"left"}});
  addText(s,"Recording rule",66,548,180,32,{fontSize:17,bold:true,color:C.blue});
  addText(s,"Begin each clip already on the correct page. Leave about one second still at the start and end for clean edits.",250,538,936,54,{fontSize:19,color:C.navy});
}

// 10 - Production appendix, clips E-G
{
  const s=deck.slides.add(); base(s,"Clip recording plan","Use the same browser size, app theme, zoom level, and sample room across every recording.",10,true);
  const rows=[
    ["Clip","Length","Screen and action","Place after"],
    ["E","14 sec","Safety Plan: show three actions. Click Compare After Making Fixes and show resolved/still/new.","Slide 5"],
    ["F","14 sec","Stats: show room count, trend, before/after, and add a second email recipient.","Slide 6"],
    ["G","9 sec","Accessibility: change text size and color mode, then toggle Read Aloud and reduced motion.","Slide 7"],
  ];
  const t=s.tables.add({rows:rows.length,columns:4,left:66,top:188,width:1120,height:270,columnWidths:[92,110,690,228],values:rows});
  t.borders.assign({style:"solid",fill:C.grid,width:1});
  t.cells.block({row:0,column:0,rowCount:1,columnCount:4}).assign({fill:C.blue,textStyle:{fontFamily:FONT,fontSize:16,bold:true,color:C.white},anchor:"middle",margins:{left:10,right:10,top:7,bottom:7}});
  t.cells.block({row:1,column:0,rowCount:3,columnCount:4}).assign({fill:C.white,textStyle:{fontFamily:FONT,fontSize:15,color:C.dark},anchor:"middle",margins:{left:10,right:10,top:8,bottom:8}});
  t.cells.block({row:1,column:2,rowCount:3,columnCount:1}).assign({textStyle:{fontFamily:FONT,fontSize:15,color:C.dark,alignment:"left"}});
  addText(s,"Privacy before recording",66,500,260,32,{fontSize:17,bold:true,color:C.blue});
  addText(s,"Use a staged room photo. Replace real account and recipient addresses with demo addresses. Hide browser bookmarks and notifications.",330,490,856,64,{fontSize:19,color:C.navy});
  addText(s,"Do not speed up scrolling so much that labels become unreadable.",66,592,1120,34,{fontSize:19,bold:true,color:C.mint});
}

// 11 - Assembly timeline
{
  const s=deck.slides.add(); base(s,"Three-minute assembly timeline","Six slides explain the idea; four app clips prove it works.",8,true);
  const rows=[
    ["Time","Media","Time","Media"],
    ["0:00-0:12","Slide 1","1:30-1:50","Clip C"],
    ["0:12-0:32","Clip A","1:50-2:05","Slide 4"],
    ["0:32-0:44","Slide 2","2:05-2:20","Slide 5"],
    ["0:44-1:14","Clip B","2:20-2:45","Clip D"],
    ["1:14-1:30","Slide 3","2:45-3:00","Slide 6"],
  ];
  const t=s.tables.add({rows:rows.length,columns:4,left:120,top:184,width:1040,height:390,columnWidths:[180,340,180,340],values:rows});
  t.borders.assign({style:"solid",fill:C.grid,width:1});
  t.cells.block({row:0,column:0,rowCount:1,columnCount:4}).assign({fill:C.blue,textStyle:{fontFamily:FONT,fontSize:16,bold:true,color:C.white},anchor:"middle",margins:{left:10,right:10,top:6,bottom:6}});
  t.cells.block({row:1,column:0,rowCount:5,columnCount:4}).assign({fill:C.white,textStyle:{fontFamily:FONT,fontSize:16,color:C.dark},anchor:"middle",margins:{left:10,right:10,top:6,bottom:6}});
  addText(s,"Narration script is stored in the speaker notes on Slides 1-6.",120,600,1040,38,{fontSize:20,bold:true,color:C.blue,alignment:"center"});
}

// Keep only the six slides intended for the final video.
deck.slides.keep([0,1,2,4,5,7]);

for (let i=0;i<deck.slides.items.length;i++) {
  const slide=deck.slides.items[i];
  const png=await deck.export({slide,format:"png",scale:1});
  await fs.writeFile(path.join(buildDir,`slide-${String(i+1).padStart(2,"0")}.png`),new Uint8Array(await png.arrayBuffer()));
}
const montage=await deck.export({format:"webp",montage:true});
await fs.writeFile(path.join(buildDir,"montage.webp"),new Uint8Array(await montage.arrayBuffer()));

const { finalizePresentation } = await import(pathToFileURL(path.join(skillDir,"container_tools/artifact_tool_utils.mjs")).href);
const stagingDir=path.join(buildDir,"finalizer"); await fs.mkdir(stagingDir,{recursive:true});
const candidatePath=path.join(stagingDir,"candidate.pptx");
await (await PresentationFile.exportPptx(deck)).save(candidatePath);
const result=await finalizePresentation({
  workspaceDir,candidatePath,finalPath:finalPptx,pythonExecutable,
  integrityValidatorPath:path.join(skillDir,"container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath:path.join(skillDir,"container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs:["--expected-slide-size-emu","12192000,6858000","--validate-heading-fit","--require-native-table-slide","5"],
  requiredNativeTableOwnerSlides:[5],
  explicitTotalSlideCount:6,
  fontPolicy:{basis:"design",families:["Aptos"]},
  verifyArtifactToolImport:true,
  receiptPath:path.join(stagingDir,"cac-annotated-final-v3-validation.json"),
});
console.log(JSON.stringify({finalPptx,result},null,2));
