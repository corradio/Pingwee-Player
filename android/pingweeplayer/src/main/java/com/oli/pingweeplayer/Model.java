package com.oli.pingweeplayer;

import android.graphics.BitmapFactory;
import android.os.Looper;
import android.util.Log;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;

/**
 * Created by corradio on 15/07/2013.
 * The Handler should set the Model, which then updates the UI
 */
public class Model {
    private MainActivity mainActivity;
    private WebSocketClient ws;
    private String TAG = "Model";

    // UI references (Views)
    ListView vTagList;
    Button btnPlay;
    TextView tTrackInfo;
    ImageView iCover;

    // Model
    ArrayList<String> mTags = new ArrayList<String>();
    ArrayList<String> mSpecialTags = new ArrayList<String>();
    ArrayList<Boolean> mTagsEnabled = new ArrayList<Boolean>();

    public Model(MainActivity mainActivity) {
        this.mainActivity = mainActivity;
        this.ws = new WebSocketClient("ws://192.168.1.6:8088/websocket", new Handler(Looper.getMainLooper(), this), this);

        this.btnPlay = (Button) mainActivity.findViewById(R.id.button);
        this.tTrackInfo = (TextView) mainActivity.findViewById(R.id.textView);
        this.iCover = (ImageView) mainActivity.findViewById(R.id.imageView);
    }

    public WebSocketClient getSocket() { return this.ws; }

    public void setTagList(ArrayList<String> lstTags) {
        if (lstTags == null)
            return;

        mTags.clear();
        mSpecialTags.clear();
        for (int i=0; i<lstTags.size(); i++) {
            if (lstTags.get(i).startsWith("!"))
                mSpecialTags.add(lstTags.get(i));
            else
                mTags.add(lstTags.get(i));
        }

        uiUpdateTagList();
    }

    public void setCurrentTags(ArrayList<String> tags) {
        mTagsEnabled.clear();

        for (int i=0; i<mTags.size(); i++) {
            mTagsEnabled.add(tags.contains(mTags.get(i)));
        }

        uiUpdateTagList();
    }

    public boolean setPlayerState(String playerState) {
        Log.d(TAG, "setPlayerState: make sure we don't update the state unless needed. Also return whether or not an update was done.");

        if (playerState.equals("play")) {
            btnPlay.setText("Pause");
        } else {
            btnPlay.setText("Play");
        }
        // Return true if the update was done or necessary
        return true;
    }

    public void setCurrentTrackInfo(String currentTrackInfo) {
        tTrackInfo.setText(currentTrackInfo);
    }

    public void setTagged(int i, boolean checked) {
        Log.e(TAG, "setTagged: Please call with the 'track' argument.");
        try {
            if (checked) {
                ws.send("tag_track", new JSONObject(String.format("{tag: %s}", mTags.get(i))));
            } else {
                ws.send("untag_track", new JSONObject(String.format("{tag: %s}", mTags.get(i))));
            }
        } catch (JSONException e) {
            e.printStackTrace();
        }
    }

    public void setCover(byte[] bytes) {
        iCover.setImageBitmap(BitmapFactory.decodeByteArray(bytes, 0, bytes.length));
    }

    public void setvTagList(ListView vTagList) {
        this.vTagList = vTagList;

        // Bind
        vTagList.setAdapter(
                new ArrayAdapter<String>(
                        mainActivity,
                        android.R.layout.simple_list_item_multiple_choice,
                        mTags
                )
        );
        vTagList.setChoiceMode(ListView.CHOICE_MODE_MULTIPLE);

        uiUpdateTagList();
    }

    private void uiUpdateTagList() {
        if (vTagList == null)
            return;

        // Check
        for (int i=0; i<mTags.size(); i++) {
            vTagList.setItemChecked(i, mTagsEnabled.get(i));
        }

    }

    public void showToast(String text) {
        Toast.makeText(this.mainActivity.getApplicationContext(), text, Toast.LENGTH_SHORT).show();
    }


}
