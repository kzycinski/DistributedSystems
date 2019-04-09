package com.sr;

import com.rabbitmq.client.*;

import javax.annotation.PostConstruct;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.TimeoutException;


public class Doctor {

    private final String INFO_KEY = "info";
    private final String EXCHANGE_NAME = "my_exchange";
    private Channel channel;
    private List<String> possibleInjuries = Arrays.asList("knee", "elbow", "hip");
    private ArrayList<String> orderedProcedures = new ArrayList<>();
    private BufferedReader br = new BufferedReader(new InputStreamReader(System.in));

    public static void main(String[] args) throws Exception {
        Doctor lek = new Doctor();
        lek.init();
        lek.mainLoop();
    }

    @PostConstruct
    private void init() throws Exception {
        initConnection();
        joinChannels(initConsumer());
    }

    private Consumer initConsumer() {
        return new DefaultConsumer(channel) {
            @Override
            public void handleDelivery(String consumerTag, Envelope envelope, AMQP.BasicProperties properties, byte[] body) {
                String message = new String(body, StandardCharsets.UTF_8);
                System.out.println("Handling delivery");
                if (isForMe(envelope.getRoutingKey())) {
                    System.out.println("Received: " + message + "\tKey: " + envelope.getRoutingKey());
                }
            }
        };
    }

    private void joinChannels(Consumer consumer) throws IOException {
        String RESPONSE_KEY = "response.#";
        channel.exchangeDeclare(EXCHANGE_NAME, BuiltinExchangeType.TOPIC);
        String queueNameExchange = channel.queueDeclare().getQueue();
        channel.queueBind(queueNameExchange, EXCHANGE_NAME, INFO_KEY);
        channel.queueBind(queueNameExchange, EXCHANGE_NAME, RESPONSE_KEY);
        System.out.println("Created queue: " + queueNameExchange);
        channel.basicConsume(queueNameExchange, true, consumer);
    }

    private void initConnection() throws IOException, TimeoutException {
        ConnectionFactory factory = new ConnectionFactory();
        factory.setHost("localhost");
        Connection connection = factory.newConnection();
        channel = connection.createChannel();

        for (String treat : possibleInjuries) {
            String QUEUE_NAME = queueName(treat);
            System.out.println("Joing queue " + QUEUE_NAME);
            channel.queueDeclare(QUEUE_NAME, false, false, false, null);
        }
    }

    private void mainLoop() throws Exception {
        while (true) {
            System.out.println("Enter injury name:");
            String proc = br.readLine();
            try {
                validateInjury(proc);
            } catch (IllegalArgumentException e) {
                System.out.println(e.getMessage());
                continue;
            }
            System.out.println("Enter patient name:");
            String patient = br.readLine();

            sendMsg(proc, patient);
        }
    }

    private void validateInjury(String proc) throws IllegalArgumentException {
        if (possibleInjuries.contains(proc.toLowerCase())) {
            return;
        }
        throw new IllegalArgumentException("Wrong injury type: " + proc);
    }

    private boolean isForMe(String key) {
        String procedure = key.substring(key.indexOf(".") + 1);
        if (key.startsWith(INFO_KEY))
            return true;
        if (orderedProcedures.contains(procedure)) {
            orderedProcedures.remove(procedure);
            return true;
        }
        return false;
    }

    private String queueName(String treat) {
        return "treat_" + treat;
    }

    private void sendMsg(String proc, String patient) throws Exception {
        String LOG_KEY = "log";
        String message = proc + "." + patient;
        System.out.println("Sending " + message + " to: " + queueName(proc));
        channel.basicPublish("", queueName(proc), null, message.getBytes());
        channel.basicPublish(EXCHANGE_NAME, LOG_KEY, null, message.getBytes(StandardCharsets.UTF_8));
        orderedProcedures.add(message);
        System.out.println(orderedProcedures.toString());
    }

}
