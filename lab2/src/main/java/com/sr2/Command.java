package com.sr2;

public class Command {
    private Operation operation;
    private String key;
    private Integer value;

    public Command(Operation operation, String key, Integer value) {
        this.operation = operation;
        this.key = key;
        this.value = value;
    }

    public Operation getOperation() {
        return operation;
    }

    public String getKey() {
        return key;
    }

    public Integer getValue() {
        return value;
    }
}
