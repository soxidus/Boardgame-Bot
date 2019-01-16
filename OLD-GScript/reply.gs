// if message is a reply_to, check whether we are expecting a reply_to and send it to the right function
function checkReplyTo(data,id){
  if(data.message.reply_to_message){
    if(/SpieleabendV2_bot/.test(data.message.reply_to_message.from.username)){
      var dealtWith = false;
      var set = getWhichForceSet();
      if(set.length>0){
        for(i=0;i<set.length;i++){
          var f=getForce(set[i]);
          switch(set[i]){
            // might be trying to authenticate
            case 1:
              dealtWith = replyAuth(id,data,f);
              break;
            // might be registering new game
            case 2:
              dealtWith = replyTitle(id,data,f);
              break;
            case 3:
              dealtWith = replyOwner(id,data,f);
              break;
            case 4:
              dealtWith = replyPlayers(id,data,f);
              break;
            case 5:
              dealtWith = replyExpansionGame(id,data,f);
              break;
            case 6:
              dealtWith = replyExpansionTitle(id,data,f);
              break;
            case 7:
              dealtWith = replyExpansionPoll(id,data,f);
              break;
            case 8:
              dealtWith = replyDate(id,data,f);
              break;
          }
        }
      }
    }
    return dealtWith;
  }
  return false;
}

function forceReply(id,text,reply_to){
  if(reply_to){
    var force = {"force_reply":true,"selective":true};
    force = JSON.stringify(force);
    force = encodeURI(force);
    var url = telegramUrl + "/sendMessage?chat_id=" + id + "&text=" + text + "&reply_to_message_id" + reply_to + "&reply_markup=" + force;
  }
  else{
    var force = {"force_reply":true,"selective":false};
    force = JSON.stringify(force);
    force = encodeURI(force);
    var url = telegramUrl + "/sendMessage?chat_id=" + id + "&text=" + text + "&reply_markup=" + force;
  }
  var response = UrlFetchApp.fetch(url);
  response=JSON.parse(response);
  log(id,response.result.message_id,response.result,"Sent force Reply");
  return response.result.message_id;
}

function replyAuth(id,data,f){
  var reply_to = data.message.message_id;
  var msg_id = data.message.reply_to_message.message_id;
  // waiting for this
  if(isDuplicateRow(f.ids,msg_id)){
    log(id,reply_to,data.message,"Replying to authentication try...");
    var given_key=data.message.text.split(" ")[0];
    if(given_key == "neuschnee"){
      log(id,reply_to," - ","Authentication successful.");
      var sheet = SpreadsheetApp.openById(ssID).getSheetByName("authorized");
      sheet.appendRow([id]);
      var keyboard = {"remove_keyboard":true};
      keyboard = JSON.stringify(keyboard);
      keyboard = encodeURI(keyboard);
      var text = "Super! Wir dürfen jetzt miteinander reden.";
      var url = telegramUrl + "/sendMessage?chat_id=" + id + "&text=" + text + "&reply_markup=" + keyboard;
      var response = UrlFetchApp.fetch(url);
      response = JSON.parse(response);
      log(id,response.result.message_id,response.result,"sent message");
    }
    else{
      log(id,reply_to," - ","Authentication failed.");
      sendText(id,"Das war leider nichts.");
      //leaveChat geht nur in Gruppen
      if(data.message.chat.type == "group"){
        var url = telegramUrl + "/leaveChat?chat_id=" + id;
        var response = UrlFetchApp.fetch(url);
        Logger.log(response.getContentText());
      }
    }
    rmIDForce(1,f,msg_id);
    return true;
  }
  else{
    return false;
  }
}

function replyTitle(id,data,f){
  var msg_id = data.message.reply_to_message.message_id;
  var title = data.message.text;
  var owner = data.message.from.username ? data.message.from.username : data.message.chat.username;
  var reply_to = data.message.message_id;
  if(isDuplicateRow(f.ids,msg_id)){
    log(id,reply_to,data.message,"Replying to the new game's title...");
    rmIDForce(2,f,msg_id);
    if(/\/Stop/i.test(title)){
      sendText(id,"Na gut, hier ist nichts passiert.",reply_to);
      return true;
    }
    if(!checkGameOwned(owner,title)){
      var partner = getPartner(owner);
      if(partner){
        owner = owner + " + " + partner;
      }
      var text = "Mit wie vielen Leuten kann man "+title+" maximal spielen? Anworte mit EINER Zahl oder einem X, wenn es mit unendlich vielen gespielt werden kann. Antworte mit /stop, wenn du abbrechen möchtest oder die Spieleranzahl gerade nicht weißt."
      var msg = forceReply(id, text,reply_to);
      addIDForce(4,msg,title,owner);
    }
    else{
      sendText(id,"Ich weiß schon, dass du das Spiel hast.",reply_to);
    }
    return true;
  }
  return false;
}

function replyPlayers(id,data,f){
  var msg_id = data.message.reply_to_message.message_id;
  var reply_to = data.message.message_id;
  if(isDuplicateRow(f.ids,msg_id)){
    log(id,reply_to,data.message,"Replying to the new game's player count...");
    var index = f.ids.indexOf(msg_id);
    var title = f.titles[index];
    var owner = f.owners[index];
    rmIDForce(4,f,msg_id);
    if(/\/Stop/i.test(data.message.text)){
      sendText(id,"Na gut, hier ist nichts passiert.",reply_to);
      return true;
    }
    addGame(id,reply_to,[owner,title, data.message.text]);
    log(id,reply_to," - ","Added the new game (probably).");
    return true;
  }
  return false;
}

function replyExpansionGame(id,data,f){
  var msg_id = data.message.reply_to_message.message_id;
  var game_title = data.message.text;
  var reply_to = data.message.message_id;
  if(isDuplicateRow(f.ids,msg_id)){
    log(id,reply_to,data.message,"Replying to new expansion for <game>");
    rmIDForce(5,f,msg_id);
    if(/\/Stop/i.test(game_title)){
      sendText(id,"Na gut, hier ist nichts passiert.",reply_to);
      return true;
    }
    var text = "Wie heißt die Erweiterung für "+game_title+", die du gekauft hast? Bitte nenne mir nur eine. Antworte mit /stop, wenn du abbrechen möchtest.";
    var msg = forceReply(id,text, reply_to);
    addIDForce(6,msg,null,null,game_title);
    return true;
  }
  return false;
}

function replyExpansionTitle(id,data,f){
  var msg_id = data.message.reply_to_message.message_id;
  var expansion_title = data.message.text;
  var reply_to = data.message.message_id;
  if(data.message.chat.type == "group"){
    var owner = data.message.from.username;
  }
  else{
    var owner = data.message.chat.username;
  }
  if(isDuplicateRow(f.ids,msg_id)){
    log(id,reply_to,data.message,"Replying to the new expansion's title.");
    var index = f.ids.indexOf(msg_id);
    var game_title = f.games[index];
    rmIDForce(6,f,msg_id);
    if(/\/Stop/i.test(expansion_title)){
      sendText(id,"Na gut, hier ist nichts passiert.",reply_to);
      return true;
    }
    insertExpansion(id,reply_to,game_title,expansion_title,owner);
    log(id,reply_to," - ","Added the new expansion (probably).");
    return true;
  }
  return false;
}

function replyExpansionPoll(id,data,f){
  var msg_id = data.message.reply_to_message.message_id;
  var user = data.message.from.username ? data.message.from.username : data.message.chat.username;
  var reply_to = data.mesage.message_id;
  if(isDuplicateRow(f.ids,msg_id) && isRegistered(user)){
    log(id,reply_to,data.message,"Replying to expansion poll's game title...");
    rmIDForce(7,f,msg_id);
    if(/\/Stop/i.test(data.message.text)){
      sendText(id,"Na gut, hier ist nichts passiert.",reply_to);
      return true;
    }
    var registered = new Array();
    var plan = SpreadsheetApp.openById(ssID).getSheetByName("Plan");
    if(plan){
      if(getPoll().ready){
        // Plan has registered people in row
        registered = plan.getSheetValues(3, 1, 1, 15)[0].filter(String);
      }
      else{
        // Plan has registered people in column
        var players = plan.getSheetValues(1, 4, 15, 1).filter(String);
        var no_players = players.length;
        for(i=0;i<no_players;i++){
          registered.push(players[i][0]);
        }
      }
      generateExpOptions(id,getPoll(),data.message.text,registered);
    }
    else{
      sendText(id,"Macht erst einmal einen neuen Termin aus (/neuertermin) bzw. meldet euch an (/ich).");
    }
    return true;
  }
  return false;
}

function replyDate(id,data,f){
  var msg_id = data.message.reply_to_message.message_id;
  var user = data.message.from.username ? data.message.from.username : data.message.chat.username;
  var reply_to = data.message.message_id;
  if(isDuplicateRow(f.ids,msg_id)){
    log(id,reply_to,data.message,"Replying to new date...");
    var lock = LockService.getScriptLock();
    try {
      lock.waitLock(30000); // wait 30 seconds for others' use of the code section and lock to stop and then proceed
    } catch (e) {
      sendText(id,"Tut mir leid, ich habe gerade zu viel zu tun. Versuch es gleich nochmal!",reply_to);
      return false;
    }
    log(id,reply_to,data.message,"Cleaning plan...");
    rmIDForce(8,f,msg_id);
    if(/\/Stop/i.test(data.message.text)){
      sendText(id,"Na gut, hier ist nichts passiert.",reply_to);
      return true;
    }
    cleanPlan();
    terminFrei = setTermin(false,data.message.text);
    SpreadsheetApp.flush();
    lock.releaseLock();
    log(id,reply_to," - ","Plan set up.");
    var keyboard = {"remove_keyboard":true};
    keyboard = JSON.stringify(keyboard);
    keyboard = encodeURI(keyboard);
    var text = "Okay, schreit einfach /ich, wenn ihr am "+ data.message.text +" mitmachen wollt!";
    var url = telegramUrl + "/sendMessage?chat_id=" + id + "&text=" + text + "&reply_markup=" + keyboard;
    var response = UrlFetchApp.fetch(url);
    response = JSON.parse(response);
    log(id,response.result.message_id,response.result,"sent message");
    if(data.message.chat.type == "group"){
      var newChatTitle = "Spielwiese: "+encodeURI(data.message.text);
      var url = telegramUrl + "/setChatTitle?chat_id=" + id + "&title=" + newChatTitle;
      var response = UrlFetchApp.fetch(url);
      response = JSON.parse(response);
      log(id," - ",response.result,"Informed everyone about upcoming date.");
    }
    return true;
  }
  return false;
}

//#######################OBSOLETE#######################

function replyOwner(id,data,f){
  var msg_id = data.message.reply_to_message.message_id;
  var reply_to = data.message.message_id;
  if(isDuplicateRow(f.ids,msg_id)){
    log(id,reply_to,data.message,"Replying to new game's owner...");
    var index = f.ids.indexOf(msg_id);
    var title = f.titles[index];
    rmIDForce(3,f,msg_id);
    if(/\/Stop/i.test(data.message.text)){
      sendText(id,"Na gut, hier ist nichts passiert.",reply_to);
      return true;
    }
    var msg = forceReply(id, "Mit wie vielen Leuten kann man es spielen? Anworte mit einer Zahl oder einem X, wenn du es nicht weißt. Antworte mit /stop, wenn du abbrechen möchtest.",reply_to);
    addIDForce(4,msg,title,data.message.text);
    return true;
  }
  return false;
}