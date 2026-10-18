import { useEffect, useRef, useState } from "react";

// Opens the websocket and reconnects with a growing delay if it drops.
export default function useLiveStream(onMessage) {
  const [connected, setConnected] = useState(false);
  const handler = useRef(onMessage);
  handler.current = onMessage;

  useEffect(() => {
    let socket;
    let retry = 0;
    let timer;
    let stopped = false;

    function connect() {
      const proto = location.protocol === "https:" ? "wss" : "ws";
      socket = new WebSocket(`${proto}://${location.host}/api/ws`);

      socket.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        if (msg.type === "ready") {
          retry = 0;
          setConnected(true);
        } else {
          handler.current(msg);
        }
      };

      socket.onclose = () => {
        setConnected(false);
        if (stopped) return;
        retry += 1;
        timer = setTimeout(connect, Math.min(1000 * 2 ** retry, 15000));
      };
    }

    connect();
    return () => {
      stopped = true;
      clearTimeout(timer);
      socket?.close();
    };
  }, []);

  return connected;
}
