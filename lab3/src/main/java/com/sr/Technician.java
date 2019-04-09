package com.sr;

import com.rabbitmq.client.*;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.TimeoutException;

public class Technician {

    private static final int MAX_TREATMENTS = 2;
    private final String RESPONSE_KEY_PREFIX = "response.";
    private final String LOG_KEY = "log";
    private final String EXCHANGE_NAME = "my_exchange";
    private BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
    private Channel channel;
    private List<String> specialties = new ArrayList<>();
    private List<String> possibleSpecialties = Arrays.asList("knee", "elbow", "hip");


    public static void main(String[] args) throws Exception {
        Technician tech = new Technician();
        tech.init();
        System.out.println("Waiting for messages\n");
    }

    private void init() throws IOException, TimeoutException {
        initSpecialties();
        initConnection();
        initTreatmentConsumer();
        initInfoConsumer();
    }

    private void initTreatmentConsumer() throws IOException {
        Consumer consumerTreatment = getTreatmentConsumer();

        for (String specialty : specialties) {
            String QUEUE_NAME = queueName(specialty);
            System.out.println("Joing queue " + QUEUE_NAME);
            channel.queueDeclare(QUEUE_NAME, false, false, false, null);
            channel.basicConsume(QUEUE_NAME, true, consumerTreatment);
        }
    }

    private Consumer getTreatmentConsumer() {
        return new DefaultConsumer(channel) {
            @Override
            public void handleDelivery(String consumerTag, Envelope envelope, AMQP.BasicProperties properties, byte[] body) throws IOException {
                String message = new String(body, StandardCharsets.UTF_8);
                String responseKey = RESPONSE_KEY_PREFIX + message;
                System.out.println("Received treatment message " + message + "\tKey: " + envelope.getRoutingKey());
                try {
                    Thread.sleep(1000);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                System.out.println("Treatment " + message + " DONE");
                message += ".DONE";
                channel.basicPublish(EXCHANGE_NAME, responseKey, null, message.getBytes(StandardCharsets.UTF_8));
                channel.basicPublish(EXCHANGE_NAME, LOG_KEY, null, message.getBytes(StandardCharsets.UTF_8));
            }
        };
    }

    private void initInfoConsumer() throws IOException {
        Consumer consumerInfo = getInfoConsumer();

        channel.exchangeDeclare(EXCHANGE_NAME, BuiltinExchangeType.TOPIC);
        String queueNameExchange = channel.queueDeclare().getQueue();
        String INFO_KEY = "info.#";
        channel.queueBind(queueNameExchange, EXCHANGE_NAME, INFO_KEY);
        System.out.println("Created queue: " + queueNameExchange);
        channel.basicConsume(queueNameExchange, true, consumerInfo);

    }

    private Consumer getInfoConsumer() {
        return new DefaultConsumer(channel) {
            @Override
            public void handleDelivery(String consumerTag, Envelope envelope, AMQP.BasicProperties properties, byte[] body) {
                String message = new String(body, StandardCharsets.UTF_8);
                System.out.println("Received: " + message + "\n\tKey: " + envelope.getRoutingKey());
            }
        };
    }

    private void initConnection() throws IOException, TimeoutException {
        ConnectionFactory factory = new ConnectionFactory();
        factory.setHost("localhost");
        Connection connection = factory.newConnection();
        channel = connection.createChannel();
    }

    private void initSpecialties() throws IOException {
        System.out.println("Enter specialties: ");
        for (int i = 0; i < MAX_TREATMENTS; i++) {
            String treatment = br.readLine();
            validateTreatment(treatment);
            specialties.add(treatment);
        }
    }

    private void validateTreatment(String specialty) {
        if (possibleSpecialties.contains(specialty)) {
            return;
        }
        throw new IllegalArgumentException("Wrong specialty name: " + specialty);
    }

    private String queueName(String treat) {
        return "treat_" + treat;
    }

}
