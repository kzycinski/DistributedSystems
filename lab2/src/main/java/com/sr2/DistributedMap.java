package com.sr2;


import org.jgroups.JChannel;
import org.jgroups.Message;
import org.jgroups.ReceiverAdapter;
import org.jgroups.protocols.*;
import org.jgroups.protocols.pbcast.*;
import org.jgroups.stack.ProtocolStack;
import org.jgroups.util.Util;

import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetAddress;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class DistributedMap implements SimpleStringMap {
    private static final String IP_ADDRESS = "230.0.0.1";
    private static final String CHANNEL_NAME = "xD";

    private JChannel jChannel;
    private Map<String, Integer> localHashMap = new ConcurrentHashMap<>();

    public DistributedMap() {
        initChannel();
    }

    private void initChannel() {
        jChannel = new JChannel(false);
        ProtocolStack stack = new ProtocolStack();
        jChannel.setProtocolStack(stack);
        try {
            stack.addProtocol(new UDP().setValue("mcast_group_addr", InetAddress.getByName(IP_ADDRESS)))
                    .addProtocol(new PING())
                    .addProtocol(new MERGE3())
                    .addProtocol(new FD_SOCK())
                    .addProtocol(new FD_ALL().setValue("timeout", 12000).setValue("interval", 3000))
                    .addProtocol(new VERIFY_SUSPECT())
                    .addProtocol(new BARRIER())
                    .addProtocol(new NAKACK2())
                    .addProtocol(new UNICAST3())
                    .addProtocol(new STABLE())
                    .addProtocol(new GMS())
                    .addProtocol(new UFC())
                    .addProtocol(new MFC())
                    .addProtocol(new FRAG2())
                    .addProtocol(new STATE())
                    .addProtocol(new SEQUENCER())
                    .addProtocol(new FLUSH());

            stack.init();
            jChannel.setReceiver(new Receiver(jChannel, this));
            jChannel.connect(CHANNEL_NAME);
            getInitialState();
        } catch (Exception e) {
            System.out.println("Error while initiating a channel: \n");
            e.printStackTrace();
        }
    }

    private void getInitialState() {
        try {
            jChannel.getState(null, 10000);
        } catch (Exception e) {
            System.out.println("Error in getting initial state: \n");
            e.printStackTrace();
        }
    }

    public void getState(OutputStream output) throws Exception {
        synchronized (localHashMap) {
            Util.objectToStream(localHashMap, new DataOutputStream(output));
        }
    }

    public void setState(Map<String, Integer> map) throws Exception {
        localHashMap.clear();
        localHashMap.putAll(map);
    }

    public void send(String s) throws Exception {
        Message msg = new Message(null, null, s);
        jChannel.send(msg);
    }

    public static Command parseCommand(String command) {
        Operation operation = null;
        String op = null;
        String key = null;
        Integer value = null;

        String[] split = command.split("\\s+");

        if (split.length >= 2) {
            op = split[0];
            for(Operation o : Operation.values()) {
                if (o.toString().equals(op)){
                    operation = o;
                }
            }
            if (operation == null) {
                throw new IllegalArgumentException("Wrong operation in input\n");
            }
            key = split[1];
        }
        if (split.length >= 3)
            value = Integer.parseInt(split[2]);

        return new Command(operation, key, value);
    }

    public Map<String, Integer> getLocalHashMap() {
        return localHashMap;
    }

    public boolean containsKey(String key) {
        return this.localHashMap.containsKey(key);
    }

    public Integer get(String key) {
        return this.localHashMap.get(key);
    }

    public Integer put(String key, Integer value) {
        try {
            send(String.format("PUT %s %d", key, value));
        } catch (Exception e) {
            e.printStackTrace();
        }
        return this.localHashMap.put(key, value);
    }

    public Integer remove(String key) {
        try {
            send(String.format("REMOVE %s", key));
        } catch (Exception e) {
            e.printStackTrace();
        }
        return this.localHashMap.remove(key);
    }
}
