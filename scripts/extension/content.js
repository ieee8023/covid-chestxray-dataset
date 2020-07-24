//https://stackoverflow.com/questions/11431337/sending-message-to-chrome-extension-from-a-web-page
window.addEventListener("message", function(event) {
    // We only accept messages from ourselves
    if (event.source != window)
        return;

    if (event.data.type && (event.data.type == "FROM_PAGE")) {
        //https://developer.chrome.com/extensions/messaging
        chrome.runtime.sendMessage({greeting: "hello"}, function(response) {
            window.postMessage({type: "FROM_CONTENT", text: response.farewell})
        });
    }
});

//var data = { type: "FROM_PAGE", text: "Hello from the webpage!" };
//window.postMessage(data, "*");
