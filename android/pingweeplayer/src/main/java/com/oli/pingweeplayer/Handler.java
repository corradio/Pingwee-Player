package com.oli.pingweeplayer;

import android.os.Looper;
import android.os.Message;
import android.util.Base64;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;

/**
 * Created by corradio on 15/07/2013.
 * The Handler should set the Model, which then updates the UI and sends socket updates
 */
public class Handler extends android.os.Handler {

    private String TAG = "Handler";
    private Model mdl;
    public Handler(Looper looper, Model mdl) {
        super(looper);
        this.mdl = mdl;
    }

    @Override
    public void handleMessage(Message inputMessage) {
        if (inputMessage.obj == null)
            return;

        try {
            JSONObject json = new JSONObject(inputMessage.obj.toString());
            String message = json.getString("message");
            JSONObject data = json.getJSONObject("data");

            Log.d(TAG, String.format("Received message: %s", message));

            if (message.equals("list_tags")) {
                mdl.setTagList(JSONhelper.<String>toList(data.getJSONArray("Tags")));

            } else if (message.equals("describe_player_state")) {
                mdl.setPlayerState(data.getString("state"));

            } else if (message.equals("describe_queue") || message.equals("queue_changed")) {
                mdl.getSocket().send("describe_currently_playing");

            } else if (message.equals("describe_currently_playing")) {
                if (data.isNull("TrackInfo"))
                    return;
                JSONObject currentTrack = data.getJSONObject("TrackInfo");
                JSONArray tags = currentTrack.optJSONArray("tags");
                mdl.setCurrentTags(
                        tags==null?new ArrayList<String>():JSONhelper.<String>toList(tags)
                );
                mdl.setCurrentTrackInfo(String.format(
                        "%s - %s",
                        currentTrack.getString("artist"),
                        currentTrack.getString("title"))
                );
                mdl.getSocket().send("get_coverart", new JSONObject("{QueueIndex: " + data.getInt("QueueIndexOfCurrentlyPlaying") + "}"));


            } else if (message.equals("get_coverart")) {
                String rawdata = data.getString("data");
                int i0 = rawdata.indexOf(",") + 1;
                rawdata = rawdata.substring(i0, rawdata.length());
                if (rawdata.startsWith("http")) {
                    Log.e(TAG, "Download cover from Internet is not supported");
                } else {
                    mdl.setCover(Base64.decode(rawdata.getBytes(), Base64.DEFAULT));
                }

            } else if (message.equals("player_changed")) {
                if (mdl.setPlayerState(data.getString("State")))
                    // ask for the queue if the currently played item has been changed
                    mdl.getSocket().send("describe_currently_playing");
            }

        } catch (JSONException e) {
            e.printStackTrace();
        }

    }
}
