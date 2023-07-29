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

  listen(websocket)

});



function init(websocket) {
  //function to start a game upon the initialization of a websocket
  websocket.addEventListener("open", () => {
    /* 
     * when a connection is opened, it will either be the initializing player 
     * OR it will be a player joining a specific game from a link
     *
     * thus we need to parse the URL to see if there is anything in it related to the game*/


  // generate the id for the user
  const location = window.location

  const hostname = location.hostname
  const port = location.port

  // https://stackoverflow.com/a/68470365
  const random_string = (len, chars='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789') => [...Array(len)].map(() => chars.charAt(Math.floor(Math.random() * chars.length))).join('')
  const salt = random_string(5)

  let id = hostname + "-" + port + "-" + salt 

  const message = {
      type: "request",
      operation: "list-games",
      id: id
    }
  const jsoned_message = JSON.stringify(message)
  console.log("sending >>>", message)
  websocket.send(jsoned_message)
  });
}

function listen(websocket) {
  websocket.addEventListener("message", ({ data }) => {
    // receive message from the server
    const message = JSON.parse(data);
    console.log("recieved <<<", message)

  });
}
