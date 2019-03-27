package com.sr2;

import java.io.BufferedReader;
import java.io.InputStreamReader;

public class Main {
    public static void main(String[] args) throws Exception {
        System.setProperty("java.net.preferIPv4Stack","true");
        DistributedMap map = new DistributedMap();
        InputStreamReader inp = new InputStreamReader(System.in);
        BufferedReader reader = new BufferedReader(inp);
        String msg;

        for(boolean c = true; c; c = !msg.equals("quit")){
            msg = reader.readLine();
            System.out.println(execute(map, msg));
        }
        reader.close();
    }

    public static Object execute(DistributedMap map, String msg) {
        try {
            Command cmd = DistributedMap.parseCommand(msg);
            switch (cmd.getOperation()) {
                case PUT:
                    if (cmd.getValue() != null)
                        return map.put(cmd.getKey(), cmd.getValue());
                    break;
                case GET:
                    return map.get(cmd.getKey());
                case REMOVE:
                    return map.remove(cmd.getKey());
                case CONTAINSKEY:
                    return map.containsKey(cmd.getKey());
            }
        } catch (IllegalArgumentException e) {
            System.out.println("Wrong Command");
        }
        return "XD";
    }
}
