function cleanPlan(){
  var plan = SpreadsheetApp.openById(ssID).getSheetByName("Plan");
  if(plan){
    SpreadsheetApp.openById(ssID).deleteSheet(plan);
    var poll = getPoll();
    poll.ready = false;
    setPoll(poll.running,poll.noOpt,poll.options,poll.ready);
    return;
  }
  else{
    return;
  }
}

function registerPlayer(name){
  var plan =  SpreadsheetApp.openById(ssID).getSheetByName("Plan");
  var registered = plan.getSheetValues(1, 4, 15, 1);
  var lastVal = registered.filter(String).length;
  if(!isDuplicateColumn(registered,name,0)){
    var range = plan.getRange(lastVal+1, 4);
    range.setValue(name);
  }
}

// copys all the boardgames ownes by the participant into a planning sheet
function plan(id,participant,name){
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(30000); // wait 30 seconds for others' use of the code section and lock to stop and then proceed
  } catch (e) {
    sendText(id,"Tut mir leid, ich habe gerade zu viel zu tun. Versuch es gleich nochmal!");
    return;
  }
  var sheetName = "Plan";
  var plan =  SpreadsheetApp.openById(ssID).getSheetByName(sheetName) ? SpreadsheetApp.openById(ssID).getSheetByName(sheetName) : SpreadsheetApp.openById(ssID).insertSheet(sheetName);
  var sheet = SpreadsheetApp.openById(ssID).getSheets()[0];
  // get all the data to write
  var lastRow = sheet.getLastRow();
  var data = sheet.getRange(1, 1, lastRow, 3).getValues();
  // get all the data already written
  var plan_lastRow = plan.getLastRow();
  if(plan_lastRow>0){
    var plan_data = plan.getSheetValues(1,1,plan_lastRow,1);
  }
  // iterate!
  for(i=0;i<data.length;i++){
    if(data[i][0].toString().match(participant)==participant){
      var spiel=data[i][1].toString().trim();
      if(!isDuplicateColumn(plan_data,spiel,0)){
        // Name of the game + max amount of players
        plan.appendRow([spiel,data[i][2]]);
      }
    }
  }
  registerPlayer(participant);
  SpreadsheetApp.flush();
  lock.releaseLock();
  var date = getTermin().date;
  var response = "Danke " + name + ", ich habe dich für den kommenden Spieleabend am "+date+" eingeplant! Soll ich dir den Termin in deinen Google Calendar eintragen?"
  sendKeyboardMarkup(id,["Ja", "Nein"],response);
  return;
}

function registerPlayerOnRunningPoll(id,name,participant){
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(30000); // wait 30 seconds for others' use of the code section and lock to stop and then proceed
  } catch (e) {
    sendText(id,"Tut mir leid, ich habe gerade zu viel zu tun. Versuch es gleich nochmal!");
    return;
  }
  var plan =  SpreadsheetApp.openById(ssID).getSheetByName("Plan");
  var registered =plan.getSheetValues(3, 1, 1, 15)[0];
  var last = registered.filter(String).length;
  if(!isDuplicateRow(registered,name)) {
     plan.getRange(3, last+1).setValue(name);
  }
  SpreadsheetApp.flush();
  lock.releaseLock();
  var date = getTermin().date;
  var response = "Danke " + participant + ", ich habe dich für den kommenden Spieleabend am "+date+" eingeplant! Soll ich dir den Termin in deinen Google Calendar eintragen?"
  sendKeyboardMarkup(id,["Ja", "Nein"],response);
}

function handleCallbackCalendar(answer,callback_id){
  if(answer=="Ja"){
    answerCallback(callback_id,"Oh, tut mir leid, leider kann ich das noch gar nicht. Aber bald bestimmt!");
  }
  if(answer=="Nein"){
    answerCallback(callback_id);
  }
}

// generates Options for poll about expansions
function generateExpOptions(id,poll,game,registered){
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(30000); // wait 30 seconds for others' use of the code section and lock to stop and then proceed
  } catch (e) {
    sendText(id,"Tut mir leid, ich habe gerade zu viel zu tun. Versuch es gleich nochmal!");
    return;
  }
  var plan =  SpreadsheetApp.openById(ssID).getSheetByName("Plan");
  var sheet = SpreadsheetApp.openById(ssID).getSheets()[0];
  var lastRow = sheet.getLastRow();
  if(lastRow>0){
    var sheet_data = sheet.getSheetValues(1,1,lastRow,2);
    // not in the database
    if(!isDuplicateColumn(sheet_data,game,1)){
      var keyboard = {"remove_keyboard":true};
      keyboard = JSON.stringify(keyboard);
      keyboard = encodeURI(keyboard);
      var text = "Tut mir leid, aber das Spiel habt ihr nicht. Zumindest nicht, dass ich wüsste."
      var url = telegramUrl + "/sendMessage?chat_id=" + id + "&text=" + text + "&reply_markup=" + keyboard;
      var response = UrlFetchApp.fetch(url);
      return;
    }
    var indexes = new Array();
    // in the database - what expansions do we have?
    for(i=0;i<sheet_data.length;i++){
      if(sheet_data[i][1].toString().match(game)==game){
        for(j=0;j<registered.length;j++){
          if(sheet_data[i][0].toString().match(registered[j].toString())==registered[j].toString()){
            indexes.push(i+1);
          }
        }
      }
    }
    if(indexes.length>0){
      var options = new Array();
      for(i=0;i<indexes.length;i++){
        var expansions = sheet.getSheetValues(indexes[i], 4, 1, 20)[0].filter(String);
        if(expansions.length==0){
          // keine Erweiterungen vorhanden
          expansions.push("Grundspiel");
        }
        for(j=0;j<expansions.length;j++){
          var exp=expansions[j];
          if(!isDuplicateRow(options,exp)){
            options.push(exp);
          }
        }
      }
    }
    else{
      var keyboard = {"remove_keyboard":true};
      keyboard = JSON.stringify(keyboard);
      keyboard = encodeURI(keyboard);
      var text = "Tut mir leid, aber das Spiel steht euch nicht zur Verfügung. Niemand, der am Spieleabend teilnimmt, hat es."
      var url = telegramUrl + "/sendMessage?chat_id=" + id + "&text=" + text + "&reply_markup=" + keyboard;
      var response = UrlFetchApp.fetch(url);
      return;
    }
    plan.deleteColumns(1,10);
    plan.insertColumnsBefore(1, 10);
    poll.running = true;
    poll.options = options;
    poll.noOpt = options.length;
    poll.ready = true;
    poll = setPoll(poll.running,poll.noOpt,poll.options,poll.ready);
    initPoll(id,options,registered);
    SpreadsheetApp.flush();
    lock.releaseLock();
  }
  lock.releaseLock();
}

// generates Options for the poll
function generateOptions(id,poll){
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(30000); // wait 30 seconds for others' use of the code section and lock to stop and then proceed
  } catch (e) {
    sendText(id,"Tut mir leid, ich habe gerade zu viel zu tun. Versuch es gleich nochmal!");
    return;
  }
  var plan =  SpreadsheetApp.openById(ssID).getSheetByName("Plan");
  var lastRow = plan.getLastRow();
  var registered = plan.getSheetValues(1, 4, 15, 1).filter(String)
  var no_players = registered.length;
  if(lastRow>0){
    var data = plan.getSheetValues(1,1,lastRow,2);
    var options = new Array();
    // skip the random part, no need for that
    if(data.length <= 4){
      for(var i=0;i<data.length;i++){
        if(data[i][1]>=no_players || data[i][1]=='X'){
          options.push(data[i][0]);
        }
      }
    }
    else{
      for(var n=0;n<4;n++){
        var index = Math.floor(Math.random()*data.length);
        if(data[index][1]>=no_players || data[index][1]=='X'){
          options.push(data[index][0]);
          data.splice(index,1);
        }
        else{
          n--;
        }
      }
    }
    if(options=='undefined'){
      sendText(id, "Mmh, ihr seid zu viele!")
    }
    else{
      // cleanup
      plan.deleteColumns(1,4);
      plan.insertColumnsBefore(1, 4);
      var players = new Array();
      for(i=0;i<no_players;i++){
        players.push(registered[i][0]);
      }
      poll.running = true;
      poll.options = options;
      poll.noOpt = options.length;
      poll.ready = true;
      poll = setPoll(poll.running,poll.noOpt,poll.options,poll.ready);
      initPoll(id,options,players);
      SpreadsheetApp.flush();
      lock.releaseLock();
      return poll;
    }
  }
  // there is no plan
  else{
    sendText(id,"Niemand möchte am Spieleabend teilnehmen. Schade!");
    lock.releaseLock();
    return poll;
  }
}

function initPoll(id,options,players){
  var plan = SpreadsheetApp.openById(ssID).getSheetByName("Plan");
  plan.appendRow(options);
  var zeros = new Array();
  for(i=0;i<options.length;i++){
    zeros.push(0);
  }
  plan.appendRow(zeros);
  plan.appendRow(players);
  var date = getTermin().date;
  var text = "Was wollt ihr "+date+" spielen?"
  chooseReply(id,options,text);
  return;
}

// sends message into chat with options on keyboard
function sendKeyboardMarkup(id,options,text){
  var keys = new Array();
  for(i=0;i<options.length;i++){
    keys.push([{"text":options[i],"callback_data":options[i]}]);
  }
  var keyboard = {"inline_keyboard":keys};
  var keyboardString = JSON.stringify(keyboard);
  var param = encodeURI(keyboardString);
  var url = telegramUrl + "/sendMessage?chat_id=" + id + "&text=" + text + "&reply_markup=" + param;
  var response = UrlFetchApp.fetch(url);
  response = JSON.parse(response);
  log(id,response.result.message_id,response.result,"Generated options on keyboard!");
  return;
}

// returns 'undefined' if has not voted, index of options otherwise
function hasVoted(indexVoter,plan){
  var chose = plan.getRange(4, indexVoter).getValue();
  return chose;
}

function isRegistered(person){
  var plan = SpreadsheetApp.openById(ssID).getSheetByName("Plan");
  if(plan){
    var poll = getPoll();
    if(poll.ready){
      var allowed = plan.getSheetValues(3, 1, 1, 15).filter(String)[0];
      return (isDuplicateRow(allowed,person));
    }
    else{
      var allowed = plan.getSheetValues(1, 4, 15, 1);
      return (isDuplicateColumn(allowed,person,0));
    }

  }
  else{
    return false;
  }
}

function answerCallback(callback_id, text, alert){
  var url = telegramUrl + "/answerCallbackQuery?callback_query_id=" + callback_id;
  if(text){
    text = encodeURI(text);
    url = url + "&text=" + text
  }
  if(alert){
    url = url + "&show_alert=true";
  }
  try {
    var response = UrlFetchApp.fetch(url);
    response = JSON.parse(response);
    log(callback_id,undefined,response.result,"replied to callback button");
    return response.result;
  } catch (e) {
    log(callback_id,undefined,e,"Callback Answer failed :(");
  }
}

function handleCallbackVote(voter,vote,voter_name,callback_id){
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(30000); // wait 30 seconds for others' use of the code section and lock to stop and then proceed
  } catch (e) {
    answerCallback(callback_id,"Tut mir leid, ich habe gerade zu viel zu tun. Versuch es gleich nochmal!", true);
    return;
  }
  var plan = SpreadsheetApp.openById(ssID).getSheetByName("Plan");
  var options = plan.getSheetValues(1, 1, 1, 4).filter(String)[0];
  var allowedVoters = plan.getSheetValues(3, 1, 1, 15).filter(String)[0];
  if(isDuplicateRow(allowedVoters,voter)){
    var indexVoter = allowedVoters.indexOf(voter) +1;
    var indexChoice = options.indexOf(vote) +1;
    var indexOldVote = hasVoted(indexVoter,plan);
    // same vote
    if(indexOldVote>=0 && typeof(indexOldVote)==='number' && indexOldVote==indexChoice){
      lock.releaseLock();
      answerCallback(callback_id,"Okay "+voter_name+", du hast dich erneut für "+vote+" entschieden. Du musst mir das nicht mehrmals sagen, ich bin fähig ;)", true);
      return;
    }
    //change vote
    if(indexOldVote>=0 && typeof(indexOldVote)==='number' && indexOldVote!=indexChoice){
      var oldVoteCount = plan.getRange(2, indexOldVote).getValue()-1;
      plan.getRange(2, indexOldVote).setValue(oldVoteCount);
      var newVoteCount = plan.getRange(2, indexChoice).getValue()+1;
      plan.getRange(2, indexChoice).setValue(newVoteCount);
    }
    //new vote
    else {
      var newVoteCount = plan.getRange(2, indexChoice).getValue()+1;
      plan.getRange(2, indexChoice).setValue(newVoteCount);
    }
    // register vote
    plan.getRange(4, indexVoter).setValue(indexChoice);
    SpreadsheetApp.flush();
    lock.releaseLock();
    answerCallback(callback_id,"Okay "+voter_name+", du hast dich für "+vote+" entschieden.", true);
  }
  else{
    lock.releaseLock();
    answerCallback(callback_id,"Du darfst leider nicht mit abstimmen. Bitte sag erst mit /ich Bescheid, dass du teilnimmst!");
  }
}

function showResults(id){
  var plan = SpreadsheetApp.openById(ssID).getSheetByName("Plan");
  var options = plan.getSheetValues(1, 1, 1, 15)[0].filter(String);
  var votes = plan.getSheetValues(2, 1, 1, options.length)[0];
  var answer = "";
  for(i=0;i<options.length;i++){
    answer += options[i] + ": " + votes[i] + " Stimmen\n";
  }
  sendText(id,answer);
}

function endPoll(id,poll){
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(30000); // wait 30 seconds for others' use of the code section and lock to stop and then proceed
  } catch (e) {
    sendText(id,"Tut mir leid, ich habe gerade zu viel zu tun. Versuch es gleich nochmal!");
    return;
  }
  poll = setPoll(false,0,null,true);
  setTermin(true);
  lock.releaseLock();
  var keyboard = {"remove_keyboard":true};
  keyboard = JSON.stringify(keyboard);
  keyboard = encodeURI(keyboard);
  var text = "Abstimmung beendet. Um die Ergebnisse zu sehen, frag mich einfach mit /ergebnis danach."
  var url = telegramUrl + "/sendMessage?chat_id=" + id + "&text=" + text + "&reply_markup=" + keyboard;
  var response = UrlFetchApp.fetch(url);
  Logger.log(response.getContentText());
  return poll;
}


//#######################OBSOLETE#######################

function vote(id,voter,text,voter_name){
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(30000); // wait 30 seconds for others' use of the code section and lock to stop and then proceed
  } catch (e) {
    sendText(id,"Tut mir leid, ich habe gerade zu viel zu tun. Versuch es gleich nochmal!");
    return;
  }
  var plan = SpreadsheetApp.openById(ssID).getSheetByName("Plan");
  var options = plan.getSheetValues(1, 1, 1, 4).filter(String)[0];
  var allowedVoters = plan.getSheetValues(3, 1, 1, 15).filter(String)[0];
  if(isDuplicateRow(allowedVoters,voter)){
    var indexVoter = allowedVoters.indexOf(voter) +1;
    var indexChoice = options.indexOf(text) +1;
    var indexOldVote = hasVoted(indexVoter,plan);
    // same vote
    if(indexOldVote>=0 && typeof(indexOldVote)==='number' && indexOldVote==indexChoice){
      lock.releaseLock();
      sendText(id,"Okay "+voter_name+", du hast dich erneut für "+text+" entschieden. Du musst mir das nicht mehrmals sagen, ich bin fähig ;)");
      return;
    }
    //change vote
    if(indexOldVote>=0 && typeof(indexOldVote)==='number' && indexOldVote!=indexChoice){
      var oldVoteCount = plan.getRange(2, indexOldVote).getValue()-1;
      plan.getRange(2, indexOldVote).setValue(oldVoteCount);
      var newVoteCount = plan.getRange(2, indexChoice).getValue()+1;
      plan.getRange(2, indexChoice).setValue(newVoteCount);
    }
    //new vote
    else {
      var newVoteCount = plan.getRange(2, indexChoice).getValue()+1;
      plan.getRange(2, indexChoice).setValue(newVoteCount);
    }
    // register vote
    plan.getRange(4, indexVoter).setValue(indexChoice);
    SpreadsheetApp.flush();
    lock.releaseLock();
    sendText(id,"Okay "+voter_name+", du hast dich für "+text+" entschieden.");
  }
  else{
    lock.releaseLock();
    sendText(id,"Du darfst leider nicht mit abstimmen. Bitte sag erst mit /ich Bescheid, dass du teilnimmst!");
  }
}

// whenever someone wants to use this: just use the new sendKeyboardMarkup-function!
function chooseReplyTitles(id,options){
  var keys = new Array();
  for(i=0;i<options.length;i++){
    keys.push([options[i]]);
  }
  var keyboard = {"keyboard":keys,"resize_keyboard":true,"one_time_keyboard":true};
  var keyboardString = JSON.stringify(keyboard);
  var param = encodeURI(keyboardString);
  var text = "Wähle ein Spiel aus: "
  var url = telegramUrl + "/sendMessage?chat_id=" + id + "&text=" + text + "&reply_markup=" + param;
  var response = UrlFetchApp.fetch(url);
  Logger.log(response.getContentText());
  return;
}



