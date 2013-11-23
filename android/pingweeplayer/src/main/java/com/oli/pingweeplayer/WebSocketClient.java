package com.oli.pingweeplayer;

import android.os.Message;
import android.util.Log;

import org.json.JSONException;
import org.json.JSONObject;

import java.net.ConnectException;
import java.net.SocketException;

import static com.oli.pingweeplayer.MainActivity.getModel;

/**
 * Created by corradio on 15/07/2013.
 */
public class WebSocketClient {
    private String TAG = "WebSocketClient" ;
    private com.codebutler.android_websockets.WebSocketClient ws;
    private Handler hdl;
    private Model mdl;

    public WebSocketClient(String URI, Handler hdl, Model mdl) {
        this.ws = new com.codebutler.android_websockets.WebSocketClient(java.net.URI.create(URI), new WebSocketListener(), null);
        this.hdl = hdl;
        this.mdl = mdl;
    }

    public void send(String message, JSONObject data) {
        Log.e(TAG, "ws.isThreadAlive():" + ws.isThreadAlive());
        if (ws.isConnected()) {
            try {
                JSONObject obj = new JSONObject();
                obj.put("message", message);
                obj.put("data", data == null ? "" : data);
                ws.send(obj.toString());
                Log.d(TAG, "Sent message: " + message);
            } catch (JSONException e) {
                e.printStackTrace();
            }
        } else {
            Log.e(TAG, "Data was not sent because socket is closed.");
        }
    }
    public void send(String message) {
        this.send(message, null);
    }

    public void connect() {
        ws.connect();
    }

    public void disconnect() {
        ws.disconnect();
    }

    private class WebSocketListener implements com.codebutler.android_websockets.WebSocketClient.Listener {
        public WebSocketListener() {
            super();
        }

        @Override
        public void onConnect() {
            Log.d(TAG, "Connected!");
            ws.send("{\"message\":\"list_tags\",\"data\":\"\"}");
            ws.send("{\"message\":\"describe_queue\",\"data\":\"\"}");
            //mdl.showToast("Connected");
        }

        @Override
        public void onMessage(String message) {
            //Log.d(TAG, String.format("Received raw data: %s", message));
            Message mMessage = hdl.obtainMessage(0, message);
            mMessage.sendToTarget();
        }

        @Override
        public void onMessage(byte[] data) {
            //Log.d(TAG, String.format("Got binary message! %s", java.lang.Integer.toHexString(data)));
        }

        @Override
        public void onDisconnect(int code, String reason) {
            //mdl.showToast("Disconnected (" + reason + ")");
            Log.e(TAG, String.format("Disconnected! Code: %d Reason: %s", code, reason));
            Log.d(TAG, "Retrying to connect..");
            hdl.postDelayed(new Runnable() {
                public void run() {
                    ws.connect();
                }
            }, 5000);
        }

        @Override
        public void onError(Exception error) {
            // Figure out whether or not we should reconnect based on the error
            //this.onDisconnect(-1 , error.toString());
            if (
                    error instanceof ConnectException ||
                    error instanceof SocketException
               ) {
                this.onDisconnect(-1, error.toString());
            } else {
                Log.e(TAG, "Unhandled error. Will not try to reconnect!", error);
            }
        }
    }

}
