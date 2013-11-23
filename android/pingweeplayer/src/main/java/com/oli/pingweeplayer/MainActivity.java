package com.oli.pingweeplayer;

import android.content.Intent;
import android.os.Bundle;
import android.app.Activity;
import android.view.Menu;
import android.util.Log;
import android.view.MenuItem;
import android.view.View;
import android.widget.AdapterView;
import android.widget.CheckedTextView;
import android.widget.ListView;


import com.dropbox.sync.android.DbxAccountManager;
import com.dropbox.sync.android.DbxFileSystem;

public class MainActivity extends Activity {

    private String TAG = "MainActivity";
    private static Model mdl;

    private DbxAccountManager mDbxAcctMgr;
    private DbxFileSystem dbxFs;
    static final int REQUEST_LINK_TO_DBX = 0;  // This value is up to you

    public static Model getModel() {
        return mdl;
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        Log.d(TAG, "onCreate() called");
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        mdl = new Model(this);
        mdl.getSocket().connect();


        mDbxAcctMgr = DbxAccountManager.getInstance(getApplicationContext(), "ub1alrgonxdg8jf", "z9a8wjyipfded4k");
        if (mDbxAcctMgr.getLinkedAccount() == null) {
            mDbxAcctMgr.startLink((Activity)this, REQUEST_LINK_TO_DBX);
        }

        /*try {
            dbxFs = DbxFileSystem.forAccount(mDbxAcctMgr.getLinkedAccount());
            dbxFs.addSyncStatusListener(new DbxFileSystem.SyncStatusListener() {
                @Override
                public void onSyncStatusChange(DbxFileSystem fs) {
                    DbxSyncStatus fsStatus = null;
                    try {
                        fsStatus = fs.getSyncStatus();
                        Log.d(TAG, fsStatus.toString());
                    } catch (DbxException e) {
                        e.printStackTrace();
                    }
                    if (fsStatus.anyInProgress()) {
                        // Show syncing indictor
                    }
                }
                // Set syncing indicator based on current sync status
            });
        } catch (DbxException.Unauthorized unauthorized) {
            unauthorized.printStackTrace();
        }*/

        /*DbxFile testFile = null;
        try {
            testFile = dbxFs.create(new DbxPath("hello.txt"));
        } catch (DbxException e) {
            e.printStackTrace();
        }
        try {
            testFile.writeString("Hello Dropbox!");
        } catch (IOException e) {
            e.printStackTrace();
        } finally {
            testFile.close();
        }*/

    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.main, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        // Handle item selection
        switch (item.getItemId()) {
            case R.id.action_tag:
                Intent intent = new Intent(this, EditTagsActivity.class);
                startActivity(intent);
                return true;
            case R.id.action_delete:
                mdl.getSocket().send("delete");
            default:
                return super.onOptionsItemSelected(item);
        }
    }

    @Override
    public void onResume() {
        super.onResume();
        //mdl.getSocket().send("describe_player_state");
        //mdl.getSocket().send("describe_queue");
    }

    @Override
    public void onPause() {
        super.onResume();
        //mdl.getSocket().disconnect();
    }

    @Override
    public void onStop() {
        super.onStop();
        mdl.getSocket().disconnect();
    }

    public void onPlayPauseClick(View sender) {
        mdl.getSocket().send("play_pause_toogle");
    }

    public void onNextClick(View sender) {
        mdl.getSocket().send("next");
    }

    @Override
    public void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == REQUEST_LINK_TO_DBX) {
            if (resultCode == Activity.RESULT_OK) {
                // ... Start using Dropbox files.
                Log.d(TAG, "Hurray: Dropbox is allowed!");
            } else {
                // ... Link failed or was cancelled by the user.
            }
        } else {
            super.onActivityResult(requestCode, resultCode, data);
        }
    }

}
