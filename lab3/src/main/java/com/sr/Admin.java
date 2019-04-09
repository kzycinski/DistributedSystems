package com.sr;

import com.rabbitmq.client.*;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.TimeoutException;

public class Admin {

    private final String EXCHANGE_NAME = "my_exchange";
    private BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
    private Channel channel;

    public static void main(String[] args) throws Exception {
        Admin admin = new Admin();
        admin.init();
        admin.mainLoop();
    }

    private void init() throws IOException, TimeoutException {
        initConnection();
        initConsumer();
    }

    private void initConsumer() throws IOException {
        String queueName = channel.queueDeclare().getQueue();
        String LOG_KEY = "log";
        channel.queueBind(queueName, EXCHANGE_NAME, LOG_KEY);

        channel.basicConsume(queueName, true, getConsumer());
    }

    private Consumer getConsumer() {
        return new DefaultConsumer(channel) {
            @Override
            public void handleDelivery(String consumerTag, Envelope envelope, AMQP.BasicProperties properties, byte[] body) {
                String message = new String(body, StandardCharsets.UTF_8);
                System.out.println("LOG: " + message);
            }
        };
    }

    private void initConnection() throws IOException, TimeoutException {
        ConnectionFactory factory = new ConnectionFactory();
        factory.setHost("localhost");
        Connection connection;
        connection = factory.newConnection();
        channel = connection.createChannel();
        channel.exchangeDeclare(EXCHANGE_NAME, BuiltinExchangeType.TOPIC);
    }

    private void mainLoop() throws Exception {
        while (true) {
            System.out.println("Rdy to send info");
            String info = br.readLine();

            System.out.println("Sending " + info);
            channel.basicPublish(EXCHANGE_NAME, "info", null, info.getBytes(StandardCharsets.UTF_8));
        }
    }

}
