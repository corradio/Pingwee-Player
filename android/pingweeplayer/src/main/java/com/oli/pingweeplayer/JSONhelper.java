package com.oli.pingweeplayer;

import org.json.JSONArray;
import org.json.JSONException;

import java.util.ArrayList;

/**
 * Created by corradio on 15/07/2013.
 */
public class JSONhelper {
    public static <T> ArrayList<T> toList(JSONArray array) throws JSONException {
        ArrayList<T> list = new ArrayList<T>();
        for (int i=0; i<array.length(); i++)
            list.add((T) array.get(i));
        return list;
    }
}
