function getPartner(person){
  var haus =  SpreadsheetApp.openById(ssID).getSheetByName("Haushalte");
  var lastRow = haus.getLastRow();
  var people = haus.getSheetValues(1, 1, 2, lastRow);
  for(i=0;i<lastRow;i++){
    if(people[i][0].match(person)==person){
      return people[i][1];
    }
    else if(people[i][1].match(person)==person){
      return people[i][0];
    }
  }
  return null;
}

function getPoll(){
  var global =  SpreadsheetApp.openById(ssID).getSheetByName("global");
  var poll = {running:false, noOpt:0, options:[],ready:false};
  poll.running = global.getRange(1, 2).getValue();
  poll.noOpt = global.getRange(2, 2).getValue();
  poll.ready = global.getRange(4,2).getValue();
  if(poll.noOpt>0){
    poll.options = global.getRange(3, 2, 1, poll.noOpt).getValues()[0];
  }
  return poll;
}

function setPoll(run,no,opt,ready){
  var global =  SpreadsheetApp.openById(ssID).getSheetByName("global");
  var poll = {running:run, noOpt:no, options:opt,ready:ready};
  global.getRange(1, 2).setValue(poll.running);
  global.getRange(2, 2).setValue(poll.noOpt);
  global.getRange(4,2).setValue(poll.ready);
  if(poll.noOpt>0){
    global.getRange(3, 2, 1, poll.noOpt).setValues([poll.options]);
  }
  else{
    global.getRange(3, 2, 1, 4).clear();
    poll.options=[];
  }
  return poll;
}

function getTermin(){
  var global =  SpreadsheetApp.openById(ssID).getSheetByName("global");
  var termin = {set:false,date:null};
  termin.set=global.getRange(5, 2).getValue();
  termin.date = global.getRange(5,3).getValue() ? global.getRange(5,3).getValue() : null;
  return termin;
}

function setTermin(bool,date){
  var global =  SpreadsheetApp.openById(ssID).getSheetByName("global");
  global.getRange(5,2).setValue(bool);
  if(date){
    global.getRange(5, 3).setValue(date);
  }
  return bool;
}

function getWhichForceSet(){
  var global =  SpreadsheetApp.openById(ssID).getSheetByName("global");
  var auth = global.getRange(7,2).getValue();
  var newGameTitle = global.getRange(11, 2).getValue();
  var newGameOwner = global.getRange(15,2).getValue();
  var newGamePlayers = global.getRange(20,2).getValue();
  var newExpansion = global.getRange(26,2).getValue();
  var newExpansionTitle = global.getRange(30,2).getValue();
  var expPoll = global.getRange(35,2).getValue();
  var datePoll = global.getRange(39,2).getValue();
  var set = new Array();
  if(auth){
    set.push(1);
  }
  if(newGameTitle){
    set.push(2);
  }
  if(newGameOwner){
    set.push(3);
  }
  if(newGamePlayers){
    set.push(4);
  }
  if(newExpansion){
    set.push(5);
  }
  if(newExpansionTitle){
    set.push(6);
  }
  if(expPoll){
    set.push(7);
  }
  if(datePoll){
    set.push(8);
  }
  return set;
}

function getForce(type){
  var global =  SpreadsheetApp.openById(ssID).getSheetByName("global");
  switch(type){
    case 1:
      var startRow = 7;
      var force = {set:false, no:0, ids: []};
      force.no = global.getRange(startRow+1,2).getValue();
      break;
    case 2:
      var startRow = 11;
      var force = {set:false, no:0, ids: []};
      force.no = global.getRange(startRow+1,2).getValue();
      break;
    case 3:
      var startRow = 15;
      var force = {set:false, no:0, ids: [], titles: []};
      force.no = global.getRange(startRow+1,2).getValue();
      if(force.no>0){
        force.titles= global.getRange(startRow+3,2,1,force.no).getValues()[0];
      }
      break;
    case 4:
      var startRow = 20;
      var force = {set:false, no:0, ids: [], titles: [], owners:[]};
      force.no = global.getRange(startRow+1,2).getValue();
      if(force.no>0){
        force.titles= global.getRange(startRow+3,2,1,force.no).getValues()[0];
        force.owners= global.getRange(startRow+4,2,1,force.no).getValues()[0];
      }
      break;
    case 5:
      var startRow = 26;
      var force = {set:false, no:0, ids: []};
      force.no = global.getRange(startRow+1,2).getValue();
      break;
    case 6:
      var startRow = 30;
      var force = {set:false, no:0, ids: [], games: []};
      force.no = global.getRange(startRow+1,2).getValue();
      if(force.no>0){
        force.games= global.getRange(startRow+3,2,1,force.no).getValues()[0];
      }
      break;
    case 7:
      var startRow = 35;
      var force = {set:false, no:0, ids: []};
      force.no = global.getRange(startRow+1,2).getValue();
      break;
    case 8:
      var startRow = 39;
      var force = {set:false, no:0, ids: []};
      force.no = global.getRange(startRow+1,2).getValue();
      break;
  }
  force.set = global.getRange(startRow,2).getValue();
  if(force.no>0){
    force.ids = global.getRange(startRow+2,2,1,force.no).getValues()[0];;
  }
  return force;
}

function setForce(type,set,no,ids,titles,owners,games){
  var global =  SpreadsheetApp.openById(ssID).getSheetByName("global");
  switch(type){
    case 1:
      var startRow = 7;
      var no_old = global.getRange(startRow+1, 2).getValue();
      break;
    case 2:
      var startRow = 11;
      var no_old = global.getRange(startRow+1, 2).getValue();
      break;
    case 3:
      var startRow = 15;
      if(no>0){
        global.getRange(startRow+3,2,1,no).setValues([titles]);
        var no_old = global.getRange(startRow+1, 2).getValue();
        if(no_old>no){
          global.getRange(startRow+3, no+1,1, no_old).clear();
        }
      }
      break;
    case 4:
      var startRow = 20;
      if(no>0){
        global.getRange(startRow+3,2,1,no).setValues([titles]);
        global.getRange(startRow+4,2,1,no).setValues([owners]);
        var no_old = global.getRange(startRow+1, 2).getValue();
        if(no_old>no){
          global.getRange(startRow+3, no+1,2, no_old).clear();
          global.getRange(startRow+4, no+1,2, no_old).clear();
        }
      }
      break;
    case 5:
      var startRow = 26;
      var no_old = global.getRange(startRow+1, 2).getValue();
      break;
    case 6:
      var startRow = 30;
      if(no>0){
        global.getRange(startRow+3,2,1,no).setValues([games]);
        var no_old = global.getRange(startRow+1, 2).getValue();
        if(no_old>no){
          global.getRange(startRow+3, no+1,2, no_old).clear();
        }
      }
      break;
    case 7:
      var startRow = 35;
      var no_old = global.getRange(startRow+1, 2).getValue();
      break;
    case 8:
      var startRow = 39;
      var no_old = global.getRange(startRow+1, 2).getValue();
      break;
  }
  global.getRange(startRow, 2).setValue(set);
  if(no>0){
    global.getRange(startRow+2, 2, 1, no).setValues([ids]);
    if(no_old>no){
      global.getRange(startRow+2, no+1,1, no_old).clear();
    }
  }
  else{
    var no_old = global.getRange(startRow+1, 2).getValue();
    global.getRange(startRow+2, 2, 1, no_old).clear();
  }
  global.getRange(startRow+1, 2).setValue(no);
}

function rmIDForce(type,f,msg_id){
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(30000); // wait 30 seconds for others' use of the code section and lock to stop and then proceed
  } catch (e) {
    sendText(id,"Tut mir leid, ich habe gerade zu viel zu tun. Versuch es gleich nochmal!");
    return;
  }
  // got the lock
  var index = f.ids.indexOf(msg_id);
  f.no = f.no-1;
  if(f.no==0){
    f.set = false;
  }
  f.ids.splice(index,1);
  if(type==3){
    f.titles.splice(index,1);
    setForce(type,f.set,f.no,f.ids,f.titles);
    SpreadsheetApp.flush(); // applies all pending spreadsheet changes
    lock.releaseLock();
    return;
  }
  else if (type==4){
    f.titles.splice(index,1);
    f.owners.splice(index,1);
    setForce(type,f.set,f.no,f.ids,f.titles,f.owners);
    SpreadsheetApp.flush(); // applies all pending spreadsheet changes
    lock.releaseLock();
    return;
  }
  else if (type==6) {
    f.games.splice(index,1);
    setForce(type,f.set,f.no,f.ids,null,null,f.games);
    SpreadsheetApp.flush(); // applies all pending spreadsheet changes
    lock.releaseLock();
    return;
  }
  setForce(type,f.set,f.no,f.ids);
  SpreadsheetApp.flush(); // applies all pending spreadsheet changes
  lock.releaseLock();
  return;
}

function addIDForce(type,msg_id,title,owner,expansion_for){
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(30000); // wait 30 seconds for others' use of the code section and lock to stop and then proceed
  } catch (e) {
    sendText(id,"Tut mir leid, ich habe gerade zu viel zu tun. Versuch es gleich nochmal!");
    return;
  }
  // got the lock
  f = getForce(type);
  f.ids.push(msg_id);
  if(!f.set){
    f.set=true;
  }
  if(title){
    f.titles.push(title);
  }
  else{
    if(expansion_for){
      f.games.push(expansion_for);
      setForce(type,f.set,f.no+1,f.ids,null,null,f.games);
      SpreadsheetApp.flush(); // applies all pending spreadsheet changes
      lock.releaseLock();
      return;
    }
    else {
      setForce(type,f.set,f.no+1,f.ids);
      SpreadsheetApp.flush(); // applies all pending spreadsheet changes
      lock.releaseLock();
      return;
    }
  }
  if(owner){
    f.owners.push(owner);
  }
  else{
    setForce(type,f.set,f.no+1,f.ids,f.titles);
    SpreadsheetApp.flush(); // applies all pending spreadsheet changes
    lock.releaseLock();
    return;
  }
  setForce(type,f.set,f.no+1,f.ids,f.titles,f.owners);
  SpreadsheetApp.flush(); // applies all pending spreadsheet changes
  lock.releaseLock();
  return;
}

//#######################OBSOLETE#######################