function getWebSocketServer() {
  if (window.location.host === "fkbad.github.io") {
    return "wss://sylv-connect4-ba23863cf42a.herokuapp.com/";
  } else if (window.location.host === "localhost:8000") {
    return "ws://localhost:8001/";
  } else {
    throw new Error(`Unsupported host: ${window.location.host}`);
  }
}

// overall initializer, the bootstrap or "main"
window.addEventListener("DOMContentLoaded", () => {
  // Open the WebSocket connection and register event handlers.
  // port specified in main() of `app.py`

  const websocket_address = getWebSocketServer()
  const websocket = new WebSocket(websocket_address);

  init(websocket)

});



function init(websocket) {
  //function to start a game upon the initialization of a websocket
  websocket.addEventListener("open", () => {
    /* 
     * when a connection is opened, it will either be the initializing player 
     * OR it will be a player joining a specific game from a link
     *
     * thus we need to parse the URL to see if there is anything in it related to the game*/

  const message = {
      type: "request",
      operation: "create-match",
      id: "linux1.cs.uchicago.edu:54793-00001246",
    }
  const jsoned_message = JSON.stringify(message)
  console.log("sending", jsoned_message)
  websocket.send(jsoned_message)
  });
}
