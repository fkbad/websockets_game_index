
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

  // listening for someone opening a websocket
  initGame(websocket)

});



// prototype
// function init(websocket) {
//   //function to start a game upon the initialization of a websocket
//   websocket.addEventListener("open", () => {
//     /* 
//      * when a connection is opened, it will either be the initializing player 
//      * OR it will be a player joining a specific game from a link
//      *
//      * thus we need to parse the URL to see if there is anything in it related to the game*/

//   const message = {
//     "type": "request",
//     "operation": "create-match",
//     "id": "linux1.cs.uchicago.edu:54793-00001246",
//     "params":
//     {
//       "game": "tictactoe",
//       "player-name": "Alex"
//     }
//   }
//   const jsoned_message = JSON.stringify(message)
//   console.log("sending", jsoned_message)
//   websocket.send(jsoned_message)
//   });
// }


function initGame(websocket) {

  //function to start a game upon the initialization of a websocket
  websocket.addEventListener("open", () => {

    // this returns a dictionary
    const url_params = new URLSearchParams(window.location.search)

    // search params uses dict-like get syntax
    // has separate method to check whether or not a field is in the URL

    // const match_id = url_params.get("match-id")
    const join_match_id = url_params.get("join")
    const spectate_match_id = url_params.get("spectate")

    if (join_match_id && spectate_match_id) {
      console.log('found both join and spectate match id in URI, exiting')
      return
    }

    // generate the id for the user
    const location = window.location

    const hostname = location.hostname
    const port = location.port

    // const uuid = self.crypto.randomUUID()
    // let id = hostname + "-" + port + "-" + uuid + "--:3"

    const id = self.crypto.randomUUID()
    let id = hostname + "-" + port + "-" + uuid + "--:3"

    // placeholder event 
    let message = {
      "type": "request",
      "id": id
    }
    if (join_match_id) {
      // added creator tag for user creating the match
      console.log("found JOIN match id[", join_match_id, "]in URL ")
      message.operation = "join-match"
      const params = {
        "match-id" : join_match_id,
        "player-name" : "player2"
      }
      message.params = params


    } else if (spectate_match_id) {
      // spectating match
      message.operation = "spectate-match"
      const params = {
        "match-id" : spectate_match_id,
        "player-name" : "player2"
      }
      message.params = params
    } else  { 
      // TODO make global utils to store the information
      // about message format so this could be a global variable call
      message.operation = "create-match"
      const params = {
        "game" : "p1wins",
        "player-name" : "player1"
      }
      message.params = params
    }
    const jsoned_message = JSON.stringify(message)
    console.log("sending :",message)
    websocket.send(jsoned_message)
  });
}



function listen(websocket) {
  websocket.addEventListener("message", ({ data }) => {
    // receive message from the server
    const message = JSON.parse(data);
    console.log("recieved", message)
    // switch (message.type) {
    //   case "error":
    //     showMessage(message.message);
    //     break;

    //   default:
    //     throw new Error(`Unsupported event type: ${message.type}.`);
    // }
  });
}

