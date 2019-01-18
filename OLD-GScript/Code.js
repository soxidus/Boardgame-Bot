/*
BISHERIGE KOMMANDOS (werden so beim Botfather eingetragen:
key - Authentifiziere dich!
neuertermin - Wir wollen spielen! (nur in Gruppen)
ich - Nimm am nächsten Spieleabend teil!
newpoll - Wähle, welches Spiel du spielen möchtest! (nur in Gruppen)
pollerweiterung - Stimmt ab, welche Erweiterung eines Spiels ihr spielen wollt. (nur in Gruppen)
endpoll - Beende die Abstimmung. (nur in Gruppen)
ergebnis - Lass dir die bisher abgegebenen Stimmen anzeigen.
spiele - Ich sage dir, welche Spiele du bei mir angemeldet hast.
neuesspiel - Trag dein neues Spiel ein!
neueerweiterung - Trag deine neue Erweiterung ein.
flush - Lösche alle laufenden Pläne und Abstimmungen (laufende Spiel-Eintragungen etc. sind davon nicht betroffen)
help - Was kann ich alles tun?
WICHTIG: HELP-STRING UPDATEN!
*/

var token = "702260882:AAF3VcoDbf3sSRVDht5xM3JYu-QNywEpgZg";
var telegramUrl = "https://api.telegram.org/bot" + token;
var scriptUrl = "https://script.google.com/macros/s/AKfycbwSbSFaTM_NhX2hR399NBum2U3U45YKCjALDr_liik7r0QgmG0/exec";
var ssID = "1zYiRzC_pRkBpZ2FT1D5f3uUrPRe0aay7j716YFNH7Ug";

function getMe() {
 var url = telegramUrl + "/getMe";
 var response = UrlFetchApp.fetch(url);
 Logger.log(response.getContentText());
}

function setWebhook() {
  var url = telegramUrl + "/setWebhook?url=" + scriptUrl;
  var response = UrlFetchApp.fetch(url);
  Logger.log(response.getContentText());
}

function sendText(id,text,reply_to) {
  text = encodeURI(text);
  if(reply_to){
    var url = telegramUrl + "/sendMessage?chat_id=" + id + "&disable_notification=true" + "&text=" + text + "&reply_to_message_id" + reply_to;
  }
  else{
    var url = telegramUrl + "/sendMessage?chat_id=" + id + "&disable_notification=true" + "&text=" + text;
  }
  var response = UrlFetchApp.fetch(url);
  response = JSON.parse(response);
  log(id,response.result.message_id,response.result,"sent a message");
  return response.result.message_id;
}

function checkAuthorized(idToCheck){
  var sheet = SpreadsheetApp.openById(ssID).getSheetByName("authorized");
  var lastRow = sheet.getLastRow();
  if(lastRow>0){
    var data = sheet.getRange(1, 1, lastRow, 1).getValues();
    for(i=0;i<data.length;i++){
      if(data[i][0]==idToCheck){
        return true;
      }
    }
  }
  return false;
}

// upon typing "key": asks for password
// IDEA: do via deep linking of /start command (see https://core.telegram.org/bots#deep-linking)
function authenticate(id,text,reply_to){
  // been here before?
  if(checkAuthorized(id)){
    sendText(id,"Du musst nicht neustarten. Rede einfach mit mir!");
    return;
  }
  var msg_id = forceReply(id, "Wie lautet das Passwort?",reply_to);
  addIDForce(1,msg_id);
}

// adds a new game
function addGame(id,reply_to,param){
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(30000); // wait 30 seconds for others' use of the code section and lock to stop and then proceed
  } catch (e) {
    sendText(id,"Tut mir leid, ich habe gerade zu viel zu tun. Versuch es gleich nochmal!",reply_to);
    return;
  }
  // got the lock
  var sheet = SpreadsheetApp.openById(ssID).getSheets()[0];
  sheet.appendRow(param);
  var lastRow = sheet.getLastRow();
  var lastCol = sheet.getLastColumn();
  sheet.getRange(1, 1, lastRow, lastCol).sort(2);

  SpreadsheetApp.flush(); // applies all pending spreadsheet changes
  lock.releaseLock();
  sendText(id,"Okay, ich weiß Bescheid.",reply_to);
  return;
}

// checks whether according to database owner owns game
function checkGameOwned(owner,game){
  var sheet = SpreadsheetApp.openById(ssID).getSheets()[0];
  var lastRow = sheet.getLastRow();
  var data = sheet.getRange(1, 1, lastRow, 2).getValues();
  for(i=0;i<data.length;i++){
    if(data[i][0].toString().match(owner)==owner){
      if(data[i][1].toString().match(game)==game){
        return true;
      }
    }
  }
  return false;
}

// looks into the "Spiele"-Sheet and returns a list of all boardgames owned by the "owner"
function gamesOwned(id,owner){
  var sheet = SpreadsheetApp.openById(ssID).getSheets()[0];
  var lastRow = sheet.getLastRow();
  var data = sheet.getRange(1, 1, lastRow, 2).getValues();
  var spiele = "Du besitzt folgende Spiele: ";
  for(i=0;i<data.length;i++){
    if(data[i][0].toString().match(owner)==owner){
      spiele = spiele + data[i][1].toString().trim()+ ", ";
    }
  }
  sendText(id,spiele);
}

function expansionsOwned(id,owner){
  var sheet = SpreadsheetApp.openById(ssID).getSheets()[0];
  var lastRow = sheet.getLastRow();
  var data = sheet.getRange(1, 1, lastRow, 2).getValues();
  // new array -> init with NULL
  var spiele = new Array();
  //Testing stuff
  var liste = "hier!:  ";
  for(i=0;i<data.length;i++){
    if(data[i][0].toString().match(owner)==owner){
      spiele[i] = data[i][1].toString().trim()+ ", ";
    }
  }
  //Testing stuff
  for(i=0;i<spiele.length;i++){
    liste = liste + spiele[i] + "\n" ;
  }
  return spiele;
}


// returns true if stringToTest is already held within sheet_data
function isDuplicateColumn(sheet_data,stringToTest,column){
  if(sheet_data==undefined){
    // means there is nothing in there yet
    return false;
  }
  if(stringToTest==undefined){
    // someone is trying to fool you, damn him!
    return false;
  }
  for(j=0;j<sheet_data.length;j++){
    if(sheet_data[j][column].toString().match(stringToTest)==stringToTest){
      return true;
    }
  }
  return false;
}

function isDuplicateRow(sheet_data,stringToTest){
  if(sheet_data==undefined){
    // means there is nothing in there yet
    return false;
  }
  if(stringToTest==undefined){
    // someone is trying to fool you, damn him!
    return false;
  }
  for(j=0;j<sheet_data.length;j++){
    if(sheet_data[j].toString().match(stringToTest)==stringToTest){
      return true;
    }
  }
  return false;
}

function fun(id){
  var sticker_id = "CAADAgADaQIAA8k5CgcaRG9pldrFAg";
  var url = telegramUrl + "/sendSticker?chat_id=" + id + "&sticker=" + sticker_id;
  var response = UrlFetchApp.fetch(url);
  response = JSON.parse(response);
  log(id,response.result.message_id,response.result,"sent message");
}

// find out whether the game is registered with this owner and return the index of it
function getExpansionIndex(sheet,game,owner){
  var lastRow = sheet.getLastRow();
  if(lastRow>0){
    var sheet_data = sheet.getSheetValues(1,1,lastRow,2);
    // not in the database
    if(!isDuplicateColumn(sheet_data,game,1)){
      return;
    }
    // in the database - but is it yours?
    for(i=0;i<sheet_data.length;i++){
      if(sheet_data[i][0].toString().match(owner)==owner){
        if(sheet_data[i][1].toString().match(game)==game){
          return i+1;
        }
      }
    }
    // nope, not your game
    return;
  }
}

function insertExpansion(id,reply_to,game,expansion_title,owner){
  var sheet = SpreadsheetApp.openById(ssID).getSheets()[0];
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(30000); // wait 30 seconds for others' use of the code section and lock to stop and then proceed
  } catch (e) {
    sendText(id,"Tut mir leid, ich habe gerade zu viel zu tun. Versuch es gleich nochmal!");
    return;
  }
  // got the lock
  var index = getExpansionIndex(sheet,game,owner);
  if(index){
    var known_expansions = sheet.getSheetValues(index, 4, 1, 20)[0].filter(String);
    if(!isDuplicateRow(known_expansions,expansion_title)){
      var new_index = known_expansions.length + 4;
      sheet.getRange(index, new_index).setValue(expansion_title);
      sendText(id,"Okay, ich weiß Bescheid.",reply_to);
    }
    else{
      sendText(id,"Ich wusste schon, dass du diese Erweiterung besitzt.",reply_to);
    }
  }
  else{
    sendText(id,"Tut mir leid, aber meines Wissens besitzt du dieses Spiel nicht. Versuche es mit /neuesspiel!");
  }
  SpreadsheetApp.flush(); // applies all pending spreadsheet changes
  lock.releaseLock();
}

function log(id,msg_id,msg,action){
  var log = SpreadsheetApp.openById(ssID).getSheetByName("Log");
  if(log.getLastRow()>=100){

    log.deleteRows(1, log.getLastRow()-1);
  }
  log.appendRow([new Date(), id, msg_id, msg,action]);
}

function checkAlias(data){
  if(data.message.from.username || data.message.chat.username){
    return true;
  }
  return false;
}

function doPost(e) {
  // this is where telegram works
  var data = JSON.parse(e.postData.contents);
  var poll = getPoll();
  var terminFrei = getTermin().set;
  if(data.callback_query){
    if(poll.running && isDuplicateRow(poll.options,data.callback_query.data)){
      var voter = data.callback_query.from.username;
      var name = data.callback_query.from.first_name;
      log(data.callback_query.id,undefined,data.callback_query,"Someone pressed a button...");
      handleCallbackVote(voter,data.callback_query.data,name,data.callback_query.id);
      return;
    }
    else{
      // for now, callback buttons are ONLY used for voting and calendar stuff, so this is safe
      // however, we should probably check with a global variable (love those)
      handleCallbackCalendar(data.callback_query.data,data.callback_query.id);
      return;
    }
  }
  var text = data.message.text;
  var id = data.message.chat.id;
  var reply_to = data.message.message_id;

  if(!checkAlias(data)){
    log(id,reply_to,data.message,"Alias not set, asking for it...");
    var name = data.message.from.first_name ? data.message.from.first_name : data.message.chat.first_name;
    var text = "Liebe/r " + name + ", bitte lege erst deinen Alias fest. Sonst wird das nichts mit uns.";
    sendText(id,text);
  }

  else if(!checkReplyTo(data,id)){

    // get to know the new person
    if(/\/Key/i.test(text)) {
        log(id,reply_to,data.message,"Got a message from unknown identity. Waiting for key now...");
        authenticate(id,text,reply_to);
    }

    // do we know each other?
    else if(checkAuthorized(id)){

      if(/\/Ich/i.test(text)) {
        if(terminFrei){
          log(id,reply_to,data.message,"Wants to participate, but no date set.");
          sendText(id,"Melde erst einmal einen neuen Termin an!",reply_to);
        }
        else{
          if(data.message.chat.type == "group"){
            var user = data.message.from.username;
            var pm = data.message.from.id;
            var name = data.message.from.first_name;
          }
          else{
            var user = data.message.chat.username;
            var pm = id;
            var name = data.message.chat.first_name;
          }
          if(poll.running){
            log(id,reply_to,data.message,"Registering player on running poll...");
            registerPlayerOnRunningPoll(pm,user,name);
          }
          else{
            log(id,reply_to,data.message,"Wants to participate, adding to the plan.");
            plan(pm,user,name);
          }
        }
      }

      else if(/\/Spiele/i.test(text)) {
        if(data.message.chat.type == "group"){
          var name = data.message.from.username;
        }
        else{
          var name = data.message.chat.username;
        }
        log(id,reply_to,data.message,"Game list requested.");
        gamesOwned(id,name);
      }

      else if(/\/Erweiterungen/i.test(text)) {
        if(data.message.chat.type == "group"){
          var name = data.message.from.username;
          log(id,reply_to,data.message,"Expansion list requested. Did not answer since request occured in group chat.");
          sendText(id,"Spam doch bitte deinen eigenen Chat voll :p", reply_to);
        }
        else{
          log(id,reply_to,data.message,"Expansion list requested. Sending now.");
          var name = data.message.chat.username;
          expansionsOwned(id,name);
        }
      }

      else if(/\/NeuesSpiel/i.test(text)) {
        log(id,reply_to,data.message,"Someone bought a new game...");
        var msg_id = forceReply(id,"Wie heißt dein neues Spiel? Antworte mit /stop, wenn du abbrechen möchtest.",reply_to);
        addIDForce(2,msg_id);
      }

      else if(/\/NeueErweiterung/i.test(text)) {
        log(id,reply_to,data.message,"Someone has a new expansion...");
        var msg_id = forceReply(id,"Für welches Spiel soll die Erweiterung sein? Antworte mit /stop, wenn du abbrechen möchtest.",reply_to);
        addIDForce(5,msg_id);
      }

      else if(/\HeyBot/i.test(text)) {
        log(id,reply_to,data.message,"They found the secret command!");
        fun(id);
      }

      else if(/\/Newpoll/i.test(text)) {
        if(poll.running){
          log(id,reply_to,data.message,"New poll requested, but already running.");
          sendText(id,"Es läuft bereits eine Abstimmung.");
        }
        else{
          if(data.message.chat.type == "group"){
            var user = data.message.chat.username ? data.message.chat.username : data.message.from.username;
            if(isRegistered(user)){
              log(id,reply_to,data.message,"Creating new poll...");
              generateOptions(id,poll);
            }
            else{
              log(id,reply_to,data.message,"Poll creation request. Denied.");
              var name = data.message.chat.first_name ? data.message.chat.first_name : data.message.from.first_name;
              sendText(id,name+", du nimmst doch gar nicht am Spieleabend teil. Da kannst du doch nicht einfach entscheiden, wann die anderen abstimmen sollen!");
            }
          }
          //private chat
          else{
            log(id,reply_to,data.message,"New Poll requested, but in private chat.");
            sendText(id,"Tut mir leid, aber diese Funktion wurde für Privatchats deaktiviert. Frag mich in der Gruppe nochmal!");
          }
        }
      }

      else if(/\/PollErweiterung/i.test(text)) {
        if(poll.running){
          log(id,reply_to,data.message,"New expansion poll requested, but already running.");
          sendText(id,"Es läuft bereits eine Abstimmung.");
        }
        else{
          if(data.message.chat.type == "group"){
            var user = data.message.chat.username ? data.message.chat.username : data.message.from.username;
            if(isRegistered(user)){
              log(id,reply_to,data.message,"Creating new expansion poll, waiting for game title...");
              var msg_id = forceReply(id,"Für welches Spiel wollt ihr über die Erweiterungen abstimmen? Antworte mit /stop, wenn du abbrechen möchtest.",null);
              addIDForce(7,msg_id);
            }
            else{
              log(id,reply_to,data.message,"Poll creation request. Denied.");
              var name = data.message.chat.first_name ? data.message.chat.first_name : data.message.from.first_name;
              sendText(id,name+", du nimmst doch gar nicht am Spieleabend teil. Da kannst du doch nicht einfach entscheiden, wann die anderen abstimmen sollen!");
            }
          }
          else{
            log(id,reply_to,data.message,"New expansion poll requested, but in private chat.");
            sendText(id,"Tut mir leid, aber diese Funktion wurde für Privatchats deaktiviert. Frag mich in der Gruppe nochmal!");
          }
        }
      }

      else if(/\/Endpoll/i.test(text)){
        Logger.log(poll);
        if(poll.running){
          if(data.message.chat.type == "group"){
            var user = data.message.chat.username ? data.message.chat.username : data.message.from.username;
            if(isRegistered(user)){
              log(id,reply_to,data.message,"Ending poll...");
              endPoll(id,poll);
            }
            else{
              log(id,reply_to,data.message,"Poll end requested. Denied.");
              var name = data.message.chat.first_name ? data.message.chat.first_name : data.message.from.first_name;
              sendText(id,name+", du nimmst doch gar nicht am Spieleabend teil. Da kannst du doch nicht einfach entscheiden, wann die anderen nicht mehr abstimmen dürfen!");
            }
          }
          else{
            log(id,reply_to,data.message,"Poll end requested, but in private chat.");
            sendText(id,"Tut mir leid, aber diese Funktion wurde für Privatchats deaktiviert. Frag mich in der Gruppe nochmal!");
          }
        }
        else{
          log(id,reply_to,data.message,"Poll end requested, but no poll to end...");
          sendText(id,"Es läuft doch gar keine Abstimmung!",reply_to);
        }
      }

      else if(/\/Ergebnis/i.test(text)){
        if(poll.ready){
          log(id,reply_to,data.message,"Showing results.");
          showResults(id);
        }
        else{
          log(id,reply_to,data.message,"Results requested, not possible.");
          sendText(id,"Es gibt leider keine Ergebnisse, die ich dir zeigen kann.");
        }
      }

      else if(/\/NeuerTermin/i.test(text)){
        if(terminFrei){
          if(data.message.chat.type == "group"){
            log(id,reply_to,data.message,"New Date requested. Asking for date...");
            var msg_id = forceReply(id,"Wann wollt ihr spielen? Antworte mit /stop, wenn du abbrechen möchtest.");
            addIDForce(8,msg_id);
          }
          else{
            log(id,reply_to,data.message,"New Date requested, but in private chat.");
            sendText(id,"Tut mir leid, aber diese Funktion wurde für Privatchats deaktiviert. Frag mich in der Gruppe nochmal!");
          }
        }
        else{
          log(id,reply_to,data.message,"Date setting requested. Date already set.");
          sendText(id,"Melde dich doch einfach mit /ich beim nächsten Termin an!");
        }
      }

      else if(/\/Help/i.test(text)){
        log(id,reply_to,data.message,"Got a help request. I will do my best!");
        if(data.message.chat.type == "group"){
          sendText(id,"Ich habe folgende Funktionen:\n/key - Authentifiziere dich!\n/neuertermin - Wir wollen spielen!\n/ich - Nimm am nächsten Spieleabend teil!\n/newpoll - Wähle, welches Spiel du spielen möchtest!\n/pollerweiterung - Stimmt ab, welche Erweiterung eines Spiels ihr spielen wollt.\n/endpoll - Beende die Abstimmung.\n/ergebnis - Lass dir die bisher abgegebenen Stimmen anzeigen.\n/spiele - Ich sage dir, welche Spiele du bei mir angemeldet hast.\n/neuesspiel - Trag dein neues Spiel ein!\n/neueerweiterung - Trag deine neue Erweiterung ein.\n/flush - Lösche alle laufenden Pläne und Abstimmungen (laufende Spiel-Eintragungen etc. sind davon nicht betroffen)\n/help - Was kann ich alles tun?");
        }
        // private chat
        else{
          sendText(id,"Ich habe folgende Funktionen:\n/key - Authentifiziere dich!\n/ich - Nimm am nächsten Spieleabend teil!\n/ergebnis - Lass dir die bisher abgegebenen Stimmen anzeigen.\n/spiele - Ich sage dir, welche Spiele du bei mir angemeldet hast.\n/neuesspiel - Trag dein neues Spiel ein!\n/neueerweiterung - Trag deine neue Erweiterung ein.\n/help - Was kann ich alles tun?");
        }
      }

      else if(/\/Flush/i.test(text)){
        if(data.message.chat.type == "group"){
          log(id,reply_to,data.message,"Flush request. Begin flushing...");
          cleanPlan();
          setPoll(false,0,[],false);
          setTermin(true);
          log(id,reply_to," -","Flushing complete.");
          var keyboard = {"remove_keyboard":true};
          keyboard = JSON.stringify(keyboard);
          keyboard = encodeURI(keyboard);
          var text = "Okay, ich habe alles zurückgesetzt.";
          var url = telegramUrl + "/sendMessage?chat_id=" + id + "&text=" + text + "&reply_markup=" + keyboard;
          var response = UrlFetchApp.fetch(url);
          response = JSON.parse(response);
          log(id,response.result.message_id,response.result,"sent message");
          if(data.message.chat.type == "group"){
            var newChatTitle = "Spieleabend";
            url = telegramUrl + "/setChatTitle?chat_id=" + id + "&title=" + newChatTitle;
            response = UrlFetchApp.fetch(url);
            response = JSON.parse(response);
            log(id," - ",response.result,"No date set anymore.");
          }
        }
        else{
          log(id,reply_to,data.message,"Flushing requested, but in private chat.");
          sendText(id,"Tut mir leid, aber diese Funktion wurde für Privatchats deaktiviert. Frag mich in der Gruppe nochmal!");
        }
      }
      // THIS IS THE SPOT WHERE THE OLD VOTE-OPTION WOULD HAVE BEEN (check below) -> just reinsert it here if you want to keep using it
      // default logging
      else{
        log(id,reply_to,data);
      }
    }
    // not authorized
    else {
      log(id,reply_to,data.message,"Unauthorized person trys to talk to me. I ain't takin' no candy!");
      var answer = "Oh, hi. Ich darf leider nicht mit dir reden. Bitte authentifiziere dich mit /key!";
      sendText(id,answer);
    }
  }
}

function doGet(e) {
  return HtmlService.createHtmlOutput("Hi there");
}

//#######################OBSOLETE#######################

/*
      else if(poll.running){
        if(isDuplicateRow(poll.options,text)){
          log(id,reply_to,data.message,"It's a vote!");
          var voter = data.message.chat.username ? data.message.chat.username : data.message.from.username;
          var name = data.message.chat.first_name ? data.message.chat.first_name : data.message.from.first_name;
          vote(id,voter,text,name);
        }
        else{
          log(id,reply_to,data,"Invalid vote: Option non-existent. Probably some text message not intended for me.");
        }
      }
*/