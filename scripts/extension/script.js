//https://stackoverflow.com/questions/23150333/html5-javascript-dataurl-to-blob-blob-to-dataurl
//**blob to dataURL**
function blobToDataURL(blob, callback) {
    var a = new FileReader();
    a.onload = function(e) {callback(e.target.result);}
    a.readAsDataURL(blob);
}

//From https://github.com/vsDizzy/SaveAsMHT/blob/master/extension/background.js
//https://stackoverflow.com/questions/6497548/chrome-extension-make-it-run-every-page-load
//https://github.com/parsegarden/Save-As-MHTML/blob/master/js/background.js

function saveCurrentTab (tabId, sendResponse) { //, changeInfo, tab) {
//    if (changeInfo.status == 'complete') {
        console.log(tabId)
        chrome.pageCapture.saveAsMHTML({tabId:tabId},
        function(blob) {
            blobToDataURL(blob,
            function(dataurl) {
                chrome.downloads.download({saveAs:false,url:dataurl,filename:"saved.mhtml"});
            })
            sendResponse({farewell:FileReader().readAsText(blob)})
        })
//    }
}

//https://stackoverflow.com/questions/951021/what-is-the-javascript-version-of-sleep
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

//chrome.tabs.onUpdated.addListener()

chrome.commands.onCommand.addListener(function (command) {
    console.log("key");
    if (command == "save_page_as_mhtml") {
        tabId = chrome.tabs.getSelected(null, function(tab) {
            console.log(JSON.stringify(tab,null, 2))
            saveCurrentTab(tab.id);
        })
        //await sleep(30 * 1000)
    }
})

//To send a message from the browser to the extension, we need to
//pass a message to a content script in the middle.
//https://stackoverflow.com/questions/26156978/sending-message-from-content-script-to-background-script-breaks-chrome-extension
//https://stackoverflow.com/questions/11431337/sending-message-to-chrome-extension-from-a-web-page

chrome.runtime.onMessage.addListener(
  function(request, sender, sendResponse) {
    console.log(sender.tab ?
                "from a content script:" + sender.tab.url :
                "from the extension");
    if (request.greeting == "hello") {
        tabId = chrome.tabs.getSelected(null, function(tab) {
            console.log(JSON.stringify(tab,null, 2))
            saveCurrentTab(tab.id, sendResponse);
        })
        //await sleep(30 * 1000)
    }
    return true; //https://stackoverflow.com/questions/54126343/how-to-fix-unchecked-runtime-lasterror-the-message-port-closed-before-a-respon
    //it would be better to send a message back
  });
