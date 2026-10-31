// Execute the actual localized handler with browser-boundary stubs.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const js=fs.readFileSync('static/app.js','utf8');
const start=js.indexOf('const startCampaignBtn =');
const code=js.slice(start,js.indexOf("$('saveCampaignBtn')",start));
async function run(name,status,body,options={}) {
 let handler,calls=0,refreshes=0,reloads=0,messages=[];
 const button={disabled:false,addEventListener:(_event,fn)=>handler=fn};
 const context={currentUIMode:'player',startCampaignBusy:false,state:{ui:{campaign_can_start:true}},
  $:()=>button,apiUrl:()=>'/start_campaign',
  addMessage:(_role,_who,text)=>{messages.push(text);return 0},
  replaceMessage:(_id,_role,_who,text)=>{messages[0]=text},
  fetch:async()=>{calls++;if(options.transport)throw Error('PRIVATE');if(options.retry && calls===2)return {status:200,ok:true,json:async()=>({ok:true,gm_output:{player_facing_text:'Retry opening'}})};return {status,ok:status<400,json:async()=>{if(options.badJSON)throw Error('PRIVATE');return body}}},
  loadState:async()=>{refreshes++;if(options.refreshFailure)throw Error('PRIVATE');context.state.ui.campaign_can_start=!body.ok},
  reloadAll:async()=>{reloads++;messages=['persisted narration'];context.state.ui.campaign_can_start=false},
  updateCampaignBootstrapUI:s=>button.disabled=!s.ui.campaign_can_start,
  formatBlockedNewCampaignMessage:()=> 'Blocked',newCampaignBlockedDetails:()=>null};
 vm.createContext(context);vm.runInContext(code,context);await handler();
 if(options.success){assert.equal(reloads,1);assert.equal(messages[0],'persisted narration');assert(button.disabled)}
 else {assert.equal(reloads,0);assert(messages[0] && !messages[0].includes('PRIVATE'));assert(!button.disabled)}
 assert.equal(calls,1);assert.equal(context.startCampaignBusy,false);
 if(options.retry){await handler();assert.equal(calls,2);assert.equal(reloads,1);assert(button.disabled)}
 if(options.success){await handler();assert.equal(calls,1)}
 return {name,pass:true,message:messages[0],calls,refreshes,reloads};
}
(async()=>{
const results=[];
results.push(await run('U1',200,{ok:true,gm_output:{player_facing_text:'Scene opening'}},{success:true}));
results.push(await run('U2',422,{ok:false,status:'opening_failed',error:'PRIVATE'}));
results.push(await run('U3',500,{ok:false,error:'PRIVATE'}));
results.push(await run('U4',422,{ok:false,error:'PRIVATE'}));
results.push(await run('U5',422,{ok:false},{retry:true}));
// U6: disabled authoritative state prevents a second submission.
// Test by replacing the run success handler's state guard with initial false.
let calls=0;const ctx={currentUIMode:'player',startCampaignBusy:false,state:{ui:{campaign_can_start:false}},$ :()=>({addEventListener:(_e,fn)=>ctx.handler=fn}),fetch:()=>calls++};
vm.createContext(ctx);vm.runInContext(code,ctx);await ctx.handler();assert.equal(calls,0);
results.push({name:'U6',pass:true,calls});
results.push(await run('U7',422,{ok:false},{refreshFailure:true}));
results.push(await run('transport',0,{}, {transport:true}));
results.push(await run('badJSON',500,{}, {badJSON:true}));
fs.writeFileSync('artifacts/pr_play_07/ui_results.json',JSON.stringify(results,null,2));
console.log(`${results.length} campaign-start UI boundary checks passed`);
})().catch(e=>{console.error(e);process.exitCode=1});
